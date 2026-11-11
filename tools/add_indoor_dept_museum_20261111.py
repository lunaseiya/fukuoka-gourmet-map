# -*- coding: utf-8 -*-
"""デパートと展示会場(美術館・博物館)を館内モード用に登録する(2026-11-11・ユーザー要望
「展示に行ったとき世話になるのはデパート。授乳室・おむつ替えの場所を登録したい」)。

  python tools/add_indoor_dept_museum_20261111.py <newspots*.json のフォルダ> [--apply]

- newspots_*.json(公式サイトで確認した基本情報)から spots.json に施設スポットを足す(青ピン=未訪問)
- 座標は geocoding.jp で住所から引く(10秒間隔)。県の範囲から外れたら止める
- children に書かれた既存スポットに in=<施設id> を付ける(既に別の in がある店は触らない)
- 設備の階と図は別ツール(indoor_merge.py / indoor_plans_merge.py)で取り込む
"""
import glob
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = sys.argv[1]
APPLY = '--apply' in sys.argv
SKIP = {'solaria-stage'}   # 公式に子連れ設備の記載もフロア図も無い → 登録しない
CACHE = os.path.join(SRC, '_geo_cache.json')
BOX = {'福岡県': (33.0, 34.3, 129.9, 131.3), '佐賀県': (32.9, 33.7, 129.7, 130.6), '長崎県': (32.5, 34.8, 128.5, 130.5),
       '熊本県': (32.0, 33.3, 129.9, 131.4), '大分県': (32.7, 33.8, 130.8, 132.2), '宮崎県': (31.3, 32.9, 130.6, 132.0),
       '鹿児島県': (27.0, 32.4, 128.3, 131.3), '山口県': (33.7, 34.9, 130.7, 132.5)}


def geocode(addr, cache):
    if addr in cache:
        return cache[addr]
    url = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(addr)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    xml = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
    la, ln = re.search(r'<lat>([\d.]+)</lat>', xml), re.search(r'<lng>([\d.]+)</lng>', xml)
    time.sleep(10)
    if not (la and ln):
        return None
    cache[addr] = [round(float(la.group(1)), 6), round(float(ln.group(1)), 6)]
    json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    return cache[addr]


spots = json.load(open(P, encoding='utf-8'))
by = {s['id']: s for s in spots}
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
results = {}
for f in glob.glob(os.path.join(SRC, 'result*.json')):
    results.update(json.load(open(f, encoding='utf-8')).get('done') or {})

added, linked, bad = [], 0, []
for f in sorted(glob.glob(os.path.join(SRC, 'newspots*.json'))):
    for n in json.load(open(f, encoding='utf-8')):
        fid = n['id']
        if fid in SKIP or fid in by:
            continue
        addr = n['address'] if n['address'].startswith(n['pref']) else n['pref'] + n['address']
        g = geocode(re.sub(r'\s.*$', '', addr), cache)
        b = BOX.get(n['pref'])
        if not g or (b and not (b[0] <= g[0] <= b[1] and b[2] <= g[1] <= b[3])):
            bad.append((fid, addr, g)); continue
        res = results.get(fid, {})
        am = ' '.join((a.get('kind', '') + a.get('where', '')) for a in res.get('amenities', []))
        tail = ' '.join(x for x in [
            ('営業 ' + n['hours'] + '。') if n.get('hours') else '',
            ('休み ' + n['closed'] + '。') if n.get('closed') else '',
            ('TEL ' + n['tel'] + '。') if n.get('tel') else '',
            '⚠子連れ設備は公式サイトで確認した内容で、現地ではまだ確認していない。'] if x)
        s = {
            'id': fid, 'name': n['name'], 'area': n.get('area') or '', 'city': n['city'], 'pref': n['pref'],
            'genre': n['genre'], 'lat': g[0], 'lng': g[1], 'address': addr,
            'visited': None, 'with': 'family',
            'kids': {'stroller': True if 'ベビーカー' in am else None,
                     'diaper': True if re.search('おむつ|ベビー休憩|ベビールーム', am) else None,
                     'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
            'verdict': (n.get('memo') or '') + ' ' + tail,
            'video': {'youtube': None, 'tiktok': None, 'instagram': None},
            'thumb': None, 'wish': True, 'web': n.get('web'), 'category': 'play',
            'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'auto',
            'floormap': res.get('floormap') or None,
            'points': (n.get('points') or []) + ['⚠ 子連れ設備は現地未確認(公式サイトより)'],
            'memo': n.get('memo') or '',
        }
        spots.append(s); by[fid] = s; added.append(fid)
        for cid in n.get('children') or []:
            c = by.get(cid)
            if c and not c.get('in') and cid != fid:
                c['in'] = fid; linked += 1

print('追加', len(added), added)
print('in を付けた既存スポット', linked)
print('座標が取れない/範囲外', bad)
if APPLY and not bad:
    json.dump(spots, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('spots.json を書いた')
elif APPLY:
    print('⚠ 座標の問題があるので書かなかった')
