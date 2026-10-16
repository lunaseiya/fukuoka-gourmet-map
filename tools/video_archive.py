# -*- coding: utf-8 -*-
"""過去に投稿した動画を「店ごとのフォルダ」に揃えて、索引を作る(2026-10-14 ユーザー依頼)。

目的: Dropboxで素材管理を始める前の投稿(2023〜2026前半)は、何の動画を作ったか・どの店かが
      手元に残っていない。3選/ランキングを組むときに引けるよう、
        ① YouTube の全投稿を正として一覧化(日付・タイトル・尺・URL)
        ② 1本ずつ店(spots.json の id)に対応づけ
        ③ 0.アップロード済/<店のフォルダ>/ に完成動画を置く(無いものは YouTube からダウンロード)
        ④ 0.アップロード済/README_動画索引.md を作る(店・日付・タイトル・URL・置き場)
      同じ店(支店)は1つのフォルダで管理する(撮り直しのときに過去作をすぐ引ける)。

使い方:
  python tools/video_archive.py fetch            # YouTube の全投稿メタデータを data/video_cache/ に保存(10〜20分)
  python tools/video_archive.py plan             # 対応表 data/video_cache/plan.json と 索引 README を作る(ダウンロードはしない)
  python tools/video_archive.py download         # plan に従って未保存ぶんをダウンロード(1本ずつ順に・既にあるものは飛ばす)
  python tools/video_archive.py download --limit 20

店の対応づけの優先順位:
  1. spots.json の video.youtube / video.tiktok に入っている動画 → その店
  2. data/照合除外.txt に載っている動画 → まとめ回/自宅/対象外(店なし)
  3. どちらにも無い → 「未特定」(索引に残し、人が後で店名を付ける)
フォルダの決め方:
  - 店が分かる動画: 0.アップロード済 の既存フォルダ名と店名を突き合わせ(スペース・`1st_`・`(10)` を除いた上で
    店名の語がフォルダ名に含まれる)。合えばそこ、合わなければ `<店名>` でフォルダを作る
  - 店が無い動画: まとめ_ランキング・3選 / まとめ_自宅と商品 / まとめ_お土産 / まとめ_イベント・おでかけ / 未特定
ファイル名: 投稿済_YYYY-MM-DD_<タイトル先頭40字>.mp4(YouTube からの保存)。
  既存フォルダに 完成_*.mp4 がある最近の回はダウンロードしない(完成品が手元にある)。
"""
import os, re, sys, json, glob, subprocess, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SPOTS = os.path.join(ROOT, "data", "spots.json")
IGNORE = os.path.join(ROOT, "data", "照合除外.txt")
CACHE = os.path.join(ROOT, "data", "video_cache")
UPLOADED = os.path.join(os.path.dirname(ROOT), "0.アップロード済")
INDEX_MD = os.path.join(UPLOADED, "README_動画索引.md")
YT_CHANNEL = "https://www.youtube.com/@tenjinconnect/shorts"
YT_LONG = "https://www.youtube.com/@tenjinconnect/videos"
JST = datetime.timezone(datetime.timedelta(hours=9))

os.makedirs(CACHE, exist_ok=True)


# ---------- 取得 ----------
def fetch():
    """yt-dlp で全投稿のメタデータを取る。1本1リクエストなので遅い(248本で15分前後)"""
    out = os.path.join(CACHE, "yt_full.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for url in (YT_CHANNEL, YT_LONG):
            cmd = [sys.executable, "-m", "yt_dlp", "--no-update", "-j", "--skip-download", "--ignore-errors",
                   "--extractor-args", "youtube:lang=ja", url]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            f.write(r.stdout)
    print("saved", out)


def load_tiktok():
    """data/video_cache/tt_list.json(yt-dlp --impersonate chrome --flat-playlist -J tiktokuser:<channel_id>)"""
    p = os.path.join(CACHE, "tt_list.json")
    if not os.path.exists(p):
        return []
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for e in j.get("entries") or []:
        ts = e.get("timestamp")
        date = datetime.datetime.fromtimestamp(ts, JST).strftime("%Y-%m-%d") if ts else ""
        out.append(dict(id=str(e.get("id")), title=e.get("title") or "", date=date, dur=int(e.get("duration") or 0),
                        url=f"https://www.tiktok.com/@tencone/video/{e.get('id')}"))
    return out


def load_videos():
    vids = {}
    for fn in ("yt_full.jsonl",):
        p = os.path.join(CACHE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            vid = j.get("id")
            if not vid or vid in vids:
                continue
            ts = j.get("timestamp") or j.get("release_timestamp")
            if ts:
                date = datetime.datetime.fromtimestamp(ts, JST).strftime("%Y-%m-%d")
            else:
                d = j.get("upload_date") or ""
                date = f"{d[:4]}-{d[4:6]}-{d[6:]}" if len(d) == 8 else ""
            vids[vid] = dict(id=vid, title=j.get("title") or "", date=date,
                             dur=int(j.get("duration") or 0), views=j.get("view_count"),
                             url=f"https://youtube.com/shorts/{vid}" if (j.get("duration") or 0) <= 180 else f"https://www.youtube.com/watch?v={vid}")
    return vids


# ---------- 対応づけ ----------
def load_ignore():
    ids = {}
    if not os.path.exists(IGNORE):
        return ids
    for line in open(IGNORE, encoding="utf-8-sig"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Za-z0-9_-]{11}|\d{15,20})\s*[|#]?\s*(.*)", line)
        if m:
            ids[m.group(1)] = m.group(2).strip()
    return ids


YT_ID_RE = re.compile(r"(?:shorts/|watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")
TT_ID_RE = re.compile(r"/video/(\d{15,20})")


def spot_links(spots):
    by_yt, by_tt = {}, {}
    for s in spots:
        v = s.get("video") or {}
        m = YT_ID_RE.search(v.get("youtube") or "")
        if m:
            by_yt[m.group(1)] = s
        m = TT_ID_RE.search(v.get("tiktok") or "")
        if m:
            by_tt[m.group(1)] = s
    return by_yt, by_tt


def kana(s):
    """ひらがな→カタカナ(「はっちゃん」と「ハちゃん」を同じにする)"""
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)


# 店名の照合で無視する語(これだけで一致させると「博多ラーメン 将丸」が「博多ラーメン はかたや」に付く)
GENERIC = ["ラーメン", "らーめん", "らぁめん", "ラァメン", "総本店", "本店", "1st", "1ST", "元祖", "本家"]


def norm(s):
    s = re.sub(r"^1st_", "", s)
    s = re.sub(r"\(\d+\)", "", s)
    s = kana(s)
    for g in GENERIC:
        s = s.replace(kana(g), "")
    s = re.sub(r"[\s　・･\-_–—/／()（）「」『』【】&＆×]", "", s)
    s = s.replace("ー", "").replace("ッ", "")   # 長音・促音の揺れを吸収
    return s.lower()


def lcs(a, b):
    """最長共通部分文字列(長さ, 文字列)"""
    best, bs = 0, ""
    for i in range(len(a)):
        for j in range(len(b)):
            k = 0
            while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                k += 1
            if k > best:
                best, bs = k, a[i:i + k]
    return best, bs


def existing_folders():
    if not os.path.isdir(UPLOADED):
        return []
    return sorted(d for d in os.listdir(UPLOADED) if os.path.isdir(os.path.join(UPLOADED, d)))


# 地名・業態などの「店名の核ではない語」。これを抜いてから照合する(「天神今泉店」「大野城店」「ホテル」で別の店に付く事故を防ぐ)。
# 支店の区別には逆にこの語を使う(福岡・博多は多すぎるので区別には使わない)
PLACE = ["福岡市", "福岡", "博多駅", "博多", "天神", "今泉", "大名", "中洲", "香椎浜", "香椎", "名島", "千早", "大野城", "新宮", "久留米",
         "別府", "佐世保", "大分", "長崎", "鳥栖", "武雄", "太宰府", "春日", "箱崎", "志免", "久山", "薬院", "赤坂", "西新", "川端",
         "呉服町", "東区", "西区", "南区", "中央区", "早良区", "デイトス", "空港", "和白", "古賀", "めん街道", "ラーメンスタジアム", "くうてん",
         "月隈", "松島", "九産大前", "下原", "鉄板", "小戸", "海の中道", "日出", "うきは", "北九州", "熊本", "大阪", "宗像", "福津", "折尾",
         "那珂川", "奈多", "粕屋", "西公園", "平尾", "鹿子前", "田隈", "照葉", "楽市街道", "新門司", "泉大津", "雑餉隈", "水城", "筑紫野",
         "八幡東", "小倉", "春吉", "西戸崎", "舞松原", "鳥栖元町", "祇園", "住吉", "原", "諏訪野町", "松島", "アクロス", "BRANCH", "パピヨンガーデン",
         "総本店", "本店", "支店", "店", "駅", "前", "ホテル", "旅館", "公園", "カフェ", "cafe", "coffee", "コーヒー", "うどん", "ラーメン",
         "らーめん", "らぁめん", "食堂", "酒場", "屋台", "寿司", "とんかつ", "トンカツ", "天ぷら", "天麩羅", "居酒屋", "リゾート", "スパ",
         "温泉", "中華", "ハンバーガー", "レストラン", "焼肉", "やきにく", "ダイニング", "専門店", "商店街", "1st"]
COMMON_PLACE = {"福岡市", "福岡", "博多", "店", "本店", "総本店", "支店", "駅", "前"}


def core(s):
    """店名の核: 正規化した上で地名・業態語を抜く。空になったら(「福岡空港」等)正規化だけの文字列"""
    n = norm(s)
    c = n
    for p in sorted(PLACE, key=len, reverse=True):
        c = c.replace(norm(p), "")
    return c if len(c) >= 2 else n


def places(s):
    n = norm(s)
    return {p for p in PLACE if p not in COMMON_PLACE and norm(p) and norm(p) in n}


def match_folder(spot, folders):
    """既存フォルダのうち、店名の核が合うものを返す (フォルダ名, 一致率)。
       合格: 核どうしの最長共通部分が3文字以上かつ店名の核の60%以上、または核が丸ごと含まれる。
       同点なら 支店の地名が合うもの > フォルダ名との相互一致率が高いもの"""
    name = spot.get("name", "")
    a = core(name)
    if not a:
        return None, 0
    pa = places(name)
    best, best_key = None, None
    for d in folders:
        b = core(d)
        l, sub = lcs(a, b)
        m = min(len(a), len(b))
        r = l / m
        # 強い一致: 短いほうの核の8割以上が共通(3文字以上)、または短いほうが丸ごと含まれる(2文字以上)
        strong = (l >= 3 and r >= 0.8) or (l == m and l >= 2)
        # 弱い一致: 4文字以上の共通部分が短いほうの6割以上(索引で「要確認」にする)
        weak = (l >= 4 and r >= 0.6)
        if not (strong or weak):
            continue
        pd = places(d)
        # 支店違い: フォルダ側にだけ別の地名が付いていて、店側の地名と1つも重ならない → 別の支店とみなして除外
        extra = pd - pa
        if extra and pa and not (pa & pd):
            continue
        key = (1 if strong else 0, len(pa & pd), -len(extra), round(l / max(len(a), len(b)), 2))
        if best_key is None or key > best_key:
            best, best_key = d, key
    if not best:
        return None, 0
    # 店側にだけ支店の地名があり、フォルダ名に無い(例: 味壱家 博多めん街道店 → フォルダ「モヒカンラーメン」)は要確認扱い
    branch_doubt = bool(pa - places(best)) and not (pa & places(best))
    return best, (0.6 if (not best_key[0] or branch_doubt) else 1.0)


def has_finished(folder):
    p = os.path.join(UPLOADED, folder)
    return bool(glob.glob(os.path.join(p, "完成_*.mp4")) or glob.glob(os.path.join(p, "*完成*.mp4")))


def safe_name(s, n=40):
    s = re.sub(r"#\S+", "", s)                 # ハッシュタグを落とす
    s = re.sub(r"[\\/:*?\"<>|\r\n\t]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n].rstrip(" 　。、!！")


def category_for(title, note):
    t = title + " " + (note or "")
    if re.search(r"今週|連休|家族で行けるところ|おでかけ\d+選|子連れおでかけ", t):
        return "まとめ_イベント・おでかけ"
    if re.search(r"ランキング|TOP\s*\d|トップ\s*\d|\d選|3大|まとめ", t, re.I):
        return "まとめ_ランキング・3選"
    if re.search(r"宅配|宅麺|インスタント|レシピ|自家製|手作り|カルディ|検証|お土産|土産|銘菓", t):
        return "まとめ_自宅・商品・お土産"
    if re.search(r"イルミ|クリスマス|おでかけ|遊べる|公園|イベント|選！", t):
        return "まとめ_イベント・おでかけ"
    return "未特定_店名不明"


def plan():
    vids = load_videos()
    if not vids:
        print("先に fetch を実行してください"); return
    spots = json.load(open(SPOTS, encoding="utf-8"))
    by_yt, by_tt = spot_links(spots)
    ignore = load_ignore()
    folders = existing_folders()
    rows = []
    for v in sorted(vids.values(), key=lambda x: x["date"], reverse=True):
        sp = by_yt.get(v["id"])
        if sp:
            folder, cov = match_folder(sp, folders)
            kind, check = "store", ""
            if not folder:
                folder = safe_name(sp["name"], 50)
                kind = "store-new"
                # Dropbox管理(2026-07〜)以降の回なのに既存フォルダに一致しない = フォルダ名が店名と違うだけの可能性が高い。
                # 重複保存を避けるため自動ではダウンロードせず、人が既存フォルダ名を直す/指定する
                if v["date"] >= "2026-07-01":
                    check = "最近の回なのに既存フォルダに一致せず(フォルダ名を店名に寄せるか確認)"
            elif cov < 0.8:
                check = "フォルダ照合が弱い(部分一致)。同じ店か確認"
            r = dict(v, spot=sp["id"], store=sp["name"], city=sp.get("city") or "", folder=folder, kind=kind,
                     local=has_finished(folder) if kind == "store" else False, check=check,
                     skip=bool(check and kind == "store-new"))
        elif v["id"] in ignore:
            folder = category_for(v["title"], ignore[v["id"]])
            r = dict(v, spot="", store="", city="", folder=folder, kind="noshop", local=False, note=ignore[v["id"]], check="", skip=False)
        else:
            folder = category_for(v["title"], "")
            r = dict(v, spot="", store="", city="", folder=folder, kind="unknown", local=False, check="店が未特定", skip=False)
        r["platform"] = "youtube"; r["tiktok"] = ""
        rows.append(r)

    # ---- TikTok: YouTube と同じ動画は同じ行に URL を足す。TikTok にしか無いものは行を足す ----
    def days(a, b):
        try:
            return abs((datetime.date.fromisoformat(a) - datetime.date.fromisoformat(b)).days)
        except Exception:
            return 99
    for t in load_tiktok():
        sp = by_tt.get(t["id"])
        hit = None
        if sp:
            cands = [r for r in rows if r.get("spot") == sp["id"] and r["platform"] == "youtube" and not r["tiktok"]]
            hit = min(cands, key=lambda r: days(r["date"], t["date"]), default=None)
            if hit and days(hit["date"], t["date"]) > 3:
                hit = None
        if not hit:
            # 店の紐付きが無くても、近い日(±3日)の YouTube 動画で「店名がキャプションに入っている」か
            # 「タイトルの共通部分が長い」ものがあれば同じ動画とみなす(TikTokのキャプションはYouTubeの題名と違うことが多い)
            tn = norm(t["title"])
            best, best_s = None, 0
            for r in rows:
                if r["platform"] != "youtube" or r["tiktok"] or days(r["date"], t["date"]) > 3:
                    continue
                s = lcs(tn, norm(r["title"]))[0]
                if r.get("store"):
                    toks = [norm(p) for p in re.split(r"[\s　・･/／()（）「」『』【】]+", r["store"])]
                    if any(len(x) >= 2 and x in tn for x in toks):
                        s += 100
                if s > best_s:
                    best, best_s = r, s
            if best and (best_s >= 100 or best_s >= 5):
                hit = best
            elif not best_s:
                # 同じ日に YouTube が1本だけならそれ
                cands = [r for r in rows if r["platform"] == "youtube" and not r["tiktok"] and days(r["date"], t["date"]) <= 1]
                hit = cands[0] if len(cands) == 1 else None
        if hit:
            hit["tiktok"] = t["url"]
            continue
        if sp:
            folder, cov = match_folder(sp, folders)
            kind, check = "store", ""
            if not folder:
                folder = safe_name(sp["name"], 50); kind = "store-new"
                if t["date"] >= "2026-07-01":
                    check = "最近の回なのに既存フォルダに一致せず(フォルダ名を店名に寄せるか確認)"
            elif cov < 0.8:
                check = "フォルダ照合が弱い(部分一致)。同じ店か確認"
            r = dict(t, spot=sp["id"], store=sp["name"], city=sp.get("city") or "", folder=folder, kind=kind,
                     local=has_finished(folder) if kind == "store" else False, check=check, skip=bool(check and kind == "store-new"))
        elif t["id"] in ignore:
            r = dict(t, spot="", store="", city="", folder=category_for(t["title"], ignore[t["id"]]), kind="noshop", local=False,
                     note=ignore[t["id"]], check="", skip=False)
        else:
            r = dict(t, spot="", store="", city="", folder=category_for(t["title"], ""), kind="unknown", local=False,
                     check="店が未特定(TikTokのみ)", skip=False)
        r["platform"] = "tiktok"; r["tiktok"] = t["url"]
        rows.append(r)

    for r in rows:
        tag = "" if r["platform"] == "youtube" else "TikTok_"
        r["file"] = f"投稿済_{r['date']}_{tag}{safe_name(r['title'])}.mp4"
        r["path"] = os.path.join(UPLOADED, r["folder"], r["file"])
        r["exists"] = os.path.exists(r["path"])
    rows.sort(key=lambda r: r["date"], reverse=True)
    json.dump(rows, open(os.path.join(CACHE, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_index(rows)
    c = {}
    for r in rows:
        c[r["kind"]] = c.get(r["kind"], 0) + 1
    need = sum(1 for r in rows if not r["exists"] and not r["local"] and not r.get("skip"))
    tt_only = sum(1 for r in rows if r["platform"] == "tiktok")
    both = sum(1 for r in rows if r["platform"] == "youtube" and r["tiktok"])
    print(f"動画 {len(rows)}本(YouTube {len(rows)-tt_only}・うちTikTokにもある {both} / TikTokのみ {tt_only}): "
          f"店に紐付き {c.get('store',0)+c.get('store-new',0)}(新フォルダ {c.get('store-new',0)}) / "
          f"まとめ・対象外 {c.get('noshop',0)} / 未特定 {c.get('unknown',0)} / ダウンロード要 {need}")
    print("索引:", INDEX_MD)


def write_index(rows):
    by_folder = {}
    for r in rows:
        by_folder.setdefault(r["folder"], []).append(r)
    lines = ["# 投稿済み動画の索引(店ごと)", "",
             f"更新 {datetime.date.today().isoformat()} / YouTube @tenjinconnect の全投稿 {len(rows)}本。"
             "作り直しは `python 4.MAP生成/tools/video_archive.py plan`(ダウンロードは `download`)。", "",
             "- 店が分かる動画は spots.json の紐付き(マップのid)で振り分け。フォルダは 0.アップロード済 の中",
             "- 「まとめ_*」はランキング・3選・自宅・お土産など店に紐付かない回。「未特定_店名不明」は人が店名を付ける",
             "- 置き場の列: ✅=保存済み / 📁=そのフォルダに完成品あり(ダウンロード不要) / ⬇=未保存 / ⏸=保留(要確認)", ""]
    checks = [r for r in rows if r.get("check")]
    if checks:
        lines += ["## ⚠ 要確認", "", "| 投稿日 | 店/フォルダ | 理由 | タイトル | URL |", "|---|---|---|---|---|"]
        for r in sorted(checks, key=lambda r: r["date"], reverse=True):
            lines.append(f"| {r['date']} | {r.get('store') or r['folder']} | {r['check']} | {safe_name(r['title'], 50)} | {r['url']} |")
        lines.append("")
    # 店フォルダ → まとめ → 未特定 の順
    def order(k):
        return (0 if not k.startswith(("まとめ_", "未特定_")) else 1 if k.startswith("まとめ_") else 2, k)
    for folder in sorted(by_folder, key=order):
        rs = sorted(by_folder[folder], key=lambda r: r["date"], reverse=True)
        head = rs[0]
        label = folder if not head.get("store") else f"{folder}  ← {head['store']}({head['city']}・id={head['spot']})"
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| 投稿日 | 置き場 | 尺 | タイトル | URL |")
        lines.append("|---|---|---|---|---|")
        for r in rs:
            st = "✅" if r["exists"] else ("📁" if r["local"] else ("⏸" if r.get("skip") else "⬇"))
            urls = r["url"] + (f" / {r['tiktok']}" if r.get("tiktok") and r["platform"] == "youtube" else "")
            lines.append(f"| {r['date']} | {st} | {r['dur']}秒 | {safe_name(r['title'], 60)} | {urls} |")
        lines.append("")
    os.makedirs(UPLOADED, exist_ok=True)
    with open(INDEX_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------- ダウンロード ----------
def download(limit=None, only=None):
    rows = json.load(open(os.path.join(CACHE, "plan.json"), encoding="utf-8"))
    todo = [r for r in rows if not os.path.exists(r["path"]) and not r["local"] and not r.get("skip")]
    if only:
        todo = [r for r in todo if r["id"] in only or r["folder"] in only]
    if limit:
        todo = todo[:limit]
    print(f"ダウンロード {len(todo)}本")
    ok = ng = 0
    # ⚠Dropbox の中で yt-dlp に直接書かせると、.part の改名を Dropbox が掴んで PermissionError になる(2026-10-14に3本目で停止)。
    #   Dropbox の外(一時フォルダ)に落としてから、完成ファイル名でコピーして入れる(改名しないのでロックに当たらない)
    import tempfile, shutil, time
    tmpdir = os.path.join(tempfile.gettempdir(), "video_archive_dl")
    os.makedirs(tmpdir, exist_ok=True)
    for i, r in enumerate(todo, 1):
        os.makedirs(os.path.dirname(r["path"]), exist_ok=True)
        tmp = os.path.join(tmpdir, f"{r['id']}.mp4")
        if os.path.exists(tmp):
            os.remove(tmp)
        cmd = [sys.executable, "-m", "yt_dlp", "--no-update", "-q", "--no-warnings",
               "-f", "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b",
               "--merge-output-format", "mp4", "-o", tmp]
        if r.get("platform") == "tiktok":
            cmd += ["--impersonate", "chrome"]   # TikTok は curl_cffi(0.13系) でブラウザ偽装しないと弾かれる
        cmd.append(r["url"])
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            done = False
            for _ in range(10):
                try:
                    shutil.copyfile(tmp, r["path"]); done = True; break
                except PermissionError:
                    time.sleep(2)
            if done:
                os.remove(tmp); ok += 1
                print(f"[{i}/{len(todo)}] ok  {r['folder']}/{r['file']}", flush=True)
            else:
                ng += 1
                print(f"[{i}/{len(todo)}] NG  コピー失敗(Dropboxロック) {r['path']}", flush=True)
        else:
            ng += 1
            print(f"[{i}/{len(todo)}] NG  {r['url']}  {res.stderr.strip()[-200:]}", flush=True)
    # 索引の✅を更新
    for r in rows:
        r["exists"] = os.path.exists(r["path"])
    json.dump(rows, open(os.path.join(CACHE, "plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_index(rows)
    print(f"完了 ok={ok} ng={ng}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "plan", "download"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if a.cmd == "fetch":
        fetch()
    elif a.cmd == "plan":
        plan()
    else:
        download(a.limit, a.only)
