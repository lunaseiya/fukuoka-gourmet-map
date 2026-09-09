# -*- coding: utf-8 -*-
"""口コミで受けた2件を既存レコードに反映する(2026-09-04)。どちらも既に登録済みだったので新規追加ではなく更新。

・和カフェ Tsumugi ワン・フクオカ店(id: onefukuoka_42) … 「子連れに良い」「子供椅子あり」の口コミ。
  ⚠子供椅子は口コミ由来で現地未確認なので、kids.kidsChair は true にせず**verdict にだけ書く**
  (map-spot スキルの「子連れ情報(kids)の取り方」ルール: 確度の低い情報は kids フィールドではなく文章で残す)。
・旅館初音荘(id: stayc3f0c48796) … 「キッズスペース付きの部屋がある」の口コミ。
  公式サイトで確認したところ**具体的な部屋タイプ名**(アトラクションファミリースイート/ルーム、
  すべり台付き)が見つかったので、それを verdict に追記する。
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

TSUMUGI_ADD = ('⭐ユーザーへの口コミで**子連れに良い・子供椅子がある**という情報を受けた'
               '(2026-09-04時点で現地未確認のため参考情報)。')
HATSUNE_ADD = ('⭐**すべり台付きのキッズスペース客室**がある(口コミで確認・2026-09-04)。'
               '本館2Fの「アトラクションファミリースイート」(すべり台+ホームシアター)、'
               '新館2-3Fの「アトラクションファミリールーム」(10畳・アトラクションロフト付すべり台、'
               '2023年3月リニューアル)の2タイプ。子供椅子の無料貸し出しあり。')


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    by_id = {s['id']: s for s in sp}

    t = by_id['onefukuoka_42']
    if 'kidsChair' not in (t.get('verdict') or '') and '子連れに良い' not in (t.get('verdict') or ''):
        t['verdict'] = (t.get('verdict') or '') + ' ' + TSUMUGI_ADD
        print('更新:', t['name'])
    else:
        print('既に反映済み:', t['name'])

    h = by_id['stayc3f0c48796']
    if 'アトラクションファミリー' not in (h.get('verdict') or ''):
        h['verdict'] = (h.get('verdict') or '') + ' ' + HATSUNE_ADD
        print('更新:', h['name'])
    else:
        print('既に反映済み:', h['name'])

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
