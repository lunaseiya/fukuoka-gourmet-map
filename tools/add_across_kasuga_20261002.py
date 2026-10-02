# -*- coding: utf-8 -*-
"""アクロスモール春日(親・赤ピン) + こどもひろばどれみ(遊び場・赤ピン・in=親) を登録。撮影 2026-09-23"""
import io, json, os, shutil, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\アクロスモール春日'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_across')
s = json.load(io.open(P, encoding='utf-8'))
MALL, DRM = 'acrossmall-kasuga', 'doremi-acrossmall-kasuga'
assert MALL not in {x['id'] for x in s} and DRM not in {x['id'] for x in s}


def photo(src, name, thumb=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, src))).convert('RGB')
    if thumb:
        ImageOps.fit(im, (240, 300), Image.LANCZOS).save(os.path.join(TH, thumb), quality=88)
    im.thumbnail((1080, 1920)); im.save(os.path.join(PH, name), quality=85)
    return name


mall_ph = [photo('15_写真_フロアガイド(ACROSSMALL).jpg', MALL + '_01_フロアガイド.jpg', MALL + '.jpg'),
           photo('13_写真_ガシャポンコーナー.jpg', MALL + '_02_ガシャポン.jpg'),
           photo('14_写真_ゲームセンター.jpg', MALL + '_03_ゲームセンター.jpg'),
           photo('10_写真_ベビールーム(授乳室あり).jpg', MALL + '_04_ベビールーム.jpg'),
           photo('08_写真_調乳用のお湯と体重計.jpg', MALL + '_05_調乳用のお湯.jpg'),
           photo('未使用_13_写真_木製キッズチェア.jpg', MALL + '_06_木製キッズチェア.jpg')]
drm_ph = [photo('01_写真_どれみ_やわらかマットのエリア(無人).jpg', DRM + '_01_やわらかマットのエリア.jpg', DRM + '.jpg'),
          photo('02_写真_どれみ_ボールプール(無人).jpg', DRM + '_02_ボールプール.jpg'),
          photo('05_写真_ボルダリングコーナー.jpg', DRM + '_03_ボルダリング.jpg'),
          photo('06_写真_ままごとキッチン.jpg', DRM + '_04_ままごとキッチン.jpg'),
          photo('11_写真_どれみ料金表(0歳無料).jpg', DRM + '_05_料金表.jpg'),
          photo('12_写真_フリーパスの案内.jpg', DRM + '_06_フリーパス.jpg')]
base = {'area': None, 'city': '春日市', 'pref': '福岡県', 'address': '福岡県春日市春日5-17',
        'lat': 33.518199, 'lng': 130.470529, 'visited': '2026-09-23', 'with': 'family', 'wish': False,
        'video': {'youtube': None, 'tiktok': None, 'instagram': None}}
s.append(dict(base, id=MALL, name='アクロスモール春日', genre='ショッピングモール', category='play',
    kids={'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None},
    verdict='⭐2階に屋内遊び場「こどもひろばどれみ」。ベビールーム(授乳室・おむつ替え・調乳用のお湯と体重計)、フードコートに木製キッズチェア。'
            'ガシャポン専門店・ゲームセンター・駄菓子屋もある。専門店10:00〜21:00。無料駐車場1,354台。TEL 092-284-0855。',
    thumb=MALL + '.jpg', photos=mall_ph, ages=['baby', 'toddler', 'kids'], ages_src='manual'))
s.append(dict(base, id=DRM, name='こどもひろば どれみ アクロスモール春日店', genre='室内遊び場', category='play', **{'in': MALL},
    kids={'stroller': None, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
    verdict='⭐0歳〜12歳の屋内遊び場(アクロスモール春日2F)。ボールプール・エアートランポリン・ボルダリング・ままごとキッチン・'
            '赤ちゃん専用のハイハイマットあり。⭐料金: こども1時間600円・おとな1時間200円・**0歳は年齢確認できるもの持参で無料**。'
            '平日1日フリーパス(こども1,500円・大人500円・再入場OK)、1ヶ月フリーパス(大人1+子1で10,000円)。'
            '保護者同伴必須。会員登録は初回無料。10:00〜19:00。TEL 092-586-6777。(2026-09-23 店頭掲示で確認)',
    thumb=DRM + '.jpg', photos=drm_ph, ages=['baby', 'toddler', 'kids'], ages_src='manual'))
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('added', MALL, DRM)
