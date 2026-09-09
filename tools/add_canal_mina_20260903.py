# -*- coding: utf-8 -*-
"""キャナルシティ博多 と ミーナ天神 の館内テナントを登録する(2026-09-03)。

親施設(キャナルシティ博多)は既に登録済みなので、**子施設(テナント)を足して、
親施設側には館内の子連れ設備を書き足す**。ミーナ天神は親施設から新規で作る。

■ 写真
  ・**人が写っているものは使わない**。使いたい絵に人がいる場合は、
    モザイクをかけるのではなく**人が枠に入らない位置で切り出す**(飛牛・麺街道と同じ方針)。
  ・スキッズガーデンの料金表は下にモニター(遊んでいる子の映像)があるので**上半分だけ**切る。
  ・マサジローバーガーの子供椅子は窓の外に客がいるので**椅子まわりだけ**切る。
"""
import os, io, json
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'map')
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\キャナルシティ出店リスト'

CANAL_LL = (33.589628, 130.411195)
CANAL_ADDR = '福岡県福岡市博多区住吉1-2-22 キャナルシティ博多'
MINA_LL = (33.593458, 130.398080)
MINA_ADDR = '福岡県福岡市中央区天神4-3-8 ミーナ天神'

# キャナルシティ館内の子連れ設備(全テナント共通で verdict に添える)
CANAL_KIDS = ('⭐キャナルシティ博多には**1階に「こどものトイレ」**(子供サイズの便器の専用トイレ)があり、'
              '各階の多目的トイレに**おむつ交換台とベビーキープ**がある。'
              '5階のラーメンスタジアム階にも多目的トイレあり。')

# (店名, ジャンル, フロア/補足, category)  ※category が None なら飲食
CANAL = [
    # --- ラーメンスタジアム(センターウォーク5F・2026年4月17日リニューアル。全8店) ---
    ('らーめん二男坊 ラーメンスタジアム店', '豚骨ラーメン', 'センターウォーク5F ラーメンスタジアム。継続出店。', None),
    ('博多豚骨 初代秀ちゃん ラーメンスタジアム店', '豚骨ラーメン', 'センターウォーク5F ラーメンスタジアム。継続出店。', None),
    ('札幌 一期一会 みその ラーメンスタジアム店', '味噌ラーメン(札幌)', 'センターウォーク5F ラーメンスタジアム。北海道からの継続出店。', None),
    ('濃熟鶏白湯 らーめん錦 ラーメンスタジアム店', '鶏白湯ラーメン', 'センターウォーク5F ラーメンスタジアム。秋田から**九州初出店**。', None),
    ('麺屋たいそん ラーメンスタジアム店', 'ラーメン', 'センターウォーク5F ラーメンスタジアム。ラースタ初出店。', None),
    ('麺や 豚夢(チャーシュードリーム)ラーメンスタジアム店', 'ラーメン', 'センターウォーク5F ラーメンスタジアム。大阪の人類みな麺類系列で**九州初出店**。', None),
    ('ラーメンろくでなし ラーメンスタジアム店', 'ラーメン', 'センターウォーク5F ラーメンスタジアム。ラースタ初出店。※店頭を撮っていないので館内表示から。', None),
    # --- 飲食 ---
    ('しゃぶ葉 キャナルシティ博多店', 'しゃぶしゃぶ食べ放題', 'すかいらーく系の食べ放題。', None),
    ('うまや キャナルシティ博多店', 'もつ鍋・牛たん', '', None),
    ('KollaBo(コラボ)キャナルシティ博多店', '焼肉・韓国料理', '', None),
    ('サイゼリヤ キャナルシティ博多店', 'イタリアン', '', None),
    ('いきなり!ステーキ キャナルシティ博多店', 'ステーキ', '骨付きリブロースなど。', None),
    ('星乃珈琲店 キャナルシティ博多店', '喫茶・カフェ', '', None),
    ('新宿さぼてん キャナルシティ博多店', 'とんかつ', '', None),
    ('広島お好み焼き 電光石火 キャナルシティ博多店', 'お好み焼き', 'ミシュラン獲得を掲げる広島風お好み焼き。', None),
    ('あぶら食堂 キャナルシティ博多店', '韓国料理', '', None),
    ('仙台辺見 キャナルシティ博多店', '牛タン', '', None),
    ('ピエトロ キャナルシティ博多店', 'パスタ', '', None),
    ('築地銀だこ キャナルシティ博多店', 'たこ焼き', '', None),
    ('Yoajung(ヨアジョン)キャナルシティ博多店', '韓国ヨーグルトアイス', '', None),
    ('Dipper Dan キャナルシティ博多店', 'クレープ', '', None),
    ('マクドナルド キャナルシティ博多店', 'ハンバーガー', '', None),
    ('UOVO Itoshima Farm House キャナルシティ博多店', '糸島たまごスイーツ', '「濃厚ふわもこ。」の卵スイーツ。', None),
    ('Gong cha(ゴンチャ)キャナルシティ博多店', 'タピオカ・台湾ティー', '', None),
    ('MASAJIRO BURGER(マサジローバーガー)キャナルシティ博多店', 'ハンバーガー', '⭐**木製の子供椅子(肘掛け付き)を用意している**。実写で確認。', None),
    ('クリスピー・クリーム・ドーナツ キャナルシティ博多店', 'ドーナツ', '', None),
    ('サーティワンアイスクリーム キャナルシティ博多店', 'アイスクリーム', '', None),
    ('スターバックスコーヒー キャナルシティ博多店', 'カフェ', '', None),
    ('Cinnamoroll Cafe KUOHKA(シナモロールカフェ)', 'キャラクターカフェ', '10:00-21:00(LO20:30)。新グルメストリート「KUOHKA(食謳歌)」内。', None),
    # --- 遊び場 ---
    ('SKIDS GARDEN(スキッズガーデン)キャナルシティ博多店', '屋内キッズ遊び場', '', 'play'),
    ('サンリオギャラリー キャナルシティ博多店', 'キャラクターショップ', '', 'play'),
    ('JUMP SHOP キャナルシティ博多店', 'キャラクターショップ', 'ジャンプ作品の公式ショップ。', 'play'),
    ('どんぐり共和国 キャナルシティ博多店', 'キャラクターショップ', 'ジブリ作品の公式ショップ。トトロの像がある。', 'play'),
    ('クレヨンしんちゃん シネマパレード キャナルシティ博多店', 'キャラクターショップ', '映画の公式ストア。', 'play'),
]
SKIDS_V = ('キャナルシティ博多の屋内キッズ遊び場。ボールプール・アスレチック・ままごと(お花屋さん/ラーメン屋台)がある。'
           '⭐**料金は こども 最初の30分800円+延長15分ごと300円 / おとな 平日無料・土日祝500円(延長料金なし)。'
           '0歳は無料**。入場時に母子手帳などの確認がある。営業時間10:00〜21:00。' + CANAL_KIDS)

MINA_NOTE = ('ミーナ天神(天神北)の館内。B1に飲食が集まっていて**7:00〜22:00**と朝が早い。'
             'イオンショッパーズ福岡店と連絡通路でつながっている。')
MINA = [
    ('スターバックスコーヒー ミーナ天神店', 'カフェ', 'B1。', None),
    ('TeaWay ミーナ天神店', 'カフェ・ティー', 'B1。', None),
    ('ケンタッキーフライドチキン ミーナ天神店', 'ファストフード', 'B1。', None),
    ('てっぱんのスパゲッティ ミーナ天神店', 'スパゲッティ', 'B1。', None),
    ('吉野家 ミーナ天神店', '牛丼', 'B1。はなまるうどんとの併設店。', None),
    ('はなまるうどん ミーナ天神店', 'うどん', 'B1。吉野家との併設店。', None),
    ('マクドナルド ミーナ天神店', 'ハンバーガー', 'B1。', None),
    ('ネデンカフェ ミーナ天神店', 'カフェ', '8F。屋上のフットサルコート・ドッグランの受付も兼ねる。10:00-22:00。', None),
    ('GiGO ミーナ天神店', 'アミューズメント(ゲームセンター)', '7F。10:00-21:00。', 'play'),
    ('ミーナ天神 フットサルコート・ドッグラン', 'フットサル・ドッグラン', '屋上(RF)。10:00-22:00。利用は8Fのネデンカフェ受付へ。', 'play'),
]
MINA_PARENT_V = (MINA_NOTE +
                 ' 2F ユニクロ / 3F GU / 4F LOFT / 5F AOKI・ABC-MART・クラフトハートトーカイ / '
                 '6F ニトリEXPRESS・セリア / 7F BOOK-OFF BAZAAR・GiGO / 8F クロサワ楽器店・ネデンカフェ / '
                 '屋上 フットサルコート・ドッグラン。B2は地下駐車場(7:00-22:00)。')

# 写真: (元ファイル, 出力名, 切り出し比率 or None)
PHOTOS = [
    ('キャナルシティ1Fキッズトイレ.jpg', 'canalcity_kids_toilet.jpg', None),
    ('キャナルシティ1Fトイレ.jpg', 'canalcity_1f_toilet.jpg', None),
    ('5Fトイレ.jpg', 'canalcity_5f_toilet.jpg', None),
    # 下半分にモニター(遊んでいる子の映像)があるので上だけ
    ('写真 2026-09-02 13 39 58.jpg', 'skidsgarden_price.jpg', (0.0, 0.0, 1.0, 0.52)),
    # 窓の外に客がいるので椅子まわりだけ
    ('マサジローバーガーの子供椅子.jpg', 'masajiro_kidschair.jpg', (0.28, 0.38, 0.74, 0.92)),
]


def save_photo(src, out, box):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, src))).convert('RGB')
    if box:
        w, h = im.size
        im = im.crop((int(w * box[0]), int(h * box[1]), int(w * box[2]), int(h * box[3])))
    im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    im.save(os.path.join(MAP, 'photos', out), quality=90)
    return im


def thumb(im, name):
    w = int(im.height * 4 / 5)
    if w <= im.width:
        x = (im.width - w) // 2
        im = im.crop((x, 0, x + w, im.height))
    else:
        im = im.crop((0, 0, im.width, min(int(im.width * 5 / 4), im.height)))
    im.resize((240, 300), Image.LANCZOS).save(os.path.join(MAP, 'thumbs', name), quality=90)


def spot(sid, name, area, city, genre, ll, addr, verdict, cat=None, kids=None, photos=None):
    d = {
        "id": sid, "name": name, "area": area, "city": city, "pref": "福岡県",
        "genre": genre, "lat": ll[0], "lng": ll[1], "address": addr,
        "visited": None, "with": "family",
        "kids": kids or {"stroller": None, "diaper": "facility", "tatami": False,
                         "kidsChair": None, "serveMin": None, "noise": None},
        "verdict": verdict,
        "video": {"youtube": None, "tiktok": None, "instagram": None},
        "thumb": None, "wish": True,
    }
    if cat:
        d["category"] = cat
    if photos:
        d["photos"] = photos
    return d


def main():
    os.makedirs(os.path.join(MAP, 'photos'), exist_ok=True)
    imgs = {}
    for src, out, box in PHOTOS:
        imgs[out] = save_photo(src, out, box)
        print('写真:', out, imgs[out].size)

    sp = json.load(io.open(P, encoding='utf-8'))
    have = {x['name'] for x in sp}
    add = []

    # 親施設(キャナルシティ博多)に館内の子連れ設備を書き足す
    for x in sp:
        if x['name'] == 'キャナルシティ博多':
            if 'こどものトイレ' not in (x.get('verdict') or ''):
                x['verdict'] = (x.get('verdict') or '') + ' ' + CANAL_KIDS
            ph = x.get('photos') or []
            for p in ('canalcity_kids_toilet.jpg', 'canalcity_1f_toilet.jpg', 'canalcity_5f_toilet.jpg'):
                if p not in ph:
                    ph.append(p)
            x['photos'] = ph
            k = x.setdefault('kids', {}) or {}
            k['diaper'] = 'facility'
            x['kids'] = k
            print('親施設を更新: キャナルシティ博多(こどものトイレ+写真3枚)')

    # キャナルシティのテナント
    for i, (name, genre, note, cat) in enumerate(CANAL, 1):
        if name in have:
            print('既にある:', name); continue
        v = ('キャナルシティ博多の館内。%s %s' % (note, CANAL_KIDS)).strip()
        k = {"stroller": None, "diaper": "facility", "tatami": False,
             "kidsChair": None, "serveMin": None, "noise": None}
        ph = None
        if 'SKIDS GARDEN' in name:
            v = SKIDS_V
            ph = ['skidsgarden_price.jpg']
        if 'MASAJIRO' in name:
            k['kidsChair'] = True
            ph = ['masajiro_kidschair.jpg']
        s = spot('canalcity_%02d' % i, name, 'キャナルシティ博多', '福岡市博多区', genre,
                 CANAL_LL, CANAL_ADDR, v, cat, k, ph)
        add.append(s)

    # ミーナ天神(親施設)
    if 'ミーナ天神' not in have:
        add.append(spot('minatenjin', 'ミーナ天神', '天神北', '福岡市中央区', 'ショッピングセンター',
                        MINA_LL, MINA_ADDR, MINA_PARENT_V, 'play',
                        {"stroller": None, "diaper": None, "tatami": False,
                         "kidsChair": None, "serveMin": None, "noise": None}))
    # ミーナ天神のテナント
    for i, (name, genre, note, cat) in enumerate(MINA, 1):
        if name in have:
            print('既にある:', name); continue
        k = {"stroller": None, "diaper": None, "tatami": False,
             "kidsChair": None, "serveMin": None, "noise": None}
        add.append(spot('minatenjin_%02d' % i, name, 'ミーナ天神(天神北)', '福岡市中央区', genre,
                        MINA_LL, MINA_ADDR, '%s %s' % (MINA_NOTE, note), cat, k))

    ids = {x['id'] for x in sp}
    for s in add:
        assert s['id'] not in ids, s['id']
        ids.add(s['id'])
    sp.extend(add)

    # サムネ
    thumb(imgs['skidsgarden_price.jpg'], 'skidsgarden_canal.jpg')
    for s in sp:
        if s['id'] == 'canalcity_%02d' % next(i for i, c in enumerate(CANAL, 1) if 'SKIDS' in c[0]):
            s['thumb'] = 'skidsgarden_canal.jpg'

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print()
    print('  キャナルシティ %2d件' % sum(1 for s in add if s['id'].startswith('canalcity')))
    print('  ミーナ天神     %2d件' % sum(1 for s in add if s['id'].startswith('minatenjin')))
    print('  合計 %d件追加 / 全%d件' % (len(add), len(sp)))


if __name__ == '__main__':
    main()
