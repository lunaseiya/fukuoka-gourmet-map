# -*- coding: utf-8 -*-
"""会期が残っているイベントに **会場スポットの id を `in` で紐付ける**【2026-09-16ユーザー確定】

ユーザーの指摘:
  「このイベントで記載されている内容って、一部MAPで使われてますよね？たしか。。
    それはどう取り扱うべきですかね？ ボスイーゾビルの魔法の美術館とか、香りの博物館とか」
  → 調べたら**「会場」と「そこで開催中のイベント」が別レコードで、紐付いていなかった**。
    (例: `ev-15659 魔法の美術館` と `bossezofukuoka BOSS E・ZO FUKUOKA` が別ピン)

■ 何が問題だったか
  ① 同じ座標にピンが2本立つ(会期が切れればイベント側は消えるが、今は重複して見える)
  ② **収益機会を捨てていた**。イベント側は asoview/tabelog を持たないので、
     イベントを見た人が**会場のチケットリンクに到達できない**
  ③ イベント一覧の座標埋めを「会場名の文字列突合」でやっていたため、
     area が「BOSS E・ZO FUKUOKA **6Fイベントホール**」のように館内の場所まで入ると
     突合できず、**220件中90件しか座標が取れていなかった**

■ どう直すか
  `in` に会場スポットの id を入れる。既に館内テナント(キッザニア等)で使っている仕組みなので
  マップ側の処理にそのまま乗る。イベント一覧は `in` を最優先で見て会場を確定する。

■ 紐付けは**1件ずつ近傍と名前を突き合わせて手で確定させた**(自動名寄せはしない)。
  ⚠**会場が spots.json に無いものは None のまま**にする。推測で別の施設に結びつけない。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

# (イベントid, 会場スポットid, 根拠)
LINK = [
    ('ev-15659', 'bossezofukuoka',
     'area=「BOSS E・ZO FUKUOKA 6Fイベントホール」。0.00kmで一致'),
    ('ev-17268', 'onojokokoronofurusatokan',
     'area=「大野城心のふるさと館」。0.01kmで一致'),
    ('ev-591660', 'fukuokakenseishounenkagakuka',
     'area=「福岡県青少年科学館」。0.01kmで一致。会場側にアソビューリンクあり'),
    ('ev-2dcc05e8-b7e9-409d-bb7a-1d420d6ca028', 'aeonmallkashiihama',
     'area=「イオンモール香椎浜 1階セントラルコート」。館が一致'),
    ('ev-a50d43bf-8107-4ba7-9606-434966d96b95', 'aeonmallchikushino',
     'area=「イオンモール筑紫野」。館が一致'),
    ('ev-3614679-html', 'lalaportfukuoka',
     'area=「ららぽーと福岡」。館が一致'),
    ('ev-597275', 'hakozakihatotaroushouten', None),   # ⚠下で除外する。下記の注記を読む
]
# ⚠**会場が spots.json に無い / 特定できないものは紐付けない**。
#   放生会は筥崎宮そのもののスポットが無く、近傍に出るのは**参道の飲食店**なので
#   会場として結びつけるのは誤り。キャナルお目覚めフェスも近傍がラーメン店ばかりで
#   「キャナルシティ博多」のスポットが無い。ジブリ展(山口/佐賀)も美術館のスポットが無い。
#   → これらは `in` を付けず、イベント一覧では従来どおり近隣スポットだけを出す
SKIP = {
    'ev-597275': '筥崎宮のスポットが無い(近傍は参道の飲食店なので会場ではない)',
    'ev-194-publish-begin-26-09-09-publish-en': 'キャナルシティ博多のスポットが無い',
    'aso_kinro_ghibli_yamaguchi': '山口県立美術館のスポットが無い',
    'aso_kinro_ghibli_saga': '佐賀県立美術館・博物館のスポットが無い',
    'chinsuru_restaurant_fukuoka': 'アイランドアイのスポットが無い(近傍は館内の別テナント)',
    'ev-596239': 'イオン甘木店のスポットが無い',
    'ev-596517': 'TNC住宅展示場のスポットが無い',
}

s = json.load(io.open(P, encoding='utf-8'))
by = {x['id']: x for x in s}
shutil.copy(P, P + '.bak_eventvenue')
done, skipped, miss = [], [], []
for eid, vid, why in LINK:
    if eid in SKIP:
        skipped.append((eid, SKIP[eid])); continue
    if eid not in by:
        miss.append(eid); continue
    if vid not in by:
        miss.append(vid); continue
    ev = by[eid]
    before = {'wish': ev.get('wish'), 'until': ev.get('until'),
              'lat': ev.get('lat'), 'lng': ev.get('lng')}
    ev['in'] = vid
    done.append((eid, vid, by[vid].get('name'), why, before))
for eid, why in SKIP.items():
    if eid in by and not any(d[0] == eid for d in done):
        skipped.append((eid, why))
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
    print('○ %-46s → in=%-30s %s' % ((y.get('name') or '')[:46], vid, vname))
print()
for eid, why in sorted(set(skipped)):
    print('- 紐付けない %-40s %s' % ((b2.get(eid, {}).get('name') or eid)[:40], why))
ids = [x['id'] for x in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
print()
print('件数 %d / id重複 %d件 / 紐付け %d件 / 見送り %d件 / 参照切れ %d件'
      % (len(s2), len(dup), len(done), len(set(skipped)), len(miss)))
if dup or ng or miss:
    raise SystemExit('!! 検算NG dup=%s 変化=%s 参照切れ=%s' % (dup[:3], ng, miss))
print('OK  ピンの色・会期・座標は変えていない')
