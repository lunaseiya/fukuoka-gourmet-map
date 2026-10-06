# -*- coding: utf-8 -*-
"""久原本家 総本店(茅乃舎の本家・旗艦店/糟屋郡久山町)を新規・赤ピン登録(2026-10-05訪問・素材の撮影日)
   素材: ショート動画用/茅乃舎本家(iPhone SDR bt709 → トーンマップ不要。写真は exif_transpose)
   座標: geocoding.jp(住所で取得)。写真EXIFのGPS(33.6430,130.5054)とも約65mで一致
   コンプライアンス: ✅(公式に撮影ルールの記載なし・独立店舗)
   子連れ設備は実写で確認できたものだけ(外トイレ棟のスロープ+手すり/多目的トイレのTOTOベビーシート)。
   キッズチェアは未確認なので null
   人の映り込み: 使用カットはすべて目視で人物なし(本人が映るクリップは使わない)"""
import io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\茅乃舎本家'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_kubarahonke')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'kubara-honke-souhonten'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '久原' in x['name'] or '茅乃舎' in x['name']]


def img(name, ss=0):
    p = os.path.join(SRC, name)
    if p.lower().endswith('.mov'):
        t = os.path.join(PH, '_t.jpg')
        subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', p, '-frames:v', '1', '-q:v', '2', t], check=True)
        im = Image.open(t).convert('RGB'); im.load(); os.remove(t); return im
    return ImageOps.exif_transpose(Image.open(p)).convert('RGB')


# サムネ: 「総本店 創業明治二十六年 久原本家」の幕(02 3.5s・人なし)
ImageOps.fit(img('02_6s_総本店の幕.mov', 3.5), (240, 300), Image.LANCZOS, centering=(0.5, 0.45)).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (素材, 秒, 内容)
items = [('02_6s_総本店の幕.mov', 3.5, '総本店の幕'),
         ('28_写真_多目的トイレのベビーシート.jpg', 0, '多目的トイレのベビーシート'),
         ('27_写真_外のトイレ棟(スロープと手すり).jpg', 0, 'トイレ棟のスロープ'),
         ('21_5s_醤油ソフトの寄り.mov', 2.0, '醤油ソフト'),
         ('16_写真_博多限定もつ入り肉饅頭のポスター.jpg', 0, 'もつ入り肉饅頭'),
         ('25_5s_テラス席と田んぼの景色.mov', 3.0, 'テラス席')]
photos = []
for k, (n, ss, lab) in enumerate(items, 1):
    im = img(n, ss); im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '久原本家 総本店(茅乃舎)', 'area': '久山', 'city': '糟屋郡久山町', 'pref': '福岡県',
    'genre': '調味料・お土産', 'lat': 33.643566, 'lng': 130.505056, 'address': '福岡県糟屋郡久山町大字久原2527',
    'visited': '2026-10-05', 'with': 'family', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
    'verdict': '⭐外の独立トイレ棟はスロープと手すり付き、多目的トイレにTOTOのベビーシート(おむつ交換台)あり。'
               '茅乃舎だしの久原本家(明治26年創業)の旗艦店で、だしの試飲・試食コーナーあり。'
               'テイクアウトは醤油ソフトクリーム350円・椒房庵の博多限定もつ入り肉饅頭650円(数量限定)、'
               '田んぼを望むパラソル付きテラス席で食べられる。広い駐車場あり。'
               '10:00〜18:00・元日休み。TEL 092-976-3408。(2026-10-05実訪問)',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
