# -*- coding: utf-8 -*-
"""すし酒場 さじ(中央区大名)を新規・赤ピン登録(visited=2023-03-28・動画素材の作成日)
   素材: ショート動画用/居酒屋さじ　大名(iPhone 1080p SDR .mov → フレーム抜き出し。ファイル名はリネーム済みなので clip id で glob)
   座標: geocoding.jp(住所「福岡県福岡市中央区大名1-3-23」で取得。Google表記も「葵ビル」で一致)
   営業時間・定休日・座敷/個室: 公式 saji-lds.com
   with=friends(夜の居酒屋・子連れ外出ではない)→ README/スキル準拠で kids=null(公式の座敷情報も kids には入れず verdict に書く)
   人の映り込み: 使用フレームはすべて人なし。メニュー(2023年の価格)のフレームは使わない
   食べログ 40056761(名前・住所一致)は「運営状況未確認のため掲載保留」表示 → tabelog は付けない。
   公式サイトも緊急事態宣言期の記載が残る古い状態。営業状況は要確認として verdict に明記"""
import glob, io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\居酒屋さじ　大名'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_saji')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'sushisakaba-saji'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if 'さじ' in x['name']]


def clip(cid):
    m = glob.glob(os.path.join(SRC, '*_%s_*.mov' % cid))
    assert len(m) == 1, (cid, m)
    return m[0]


def img(cid, ss=0, box=None):
    """box = 比率 (x0, y0, x1, y1) で切り出し"""
    t = os.path.join(tempfile.gettempdir(), '_saji_t.jpg')  # Dropbox配下だと同期がロックするので外に置く
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', clip(cid),
                    '-frames:v', '1', '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


# サムネ: 木の看板「鮨と酒と旨き魚 すし酒場 さじ」(1786 1.6s・人なし)
ImageOps.fit(img('1786', 1.6, (0.2, 0.02, 0.92, 0.56)), (240, 300), Image.LANCZOS).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

# (clip id, 秒, 切り出し, 内容)
items = [('1800', 9.0, None, 'スプーン寿司の大トロ'),
         ('1799', 9.3, None, 'ホタテとウニのスプーン寿司'),
         ('1792', 13, None, 'あさりの土鍋'),
         ('1793', 1, None, '牡蠣ポン酢')]
photos = []
for k, (c, ss, box, lab) in enumerate(items, 1):
    im = img(c, ss, box); im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': 'すし酒場 さじ', 'area': '大名', 'city': '福岡市中央区', 'pref': '福岡県',
    'genre': '居酒屋・寿司', 'lat': 33.586077, 'lng': 130.393197, 'address': '福岡県福岡市中央区大名1-3-23 葵ビル1F右',
    'visited': '2023-03-28', 'with': 'friends', 'category': 'gourmet', 'wish': False,
    'kids': None,
    'verdict': '⭐名物はスプーンにのせて一口で食べる創作すし(大トロ・ウニ・穴子など)。蟹プリンなど一品料理も。'
               '⚠夜は居酒屋なので子連れ向きではない。掘りごたつ・お座敷・完全個室あり(公式)。'
               'ランチ11:30〜15:00(要相談)/ディナー18:00〜25:00、月曜定休(公式)。赤坂駅から徒歩約7分。'
               '⚠食べログは「運営状況が確認できない」として掲載保留中(2026年10月時点)。営業しているか行く前に要確認。',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
