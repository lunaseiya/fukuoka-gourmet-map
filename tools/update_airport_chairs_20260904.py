# -*- coding: utf-8 -*-
"""福岡空港の3店で子供椅子を現地確認した内容を反映する(2026-09-04)。

・黄金色の豚 福岡空港店 … 木製の子供椅子(ベルト付き)3台を実写で確認 → kidsChair: true
・博多一幸舎 福岡空港店 … 木製の子供椅子2台(旧型+CRES製ベルト付き)を実写で確認 → kidsChair: true
・博多鶏sobaナカムラボ 福岡空港店 … 写真は補助的な座面かさ上げクッションで、
  **ベビーチェアと呼べるものではない**とユーザーが判断(2026-09-04)。
  kidsChair は true にせず、verdict にだけ「座面かさ上げの補助椅子あり」と書く。
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')


def add(v, note):
    return (v or '') + ' ' + note


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    by_id = {s['id']: s for s in sp}

    a = by_id['ape3926bd148']  # 黄金色の豚
    a['kids']['kidsChair'] = True
    a['verdict'] = add(a.get('verdict'),
                       '⭐**木製の子供椅子(ベルト付き)を3台**実写で確認(2026-09-04)。')

    b = by_id['ap56c212742b']  # 博多一幸舎 福岡空港店
    b['kids']['kidsChair'] = True
    b['verdict'] = add(b.get('verdict'),
                       '⭐**木製の子供椅子を2台**実写で確認(2026-09-04)。')

    c = by_id['ap64f6682535']  # ナカムラボ
    c['verdict'] = add(c.get('verdict'),
                       '座面をかさ上げする補助クッションの用意はあるが、'
                       '**ベビーチェアと呼べるものではない**(2026-09-04現地確認)。')

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    for s in (a, b, c):
        print('更新:', s['name'], '/ kidsChair=', s['kids'].get('kidsChair'))


if __name__ == '__main__':
    main()
