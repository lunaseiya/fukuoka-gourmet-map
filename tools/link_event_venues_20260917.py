# -*- coding: utf-8 -*-
"""**前回「会場スポットが無い」で見送ったイベント**に `in` を付ける【2026-09-17】

2026-09-16 に `link_event_venues_20260916.py` で6件を紐付けたとき、
「会場が spots.json に無い」ものは**推測で結びつけず見送った**。
その後この2つが登録/判明したので、今回付ける:

  ・**筥崎宮** … 2026-09-17 に恒久スポット(`hakozakigu`)として登録した
    (それまでは「筥崎宮 放生会」という until 付きイベントしか無く、会期後に消える状態だった)
  ・**キャナルシティ博多** … 実は `canalcityhakata` で**既に登録済み**だった。
    前回「スポットが無い」と判断したのは確認漏れ(名前突合で判明した)

■ なぜ `in` が要るか(今回の実害)
  イベント一覧で**放生会が同じ日に2回出ていた**。統合の条件に「同じ会場」を使っているが、
  片方は会場名の文字列突合で `venueSpot='hakozakigu'`、もう片方は `venue='筥崎宮'` だけで、
  **キーが食い違って統合できなかった**。`in` を付けると両方が同じ会場として揃う。
  (あわせて export 側のキーも名前ベースに統一した)

⚠まだ見送るもの(会場が spots.json に無い。**推測で別の施設に結びつけない**):
  山口県立美術館 / 佐賀県立美術館・博物館 / アイランドアイ / イオン甘木店 / TNC住宅展示場
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

# (イベントid, 会場スポットid, 根拠)
LINK = [
    ('ev-597275', 'hakozakigu',
     '「筥崎宮 放生会」の area=「筥崎宮」。2026-09-17に筥崎宮を恒久スポットとして登録した'),
    ('ev-194-publish-begin-26-09-09-publish-en', 'canalcityhakata',
     'キャナルお目覚めフェス。canalcityhakata は既に登録済みだった(前回は確認漏れ)'),
]

s = json.load(io.open(P, encoding='utf-8'))
by = {x['id']: x for x in s}
shutil.copy(P, P + '.bak_eventvenue2')
done, miss = [], []
for eid, vid, why in LINK:
    if eid not in by:
        miss.append(('イベント', eid)); continue
    if vid not in by:
        miss.append(('会場', vid)); continue
    ev = by[eid]
    if ev.get('in') == vid:
        print('- 既に紐付いている %s → %s' % (eid, vid)); continue
    before = {'wish': ev.get('wish'), 'until': ev.get('until'),
              'lat': ev.get('lat'), 'lng': ev.get('lng')}
    ev['in'] = vid
    done.append((eid, vid, by[vid].get('name'), why, before))
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ─────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
b2 = {x['id']: x for x in s2}
ng = []
for eid, vid, vname, why, before in done:
    y = b2[eid]
    after = {'wish': y.get('wish'), 'until': y.get('until'),
             'lat': y.get('lat'), 'lng': y.get('lng')}
    if after != before or y.get('in') != vid:
        ng.append(eid)
    print('○ %-40s → in=%-20s (%s)' % ((y.get('name') or '')[:40], vid, vname))
    print('   根拠: %s' % why)
ids = [x['id'] for x in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
print()
print('件数 %d / id重複 %d件 / 紐付け %d件 / 参照切れ %s'
      % (len(s2), len(dup), len(done), miss or 'なし'))
if dup or ng or miss:
    raise SystemExit('!! 検算NG 変化=%s 参照切れ=%s' % (ng, miss))
print('OK  ピンの色・会期・座標は変えていない')
