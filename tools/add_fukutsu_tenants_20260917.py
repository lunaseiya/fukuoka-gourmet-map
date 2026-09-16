# -*- coding: utf-8 -*-
"""イオンモール福津の**館内テナントを一括登録**する【2026-09-17ユーザー指示】

ユーザーの指示(逐語):
  「イオンモール福津のフォルダを保存しました、親として登録してください。
    一部子供向け店舗の外観とったので、リストだけしてもらいたいです。
    全て赤ピンで良いです。
    飲食についてはフードコートは赤登録で、レストランエリアは青ピンです。」

■ 親施設は**既に登録済み**だった
  `aeonmallfukutsu` が wish=false(赤ピン)で存在したが **`visited` が null** という
  矛盾した状態だった(赤ピンなのに訪問日が無い)。今回訪問したので visited を入れ、
  現地で読み取った子連れ設備を verdict と kids に反映する。**新規登録はしない**。
  撮影日は EXIF(36867) が 37枚とも 2026:09:16 だったので **2026-09-16**(推測しない)。

■ ピンの色はユーザー指示どおりに振り分ける
  | 区分 | ピン | 理由 |
  |---|---|---|
  | 子供向け店舗 | **赤**(訪問済み) | 外観を撮っている |
  | FOOD FOREST(フードコート)のテナント | **赤** | 同上の扱いでよいとの指示 |
  | 2Fレストラン街のテナント | **青**(未訪問) | 入っていない |

■ テナント名の出所
  ・FOOD FOREST 13店 = **フードコートの床に敷かれた案内マップを原寸で読んだ**(写真33)
  ・2Fレストラン街 16店 = **館内のデジタルフロアマップを原寸で読んだ**(写真35)
  ・子供向け店舗 = **店頭の外観写真**から店名を確定(写真09〜21)
  ⚠縮小のままだと読み外す。2倍に拡大して1項目ずつ読んで確定させた

■ 座標は**親施設の代表座標を共有する**(map-spot の商業施設ルール)
  館内の店なので建物の1点でよい。⚠**推測で散らさない**

■ 既に登録済みで触らないもの
  ・猫カフェMOCHA イオンモール福津店(青) … レストラン街なので青のままで指示と一致
  ・はま寿司 イオンモール福津店(青)       … 同上
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

PARENT = 'aeonmallfukutsu'
VISITED = '2026-09-16'
LAT, LNG = 33.753025, 130.492828
CITY, PREF = '福津市', '福岡県'

# ── 親施設の verdict(現地で読み取ったものだけ書く) ───────────────────
PARENT_VERDICT = (
    '専門店約180店。TOHOシネマズ福津(10スクリーン)併設。 '
    '⭐**フードコート「FOOD FOREST」に「キッズゾーン」**があり、館内の掲示に'
    '「小上がり席」「**ベビーカーのまま着席できるソファBOX席**」'
    '「**お子さまを対面に座らせられる席(離乳食時向け)**」「**子供サイズのデスク・チェア**」'
    'と明記されている(現地の床マップと掲示で確認)。フードコートは13店。 '
    '⭐**館内に無料で遊べる「キッズヒカリパーク」**(木製の滑り台とトンネル)と、'
    '**有料の室内遊び場「あそびぱ～く」**がある。 '
    '⭐**BABY ROOM**(授乳室)・**おむつ替え台**・**調乳用の給湯器**・'
    '**FAMILY みんなのトイレ**(多目的)を現地で確認。 '
    '⭐**子供乗せカート(車型)**とベルト付きの木製ベビーチェア・ハイチェアあり。 '
    '⚠2Fのレストラン街は16店で別エリア(こちらは未入店)。'
)

# ── 子供向け店舗(赤ピン)。外観写真から店名を確定したもの ──────────────
KIDS = [
    ('fukutsu-toysrus', 'トイザらス・ベビーザらス イオンモール福津店', 'おもちゃ',
     '館内のおもちゃ・ベビー用品の大型店。店頭にアンパンマンの自販機。'
     '店内にチャイルドシートやベビーカーの実機が並ぶ。'),
    ('fukutsu-genkikids', 'Genki-Kids イオンモール福津店', '子供服',
     '子供服。館内。'),
    ('fukutsu-gachagacha-mori', 'ガチャガチャの森 イオンモール福津店', 'ガチャガチャ',
     'カプセルトイの専門店。壁一面がガチャ。小銭があれば数分で遊べるので待ち時間に使える。'),
    ('fukutsu-hobbyzone', 'Hobby Zone イオンモール福津店', 'おもちゃ',
     'プラモデル・ホビー。館内。'),
    ('fukutsu-caramelbone', 'キャラメル・ボーン イオンモール福津店', 'キャラクターショップ',
     'キャラクターグッズ。館内。'),
    ('fukutsu-cc-carrous', 'C&C by CARROUS イオンモール福津店', '雑貨',
     '雑貨・文具(Creation and Community Shop)。館内。'),
    ('fukutsu-dagashiya', '昔なつかし 駄菓子屋さん イオンモール福津店', '駄菓子',
     '⭐**駄菓子が1点76円〜**で山積み。お面やくじも下がっていて、'
     '子供が自分で選んで買う体験ができる。店頭にガチャとガムボールマシン。'),
    ('fukutsu-thankyoumart', 'THANK YOU MART イオンモール福津店', '雑貨',
     '**全品390円**の雑貨店。館内。'),
    ('fukutsu-rakuichirakuza', '樂市樂座 イオンモール福津店', 'ゲームセンター',
     'ゲームセンター(HYPER AMUSEMENT)。館内。'),
    ('fukutsu-kids-hikari-park', 'キッズヒカリパーク(イオンモール福津)', '室内遊び場',
     '⭐**館内の無料の遊び場**。木製の滑り台とトンネル、段差の少ない園路。'
     'フードコートの近くにあるので食事の前後に寄れる。⚠対象年齢の掲示は未確認。'),
    ('fukutsu-asobi-park', 'あそびぱ～く イオンモール福津', '室内遊び場',
     '⭐館内の**有料の室内遊び場**。ボールプール・ジャングルジム・おままごと。'
     '⚠料金と対象年齢は現地の掲示で要確認。'),
]

# ── FOOD FOREST(フードコート)= 赤ピン。**床の案内マップを原寸で読んだ13店** ──
FOODCOURT = [
    ('fukutsu-fc-mcdonalds', 'マクドナルド イオンモール福津店', 'ハンバーガー'),
    ('fukutsu-fc-dessert-oukoku', 'デザート王国 イオンモール福津店', 'スイーツ'),
    ('fukutsu-fc-baskinrobbins', 'サーティワンアイスクリーム イオンモール福津店', 'アイスクリーム'),
    ('fukutsu-fc-saizeriya', 'サイゼリヤ イオンモール福津店', 'イタリアン'),
    ('fukutsu-fc-gindaco', '築地銀だこ イオンモール福津店', 'たこ焼き'),
    ('fukutsu-fc-ringerhut', 'リンガーハット イオンモール福津店', 'ちゃんぽん'),
    ('fukutsu-fc-sukiya', 'すき家 イオンモール福津店', '牛丼'),
    ('fukutsu-fc-marugame', '丸亀製麺 イオンモール福津店', 'うどん'),
    ('fukutsu-fc-kfc', 'ケンタッキーフライドチキン イオンモール福津店', 'フライドチキン'),
    ('fukutsu-fc-ippudo', '一風堂 イオンモール福津店', 'ラーメン'),
    ('fukutsu-fc-pepperlunch', 'ペッパーランチ イオンモール福津店', 'ステーキ'),
    ('fukutsu-fc-bibintei', 'ビビン亭 イオンモール福津店', '韓国料理'),
    ('fukutsu-fc-misterdonut', 'ミスタードーナツ イオンモール福津ショップ', 'ドーナツ'),
]
FC_VERDICT = ('イオンモール福津のフードコート「**FOOD FOREST**」内。'
              '⭐フードコートに**キッズゾーン**(小上がり席／ベビーカーのまま着席できる'
              'ソファBOX席／お子さまを対面に座らせられる席／子供サイズのデスク・チェア)がある。')

# ── 2Fレストラン街 = 青ピン。**デジタルフロアマップを原寸で読んだ** ─────────
#   ⚠猫カフェMOCHA(239) と はま寿司(228) は**既に青ピンで登録済み**なので入れない
RESTAURANT = [
    ('fukutsu-rs-shabusai', 'しゃぶ菜 イオンモール福津店', 'しゃぶしゃぶ', '221'),
    ('fukutsu-rs-bikkuridonkey', 'びっくりドンキー イオンモール福津店', 'ハンバーグ', '222'),
    ('fukutsu-rs-futaba', '播州とんかつ 双葉 イオンモール福津店', 'とんかつ', '223'),
    ('fukutsu-rs-piasapido', 'ピアサピド イオンモール福津店', 'イタリアン', '224'),
    ('fukutsu-rs-sachifukuya', '釜戸ごはん さち福や イオンモール福津店', '和食', '225'),
    ('fukutsu-rs-benitora', '紅虎餃子房 イオンモール福津店', '中華', '226'),
    ('fukutsu-rs-takao', '博多天ぷら たかお イオンモール福津店', '天ぷら', '227'),
    ('fukutsu-rs-tullys', 'タリーズコーヒー イオンモール福津店', 'カフェ', '229'),
    ('fukutsu-rs-burgerking', 'バーガーキング イオンモール福津店', 'ハンバーガー', '230'),
    ('fukutsu-rs-osakanakazoku', 'おさかな家族 イオンモール福津店', '海鮮', '231'),
    ('fukutsu-rs-seattlesbest', 'シアトルズベストコーヒー イオンモール福津店', 'カフェ', '233'),
    ('fukutsu-rs-kushiya', '神楽食堂 串家物語 イオンモール福津店', '串揚げ', '234'),
    ('fukutsu-rs-pinocchio', 'グリル&パフェ ピノキオ イオンモール福津店', '洋食', '235'),
    ('fukutsu-rs-okashibakkashi', 'おかしばっかし イオンモール福津店', '菓子', '241'),
]
RS_VERDICT = ('イオンモール福津2階の**レストラン街**(F-2 2F入口)の%s区画。'
              'レストラン街にはおむつ替え台と多目的トイレがある(フロアマップで確認)。'
              '⚠こちらは未入店。子連れ設備は店ごとに要確認。')


def mk(i, name, genre, verdict, wish, cat):
    d = {'id': i, 'name': name, 'area': None, 'city': CITY, 'pref': PREF,
         'genre': genre, 'lat': LAT, 'lng': LNG,
         'visited': None if wish else VISITED, 'with': 'family',
         'kids': None, 'verdict': verdict,
         'video': {'youtube': None, 'tiktok': None, 'instagram': None},
         'thumb': None, 'wish': wish, 'in': PARENT}
    if cat:
        d['category'] = cat
    return d


NEW = []
for i, n, g, v in KIDS:
    NEW.append(mk(i, n, g, v, False, 'play'))
for i, n, g in FOODCOURT:
    NEW.append(mk(i, n, g, FC_VERDICT, False, None))
for i, n, g, no in RESTAURANT:
    NEW.append(mk(i, n, g, RS_VERDICT % no, True, None))

s = json.load(io.open(P, encoding='utf-8'))
shutil.copy(P, P + '.bak_fukutsu')
by = {x['id']: x for x in s}
names = {x.get('name') for x in s}

# ── ① 親施設を更新(新規登録ではない) ───────────────────────────
par = by.get(PARENT)
if not par:
    raise SystemExit('!! 親施設 %s が無い' % PARENT)
before = {'lat': par.get('lat'), 'lng': par.get('lng'), 'wish': par.get('wish')}
par['visited'] = par.get('visited') or VISITED
par['verdict'] = PARENT_VERDICT
# 現地で見たものだけ True にする。見ていない項目は null のまま
par['kids'] = {'stroller': True, 'diaper': True, 'tatami': True,
               'kidsChair': True, 'serveMin': None, 'noise': 'ok'}
print('○ 親施設を更新  %s  visited=%s' % (par['name'], par['visited']))

# ── ② テナントを追加 ─────────────────────────────────
added, skipped = [], []
for d in NEW:
    if d['id'] in by:
        skipped.append((d['id'], 'id が既にある')); continue
    if d['name'] in names:
        skipped.append((d['id'], '同名の「%s」が既にある' % d['name'])); continue
    s.append(d); by[d['id']] = d; names.add(d['name'])
    added.append(d)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ──────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
ids = [x['id'] for x in s2]
nm = [x.get('name') for x in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
dupn = [n for n in set(nm) if nm.count(n) > 1]
bad = [x['id'] for x in s2
       if x.get('wish') and any((x.get('video') or {}).get(k)
                                for k in ('youtube', 'tiktok', 'instagram'))]
untl = [d['id'] for d in added if d.get('until')]      # 常設店に until は禁止
p2 = [x for x in s2 if x['id'] == PARENT][0]
moved = {'lat': p2.get('lat'), 'lng': p2.get('lng'), 'wish': p2.get('wish')} != before

print()
for lbl, grp in (('子供向け(赤)', KIDS), ('フードコート(赤)', FOODCOURT),
                 ('レストラン街(青)', RESTAURANT)):
    got = [d for d in added if d['id'] in {g[0] for g in grp}]
    print('■ %s  %d件' % (lbl, len(got)))
    for d in got:
        print('   %s %-42s %s' % ('青' if d['wish'] else '赤', d['name'][:42], d['genre']))
print()
for i, why in skipped:
    print('- 見送り %-32s %s' % (i, why))
print()
print('件数 %d (+%d) / id重複 %d / 同名重複 %d / wish=trueなのに動画URLあり %d'
      % (len(s2), len(added), len(dup), len(dupn), len(bad)))
print('新規に until なし: %s / 親の座標とピン色: %s'
      % ('OK' if not untl else untl, '変えていない ✓' if not moved else '⚠変わった'))
if dup or dupn or bad or untl or moved:
    raise SystemExit('!! 検算NG dup=%s dupn=%s bad=%s' % (dup[:3], dupn[:3], bad[:3]))
print('OK')
