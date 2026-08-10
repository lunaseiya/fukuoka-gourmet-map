# -*- coding: utf-8 -*-
"""投稿済み動画とspots.jsonの突合チェック

YouTube/TikTokの投稿一覧をyt-dlpで取得し、spots.jsonに動画URLが
登録されていない「マップ未反映の投稿」を検出する。

使い方: python tools/check_upload_sync.py
(リポジトリルートから実行。Instagramはログインが要るため対象外 →
 未反映が出たらインスタ分はClaude+Chromeで確認する)
"""
import json
import os
import re
import subprocess
import sys

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, "data", "spots.json")
PENDING = os.path.join(ROOT, "data", "投稿待ち.md")
IGNORE = os.path.join(ROOT, "data", "照合除外.txt")


def load_ignore():
    """保留済み(店名不明・チェーン店等)の動画ID。行頭#はコメント"""
    ids = set()
    if os.path.exists(IGNORE):
        with open(IGNORE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ids.add(line.split("|")[0].strip())
    return ids

YT_CHANNEL = "https://www.youtube.com/@tenjinconnect/shorts"
TT_CHANNEL = "https://www.tiktok.com/@tencone"


def enumerate_channel(url):
    """チャンネルの全動画を [(id, title), ...] で返す"""
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


def registered_ids(spots):
    yt, tt = set(), set()
    for s in spots:
        v = s.get("video") or {}
        u = v.get("youtube") or ""
        m = re.search(r"(?:shorts/|watch\?v=)([\w-]{6,})", u)
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
    for label, url, reg, link in (
        ("YouTube", YT_CHANNEL, yt_reg, "https://youtube.com/shorts/{}"),
        ("TikTok", TT_CHANNEL, tt_reg, "https://www.tiktok.com/@tencone/video/{}"),
    ):
        try:
            vids = enumerate_channel(url)
        except Exception as e:
            print(f"[{label}] 取得失敗: {e}")
            continue
        if not vids:
            print(f"[{label}] ⚠ 取得0本 = 列挙失敗の可能性大(レート制限等)。"
                  "時間をおいて再実行してください")
            continue
        un = [(v, t) for v, t in vids if v not in reg and v not in ignore]
        print(f"[{label}] 投稿 {len(vids)}本 / マップ未反映 {len(un)}本")
        for v, t in un:
            print(f"  - {t}")
            print(f"    {link.format(v)}")
        missing.extend(un)

    if os.path.exists(PENDING):
        print("\n--- data/投稿待ち.md(完成済み・投稿待ちの動画) ---")
        with open(PENDING, encoding="utf-8") as f:
            print(f.read().strip())

    if not missing:
        print("\n✅ 投稿済み動画はすべてマップに反映されています")
    else:
        print(f"\n⚠ マップ未反映の投稿が {len(missing)}本 あります。"
              "青ピンからの移行 or 新規赤ピン追加を行ってください")


if __name__ == "__main__":
    main()
