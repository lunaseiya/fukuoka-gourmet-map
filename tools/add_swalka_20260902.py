# -*- coding: utf-8 -*-
"""Kidsspace & Coffeestand Swalka(福岡市南区長住)をマップに追加する(2026-09-02)。

キッズスペースが主役でコーヒースタンドが併設という業態なので、
**遊び場としても飲食としても**登録する(ユーザー指示)。
1スポットを2タブに載せる仕組みは `cats:["play","gourmet"]`(一蘭の森と同じ形)。

未訪問なので青ピン(wish=True / visited=None)。
"""
import os, json, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

SPOT = {
    "id": "swalka_nagazumi",
    "name": "Kidsspace & Coffeestand Swalka",
    "area": "長住",
    "city": "福岡市南区",
    "pref": "福岡県",
    "genre": "キッズスペース・カフェ",
    "lat": 33.550252,
    "lng": 130.397156,
    "address": "福岡県福岡市南区長住2-13-12 ハイツ上野1F",
    "visited": None,
    "with": "family",
    "kids": {
        # 県の「子育て応援の店」に**オムツ交換台・授乳スペース**の記載あり
        "stroller": None,
        "diaper": True,
        "tatami": None,
        "kidsChair": None,   # お子様メニューの記載はあるが椅子は未確認
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "全天候型のキッズスペースにコーヒースタンドを合体させた店。"
        "⭐**授乳スペースとオムツ交換台あり**・キッズスペース・おもちゃ・"
        "ミルク用のお湯・お子様メニュー・使いやすいトイレが揃っている"
        "(福岡県「子育て応援の店」登録)。ドリンクを頼むとガチャガチャのコインがもらえる。"
        "料金は時間制で 子ども45分600円/90分1,000円(2人目以降45分400円/90分700円)、"
        "大人45分400円/90分600円。営業10:00〜(平日17:00・土日18:00閉店)。"
        "駐車場は無く近隣のコインパーキング。TEL 070-2251-7374。"
        "※料金・営業時間はネット情報のため現地で要確認。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "category": "play",
    "cats": ["play", "gourmet"],
    "wish": True,
}


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    if any(s['id'] == SPOT['id'] for s in sp):
        print('既にある:', SPOT['id']); return
    sp.append(SPOT)
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('追加:', SPOT['name'])
    print('  cats =', SPOT['cats'], '(遊び場タブ・お食事タブの両方に出る)')
    print('  %.6f, %.6f' % (SPOT['lat'], SPOT['lng']))
    print('  青ピン(未訪問) / 全%d件' % len(sp))


if __name__ == '__main__':
    main()
