# -*- coding: utf-8 -*-
"""2026-09-13 エモ版2本ぶんのマップ登録。
  ① めんちゃんラーメン(福岡市博多区上川端町) … **新規・赤ピン**
  ② はま寿司 香椎いーなテラス店            … 既存の**青ピン → 赤ピン化**

鉄則(map-spot スキル):
 ・未確認の項目は null。推測で埋めない
 ・書き換え前に spots.json をバックアップ
 ・ジオコーディングは geocoding.jp を住所で・10秒以上あけて
 ・書き戻したら ①id重複ゼロ ②wish=true なのに動画URLがある矛盾ゼロ を検算
 ・**現地で見た事実 > ネット情報**。写真・映像で確認していない項目は null のまま

使い方: python tools/reg_emo_2026_09_13.py        (ドライラン)
        python tools/reg_emo_2026_09_13.py --go
"""
import io, json, os, re, shutil, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
GO = '--go' in sys.argv
UA = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ja'}

MEN_ADDR = '福岡県福岡市博多区上川端町3-1'


def geocode(addr):
    u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(addr)
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode('utf-8')
    la = re.search(r'<lat>([\d.]+)</lat>', r)
    ln = re.search(r'<lng>([\d.]+)</lng>', r)
    if not (la and ln) or float(la.group(1)) == 0:
        return None, None
    return float(la.group(1)), float(ln.group(1))


sp = json.load(io.open(P, encoding='utf-8'))

# ---------------- ① めんちゃんラーメン(新規・赤ピン) ----------------
MEN_ID = 'menchan-kamikawabata'
exists = [s for s in sp if s['id'] == MEN_ID or s.get('name') == 'めんちゃんラーメン']
if exists:
    print('めんちゃん: すでにある → 追加しない')
    men = None
else:
    lat = lng = None
    if GO:
        lat, lng = geocode(MEN_ADDR)
        print('  ジオコーディング %s → %s, %s' % (MEN_ADDR, lat, lng))
        if lat is None:
            print('  ! 失敗。座標は null で登録する(推測で埋めない)')
    men = {
        'id': MEN_ID,
        'name': 'めんちゃんラーメン',
        'area': '上川端',
        'city': '福岡市博多区',
        'pref': '福岡県',
        'genre': 'ラーメン',
        'lat': lat, 'lng': lng,
        'address': MEN_ADDR,
        'visited': '2024-08-06',          # 素材のメタデータ(creationdate)より。推測ではない
        'with': 'solo',                   # 深夜0時に撮影者本人のみ → kids は null でよい
        'kids': None,
        'verdict': ('⭐19:00〜28:00(翌朝4時)営業で、締めの一杯に使える。博多川の川沿い、'
                    'カウンター中心の14席(うち外のテーブル4席)。青ネギが山盛りで紅生姜は好きなだけ。'
                    '⚠駐車場なし・日曜と祝日は休み。通路が狭く営業も深夜帯なので'
                    '**子連れには向かない**。創業は30年以上とされる(要確認)。'),
        'video': {'youtube': None, 'tiktok': None, 'instagram': None},
        'thumb': None,
    }

# ---------------- ② はま寿司 香椎いーなテラス店(青→赤) ----------------
hama = None
for s in sp:
    if s['id'] == 'sp55374109dd':
        hama = s
        break
if hama is None:
    print('!! はま寿司の既存エントリが見つからない')
    sys.exit(1)

HAMA_NEW = {
    'visited': '2026-09-13',              # レシート(2026年09月13日 17時54分)より
    'kids': {
        'stroller': None,                 # 映像で確認していないので null
        'diaper': True,                   # 多目的トイレにおむつ替え台(写真で確認)
        'tatami': None,
        'kidsChair': True,                # 木製4台+バンボ(写真で確認)
        'serveMin': 1,                    # タブレット注文から30秒前後(体感)
        'noise': 'ok',
        'kidsMenu': True,                 # ハマッコポテトセットを実際に注文(レシート)
    },
    'verdict': ('⭐注文タブレットの音声を声優の声に変更できる(花江夏樹さん・緒方恵美さんから選択)。'
                '切り替えると「まもなく到着します」「お取り忘れにご注意ください」がその声になる。'
                '⭐提供が速く、タブレット注文から30秒前後で到着。'
                '⭐子連れ設備が充実。木製ベビーチェア4台+バンボ、子供用の茶碗とフォーク・スプーン、'
                '多目的トイレにおむつ替え台とベビーキープ。出口にガチャガチャあり。'
                '⭐醤油は減塩・だし・さしみ(九州風)・甘口(関西風)の4種類。'
                'この日は4人で寿司25皿+サイド7点で5,852円。'
                '⚠夕方は店頭に待ち客が並ぶので、時間をずらすか先に発券しておくとよい。'),
    'address': '福岡県福岡市東区香椎浜3-12-1',   # レシート印字と一致(香椎浜三丁目12番1)
}

print('=== マップ登録 (%s) ===' % ('実行' if GO else 'ドライラン'))
if men:
    print('  + 新規  %s  %s' % (men['name'], MEN_ADDR))
    print('          赤ピン / visited=%s / with=solo / kids=null' % men['visited'])
print('  ~ 更新  %s (%s)' % (hama['name'], hama['id']))
print('          青ピン → **赤ピン** / visited=%s' % HAMA_NEW['visited'])
print('          kids: kidsChair=True diaper=True kidsMenu=True serveMin=1 noise=ok')
print('                stroller/tatami は映像で未確認なので null のまま')

if not GO:
    print()
    print('※ --go で実行します')
    sys.exit(0)

shutil.copy(P, P + '.bak_emo20260913')
if men:
    sp.append(men)
hama.update(HAMA_NEW)
hama.pop('wish', None)                    # 赤ピン化(wish を消す。False を置くのではなく削除)
io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))

# ---------------- 検算 ----------------
import collections
c = collections.Counter(s['id'] for s in sp)
dup = [k for k, v in c.items() if v > 1]
bad = [s['id'] for s in sp if s.get('wish') and any((s.get('video') or {}).values())]
names = collections.Counter(s['name'] for s in sp)
ndup = [k for k, v in names.items() if v > 1]
print()
print('総数 %d / id重複 %d / 青ピンに動画がある矛盾 %d / 同名重複 %d'
      % (len(sp), len(dup), len(bad), len(ndup)))
if dup: print('  id重複:', dup)
if bad: print('  矛盾:', bad)
if ndup: print('  同名:', ndup[:6])
print('※ このあと python tools/monetize.py --ids %s sp55374109dd --apply を回す'
      % (MEN_ID if men else ''))
print('※ python tools/build_pages.py → push')
