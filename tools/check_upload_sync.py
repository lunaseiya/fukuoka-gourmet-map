# -*- coding: utf-8 -*-
"""投稿済み動画とspots.jsonの突合チェック

YouTube/TikTokの投稿一覧をyt-dlpで取得し、spots.jsonに動画URLが
登録されていない「マップ未反映の投稿」を検出する。

使い方: python tools/check_upload_sync.py
(リポジトリルートから実行。Instagramはログインが要るため対象外 →
 未反映が出たらインスタ分はClaude+Chromeで確認する)
"""
import datetime
import json
import os
import re
import subprocess
import sys

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

JST = datetime.timezone(datetime.timedelta(hours=9))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, "data", "spots.json")
PENDING = os.path.join(ROOT, "data", "投稿待ち.md")
IGNORE = os.path.join(ROOT, "data", "照合除外.txt")


def load_ignore():
    """保留済み(店名不明・チェーン店等)の動画ID。行頭#はコメント。

    照合除外.txt の実際の書式は `<動画ID>  # 説明` なので、**行末のコメントも落とす**。
    以前は "|" でしか切っておらず、ID にコメントが付いたまま集合に入っていたため
    除外リストが1件も機能していなかった(2026-09-09に発覚。26本すべて素通りしていた)。
    """
    ids = set()
    if os.path.exists(IGNORE):
        with open(IGNORE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                vid = line.split("|")[0].split("#")[0].strip()
                if vid:
                    ids.add(vid)
    return ids

YT_CHANNEL = "https://www.youtube.com/@tenjinconnect/shorts"
YT_LONG = "https://www.youtube.com/@tenjinconnect/videos"
TT_CHANNEL = "https://www.tiktok.com/@tencone"

# チャンネル一覧の先頭から何本を「最近の投稿」として扱うか。
# 2026-08-23のユーザー判断で、それ以前の未反映(80本前後)は追加しない方針。
# 全部を並べると最近の数本が埋もれて見落とすので(2026-09-09に実際に7本溜めた)、
# 最近分だけを「要対応」として先に出し、古い分は件数だけにまとめる。
RECENT_N = 40

# 投稿日を個別取得する上限。1本あたり1リクエストかかるので、要対応分だけに絞る
MAX_DATE_LOOKUPS = 20


def enumerate_channel(url):
    """チャンネルの全動画を [(id, title), ...] で返す(新しい順)"""
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist",
           "--print", "%(id)s|%(title)s",
           "--extractor-args", "youtube:lang=ja", url]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    vids = []
    for line in (r.stdout or "").splitlines():
        if "|" in line:
            vid, title = line.split("|", 1)
            vids.append((vid.strip(), title.strip()))
    return vids


def jst_posted(video_id):
    """動画の投稿日を JST の "YYYY-MM-DD" で返す。取れなければ None。

    yt-dlp の %(upload_date)s は **UTC** の日付なので、そのまま posted に入れると
    JSTの日付と1日ずれることがある(実際に2件ずれていた: 2026-09-09に訂正)。
    epoch の %(timestamp)s を JST に直して日付を取るのが正しい。
    """
    cmd = [sys.executable, "-m", "yt_dlp", "--skip-download",
           "--print", "%(timestamp)s|%(release_timestamp)s|%(upload_date)s",
           "https://www.youtube.com/watch?v=" + video_id]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except Exception:
        return None
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    parts = line[0].split("|")
    for p in parts[:2]:
        if p.isdigit():
            jst = datetime.datetime.fromtimestamp(int(p), JST)
            return jst.strftime("%Y-%m-%d")
    # timestamp が取れない場合だけ upload_date にフォールバック(UTC日付なので注意)
    if len(parts) > 2 and re.fullmatch(r"\d{8}", parts[2].strip()):
        d = parts[2].strip()
        return "%s-%s-%s(UTC。JSTとずれる可能性あり)" % (d[:4], d[4:6], d[6:])
    return None


# spots.json の YouTube URL は3形式が混在している。youtu.be を拾えておらず、
# 登録済みの動画を「未反映」と誤検出していた(2026-09-09に発覚)
YT_URL_RE = re.compile(r"(?:shorts/|watch\?v=|youtu\.be/|/live/|/embed/)([\w-]{6,})")


def registered_ids(spots):
    yt, tt = set(), set()
    for s in spots:
        v = s.get("video") or {}
        u = v.get("youtube") or ""
        m = YT_URL_RE.search(u)
        if m:
            yt.add(m.group(1))
        u = v.get("tiktok") or ""
        m = re.search(r"/video/(\d+)", u)
        if m:
            tt.add(m.group(1))
    return yt, tt


def main():
    with open(SPOTS, encoding="utf-8") as f:
        spots = json.load(f)
    yt_reg, tt_reg = registered_ids(spots)
    ignore = load_ignore()

    print(f"spots.json 登録済み: YouTube {len(yt_reg)}本 / TikTok {len(tt_reg)}本"
          f" / 保留(除外) {len(ignore)}本")
    print("チャンネル一覧を取得中(1〜2分)...")

    missing = []
    for label, urls, reg, link, dates in (
        ("YouTube", [YT_CHANNEL, YT_LONG], yt_reg,
         "https://youtube.com/shorts/{}", True),
        ("TikTok", [TT_CHANNEL], tt_reg,
         "https://www.tiktok.com/@tencone/video/{}", False),
    ):
        vids, seen = [], set()
        failed = False
        for url in urls:
            try:
                got = enumerate_channel(url)
            except Exception as e:
                print(f"[{label}] {url} の取得失敗: {e}")
                failed = True
                continue
            # ショートと通常動画は別タブなので両方見る。順番(新しい順)は保つ
            for v, t in got:
                if v not in seen:
                    seen.add(v)
                    vids.append((v, t))
        if not vids:
            print(f"[{label}] ⚠ 取得0本 = 列挙失敗の可能性大(レート制限等)。"
                  "時間をおいて再実行してください")
            continue
        if failed:
            print(f"[{label}] ⚠ 一部のタブが取得できていません。件数は参考値です")

        un = [(i, v, t) for i, (v, t) in enumerate(vids)
              if v not in reg and v not in ignore]
        recent = [x for x in un if x[0] < RECENT_N]
        old = [x for x in un if x[0] >= RECENT_N]

        print(f"[{label}] 投稿 {len(vids)}本 / マップ未反映 {len(un)}本"
              f" (うち最近{RECENT_N}本以内 = **{len(recent)}本**)")

        if recent:
            print(f"  ── 要対応: 最近の未反映 {len(recent)}本 ──")
            for n, (_, v, t) in enumerate(recent):
                posted = None
                if dates and n < MAX_DATE_LOOKUPS:
                    posted = jst_posted(v)
                head = f"  - [{posted}] " if posted else "  - "
                print(f"{head}{t}")
                print(f"    {link.format(v)}")
            if dates and len(recent) > MAX_DATE_LOOKUPS:
                print(f"  ※投稿日は先頭{MAX_DATE_LOOKUPS}本のみ取得しています")
        if old:
            print(f"  ── 旧backlog {len(old)}本 (2026-08-23のユーザー判断で追加しない方針。"
                  "対応不要) ──")
        missing.extend((v, t) for _, v, t in recent)

    if os.path.exists(PENDING):
        print("\n--- data/投稿待ち.md(完成済み・投稿待ちの動画) ---")
        with open(PENDING, encoding="utf-8") as f:
            print(f.read().strip())

    if not missing:
        print("\n✅ 最近の投稿はすべてマップに反映されています")
    else:
        print(f"\n⚠ 最近の投稿で未反映が {len(missing)}本 あります。"
              "青ピンからの移行 or 新規赤ピン追加を行ってください")
        print("  posted には上の [YYYY-MM-DD](JST) をそのまま入れる。"
              "yt-dlp の upload_date はUTCなので使わないこと")


if __name__ == "__main__":
    main()
