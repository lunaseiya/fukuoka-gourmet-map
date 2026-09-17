# -*- coding: utf-8 -*-
"""JR博多シティ 屋上つばめの杜ひろば を青ピンで登録する【2026-09-17】

きっかけ: ユーザーが「10月屋上つばめの杜ひろばイベント」の告知を見つけて
「定期的にイベントしてるのか / 源に入れるべきか」と聞いてきた。調べたら月次で
子連れイベントを回している屈指の場所なのに、**マップには未登録**だった
(博多シティ関連は一風堂博多駅店・名島亭デイトス店・マクドナルドアミュプラザ博多店
 といったテナント飲食店だけ)。

■ 裏取りは**すべて公式サイト**(2026-09-17に実測)
  ・屋上営業時間 10:00-22:00                    /kids/detail/?cd=000033 (2026/08/31更新)
  ・⚠**屋上つばめ電車は運行終了**               同上。名前の由来の乗り物はもう無い
  ・⚠**天空の広場の三輪車はやけど防止で使用中止**(当面の間)  同上
  ・荒天時は閉鎖する場合あり                     同上
  ・おむつ交換 = アミュプラザ**全階(1F・2Fおよび屋上を除く)** /information/service/
    → ⚠**屋上にはおむつ交換台が無い**。子連れには効く注意点なので verdict に書く
  ・授乳室 = 6F・7F・9F・10F アミュプラザ博多(個室・お湯の出る蛇口あり)
  ・子ども用お手洗い = アミュプラザ博多 6F・8F
  ・ベビーカー無料貸出 = 1F・3F アミュプラザ博多インフォメーション
  ・鉄道神社が屋上にある(レポート「鉄道神社に灯る竹あかり」)
  ・ファーマーズくらぶ(屋上の農園)で収穫体験を回している

■ 座標
  ⚠**geocoding.jp は「博多駅中央街1-1」で lat=0 を返す**(表記を変えても駄目だった)。
  推測で作らず、**同じ建物内の裏取り済みスポット**
  `ippuudouhakataekimise-83`(一風堂 博多駅店＝くうてん9F)の座標を借りる。
  屋上はそのくうてんの真上なので、建物としては同一点で問題ない。

■ ピンの色
  **青(wish=True / visited=None)**。公式サイトで調べただけで、まだ行っていない。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
spots = json.load(io.open(P, encoding='utf-8'))
by_id = {x['id']: x for x in spots}

SRC = by_id['ippuudouhakataekimise-83']          # 同じ建物(くうてん9F)から座標を借りる
NEW = {
    'id': 'tsubamenomori-hirobajrhakatacity',
    'name': 'JR博多シティ 屋上つばめの杜ひろば',
    'area': '博多駅(JR博多シティ屋上)',
    'genre': '屋上ひろば',
    'lat': SRC['lat'],
    'lng': SRC['lng'],
    'visited': None,
    'with': 'family',
    'kids': {
        # 屋上そのものにはおむつ交換台が無い(公式の記載が「屋上を除く」)。
        # ベビーカーは館内で無料貸出があり、屋上まで上がれる
        'stroller': True,
        'diaper': False,
        'tatami': None,
        'kidsChair': None,
        'serveMin': None,
        'noise': None,
    },
    'verdict': ('⭐JR博多駅ビルの屋上にある無料のひろば。10:00〜22:00で、'
                '鉄道神社・芝生・展望テラスがあり、こどもCITY HAKATAとして'
                '月1回ペースで子連れイベント(収穫体験・天体観測・工作教室・ミニ動物園)を開催。'
                'ベビーカーは1F・3Fインフォメーションで無料貸出。'
                '⚠おむつ交換台はアミュプラザ各階にあるが**屋上には無い**(公式表記が「屋上を除く」)。'
                '授乳室は6F・7F・9F・10F、子ども用トイレは6F・8F。'
                '⚠**屋上つばめ電車は運行終了**、天空の広場の三輪車もやけど防止で当面使用中止。'
                '荒天時は閉鎖の場合あり(2026-09-17時点の公式情報)'),
    'video': {'youtube': None, 'tiktok': None, 'instagram': None},
    'thumb': None,
    'city': '福岡市博多区',
    'pref': '福岡県',
    'category': 'play',
    'wish': True,
    'address': '福岡県福岡市博多区博多駅中央街1-1 JR博多シティ屋上',
    'web': 'https://www.jrhakatacity.com/kids/',
}

if NEW['id'] in by_id:
    raise SystemExit('!! 既に登録済み: ' + NEW['id'])
same = [x for x in spots if x['name'] == NEW['name']]
if same:
    raise SystemExit('!! 同名が居る: ' + same[0]['id'])

shutil.copy(P, P + '.bak_tsubamenomori')
spots.append(NEW)
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

# ── 検算 ─────────────────────────────────────────────
back = json.load(io.open(P, encoding='utf-8'))
ids = [x['id'] for x in back]
names = [x['name'] for x in back]
dup_id = [i for i in set(ids) if ids.count(i) > 1]
dup_nm = [n for n in set(names) if names.count(n) > 1]
bad = [x['id'] for x in back if x.get('wish') and (x.get('video') or {}).values()
       and any((x.get('video') or {}).values())]
print('登録: %s (%s)' % (NEW['name'], NEW['id']))
print('  座標 %s, %s ← %s から借用' % (NEW['lat'], NEW['lng'], SRC['id']))
print('  スポット数 %d → %d' % (len(spots) - 1, len(back)))
print('  id重複 %s / 同名重複 %s' % (dup_id or 'なし ✓', dup_nm or 'なし ✓'))
print('  青ピンに動画URLがある矛盾: %s' % (bad or 'なし ✓'))
