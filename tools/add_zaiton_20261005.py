# -*- coding: utf-8 -*-
"""ざいとん 香椎本店(香椎駅前・既存 spc4bd06a47d)を赤ピン化(2024-09-16訪問・素材の撮影日)
   素材: ショート動画用/東区香椎駅　ざいとん(iPhone 4K HEVC / HLG HDR → トーンマップして抜く)
   子連れ設備は撮影なし(カウンター中心のラーメン店)なので kids は null のまま
   券売機写真(2024年の価格)と 8685 の営業時間ポスター(古い)は使わない
   ファイル名の接頭辞(未使用_ 等)は変わりうるのでクリップ番号で glob する"""
import glob, io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\東区香椎駅　ざいとん'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
VF = 'zscale=t=linear:npl=203,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_zaiton')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'spc4bd06a47d'
sp = [x for x in s if x['id'] == SID]
assert len(sp) == 1
sp = sp[0]


def clip(cid):
    f = glob.glob(os.path.join(SRC, '*_%s_*.mov' % cid))
    assert len(f) == 1, (cid, f)
    return f[0]


def img(cid, ss):
    t = os.path.join(PH, '_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(cid),
                    '-frames:v', '1', '-vf', VF, '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t); return im


# サムネ: 「らーめん・まぜそば ざいとん」の看板(8681 0.5s)
#   下端の店先に客が座っている → 4:5 を上端寄せで切り出して人を枠に入れない
#   (人は縦 3120px 以降、切り出しは 0〜2700px)
th = img('8681', 0.5)
ImageOps.fit(th, (240, 300), Image.LANCZOS, centering=(0.5, 0.0)).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (クリップ番号, 秒, 内容)
items = [('8687', 3.0, 'まぜそば'),
         ('8688', 2.3, 'まぜそばとご飯'),
         ('8692', 3.6, '追い飯')]
photos = []
for k, (cid, ss, lab) in enumerate(items, 1):
    im = img(cid, ss); im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

sp['visited'] = '2024-09-16'
sp['wish'] = False
sp['thumb'] = SID + '.jpg'
sp['photos'] = photos
sp['verdict'] = ('中華そばが名物のカウンター中心の小さな店(席数少なめ・行列あり)、駐車場なし、食券制。'
                 'まぜそばはご飯付きで、残ったタレに入れて追い飯にできる。'
                 '営業時間・定休日は情報源で食い違うので要確認。')

ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
