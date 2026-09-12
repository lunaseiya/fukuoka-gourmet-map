# -*- coding: utf-8 -*-
"""カルーセル画像(1080x1350)を **YouTube Shorts 用のスライドショー動画(1080x1920)** にする。
【2026-09-13ユーザー確定「YouTube版も」】

YouTubeは静止画のカルーセル投稿ができないので、同じ画像を動画にして Shorts に出す。

■ 作り方(short-video スキルの作法に合わせる)
  ・4:5 の画像を 9:16 に載せるので、**背景は自分自身のブラー**で埋める
    (F型の fit_wide と同じ手。上下に無地の帯を出さない)
  ・1枚ずつゆっくりズームイン。**zoompan は2倍解像度で処理してlanczosで縮小**
    (s=1080x1920 で直接出すと階段状にガタつく)
  ・**必ず2段階レンダ**: 各スライドを中間mp4にしてから concat。
    14枚を一発で繋ぐとタイムアウトで0バイトが残る事故がある
  ・BGM は swing_swing.mp3 固定(非ホテル回)。スライド切替に「パッ」を置く
  ・音量は完成品を volumedetect して mean -14〜-16dB / max -1〜-6dB に入れる

使い方:
    python tools/event_slideshow.py --dir data/carousel_2026-09-14
    python tools/event_slideshow.py --dir ... --sec 3.5 --out "YouTube_今週.mp4"
"""
import argparse, glob, io, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin'
SHORT = r'C:\Users\totor\Dropbox\ショート動画用'
BGM = os.path.join(SHORT, '2.BGM', 'swing_swing.mp3')
SE = os.path.join(SHORT, '3.効果音', 'パッ.mp3')
W, H = 1080, 1920


def run(a):
    r = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print('FFMPEG ERROR\n', ' '.join(a[-5:]), '\n', r.stderr[-1200:])
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--sec', type=float, default=3.5)
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    d = os.path.abspath(a.dir)
    imgs = sorted(glob.glob(os.path.join(d, '*.jpg')))
    if not imgs:
        raise SystemExit('画像が無い: ' + d)
    tmp = os.path.join(d, '_slides')
    os.makedirs(tmp, exist_ok=True)
    nf = max(2, int(a.sec * 30))
    print('%d枚 × %.1f秒 = %.1f秒' % (len(imgs), a.sec, len(imgs) * a.sec))

    # ① 各スライドを中間mp4へ(背景=自分自身のブラー / ゆっくりズーム)
    parts = []
    for i, p in enumerate(imgs):
        o = os.path.join(tmp, 's%02d.mp4' % i)
        vf = (
            # 背景: 9:16を覆うまで拡大してブラー+わずかに暗く
            '[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,'
            'gblur=sigma=34,eq=brightness=-0.06[bg];'
            # 前景: 幅いっぱい(1080)で中央に
            '[0:v]scale=%d:-1:flags=lanczos[fg];'
            '[bg][fg]overlay=(W-w)/2:(H-h)/2,'
            # 2倍解像度でズームしてからlanczosで縮小(階段状のガタつきを防ぐ)
            'scale=%d:%d:flags=lanczos,'
            "zoompan=z='1.0+0.055*in/%d':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            ':d=1:s=%dx%d:fps=30,scale=%d:%d:flags=lanczos,setsar=1[v]'
            % (W, H, W, H, W, W * 2, H * 2, nf, W * 2, H * 2, W, H))
        run([os.path.join(FF, 'ffmpeg'), '-y', '-hide_banner', '-loglevel', 'error',
             '-loop', '1', '-framerate', '30', '-t', '%.3f' % a.sec, '-i', p,
             '-filter_complex', vf, '-map', '[v]', '-an',
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
             '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', o])
        parts.append(o)
        print('  %2d/%d %s' % (i + 1, len(imgs), os.path.basename(p)[:34]), flush=True)

    # ② 連結
    lst = os.path.join(tmp, 'list.txt')
    io.open(lst, 'w', encoding='utf-8').write(
        '\n'.join("file '%s'" % os.path.basename(x) for x in parts) + '\n')
    vid = os.path.join(tmp, 'video.mp4')
    run([os.path.join(FF, 'ffmpeg'), '-y', '-hide_banner', '-loglevel', 'error',
         '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])

    # ③ 音: BGM + スライド切替のSE
    tot = len(imgs) * a.sec
    sin, sf, tags = [], [], []
    for i in range(len(imgs)):
        ms = int(i * a.sec * 1000)
        sin += ['-i', SE]
        sf.append('[%d:a]volume=0.40,adelay=%d|%d[s%d]' % (i, ms, ms, i))
        tags.append('[s%d]' % i)
    ses = os.path.join(tmp, 'se.wav')
    run([os.path.join(FF, 'ffmpeg'), '-y', '-hide_banner', '-loglevel', 'error'] + sin +
        ['-filter_complex', ';'.join(sf) + ';%samix=inputs=%d:duration=longest:normalize=0[o]'
         % (''.join(tags), len(tags)), '-map', '[o]', '-ar', '48000', '-t', '%.3f' % tot, ses])

    name = a.out or ('YouTube_スライドショー_%.0f秒.mp4' % tot)
    out = os.path.join(d, name)
    fc = ('[1:a]atrim=0:%.3f,asetpts=N/SR/TB,volume=0.55,'
          'afade=t=in:d=0.4,afade=t=out:st=%.2f:d=1.5[b];'
          '[2:a]volume=1.0[s];[b][s]amix=inputs=2:duration=first:normalize=0,'
          'alimiter=limit=0.85:level=false[a]' % (tot, tot - 1.5))
    run([os.path.join(FF, 'ffmpeg'), '-y', '-hide_banner', '-loglevel', 'error',
         '-i', vid, '-ss', '0.4', '-i', BGM, '-i', ses,
         '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-movflags', '+faststart', '-t', '%.3f' % tot, out])
    print()
    print('書き出し:', out)
    r = subprocess.run([os.path.join(FF, 'ffmpeg'), '-hide_banner', '-i', out,
                        '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    for ln in r.stderr.splitlines():
        if 'mean_volume' in ln or 'max_volume' in ln:
            print('  ' + ln.split('] ')[-1])
    for p in parts:
        os.remove(p)


if __name__ == '__main__':
    main()
