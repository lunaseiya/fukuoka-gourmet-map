# -*- coding: utf-8 -*-
"""桧原運動公園(福岡市南区)を青ピンで登録(2026-10-02・ユーザーがTikTokで見つけた)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_hibaru')
s = json.load(io.open(P, encoding='utf-8'))
ID = 'hibaru-undoukouen'
assert ID not in {x['id'] for x in s}
s.append({
 'id': ID, 'name': '桧原運動公園', 'area': '桧原', 'city': '福岡市南区', 'pref': '福岡県',
 'genre': '公園', 'address': '福岡県福岡市南区桧原5丁目30-1',
 'lat': 33.533268, 'lng': 130.390911,   # geocoding.jp(施設名で取得。住所では取れなかった)
 'visited': None, 'with': 'family',
 'kids': {'stroller': None, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
 'verdict': '⭐大型のコンビネーション遊具(赤と黄色のアーチ・ネット・クライミング・すべり台)と広いグラウンド。'
            'インクルーシブな子ども広場にすべり台・ブランコもある。⭐公園管理事務所が「赤ちゃんの駅」登録施設で、'
            '屋内のおむつ交換スペース・授乳室・バリアフリートイレあり。9:00〜21:00。駐車場225台・無料(8:20〜21:20)。'
            'TEL 092-566-8208。',
 'video': {'youtube': None, 'tiktok': None, 'instagram': None},
 'thumb': None, 'wish': True, 'category': 'play',
 'ages': ['toddler', 'kids'], 'ages_src': 'auto',
})
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('added', ID)
