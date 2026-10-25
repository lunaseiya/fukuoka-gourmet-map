# -*- coding: utf-8 -*-
"""タリーズコーヒー 福岡東平尾公園店(博多区・東平尾公園 大谷広場の中)を新規・赤ピン登録(visited=2026-10-22)
   素材: ショート動画用/タリーズ＆東平尾公園(iPhone SDR .mov / .jpg)。親スポット touheiokouenootanihiroba の in: に入れる
   座標: geocoding.jp「福岡県福岡市博多区東平尾公園２丁目１−５」→ 33.58332,130.460552
   子連れ設備は現地写真: ベルト付き子供椅子(12 45 07)・トイレ内のおむつ替え台+ベビーキープ(12 45 35)・キッズスペース(ソファの囲い+絵本)・
   キッズメニューの黒板(12 42 14)。レシート(12 56 43)で店名表記「タリーズコーヒー 福岡東平尾公園店」TEL 092-402-5070・税込表示を確認"""
import io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\タリーズ＆東平尾公園'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_tullys')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'tullys-fukuoka-higashihirao-park'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '東平尾公園店' in x['name']]
assert [x for x in s if x['id'] == 'touheiokouenootanihiroba']


def vid(name, ss, box=None):
    t = os.path.join(tempfile.gettempdir(), '_tullys_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', os.path.join(SRC, name),
                    '-frames:v', '1', '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    return crop(im, box)


def pho(name, box=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name))).convert('RGB')
    return crop(im, box)


def crop(im, box):
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


# サムネ: 外観(TULLY'S COFFEE の看板とテラス)
ImageOps.fit(vid('01_9s_タリーズ外観テラスから看板へパン.mov', 6.0, (0.05, 0.10, 0.95, 0.85)), (240, 300), Image.LANCZOS).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

items = [(vid('01_9s_タリーズ外観テラスから看板へパン.mov', 6.0), '外観(テラス席と看板)'),
         (pho('写真 2026-10-22 12 45 07.jpg'), 'ベルト付きの子供椅子'),
         (vid('02_15s_キッズスペース絵本→窓越しの公園→テラス席.mov', 2.0), 'キッズスペース(ソファの囲いと絵本)'),
         (pho('写真 2026-10-22 12 45 35.jpg'), 'トイレ内のおむつ替え台とベビーキープ'),
         (pho('写真 2026-10-22 12 42 14.jpg', (0.0, 0.40, 0.80, 0.90)), 'キッズメニューの黒板'),
         (vid('02_15s_キッズスペース絵本→窓越しの公園→テラス席.mov', 8.0), '店内から公園が見える全面ガラス'),
         (pho('写真 2026-10-22 12 42 06.jpg'), '入口の営業時間')]
photos = []
for k, (im, lab) in enumerate(items, 1):
    im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': 'タリーズコーヒー 福岡東平尾公園店', 'area': '東平尾公園', 'city': '福岡市博多区', 'pref': '福岡県',
    'genre': 'カフェ', 'lat': 33.58332, 'lng': 130.460552,
    'address': '福岡県福岡市博多区東平尾公園2丁目1-5',
    'visited': '2026-10-22', 'with': 'family', 'category': 'gourmet', 'wish': False,
    'in': 'touheiokouenootanihiroba',
    'kids': {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': True, 'kidsMenu': True, 'kidsSpace': True, 'sofa': True,
             'babyKeep': True, 'serveMin': None, 'noise': None},
    'verdict': '⭐2025年4月1日オープン。タリーズとして**九州初の公園内店舗**で、東平尾公園 大谷広場(博多の森)の入口にある。全面ガラス張りで店内から遊具や草スキー場が見え、'
               'テラス席(20席)も公園に面している。62席・ドライブスルーあり。'
               '⭐子連れ歓迎: **ベルト付きの子供椅子**・**キッズスペース**(ソファで囲ったコーナーに絵本)・仕切れる半個室のソファ席・トイレ内に**おむつ替え台とベビーキープ**。'
               '⭐キッズメニューあり(税込): キッズドリンク各370円(りんご100%・ココア・ミルク)/キッズパンケーキ アイス付き ドリンクセット765円/おやこパスタセット1,625円/アイス300円。'
               '実食はドッグ チーズメルト500円・アイスチャイティー(S)530円(税込・2026年10月)。'
               '平日9:00〜20:00/土日祝8:00〜20:00。**公園の駐車場(大谷第1)がタリーズ利用で1時間無料**(通常は入庫後20分無料・60分100円・最大500円)。'
               '遊んだあとの休憩に。土日は混む・ドライブスルーは時間がかかるという口コミあり(食べログ)。TEL 092-402-5070',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400107/40070151/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
