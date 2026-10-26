# -*- coding: utf-8 -*-
"""居酒屋 あまや鳥(福岡市中央区平尾2-2-18・西鉄平尾駅徒歩3分)を新規・赤ピン登録(visited=2023-08-08・素材の撮影日)
   素材: ショート動画用/あまや鳥　平尾店　末ちゃんと(iPhone 1080p .mov・写真なし)。全席喫煙可・個室/座敷なし → 子連れ向きではない旨を verdict に
   座標: geocoding.jp「福岡県福岡市中央区平尾2-2-18」→ 33.575118,130.403825
   価格: ホットペッパー 2026-10-26(税込)。映像内の2023年メニュー価格は使わない"""
import io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\あまや鳥　平尾店　末ちゃんと'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_amayadori')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'amayadori-hirao'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if 'あまや鳥' in x['name']]
import glob


def clip(prefix):
    g = glob.glob(os.path.join(SRC, prefix + '_*.mov')); assert len(g) == 1, g; return g[0]


def vid(prefix, ss, box=None):
    t = os.path.join(tempfile.gettempdir(), '_ama_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(prefix), '-frames:v', '1', '-q:v', '2',
                    '-vf', "eq=brightness=0.03:saturation=1.08", t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size; im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


ImageOps.fit(vid('01', 5.5, (0.05, 0.08, 0.95, 0.80)), (240, 300), Image.LANCZOS).save(os.path.join(TH, SID + '.jpg'), quality=88)
items = [(vid('01', 5.5), '外観(電飾看板と提灯)'), (vid('06', 3.0), 'おまかせ5本盛り'), (vid('05', 3.0), '鯛わた塩辛'),
         (vid('09', 3.0), 'トマトチーズ巻き'), (vid('11', 2.0), '大根の唐揚げ'), (vid('02', 1.0), '店内の壁(手書きの額と日本酒)')]
photos = []
for k, (im, lab) in enumerate(items, 1):
    im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab); im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '居酒屋 あまや鳥', 'area': '平尾', 'city': '福岡市中央区', 'pref': '福岡県', 'genre': '居酒屋',
    'lat': 33.575118, 'lng': 130.403825, 'address': '福岡県福岡市中央区平尾2-2-18',
    'visited': '2023-08-08', 'with': 'friend', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': None, 'diaper': None, 'tatami': False, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None},
    'verdict': '⭐西鉄平尾駅から徒歩3分、高宮通り沿いの焼鳥と海鮮の居酒屋(2019年11月オープン。店名は「海(あま)の幸」+「鶏(とり)」)。'
               '焼鳥は1本132円〜、おまかせ5本盛り1,188円、つくね275円、トマトチーズ巻き330円、大根の唐揚げ550円、鯛わた塩辛・梅水晶 各528円(2026年10月 ホットペッパー掲載・税込)。'
               '口コミでは白レバ刺し・鳥刺し盛り合わせ・大根の唐揚げの評判が高い(食べログ・ホットペッパー)。'
               '⚠**全席喫煙可**(紙・加熱式)で個室・座敷なし、18時開店の夜の店。子連れ向きではなく、大人の夜飲みに。カード払いは4%上乗せの掲示あり(2023年8月時点)。'
               '営業 18:00〜24:00(金土祝前〜翌2:00・サイトにより表記差あり)。定休日は不定休または水曜(要確認)。TEL 092-406-9698。※動画は2023年8月の撮影',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400104/40053356/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
