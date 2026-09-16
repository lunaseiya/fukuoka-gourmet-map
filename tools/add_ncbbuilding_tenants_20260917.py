# -*- coding: utf-8 -*-
"""西日本シティビルのテナント案内から登録できるものを登録する【2026-09-17ユーザー指示】

ユーザーの指示(逐語):
  「テナント案内からMAP登録できるものは照合して登録お願いします。」

■ 掲示(写真11)を**原寸で読み直して確定した全区画**
    1F  1 BLUE BOTTLE COFFEE / 2 SHAKE SHACK / 3 STAND T / 4 dacō I'm donut ?
    B1F LAWSON STATION
    上層 wework / NCB創業応援サロンHAKATA
  ⚠**台本には BLUE BOTTLE COFFEE が抜けていた**(今回の読み直しで発覚)。
  ⚠B1F は最初「LAUNDRY STATION」と読み違えた。**正しくは LAWSON STATION**(ローソン)。
    縮小画像で読んだせい。原寸クロップで確定させた

■ 登録するもの / しないもの
  | 区画 | 扱い |
  |---|---|
  | BLUE BOTTLE COFFEE | **登録**(ブルーボトルコーヒー 博多カフェ) |
  | dacō / I'm donut ? | **登録**(1空間に2ブランド) |
  | SHAKE SHACK | 既に赤ピンで登録済み(`shakeshack-hakata`) |
  | STAND T | 既に青ピンで登録済み(`standt-hakata`) |
  | B1F LAWSON STATION | **登録しない**。コンビニは子連れの行き先として意味が薄く、
  |                    | 入れ始めると数百件になる(このマップの趣旨から外れる) |
  | wework / NCB創業応援サロン | **登録しない**。オフィスで「おでかけ先」ではない |

■ ピンは**青(未訪問)**。今回入ったのはシェイクシャックだけ

■ 裏取り(複数記事で一致)
  ・ブルーボトルコーヒー 博多カフェ … 2026年7月21日オープン / 8:00〜20:00 /
    西日本シティビル1F / **九州2店舗目**(2024年2月の福岡天神カフェに続く)
    出所: Blue Bottle Coffee Japan プレスリリース(PR TIMES) / fukuoka-leapup / カフェトライブ
  ・dacō / I'm donut ? 博多駅前 … 2026年7月21日オープン / 8:00〜20:00(L.O.19:30) /
    **dacōは16席**。生ドーナツ専門店とベーカリーカフェの2ブランドが仕切りなしの1空間。
    運営は株式会社 peace put(平子良太)
    出所: peace put プレスリリース(PR TIMES) / 西日本新聞 / 食べログ
  ⚠子連れ設備(ベビーカー可否・おむつ替え)は**どの記事にも無い**ので kids は null

■ 座標は同じビル1Fのシェイクシャック博多店と同じ点(館内の店は建物の代表座標でよい)
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
LAT, LNG = 33.589442, 130.418255      # 西日本シティビル 1F

NEW = [
    {'id': 'bluebottle-hakata',
     'name': 'ブルーボトルコーヒー 博多カフェ',
     'genre': 'カフェ',
     'verdict': ('2026年7月21日オープン。西日本シティビル1F。**九州2店舗目**'
                 '(2024年2月の福岡天神カフェに続く)。8:00〜20:00。'
                 'JR・地下鉄「博多駅」博多口から徒歩約1分。 '
                 '⚠子連れ設備(ベビーカーでの入店・おむつ替え)は未確認。'
                 '隣の明治公園とセットで寄れる立地。'),
     'web': 'https://store.bluebottlecoffee.jp/pages/hakata'},
    {'id': 'imdonut-daco-hakata',
     'name': "I'm donut ? ／ dacō 博多駅前",
     'genre': 'ドーナツ、ベーカリー',
     'verdict': ('2026年7月21日オープン。西日本シティビル1F。生ドーナツ専門店'
                 '**I\'m donut ?** とベーカリーカフェ **dacō** の2ブランドが'
                 '**仕切りなしの1空間**に入っている(運営は株式会社peace put・平子良太)。'
                 '8:00〜20:00(L.O.19:30)、**dacōは16席**。 '
                 '⚠開店直後から行列ができている。子連れ設備は未確認。'),
     'web': None},
]

s = json.load(io.open(P, encoding='utf-8'))
by = {x['id']: x for x in s}
names = {x.get('name') for x in s}
shutil.copy(P, P + '.bak_ncbtenants')

added, skipped = [], []
for n in NEW:
    if n['id'] in by:
        skipped.append((n['id'], 'id が既にある')); continue
    if n['name'] in names:
        skipped.append((n['id'], '同名の「%s」が既にある' % n['name'])); continue
    d = {'id': n['id'], 'name': n['name'], 'area': '西日本シティビル 1F',
         'city': '福岡市博多区', 'pref': '福岡県', 'genre': n['genre'],
         'lat': LAT, 'lng': LNG, 'visited': None, 'with': 'family', 'kids': None,
         'verdict': n['verdict'],
         'video': {'youtube': None, 'tiktok': None, 'instagram': None},
         'thumb': None, 'wish': True}
    if n['web']:
        d['web'] = n['web']
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
untl = [d['id'] for d in added if d.get('until')]
for d in added:
    print('○ 青 %-32s %-18s %s, %s' % (d['name'][:32], d['genre'], d['lat'], d['lng']))
for i, why in skipped:
    print('- 見送り %-24s %s' % (i, why))
print()
print('■ 登録しなかった区画(理由つき)')
print('   LAWSON STATION(B1F) … コンビニは子連れの行き先として意味が薄い')
print('   wework / NCB創業応援サロンHAKATA … オフィスで「おでかけ先」ではない')
print()
print('件数 %d (+%d) / id重複 %d / 同名重複 %d / wish=trueなのに動画URLあり %d / 新規にuntil %s'
      % (len(s2), len(added), len(dup), len(dupn), len(bad), 'なし' if not untl else untl))
if dup or dupn or bad or untl:
    raise SystemExit('!! 検算NG')
print('OK')
