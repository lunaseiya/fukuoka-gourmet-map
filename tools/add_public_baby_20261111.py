# -*- coding: utf-8 -*-
"""おむつ替え・授乳室のある公共施設を登録する(2026-11-11・ユーザー要望
「そぴあしんぐうや市の建物にはおむつ替えシートがある可能性がある。調べて登録。分からないものは分からないでいい」)。

  python tools/add_public_baby_20261111.py <public_facilities.json> [--apply]

- 入力は自治体の「赤ちゃんの駅」一覧や施設公式で確認できた施設だけ(diaper か nursing が true)
- 既に登録済みの施設(名前が一致)は kids.diaper / kids.nursing と points を足すだけ
- 新規は utility:true の青ピンで登録する。utility はふだんのタブには出ず、
  検索と「📍→最寄りのおむつ替え・授乳室」から開いたときだけ地図に出る(map/index.html applyFilters)
- 座標は geocoding.jp(10秒間隔)。福岡県の範囲から外れたものは登録しない
"""
import hashlib
import unicodedata
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
CACHE = os.path.join(os.path.dirname(SRC), '_geo_cache.json')
TODAY = '2026-11-11'


def norm(s):
    # ⚠町名は消さない(「新宮町立図書館」と「粕屋町立図書館」が同じになって取り違えた・2026-11-11)
    return re.sub(r'[\s　・･()（）「」\-ー]', '', s or '').lower()


def geocode(addr, cache):
    if addr in cache:
        return cache[addr]
    for q in (addr, re.sub(r'(\d+)-(\d+)', r'\1丁目\2', addr, count=1)):
        url = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(q)
        try:
            xml = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'replace')
        except Exception:
            xml = ''
        time.sleep(10)
        la, ln = re.search(r'<lat>([\d.]+)</lat>', xml), re.search(r'<lng>([\d.]+)</lng>', xml)
        if la and ln and float(la.group(1)) > 1:
            cache[addr] = [round(float(la.group(1)), 6), round(float(ln.group(1)), 6)]
            json.dump(cache, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
            return cache[addr]
    return None


spots = json.load(open(P, encoding='utf-8'))
src = json.load(open(SRC, encoding='utf-8'))
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
byn = {}
for s in spots:
    if s.get('pref') == '福岡県' and not s['id'].startswith('ev-') and not s.get('until'):
        byn.setdefault(norm(s['name']), s)

upd, new, bad, seen = [], [], [], set()
for f in src['facilities']:
    k = norm(f['name'])
    k2 = norm(re.sub(r'[（(].*$', '', f['name']))
    if k in seen:
        continue
    seen.add(k)
    hit = byn.get(k) or byn.get(k2) or next((s for n, s in byn.items() if len(k2) >= 5 and (k2 in n or (len(n) >= 5 and n in k2)) and s.get('city') == f.get('city')), None)
    src_label = {'赤ちゃんの駅一覧': '自治体の「赤ちゃんの駅」一覧', '施設公式': '施設の公式サイト', '自治体公式': '自治体の公式サイト'}.get(f.get('source_kind'), '公式サイト')
    pts = []
    if f.get('diaper') is True:
        pts.append('おむつ替えあり' + (f'({f["diaper_where"]})' if f.get('diaper_where') else ''))
    if f.get('nursing') is True:
        pts.append('授乳室あり' + (f'({f["nursing_where"]})' if f.get('nursing_where') else ''))
    if f.get('hot_water') is True:
        pts.append('ミルク用のお湯あり')
    if f.get('kids_space') is True:
        pts.append('キッズスペースあり')
    if hit:
        kd = hit.get('kids') or {}
        if f.get('diaper') is True and kd.get('diaper') is None:
            kd['diaper'] = True
        if f.get('nursing') is True and kd.get('nursing') is None:
            kd['nursing'] = True
        hit['kids'] = kd
        have = ' '.join(hit.get('points') or [])
        add = [p for p in pts if p.split('(')[0] not in have]
        if add:
            hit['points'] = (hit.get('points') or []) + [p + f'({src_label})' if '(' not in p else p for p in add]
        upd.append((hit['id'], hit['name'], f['name']))
        continue
    addr = f.get('address') or ''
    if not addr.startswith('福岡県'):
        addr = '福岡県' + addr
    addr_q = unicodedata.normalize('NFKC', addr).replace('−', '-').replace('－', '-')
    m_ = re.match(r'^(.*?\d+(?:丁目)?(?:[-番]\d+)*(?:号)?)', addr_q)   # 番地より後ろ(ビル名・階)は落とす
    addr_q = m_.group(1) if m_ else re.sub(r'\s.*$', '', addr_q)
    sid = 'pub-' + hashlib.sha1((f['name'] + (f.get('city') or '')).encode('utf-8')).hexdigest()[:10]
    if any(x['id'] == sid for x in spots):
        continue
    g = geocode(addr_q, cache) if len(addr) > 8 else None
    if not g or not (33.3 <= g[0] <= 34.0 and 130.0 <= g[1] <= 130.8):
        bad.append((f['name'], addr, g)); continue
    what = '・'.join(x for x in ['おむつ替え' if f.get('diaper') is True else '', '授乳室' if f.get('nursing') is True else ''] if x)
    tail = ' '.join(x for x in [
        ('利用時間 ' + f['hours'] + '。') if f.get('hours') else '',
        ('休み ' + f['closed'] + '。') if f.get('closed') else '',
        ('TEL ' + f['tel'] + '。') if f.get('tel') else '',
        f'⚠{src_label}で確認した内容で、現地ではまだ確認していない。'] if x)
    city = f.get('city') or ''
    s = {
        'id': 'pub-' + hashlib.sha1((f['name'] + city).encode('utf-8')).hexdigest()[:10],
        'name': f['name'], 'area': '', 'city': city, 'pref': '福岡県',
        'genre': (f.get('kind') or '公共施設') + '(公共施設)', 'lat': g[0], 'lng': g[1], 'address': addr,
        'visited': None, 'with': 'family',
        'kids': {'stroller': None, 'diaper': True if f.get('diaper') is True else None,
                 'nursing': True if f.get('nursing') is True else None,
                 'kidsSpace': True if f.get('kids_space') is True else None,
                 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
        'verdict': f'{what}が使える公共施設({src_label}より)。' + ' '.join(p + '。' for p in pts) + ' ' + tail,
        'video': {'youtube': None, 'tiktok': None, 'instagram': None},
        'thumb': None, 'wish': True, 'web': f.get('web') or f.get('source'), 'category': 'play', 'utility': True,
        'ages': ['baby', 'toddler'], 'ages_src': 'auto',
        'points': pts + ['⚠ 現地未確認(' + src_label + 'より)'],
        'memo': f'{what}が使える公共施設。お出かけの途中の立ち寄りに。' + (f'利用時間 {f["hours"]}。' if f.get('hours') else ''),
        'added': TODAY,
    }
    spots.append(s); new.append((s['id'], s['name'], city))

print('既存を更新', len(upd)); [print('  ', u) for u in upd]
print('新規', len(new)); [print('  ', n) for n in new[:400]]
print('座標が取れない/範囲外', len(bad)); [print('  ', b) for b in bad]
ids = [s['id'] for s in spots]
assert len(ids) == len(set(ids)), 'id重複'
if APPLY:
    json.dump(spots, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('spots.json を書いた')
