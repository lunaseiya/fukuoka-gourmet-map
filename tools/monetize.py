# -*- coding: utf-8 -*-
"""収益リンクの自動照合(2026-08-28確立)。登録・照合のタイミングで回す。

  python tools/monetize.py --ids id1 id2 ...   # 指定スポットだけ照合(登録フローで使う)
  python tools/monetize.py --sweep gourmet --limit 30   # 未付与の赤ピンから一括埋め
  --apply を付けたときだけ書き込む(省略時はドライラン)

3系統:
  gourmet → tabelog  (食べログ店舗URL。マップの「食べログ」PRボタン+LinkSwitchで収益化)
  play    → asoview  (data/asoview_index.json との照合。誤マッチガード付き)
  stay    → booking  (じゃらんの宿ページ直リンク。LinkSwitchで収益化)

鉄則:
  - 既存のリンクは上書きしない
  - 店名の一致だけで採らない。食べログ/じゃらんは店舗ページを開いて
    「閉店・移転が付いていないか」「住所の市区が合うか」を確認してから書く
  - 確認できなければ付けない(推測禁止)
"""
import json, io, re, os, sys, time, shutil, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP  = os.path.join(ROOT, 'data', 'spots.json')
AIDX = os.path.join(ROOT, 'data', 'asoview_index.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
SLEEP = 4.0   # 外部サイトへのリクエスト間隔

def get(url, enc='utf-8'):
    raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
    for e in (enc, 'utf-8', 'cp932'):
        try: return raw.decode(e)
        except Exception: pass
    return raw.decode('utf-8', 'replace')

def norm(s):
    s = re.sub(r'[（(].*?[)）]', '', str(s))
    s = re.sub(r'[\s　・=\-−ー_,、。&＆/／「」『』!！\'\"★☆]', '', s)
    s = s.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'))
    return s.lower()

# ---------------- 食べログ ----------------
def _tabelog_search(q):
    h = get('https://tabelog.com/rst/rstsearch/?sk=' + urllib.parse.quote(q))
    return list(zip(
        re.findall(r'class="list-rst__rst-name-target[^"]*"[^>]*>([^<]+)<', h),
        re.findall(r'https://tabelog\.com/\w+/A\d+/A\d+/\d+/', h)))

def find_tabelog(spot):
    """店名+エリアで検索(クエリは短いほどヒットする。市区まで付けると0件になる=実測)。
       候補ページを開いて閉店/移転と市区の一致を確認してからURLを返す"""
    name = spot['name']
    # 「ラーメン/カフェ」等の冠と「◯◯店」の枝番を落とした本体名も試す
    core = re.sub(r'^(ラーメン|らーめん|カフェ|定食|食堂|中華食堂|回転寿司|焼肉)\s*', '', name)
    core = re.sub(r'\s.*?店$', '', core)
    area = re.sub(r'[（(].*?[)）]', '', str(spot.get('area') or '')).strip()
    city = str(spot.get('city') or '')
    queries = []
    for q in [f'{name} {area}', f'{core} {area}', f'{core} {city}', core]:
        q = q.strip()
        if q and q not in queries: queries.append(q)
    n0 = norm(name)
    n0core = re.sub(r'店$', '', norm(name))
    citykey = city.replace('福岡市', '').replace('市', '').replace('区', '').replace('郡', '')[:2]
    for qi, q in enumerate(queries):
        try:
            pairs = _tabelog_search(q)
        except Exception:
            time.sleep(SLEEP); continue
        for rank, (cand, url) in enumerate(pairs[:3]):
            nc = norm(cand)
            strong = (n0core and (n0core in nc or nc in n0core))
            weak = (rank == 0 and len(set(n0) & set(nc)) >= 3)   # 表記ゆれ(カナ⇔漢字)は1位のみ許容
            if not (strong or weak):
                continue
            time.sleep(SLEEP)
            try:
                page = get(url)
            except Exception:
                continue
            title = re.search(r'<title>(.*?)</title>', page, re.S)
            title = re.sub(r'\s+', ' ', title.group(1)) if title else ''
            if '閉店' in title or '移転' in title:
                return None, '閉店/移転: ' + title[:40]
            addr = re.search(r'(?:福岡県|大分県|佐賀県|長崎県|熊本県|宮崎県|鹿児島県|山口県)[^<"]{2,40}', page)
            if citykey and addr and citykey not in addr.group(0):
                continue   # 同名の他都市店。次の候補へ
            if not strong and not (citykey and addr and citykey in addr.group(0)):
                continue   # 弱一致は住所一致が取れたときだけ採用
            return url, cand.strip()
        time.sleep(SLEEP)
    return None, '検索ヒットなし(%d クエリ試行)' % len(queries)

# ---------------- じゃらん ----------------
def find_jalan(spot):
    # ★キーワードはcp932で送らないと日本語が0件になる(2026-08-26実測)
    q = urllib.parse.quote(spot['name'].encode('cp932', 'ignore'))
    try:
        h = get('https://www.jalan.net/uw/uwp2011/uww2011init.do?keyword=' + q, enc='cp932')
    except Exception as e:
        return None, 'search err: %r' % (e,)
    ids = []
    for m in re.finditer(r"openYadoSyosai\('(\d+)'", h):
        if m.group(1) not in ids: ids.append(m.group(1))
    for yid in ids[:3]:
        time.sleep(SLEEP)
        url = 'https://www.jalan.net/yad%s/' % yid
        try:
            page = get(url, enc='cp932')
        except Exception:
            continue
        title = re.search(r'<title>(.*?)</title>', page, re.S)
        title = re.sub(r'\s+', ' ', title.group(1)) if title else ''
        n0, nt = norm(spot['name']), norm(title)
        if not (n0 in nt or len(set(n0) & set(nt)) >= max(3, int(len(n0)*0.6))):
            continue
        city = (spot.get('city') or '').replace('市', '').replace('郡', '')
        if city and city[:2] not in page:
            continue
        return url, title[:36]
    return None, '該当宿なし'

# ---------------- アソビュー ----------------
CONTAINER_GENRE = {'ショッピングモール', 'ショッピングモール(アウトレット)', '空港ターミナル', '道の駅'}
TENANT_WORDS = ['カフェ', 'Café', 'cafe', 'MOCHA', 'モカ', 'Rio', 'アニマル', 'animal',
                'VS PARK', 'ザキッズ', 'キッズランド', 'リトルプラネット', 'あそびパーク',
                'Yukids', 'モーヴィ']
def clean_aso(t):
    t = str(t)
    t = re.sub(r'[｜|]\s*(ネット予約なら)?アソビュー[！!].*$', '', t)
    t = re.sub(r'の(前売りチケット|ネット予約)[^ ]*[-ー]\s*アソビュー[！!]?\s*$', '', t)
    t = re.sub(r'の(前売りチケット|ネット予約|割引)[・、].*$', '', t)
    t = re.sub(r'\s*[-ー]\s*アソビュー[！!]?\s*$', '', t)
    t = re.sub(r'[｜|].*$', '', t)
    t = re.sub(r'^【[^】]*】\s*', '', t)
    t = re.sub(r'^(超特割！|特割！)\s*', '', t)
    t = re.sub(r'(の前売りチケット|のネット予約|の口コミ).*$', '', t)
    return t.strip()

def find_asoview(spot, idx, used):
    if str(spot.get('genre')) in CONTAINER_GENRE:
        return None, '入れ物ジャンル'
    n = norm(spot['name'])
    if len(n) < 4:
        return None, '名前が短すぎ'
    for bid, t in idx.items():
        if bid in used: continue
        cn = norm(t)
        if len(cn) < 4: continue
        exact = (n == cn); contain = (n in cn or cn in n)
        if not (exact or contain): continue
        extra = [w for w in TENANT_WORDS if norm(w) in cn and norm(w) not in n]
        if extra and not exact:
            return None, 'テナント語ガード: ' + ','.join(extra)
        return 'https://www.asoview.com/base/%s/' % bid, t
    return None, 'インデックスに無し'

# ---------------- メイン ----------------
def spot_kind(s):
    if s.get('stay') is True or re.search(r'旅館|ホテル|リゾート|ペンション|民宿|別邸|お宿|の宿|温泉宿',
                                          (s.get('genre') or '') + s['name']):
        return 'stay'
    if s.get('category') == 'play':
        return 'play'
    return 'gourmet'

def main():
    args = sys.argv[1:]
    apply_it = '--apply' in args
    sp = json.load(io.open(MAP, encoding='utf-8'))
    by = {s['id']: s for s in sp}
    idx = {b: clean_aso(t) for b, t in json.load(io.open(AIDX, encoding='utf-8')).items() if clean_aso(t)}
    used = {str(s.get('asoview', '')).split('/')[-2] for s in sp if s.get('asoview')}

    if '--ids' in args:
        ids = args[args.index('--ids')+1:]
        ids = [i for i in ids if not i.startswith('--')]
        targets = [by[i] for i in ids if i in by]
    elif '--sweep' in args:
        kind = args[args.index('--sweep')+1]
        limit = int(args[args.index('--limit')+1]) if '--limit' in args else 20
        targets = [s for s in sp if spot_kind(s) == kind
                   and not s.get('tabelog') and not s.get('booking') and not s.get('asoview')
                   and not s.get('wish')][:limit]     # 赤ピン優先(訪問済み=動画導線がある)
    else:
        print(__doc__); return

    results = []
    for s in targets:
        kind = spot_kind(s)
        if kind == 'gourmet' and not s.get('tabelog'):
            url, note = find_tabelog(s); field = 'tabelog'
        elif kind == 'stay' and not s.get('booking'):
            url, note = find_jalan(s); field = 'booking'
        elif kind == 'play' and not s.get('asoview'):
            url, note = find_asoview(s, idx, used); field = 'asoview'
            if url: used.add(url.split('/')[-2])
        else:
            results.append((s['id'], s['name'], '-', 'リンク済み', None)); continue
        results.append((s['id'], s['name'], field, note, url))
        time.sleep(SLEEP)

    print('=== 照合結果 (%s) ===' % ('書き込み' if apply_it else 'ドライラン'))
    n_ok = 0
    for sid, name, field, note, url in results:
        mark = '○' if url else '×'
        print(' %s %-16s %-26s %-8s %s' % (mark, sid[:16], name[:26], field, url or note))
        if url: n_ok += 1
    print('付与可能 %d / %d件' % (n_ok, len(results)))

    if apply_it and n_ok:
        shutil.copy(MAP, MAP + '.bak_monetize')
        for sid, name, field, note, url in results:
            if url: by[sid][field] = url
        io.open(MAP, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print('spots.json に書き込みました(バックアップ: .bak_monetize)')

if __name__ == '__main__':
    main()
