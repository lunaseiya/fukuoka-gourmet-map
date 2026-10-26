# -*- coding: utf-8 -*-
"""紀左衛門(キザエモン・たこ焼きバー・福岡市中央区春吉3-13-27)を新規・赤ピン登録(visited=2023-03-01・素材の撮影日)
   動画は保留(素材が2023年のiPhone 8 Plus・料理カット不足)。マップ登録のみ(2026-10-26ユーザー指示「焼鳥と一緒にマップの登録のみ」)
   素材: ショート動画用/たこ焼きバー　春吉(動画7本・写真なし)。座標: geocoding.jp → 33.589379,130.406331
   深夜バー・カウンター7席・チャージあり・灰皿が写る → 子連れ向きでない旨を verdict に。価格は現行が取れないので書かない(2019年の口コミ価格は使わない)"""
import io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\たこ焼きバー　春吉'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_kizaemon')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'kizaemon-haruyoshi'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '紀左衛門' in x['name']]


def clip(n):
    g = [f for f in os.listdir(SRC) if f.startswith('未使用_%s_' % n)]; assert len(g) == 1, g; return os.path.join(SRC, g[0])


def vid(n, ss, box=None):
    t = os.path.join(tempfile.gettempdir(), '_kiz_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(n), '-frames:v', '1', '-q:v', '2',
                    '-vf', 'eq=brightness=0.03:saturation=0.95', t], check=True)   # 赤被りを少し戻す
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size; im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


ImageOps.fit(vid('1340', 6.0, (0.05, 0.05, 0.95, 0.80)), (240, 300), Image.LANCZOS).save(os.path.join(TH, SID + '.jpg'), quality=88)
items = [(vid('1340', 6.0), '外観(紀左衛門の看板)'), (vid('1344', 1.0), 'たこ焼き2皿(白マヨと明太マヨ)'),
         (vid('1342', 1.5), 'たこ焼き(マヨ)'), (vid('1341', 1.5), 'バーカウンターの酒棚')]
photos = []
for k, (im, lab) in enumerate(items, 1):
    im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab); im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '紀左衛門(キザエモン)', 'area': '春吉', 'city': '福岡市中央区', 'pref': '福岡県', 'genre': 'たこ焼き',
    'lat': 33.589379, 'lng': 130.406331, 'address': '福岡県福岡市中央区春吉3-13-27',
    'visited': '2023-03-01', 'with': 'friend', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': None, 'diaper': None, 'tatami': False, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None},
    'verdict': '⭐天神南駅から徒歩5分、春吉のたこ焼きバー(Takoyaki Bar Kizaemon)。表面はとろっと、皮はクレープのようにきめ細かい生地で、ソース・塩マヨ・ゆず胡椒マヨ・明太マヨ・テリタマなどの味がある。'
               'ハイボールと合わせる「2軒目」の店で、持ち帰りもできる(食べログ・Retty・hamoni)。'
               '⚠**カウンター7席だけの深夜バー**(19:00〜翌2:00・金土は〜翌5:00、日曜定休。媒体で表記差あり)。店内飲食はチャージあり。2023年3月の訪問時は卓上に灰皿があった。**子連れ向きではなく大人の〆の一軒**。'
               '価格は現行の表が取れていないので未記載。営業は2025年1月の訪問記録まで確認(閉店表示なし・行く前に電話確認を)。TEL 092-762-8808。※動画は作らず保留(2023年撮影の素材のみ)',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400103/40040863/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
