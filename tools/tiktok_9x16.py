# -*- coding: utf-8 -*-
"""カルーセルの4:5画像(1080x1350)から **TikTok写真投稿用の9:16版(1080x1920)** を作る。
【2026-09-13ユーザー質問「TikTokやInstagramで画像の大きさ調節は自動でされる？」への対応】

  ・Instagram カルーセル … 4:5 は正式対応。**そのまま入る**(ただし1枚目の比率に全枚が揃う)
  ・Instagram グリッド    … 3:4 に切られる。左右が約34pxずつ落ちるが、
                            カードの余白64pxの内側に文字があるので切れない
  ・TikTok 写真投稿       … 9:16 枠で表示され**上下に自動でブラー帯が入る**。
                            → 見栄えのために**こちらで9:16に作っておく**(この스크립트)

背景は自分自身のブラー(F型の fit_wide と同じ手)。前景は幅1080でそのまま中央に置くので
**文字は一切切れない**。

使い方:
    python tools/tiktok_9x16.py --dir data/carousel_2026-09-14
"""
import argparse, glob, os, sys

sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageFilter, ImageEnhance
W, H = 1080, 1920


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    a = ap.parse_args()
    d = os.path.abspath(a.dir)
    out = os.path.join(d, 'tiktok_9x16')
    os.makedirs(out, exist_ok=True)
    n = 0
    for p in sorted(glob.glob(os.path.join(d, '*.jpg'))):
        im = Image.open(p).convert('RGB')
        s = max(W / im.width, H / im.height)
        bg = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        bx, by = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(34))
        bg = ImageEnhance.Brightness(bg).enhance(0.94)
        fg = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
        bg.paste(fg, (0, (H - fg.height) // 2))
        bg.save(os.path.join(out, os.path.basename(p)), quality=92)
        n += 1
    print('%d枚 → %s' % (n, out))


if __name__ == '__main__':
    main()
