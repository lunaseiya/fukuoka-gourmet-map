# -*- coding: utf-8 -*-
"""スタミナ鉄板 博多アイアンマン 古賀店(古賀市天神)を新規・赤ピン登録(visited=2026-10-07・ユーザー実訪問)
   座標: geocoding.jp(住所「福岡県古賀市天神3-17-5」で取得)
   with=family。kids はユーザーの現地証言(子供椅子なし/板張りのボックス席・座敷個室なし/
   子供用フォーク・スプーン・取り皿あり/キッズメニューなし)から。未確認の項目は null
   写真・素材フォルダなし → thumb=null
   食べログは手で付与(monetize.py の食べログ検索が壊れているため)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_ironman_koga')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'ironman-koga'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if 'アイアンマン' in x['name']]

s.append({'id': SID, 'name': 'スタミナ鉄板 博多アイアンマン 古賀店', 'area': '古賀', 'city': '古賀市', 'pref': '福岡県',
    'genre': '定食・鉄板焼き', 'lat': 33.738899, 'lng': 130.466809, 'address': '福岡県古賀市天神3-17-5',
    'visited': '2026-10-07', 'with': 'family', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': None, 'diaper': None, 'tatami': False, 'kidsChair': False,
             'serveMin': None, 'noise': None, 'kidsMenu': False},
    'ages': ['kids'], 'ages_src': 'manual',
    'verdict': '⚠子連れ向きとは言いにくい。子供椅子・キッズメニューなし、席は板張りのボックス席(座敷・個室なし)。'
               '豚肉とキャベツの鉄板にご飯・味噌汁の定食スタイルなので、小学生くらいで取り分けるならOK。'
               '⭐子供用のフォーク・スプーン・取り皿あり、駐車場あり、店内全面禁煙(屋外に喫煙所)。'
               '11:00-15:00/17:00-21:00・不定休、食券制、44席(カウンターあり)。JR古賀駅から徒歩約9分。TEL 092-692-7529。',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None,
    'tabelog': 'https://tabelog.com/fukuoka/A4003/A400302/40061601/'})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', len(s))
