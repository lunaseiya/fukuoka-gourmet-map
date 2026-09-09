# -*- coding: utf-8 -*-
"""博多めん街道(博多デイトス2F)の12店をマップに整備する(2026-09-02)。

・未登録の6店を新規追加(青ピン。訪問したのは どさんこ だけなので)
・既存6店を含む全12店に**店頭の写真**を付ける
・**デイトス2Fの多目的トイレにおむつ替え台とベビーチェアがある**(実写で確認)ので、
  全12店の kids.diaper を "facility"(店には無いが同じ建物にある)にする

写真は**看板の部分だけを切り出す**。店頭の引きは客と通行人が必ず写るので、
モザイクを大量に掛けるより「そもそも人を枠に入れない」ほうがきれい(飛牛・プロントと同じ方針)。
"""
import os, json, io
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'map')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\博多駅の麺街道'
P = os.path.join(ROOT, 'data', 'spots.json')

LAT, LNG = 33.59113, 130.421399          # どさんこと同じ建物(博多デイトス2F)
ADDR = '福岡県福岡市博多区博多駅中央街1-1 博多デイトス2F'
AREA = '博多駅中央街(博多めん街道)'
DIAPER = ('⭐デイトス2Fの多目的トイレに**おむつ替え台とベビーチェア**がある(実写で確認)。'
          '店内には無いが同じフロアなので困らない。')

# (写真ファイル, スラッグ, 店名, ジャンル, 説明, 看板を切る高さの割合)
SHOPS = [
    ('写真 2026-08-28 12 50 26.jpg', 'nagahamano1_deitos', '長浜ナンバーワン 博多デイトス店',
     'ラーメン(長浜)', '長浜屋台系の老舗。', 0.50),
    ('写真 2026-08-28 12 51 15.jpg', 'kanetora_deitos', '麺や兼虎 博多デイトス店',
     'つけ麺・ラーメン', '辛misoつけ麺で知られる天神の人気店の博多駅店。', 0.58),
    ('写真 2026-08-28 12 52 05.jpg', 'darma_deitos', '元祖博多だるま 博多デイトス店',
     '豚骨ラーメン', '昭和38年創業の博多豚骨。', 0.40),
    ('写真 2026-08-28 12 52 22.jpg', 'ikkousha_deitos', '博多一幸舎 博多デイトス店',
     '豚骨ラーメン', '泡系の豚骨で世界展開する博多の有名店。', 0.42),
    ('写真 2026-08-28 12 52 37.jpg', 'tsukiya_deitos', '博多醤油ラーメン 月や 博多デイトス店',
     '醤油ラーメン', '豚骨だらけの博多で醤油を出す店。', 0.40),
    ('写真 2026-08-28 12 53 46.jpg', 'naoto_deitos', '博多非豚骨 なお人 博多デイトス店',
     '鶏白湯ラーメン', '博多濃厚鶏白湯らぁ麺。**非豚骨**を掲げている。', 0.62),
]
# 既存スポットに写真だけ足すもの (写真ファイル, 既存の名前に含まれる語, 切る割合)
EXISTING = [
    ('写真 2026-08-28 12 51 05.jpg', '名島亭 博多デイトス店', 0.40),
    ('写真 2026-08-28 12 51 53.jpg', 'らーめん二男坊 博多デイトス店', 0.40),
    ('写真 2026-08-28 12 53 08.jpg', '博多らーめんShinShin 博多デイトス店', 0.42),
    ('写真 2026-08-28 12 53 18.jpg', 'ラーメン海鳴 博多デイトス店', 0.42),
    ('写真 2026-08-28 12 51 35.jpg', '博多川端どさんこ 博多デイトス店', 0.46),
]
# おむつ替え設備の写真(全店で共有する)
DIAPER_PHOTO = 'デイトス内(麺街道と少し離れています).jpg'


def sign(path, ratio):
    """看板の部分(上から ratio まで)を切って幅1080で返す。人は下側にいるので枠外に出る。"""
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, path))).convert('RGB')
    im = im.crop((0, 0, im.width, int(im.height * ratio)))
    return im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)


def thumb(im, name):
    w = int(im.height * 4 / 5)
    if w <= im.width:
        box = ((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height)
    else:
        h = int(im.width * 5 / 4)
        box = (0, 0, im.width, min(h, im.height))
    im.crop(box).resize((240, 300), Image.LANCZOS).save(
        os.path.join(MAP, 'thumbs', name), quality=90)


def main():
    os.makedirs(os.path.join(MAP, 'photos'), exist_ok=True)
    dp = ImageOps.exif_transpose(Image.open(os.path.join(SRC, DIAPER_PHOTO))).convert('RGB')
    dp = dp.resize((1080, round(dp.height * 1080 / dp.width)), Image.LANCZOS)
    dp.save(os.path.join(MAP, 'photos', 'deitos_omutsu.jpg'), quality=90)
    print('共有写真 deitos_omutsu.jpg', dp.size)

    sp = json.load(io.open(P, encoding='utf-8'))
    have = {s['id'] for s in sp}
    by_name = {s['name']: s for s in sp}

    n_new = 0
    for f, slug, name, genre, note, ratio in SHOPS:
        im = sign(f, ratio)
        pn = '%s_01.jpg' % slug
        im.save(os.path.join(MAP, 'photos', pn), quality=90)
        thumb(im, '%s.jpg' % slug)
        if slug in have:
            print('既にある:', slug); continue
        sp.append({
            "id": slug, "name": name, "area": AREA, "city": "福岡市博多区", "pref": "福岡県",
            "genre": genre, "lat": LAT, "lng": LNG, "address": ADDR,
            "visited": None, "with": "family",
            "kids": {"stroller": None, "diaper": "facility", "tatami": False,
                     "kidsChair": None, "serveMin": None, "noise": None},
            "verdict": '博多めん街道(博多デイトス2F)の12店のひとつ。' + note + DIAPER,
            "video": {"youtube": None, "tiktok": None, "instagram": None},
            "thumb": '%s.jpg' % slug,
            "photos": [pn, 'deitos_omutsu.jpg'],
            "wish": True,
        })
        n_new += 1
        print('追加: %-34s' % name[:34])

    n_up = 0
    for f, name, ratio in EXISTING:
        s = by_name.get(name)
        if not s:
            print('!! 見つからない:', name); continue
        slug = s['id']
        im = sign(f, ratio)
        pn = '%s_men01.jpg' % slug
        im.save(os.path.join(MAP, 'photos', pn), quality=90)
        ph = s.get('photos') or []
        for x in (pn, 'deitos_omutsu.jpg'):
            if x not in ph:
                ph.append(x)
        s['photos'] = ph
        if not s.get('thumb'):
            thumb(im, '%s.jpg' % slug)
            s['thumb'] = '%s.jpg' % slug
        k = s.setdefault('kids', {}) or {}
        if k.get('diaper') is None:
            k['diaper'] = 'facility'
        s['kids'] = k
        if DIAPER not in (s.get('verdict') or ''):
            s['verdict'] = (s.get('verdict') or '') + ' ' + DIAPER
        n_up += 1
        print('写真追加: %-34s' % name[:34])

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print()
    print('新規%d件 / 写真追加%d件 / 全%d件' % (n_new, n_up, len(sp)))


if __name__ == '__main__':
    main()
