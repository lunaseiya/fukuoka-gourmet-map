# -*- coding: utf-8 -*-
"""STAND T -HAKATA- を青ピンで登録する【2026-09-17ユーザー指示】

ユーザーの指示(逐語):
  「12_STAND看板は使用しなくて良いです、今回入っていないお店です。
    良ければMAPのみ登録ください。」
  → 動画には使わないが、マップには載せる。**入っていないので青ピン(wish=true)**。

■ 何の店か(裏取り)
  ロイヤルグループの「東京×博多」ハイブリッド立ち飲み酒場。
  **2026年7月21日オープン**(西日本シティビルの開業と同日。複数の記事で一致)。
  おつまみ250円から、東京で話題のロメスパを出す。昼は定食、夜は立ち飲み。
  出所: ファンファン福岡 https://fanfun.jp/321634/ / 号外NET福岡市博多区 / TABERY
  ⚠**立ち飲み酒場なので子連れ向きではない**。`with` は 'friends' にして
    `kids` は null のままにする(README: with が solo/friends なら kids は null でよい)。
    verdict にも子連れ向きでない旨を書く(このマップは子連れ用なので明示しておく)

■ 座標は同じビル1Fの**シェイクシャック博多店と同じ点**を使う
  (map-spot の商業施設ルール。館内の店は建物の代表座標でよい。⚠推測で散らさない)

■ ⚠掲示にあった他のテナントは**登録していない**
  現地のテナント案内(写真11)を原寸で読むと、1Fは
    1 BLUE BOTTLE COFFEE / 2 SHAKE SHACK / 3 STAND T / 4 dacō I'm donut ? / B1F LAUNDRY STATION
  の5区画だった。**台本には BLUE BOTTLE COFFEE が抜けていた**(今回の読み直しで発覚)。
  指示は STAND のみだったので他は入れていない。要るなら別途登録する。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

NEW = {
    'id': 'standt-hakata',
    'name': 'STAND T -HAKATA-',
    'area': '西日本シティビル 1F',
    'city': '福岡市博多区',
    'pref': '福岡県',
    'genre': '立ち飲み',
    'lat': 33.589442,          # シェイクシャック博多店と同じ(同じビルの1F)
    'lng': 130.418255,
    'visited': None,
    'with': 'friends',
    'kids': None,
    'verdict': ('ロイヤルグループの「東京×博多」ハイブリッド立ち飲み酒場。2026年7月21日'
                'オープン(西日本シティビルの開業と同日)。おつまみ250円から、東京で話題の'
                'ロメスパも。昼は定食、夜は立ち飲み。 '
                '⚠**立ち飲み酒場なので子連れ向きではない**。同じビル1Fのシェイクシャックや'
                '隣の明治公園とセットで、大人だけのときの選択肢として。 '
                '⚠営業時間・定休日は未確認。'),
    'video': {'youtube': None, 'tiktok': None, 'instagram': None},
    'thumb': None,
    'wish': True,
}

s = json.load(io.open(P, encoding='utf-8'))
by = {x['id']: x for x in s}
names = {x.get('name') for x in s}
if NEW['id'] in by:
    raise SystemExit('!! id が既にある: %s' % NEW['id'])
if NEW['name'] in names:
    raise SystemExit('!! 同名が既にある: %s' % NEW['name'])
shutil.copy(P, P + '.bak_standt')
s.append(NEW)
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
me = [x for x in s2 if x['id'] == NEW['id']][0]
print('○ %s  青ピン  %s, %s  %s' % (me['name'], me['lat'], me['lng'], me['genre']))
print('   until なし: %s / visited は null: %s'
      % ('OK' if not me.get('until') else '⚠付いている', 'OK' if me['visited'] is None else '⚠入っている'))
print()
print('件数 %d / id重複 %d / 同名重複 %d / wish=trueなのに動画URLあり %d'
      % (len(s2), len(dup), len(dupn), len(bad)))
if dup or dupn or bad or me.get('until'):
    raise SystemExit('!! 検算NG')
print('OK')
