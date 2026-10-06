# -*- coding: utf-8 -*-
"""イオンモール筑紫野 実訪問(2026-10-06)の反映。
   テンプレ: tools/add_aeon_onojo_chikushino_20261006.py(子スポットを作成) / tools/add_aeon_fukuoka_playareas_20261006.py
   素材: ショート動画用/イオンモール筑紫野/写真 2026-10-06 HH MM SS.jpg(3024x4032・exif_transpose済みの座標)
   1. 親 aeonmallchikushino … visited=2026-10-06(赤のまま)。写真で確認した館内設備を verdict に。写真6枚+サムネ
   2. ピエトロ chikushino-rs-pietro … 実際に食事 → 赤ピン(wish=False / visited)。kidsChair=True(写真)。写真3枚+サムネ
   3. 他の飲食 … 食べていないので青のまま。店頭写真を photos/thumb に。写真で読めた設備だけ追記
      (天神ホルモン/うまや/こんぺい亭=キッズチェア、うまや=掘りごたつ・お子さまランチのサンプル)
   4. 福恩麻辣湯 … 未登録だったので青の子スポットとして新規
   値札・メニュー価格が写る部分は「切り出し(CROP)で外す」か「モザイクで潰す」。人物は大人・子供問わずモザイク。
   座標はグリッドを焼いた縮小画像で実測した原寸座標。"""
import io, json, os, shutil, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\イオンモール筑紫野'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
RV = os.path.join(R, 'thumbs_review')
BLOCK = 16
V = '2026-10-06'

# 原寸座標 (x0,y0,x1,y1)。CROP=切り出し範囲 / MOSAIC=人物・値札を潰す範囲
CROP = {
    '16 51 55': (0, 975, 3024, 2453),        # ピエトロのキッズメニュー(上の¥1,480札・下の価格札を外す)
    '16 48 45': (200, 1200, 2080, 3870),     # 天神ホルモン店内のキッズチェア(レジ画面を外す)
    '16 48 35': (0, 300, 2600, 3300),        # 天神ホルモン外観(右の価格入りスタンドを外す)
    '16 47 18': (0, 700, 3024, 3100),        # グランブッフェ(左下の案内板を外す)
    '16 49 06': (0, 600, 3024, 2600),        # ピアサピド(ショーケースの値札を外す)
    '16 50 59': (0, 0, 3024, 2450),          # 因幡うどん(ショーケースの値札を外す)
    '16 51 13': (0, 200, 3024, 2350),        # うまや外観(ショーケース値札・店内の客を外す)
    '16 51 19': (1010, 1750, 2890, 2690),    # うまや お子さまランチのサンプル
    '16 52 46': (650, 250, 3024, 2450),      # こんぺい亭(左の価格入り看板を外す)
    '16 52 48': (300, 2150, 1680, 3630),     # こんぺい亭のハイチェア+ベビーチェア
    '16 53 11': (1300, 450, 3024, 2250),     # 龍神丸(装飾の人物写真パネルと定食の価格ボードを外す)
    '17 51 26': (0, 900, 3024, 1950),        # 福恩麻辣湯(列に並ぶ客を外す)
    '17 58 30': (0, 900, 3024, 2500),        # 美山(価格入りメニューボードを外す)
    '17 58 45': (0, 600, 3024, 1950),        # 濱かつ(ショーケース・価格スタンドを外す)
    '17 59 22': (0, 300, 3024, 3300),        # 那かむら(月替定食の価格を外す)
    '17 59 26': (0, 1250, 1250, 2050),       # 百菜(店前の客2名・価格パネルを外す)
    '17 59 41': (0, 300, 3024, 1850),        # 紅虎餃子房(ショーケース・メニュースタンドを外す)
    '18 00 01': (0, 500, 3024, 2150),        # ABURI百貫(スタッフ・価格ボードを外す)
    '18 00 06': (0, 500, 2450, 2550),        # バーガーキング(右の価格ポスターを外す)
}
MOSAIC = {
    '16 42 53': [(300, 2050, 1000, 2450),                       # スタバ 左カウンターの客3名
                 (1560, 2000, 2750, 2600)],                     # 奥のレジ前・テーブルの客とスタッフ
    '16 48 35': [(1050, 2250, 1260, 2460), (1480, 2280, 1620, 2460),  # 厨房のスタッフ2名
                 (780, 2650, 1450, 3150),                       # 価格入りメニュースタンド
                 (0, 2650, 270, 3300), (2400, 2920, 2600, 3300)],  # 左のメニューケース・右下の貼り紙
    '16 50 59': [(2480, 1900, 3024, 2450)],                     # 壁のメニュー(価格)
    '16 51 19': [(2080, 2385, 2320, 2590)],                     # おこさまランチの値札
    '16 52 46': [(1000, 2250, 1150, 2350)],                     # 店内奥の客の頭
    '16 52 26': [(1800, 2680, 1980, 2870), (2700, 2700, 2880, 2830),  # 店内のスタッフ・客
                 (1550, 3150, 1950, 3500)],                     # 入口のメニュー板
    '16 53 43': [(400, 2150, 1100, 2490), (2500, 2050, 3024, 2850)],  # メニュー台(価格)
    '16 56 33': [(0, 1690, 610, 1870)],                         # 卓上メニュー
    '17 51 26': [(1050, 1500, 1800, 1850), (400, 1700, 650, 1950)],   # 価格入りメニューボード・ポスター
    '17 59 22': [(1100, 1700, 2150, 2550),                      # 入口の客3名
                 (400, 1500, 800, 2150),                        # お持ち帰りメニュー(価格)
                 (2150, 1950, 2750, 2450)],                     # 月替定食の貼り紙
    '18 00 06': [(1050, 1780, 1980, 2050),                      # メニュー画面(価格)
                 (1150, 2150, 1960, 2480)],                     # カウンター内のスタッフ
}


def load(t):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, '写真 2026-10-06 %s.jpg' % t))).convert('RGB')
    assert im.size == (3024, 4032), (t, im.size)
    cx, cy, cx1, cy1 = CROP.get(t, (0, 0, im.width, im.height))
    im = im.crop((cx, cy, cx1, cy1))
    W = im.width
    im.thumbnail((1080, 1920), Image.LANCZOS)
    sc = im.width / W
    for (x0, y0, x1, y1) in MOSAIC.get(t, []):
        x0, x1 = max(x0, cx), min(x1, cx1); y0, y1 = max(y0, cy), min(y1, cy1)
        if x1 <= x0 or y1 <= y0:
            continue
        b = tuple(int(v * sc) for v in (x0 - cx, y0 - cy, x1 - cx, y1 - cy))
        r = im.crop(b)
        sm = r.resize((max(1, r.width // BLOCK), max(1, r.height // BLOCK)), Image.BILINEAR)
        im.paste(sm.resize(r.size, Image.NEAREST), b[:2])
    return im


done_photos = {}


def photos(sid, items, thumb_t):
    out = []
    for k, (t, name) in enumerate(items, 1):
        im = load(t); nm = '%s_%02d_%s.jpg' % (sid, k, name)
        im.save(os.path.join(PH, nm), quality=85); out.append(nm)
        if MOSAIC.get(t):
            os.makedirs(os.path.join(RV, sid), exist_ok=True)
            im.save(os.path.join(RV, sid, '%02d_%s.jpg' % (k, name)), quality=85)
    ImageOps.fit(load(thumb_t), (240, 300), Image.LANCZOS).save(os.path.join(TH, sid + '.jpg'), quality=88)
    done_photos[sid] = out
    return out


shutil.copy(P, P + '.bak_chikushino_visit')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
OLD = json.load(io.open(P, encoding='utf-8'))
NOTE = '⚠未訪問。キッズチェア等は要確認。'
SEEN = '(2026-10-06店頭で確認)'

# ================= 1. 親: イオンモール筑紫野 =================
c = by['aeonmallchikushino']
assert c.get('wish') is False
c['visited'] = V
c['kids']['diaper'] = True
c['verdict'] = ('専門店約210店の3層モール(蔦屋書店・イオンシネマ・トイザらス)。'
    '⭐1Fの赤ちゃんルーム(エレベーターC2そば)を実際に確認:おむつ替え台・カーテン付きの授乳ブース・調乳用温水器と流し・身長計/体重計。'
    '⭐1Fに「KIDS こども用トイレ」(ドレミの扉の子供サイズ個室・子供用小便器・おむつ替えベッド3台)。男性トイレの表示にもおむつ替え台とベビーキープのマーク。'
    '赤ちゃんルームは公式では1F(ウエストコート南入口近く)・2F(クイックカラーQ近く)・3F(セイハ英語学院近く)の3か所、こどもトイレも1〜3Fのセントラルコートに。'
    '⭐1F E2入口(イオン側)にアンパンマン・キティ・トーマスの車型キッズカート「きゃらくるカート」と、ベビーシート付きのショッピングカートが並ぶ。'
    '⭐3Fフードコート「フードフォレスト」(1,100席)の近くに子供用テーブル・イスの「キッズダイニング」(アニメイト近く)、3〜6歳の「キッズパーク」(だがし夢や近く・無料)。'
    'ベビーカー貸出あり(口コミ情報・要確認)。駐車場約3,800台(料金は無料とされるが要確認)。'
    '専門店10:00〜21:00/レストラン11:00〜22:00/フードコート10:00〜21:00/イオン9:00〜22:00。TEL 092-929-2300。(2026-10-06実訪問)')
c['photos'] = photos('aeonmallchikushino', [
    ('17 44 09', '1F赤ちゃんルーム(身長計・体重計)'), ('17 44 12', '赤ちゃんルームのおむつ替え台'),
    ('17 44 24', '調乳用温水器と流し'), ('16 44 21', '1Fこども用トイレの個室'),
    ('16 44 28', 'こども用トイレのおむつ替えベッド'), ('17 49 41', 'キャラクターのキッズカート')], '17 49 41')
c['thumb'] = 'aeonmallchikushino.jpg'

# ================= 2. ピエトロ(実際に食事 → 赤ピン) =================
p = by['chikushino-rs-pietro']
p['wish'] = False; p['visited'] = V
p['kids']['kidsChair'] = True
p['verdict'] = p['verdict'].replace(NOTE,
    '⭐キッズメニュー(パスタのサラダプレート/ポテトプレート・カップスープ付き)を店頭のサンプルで確認。'
    '⭐店内にブースターシート(積み重ね)と木製のハイチェアあり。窓側は明るいテーブル席。(2026-10-06実訪問)')
assert NOTE not in p['verdict']
p['photos'] = photos(p['id'], [('16 52 26', '店構え'), ('16 51 55', 'キッズメニューのサンプル'),
                               ('16 56 33', 'ブースターシートとハイチェア')], '16 52 26')
p['thumb'] = p['id'] + '.jpg'

# ================= 3. 他の飲食(青のまま) =================
def blue(sid, items, thumb_t, chair=False, extra=''):
    x = by[sid]
    assert x.get('wish') is True and x.get('visited') is None, sid
    if chair:
        if x.get('kids') is None:
            x['kids'] = {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None}
        x['kids']['kidsChair'] = True
    add = ('⭐キッズチェアあり' + SEEN + '。' if chair else '') + extra
    if add:
        assert NOTE in x['verdict'], sid
        x['verdict'] = x['verdict'].replace(NOTE, add + '⚠未訪問(店頭のみ)。')
    x['photos'] = photos(sid, items, thumb_t)
    x['thumb'] = sid + '.jpg'


blue('chikushino-starbucks', [('16 42 53', '店構え')], '16 42 53')
blue('chikushino-rs-granbuffet', [('16 47 18', '店構え')], '16 47 18')
blue('chikushino-rs-tenjinhorumon', [('16 48 35', '店構え'), ('16 48 45', '木製のキッズチェア')], '16 48 35', chair=True)
blue('chikushino-rs-piasapido', [('16 49 06', '店構え')], '16 49 06')
blue('chikushino-rs-inabaudon', [('16 50 59', '店構え')], '16 50 59')
blue('chikushino-rs-umaya', [('16 51 13', '店構え'), ('16 53 43', 'キッズチェアと掘りごたつの案内'),
                             ('16 51 19', 'お子さまランチのサンプル')], '16 53 43', chair=True,
     extra='⭐入口に「ゆったり掘りごたつあります」の案内、店頭にお子さまランチのサンプル' + SEEN + '。')
blue('chikushino-rs-konpeitei', [('16 52 46', '店構え'), ('16 52 48', 'ハイチェアとベビーチェア')], '16 52 46', chair=True,
     extra='⭐入口近くに座面の高いキッズチェアと乳児用のベビーチェアも' + SEEN + '。')
blue('chikushino-rs-ryujinmaru', [('16 53 11', '店構え')], '16 53 11')
blue('chikushino-rs-miyama', [('17 58 30', '店構え')], '17 58 30')
blue('chikushino-rs-hamakatsu', [('17 58 45', '店構え')], '17 58 45')
blue('chikushino-rs-tempuranakamura', [('17 59 22', '店構え')], '17 59 22')
blue('chikushino-rs-hyakusai', [('17 59 26', '店構え')], '17 59 26')
blue('chikushino-rs-benitora', [('17 59 41', '店構え')], '17 59 41')
blue('chikushino-rs-aburihyakkan', [('18 00 01', '店構え')], '18 00 01')
blue('chikushino-burgerking', [('18 00 06', '店構え')], '18 00 06')

# ================= 4. 福恩麻辣湯(新規・青) =================
FID = 'chikushino-fuenmalatang'
assert FID not in by and not [x for x in s if '福恩' in x['name']]
s.append({'id': FID, 'name': '福恩麻辣湯 イオンモール筑紫野店', 'area': None, 'city': c['city'], 'pref': '福岡県',
          'genre': '麻辣湯', 'lat': c['lat'], 'lng': c['lng'], 'visited': None, 'with': 'family', 'kids': None,
          'verdict': '大分発の麻辣湯専門店(2026-03-12オープン)。具材を選んでスープの辛さを調節できる(ニュース記事)。'
                     '店の前にテーブル席' + SEEN + '。営業時間は10:00〜21:00(LO20:00)との記事情報(要確認)。館内の区画は要確認。⚠未訪問。キッズチェア等は要確認。',
          'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None, 'wish': True,
          'category': 'gourmet', 'in': 'aeonmallchikushino'})
by[FID] = s[-1]
s[-1]['photos'] = photos(FID, [('17 51 26', '店構え')], '17 51 26')
s[-1]['thumb'] = FID + '.jpg'

# ================= 整合チェック =================
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids)), 'id重複'
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())], 'wish=Trueに動画'
oldby = {x['id']: x for x in OLD}
touched = sorted(i for i in by if json.dumps(by[i], ensure_ascii=False, sort_keys=True) != json.dumps(oldby.get(i), ensure_ascii=False, sort_keys=True))
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('touched', len(touched), touched)
for k, v in done_photos.items():
    print(k, v)
