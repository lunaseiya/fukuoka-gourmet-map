# -*- coding: utf-8 -*-
"""筑紫の湯(筑紫野市)を **青ピン(未訪問)** で登録する【2026-09-16ユーザー依頼】
  「筑紫野の湯、日帰り温泉、家族風呂として登録してください」
⚠正式名称は **「筑紫の湯」**(ちくしのゆ)。「筑紫野の湯」ではない。
  運営は「筑紫の郷」グループ(https://www.chikushinosato.co.jp/)。
  施設名に **「サウナと家族湯 筑紫の湯」** と付けている媒体(YUASOBI)もあるが、
  公式サイト・福岡県公式(クロスロードふくおか)はいずれも「筑紫の湯」なのでそちらを正とする。
⚠料金は**公式サイトを正**にした。集約サイトには旧料金(大人850円/小人400円)が残っている。
  公式 = 大人 平日880円・土日祝980円 / 小学生以下 平日480円・土日祝580円 / 3歳未満無料。
⚠同じ筑紫野市には既に **筑紫野 天拝の郷**(chikushinotenhainosato)が登録済み。**別施設**。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

NEW = {
    "id": "chikushinoyu",
    "name": "筑紫の湯",
    "area": "筑紫野市(筑紫・城山IC そば)",
    "city": "筑紫野市",
    "pref": "福岡県",
    "genre": "日帰り温泉・家族風呂(貸切湯6室)",
    # 住所で geocoding.jp から取得(2026-09-16)。
    # ⚠「福岡県筑紫野市筑紫973」はゼロが返るので **都道府県名を外した「筑紫野市筑紫973」** で引く
    "lat": 33.457976,
    "lng": 130.535622,
    "address": "福岡県筑紫野市筑紫973",
    "postal": "818-0025",
    "visited": None,
    "with": "family",
    # 現地で見ていない設備は null のまま(推測で埋めない)
    "kids": {
        "stroller": None,
        "diaper": None,
        "tatami": None,
        "kidsChair": None,
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "⭐**家族風呂(貸切湯)が全6室**あり、90分制で予約して使える。"
        "うち**「開運の湯」には小さな子供用の浅瀬スペースがある**ので、"
        "まだ湯船に立てない子を連れて行くならこの部屋。"
        "料金は開運の湯・サンディエゴブルー 3,900円(土日祝4,400円)、"
        "シルキーの湯・ひのきの湯 4,300円(4,800円)、"
        "ソロサウナ・キング/マックス 5,300円(5,800円)。延長は30分1,500円(土日祝2,000円)。"
        "◆大浴場は大人880円・小学生以下480円(土日祝は980円/580円)、**3歳未満は無料**。"
        "露天風呂・炭酸泉あり。男湯「地獄熱波サウナ」/女湯「美容塩サウナ」。"
        "**年中無休**で平日10:00〜翌1:00、土9:00〜、日祝7:00〜(最終受付は24:00前後)。"
        "駐車場400台。九州道 筑紫野ICから約5分、鳥栖筑紫野道路 城山ICそば。TEL 092-919-8426。"
        "⚠**家族風呂は大浴場とは別料金**で、大浴場の入浴料では入れない。"
        "⚠おむつが取れていない子の浴槽可否・ベビーベッドの有無は公式に記載が無いので要問合せ。"
    ),
    "bathAge": "記載なし(要問合せ)。3歳未満は大浴場無料。家族風呂なら人目を気にせず入れる",
    "web": "https://www.chikushinosato.co.jp/onsen.html",
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "category": "onsen",
    "dayUse": True,
    "wish": True,           # 青ピン = 未訪問(下調べで登録)
}

s = json.load(io.open(P, encoding='utf-8'))
ids = {x['id'] for x in s}
if NEW['id'] in ids:
    raise SystemExit('!! id が既にある: %s' % NEW['id'])
# 近傍の重複チェック(表記ゆれ対策)。1km以内に同種がないか見る
import math
for x in s:
    # ⚠lat/lng が None のスポットが混ざっている(住所が取れなかったもの)。先に弾く
    if x.get('lat') is None or x.get('lng') is None:
        continue
    d = math.hypot((x['lat'] - NEW['lat']) * 111,
                   (x['lng'] - NEW['lng']) * 111 * math.cos(math.radians(NEW['lat'])))
    if d < 1.0:
        print('  近傍 %.2fkm  %s (%s)' % (d, x['name'], x['id']))

shutil.copy(P, P + '.bak_chikushinoyu')
s.append(NEW)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ───────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
dup = [i for i in {x['id'] for x in s2} if sum(1 for x in s2 if x['id'] == i) > 1]
bad = [x['id'] for x in s2
       if x.get('wish') and any((x.get('video') or {}).get(k) for k in ('youtube', 'tiktok', 'instagram'))]
print('件数 %d → %d / id重複 %d件 / wish=trueなのに動画URLあり %d件'
      % (len(s), len(s2), len(dup), len(bad)))
if dup or bad:
    raise SystemExit('!! 検算NG %s %s' % (dup[:5], bad[:5]))
print('OK  %s を登録した(青ピン)' % NEW['name'])
