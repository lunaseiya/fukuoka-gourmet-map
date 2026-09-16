# -*- coding: utf-8 -*-
"""古民家かふぇ 美土里 を青ピンで登録する【2026-09-17ユーザー指示「これ青ピン登録しておいて」】

■ 情報の出所は**他者のInstagram投稿**(@paru_odekake_fukuoka / 2026年8月29日)
  ⚠**こちらで現地確認をしていない**ので、投稿者が書いた内容を転記する。
    投稿者自身も「投稿当時の情報のため、変更になる場合があります」と注記している。
    → verdict に**出所と「要確認」を明記**する(map-spot の鉄則: 断定しない)。
  ⚠写真は引用しない(サムネは無し)。文字情報だけを取る。

■ 投稿から読み取れた内容(逐語に近い形で)
  ・住所 福岡県福岡市南区弥永3-4-5
  ・営業時間 10:00〜19:00 / 定休日 木曜
  ・駐車場 無料
  ・**おむつ替え台・授乳室あり**(投稿者いわく「夏場は暑かった」)
  ・★**おもちゃ付きの完全個室**がある。部屋が広く赤ちゃん連れでも過ごせる。**2時間制**
  ・お子様ランチあり。落ち着いたテーブル席もあり
  ・人気の個室はすぐ埋まるので**事前予約推奨**

■ kids は**投稿で明言されているものだけ** True にする
  diaper(おむつ替え台あり)/ tatami は個室が座敷かどうか不明なので null。
  kidsChair は記載が無いので null。noise は完全個室があるので 'ok'。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

NEW = {
    'id': 'kominka-cafe-midori',
    'name': '古民家かふぇ 美土里',
    'area': '弥永',
    'city': '福岡市南区',
    'pref': '福岡県',
    'genre': 'カフェ',
    'lat': 33.526112,          # 住所「福岡県福岡市南区弥永3-4-5」から geocoding.jp
    'lng': 130.432227,
    'visited': None,
    'with': 'family',
    'kids': {'stroller': None, 'diaper': True, 'tatami': None,
             'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
    'verdict': ('⭐**おもちゃ付きの完全個室**がある古民家カフェ。部屋が広く赤ちゃん連れでも'
                '過ごせて、周りを気にせず食事できる。**2時間制**。'
                'お子様ランチあり。落ち着いたテーブル席もあるので用途で選べる。'
                '**おむつ替え台・授乳室あり**(夏場は暑かったとの声)。駐車場**無料**。'
                '営業10:00〜19:00 / 定休日 木曜。 '
                '⚠**人気の個室はすぐ埋まるので事前予約がおすすめ**。 '
                '⚠この情報は @paru_odekake_fukuoka さんの投稿(2026年8月)からの転記で、'
                '**こちらで現地確認はしていない**。行く前に公式で最新情報の確認を。'),
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
shutil.copy(P, P + '.bak_midori')
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
print('○ %s  青ピン  %s, %s' % (me['name'], me['lat'], me['lng']))
print('   visited は null: %s / until なし: %s'
      % ('OK' if me['visited'] is None else '⚠', 'OK' if not me.get('until') else '⚠'))
print()
print('件数 %d / id重複 %d / 同名重複 %d / wish=trueなのに動画URLあり %d'
      % (len(s2), len(dup), len(dupn), len(bad)))
if dup or dupn or bad or me.get('until'):
    raise SystemExit('!! 検算NG')
print('OK')
