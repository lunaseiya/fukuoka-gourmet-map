# -*- coding: utf-8 -*-
"""笑伝の店舗取り違えを修正(2026-10-07)
shoden-hakata(博多区店屋町の 博多魚菜と串焼き百珍 笑伝)として登録していたが、
実際に行ったのは 笑伝 春吉店(動画GPS 33.5888,130.4052 / 2023-09-16)。
- id を shoden-haruyoshi に変更し、thumb/photos のファイル名も新idへリネーム
- 店名・エリア・住所・座標・食べログ・verdict を春吉店の情報に書き換え
- 店屋町店は未訪問なので新規追加しない
- data/投稿待ち.md と キャプション_笑伝.txt も春吉店に差し替え
座標: geocoding.jp「福岡県福岡市中央区春吉3丁目22-7」→ 33.588848,130.405112(GPSと約10m差)
情報源: 食べログ https://tabelog.com/fukuoka/A4001/A400103/40058862/
"""
import io, json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
PENDING = os.path.join(ROOT, 'data', '投稿待ち.md')
CAPTION = os.path.join(os.path.dirname(ROOT), '笑伝', 'キャプション_笑伝.txt')
OLD, NEW = 'shoden-hakata', 'shoden-haruyoshi'
TAG = '.bak_shoden_haruyoshi'

for p in (SPOTS, PENDING, CAPTION):
    if not os.path.exists(p + TAG):
        shutil.copy(p, p + TAG)

# ---- spots.json ----
spots = json.load(io.open(SPOTS, encoding='utf-8'))
assert not any(s['id'] == NEW for s in spots), 'new id already exists'
sp = next(s for s in spots if s['id'] == OLD)

sp['id'] = NEW
sp['name'] = '笑伝 春吉店'
sp['area'] = '春吉'
sp['city'] = '福岡市中央区'
sp['lat'] = 33.588848
sp['lng'] = 130.405112
sp['address'] = '福岡県福岡市中央区春吉3-22-7-1 プロスペリタ天神1'
sp['tabelog'] = 'https://tabelog.com/fukuoka/A4001/A400103/40058862/'
sp['verdict'] = ('雲仙・島原の食材にこだわる串焼き居酒屋(笑伝=えでん)。名物は雲仙スーパーポークの豚バラ、'
                 '自家製手ごねつくね、島原の「ごちそい」豆腐、「ハム界の反逆児」雲仙ハム。サントリー神泡達人店。'
                 '⚠夜の居酒屋なので子連れ向きではない。18:00〜翌3:00(L.O.2:00)・不定休・36席(テーブル・カウンター)。'
                 '渡辺通駅から徒歩約3分(天神南駅からも約320m)。TEL 092-712-8777。')
# visited / with / kids / wish はそのまま(2023-09-16・friends・null・赤ピン)

# 画像リネーム
def ren(sub, fn):
    nfn = NEW + fn[len(OLD):]
    src, dst = os.path.join(ROOT, 'map', sub, fn), os.path.join(ROOT, 'map', sub, nfn)
    if os.path.exists(src) and not os.path.exists(dst):
        os.rename(src, dst)
    assert os.path.exists(dst), dst
    return nfn
sp['thumb'] = ren('thumbs', sp['thumb'])
sp['photos'] = [ren('photos', f) for f in sp['photos']]

# 他スポットからの参照(in 等)を差し替え
def swap(o):
    if isinstance(o, dict):
        return {k: swap(v) for k, v in o.items()}
    if isinstance(o, list):
        return [swap(v) for v in o]
    return NEW if o == OLD else o
spots = [swap(s) for s in spots]

ids = [s['id'] for s in spots]
assert len(ids) == len(set(ids)), 'duplicate id'
bad = [s['id'] for s in spots if s.get('wish') is True and any((s.get('video') or {}).values())]
assert not bad, bad
assert OLD not in json.dumps(spots, ensure_ascii=False)
io.open(SPOTS, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

# ---- 投稿待ち.md ----
t = io.open(PENDING, encoding='utf-8').read()
t = t.replace('博多魚菜と串焼き百珍 笑伝(エモ版', '笑伝 春吉店(エモ版')
t = t.replace('新規id: shoden-hakata(', '新規id: shoden-haruyoshi(')
assert OLD not in t
io.open(PENDING, 'w', encoding='utf-8').write(t)

# ---- キャプション ----
c = io.open(CAPTION, encoding='utf-8').read()
reps = [
    ('#博多グルメ #串焼き #博多居酒屋 #福岡', '#天神グルメ #串焼き #春吉グルメ #福岡'),
    ('【博多・店屋町】名物串の紹介がクセ強すぎた。', '【福岡・春吉】名物串の紹介がクセ強すぎた。'),
    ('長崎の食材にこだわる串焼き屋さん。', '雲仙・島原の食材にこだわる串焼き屋さん。'),
    ('📍博多魚菜と串焼き百珍 笑伝\n福岡市博多区店屋町2-20\n地下鉄 呉服町駅すぐ\n夜営業(17時〜)',
     '📍笑伝 春吉店\n福岡市中央区春吉3-22-7-1\n地下鉄 渡辺通駅から徒歩3分\n夜営業(18時〜翌3時)'),
    ('#博多グルメ #串焼き #博多居酒屋 #呉服町グルメ #福岡居酒屋', '#春吉グルメ #串焼き #天神グルメ #天神居酒屋 #福岡居酒屋'),
    ('福岡市博多区・呉服町駅近くの「博多魚菜と串焼き百珍 笑伝」で', '福岡市中央区・春吉の「笑伝 春吉店」で'),
    ('s/shoden-hakata.html', 's/shoden-haruyoshi.html'),
    ('長崎の食材にこだわる串焼きと魚菜のお店です。', '雲仙・島原の食材にこだわる串焼きのお店です。'),
    ('名物の自家製手ごねつくねも。', '名物の自家製手ごねつくねや、島原の「ごちそい」豆腐も。'),
    ('博多魚菜と串焼き百珍 笑伝\n福岡市博多区店屋町2-20\nTEL 092-263-3226\n地下鉄 呉服町駅から徒歩約3分\n'
     '夜営業(17:00〜。閉店時刻は情報源によって異なるため、来店前にご確認ください)',
     '笑伝 春吉店\n福岡市中央区春吉3-22-7-1 プロスペリタ天神1\nTEL 092-712-8777\n'
     '地下鉄 渡辺通駅から徒歩約3分(天神南駅からも約320m)\n18:00〜翌3:00(L.O. 2:00)・不定休'),
]
for a, b in reps:
    n = c.count(a)
    assert n >= 1, a
    c = c.replace(a, b)
for w in ('店屋町', '博多区', '呉服町', '092-263-3226', OLD, '博多魚菜'):
    assert w not in c, w
io.open(CAPTION, 'w', encoding='utf-8').write(c)
print('done:', NEW, sp['thumb'], sp['photos'])
