# -*- coding: utf-8 -*-
"""子供椅子のある3店を新規登録し、いただいた写真をマップに載せる(2026-09-02)。

  ・ゼッテリア 福岡新天町店(天神)      … 子供椅子3脚。※他の客2名が写るのでモザイク
  ・吉野家 天神サザン通り店            … 子供椅子2脚 + 外観「こども元気割」ポスター
  ・È PRONTO ミーナ天神店(地下1F)     … ベビーチェア(ベルト付き)

写真は iPhone の EXIF 回転が入っているので **必ず exif_transpose を通す**。
モザイクは1080px換算で14〜22px。座標は縮小フレームで実測して倍率を掛ける。
"""
import os, json, io
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'map')
UP = r'C:\Users\totor\.claude\uploads\47c954ea-7ae3-4311-87bd-aeb862ff2e37'
P = os.path.join(ROOT, 'data', 'spots.json')

SRC = {
    'zetteria_isu':  os.path.join(UP, 'e0445906-IMG_6040.png'),      # ゼッテリア 子供椅子(人あり)
    'yoshinoya_isu': os.path.join(UP, '10536aaa-IMG_6042.png'),      # 吉野家 子供椅子
    'yoshinoya_gai': os.path.join(UP, '6913f3a7-IMG_6041.jpeg'),     # 吉野家 外観+こども元気割
    'pronto_isu':    os.path.join(UP, '3ad5d4f2-IMG_6048.jpeg'),     # イープロント ベビーチェア
    'pronto_gai':    os.path.join(UP, '55c4aded-IMG_6045.jpeg'),     # イープロント 店頭(人あり)
}


def load(k):
    return ImageOps.exif_transpose(Image.open(SRC[k])).convert('RGB')


def to1080(im):
    return im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)


def mosaic(im, boxes, block=18):
    for x, y, w, h in boxes:
        r = im.crop((x, y, x + w, y + h))
        r = r.resize((max(1, w // block), max(1, h // block)), Image.NEAREST)
        im.paste(r.resize((w, h), Image.NEAREST), (x, y))
    return im


def save_photo(im, name):
    p = os.path.join(MAP, 'photos', name)
    im.save(p, quality=90)
    print('  photo %-34s %s' % (name, im.size))
    return name


def save_thumb(im, name, top=0.5):
    """240x300(4:5)。縦横どちらの写真でも中央から4:5を切る。"""
    w = int(im.height * 4 / 5)
    if w <= im.width:
        box = ((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height)
    else:
        h = int(im.width * 5 / 4)
        y = int((im.height - h) * top)
        box = (0, y, im.width, y + h)
    im.crop(box).resize((240, 300), Image.LANCZOS).save(
        os.path.join(MAP, 'thumbs', name), quality=90)
    print('  thumb %s' % name)
    return name


def main():
    os.makedirs(os.path.join(MAP, 'photos'), exist_ok=True)

    print('■ ゼッテリア')
    z = to1080(load('zetteria_isu'))
    # 奥のテーブルの客2名(左:女性 / 右:男性)。1080幅での実測値
    z = mosaic(z, [(370, 105, 130, 130), (760, 80, 180, 170)], block=16)
    zp = [save_photo(z, 'zetteria_shintencho_01.jpg')]
    zt = save_thumb(z, 'zetteriashintencho.jpg')

    print('■ 吉野家 天神サザン通り')
    y1 = to1080(load('yoshinoya_isu'))
    y2 = to1080(load('yoshinoya_gai'))
    yp = [save_photo(y2, 'yoshinoyatenjinsouthern_01.jpg'),
          save_photo(y1, 'yoshinoyatenjinsouthern_02.jpg')]
    yt = save_thumb(y2, 'yoshinoyatenjinsouthern.jpg')

    print('■ È PRONTO ミーナ天神')
    p1 = to1080(load('pronto_isu'))
    g = load('pronto_gai')
    # 店頭は客とスタッフが多数。**看板だけを切り出して人を枠外に出す**
    # (モザイクだらけにするより、そもそも入れない構図にするほうが良い)
    g = g.crop((0, 0, int(g.width * 0.62), int(g.height * 0.55)))
    p2 = to1080(g)
    pp = [save_photo(p2, 'epronto_minatenjin_01.jpg'),
          save_photo(p1, 'epronto_minatenjin_02.jpg')]
    pt = save_thumb(p2, 'eprontominatenjin.jpg')

    sp = json.load(io.open(P, encoding='utf-8'))
    have = {s['id'] for s in sp}

    NEW = [
    {"id": "zetteriashintencho", "name": "ゼッテリア 福岡新天町店",
     "area": "天神(新天町)", "city": "福岡市中央区", "pref": "福岡県", "genre": "ハンバーガー",
     "lat": 33.590513, "lng": 130.397785,
     "address": "福岡県福岡市中央区天神2-8-5",
     "kids": {"stroller": None, "diaper": None, "tatami": False,
              "kidsChair": True, "serveMin": None, "noise": None},
     "verdict": "⭐子供椅子あり(現地確認・木製の背もたれ付きが3脚)。新天町商店街のロッテリア系業態。TEL 092-739-5560。",
     "thumb": zt, "photos": zp},

    {"id": "yoshinoyatenjinsouthern", "name": "吉野家 天神サザン通り店",
     "area": "天神(サザン通り)", "city": "福岡市中央区", "pref": "福岡県", "genre": "牛丼",
     "lat": 33.589531, "lng": 130.39698,
     "address": "福岡県福岡市中央区天神2-6-32 天神パルスビル",
     "kids": {"stroller": None, "diaper": None, "tatami": False,
              "kidsChair": True, "serveMin": None, "noise": None},
     "verdict": ("⭐子供椅子あり(現地確認・テーブル付きの木製が2脚)。"
                 "⭐**「こども元気割」で小学生以下は丼・皿・定食・カレー・お子様メニューが80円引き**。"
                 "**春休みと夏休みに毎年やっている季節キャンペーン**(2026年は3/2〜4/20と7/16〜9/3)なので、"
                 "休みの時期は掲示を確認するとよい。"
                 "※0歳児連れで訪問した際、食べない子の分として親の牛丼に適用してもらえたことがある(店舗判断と思われる)。"
                 "TEL 092-739-9811。"),
     "thumb": yt, "photos": yp},

    {"id": "eprontominatenjin", "name": "È PRONTO ミーナ天神店",
     "area": "天神(ミーナ天神B1)", "city": "福岡市中央区", "pref": "福岡県", "genre": "カフェ・パスタ",
     "lat": 33.593458, "lng": 130.39808,
     "address": "福岡県福岡市中央区天神4-3-8 ミーナ天神 B1",
     "kids": {"stroller": None, "diaper": None, "tatami": False,
              "kidsChair": True, "serveMin": None, "noise": None},
     "verdict": ("⭐ベビーチェアあり(現地確認・ベルト付きのハイチェア)。"
                 "ミーナ天神の地下1階。パスタ・ホットドッグ・コーヒーのカフェ業態。TEL 092-791-8647。"),
     "thumb": pt, "photos": pp},
    ]

    n = 0
    for s in NEW:
        if s['id'] in have:
            print('既にある:', s['id']); continue
        s.update({"visited": None, "with": "family",
                  "video": {"youtube": None, "tiktok": None, "instagram": None},
                  "wish": False})       # 実際に行っているので赤ピン
        sp.append(s); n += 1
        print('追加: %-26s %s' % (s['name'][:26], s['address']))
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print()
    print('追加%d件 / 全%d件 / 赤ピン%d件' % (n, len(sp), sum(1 for x in sp if not x.get('wish'))))


if __name__ == '__main__':
    main()
