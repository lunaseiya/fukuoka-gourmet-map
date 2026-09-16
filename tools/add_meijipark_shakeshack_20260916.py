# -*- coding: utf-8 -*-
"""明治公園(博多駅前) と シェイクシャック博多店 を **赤ピン(訪問済み)** で登録する【2026-09-16】
1st STEP のマップ登録(素材が手元にある=行っている段階で登録する規則)。

■ 出所
 明治公園 … 事業者(東京建物)の公式リリース
   https://prtimes.jp/main/html/rd/p/000000578.000052843.html
   2026年8月7日開園 / 博多駅前三丁目24番3号 / デザイン監修 藤本壮介氏(2025大阪・関西万博の
   会場デザインプロデューサー) / 敷地約3,572㎡ / 広場5つ / 植栽約160本 /
   **立体園路 総距離226m・インクルーシブデザイン対応** / 公園は24時間開放
   (立体園路と店舗棟は0:00〜5:30閉鎖)
 店舗棟のテナント … 現地のフロア案内を**原寸で1行ずつ**読んだ
   ⚠縮小で読むと外す。「400℃ PIZZA」を「AWFY PIZZA」、「POSS COFFEE」を「Pizza COFFEE」、
     「Land Bageri」を「Lord Nagao」と誤読しかけた
 シェイクシャック … レシート(2026/09/15 12:59:54)が一次情報 + 公式報道
   https://fanfun.jp/321634/  2026年7月21日オープン・九州初出店
 FUKUOKA EXCLUSIVE … 店内メニューボードを原寸で読んだ。**価格は税抜表示+括弧内に税込**

■ 座標
 geocoding.jp / 住所で引いた(2026-09-16)。
 ⚠「福岡市博多区博多駅前3-1-1」はゼロが返る。**「3丁目1-1」に直すと通る**

■ 写真
 素材の動画からフレームを抜いた。⚠**7点すべて人が写っていないことを等倍で確認済み**
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
P = os.path.join(ROOT, 'data', 'spots.json')
THUMBS = os.path.join(ROOT, 'map', 'thumbs')
PHOTOS = os.path.join(ROOT, 'map', 'photos')
SP = (r'C:\Users\totor\AppData\Local\Temp\claude\C--Users-totor-Dropbox-aura-quest'
      r'\470c0b1a-0dd8-4c23-9039-b8b40dc2b424\scratchpad\mp')


def save_thumb(src, out):
    """サムネは 240x300(4:5)。縦位置の素材なので中央から4:5を切る"""
    im = Image.open(os.path.join(SP, src)).convert('RGB')
    w, h = im.size
    th = int(w * 5 / 4)
    y = max(0, (h - th) // 2)
    im.crop((0, y, w, min(h, y + th))).resize((240, 300), Image.LANCZOS)\
      .save(os.path.join(THUMBS, out), quality=90)
    print('  サムネ %s' % out)


def save_photo(src, out, width=1080):
    im = Image.open(os.path.join(SP, src)).convert('RGB')
    im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)\
      .save(os.path.join(PHOTOS, out), quality=88)
    print('  %s  %dx%d' % (out, width, round(im.height * width / im.width)))


MP, SS = 'meijipark-hakata', 'shakeshack-hakata'

os.makedirs(THUMBS, exist_ok=True)
os.makedirs(PHOTOS, exist_ok=True)
# ⚠サムネは**看板より「その場所だと一目で分かる絵」**を優先した。
#   MEIJI PARKのサインは手前にオレンジの工事ネットが入るので、立体園路の方が強い
save_thumb('mp_slope.png', MP + '.jpg')
save_photo('mp_sign.png', MP + '_01_MEIJI_PARKのサイン.jpg')
save_photo('mp_slope.png', MP + '_02_立体園路(226m_段差のない設計).jpg')
save_photo('mp_lawn.png', MP + '_03_芝生広場と立体園路.jpg')

save_thumb('ss_front.png', SS + '.jpg')
save_photo('ss_front.png', SS + '_01_店頭.jpg')
save_photo('ss_burger.png', SS + '_02_シャックバーガーと明太マヨフライ.jpg')
save_photo('ss_seat.png', SS + '_03_客席とガラス天井.jpg')
save_photo('ss_wash.png', SS + '_04_店内のハンドウォッシングステーション.jpg')

NEW = [{
    "id": MP,
    "name": "明治公園",
    "area": "博多駅前",
    "city": "福岡市博多区",
    "pref": "福岡県",
    "genre": "都市公園(立体園路・広場5つ)",
    "lat": 33.588551,
    "lng": 130.417486,
    "address": "福岡県福岡市博多区博多駅前三丁目24番3号",
    "visited": "2026-09-15",
    "with": "family",
    "kids": {
        # 公式が「インクルーシブデザイン対応/足の不自由な方の利用を考慮した設計」と明記し、
        # 現地でもスロープを撮っているので true にした
        "stroller": True,
        "diaper": None,      # ⚠フロア案内に**ベビーのアイコンが無い**。多目的トイレはある
        "tatami": None,
        "kidsChair": None,
        "serveMin": None,
        "noise": "ok",       # 屋外の公園
    },
    "verdict": (
        "⭐**2026年8月7日に博多駅前に開園した"
        "「公園を立体化した」都市公園**。Park-PFIで東京建物を代表企業とするコンソーシアムが整備し、"
        "**デザイン監修は藤本壮介氏**(2025年大阪・関西万博の会場デザインプロデューサー)。"
        "⭐**空中の立体園路が総距離226mで、インクルーシブデザイン対応**。"
        "公式に「足の不自由な方の利用を考慮した設計」と明記されていて、"
        "**段差を作らずスロープで上まで回れる=ベビーカーでも一周できる**のがこの公園の一番の価値。"
        "敷地約3,572㎡に**広場が5つ**、樹木や草花が**約160本**。"
        "◆店舗棟は7区画。1F **POSS COFFEE**(カフェ/バー)・**GABBI HAKATA**(イタリアンダイニング)・"
        "**Land Bageri**(ベーカリー/ビストロ)、2F **400℃ PIZZA Piu Hakata**(ピッツェリア)・"
        "**Continue?**(ビアバー)・1区画は Coming Soon、3〜4F **TOTOPA博多駅前店**(都市型スパ)、"
        "屋上は**「空のにわ」**という広場。"
        "◆**公園は24時間開放**(立体園路と店舗棟は0:00〜5:30閉鎖。各店舗の営業時間は異なる)。"
        "⚠フロア案内の設備アイコンは女性/男性トイレ・多目的トイレ・喫煙所・コインロッカーで、"
        "**おむつ替えのアイコンは出ていない**(多目的トイレ内にある可能性はあるが未確認)。"
        "⚠**博多駅から徒歩圏だが駐車場は公園には無い**ので、周辺のコインパーキングになる(要確認)。"
    ),
    "web": "https://prtimes.jp/main/html/rd/p/000000578.000052843.html",
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": MP + ".jpg",
    "photos": [MP + "_01_MEIJI_PARKのサイン.jpg",
               MP + "_02_立体園路(226m_段差のない設計).jpg",
               MP + "_03_芝生広場と立体園路.jpg"],
    "wish": False,
    "category": "play",
}, {
    "id": SS,
    "name": "シェイクシャック 博多店",
    "area": "西日本シティビル 1F",
    "city": "福岡市博多区",
    "pref": "福岡県",
    "genre": "ハンバーガー",
    "lat": 33.589442,
    "lng": 130.418255,
    "address": "福岡県福岡市博多区博多駅前3-1-1 西日本シティビル 1F",
    "visited": "2026-09-15",
    "with": "family",
    "kids": {
        "stroller": None,
        "diaper": None,
        "tatami": False,     # 店内は全席テーブル・椅子(写真で確認)
        "kidsChair": True,   # **5点ベルト付きのベビーチェア**を現地写真で確認
        "serveMin": None,
        "noise": "ok",       # 席が仕切られていない開放的なフードホール形式
    },
    "verdict": (
        "⭐**2026年7月21日オープン・シェイクシャックの九州初出店**。"
        "明治公園の隣、同じ日に開業した**西日本シティビルの1F**(同フロアに STAND T と I'm donut ?、"
        "上層に wework と NCB創業応援サロンHAKATA)。"
        "⭐メニューに**「FUKUOKA EXCLUSIVE」という福岡限定セクション**がある。"
        "**明太マヨフライ**(Small 税込715円 / Regular 税抜790円)と、"
        "**あまおうシェイク with チロリアン**(Mini 税込770円 / Regular 税込1,089円・ホイップ+176円)。"
        "あまおう苺とピューレをフローズンカスタードにブレンドし、"
        "**チロリアン(千鳥饅頭総本舗の福岡銘菓)をストローに見立てる**という一杯。"
        "◆実食は SHACK(チーズパティ1枚) 税抜960円 / Pear Vanilla Lemonade 税抜600円 / "
        "**(S)明太マヨフライ 税抜650円** の3点で**税込2,431円**。"
        "◆⭐子連れで効いたのは **①5点ベルト付きのベビーチェア** "
        "**②店内に Hand Washing Station(手洗い場)がある**こと。"
        "**公園で遊んだ手をそのまま洗って席に着ける**。"
        "**③注文はセルフオーダー端末**なので行列に並ばずに済む。"
        "◆営業 11:00〜22:00(L.O.21:30)。TEL 092-409-1221。"
        "⚠**メニューの価格は税抜表示で、括弧内に税込**が書かれている形。レシートも税抜集計。"
    ),
    "web": "https://www.shakeshack.jp/",
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": SS + ".jpg",
    "photos": [SS + "_01_店頭.jpg",
               SS + "_02_シャックバーガーと明太マヨフライ.jpg",
               SS + "_03_客席とガラス天井.jpg",
               SS + "_04_店内のハンドウォッシングステーション.jpg"],
    "wish": False,
    "category": "gourmet",
}]

s = json.load(io.open(P, encoding='utf-8'))
ids = {x['id'] for x in s}
for n in NEW:
    if n['id'] in ids:
        raise SystemExit('!! id が既にある: %s' % n['id'])

import math
for n in NEW:
    print('%s の近傍(500m以内):' % n['name'])
    hit = 0
    for x in s:
        if x.get('lat') is None or x.get('lng') is None:
            continue
        d = math.hypot((x['lat'] - n['lat']) * 111,
                       (x['lng'] - n['lng']) * 111 * math.cos(math.radians(n['lat'])))
        if d < 0.5:
            print('   %.2fkm %s (%s)' % (d, x.get('name'), x['id'])); hit += 1
    if not hit:
        print('   なし')

shutil.copy(P, P + '.bak_meijipark')
s += NEW
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ─────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
idl = [z['id'] for z in s2]
dup = [i for i in set(idl) if idl.count(i) > 1]
bad = [z['id'] for z in s2
       if z.get('wish') and any((z.get('video') or {}).get(k) for k in ('youtube', 'tiktok', 'instagram'))]
miss = [f for n in NEW for f in n['photos'] if not os.path.exists(os.path.join(PHOTOS, f))]
miss += [n['thumb'] for n in NEW if not os.path.exists(os.path.join(THUMBS, n['thumb']))]
# ⚠常設スポットに until が付いていないこと(付くと会期後に地図から消える)
until = [n['id'] for n in NEW if n.get('until')]
print()
print('件数 %d / id重複 %d件 / wish矛盾 %d件 / 画像欠け %d件 / until誤付与 %d件'
      % (len(s2), len(dup), len(bad), len(miss), len(until)))
if dup or bad or miss or until:
    raise SystemExit('!! 検算NG %s %s %s %s' % (dup[:3], bad[:3], miss, until))
print('OK  明治公園 / シェイクシャック博多店 を登録した(どちらも赤ピン・visited=2026-09-15)')
