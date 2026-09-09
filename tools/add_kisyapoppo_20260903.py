# -*- coding: utf-8 -*-
"""「汽車ポッポ食堂と民宿・別邸」(大分県中津市)を宿として登録する(2026-09-03)。

旧耶馬渓鉄道(1975年廃線)の車両を保存・活用した施設。**別邸は1棟1車両を貸し切る完全個室**で、
昭和10〜31年製の気動車3両がそのまま客室になっている。未訪問なので青ピン。

住所は情報源が割れた。じゃらんのページからは「中津市三光大字田口1」と読めたが、
**公式サイトと楽天トラベルはどちらも「中津市大字万田500番地の1」**だったので後者を採る。
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

SPOT = {
    "id": "kisyapoppo_bettei",
    "name": "汽車ポッポ 別邸(汽車ポッポ食堂と民宿)",
    "area": "中津",
    "city": "中津市",
    "pref": "大分県",
    "genre": "ホテル・民宿(鉄道車両)",
    "lat": 33.579329,
    "lng": 131.186064,
    "address": "大分県中津市大字万田500番地の1",
    "visited": None,
    "with": "family",
    "kids": {
        # 予約サイトの人数選択に「小学生高学年/小学生低学年/幼児」の区分はあるが、
        # 添い寝の可否や子供料金の額は確認できなかったので埋めない
        "stroller": None,
        "diaper": None,
        "tatami": None,
        "kidsChair": None,
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "⭐**1975年に廃線になった旧耶馬渓鉄道の車両に、そのまま泊まれる宿**。"
        "「別邸」は**1棟1車両を貸し切る完全個室**で、3両ある。"
        "青の社(キハ102かわせみ・昭和10年製/4名/82㎡)、"
        "国東の社(キハ602しおかぜ・昭和31年製/6名/111㎡・ソファーベッド2台込み)、"
        "耶馬渓の社(キハ104せきれい・昭和12年製/4名/89㎡)。"
        "全室にバスルーム・洗面室・ウォシュレット付トイレ・冷蔵庫・エアコン・Free WiFiがある。"
        "食事は食堂本館(旧耶馬渓鉄道の車両を使った食堂)で。"
        "併設の民宿には90畳の大広間があり合宿にも使われる。"
        "チェックイン15:00〜22:00 / アウト10:00。**駐車場50台・無料**。TEL 0979-22-0275。"
        "※予約サイトの館内設備欄には大浴場の記載があるが、公式では確認できなかった(要確認)。"
        "※子供料金・添い寝の可否は未確認。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "category": "onsen",
    "stay": True,
    "dayUse": False,      # 宿泊施設。日帰り入浴の受け入れは確認できていない
    "web": "https://kisyapoppo.com/bettei/",
    "booking": "https://www.jalan.net/yad327972/",
    "wish": True,
}


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    if any(s['id'] == SPOT['id'] for s in sp):
        print('既にある:', SPOT['id']); return
    if any(s['name'] == SPOT['name'] for s in sp):
        print('同名がある:', SPOT['name']); return
    sp.append(SPOT)
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('追加:', SPOT['name'])
    print('  %s' % SPOT['address'])
    print('  %.6f, %.6f / 宿・温泉タブ / 青ピン(未訪問) / 全%d件' % (SPOT['lat'], SPOT['lng'], len(sp)))


if __name__ == '__main__':
    main()
