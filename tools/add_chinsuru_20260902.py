# -*- coding: utf-8 -*-
"""「チン!するレストラン in FUKUOKA」を期間限定スポットとして登録する(2026-09-02)。

冷凍食品の食べ放題イベント。**遊び場としても食事としても**扱う(ユーザー指示)ので
cats:["play","gourmet"] で2タブに載せる。

期間は spot 直下の from / until に入れる。今日(9/2)時点ではまだ始まっていないので、
map/index.html の判定で「📅 これから開催 … あと2日で開幕」と表示される。
"""
import os, json, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

SPOT = {
    "id": "chinsuru_restaurant_fukuoka",
    "name": "チン!するレストラン in FUKUOKA",
    "area": "アイランドシティ(香椎照葉)",
    "city": "福岡市東区",
    "pref": "福岡県",
    "genre": "冷凍食品食べ放題(期間限定イベント)",
    "lat": 33.665799,
    "lng": 130.415134,
    "address": "福岡県福岡市東区香椎照葉6丁目6番6号 福岡アイランドシティフォーラム",
    "visited": None,
    "with": "family",
    "kids": {
        # 会場は公共のホール。設備はネットで確認できなかったので埋めない
        "stroller": None,
        "diaper": None,
        "tatami": False,
        "kidsChair": None,
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "日本アクセス主催の冷凍食品食べ放題イベントで**九州初上陸**。"
        "冷凍食品約150種+アイス約50種の計約200種を、自分で電子レンジで温めて食べる。"
        "⭐**料金は90分2,500円(税込)で、小学生は半額・小学生未満は無料**(飲料は別料金)。"
        "11:00〜20:30(最終入店19:00)の**90分入れ替え制・事前予約制**で、"
        "枠は11:00 / 13:00 / 15:00 / 17:00 / 19:00 の5つ。"
        "⚠**子供向けに作られたイベントではない**点に注意。"
        "レンジで温める工程を自分でやる形式なので小さい子には忙しく、90分の入れ替え制でもある。"
        "未就学児が無料なのと、アイス50種があるのは子連れに効く。"
        "会場のおむつ替え・授乳室は未確認。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "category": "play",
    "cats": ["play", "gourmet"],
    "from": "2026-09-04",
    "fromLabel": "9月4日",
    "until": "2026-09-23",
    "untilLabel": "9月23日",
    "wish": True,
}


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    if any(s['id'] == SPOT['id'] for s in sp):
        print('既にある:', SPOT['id']); return
    sp.append(SPOT)
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('追加:', SPOT['name'])
    print('  cats =', SPOT['cats'], '(遊び場タブ・お食事タブの両方)')
    print('  期間 %s 〜 %s' % (SPOT['from'], SPOT['until']))
    print('  %.6f, %.6f / 青ピン(未訪問) / 全%d件' % (SPOT['lat'], SPOT['lng'], len(sp)))


if __name__ == '__main__':
    main()
