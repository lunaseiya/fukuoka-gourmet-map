# -*- coding: utf-8 -*-
"""博多天ぷら ながおか(中央区今泉)を新規・赤ピン登録(visited=2024-08-05・動画素材の作成日/GPS 33.5834,130.3963)
   id はキャプションのリンク s/hakatatempura-nagaoka.html に合わせる
   素材: ショート動画用/天麩羅ながおか　今泉(iPhone HLG .mov → tonemap してフレーム抜き出し。clip id で glob)
   座標: geocoding.jp(住所「福岡県福岡市中央区今泉2-4-11」で取得。動画のGPSとも一致)
   with=friends(夜のカウンター居酒屋・子連れ外出ではない)→ README/スキル準拠で kids=null
   ⚠2026-04-05 リニューアルオープン。訪問・写真はリニューアル前
   人の映り込み: 8041 冒頭・8042 は他のお客さんが写るので使わない。サムネは 8041 2.5s の木の看板を
   人(左端)が入らない位置で切り出す。8052 はトリュフを削る手元(指)のみで顔なし
   料金は書かない(古い素材の金額は使わない)"""
import glob, io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\天麩羅ながおか　今泉'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
VF = 'zscale=t=linear:npl=203,tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p'  # HLG → SDR
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_nagaoka')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'hakatatempura-nagaoka'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if 'ながおか' in x['name']]


def clip(cid):
    m = sorted(glob.glob(os.path.join(SRC, '*_%s_*.mov' % cid)))
    assert m, cid
    return m[0]  # 8040/8041 は _2 付きの重複があるので先頭(無印)を使う


def img(cid, ss=0, box=None):
    """box = 比率 (x0, y0, x1, y1) で切り出し"""
    t = os.path.join(tempfile.gettempdir(), '_nagaoka_t.jpg')  # Dropbox配下だと同期がロックするので外に置く
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(cid), '-vf', VF,
                    '-frames:v', '1', '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


# サムネ: 入口の木の看板「博多天ぷら ながおか」(8041 2.5s。左端の店内の人は切り落とす)
ImageOps.fit(img('8041', 2.5, (0.25, 0.17, 0.93, 0.65)), (240, 300), Image.LANCZOS).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (clip id, 秒, 切り出し, 内容)
items = [('8047', 1.0, None, 'うにといくらのプリン'),
         ('8052', 10.0, None, 'トリュフを削るポテサラ'),
         ('8063', 1.0, None, '海老天'),
         ('8043', 0.5, None, '天ぷらネタの並び'),
         ('8044', 0.5, None, 'レモンサワー')]
photos = []
for k, (c, ss, box, lab) in enumerate(items, 1):
    im = img(c, ss, box); im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '博多天ぷら ながおか', 'area': '今泉', 'city': '福岡市中央区', 'pref': '福岡県',
    'genre': '天ぷら・居酒屋', 'lat': 33.583416, 'lng': 130.396353,
    'address': '福岡県福岡市中央区今泉2-4-11 メゾンドール今泉1F',
    'visited': '2024-08-05', 'with': 'friends', 'category': 'gourmet', 'wish': False,
    'kids': None,
    'verdict': '⭐天ぷら居酒屋の人気店(予約推奨)。お通しのうにといくらのプリン、目の前で削るトリュフのポテサラ、'
               'レモンサワーが名物。天ぷらは30種以上で、塩は抹茶塩・ヒマラヤ岩塩・坊津の華の3種。'
               '⚠2026年4月5日にリニューアルオープン(訪問・写真はリニューアル前)。'
               '⚠夜のカウンター居酒屋(17席・全席禁煙・1ドリンク+お通し制)で子連れ向きではない。'
               '17:00〜23:00(L.O.22:30)、火・水定休。薬院大通駅から徒歩約5分。'
               'TEL 050-5593-9010(予約)/092-752-8200。',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400104/40044427/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
