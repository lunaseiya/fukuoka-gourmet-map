# -*- coding: utf-8 -*-
"""**座標が取れなかったイベントだけ**、源の詳細ページから会場名と住所を拾って
`data/_イベント会場.json` に溜める【2026-09-16】

■ なぜ必要か
  イベント一覧(map/events.html)の収益導線は「会場の座標 → 近隣2kmの収益スポット」。
  会場が分からないと導線が出ない。一覧ページの `venues` は**源サイトの地域カテゴリ**や
  市区名しか入っていないことが多く、**220件中86件が座標なし**のままだった。
  一方で**詳細ページには会場名と住所がある**(実測):
    ・県公式(crossroadfukuoka) … JSON-LD の `location.name` / `location.address`
    ・いこーよ                  … 「開催場所」ブロック + 住所
    ・よかなび / 久留米観光      … JSON-LD か住所表記

■ 座標の作り方(この順。⚠**推測で作らない**)
  ① 会場名が spots.json にあればその座標を借りる(既に裏取り済みの座標なので一番強い)
  ② 無ければ**詳細ページの住所**を geocoding.jp に投げる(10秒以上あける)
  ③ どちらも駄目なら null のまま。市区の代表座標などで埋めてはいけない
     (2km圏の近隣検索が無意味になり、関係ない店を「近く」と言ってしまう)

■ キャッシュするので2回目以降は取りに行かない
  `data/_イベント会場.json` はキー=イベントURL。手で直してもよい(`"fixed": true` を
  付けると以後このスクリプトは上書きしない)。

使い方:
    python tools/event_venue_fill.py --kids-only            # 子連れ向けだけ(まず試す)
    python tools/event_venue_fill.py --limit 40
    python tools/event_venue_fill.py --no-geocode           # spots突合だけ(速い)
"""
import argparse, html, io, json, os, re, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_events as E

HERE = os.path.dirname(os.path.abspath(__file__))
SPOTS = os.path.join(HERE, '..', 'data', 'spots.json')
EVENTS = os.path.join(HERE, '..', 'map', 'events.json')
OUT = os.path.join(HERE, '..', 'data', '_イベント会場.json')
UA = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
      'Accept-Language': 'ja'}
WAIT_PAGE = 4.0        # 源サイトへの間隔
WAIT_GEO = 11.0        # ⚠geocoding.jp は10秒以上あける(map-spot スキル)

# ⚠**本文から住所らしい文字列を拾うと誤爆する**【2026-09-16に踏んだ】
#   県公式の解説文「**沖縄**八県連合共進会」の開催に際して…」に当たって、
#   福岡のイベントに**沖縄の座標(26.12, 127.70)**を付けてしまった。
#   → 県名の直後に**市区郡**が続くことを必須にする
ADDR = re.compile(r'((?:北海道|東京都|大阪府|京都府|[^\x00-\x7F]{2,3}県)'
                  r'[^\x00-\x7F]{2,8}?[市区郡]'
                  r'[^<>"\n]{0,36}?[0-9０-９][-－ー0-9０-９丁目番地の]*)')
# 取れた座標がここに入っていなければ捨てる(九州北部+山口。**推測で直さない、捨てる**)
BOX = (31.0, 34.9, 128.5, 132.2)


def inbox(la, ln):
    return BOX[0] <= la <= BOX[1] and BOX[2] <= ln <= BOX[3]


# 会場として採ってはいけない文字列(源サイトの名前・地域カテゴリ)
BADV = re.compile(r'いこーよ|クロスロード|よかなび|久留米観光|エリア$')


def fetch(u):
    raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=35).read()
    for e in ('utf-8', 'shift_jis', 'cp932'):
        try:
            return raw.decode(e)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def strip(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def from_ld(h):
    """JSON-LD の location から (会場名, 住所) を取る。県公式・よかなびで効く"""
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>([\s\S]*?)</script>', h):
        try:
            o = json.loads(m.group(1))
        except Exception:
            continue
        for x in (o if isinstance(o, list) else [o]):
            if not isinstance(x, dict):
                continue
            loc = x.get('location')
            if isinstance(loc, list):
                loc = loc[0] if loc else None
            if not isinstance(loc, dict):
                continue
            nm = loc.get('name') or ''
            ad = loc.get('address')
            if isinstance(ad, dict):
                ad = ' '.join(str(ad.get(k) or '') for k in
                              ('addressRegion', 'addressLocality', 'streetAddress')).strip()
            return (strip(nm), strip(ad or ''))
    return ('', '')


def from_html(h):
    """「開催場所」「住所」の見出しの直後を拾う。いこーよ・久留米観光向けの保険"""
    v, a = '', ''
    m = re.search(r'(開催場所|会\s*場|場\s*所)[\s\S]{0,40}?</[^>]+>([\s\S]{0,400}?)<', h)
    if m:
        v = strip(m.group(2))[:60]
    m2 = re.search(r'(住\s*所|所在地)[\s\S]{0,40}?</[^>]+>([\s\S]{0,300}?)<', h)
    if m2:
        a = strip(m2.group(2))[:120]
    if not a:
        m3 = ADDR.search(h)
        if m3:
            a = strip(m3.group(1))[:120]
    return (v, a)


def norm_addr(a):
    """⚠**住所はそのまま投げると geocoding.jp が `<lat>0</lat>` を返す**【2026-09-16に実測】
      源の住所には ①郵便番号 ②県名の二重(「福岡県 福岡県大野城市…」)
      ③括弧の補足(「（海の中道海浜公園内）」) ④番地のあとのビル名・階
      (「…19-27九勧博多駅前ビル1F」)が混ざる。**番地までに削る**"""
    a = re.sub(r'〒?\s*\d{3}[-－]?\d{4}', '', a or '')
    a = re.sub(r'[（(][^）)]*[）)]', '', a)
    a = re.sub(r'\s+', '', a)
    m = list(re.finditer(r'(北海道|東京都|大阪府|京都府|[^\x00-\x7F]{2,3}県)', a))
    if len(m) >= 2:                       # 県名が複数あれば最後のものから採る
        a = a[m[-1].start():]
    m2 = re.match(r'^(.*?[0-9０-９][-－ー0-9０-９丁目番地の]*)', a)
    return (m2.group(1) if m2 else a).strip()


def variants(a):
    """表記を変えて再試行する(map-spot スキルの「`5-6-25` → `5丁目6-25`」と同じ手)"""
    v = [a]
    m = re.match(r'^(.*?[市区町村])(\d+)-(\d+)-(\d+)$', a)
    if m:
        v.append('%s%s丁目%s-%s' % m.groups())
    m2 = re.match(r'^(.*?)(\d+)丁目(\d+)-(\d+)$', a)
    if m2:
        v.append('%s%s-%s-%s' % m2.groups())
    m3 = re.match(r'^(.*?[市区町村].*?\d+)-\d+$', a)
    if m3:
        v.append(m3.group(1))             # 号を落として街区まで
    return [x for i, x in enumerate(v) if x and x not in v[:i]]


def geocode(addr):
    for j, q in enumerate(variants(norm_addr(addr))):
        if j:
            time.sleep(WAIT_GEO)
        u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(q)
        try:
            x = fetch(u)
        except Exception:
            continue
        la = re.search(r'<lat>([\d.]+)</lat>', x)
        ln = re.search(r'<lng>([\d.]+)</lng>', x)
        if la and ln and la.group(1) not in ('0', '0.0'):
            fa, fn = float(la.group(1)), float(ln.group(1))
            if not inbox(fa, fn):
                print('    ⚠圏外なので捨てる %.4f,%.4f  「%s」' % (fa, fn, q[:34]))
                continue
            return (fa, fn, q)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kids-only', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--no-geocode', action='store_true')
    a = ap.parse_args()

    spots = json.load(io.open(SPOTS, encoding='utf-8'))
    cache = json.load(io.open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    d = json.load(io.open(EVENTS, encoding='utf-8'))
    todo = []
    for e in d['events']:
        if e['lat'] is not None or not e.get('url'):
            continue
        if a.kids_only and not e['kids']:
            continue
        c = cache.get(e['url'])
        if c and (c.get('fixed') or c.get('tried')):
            continue
        todo.append(e)
    if a.limit:
        todo = todo[:a.limit]
    print('対象 %d件(座標が無く、まだ詳細を見ていないもの)' % len(todo))

    got_spot = got_geo = miss = 0
    for i, e in enumerate(todo):
        if i:
            time.sleep(WAIT_PAGE)
        try:
            h = fetch(e['url'])
        except Exception as ex:
            print('  ×取得失敗 %-34s %s' % (e['title'][:34], ex))
            cache[e['url']] = {'tried': True, 'error': str(ex)[:80]}
            miss += 1
            continue
        v, ad = from_ld(h)
        if not v or BADV.search(v):
            v2, ad2 = from_html(h)
            v = v2 if (v2 and not BADV.search(v2)) else v
            ad = ad or ad2
        v = (v or '').strip()
        rec = {'title': e['title'], 'venue': v or None, 'address': ad or None,
               'spot': None, 'lat': None, 'lng': None, 'tried': True, 'src': e.get('src')}
        # ① 会場名を spots.json と突合(裏取り済みの座標なので最優先)
        g = E.venue_coords(spots, v, '') if v else None
        if g:
            rec['spot'] = g[3]
            rec['spotName'] = g[2]
            rec['exact'] = (E.core(g[2]) == E.core(v))
            rec['lat'], rec['lng'] = g[0], g[1]
            got_spot += 1
            print('  ○spots %-30s → %s%s' % ((v or '')[:30], g[2],
                                             '' if rec['exact'] else ' (部分一致)'))
        elif ad and not a.no_geocode:
            # ② 住所から座標にする。⚠10秒以上あける
            time.sleep(WAIT_GEO)
            c = geocode(ad)
            if c:
                rec['lat'], rec['lng'] = c[0], c[1]
                rec['geoQuery'] = c[2]
                got_geo += 1
                print('  ○住所  %-30s → %.6f,%.6f  %s' % ((v or '(会場名なし)')[:30],
                                                          c[0], c[1], c[2][:34]))
            else:
                miss += 1
                print('  ×座標  %-30s 住所から取れず: %s' % ((v or '')[:30], ad[:40]))
        else:
            miss += 1
            print('  ×不明  %-34s (会場も住所も読めず)' % e['title'][:34])
        cache[e['url']] = rec

    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(cache, ensure_ascii=False, indent=1))
    print()
    print('spots突合 %d件 / 住所から %d件 / 取れず %d件  → %s (計%d件)'
          % (got_spot, got_geo, miss, os.path.normpath(OUT), len(cache)))


if __name__ == '__main__':
    main()
