# -*- coding: utf-8 -*-
"""È PRONTO ミーナ天神店を、エモ版の撮影内容で更新する(2026-09-03)。

追加する一次情報(すべて現地の実写・メニュー表から):
  ・訪問日 2026-09-01(素材の撮影日)
  ・**固めのプリン ザクザクキャラメル ¥580(税込638)**
  ・**カフェインレス(デカフェ・コーヒー¥500 / デカフェ・オレ¥550)** ※HOTのみ
    ⚠メニューに「**微量のカフェインを含みます**」と明記があるので、そこも書く
  ・席の間隔が広く、テーブル席主体。B1の飲食フロアは 7:00〜22:00 と朝が早い

写真は人が枠に入らない位置で切り出したものだけを足す(モザイクは使わない)。
"""
import os, io, json
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'map')
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\エプロントmina'

# (元ファイル, 出力名, 切り出し比率(l,t,r,b) or None)
PHOTOS = [
    ('写真 2026-09-01 14 45 42.jpg', 'epronto_minatenjin_03_ベビーチェア.jpg', (0.36, 0.0, 0.98, 1.0)),
    ('写真 2026-09-01 15 01 19.jpg', 'epronto_minatenjin_04_席の間隔.jpg',   (0.28, 0.43, 1.0, 0.98)),
    ('写真 2026-09-01 14 39 42.jpg', 'epronto_minatenjin_05_デカフェ.jpg',   (0.02, 0.60, 0.36, 0.82)),
    ('写真 2026-09-01 14 40 26.jpg', 'epronto_minatenjin_06_ショーケース.jpg', None),
]
ADD = (' 訪問は2026年9月1日。頼んだのは**固めのプリン ザクザクキャラメル ¥580**とアイスカフェラテ。'
       '⭐**カフェインレスのメニューがある**(デカフェ・コーヒー¥500 / デカフェ・オレ¥550、どちらもHOTのみ)。'
       'ただしメニューに「微量のカフェインを含みます」と注記あり。'
       'テーブル席主体で**席の間隔が広く、ベビーカーでも通れる**。'
       'ミーナ天神B1の飲食フロアは7:00〜22:00と朝が早い。'
       '⚠この日は天神のワン・フクオカを回ったが子供椅子のある店が見つからず、'
       'ここでようやく座れた、という経緯で立ち寄っている。')


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    x = next(s for s in sp if s['id'] == 'eprontominatenjin')

    names = []
    for f, out, box in PHOTOS:
        im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, f))).convert('RGB')
        if box:
            w, h = im.size
            im = im.crop((int(w * box[0]), int(h * box[1]), int(w * box[2]), int(h * box[3])))
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
        im.save(os.path.join(MAP, 'photos', out), quality=90)
        names.append(out)
        print('写真:', out, im.size)

    x['visited'] = '2026-09-01'
    ph = x.get('photos') or []
    for n in names:
        if n not in ph:
            ph.append(n)
    x['photos'] = ph
    if '固めのプリン' not in x['verdict']:
        x['verdict'] = x['verdict'] + ADD
    k = x.setdefault('kids', {})
    k['stroller'] = True          # 席の間隔が広いのを実写で確認
    x['kids'] = k

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print()
    print('更新:', x['name'])
    print('  visited =', x['visited'], '/ 写真', len(x['photos']), '枚')


if __name__ == '__main__':
    main()
