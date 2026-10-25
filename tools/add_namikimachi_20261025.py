# -*- coding: utf-8 -*-
"""並木街珈琲 博多の森店(博多区東平尾)を新規・赤ピン登録(visited=2026-10-22・素材の撮影日)
   素材: ショート動画用/並木街珈琲(iPhone SDR bt709 .mov / .jpg)
   座標: geocoding.jp(住所「福岡県福岡市博多区東平尾1-182-1」)
   ⚠入口ドアに「撮影禁止」のピクト(カメラに×)。ジョイフルは撮影許可の事前申請制(kyoka.pdf)
   → short-video スキルの⛔ルールどおり、マップには**館内の写真を載せない**(外観・屋外の掲示だけ)。
     子供椅子・おむつ替え台・絵本棚の写真は持っているが、許可が出るまで文字情報だけにする
   子連れ設備はユーザーの現地確認(2026-10-25チャット): ベルト付き子供椅子・取り皿・みんなのトイレ(男性もおむつ替え可)・
   ゆったりした椅子・整理券受付。食べログ: 子供可(乳児可)・お子様メニューあり・ベビーカー入店可・87席・全席禁煙・予約不可"""
import io, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\並木街珈琲'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
shutil.copy(P, P + '.bak_namiki')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'namikinomachi-hakatanomori'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if '並木街' in x['name']]


def vid(name, ss, box=None):
    t = os.path.join(tempfile.gettempdir(), '_namiki_t.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(ss), '-i', os.path.join(SRC, name),
                    '-frames:v', '1', '-q:v', '2', t], check=True)
    im = Image.open(t).convert('RGB'); im.load(); os.remove(t)
    return crop(im, box)


def pho(name, box=None):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name))).convert('RGB')
    return crop(im, box)


def crop(im, box):
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    return im


# サムネ: 外観(店名サイン「並木街珈琲 Namiki no machi coffee」)
ImageOps.fit(vid('動画 2026-10-22 13 19 29.mov', 1.5, (0.04, 0.12, 0.96, 0.80)), (240, 300), Image.LANCZOS).save(
    os.path.join(TH, SID + '.jpg'), quality=88)

items = [(vid('動画 2026-10-22 13 19 29.mov', 1.5), '外観(店名サイン)'),
         (vid('動画 2026-10-22 13 19 14.mov', 1.0), '駐車場入口の看板(平日10時〜22時・土日祝8時〜22時)'),
         (pho('写真 2026-10-22 14 00 06.jpg'), '入口の表示(営業時間・全席禁煙・Wi-Fi・撮影禁止・ペット不可)'),
         (pho('写真 2026-10-22 13 20 05.jpg'), '店頭の秋メニュー(渋皮栗とマスカットのパンケーキ)')]
photos = []
for k, (im, lab) in enumerate(items, 1):
    im.thumbnail((1080, 1920), Image.LANCZOS)
    nm = '%s_%02d_%s.jpg' % (SID, k, lab)
    im.save(os.path.join(PH, nm), quality=85); photos.append(nm)

s.append({'id': SID, 'name': '並木街珈琲 博多の森店', 'area': '東平尾(博多の森)', 'city': '福岡市博多区', 'pref': '福岡県',
    'genre': 'カフェ', 'lat': 33.589857, 'lng': 130.456089,
    'address': '福岡県福岡市博多区東平尾1-182-1',
    'visited': '2026-10-22', 'with': 'family', 'category': 'gourmet', 'wish': False,
    'kids': {'stroller': True, 'diaper': True, 'tatami': False, 'kidsChair': True, 'kidsMenu': None, 'serveMin': None, 'noise': None},
    'verdict': 'ファミレス「ジョイフル」が運営するカフェ(2020年5月オープン)。並木街珈琲は福岡県内ではここだけ(ほかは大分に3店)。'
               '看板は注文を受けてからメレンゲを立てて1枚ずつ焼く「ふわふわパンケーキ」と、ネルドリップの珈琲。2杯目はおかわり価格(ブレンド税込291円)。'
               '⭐子連れ歓迎: ベルト付きの子供椅子・取り皿あり・絵本の棚。椅子はゆったりしたアームチェアとソファ席で大人もゆっくりできる。'
               '⭐トイレは「みんなのトイレ(車いす・おむつ替え台)」と女性用に分かれていて、男性でもおむつ替え台が使える。'
               '受付は整理券方式なので待ち時間を管理しやすい(週末は15〜20分待ちの口コミあり)。'
               '平日10:00〜22:00/土日祝8:00〜22:00(L.O.21:00)。87席・全席禁煙・Wi-Fi・ペット不可・予約不可・駐車場あり。'
               '東平尾公園(大谷広場)から車ですぐ。福岡空港駅から徒歩14分。'
               '⚠入口に「撮影禁止」のピクトあり(ジョイフルは撮影許可の事前申請制)。館内の写真はそのため載せていません。TEL 092-624-3566',
    'tabelog': 'https://tabelog.com/fukuoka/A4001/A400107/40054278/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': SID + '.jpg', 'photos': photos})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', photos)
