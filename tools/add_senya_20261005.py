# -*- coding: utf-8 -*-
"""麺どころ 千屋(香椎駅前・既存 sp84245d44b1)を赤ピン化(2024-06-15訪問・素材の撮影日)
   素材: ショート動画用/東区香椎　千屋(iPhone 4K HEVC / HLG HDR → トーンマップして抜く)
   子連れ設備は撮影なし(深夜営業のラーメン・居酒屋カウンター店)なので kids は null のまま"""
import io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\東区香椎　千屋'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
VF = 'zscale=t=linear:npl=203,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_senya')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'sp84245d44b1'
sp = [x for x in s if x['id'] == SID]
assert len(sp) == 1
sp = sp[0]


def img(name, ss):
    t = os.path.join(PH, '_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', os.path.join(SRC, name),
                    '-frames:v', '1', '-vf', VF, '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t); return im


def mosaic(im, box, block=16):
    r = im.crop(box); w, h = r.size
    r = r.resize((max(1, w // block), max(1, h // block)), Image.BILINEAR).resize((w, h), Image.NEAREST)
    im.paste(r, box)


# サムネ: 扉の大きな「千屋」ロゴ(7475 4.3s)
#   ロゴ上のガラス越しにカウンター内の人影(ボケ)が2つ → 4K座標でモザイク
th = img('未使用_7475_21s.mov', 4.3)
for b in [(860, 1530, 1090, 1730), (1290, 1630, 1430, 1730)]:
    mosaic(th, b, block=48)
ImageOps.fit(th, (240, 300), Image.LANCZOS, centering=(0.5, 0.6)).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (素材, 秒, 内容, モザイク矩形[幅1080基準])
items = [('未使用_7475_21s.mov', 1.9, '入口', [(540, 780, 640, 870)]),   # 扉のガラス越しに店内の客の頭が小さく写る
         ('未使用_7474_14s.mov', 7.5, '深夜営業ポスター', []),
         ('未使用_7480_74s.mov', 2.8, 'ラーメン', [])]
photos = []
for k, (n, ss, lab, boxes) in enumerate(items, 1):
    im = img(n, ss); im.thumbnail((1080, 1920), Image.LANCZOS)
    for b in boxes:
        mosaic(im, b)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

sp['visited'] = '2024-06-15'
sp['wish'] = False
sp['thumb'] = SID + '.jpg'
sp['photos'] = photos
sp['verdict'] = ('西鉄香椎駅から徒歩1分(39m)、香椎名店街内。11:30〜14:00/18:00〜翌2:30(L.O.翌2:30)と深夜まで営業。'
                 '日曜定休。20席(座敷・個室なし)、お子様連れOK(ホットペッパー)。TEL 092-671-0565。')

ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
