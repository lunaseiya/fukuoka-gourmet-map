# -*- coding: utf-8 -*-
"""カルーセルの**投稿時の見え方**のサンプルを作る【2026-09-19ユーザー要望「出方のサンプル」】

3枚出す:
  1. `_サンプル_投稿イメージ.jpg` … Instagram のフィードに出たときの見た目
     (アカウント行 + 4:5の画像 + ページの点 + キャプションの冒頭)
  2. `_サンプル_プロフィール格子.jpg` … **プロフィールの格子は1:1で中央を切る**ので、
     表紙の文字が切れないかを確認する用。ここで切れていたら表紙を作り直す
  3. `_サンプル_13枚一覧.jpg` … 13枚の流れ(絵コンテ)

使い方:
    python tools/carousel_preview.py --dir data/carousel_sw_2026-09-19
"""
import argparse, glob, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw
from event_carousel import font, rounded, shadow, ROUND, MEI, MEIB

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
AVATAR = os.path.join(ROOT, 'assets', 'profile_avatar.png')
HANDLE = 'るな@福岡子育てグルメ'
INK, SUB, LINE = (34, 32, 30), (120, 116, 112), (222, 219, 214)


def pages(d):
    fs = [p for p in sorted(glob.glob(os.path.join(d, '*.jpg')))
          if not os.path.basename(p).startswith(('_', 'YouTube'))]
    return fs


def feed(cover, cap):
    """フィードでの見た目。**画像は4:5のまま丸ごと出る**(切られない)"""
    W = 1080
    im = Image.new('RGB', (W, 2120), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # アカウント行
    if os.path.exists(AVATAR):
        a = Image.open(AVATAR).convert('RGBA').resize((84, 84), Image.LANCZOS)
        im.paste(a, (28, 26), a)
    d.text((132, 50), HANDLE, font=font(MEIB, 34), fill=INK)
    d.text((132, 92), '福岡市 · 子育てグルメ', font=font(MEI, 26), fill=SUB)
    d.text((W - 44, 62), '···', font=font(MEIB, 36), fill=INK, anchor='rm')
    # 本体(4:5)
    ph = Image.open(cover).convert('RGB').resize((W, int(W * 5 / 4)), Image.LANCZOS)
    im.paste(ph, (0, 140))
    y = 140 + ph.height
    # ページの点
    n = 13
    cx = W // 2 - (n * 18) // 2
    for i in range(n):
        c = (58, 132, 222) if i == 0 else (205, 203, 200)
        d.ellipse((cx + i * 18, y + 26, cx + i * 18 + 10, y + 36), fill=c)
    y += 62
    # アクション行
    for i, s in enumerate(('♡', '♡', '↗')):
        d.text((34 + i * 66, y + 22), s, font=font(MEIB, 44), fill=INK)
    d.text((W - 40, y + 22), '📌', font=font(MEIB, 40), fill=INK, anchor='ra')
    y += 96
    d.text((34, y), 'いいね！ 128件', font=font(MEIB, 30), fill=INK)
    y += 48
    # キャプションの冒頭(フィードでは3行ほどで「続きを読む」になる)
    fm = font(MEI, 29)
    rows = [r for r in cap.split('\n') if r.strip()][:3]
    d.text((34, y), HANDLE + ' ', font=font(MEIB, 29), fill=INK)
    y += 42
    for r in rows:
        d.text((34, y), r[:40], font=fm, fill=INK)
        y += 40
    d.text((34, y + 4), '… 続きを読む', font=fm, fill=SUB)
    return im.crop((0, 0, W, min(2120, y + 70)))


def grid(cover):
    """プロフィールの格子。**1:1で中央を切る**ので表紙の端が落ちる"""
    W = 1080
    im = Image.new('RGB', (W, 1290), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 34), 'プロフィールの格子(1:1で中央を切られる)',
           font=font(MEIB, 36), fill=INK, anchor='ma')
    src = Image.open(cover).convert('RGB')
    s = src.width                                  # 4:5 → 1:1 は上下を切る
    top = (src.height - s) // 2
    sq = src.crop((0, top, s, top + s)).resize((640, 640), Image.LANCZOS)
    im.paste(sq, (220, 110))
    d.rectangle((220, 110, 220 + 640, 110 + 640), outline=LINE, width=3)
    d.text((W // 2, 790), '↓ 切られる前(投稿本体は4:5で全部出る)',
           font=font(MEI, 30), fill=SUB, anchor='ma')
    full = src.resize((320, 400), Image.LANCZOS)
    im.paste(full, (380, 840))
    dd = ImageDraw.Draw(im)
    # 切られる帯を薄く塗る
    ov = Image.new('RGBA', (320, int(400 * (top / src.height))), (206, 57, 52, 90))
    im.paste(Image.alpha_composite(
        Image.new('RGB', ov.size, (0, 0, 0)).convert('RGBA'), ov).convert('RGB'),
        (380, 840), ov)
    im.paste(Image.alpha_composite(
        Image.new('RGB', ov.size, (0, 0, 0)).convert('RGBA'), ov).convert('RGB'),
        (380, 840 + 400 - ov.height), ov)
    dd.rectangle((380, 840, 380 + 320, 840 + 400), outline=LINE, width=3)
    dd.text((W // 2, 1256), '赤い帯が格子で落ちる部分', font=font(MEI, 26),
            fill=SUB, anchor='ma')
    return im


def sheet(fs):
    """13枚の流れ"""
    C, TW, TH, PAD = 4, 330, 412, 18
    R = (len(fs) + C - 1) // C
    W = PAD + C * (TW + PAD)
    H = 78 + R * (TH + 46)
    im = Image.new('RGB', (W, H), (247, 245, 240))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 22), 'スワイプの流れ (%d枚)' % len(fs), font=font(ROUND, 42),
           fill=INK, anchor='ma')
    for i, p in enumerate(fs):
        x = PAD + (i % C) * (TW + PAD)
        y = 78 + (i // C) * (TH + 46)
        t = Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS)
        im.paste(t, (x, y))
        d.rectangle((x, y, x + TW, y + TH), outline=LINE, width=2)
        nm = re.sub(r'^\d+_', '', os.path.splitext(os.path.basename(p))[0])
        d.text((x + TW // 2, y + TH + 8), '%d. %s' % (i + 1, nm),
               font=font(MEI, 24), fill=SUB, anchor='ma')
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    a = ap.parse_args()
    fs = pages(a.dir)
    if not fs:
        print('!! 画像が無い:', a.dir); return
    capf = os.path.join(a.dir, '_キャプション_instagram.txt')
    cap = io.open(capf, encoding='utf-8').read() if os.path.exists(capf) else ''
    out = [('_サンプル_投稿イメージ.jpg', feed(fs[0], cap)),
           ('_サンプル_プロフィール格子.jpg', grid(fs[0])),
           ('_サンプル_13枚一覧.jpg', sheet(fs))]
    for nm, im in out:
        p = os.path.join(a.dir, nm)
        im.convert('RGB').save(p, quality=92)
        print('  %s  %dx%d' % (nm, im.width, im.height))


if __name__ == '__main__':
    main()
