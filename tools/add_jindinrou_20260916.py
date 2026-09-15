# -*- coding: utf-8 -*-
"""恵比寿 京鼎樓(ジンディンロウ)福岡店 を **赤ピン(訪問済み)** で登録し、
あわせて親施設 ららぽーと福岡 の verdict にトレーカートとKIDS PARKを足す。【2026-09-16】

■ 情報の出所(すべて一次情報)
  レシート(2026-09-14 13:14) … 店名の正式表記・住所・TEL・注文品と価格
    恵比寿 京鼎樓 JIN DIN ROU 福岡店 / TEL 092-586-8717
    福岡県福岡市博多区那珂6-351-1 3階
    ★三色)担々麺 1 ¥1,450(内税)  ← **注文はこの1点だけ**
  館内掲示・メニューボード … キッズ点心プレート880円(税込)/おもちゃおまけあり/チャイルドチェアあり、
    9〜11月限定 海老味噌ビャンビャン麺 税込1,130円(小籠包セット+320円)、
    担々麺1,182円、ルーロー飯1,219円、トレーカートは**フードコート内のみ**
  公式 jin-din-rou.net … 台湾で行列の小籠包専門店/ららぽーと福岡は新業態のフードコートスタイル/
    店で手包みの「超薄皮」/営業11:00〜22:00(食事L.O.21:30)/2022年4月25日オープン

■ 写真の作り方(map-spot スキル準拠)
  ⚠**人の映り込みは顔にモザイク、または枠外に出す**。この店の素材は次のとおり:
   ・店頭(02の動画 1.00秒) … カウンター奥に**店員さん1名**(コック帽+マスクだが目元が出る)。
     原寸 x1620,y2240,w300,h300 にモザイクを当てる
   ・23 こあがり席の看板 … **上部 y0〜約700 に他客の顔が10人以上**。y760から下だけを使う
   ・24 こあがり席の座卓 … 左のガラス越しに他客。動画と同じ crop 1800x3200@680,560 で外す
   ・26 トレーカート … 上部に客席。crop 2043x3632@490,400(残るのはピンクの服の肩だけ・顔なし)
   ・05 キッズメニュー / 25 多目的トイレの案内 … 無人
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
P = os.path.join(ROOT, 'data', 'spots.json')
J = r'C:\Users\totor\Dropbox\ショート動画用\ららぽーと福岡_京鼎樓(ジンディンロウ)'
FRONT = os.path.join(HERE, '..', '..', '..', '..', 'AppData', 'Local', 'Temp')  # 使わない
THUMBS = os.path.join(ROOT, 'map', 'thumbs')
PHOTOS = os.path.join(ROOT, 'map', 'photos')
SP = (r'C:\Users\totor\AppData\Local\Temp\claude\C--Users-totor-Dropbox-aura-quest'
      r'\470c0b1a-0dd8-4c23-9039-b8b40dc2b424\scratchpad\jdmap')
ID = 'jindinrou'


def mosaic(im, x, y, w, h, block=18):
    """指定矩形をモザイクにする。block は**完成幅1080換算**の粗さ"""
    reg = im.crop((x, y, x + w, y + h))
    n = max(2, int(w / (im.width / 1080) / block))
    reg = reg.resize((n, max(2, int(n * h / w))), Image.NEAREST).resize((w, h), Image.NEAREST)
    im.paste(reg, (x, y))
    return im


def save_w(im, path, width=1080):
    im.convert('RGB').resize((width, round(im.height * width / im.width)),
                             Image.LANCZOS).save(path, quality=88)
    print('  %s  %dx%d' % (os.path.basename(path), width, round(im.height * width / im.width)))


# ── 1) 店頭(看板)。動画から抜いたフレームに店員さんのモザイクを当てる ────────
front = Image.open(os.path.join(SP, 'front_raw.png')).convert('RGB')
assert front.size == (2160, 3840), front.size
front = mosaic(front, 1620, 2240, 300, 300)

os.makedirs(THUMBS, exist_ok=True)
os.makedirs(PHOTOS, exist_ok=True)
# サムネは 240x300(4:5)。看板が上1/3に入り、下にカウンターが見える窓にする
th = front.crop((0, 560, 2160, 560 + 2700)).resize((240, 300), Image.LANCZOS)
th.save(os.path.join(THUMBS, ID + '.jpg'), quality=90)
print('サムネ %s.jpg 240x300' % ID)

print('ギャラリー:')
save_w(front, os.path.join(PHOTOS, ID + '_01_店頭の看板.jpg'))


def src(f):
    return ImageOps.exif_transpose(Image.open(os.path.join(J, f))).convert('RGB')


save_w(src('05_掲示_キッズ点心プレート880円.jpg'),
       os.path.join(PHOTOS, ID + '_02_キッズ点心プレート880円.jpg'))
# ⚠上部 y0〜700 に他客の顔が並ぶので y760 から下だけ
save_w(src('23_こあがり席 FLAT_SEAT_for_KIDS の看板.jpg').crop((0, 760, 3024, 4032)),
       os.path.join(PHOTOS, ID + '_03_こあがり席FLAT_SEAT_for_KIDS.jpg'))
save_w(src('24_こあがり席の座卓.jpg').crop((680, 560, 680 + 1800, 560 + 3200)),
       os.path.join(PHOTOS, ID + '_04_こあがり席の座卓.jpg'))
save_w(src('26_食事を運ぶためのトレーカート置き場.jpg').crop((490, 400, 490 + 2043, 400 + 3632)),
       os.path.join(PHOTOS, ID + '_05_食事を運ぶトレーカート.jpg'))
save_w(src('25_多目的トイレのアイコン_ベビー休憩室とおむつ替え.jpg'),
       os.path.join(PHOTOS, ID + '_06_多目的トイレとベビー休憩室の案内.jpg'))

# ── 2) spots.json ────────────────────────────────────────────
NEW = {
    "id": ID,
    "name": "恵比寿 京鼎樓 福岡店",
    "area": "ららぽーと福岡 3階 フードコート",
    "city": "福岡市博多区",
    "pref": "福岡県",
    "genre": "台湾料理(小籠包)",
    # 館内の店なので建物の代表座標を親施設と共有する(map-spot スキル準拠)
    "lat": 33.564976,
    "lng": 130.43869,
    "address": "福岡県福岡市博多区那珂6-351-1 3階",
    "visited": "2026-09-14",
    "with": "family",
    "kids": {
        "stroller": None,        # 現地写真で確認していない
        "diaper": True,          # 同フロアの多目的トイレにおむつ替え+ベビー休憩室(25の案内で確認)
        "tatami": True,          # こあがり席 FLAT SEAT for KIDS(23/24で確認)
        "kidsChair": True,       # キッズメニューのポスターに「チャイルドチェアあり」+ 現地にベビーチェア
        "serveMin": None,
        "noise": "ok",           # フードコート業態で席が仕切られていない
    },
    "verdict": (
        "⭐**ららぽーと福岡3階の新業態フードコートスタイル**。台湾で行列のできる小籠包専門店で、"
        "熟練の職人が店で手包みする「超薄皮」の小籠包が売り。"
        "⭐**キッズ点心プレート880円(税込)**は小籠包・揚げ物・デザート・りんごジュース・炒飯・ラーメン付きで、"
        "ポスターに**おもちゃおまけあり / チャイルドチェアあり**の表示がある。"
        "⭐フードコート内の**こあがり席(FLAT SEAT for KIDS)**で靴を脱いで座って食べられ、"
        "**トレーカート**で注文品を席まで運べるので**子供を抱っこしたままでも片手が空く**。"
        "同フロアの多目的トイレにおむつ替え台、ベビー休憩室もある。"
        "◆実食は「**三色)担々麺 1,450円(税込)**」= 三色小籠包つきの担々麺セット。"
        "担々麺単品1,182円、ルーロー飯1,219円。9〜11月限定で**海老味噌ビャンビャン麺 税込1,130円**"
        "(小籠包セット+320円)。◆営業11:00〜22:00(食事L.O.21:30)、定休はららぽーと福岡に準じる。"
        "2022年4月25日オープン。TEL 092-586-8717。"
        "⚠**トレーカートはフードコート内のみ**使用可(掲示に明記)。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": ID + ".jpg",
    "photos": [
        ID + "_01_店頭の看板.jpg",
        ID + "_02_キッズ点心プレート880円.jpg",
        ID + "_03_こあがり席FLAT_SEAT_for_KIDS.jpg",
        ID + "_04_こあがり席の座卓.jpg",
        ID + "_05_食事を運ぶトレーカート.jpg",
        ID + "_06_多目的トイレとベビー休憩室の案内.jpg",
    ],
    "wish": False,               # 赤ピン = 訪問済み
    "category": "gourmet",
    "in": "lalaportfukuoka",     # 館内テナント
}

# ── 3) 親施設 ららぽーと福岡 に足す(トレーカートとKIDS PARK) ──────────
ADD = ("フードコートには**注文品を席まで運ぶトレーカート(TRAY CART)**の置き場があり、"
       "子供を抱っこしたままでも食事を運べる(掲示に「フードコート内のみご使用になれます」と明記)。"
       "モール棟には**KIDS PARK**(カラフルなマット・ベンチ・柵で囲われた休憩スペース)もあり、"
       "食事の前後に軽く遊ばせられる。")

s = json.load(io.open(P, encoding='utf-8'))
if any(x['id'] == ID for x in s):
    raise SystemExit('!! id が既にある: %s' % ID)
lala = [x for x in s if x['id'] == 'lalaportfukuoka']
if not lala:
    raise SystemExit('!! 親施設 lalaportfukuoka が無い')
before = {'wish': lala[0].get('wish'), 'visited': lala[0].get('visited'),
          'lat': lala[0].get('lat'), 'lng': lala[0].get('lng')}

shutil.copy(P, P + '.bak_jindinrou')
if 'トレーカート' not in lala[0]['verdict']:
    lala[0]['verdict'] = lala[0]['verdict'] + ADD
    print('ららぽーと福岡の verdict にトレーカート/KIDS PARK を追記')
else:
    print('ららぽーと福岡は既に追記済み(スキップ)')
s.append(NEW)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ─────────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
ids = [x['id'] for x in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
bad = [x['id'] for x in s2
       if x.get('wish') and any((x.get('video') or {}).get(k) for k in ('youtube', 'tiktok', 'instagram'))]
lala2 = [x for x in s2 if x['id'] == 'lalaportfukuoka'][0]
after = {'wish': lala2.get('wish'), 'visited': lala2.get('visited'),
         'lat': lala2.get('lat'), 'lng': lala2.get('lng')}
miss = [f for f in NEW['photos'] if not os.path.exists(os.path.join(PHOTOS, f))]
print()
print('件数 %d / id重複 %d件 / wish=trueなのに動画URLあり %d件 / 写真の取り違え %d件'
      % (len(s2), len(dup), len(bad), len(miss)))
print('親施設のピン・座標  前 %s' % before)
print('                    後 %s  %s' % (after, '変化なし ✓' if before == after else '⚠変わった'))
if dup or bad or miss or before != after:
    raise SystemExit('!! 検算NG %s %s %s' % (dup[:3], bad[:3], miss))
print('OK  %s を登録した(赤ピン・visited=%s)' % (NEW['name'], NEW['visited']))
