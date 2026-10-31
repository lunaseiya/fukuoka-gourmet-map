# -*- coding: utf-8 -*-
"""Instagram @kodomoto_cafe(福岡の子連れカフェ紹介・2023〜24年の投稿)のキャプションから拾った設備情報を
   青ピン(未訪問・未確認)でマップに入れる(2026-10-31 ユーザー確定「やっちゃいましょう」)。
   - 元データ: data/SNS情報台帳.json(投稿URLはここだけに持つ。マップには出さない=ユーザー判断 2026-10-31)
   - 表示は points/memo に「Instagramの投稿より(2023〜24年時点・未確認)」。kids の True は投稿に明記があるものだけ
   - 座標: geocoding.jp(10秒間隔)。既にマップにある店は points に1行足すだけ
   python tools/import_sns_kodomoto_20261031.py [--dry]"""
import io, json, os, re, sys, time, hashlib, urllib.request, urllib.parse, shutil
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
L = os.path.join(R, 'data', 'SNS情報台帳.json')
DRY = '--dry' in sys.argv
NOTE = '⚠ Instagramの投稿より(2023〜24年時点・未確認)'

recs = json.load(io.open(L, encoding='utf-8'))
spots = json.load(io.open(P, encoding='utf-8'))
by_id = {s['id']: s for s in spots}

SKIP = {'Moff animal cafe', '文喫 福岡天神', 'グランダイニング(ららぽーと福岡)'}   # 設備情報なし / 住所不足 / フードコート名
PARENT = {'E PRONTO ミーナ天神店': 'minatenjin', '&LOCALS 大濠公園': 'ohori-park',
          'タリーズコーヒー 福岡空港店': None, 'HONEY COFFEE 志免店': None, 'TSUTAYA BOOK GARAGE 福岡志免': None}
# 既存スポットに points を足すだけのもの(台帳の map_match で id が分かっているもの)
EXISTING = {'筥崎鳩太郎商店': 'hakozakihatotaroushouten', 'タリーズコーヒー 福岡空港店': 'apdd20f93826',
            'YOSHIMI 福岡空港店': 'apa6a48bc979', 'ファミリーガーデン大野城': 'hp6a2219f65c',
            'Soup Stock Tokyo 天神': 'tenchika_28', 'HAMORU CAFE': 'sp758403f6c3'}


def geocode(addr):
    q = '福岡県' + addr if not re.match(r'^(福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|山口県)', addr) else addr
    if addr.startswith('佐賀市'): q = '佐賀県' + addr
    cands = [q, re.sub(r'\s.*$', '', q)]
    m = re.match(r'(.*?[市区町村].*?[0-9０-９][0-9０-９\-ー丁目番地の]*[0-9０-９])', q)
    if m: cands.append(m.group(1))
    for n, c in enumerate(dict.fromkeys(cands)):
        if n: time.sleep(10)
        u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(c)
        try:
            x = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8', 'ignore')
        except Exception as e:
            print('   geocode error', e); continue
        la = re.search(r'<lat>([\d.]+)</lat>', x); ln = re.search(r'<lng>([\d.]+)</lng>', x)
        if la and ln and float(la.group(1)) > 1: return float(la.group(1)), float(ln.group(1)), c
    return None, None, None


def area_city(addr):
    m = re.search(r'(福岡市|北九州市)(\S+?区)', addr)
    if m: city = m.group(1) + m.group(2)
    else:
        m2 = re.search(r'(糟屋郡\S+?町|嘉穂郡\S+?町|\S+?市)', addr); city = m2.group(1) if m2 else ''
    rest = addr.replace('福岡県', '').replace('佐賀県', '')
    if city: rest = rest.split(city, 1)[-1] if city in rest else rest
    a = re.sub(r'[0-9０-９].*$', '', rest).strip() or city
    return a, city


def genre(name, feats):
    n = name.lower()
    if 'ブック' in name or 'tsutaya' in n or '文喫' in name: return '本屋カフェ'
    if '食堂' in name: return '食堂'
    if 'レストラン' in name or 'restaurant' in n or 'ダイニング' in name or 'キッチン' in name: return 'レストラン'
    if 'サンドイッチ' in name or 'sandwich' in n: return 'サンドイッチ'
    return 'カフェ'


def kids_from(feats):
    f = ' '.join(feats)
    k = {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None}
    if re.search(r'キッズチェア|ベビーチェア', f): k['kidsChair'] = True
    if re.search(r'ベビーカー(入店)?OK', f): k['stroller'] = True
    if re.search(r'(おむつ|オムツ)(替え|交換)台あり', f) and not re.search(r'施設内', f): k['diaper'] = True
    if 'キッズメニュー' in f: k['kidsMenu'] = True
    return k


added, updated = [], []
for r in recs:
    nm = r['name']
    if nm in SKIP: continue
    if nm in EXISTING:
        s = by_id[EXISTING[nm]]
        line = '、'.join(r['feats'])[:60] + '(Instagramの投稿より・2023〜24年時点・未確認)'
        pts = s.get('points') or []
        if not any('Instagram' in p for p in pts):
            s['points'] = pts + [line]; updated.append(s['name'])
        continue
    if r.get('map_match') and nm not in PARENT: continue   # 施設名に当たっただけのもの(ららぽーと等)は上で SKIP 済み
    sid = 'ig' + hashlib.md5(nm.encode('utf-8')).hexdigest()[:10]
    if sid in by_id: continue
    area, city = area_city(r['address'])
    pref = '佐賀県' if r['address'].startswith('佐賀') else '福岡県'
    if DRY:
        lat = lng = None; used = '(dry)'
    else:
        lat, lng, used = geocode(r['address']); time.sleep(10)
    print(('OK ' if lat else 'NG ') + nm, '|', city, area, '|', lat, lng, '|', used)
    if not lat and not DRY: continue
    feats = r['feats']
    hours = ('営業 ' + r['hours'] + '(投稿時点)。') if r.get('hours') else ''
    spot = {'id': sid, 'name': nm, 'area': area, 'city': city, 'pref': pref, 'genre': genre(nm, feats),
            'lat': lat, 'lng': lng, 'address': (pref if not r['address'].startswith(pref) else '') + r['address'],
            'visited': None, 'with': 'family', 'category': 'gourmet', 'wish': True, 'kids': kids_from(feats),
            'points': feats + [NOTE],
            'memo': 'Instagramの子連れカフェ紹介の投稿(2023〜24年)より。' + '、'.join(feats[:4]) + '。設備は現地未確認。',
            'verdict': 'Instagramの子連れカフェ紹介の投稿(2023〜24年時点)に「' + '・'.join(feats) + '」とあった店。'
                       '当方は未訪問で設備は未確認。' + hours + '行ったら確認して更新します。',
            'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None, 'photos': None,
            'source': 'instagram:@kodomoto_cafe'}
    if PARENT.get(nm): spot['in'] = PARENT[nm]
    spots.append(spot); by_id[sid] = spot; added.append(nm)

print('追加', len(added), '/ 既存に追記', len(updated), updated)
if not DRY:
    shutil.copy(P, P + '.bak_sns_kodomoto')
    ids = [x['id'] for x in spots]; assert len(ids) == len(set(ids))
    io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
    print('saved')
