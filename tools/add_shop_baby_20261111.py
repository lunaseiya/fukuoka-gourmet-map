# -*- coding: utf-8 -*-
"""スーパー・専門店・自治体の「赤ちゃんの駅」登録店の、おむつ替え・授乳室・子供乗せカートを登録する(2026-11-11)。

  python tools/add_shop_baby_20261111.py <shops_*.json のフォルダ> [--apply]

ユーザーの決めごと(2026-11-11):
- **店舗ごとの記載だけを信用する**(チェーン公式の店舗ページ・自治体一覧のその店の行)。公式にあれば確定でよい
- チェーン共通の説明を全店舗に当てはめない(入力の時点で店舗ごとに確認できた店だけが入っている)
- 現地で「ない」と確認した店は data/設備の現地確認台帳.json が優先(台帳で false の項目は true にしない)

登録の形:
- 既に登録済みの施設(名前一致、または館内モードのある施設から80m以内で名前が似ている)は kids と points を足すだけ
- 新規は utility:true の青ピン。ふだんのタブには出ず、検索と「📍→最寄りのおむつ替え・授乳室」から開いたときだけ出る
- 座標は入力にあればそれを使い、無ければ geocoding.jp(10秒間隔)。福岡県の範囲外は登録しない
"""
import glob
import hashlib
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = sys.argv[1]
APPLY = '--apply' in sys.argv
CACHE = os.path.join(SRC, '_geo_cache.json')
TODAY = '2026-11-11'
FLAGS = ('diaper', 'nursing', 'cart', 'kids_space', 'hot_water', 'kids_toilet')
KEYMAP = {'diaper': 'diaper', 'nursing': 'nursing', 'cart': 'cart', 'kids_space': 'kidsSpace'}


def norm(s):
    return re.sub(r'[\s　・･()（）「」\-ー/／]', '', unicodedata.normalize('NFKC', s or '')).lower()


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 111000 * math.cos(math.radians(a[0])))


def geocode(addr, cache):
    q = unicodedata.normalize('NFKC', addr).replace('−', '-').replace('－', '-')
    m = re.match(r'^(.*?\d+(?:丁目)?(?:[-番]\d+)*(?:号)?)', q)
    q = m.group(1) if m else re.sub(r'\s.*$', '', q)
    if q in cache:
        return cache[q]
    for qq in (q, re.sub(r'(\d+)-(\d+)', r'\1丁目\2', q, count=1)):
        try:
            xml = urllib.request.urlopen(urllib.request.Request(
                'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(qq), headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'replace')
        except Exception:
            xml = ''
        time.sleep(10)
        la, ln = re.search(r'<lat>([\d.]+)</lat>', xml), re.search(r'<lng>([\d.]+)</lng>', xml)
        if la and ln and float(la.group(1)) > 1:
            cache[q] = [round(float(la.group(1)), 6), round(float(ln.group(1)), 6)]
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
            return cache[q]
    return None


spots = json.load(open(P, encoding='utf-8'))
indoor = json.load(open(os.path.join(ROOT, 'data', 'indoor.json'), encoding='utf-8'))
ledger = json.load(open(os.path.join(ROOT, 'data', '設備の現地確認台帳.json'), encoding='utf-8'))['entries']
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
byn, byid = {}, {s['id']: s for s in spots}
for s in spots:
    if s.get('pref') == '福岡県' and not s['id'].startswith('ev-') and not s.get('until'):
        byn.setdefault(norm(s['name']), s)
facs = [s for s in spots if s['id'] in indoor and s.get('lat')]

# 入力をまとめる(同じ店が複数の出どころにあれば、true を優先して1件に)
stores = {}
for f in sorted(glob.glob(os.path.join(SRC, 'shops_*.json'))):
    for st in json.load(open(f, encoding='utf-8')).get('stores', []):
        k = norm(st['name']) + '|' + (st.get('city') or '')
        if k in stores:
            o = stores[k]
            for fl in FLAGS:
                if st.get(fl) is True:
                    o[fl] = True
            for fld in ('diaper_where', 'nursing_where', 'lat', 'lng', 'hours', 'tel', 'web'):
                o[fld] = o.get(fld) or st.get(fld)
            o['source_kind'] = o.get('source_kind') if o.get('source_kind') == st.get('source_kind') else 'チェーン公式の店舗ページ・自治体の一覧'
        else:
            stores[k] = dict(st)

# ---- 立ち寄り用途に向かないものを外す(2026-11-11) ----
#   ・保育園/幼稚園・医療・整骨院・美容室・葬祭・住宅展示場などは「客や利用者として入る前提」なので載せない
#   ・県「子育て応援の店」は店舗の自己申告。買い物・食事で入れる業種(飲食・スーパー・ドラッグストア・ホームセンター・ベビー用品・商業施設・家電・ディスカウント)だけ採る
#   ・「保育園利用者対象」などの注記がある行は外す
NG_NAME = re.compile(r'保育|ほいく|幼稚園|こども園|子ども園|託児|ヤクルト|整骨|接骨|鍼灸|整体|歯科|医院|クリニック|病院|薬局|美容|サロン|ヘア|hair|紫雲閣|葬|斎場|霊園|会館$|学習塾|教室|展示場|不動産|ハウス|ホーム株|工務店|住宅|保険|銀行|信用金庫|郵便局|ホテル|旅館|写真|スタジオ|マッサージ', re.I)
OK_PREF_KIND = ('飲食', 'スーパー', 'ドラッグストア', 'ホームセンター', 'ベビー用品', '商業施設', '家電', 'ディスカウント')
dropped = 0
for k in list(stores):
    st = stores[k]
    sk = st.get('source_kind') or ''
    if NG_NAME.search(st['name']) or '利用者対象' in (st.get('note') or ''):
        del stores[k]; dropped += 1; continue
    if '応援の店' in sk and 'チェーン' not in sk and '赤ちゃんの駅' not in sk and not any(x in (st.get('kind') or '') for x in OK_PREF_KIND):
        del stores[k]; dropped += 1
GEO_ONLY = '--geocode-only' in sys.argv      # 座標だけ先に引いてキャッシュに貯める(10秒間隔で数時間かかるため)
CACHED_ONLY = '--cached-only' in sys.argv    # キャッシュに座標がある店だけ登録する(残りは次回)
print('対象', len(stores), '/ 業種・名称で外した', dropped)

upd, new, bad, held = [], [], [], []
for st in stores.values():
    name, city = st['name'], st.get('city') or ''
    # 現地確認の台帳が優先
    for e in ledger:
        if e.get('by') != 'ユーザー現地確認' or (e.get('city') or '') != city:
            continue
        key = re.sub(r'[（(].*$', '', e['name'])
        if e.get('spot_id') and byid.get(e['spot_id']) and norm(byid[e['spot_id']]['name']) == norm(name) or (key and norm(key) in norm(name)):
            for fl in ('diaper', 'nursing'):
                if e.get(fl) is False and st.get(fl) is True:
                    st[fl] = None; held.append((name, fl, '台帳で現地「なし」'))
    if not any(st.get(fl) is True for fl in ('diaper', 'nursing', 'cart')):
        continue
    sk = st.get('source_kind') or ''
    label = ('公式の店舗ページ・自治体の一覧' if 'チェーン' in sk and ('自治体' in sk or '応援の店' in sk) else
             '自治体の「赤ちゃんの駅」一覧' if '赤ちゃんの駅' in sk else
             '福岡県「子育て応援の店」の登録内容' if '応援の店' in sk else '公式の店舗ページ')
    pts = []
    if st.get('diaper') is True:
        pts.append('おむつ替えあり' + (f'({st["diaper_where"]})' if st.get('diaper_where') else ''))
    if st.get('nursing') is True:
        pts.append('授乳室あり' + (f'({st["nursing_where"]})' if st.get('nursing_where') else ''))
    if st.get('cart') is True:
        pts.append('子供乗せカートあり')
    if st.get('hot_water') is True:
        pts.append('ミルク用のお湯あり')
    if st.get('kids_space') is True:
        pts.append('キッズスペースあり')
    if st.get('kids_toilet') is True:
        pts.append('子供用トイレあり')
    k = norm(name)
    k2 = norm(re.sub(r'[（(].*$', '', name))
    hit = byn.get(k) or byn.get(k2)
    g = [st['lat'], st['lng']] if isinstance(st.get('lat'), (int, float)) and isinstance(st.get('lng'), (int, float)) else None
    if not hit and g:   # 館内モードのある施設のすぐそば(同じ建物)で名前が似ていれば、その施設にまとめる
        for fc in facs:
            if dist(g, (fc['lat'], fc['lng'])) <= 80:
                a, b = norm(fc['name']), k2
                core = re.sub(r'(店|ショッピングセンター|sc|モール)$', '', b)
                if core[:4] and (core[:4] in a) and (core[-3:] in a or a[-3:] in core):
                    hit = fc; break
    if hit:
        kd = hit.get('kids') or {}
        for fl, key in KEYMAP.items():
            if st.get(fl) is True and kd.get(key) is None:
                kd[key] = True
        hit['kids'] = kd
        have = ' '.join(hit.get('points') or []) + (hit.get('verdict') or '')
        add = [p for p in pts if p.split('(')[0].replace('あり', '') not in have]
        if add:
            hit['points'] = (hit.get('points') or []) + [f'{p}({label})' if '(' not in p else p for p in add]
        upd.append((hit['id'], hit['name'], name)); continue
    addr = st.get('address') or ''
    if addr and not addr.startswith('福岡県'):
        addr = '福岡県' + addr
    sid = 'shop-' + hashlib.sha1((name + city).encode('utf-8')).hexdigest()[:10]
    if sid in byid:
        continue
    if not g and not addr and st.get('city'):   # 住所の無い一覧(宗像市など)は 名称+市名 で引く
        addr = '福岡県' + city + ' ' + name
    if not g and len(addr) > 8:
        if CACHED_ONLY:
            q0 = unicodedata.normalize('NFKC', addr).replace('−', '-').replace('－', '-')
            m0 = re.match(r'^(.*?\d+(?:丁目)?(?:[-番]\d+)*(?:号)?)', q0)
            g = cache.get(m0.group(1) if m0 else re.sub(r'\s.*$', '', q0))
            if not g:
                continue
        else:
            g = geocode(addr, cache)
    if GEO_ONLY:
        continue
    if not g or not (33.0 <= g[0] <= 34.3 and 129.9 <= g[1] <= 131.3):
        bad.append((name, addr, g)); continue
    what = '・'.join(x for x in ['おむつ替え' if st.get('diaper') is True else '', '授乳室' if st.get('nursing') is True else '',
                                 '子供乗せカート' if st.get('cart') is True else ''] if x)
    tail = ' '.join(x for x in [('営業 ' + st['hours'] + '。') if st.get('hours') else '', ('TEL ' + st['tel'] + '。') if st.get('tel') else '',
                                f'⚠{label}の記載で、現地ではまだ確認していない。'] if x)
    s = {
        'id': sid, 'name': name, 'area': '', 'city': city, 'pref': '福岡県',
        'genre': (st.get('kind') if st.get('kind') and st.get('kind') != 'その他' else ('公共施設' if st.get('ownership') == '公共' else '立ち寄りスポット')), 'lat': round(g[0], 6), 'lng': round(g[1], 6), 'address': addr,
        'visited': None, 'with': 'family',
        'kids': {'stroller': None, 'diaper': True if st.get('diaper') is True else None,
                 'nursing': True if st.get('nursing') is True else None,
                 'cart': True if st.get('cart') is True else None,
                 'kidsSpace': True if st.get('kids_space') is True else None,
                 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
        'verdict': f'{what}がある店({label}より)。' + ' '.join(p + '。' for p in pts) + ' ' + tail,
        'video': {'youtube': None, 'tiktok': None, 'instagram': None},
        'thumb': None, 'wish': True, 'web': st.get('web') or st.get('source'),
        'category': 'gourmet' if '飲食' in (st.get('kind') or '') else 'play', 'utility': True,
        'ages': ['baby', 'toddler'], 'ages_src': 'auto',
        'points': pts + [f'⚠ 現地未確認({label}より)'],
        'memo': f'{what}がある店。買い物やお出かけの途中の立ち寄りに。',
        'added': TODAY,
    }
    spots.append(s); byid[sid] = s; byn.setdefault(k, s); new.append((sid, name, city, st.get('chain') or st.get('kind')))

print('入力', len(stores))
print('既存を更新', len(upd)); [print('  ', u) for u in upd]
print('新規', len(new))
import collections
print('  チェーン/種類別', collections.Counter(n[3] for n in new).most_common(40))
print('  市区別', collections.Counter(n[2] for n in new).most_common(40))
print('台帳で止めた', held)
print('座標が取れない/範囲外', len(bad)); [print('  ', b) for b in bad[:60]]
ids = [s['id'] for s in spots]
assert len(ids) == len(set(ids)), 'id重複'
if APPLY:
    json.dump(spots, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('spots.json を書いた')
