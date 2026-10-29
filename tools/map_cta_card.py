# -*- coding: utf-8 -*-
"""
動画の締めに使う「マップ操作カード」に、マップの育ち(掲載件数・今週の増分)を焼き込む。

  python tools/map_cta_card.py            # 枠付き/枠のみ の両方を書き出す
  python tools/map_cta_card.py --dry      # 件数と文言だけ表示

入力: 5.共通素材/マップ操作_枠付き_4.4秒_base.mp4 / マップ操作_枠のみ_4.4秒_base.mp4 (件数なしの原版)
出力: 5.共通素材/マップ操作_枠付き_4.4秒.mp4 / マップ操作_枠のみ_4.4秒.mp4 (従来どおりの名前。build 側は変更不要)

件数の数え方は map/index.html の renderGrowbar() と同じ:
  掲載数 = until が今日より前のものを除いた全件 / 今週 = added が7日以内
2nd/エモ回を組む前にこれを1回回すと、その時点の件数がカードに入る(2026-10-29 ユーザー要望「育っているところを加えて」)。
"""
import json, os, sys, datetime, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON = os.path.join(os.path.dirname(ROOT), '5.共通素材')
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
FONT = os.path.expanduser(r'~\.claude\skills\short-video\assets\MPLUSRounded1c-Black.ttf')
W, H = 1080, 1920
PILL_TOP, PILL_H = 164, 74          # カード上端(250)の上・SNSの上帯(〜130)の下
GREEN, YELLOW, WHITE = (31, 122, 46), (255, 229, 84), (255, 255, 255)


def counts(today=None):
    today = today or datetime.date.today()
    d = json.load(open(os.path.join(ROOT, 'data', 'spots.json'), encoding='utf-8'))
    live = [s for s in d if not s.get('until') or s['until'] >= today.isoformat()]
    week = 0
    for s in live:
        a = s.get('added')
        if a:
            try:
                if (today - datetime.date.fromisoformat(a)).days <= 7:
                    week += 1
            except ValueError:
                pass
    return len(live), week


def pill_png(total, week, out):
    f = ImageFont.truetype(FONT, 42)
    left = f'九州の子連れおでかけ {total:,}件'
    right = f'今週 +{week:,}件' if week else ''
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    gap, pad = 34, 40
    lw = dr.textlength(left, font=f)
    rw = dr.textlength(right, font=f) if right else 0
    pw = int(lw + (gap + rw if right else 0) + pad * 2)
    x0 = (W - pw) // 2
    y0, y1 = PILL_TOP, PILL_TOP + PILL_H
    # 影
    dr.rounded_rectangle((x0 + 3, y0 + 5, x0 + pw + 3, y1 + 5), radius=PILL_H // 2, fill=(0, 0, 0, 90))
    dr.rounded_rectangle((x0, y0, x0 + pw, y1), radius=PILL_H // 2, fill=GREEN + (235,))
    ty = y0 + (PILL_H - 42) // 2 - 6
    dr.text((x0 + pad, ty), left, font=f, fill=WHITE)
    if right:
        rx = x0 + pad + lw + gap
        # 区切りの小さな丸
        cx = rx - gap / 2
        dr.ellipse((cx - 5, y0 + PILL_H / 2 - 5, cx + 5, y0 + PILL_H / 2 + 5), fill=(255, 255, 255, 170))
        dr.text((rx, ty), right, font=f, fill=YELLOW)
    im.save(out)
    return left + ((' ' + right) if right else '')


def burn(base, overlay, out):
    cmd = [FF, '-v', 'error', '-y', '-i', base, '-loop', '1', '-i', overlay,
           '-filter_complex',
           '[1:v]format=rgba,fade=in:st=0.25:d=0.35:alpha=1[p];[0:v][p]overlay=0:0:shortest=1,format=yuv420p[v]',
           '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-r', '30',
           '-c:a', 'copy', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)


def main():
    dry = '--dry' in sys.argv
    total, week = counts()
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'map_cta_pill.png')
    text = pill_png(total, week, tmp)
    print(f'掲載 {total:,}件 / 今週 +{week:,}件 → 「{text}」')
    if dry:
        return
    for name in ('マップ操作_枠付き_4.4秒', 'マップ操作_枠のみ_4.4秒'):
        base = os.path.join(COMMON, name + '_base.mp4')
        out = os.path.join(COMMON, name + '.mp4')
        if not os.path.exists(base):
            # 初回: 現行ファイルを原版として退避
            os.replace(out, base)
        burn(base, tmp, out)
        print('wrote', out)


if __name__ == '__main__':
    main()
