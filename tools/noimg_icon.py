# -*- coding: utf-8 -*-
"""IPコラボ回の「ポスターを出せない」を可愛く伝えるアイコン【2026-09-18】

ユーザー提案:
  「よそのSNSではグレーでしょうけども画像使ってるところもある。その場合に文章だと
    どうしても負けます。かといって文章だけだと読めば伝わりますが、読む段階に
    いたらない。…権利の都合上表示できないよアイコンを可愛く作るのとかどうでしょうか」

⚠**代替の会場写真は今は使えない**(2026-09-18に実測):
  ・IPで貼れない15件の会場(イオンモール9/大丸2/美術館2 等)は**自前写真を1枚も持っていない**
    (所持しているサムネ99枚・ギャラリー183枚は訪問した飲食店が中心)
  ・施設公式の og:image は**イオンモール全館で同一のロゴ画像**、大丸も common/ogp.png で、
    館の外観写真ではない
  → だから「可愛いアイコン + 文字を強くする」で戦うのが現実的。
    将来、訪問時に会場の外観を撮って map/thumbs に入れれば差し替えられる。

⚠絵文字フォントは使わない(PILで豆腐になる)。**図形で描く**。
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw

CREAM = (247, 240, 233, 255)
EDGE = (226, 190, 178, 255)
INK = (92, 74, 66, 255)
BLUSH = (244, 186, 178, 255)
RED = (206, 57, 52, 255)


def make(d=260, variant='frame'):
    """d = 一辺。variant: frame=額縁に照れ顔 / camera=カメラに斜線"""
    s = 4
    D = d * s
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    r = int(D * 0.20)
    g.rounded_rectangle([0, 0, D - 1, D - 1], r, fill=CREAM, outline=EDGE,
                        width=max(3, int(D * 0.035)))
    if variant == 'camera':
        # カメラの本体 + レンズ + 斜線
        bx0, by0, bx1, by1 = D * .18, D * .34, D * .82, D * .74
        g.rounded_rectangle([bx0, by0, bx1, by1], int(D * .07), outline=INK,
                            width=max(3, int(D * .035)))
        g.rounded_rectangle([D * .36, D * .25, D * .64, D * .36], int(D * .035),
                            outline=INK, width=max(3, int(D * .03)))
        cx, cy, rr = D * .5, D * .54, D * .13
        g.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=INK,
                  width=max(3, int(D * .035)))
        g.line([D * .22, D * .78, D * .78, D * .28], fill=RED, width=max(4, int(D * .055)))
    else:
        # 額縁の中に照れ顔(目は ^ ^ の弧、頬に赤み、口は小さな波)
        ew = D * 0.15
        for cx in (D * 0.34, D * 0.66):
            g.arc([cx - ew, D * .34, cx + ew, D * .34 + ew * 1.5],
                  start=200, end=340, fill=INK, width=max(3, int(D * .04)))
        for cx in (D * 0.24, D * 0.76):
            g.ellipse([cx - D * .055, D * .50, cx + D * .055, D * .50 + D * .08], fill=BLUSH)
        g.arc([D * .40, D * .50, D * .60, D * .64], start=20, end=160,
              fill=INK, width=max(3, int(D * .04)))
        # 右下に © の丸バッジ
        bx, by, br = D * .78, D * .78, D * .12
        g.ellipse([bx - br, by - br, bx + br, by + br], fill=RED)
        g.ellipse([bx - br * .52, by - br * .52, bx + br * .52, by + br * .52],
                  outline=(255, 255, 255, 255), width=max(2, int(D * .012)))
        g.line([bx - br * .22, by - br * .26, bx - br * .22, by + br * .26],
               fill=(255, 255, 255, 255), width=max(2, int(D * .016)))
    return im.resize((d, d), Image.LANCZOS)


if __name__ == '__main__':
    HERE = os.path.dirname(os.path.abspath(__file__))
    c = Image.new('RGB', (760, 340), (250, 247, 242))
    for i, v in enumerate(('frame', 'camera')):
        for j, d in enumerate((240, 130)):
            ic = make(d, v)
            c.paste(ic, (40 + i * 380 + j * 260, 40 + j * 60), ic)
    c.save(os.path.join(HERE, 'noimg_preview.png'))
    print('→ noimg_preview.png  (左=額縁に照れ顔 / 右=カメラに斜線)')
