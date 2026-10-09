# -*- coding: utf-8 -*-
"""一風堂 THE OUTLETS KITAKYUSHU店を赤ピンで追加(2026-10-08 ユーザー指示「一風堂、極みやは赤ピン」)
   写真はアウトレットのフードコートで撮った店頭(2026-10-08)。人はモザイク。
   来店日は不明なので visited は入れない(極味や アウトレット北九州店と同じ扱い)"""
import io, json, os, shutil, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\ジアウトレット\写真 2026-10-08 12 03 27.jpg'
SID = 'ippudo-theoutletskitakyushu'

im = ImageOps.exif_transpose(Image.open(SRC)).convert('RGB')
W, H = im.size
y0, y1 = int(H * 0.2), int(H * 0.6)
k = W / 1000.0                       # 1000px幅の確認画像で測った座標 → 原寸
def box(x0, yy0, x1, yy1):
    return (int(x0 * k), y0 + int(yy0 * k), int(x1 * k), y0 + int(yy1 * k))
for b in [box(200, 270, 275, 360), box(275, 280, 350, 360), box(500, 285, 575, 370),
          box(715, 310, 770, 380), box(775, 305, 830, 385), box(640, 300, 700, 360)]:   # 店員2名・客3名
    reg = im.crop(b); bw, bh = reg.size
    reg = reg.resize((max(1, bw // 24), max(1, bh // 24)), Image.NEAREST).resize((bw, bh), Image.NEAREST)
    im.paste(reg, b[:2])
front = im.crop((0, y0, W, y1))
os.makedirs(os.path.join(R, 'map', 'photos'), exist_ok=True)
ph = front.resize((1080, int(front.height * 1080 / front.width)), Image.LANCZOS)
pname = SID + '_01_店頭.jpg'
ph.save(os.path.join(R, 'map', 'photos', pname), quality=88)
th = ImageOps.fit(front.crop((int(front.width * 0.25), 0, int(front.width * 0.75), front.height)), (240, 300), centering=(0.5, 0.4))
th.save(os.path.join(R, 'map', 'thumbs', SID + '.jpg'), quality=88)

shutil.copy(P, P + '.bak_ippudo_outlets')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
ids = {s['id'] for s in spots}
assert SID not in ids and 'theoutletskitakyushu' in ids
par = next(s for s in spots if s['id'] == 'theoutletskitakyushu')
spots.append({
    'area': '東田', 'city': '北九州市八幡東区', 'pref': '福岡県',
    'address': '福岡県北九州市八幡東区東田4-1-1(THE OUTLETS KITAKYUSHU)',
    'with': 'family', 'wish': False, 'visited': None, 'in': 'theoutletskitakyushu',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None},
    'id': SID, 'name': '一風堂 THE OUTLETS KITAKYUSHU店', 'genre': 'ラーメン',
    'lat': par['lat'], 'lng': par['lng'], 'category': 'gourmet',
    'kids': {'stroller': True, 'diaper': 'facility', 'tatami': None, 'kidsChair': 'facility', 'serveMin': None, 'noise': 'ok'},
    'verdict': 'THE OUTLETS KITAKYUSHU 1F FOOD FOREST の一風堂。白丸元味・赤丸新味・からか麺などの博多とんこつ。'
               '替玉の注文口があり、イートインスペースもある。フードコート共用のベルト付き子供椅子・ベビールームあり'
               '(2026-10-08 店頭を確認)。',
    'tabelog': None,
    'thumb': SID + '.jpg',
    'photos': [pname],
})
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('追加', SID, len(spots))
