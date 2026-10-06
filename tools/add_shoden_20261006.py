# -*- coding: utf-8 -*-
"""博多魚菜と串焼き百珍 笑伝(えでん/博多区店屋町)を新規・赤ピン登録(visited=2023-09-16・動画素材の作成日)
   素材: ショート動画用/笑伝(iPhone 1080p SDR .mov → フレーム抜き出し)
   座標: geocoding.jp(住所「福岡県福岡市博多区店屋町2-20」で取得)
   with=friends(夜の居酒屋・子連れ外出ではない)→ README準拠で kids=null
   人の映り込み: 人が枠に入らない位置で切り出す(豚バラ=下端の指を落とす/つくね=上の人物と左の手袋を落とす)"""
import io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\笑伝'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_shoden')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'shoden-hakata'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '笑伝' in x['name'] or '百珍' in x['name']]


def img(name, ss=0, box=None):
    """box = 比率 (x0, y0, x1, y1) で切り出し"""
    t = os.path.join(tempfile.gettempdir(), '_shoden_t.jpg')  # Dropbox配下だと同期がロックするので外に置く
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', os.path.join(SRC, name),
                    '-frames:v', '1', '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


# サムネ: 灯りの入った「笑伝」の行灯看板(4390 0.5s・人なし)
ImageOps.fit(img('未使用_4390_118s.mov', 0.5), (240, 300), Image.LANCZOS, centering=(0.4, 0.45)).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (素材, 秒, 切り出し, 内容)
items = [('未使用_4390_118s.mov', 6.5, None, '黄色の暖簾'),
         ('未使用_4396_11s.mov', 8.0, (0, 0, 1, 0.78), '豚バラ串'),
         ('未使用_4400_6s.mov', 1.0, None, '雲仙ハム'),
         ('未使用_4399_18s.mov', 15.5, (0.21, 0.43, 1, 0.86), 'つくね')]
photos = []
for k, (n, ss, box, lab) in enumerate(items, 1):
    im = img(n, ss, box); im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '博多魚菜と串焼き百珍 笑伝', 'area': '呉服町', 'city': '福岡市博多区', 'pref': '福岡県',
    'genre': '居酒屋・串焼き', 'lat': 33.596225, 'lng': 130.409822, 'address': '福岡県福岡市博多区店屋町2-20',
    'visited': '2023-09-16', 'with': 'friends', 'category': 'gourmet', 'wish': False,
    'kids': None,
    'verdict': '長崎の食材にこだわる串焼き居酒屋(笑伝=えでん)。名物は雲仙スーパーポークの豚バラ、自家製手ごねつくね、'
               '「ハム界の反逆児」雲仙ハム。⚠夜の居酒屋なので子連れ向きではない。'
               '夜営業(17時〜、閉店時刻は情報源で異なる・要確認)。呉服町駅から徒歩約3分。TEL 092-263-3226。',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
