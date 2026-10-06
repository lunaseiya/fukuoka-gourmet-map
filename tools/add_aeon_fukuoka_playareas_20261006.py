# -*- coding: utf-8 -*-
"""イオンモール福岡(2026-10-02訪問)の館内/館外の無料あそび場3つを子スポットとして追加。
   親=aeonmallfukuoka / 子=もくもくパーク・すくすくパーク・わくわくパーク(新)
   テンプレ: tools/add_aeonmall_fukuoka_20261002.py(座標は親と共有)
   人物は大人・子供問わずモザイク(ブロック16px・出力1080幅基準)。座標はグリッドを焼いた縮小画像で実測した原寸(3024x4032)座標"""
import io, json, os, shutil, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\イオンモール福岡　ルクル'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
RV = os.path.join(R, 'thumbs_review')
BLOCK = 16

# 原寸座標でのモザイク範囲 (x0, y0, x1, y1)
MOSAIC = {
    '13 02 36': [(1170, 360, 1380, 610)],                      # 奥の店舗スタッフ2名
    '13 02 16': [(900, 1570, 1100, 1990)],                     # 通路を歩く男性(後ろ姿)
    '13 57 53': [(60, 1290, 400, 1560),                        # 左奥 BABYDOLL前の男性
                 (620, 1150, 780, 1310),                       # BABYDOLL店内の人
                 (480, 1280, 760, 1960),                       # 子供を抱く男性+子供
                 (270, 1570, 490, 1790),                       # かがむ女性
                 (460, 1640, 610, 1870),                       # 奥の子供
                 (0, 1650, 140, 1920),                         # 左端のベビーカー
                 (1170, 1420, 1280, 1580),                     # 入口奥の人
                 (1420, 1420, 1590, 1590),                     # 入口奥の女性
                 (1220, 1550, 1370, 1900),                     # 入口奥の座っている人
                 (1920, 1670, 2170, 1910),                     # 窓の中の女性
                 (2800, 1200, 3024, 1500)],                    # 右奥の人
    '13 58 45': [(0, 850, 150, 1350),                          # 左端の男性
                 (980, 970, 1150, 1210),                       # 柵の向こうの女性
                 (1050, 1290, 1190, 1430),                     # 奥の子供
                 (1430, 1270, 1630, 1530),                     # 座る女性
                 (1620, 1330, 1810, 1580),                     # 赤ちゃん
                 (1760, 1330, 1970, 1620),                     # キャップの男性
                 (1770, 1120, 1930, 1300),                     # 眼鏡の男性
                 (1940, 1040, 2250, 1340),                     # 奥の人たち
                 (2470, 870, 2690, 1340),                      # 立っている男性
                 (2540, 1330, 2840, 1620),                     # しゃがむ女性
                 (2770, 1680, 3000, 2020)],                    # 寝ている赤ちゃん
    '13 16 24': [(110, 1880, 390, 2030)],                      # 奥の広場の子供と大人
    '13 16 41': [(590, 1940, 720, 2120)],                      # 遊具の陰の子供(後ろ姿)
}


def load(t):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, '写真 2026-10-02 %s.jpg' % t))).convert('RGB')
    W = im.width
    im.thumbnail((1080, 1920))
    sc = im.width / W
    for (x0, y0, x1, y1) in MOSAIC.get(t, []):
        b = tuple(int(v * sc) for v in (x0, y0, x1, y1))
        r = im.crop(b)
        sm = r.resize((max(1, r.width // BLOCK), max(1, r.height // BLOCK)), Image.BILINEAR)
        im.paste(sm.resize(r.size, Image.NEAREST), b[:2])
    return im


def photos(sid, items, thumb_t):
    out = []
    os.makedirs(os.path.join(RV, sid), exist_ok=True)
    for k, (t, name) in enumerate(items, 1):
        im = load(t); nm = '%s_%02d_%s.jpg' % (sid, k, name)
        im.save(os.path.join(PH, nm), quality=85); out.append(nm)
        if MOSAIC.get(t):
            im.save(os.path.join(RV, sid, '%02d_%s.jpg' % (k, name)), quality=85)
    ImageOps.fit(load(thumb_t), (240, 300), Image.LANCZOS).save(os.path.join(TH, sid + '.jpg'), quality=88)
    return out


shutil.copy(P, P + '.bak_aeonfukuoka_playareas')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
V = '2026-10-02'
m = by['aeonmallfukuoka']
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}


def child(sid, name, genre, kids, verdict, items, thumb_t, ages):
    if sid in by:
        print('skip (exists):', sid); return
    s.append({'id': sid, 'name': name, 'area': None, 'city': '糟屋郡粕屋町', 'pref': '福岡県', 'genre': genre,
        'lat': m['lat'], 'lng': m['lng'], 'visited': V, 'with': 'family', 'in': 'aeonmallfukuoka', 'category': 'play', 'wish': False,
        'kids': kids, 'verdict': verdict, 'video': dict(VIDEO0), 'thumb': sid + '.jpg',
        'photos': photos(sid, items, thumb_t), 'ages': ages, 'ages_src': 'manual'})
    print('added:', sid)


child('mokumokupark-aeonmallfukuoka', 'もくもくパーク(イオンモール福岡)', 'キッズスペース',
    {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
    '⭐1F ノースモール(エスカレーター下)の無料キッズスペース。対象は3〜5歳。木をモチーフにした傾斜のある木の床で、靴を脱いで遊ぶ(靴箱あり)。'
    '⚠飲食禁止・走り回り/おもちゃ投げ禁止。保護者は目を離さず付き添い。(2026-10-02実訪問・現地看板)',
    [('13 02 16', 'もくもくパークの全景'), ('13 02 36', 'おやくそく看板(3〜5歳)')], '13 02 16', ['toddler'])

child('sukusukupark-aeonmallfukuoka', 'すくすくパーク(イオンモール福岡)', 'キッズスペース',
    {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
    '⭐2F ノースモール タリーズコーヒー前の無料あそび場。現地看板は「0〜24ヶ月 ここはあかちゃんのあそび場です」(0〜2歳)。'
    'ソフト遊具・マット敷きで、靴を脱いで遊ぶ(くつばこあり)。飲食不可。'
    '(ネット情報では0〜9歳・ボーネルンド遊具・保護者席ありとの記載もあり、対象年齢は現地看板を優先)(2026-10-02実訪問)',
    [('13 57 53', '入口と0〜24ヶ月の看板'), ('13 58 45', 'ソフト遊具のエリア')], '13 57 53', ['baby'])

child('wakuwakupark-aeonmallfukuoka', 'わくわくパーク(イオンモール福岡)', '屋外遊び場',
    {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
    '⭐ノースモール外(E2入口付近)の屋根付き複合遊具。海賊船のような遊具にすべり台・ボルダリング壁。対象2〜6歳・無料。'
    '屋根があるので日差しや小雨のときも使いやすい(要確認)。(2026-10-02実訪問)',
    [('13 16 24', '海賊船の複合遊具'), ('13 16 41', '反対側(ボルダリング壁)')], '13 16 24', ['baby', 'toddler'])

add = '1Fノースモールに3〜5歳の「もくもくパーク」、2Fに0〜24ヶ月の「すくすくパーク」(いずれも無料)、ノースモール外に2〜6歳の屋根付き遊具「わくわくパーク」(無料)。'
if 'もくもくパーク' not in m['verdict']:
    m['verdict'] = m['verdict'].replace('屋外に「ルクルパーク」(無料)。', '屋外に「ルクルパーク」(無料)。' + add, 1)
    assert 'もくもくパーク' in m['verdict']

ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok')
