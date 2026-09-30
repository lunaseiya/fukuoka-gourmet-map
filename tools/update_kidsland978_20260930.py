# -*- coding: utf-8 -*-
"""キッズランドUS MAX 福岡久山店: 実訪問(2026-09-29)を反映。写真追加・料金更新"""
import io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\usキッズmax久山'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
ID = 'kidsland-978'
PH = os.path.join(R, 'map', 'photos')
shutil.copy(P, P + '.bak_kidsland978')
spots = json.load(io.open(P, encoding='utf-8'))
s = next(x for x in spots if x['id'] == ID)


def save_photo(src, name):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB'); im.thumbnail((1080, 1920))
    im.save(os.path.join(PH, name), quality=85); return name


def frame(src, ss, name):
    tmp = os.path.join(PH, '_tmp.jpg')
    subprocess.run([FF, '-v', 'quiet', '-y', '-ss', str(ss), '-i', src, '-frames:v', '1', '-q:v', '2', tmp], check=True)
    n = save_photo(tmp, name); os.remove(tmp); return n


new = [
 save_photo(os.path.join(SRC, '未使用_37_写真_木製キッズチェアとベビーチェア.jpg'), ID + '_04_木製キッズチェアとベビーチェア.jpg'),
 frame(os.path.join(SRC, '23_11s_ベビーコーナー看板(0〜3歳).mov'), 0.8, ID + '_05_ベビーコーナー(0〜3歳専用).jpg'),
 frame(os.path.join(SRC, '26_6s_ベビーカー貸出.mov'), 3.0, ID + '_06_ベビーカー貸出.jpg'),
 save_photo(os.path.join(SRC, '未使用_40_写真_巨大ブロックの家.jpg'), ID + '_07_巨大ブロック.jpg'),
 frame(os.path.join(SRC, '05_25s_恐竜ライド(ヘルメットで走る).mov'), 3.0, ID + '_08_恐竜ライド.jpg'),
]
for n in new:
    if n not in s['photos']: s['photos'].append(n)
s['visited'] = '2026-09-29'
s['kids']['kidsChair'] = True
s['verdict'] = (s['verdict']
    .replace('⭐アソビューの事前チケットが定価より安い(平日こども1日800円前後/休日3時間1,200円前後)。',
             '⭐アソビューの平日「こども1日遊び放題」が 1,100円→900円(2026-09時点・保護者800円・0歳無料・フリータイム)。')
    + ' 【2026-09-29実訪問】恐竜に乗って走るライド、トランポリン、透明ボール、ミニトレイン、メリーゴーランド、スイングカーの坂道コース、'
      'ボールを飛ばせるボールプール、巨大ブロック、0〜3歳専用のベビーコーナー、ベビーカー貸出、木製キッズチェア、わたあめ自販機、大人用マッサージチェアあり。'
      '平日夕方は空いていてほぼ貸し切りだった。')
ids = [x['id'] for x in spots]; assert len(ids) == len(set(ids))
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('updated', ID, len(s['photos']), 'photos')
