# -*- coding: utf-8 -*-
"""DA BOCCIANO! 天神店(天神ビジネスセンター1F)を赤ピン登録(2026-10-01訪問・エモ回素材)
   コンプライアンス: ✅(天神BC/イナチカに撮影禁止の告知なし)"""
import io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\天神センタービル'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_bocciano')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'da-bocciano-tenjin'
assert SID not in {x['id'] for x in s}


def img(name, ss=1.0):
    p = os.path.join(SRC, name)
    if p.lower().endswith('.mov'):
        t = os.path.join(PH, '_t.jpg'); subprocess.run([FF, '-v', 'quiet', '-y', '-ss', str(ss), '-i', p, '-frames:v', '1', '-q:v', '2', t])
        im = Image.open(t).convert('RGB'); os.remove(t); return im
    return ImageOps.exif_transpose(Image.open(p)).convert('RGB')


items = [('動画 2026-10-01 13 08 05.mov', 0.5, '外観'), ('写真 2026-10-01 13 19 13.jpg', 0, '子供椅子'),
         ('動画 2026-10-01 13 18 54.mov', 2.5, 'ランチメニュー'), ('動画 2026-10-01 13 38 53.mov', 3.0, 'マルゲリータ')]
photos = []
for k, (n, ss, lab) in enumerate(items, 1):
    im = img(n, ss); im.thumbnail((1080, 1920)); nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)
ImageOps.fit(img(items[0][0], 0.5), (240, 300), Image.LANCZOS).save(os.path.join(TH, SID + '.jpg'), quality=88)
s.append({'id': SID, 'name': 'ピッツェリア トラットリア ダ・ボッチャーノ 天神店', 'area': '天神', 'city': '福岡市中央区', 'pref': '福岡県',
    'genre': 'ピザ・イタリアン', 'lat': 33.591367, 'lng': 130.400604, 'visited': '2026-10-01', 'with': 'family', 'in': None,
    'category': 'gourmet', 'wish': False,
    'kids': {'stroller': True, 'diaper': None, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None},
    'verdict': '⭐子供椅子(木製ハイチェア)あり。ピザW杯優勝の職人の薪窯ナポリピッツァ。'
               'ランチ(11:00〜15:00)はボッチャーノランチ1,650円(サラダ+ピッツァかパスタ+ドリンク)。'
               '天神ビジネスセンター1F。地下の天神イナチカは酒場中心で子供椅子は見当たらなかったので、子連れならこちらへ。(2026-10-01実訪問)',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos,
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400103/40060558/',
    'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'manual'})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok')
