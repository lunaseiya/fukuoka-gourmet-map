# -*- coding: utf-8 -*-
"""赤川温泉 赤川荘(大分県竹田市久住町)を登録する(2026-09-04)。

**硫黄冷鉱泉**という全国的にも珍しい泉質で、湯温は約21度。
未訪問なので青ピン。子供の年齢制限やおむつ可否は公式サイトに記載が無く、
電話でしか確認できないので **bathAge は「記載なし(要問合せ)」** にして埋めない。
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

SPOT = {
    "id": "akagawaso_kuju",
    "name": "赤川温泉 赤川荘",
    "area": "久住",
    "city": "竹田市",
    "pref": "大分県",
    "genre": "温泉旅館・日帰り温泉",
    "lat": 33.066626,
    "lng": 131.232770,
    "address": "大分県竹田市久住町久住4008-1",
    "visited": None,
    "with": "family",
    "kids": {
        "stroller": None,
        "diaper": None,
        "tatami": None,
        "kidsChair": None,
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "⭐**全国的にも珍しい「硫黄冷鉱泉」**。硫酸・カルシウム・炭酸水素・ナトリウム・"
        "マグネシウムの各イオンを豊富に含み、**日本三大天然湯の花**とも言われる湯の花が出る。"
        "源泉の湯温は**約21度の冷鉱泉**なので、加温浴槽と冷泉を交互に入るスタイル。"
        "くじゅう連山の登山口(久住山)に近い。日帰り入浴 大人1,000円、10:00〜18:00(受付17:00まで)。"
        "定休は火〜木曜(GW・盆・正月は営業)。宿泊もできる。TEL 0974-76-0081。"
        "⚠**冷泉なので小さい子には寒い可能性がある**。子供の年齢制限・おむつ可否・子供料金は"
        "公式サイトに記載が無いため要問合せ。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "category": "onsen",
    "stay": True,
    "dayUse": True,
    "bathAge": "記載なし(要問合せ)。源泉21度の冷鉱泉のため小さい子には寒い可能性あり",
    "web": "https://akagawaonsen.webnode.jp/",
    "wish": True,
}


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    if any(s['id'] == SPOT['id'] or s['name'] == SPOT['name'] for s in sp):
        print('既にある:', SPOT['name']); return
    sp.append(SPOT)
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('追加:', SPOT['name'])
    print('  %s / %.6f, %.6f' % (SPOT['address'], SPOT['lat'], SPOT['lng']))
    print('  宿・温泉タブ / 日帰りOK / 青ピン(未訪問) / 全%d件' % len(sp))


if __name__ == '__main__':
    main()
