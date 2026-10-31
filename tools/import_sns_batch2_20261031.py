# -*- coding: utf-8 -*-
"""Instagramの子連れ発信者5人+タグから拾った設備情報(投稿本文で「あり」を確認したものだけ)を青ピンで登録(2026-10-31)。
   投稿URLは data/SNS情報台帳.json にだけ持つ。表示は「Instagramの投稿より(未確認)」。
   対象はマップの範囲(飲食・遊び場・公園・施設・宿)に限定。住宅展示場・物販・プールのおむつ規定だけの投稿は除外"""
import io, json, os, re, sys, time, hashlib, urllib.request, urllib.parse, shutil
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json'); L = os.path.join(R, 'data', 'SNS情報台帳.json')
spots = json.load(io.open(P, encoding='utf-8')); by = {s['id']: s for s in spots}
ledger = json.load(io.open(L, encoding='utf-8'))
NEW = [
 # name, address, pref, city, area, genre, category, feats(あり確認済み), kids, src, post, year
 ('由布院温泉グランピング 風の響き', '大分県由布市湯布院町川上1314-1', '大分県', '由布市', '湯布院', 'グランピング', 'stay',
  ['ハイチェア・ベビーソープの貸出あり', 'おもちゃ貸出あり'], {'kidsChair': True}, '@fumi_odekake', 'C9eyjFKyoCi', '2024'),
 ('きっずゆうえんち ぐるぐるや 筑紫野店', '福岡県筑紫野市塔原東5-11-5', '福岡県', '筑紫野市', '塔原東', '室内遊び場', 'play',
  ['キッズチェア・バウンサーあり', '乳幼児コーナー・おむつ交換台・授乳室あり', '飲食の持ち込みOK', '大型遊具・ゲームコーナーあり'], {'kidsChair': True, 'diaper': True}, '@fumi_odekake', 'C9RxW5jy7By', '2024'),
 ('Wenavillage(ウェナヴィレッジ)くじゅう', '大分県玖珠郡九重町田野1685-3', '大分県', '玖珠郡九重町', '九重', 'グランピング', 'stay',
  ['お子様メニューあり'], {'kidsMenu': True}, '@fumi_odekake', 'C53AP3fSfGu', '2024'),
 ('三瀬ルベール牧場 どんぐり村', '佐賀県佐賀市三瀬村杠2234-67', '佐賀県', '佐賀市', '三瀬', '牧場・観光農園', 'play',
  ['授乳室・おむつ替えコーナーあり', '飲食の持ち込みOK'], {'diaper': True}, '@fumi_odekake', 'C4uz3jJy1hl', '2024'),
 ('caffel ひなのさと', '大分県日田市隈1-3-8', '大分県', '日田市', '日田', '旅館', 'stay',
  ['個室でくつろげる', '漫画・おもちゃの貸出あり'], {}, '@fumi_odekake', 'C2jwfTlyY2c', '2024'),
 ('道の駅うきは', '福岡県うきは市浮羽町山北729-2', '福岡県', 'うきは市', '浮羽', '道の駅', 'play',
  ['授乳室あり', '子供サイズのトイレあり'], {}, '@fumi_odekake', 'CyVZiV0JeGp', '2023'),
 ('あまぎ水の文化村', '福岡県朝倉市矢野竹1819', '福岡県', '朝倉市', '甘木', '水遊び・公園', 'play',
  ['授乳室・オムツ替えシートあり', '駐車場無料(約250台)', '⚠ 平日は基本的に休み(要確認)'], {'diaper': True}, '@naco_fukuoka_odekake', 'DXc_qVIE2DN', '2026'),
 ('フォレスタ阿蘇車帰', '熊本県阿蘇市車帰361-1', '熊本県', '阿蘇市', '阿蘇', 'グランピング', 'stay',
  ['お子様メニューあり'], {'kidsMenu': True}, '@weekend_outdoor_family', 'DO1syTEE9KL', '2026'),
 ('太陽ハーモニーファーム', '福岡県豊前市四郎丸2024-1', '福岡県', '豊前市', '豊前', '観光農園', 'play',
  ['授乳室あり', 'おむつ替えスペースあり', '野外遊具あり'], {'diaper': True}, '@fukuoka_odekake_kyouiku', 'Ddq5gFrSepP', '2026'),
 ('OLIP アサイーボウル&サラダボウル 赤坂店', '福岡県福岡市中央区赤坂3-6-37 102', '福岡県', '福岡市中央区', '赤坂', 'カフェ', 'gourmet',
  ['キッズスペースあり'], {}, '@fukuoka_odekake_kyouiku', 'DYa28idEkRD', '2026'),
 ('築上町図書館 築きのもり', '福岡県築上郡築上町築城1096', '福岡県', '築上郡築上町', '築城', '図書館', 'play',
  ['キッズスペースあり', '読み聞かせ室・授乳室・親子トイレあり'], {}, '@fukuoka_odekake_kyouiku', 'DU2wmBcEbW_', '2026'),
 ('ひばる子どもプラザ ひつじのおうち', '福岡県福岡市南区桧原2-36-15', '福岡県', '福岡市南区', '桧原', '子どもプラザ(子育て支援施設)', 'play',
  ['赤ちゃん専用の部屋あり', '授乳コーナーあり'], {}, '施設公式(@plaza_hitsujinoouti)', 'DabjGWggWcd', '2026'),
]
UPD = {'芦屋海浜公園わんぱーく': 'オムツ替え台等あり・無料(Instagramの投稿より・未確認)',
       'アミューズメントパーク万代 宗像店': 'キッズスペースあり(Instagramの投稿より・未確認)'}
CAT = {'stay': '宿', 'play': '施設', 'gourmet': '店'}


def geocode(q):
    cands = [q, re.sub(r'\s.*$', '', q), re.sub(r'(\d+)[-−ー](\d+)[-−ー]\d+.*$', r'\1-\2', q)]
    for n, c in enumerate(dict.fromkeys(cands)):
        if n:
            time.sleep(10)
        u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(c)
        try:
            x = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8', 'ignore')
        except Exception as e:
            print('  err', e); continue
        la = re.search(r'<lat>([\d.]+)</lat>', x); ln = re.search(r'<lng>([\d.]+)</lng>', x)
        if la and ln and float(la.group(1)) > 1:
            return float(la.group(1)), float(ln.group(1))
    return None, None


added = []
for (nm, ad, pref, city, area, gen, cat, feats, kids, src, code, yr) in NEW:
    sid = 'ig' + hashlib.md5(nm.encode('utf-8')).hexdigest()[:10]
    if sid in by or any(nm[:6] in s['name'] for s in spots):
        print('skip(既存)', nm); continue
    lat, lng = geocode(ad); time.sleep(10)
    print(('OK ' if lat else 'NG ') + nm, lat, lng)
    if not lat:
        continue
    k = {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None}; k.update(kids)
    note = '⚠ Instagramの投稿より(%s年時点・未確認)' % yr
    clean = [f.replace('⚠ ', '') for f in feats]
    spots.append({'id': sid, 'name': nm, 'area': area, 'city': city, 'pref': pref, 'genre': gen, 'lat': lat, 'lng': lng, 'address': ad,
        'visited': None, 'with': 'family', 'category': cat, 'wish': True, 'kids': k, 'points': feats + [note],
        'memo': 'Instagramの子連れおでかけ投稿(%s年)より。%s。設備は現地未確認。' % (yr, '、'.join(clean[:3])),
        'verdict': 'Instagramの子連れおでかけ投稿(%s年時点)に「%s」とあった%s。当方は未訪問で設備は未確認。行ったら確認して更新します。' % (yr, '・'.join(clean), CAT[cat]),
        'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None, 'photos': None, 'source': 'instagram:' + src})
    by[sid] = spots[-1]; added.append(nm)
    ledger.append({'name': nm, 'address': ad, 'feats': feats, 'src': 'instagram:' + src, 'post': 'https://www.instagram.com/p/%s/' % code, 'posted_year': yr, 'map_match': sid})
for nm, line in UPD.items():
    s = next((x for x in spots if x['name'] == nm), None)
    if s and not any('Instagram' in p for p in (s.get('points') or [])):
        s['points'] = (s.get('points') or []) + [line]; print('追記', nm)
shutil.copy(P, P + '.bak_sns2')
ids = [x['id'] for x in spots]; assert len(ids) == len(set(ids))
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
io.open(L, 'w', encoding='utf-8').write(json.dumps(ledger, ensure_ascii=False, indent=1))
print('追加', len(added), added)
