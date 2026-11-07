# -*- coding: utf-8 -*-
"""batch3 で近傍判定が誤って「重複」にした2件と、住所で位置が取れなかった1件を足す(2026-11-08)。"""
import io, json, os, re, sys, time, hashlib, urllib.request, urllib.parse, shutil, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json'); L = os.path.join(R, 'data', 'SNS情報台帳.json')
TODAY = datetime.date.today().isoformat()
C = [
 ('オールデイダイニング カメリア(ホテルオークラ福岡)', '福岡県福岡市博多区下川端町3-2', '福岡県', '福岡市博多区', '下川端町', 'ホテルのビュッフェ', 'gourmet', {}, ['小学生3,500円・4〜6歳1,200円・4歳未満無料', '夏休みは子ども料金の割引あり(要予約)'], None, None, 'yumehapi', 'Dbg5nPmTuRS', 'ホテルオークラ福岡'),
 ('昭和の森(一本松公園)川遊び場', '福岡県糟屋郡宇美町宇美', '福岡県', '糟屋郡宇美町', '宇美', '川遊び', 'play', {}, ['小さな滝と天然プールで川遊び', '駐車場から近い(3時間以内無料)'], None, None, 'yuimei', 'DcUZkWVz3ME', '一本松公園 宇美町'),
]
spots = json.load(io.open(P, encoding='utf-8')); ledger = json.load(io.open(L, encoding='utf-8'))


def geo(q):
    u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(q)
    x = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8', 'ignore')
    la = re.search(r'<lat>([\d.]+)</lat>', x); ln = re.search(r'<lng>([\d.]+)</lng>', x)
    return (float(la.group(1)), float(ln.group(1))) if la and ln and float(la.group(1)) > 1 else (None, None)


added = []
for (nm, ad, pref, city, area, gen, cat, kids, pts, stay, day, acc, code, q) in C:
    lat, lng = geo(q or ad); time.sleep(10)
    if not lat:
        print('NG', nm); continue
    sid = 'sn' + hashlib.md5(nm.encode('utf-8')).hexdigest()[:10]
    assert sid not in {s['id'] for s in spots}
    k = {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None}; k.update(kids)
    kind = {'onsen': '宿・温泉', 'play': '施設', 'gourmet': 'お店'}[cat]
    rec = {'id': sid, 'name': nm, 'area': area, 'city': city, 'pref': pref, 'genre': gen, 'lat': lat, 'lng': lng, 'address': ad,
           'visited': None, 'with': 'family', 'category': cat, 'wish': True, 'kids': k,
           'points': pts + ['⚠ 未訪問のため設備・料金は未確認(行ったら更新します)'],
           'memo': '行ってみたい%sとして登録。%s。当方は未訪問で、設備や料金は未確認です。' % (kind, '、'.join(pts[:2])),
           'verdict': '未訪問の%s。%s。設備・料金・営業日は変わることがあるので、行く前に公式で確認してください。' % (kind, '・'.join(pts)),
           'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None, 'photos': None,
           'source': 'sns:' + acc, 'added': TODAY}
    if q: rec['geo_approx'] = True
    spots.append(rec); added.append(sid)
    ledger.append({'name': nm, 'address': ad, 'feats': pts, 'src': 'instagram:@' + acc, 'post': 'https://www.instagram.com/p/%s/' % code,
                   'posted_year': '2025-2026', 'map_match': sid, 'imported': TODAY})
    print('OK', nm, lat, lng)
shutil.copy(P, P + '.bak_sns3fix')
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
io.open(L, 'w', encoding='utf-8').write(json.dumps(ledger, ensure_ascii=False, indent=1))
f = os.path.join(R, 'data', '_sns3_added_ids.txt')
io.open(f, 'w', encoding='utf-8').write((io.open(f, encoding='utf-8').read() + ' ' + ' '.join(added)).strip())
print('追加', len(added))
