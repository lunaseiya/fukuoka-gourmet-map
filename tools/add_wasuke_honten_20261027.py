# -*- coding: utf-8 -*-
"""うどん和助 本店(福岡市城南区鳥飼5-2-54)を新規・赤ピン登録(visited=2023-08-06・素材の撮影日)
   素材: ショート動画用/うどん和助　本店(iPhone 8 Plus 1080p .mov・写真なし)。座標: geocoding.jp → 33.575978,130.372839
   卓上にピンクの子供用取り皿+スプーン・フォーク(映像で確認)→ kidsPlate=True。全席禁煙・お子様連れ可(食べログ)
   価格は現行が取れないので書かない(食べログのメニューは2013年・映像は2023年)"""
import io, json, os, shutil, subprocess, sys, tempfile, glob
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\うどん和助　本店'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_wasuke')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'wasuke-honten'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '和助' in x['name']]


def clip(prefix):
    g = glob.glob(os.path.join(SRC, prefix + '_*.mov')); assert len(g) == 1, g; return g[0]


def vid(prefix, ss, box=None):
    t = os.path.join(tempfile.gettempdir(), '_wsk_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(prefix), '-frames:v', '1', '-q:v', '2',
                    '-vf', 'eq=brightness=0.02:saturation=1.08', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size; im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


ImageOps.fit(vid('02', 2.0, (0.0, 0.0, 1.0, 0.70)), (240, 300), Image.LANCZOS).save(os.path.join(TH, SID + '.jpg'), quality=88)
items = [(vid('02', 2.0), '外観(うどん和助の看板)'), (vid('01', 4.0), 'ごぼう天うどん'), (vid('06', 24.5), '麺リフト'),
         (vid('08', 12.5), '冷たい天ぷらぶっかけ'), (vid('03', 0.3), '子供用の取り皿(卓上)'), (vid('02', 11.0), '和助の壁文字')]
photos = []
for k, (im, lab) in enumerate(items, 1):
    im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab); im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': 'うどん和助 本店', 'area': '鳥飼', 'city': '福岡市城南区', 'pref': '福岡県', 'genre': 'うどん',
    'lat': 33.575978, 'lng': 130.372839, 'address': '福岡県福岡市城南区鳥飼5-2-54',
    'visited': '2023-08-06', 'with': 'family', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': None, 'diaper': None, 'tatami': False, 'kidsChair': None, 'kidsMenu': None, 'serveMin': None, 'noise': None,
             'kidsPlate': True},
    'verdict': '⭐器を覆うほど大きなごぼう天の「ごぼう天うどん」が名物の、豊前裏打会のうどん店。麺は自家製で、注文を受けてから茹でる。'
               '口コミでは「揚げたてサクサク」のごぼう天・「黄金色の出汁」・半透明でもっちりコシのある麺の評判が高い(食べログ・Retty)。冷たいぶっかけ・肉うどんも人気。'
               '👶卓上にピンクの子供用取り皿とスプーン・フォークがあり、**全席禁煙**・お子様連れ可(食べログ)。'
               '⚠**12時前後はほぼ行列**(外に待合ベンチあり)。駐車は店前2台のみ。21席(テーブル+カウンター)。'
               '営業 11:00〜15:30 / 17:30〜21:00、不定休(だいたい火曜)。TEL 092-851-0070。価格は現行の表が取れていないので未記載。糸島店(2023年3月オープン)もあり',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400105/40006619/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
