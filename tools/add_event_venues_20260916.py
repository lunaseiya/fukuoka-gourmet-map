# -*- coding: utf-8 -*-
"""**イベント会場として繰り返し出てくるのに未登録だった8件**を青ピンで登録する【2026-09-16】

■ なぜ必要か
  イベント一覧(map/events.html)で **220件中112件が座標を取れず**、
  「この近くのお店・遊び場」(=このページの収益導線)が出せていなかった。
  原因を数えたら、**会場が spots.json に無い**ものが上位を占めていた:
      大丸福岡天神店 21件 / 博多阪急 5件 / 筥崎宮 2件 /
      太宰府天満宮・宮地嶽神社・はかた伝統工芸館・道の駅原鶴 各1件
  会場を登録すれば ①イベントの座標が埋まって近隣スポットが出る
                  ②「会場のページ」導線が出る(名前が完全一致するため)
                  ③マップ自体のカバレッジも上がる

■ ⚠筥崎宮は「イベント」としてしか登録されていなかった
  既存の `筥崎宮 放生会` は `until` 付きの**期間限定イベント**なので、
  **会期が過ぎると地図から消える**。恒久スポットとしての筥崎宮が無い状態だった。
  → 別idで神社そのものを登録する(イベント側はそのまま。会期後に自然に消える)

■ ピンは全部**青(wish=true / visited=None)**
  8件とも**まだ行っていない**。行ったら赤に変えて visited を入れる。

■ 岩田屋本店はイベント源に出ていないが、ユーザー確定で天神の催事会場3店を揃えた
  (2026-09-16「百貨店3店＋主要3社＋工芸館(8件)」を選択)

■ 座標は **住所で geocoding.jp から取得**(名前で引くと精度が怪しい)。10秒以上あけた。
  ⚠博多阪急だけ「博多駅中央街1-1」の表記でないと `<lat>0</lat>` が返った。
    取れた 33.58928,130.419038 は既存のJR博多シティ内スポット群(33.5899前後)と整合する
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')


def mk(i, name, area, city, genre, lat, lng, verdict, web, kids=None, cat='play'):
    d = {'id': i, 'name': name, 'area': area, 'city': city, 'pref': '福岡県',
         'genre': genre, 'lat': lat, 'lng': lng, 'visited': None, 'with': 'family',
         'kids': kids, 'verdict': verdict,
         'video': {'youtube': None, 'tiktok': None, 'instagram': None},
         'thumb': None, 'wish': True, 'web': web}
    if cat:
        d['category'] = cat
    return d


def kd(stroller=None, diaper=None):
    return {'stroller': stroller, 'diaper': diaper, 'tatami': None,
            'kidsChair': None, 'serveMin': None, 'noise': None}


NEW = [
    # ── 天神・博多の百貨店(催事会場として最も出てくる) ──────────────
    mk('daimaru-fukuoka-tenjin', '大丸福岡天神店', '天神', '福岡市中央区', '百貨店',
       33.588815, 130.402358,
       '⭐**授乳室は本館7階と東館エルガーラ5階**。**子供用トイレ(男児・女児用)が本館7階**にあり、'
       '親子トイレは本館3階・5階・7階と東館エルガーラ1階・4階。おむつ交換台は本館B2・B1・2〜4階・'
       '6〜8階と東館1〜6階(紳士用もあり)。ベビーカー貸出は本館1階総合案内所と東館エルガーラB2'
       'サービスカウンター(生後3か月頃〜2歳・体重15kg以下)。'
       '営業10:00〜19:00(本館2〜8階・東館エルガーラ3〜5階)。'
       '⚠肉フェス・北海道展などの**催事が多く、イベント一覧に一番よく出てくる会場**。'
       '催事の会期は館の公式で確認する',
       'https://www.daimaru-fukuoka.jp/', kd(True, True)),

    mk('hakata-hankyu', '博多阪急', '博多駅', '福岡市博多区', '百貨店',
       33.58928, 130.419038,
       '⭐**7階のベビールームが県内屈指**。授乳室は個室3部屋+相部屋1部屋(計4組)で'
       '**ベビーカーのまま入室できる**。おむつ替えベッド7台+自動式の紙おむつ専用ゴミ箱2台、'
       '**離乳食スペース(トリップトラップ3台・計6組)とベビーフード販売**、'
       '**調乳専用の浄水給湯器と電子レンジ**まである。ベビーカー貸出は7階こども服中央カウンター'
       '10台・1階インフォメーション20台(新生児〜3歳)。全館10:00〜20:00。TEL 092-461-1381。'
       'JR博多シティ内なので雨でも駅から濡れずに行ける',
       'https://www.hankyu-dept.co.jp/hakata/', kd(True, True)),

    mk('iwataya-honten', '岩田屋本店', '天神', '福岡市中央区', '百貨店',
       33.588276, 130.397505,
       'ベビー休憩室・授乳室は**本館地下2階(要確認)**。営業10:00〜20:00。TEL 092-721-1111。'
       '⚠子連れ設備の詳細はまだ現地で確認していない。大丸・博多阪急と並ぶ天神の催事会場',
       'https://www.iwataya-mitsukoshi.mistore.jp/iwataya.html', kd()),

    # ── 神社(祭り・七五三で子連れの行き先になる) ────────────────
    # ⚠既存の `筥崎宮 放生会` は until 付きのイベントなので会期後に消える。これは恒久スポット
    mk('hakozakigu', '筥崎宮', '箱崎', '福岡市東区', '神社',
       33.614433, 130.42295,
       '日本三大八幡宮のひとつ。⭐**9月12〜18日の放生会は博多三大祭り**('
       'どんたく・山笠と並ぶ)で、露店とお化け屋敷が並ぶ。隔年の9月12〜14日には神幸行事。'
       '境内6:00〜19:00 / 社務所8:30〜17:00。TEL 092-641-7431。駐車場あり。'
       '⚠放生会の期間は周辺が非常に混み、駐車場も埋まる。'
       'おむつ替え・授乳の設備は未確認',
       'https://hakozakigu.or.jp/', kd()),

    mk('dazaifu-tenmangu', '太宰府天満宮', '宰府', '太宰府市', '神社',
       33.520801, 130.534875,
       '学問の神様・菅原道真を祀る全国天満宮の総本宮。参道に梅ヶ枝餅の店が並ぶ。'
       '開門は春分〜秋分の前日6:00・それ以外6:30。閉門は4・5・9〜11月19:00 / 6〜8月19:30 / '
       '12〜3月18:30。駐車場は約1,400台で**太宰府駐車センターの普通車は1回500円**'
       '(当日24時まで・再入場不可)。⭐**九州国立博物館と隣接**していて一緒に回れる。'
       'おむつ替え・授乳の設備は未確認',
       'https://www.dazaifutenmangu.or.jp/', kd()),

    mk('miyajidake-jinja', '宮地嶽神社', '宮司元町', '福津市', '神社',
       33.779976, 130.485976,
       '日本一の大注連縄で知られる。⭐**参道の先が海までまっすぐ抜ける「光の道」**が'
       '年2回(2月下旬・10月下旬)夕日と重なる。**駐車場は第一・第二で約700台が無料**なので'
       '子連れでも停めやすい。TEL 0940-52-0016。'
       '9月には秋季大祭。おむつ替え・授乳の設備は未確認',
       'https://www.miyajidake.or.jp/', kd()),

    # ── その他の会場 ────────────────────────────────
    mk('hakata-dentou-kougeikan', 'はかた伝統工芸館', '博多駅前', '福岡市博多区', '博物館',
       33.593757, 130.418201,
       '⭐**入館無料**(体験教室等は有料)。博多織・博多人形などの展示と'
       '企画展をやっていて、**屋内なので雨の日の逃げ場になる**。'
       '10:00〜18:00(入館は17:30まで)。⚠**休館は毎週水曜**'
       '(祝日の場合は開館し翌平日が振替休日)と年末年始12/29〜1/3。'
       'TEL 092-409-5450。博多駅前1-23-2 Park Front博多駅前一丁目1階',
       'https://hakata-dentou-kougeikan.jp/', kd()),

    mk('michinoeki-harazuru', '道の駅原鶴 ファームステーションバサロ', '杷木', '朝倉市', '道の駅',
       33.354342, 130.785503,
       '朝倉の農産物直売所。8:30〜17:30(第4水曜は17:00まで)、休みは年末年始。'
       '⚠子連れ設備は未確認。原鶴温泉のすぐ近くなので温泉とあわせて寄れる',
       'https://fs-basaro.jp/', kd(), cat=None),
]

s = json.load(io.open(P, encoding='utf-8'))
by = {x['id']: x for x in s}
names = {x.get('name') for x in s}
shutil.copy(P, P + '.bak_eventvenues')

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
dup = [i for i in set(ids) if ids.count(i) > 1]
nm = [x.get('name') for x in s2]
dupn = [n for n in set(nm) if nm.count(n) > 1]
bad = [x['id'] for x in s2
       if x.get('wish') and any((x.get('video') or {}).get(k)
                                for k in ('youtube', 'tiktok', 'instagram'))]
# 常設店に until を付けていないこと(店ごと地図から消える事故の防止)
untl = [d['id'] for d in added if d.get('until')]
nocoord = [d['id'] for d in added if d['lat'] is None or d['lng'] is None]

for d in added:
    print('○ %-30s %-12s %s, %s  青ピン' % (d['name'][:30], d['genre'], d['lat'], d['lng']))
for i, why in skipped:
    print('- 見送り %-26s %s' % (i, why))
print()
print('件数 %d (+%d) / id重複 %d / 同名重複 %d / wish=trueなのに動画URLあり %d'
      % (len(s2), len(added), len(dup), len(dupn), len(bad)))
print('新規に until を付けていない: %s / 座標欠け: %s'
      % ('OK' if not untl else untl, 'なし' if not nocoord else nocoord))
if dup or dupn or bad or untl or nocoord:
    raise SystemExit('!! 検算NG dup=%s dupn=%s bad=%s' % (dup[:3], dupn[:3], bad[:3]))
print('OK  既存スポットのピンの色・座標は触っていない')
