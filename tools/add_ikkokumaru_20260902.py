# -*- coding: utf-8 -*-
"""博多一黒丸(ラーメンスタジアム/キャナルシティ博多)を赤ピンで登録する(2026-09-02)。

1st STEP の時点で店には行っているので、動画の完成を待たずに登録する(スキルの運用ルール)。

写真の方針:
・暖簾のカットは**行列の客が必ず写る**ので、暖簾の部分だけを切り出して人を枠外に出す
  (麺街道・飛牛と同じ方針。モザイクを盛るより構図で外すほうがきれい)
・キッズチェアは在庫が積んである実写があり、人が写っていないのでそのまま使える
"""
import os, json, io, subprocess
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'map')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\ラーメンスタジアムいっこくまる編'
P = os.path.join(ROOT, 'data', 'spots.json')
FF = (r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages'
      r'\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe')

SLUG = 'ikkokumaru_rasuta'

# 写真(静止画): (元ファイル, 出力名, 上から何割で切るか)  ※Noneなら切らない
PHOTOS = [
    ('写真 2026-09-02 12 18 38.jpg', '%s_01_暖簾.jpg' % SLUG, 0.46),   # 下は行列なので落とす
    ('写真 2026-09-02 12 44 01.jpg', '%s_02_紹介パネル.jpg' % SLUG, None),
    ('写真 2026-09-02 12 43 10.jpg', '%s_03_キッズチェア.jpg' % SLUG, None),
    ('写真 2026-09-02 12 35 29.jpg', '%s_04_サイドメニュー.jpg' % SLUG, None),
]
# 動画から抜く静止画: (元動画, 秒, 出力名)
FRAMES = [
    ('動画 2026-09-02 12 26 14.mov', 1.6, '%s_05_ラーメン.jpg' % SLUG),
    ('動画 2026-09-02 12 32 59.mov', 1.0, '%s_06_明太丼.jpg' % SLUG),
    ('動画 2026-09-02 12 16 45.mov', 6.4, '%s_07_ラースタ入口.jpg' % SLUG),
]

VERDICT = (
    '2026年4月17日にリニューアルしたラーメンスタジアム(キャナルシティ博多センターウォーク5F)の8店のひとつ。'
    '2001年にこの場所で豚骨醤油に挑んだ伝説の店が25年ぶりに復活した。'
    '当時の店長は後に博多一幸舎を創業した吉村幸助。'
    'ラーメン950円・赤ラーメン1,050円・博多明太丼550円・替玉150円(半替玉100円)。'
    '⭐**木製のキッズチェア(背もたれ+肘掛け付き)が用意されている**・カウンター席・'
    'ベビーフードの持ち込みもできた。'
    'ラースタは全店に**ミニラーメン**があるのではしごもできる。'
    '※追加注文は現金のみ。営業11:00〜23:00。'
)


def save(im, name, w=1080):
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(os.path.join(MAP, 'photos', name), quality=90)
    return im


def thumb(im, name):
    w = int(im.height * 4 / 5)
    if w <= im.width:
        x = (im.width - w) // 2
        box = (x, 0, x + w, im.height)
    else:
        box = (0, 0, im.width, min(int(im.width * 5 / 4), im.height))
    im.crop(box).resize((240, 300), Image.LANCZOS).save(
        os.path.join(MAP, 'thumbs', name), quality=90)


def main():
    os.makedirs(os.path.join(MAP, 'photos'), exist_ok=True)
    names = []
    hero = None
    for f, out, ratio in PHOTOS:
        im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, f))).convert('RGB')
        if ratio:
            im = im.crop((0, 0, im.width, int(im.height * ratio)))
        r = save(im, out)
        if hero is None:
            hero = r
        names.append(out)
        print('写真:', out, r.size)

    for f, ss, out in FRAMES:
        tmp = os.path.join(MAP, 'photos', '_tmp.png')
        subprocess.run([FF, '-y', '-v', 'error', '-ss', str(ss), '-i', os.path.join(SRC, f),
                        '-frames:v', '1', tmp], check=True)
        im = Image.open(tmp).convert('RGB')
        r = save(im, out)
        os.remove(tmp)
        names.append(out)
        print('抜き出し:', out, r.size)

    thumb(hero, '%s.jpg' % SLUG)
    print('サムネ: %s.jpg' % SLUG)

    sp = json.load(io.open(P, encoding='utf-8'))
    if any(s['id'] == SLUG for s in sp):
        print('既にある:', SLUG); return
    sp.append({
        "id": SLUG,
        "name": "博多一黒丸 ラーメンスタジアム店",
        "area": "キャナルシティ博多",
        "city": "福岡市博多区",
        "pref": "福岡県",
        "genre": "豚骨醤油ラーメン",
        "lat": 33.589628, "lng": 130.411195,
        "address": "福岡県福岡市博多区住吉1-2-22 キャナルシティ博多 センターウォーク5F ラーメンスタジアム",
        "visited": "2026-09-02",
        "with": "family",
        "kids": {"stroller": None, "diaper": None, "tatami": False,
                 "kidsChair": True, "serveMin": None, "noise": None},
        "verdict": VERDICT,
        "video": {"youtube": None, "tiktok": None, "instagram": None},
        "thumb": "%s.jpg" % SLUG,
        "photos": names,
        "wish": False,
    })
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print()
    print('赤ピン追加: 博多一黒丸 ラーメンスタジアム店 / 全%d件' % len(sp))


if __name__ == '__main__':
    main()
