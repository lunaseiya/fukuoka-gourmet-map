# -*- coding: utf-8 -*-
"""2026-10-03 すぐ行ける版: event_to_map で位置が取れなかった3件を追加し、
   今回登録した期間限定イベントの name / verdict をカードと同じ表示名・memo に揃える"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = os.path.join(R, 'data', 'spots.json')
EX = json.load(io.open(os.path.join(R, 'data', '_イベント補足.json'), encoding='utf-8'))
DP = json.load(io.open(os.path.join(R, 'data', '_イベント表示名.json'), encoding='utf-8'))
SEL = json.load(io.open(os.path.join(R, 'data', '_週末イベント候補.json'), encoding='utf-8'))['selected']
shutil.copy(P, P + '.bak_1003mapfix')
s = json.load(io.open(P, encoding='utf-8')); ids = {x['id'] for x in s}

ADD = [  # (id, url, city, lat, lng, address, until, untilLabel)  位置は geocoding.jp / 既存スポットで確認
 ('ev-1866743-ogori', 'https://tenpo.aeon-kyushu.info/detail/ogori/event-news/1866743/', '小郡市',
  33.408759, 130.564828, '福岡県小郡市大保字弓場110', '2026-10-04', '10月4日'),
 ('ev-602195-kgg', 'https://iko-yo.net/events/602195', '北九州市八幡東区',
  33.87345, 130.811851, '福岡県北九州市八幡東区東田4-1-1(THE OUTLETS KITAKYUSHU)', '2026-10-31', '10月31日'),
 ('ev-274548-taiyo', 'https://yokanavi.com/events/274548', '福岡市中央区',
  33.591622, 130.404452, '福岡県福岡市中央区西中洲6-29(天神中央公園 貴賓館前広場)', '2026-10-04', '10月4日'),
]
for i, u, city, lat, lng, addr, until, ul in ADD:
    if i in ids:
        continue
    s.append({'id': i, 'name': '', 'area': '', 'city': city, 'pref': '福岡県', 'genre': '期間限定イベント',
              'lat': lat, 'lng': lng, 'address': addr, 'visited': None, 'with': 'family',
              'kids': {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
              'verdict': '', 'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None,
              'wish': True, 'category': 'play', 'until': until, 'untilLabel': ul, 'official': u})

n = 0
for x in s:
    u = x.get('official')
    if x.get('genre') != '期間限定イベント' or u not in SEL:
        continue
    d = DP.get(u) or {}; e = EX.get(u) or {}
    base = d.get('name') or x['name']
    multi = [y for y in s if y.get('official') == u and y.get('genre') == '期間限定イベント']
    if len(multi) > 1 and '（' in x['name']:          # 多館開催は館名を残す
        base = '%s（%s）' % (base, x['name'].rsplit('（', 1)[1].rstrip('）'))
    x['name'] = base
    det = e.get('detail') or []
    extra = [t for t in (e.get('time') and '時間 ' + e['time'], e.get('price') and '料金 ' + e['price'],
                         e.get('free') and '入場無料', e.get('note')) if t]
    if det:
        x['verdict'] = '⭐' + '。'.join(det) + '。' + ('　' + ' / '.join(extra) if extra else '')
    n += 1
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
bad = [x['id'] for x in s if x.get('genre') == '期間限定イベント' and x.get('official') in SEL
       and not (31.0 < (x.get('lat') or 0) < 34.9 and 128.5 < (x.get('lng') or 0) < 132.2)]
assert not bad, bad
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('整えた', n, '件')
for x in s:
    if x.get('genre') == '期間限定イベント' and x.get('official') in SEL:
        print(' ', x['until'], x['name'], '|', x['city'])
