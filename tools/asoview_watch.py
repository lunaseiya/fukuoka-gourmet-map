# -*- coding: utf-8 -*-
"""アソビューの新着を見張る。新しい動画作業を始めるセッションの冒頭で回す。

  python tools/asoview_watch.py            # 新着の検出だけ(既存の詳細キャッシュは触らない)
  python tools/asoview_watch.py --fetch    # 新着の詳細(住所・座標)も取得してキャッシュに足す

やること:
 1. 会期切れ(until を過ぎた)スポットを一覧にする → spots.json から消すか判断する
 2. 会期が近い(30日以内)スポットを一覧にする     → 投稿ネタとして拾う
 3. アソビューを再クロールして、キャッシュに無い base id を見つける
    → 名前に「展/フェス/期間限定」等が入るものは【期間限定候補】として別枠で出す
      (会期はページに構造化データが無いので、Web検索で調べて until を手で入れる)
    → それ以外は tools/asoview_import.py --apply で一括登録できる

■ このクロールの取りこぼし【2026-08-31 判明・重要】
アソビューのジャンル×県の一覧ページは **1県1ジャンルあたり十数件しか返さない**
(例: 福岡県 grp1=12件 / grp2=15件 / grp8=20件 / 191=4件)。ページ送りも効かない。
つまりこのクロールは**掲載施設の一部しか見ていない**。
実例: 福岡アンパンマンこどもミュージアム(base/157187)はアソビューで売っているのに
      628件のキャッシュに入っていなかった。
→ **主要施設は個別にWeb検索して base id を確かめること**。このクロールだけに頼らない。
   「<施設名> アソビュー」で検索すれば base ページが出る。

なぜ会期を自動取得しないか(2026-08-28実測):
  アソビューの施設ページには validFrom/validThrough も「開催期間」表記も無く、
  会期はページ内のどこにも機械可読な形で置かれていない。
  したがって会期だけは主催者サイト等をWeb検索して確認する運用にする。
"""
import json, io, re, os, sys, time, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP  = os.path.join(ROOT, 'data', 'spots.json')
DET  = os.path.join(ROOT, 'data', 'asoview_detail.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

# 九州7県+山口。asoview_crawl.py と同じコード
PREFS = ['prf400000','prf410000','prf420000','prf430000','prf440000',
         'prf450000','prf460000','prf350000']
GENRES = ['grp8','grp2','grp1','grp3','grp4','191','192','193','194','195','196','197','198','212','213']
LIMITED_WORD = ['展', 'フェス', '期間限定', '限定開催', 'イルミネーション', 'ナイター',
                '花火', 'まつり', '祭', 'シーズン', '開催中']
ADDR_PAT = re.compile(
    r'((?:福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|山口)県[^<">）)]{3,40}[0-9０-９][-−0-9０-９]{0,14})')

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25)\
                         .read().decode('utf-8', 'replace')

def title_of(bid):
    try:
        h = get('https://www.asoview.com/base/%s/' % bid)
    except Exception:
        return None, None, None, None
    m = re.search(r'<title>(.*?)</title>', h, re.S)
    t = re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''
    for p in [r'\s*[｜|]\s*(割引チケット|アソビュー).*$', r'^【[^】]*】\s*',
              r'の(前売りチケット|ネット予約).*$', r'\s*[-ー]\s*アソビュー[！!]?\s*$']:
        t = re.sub(p, '', t)
    a = ADDR_PAT.search(h)
    lat = re.search(r'"latitude"\s*:\s*"?([\d.]+)', h)
    lng = re.search(r'"longitude"\s*:\s*"?([\d.]+)', h)
    return (t.strip(),
            a.group(1).strip() if a else None,
            float(lat.group(1)) if lat else None,
            float(lng.group(1)) if lng else None)

def main():
    do_fetch = '--fetch' in sys.argv
    sp  = json.load(io.open(MAP, encoding='utf-8'))
    det = json.load(io.open(DET, encoding='utf-8')) if os.path.exists(DET) else {}
    today = datetime.date.today()

    # ---- 1) 会期切れ / 2) 期限が近い ----
    expired, soon = [], []
    for s in sp:
        if not s.get('until'):
            continue
        try:
            d = datetime.date.fromisoformat(s['until'])
        except Exception:
            continue
        left = (d - today).days
        (expired if left < 0 else soon if left <= 30 else []).append((left, s['name'], s['id']))
    print('=== 会期切れ %d件(マップでは自動非表示。消すなら spots.json から削除) ===' % len(expired))
    for left, n, i in sorted(expired):
        print('  %5d日前に終了  %-40s %s' % (-left, n[:40], i))
    print('=== 会期が近い %d件(投稿ネタとして優先) ===' % len(soon))
    for left, n, i in sorted(soon):
        print('  あと%3d日  %-44s %s' % (left, n[:44], i))
    print()

    # ---- 3) 新着の検出 ----
    known = set(det.keys())
    found, seen_urls = {}, set()
    for p in PREFS:
        for g in GENRES:
            u = 'https://www.asoview.com/leisure/%s/location/%s/' % (g, p)
            if u in seen_urls:
                continue
            seen_urls.add(u)
            try:
                h = get(u)
            except Exception:
                time.sleep(0.5); continue
            for m in re.finditer(r'/base/(\d+)/', h):
                found.setdefault(m.group(1), None)
            time.sleep(0.7)
    new = [b for b in found if b not in known]
    print('=== クロール結果: 掲載 %d件 / キャッシュ済み %d件 / 新着 %d件 ===' % (len(found), len(known), len(new)))
    if not new:
        print('新着なし'); print('WATCH_DONE'); return

    rows = []
    for n, bid in enumerate(new, 1):
        t, a, lat, lng = title_of(bid)
        rows.append((bid, t or '(名称取得できず)', a, lat, lng))
        if do_fetch:
            det[bid] = {'name': t, 'addr': a, 'addr2': a, 'lat': lat, 'lng': lng, 'genre': None}
        time.sleep(0.6)
    if do_fetch:
        io.open(DET, 'w', encoding='utf-8').write(json.dumps(det, ensure_ascii=False, indent=1))
        print('詳細キャッシュに %d件 追加した' % len(new))

    lim = [r for r in rows if any(w in (r[1] or '') for w in LIMITED_WORD)]
    oth = [r for r in rows if r not in lim]
    print()
    print('--- 【期間限定候補】%d件 … 会期をWeb検索して until/untilLabel を付けて登録する ---' % len(lim))
    for bid, t, a, lat, lng in lim:
        print('  base/%-8s %-44s %s' % (bid, t[:44], (a or '住所不明')[:28]))
    print('--- 通常の新着 %d件 … tools/asoview_import.py --apply で登録できる ---' % len(oth))
    for bid, t, a, lat, lng in oth[:30]:
        print('  base/%-8s %-44s %s' % (bid, t[:44], (a or '住所不明')[:28]))
    if len(oth) > 30:
        print('  ... 他 %d件' % (len(oth) - 30))
    print('WATCH_DONE')

if __name__ == '__main__':
    main()
