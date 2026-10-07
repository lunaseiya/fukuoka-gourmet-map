# -*- coding: utf-8 -*-
"""2026-10-07 ゲーム/アミューズメント施設(福岡県)の登録・更新。ユーザー事前承認済み。全て青ピン(wish=True)。

新規:
  sapura-shingu-asobitown  サープラ新宮あそびタウン(新宮ドーム内。新宮ドーム内の他スポットが無いので親子化せず単独)
  round1-kokura            ラウンドワンスタジアム 小倉店(スポッチャ設置)
更新(既存):
  spac77bd6099 アミューズメントパーク万代 トリアス久山店 … in=toriushisayama、公式店舗ページの設備・入場規制を反映
  spd33c1c75c6 アミューズメントパーク万代 宗像店         … 公式店舗ページの設備・入場規制を反映
  spdb79418865 ラウンドワンスタジアム 博多・半道橋店      … スポッチャの子供料金・入場制限を追記(ピン色は触らない)
  spa1891e0d5d ラウンドワン福岡天神店                    … 「スポッチャは半道橋店のみ」→小倉店もある、に訂正

出典:
  https://3rd-planet.jp/sp-shingu/ , /sp-shingu/detail/ , /corporate/faq/(ベビーカー入店可)
  https://iko-yo.net/facilities/177085 (対象年齢 0歳〜大人)
  https://shop.mandai-s.jp/detail/25/ , /detail/27/
  https://www.round1.co.jp/shop/area07.html (設備アイコン: スポッチャ/おむつ交換台/授乳室)
  https://www.round1.co.jp/shop/rules/fukuoka-kokura.html , fukuoka-hanmichibashi.html
  https://www.round1.co.jp/service/spo-cha/about/price.html , /aboutweb/faq.html
座標: geocoding.jp(住所で引いた)
"""
import json, shutil, os, sys, collections

P = os.path.join(os.path.dirname(__file__), '..', 'data', 'spots.json')
P = os.path.normpath(P)

AGE_RULE_FUKUOKA = '16歳未満は18時以降入場不可(保護者同伴なら22時まで)、18歳未満は22時以降入場不可'

NEW = [
    {
        "id": "sapura-shingu-asobitown",
        "name": "サープラ新宮あそびタウン",
        "area": "美咲(新宮ドーム)",
        "city": "糟屋郡新宮町",
        "pref": "福岡県",
        "genre": "ゲームセンター(クレーンゲーム)",
        "lat": 33.70618,
        "lng": 130.440628,
        "address": "福岡県糟屋郡新宮町美咲3丁目1-40",
        "visited": None,
        "with": "family",
        "kids": {"stroller": True, "diaper": None, "tatami": None,
                 "kidsChair": None, "serveMin": None, "noise": "ok"},
        "verdict": ("⭐新宮ドーム内のゲームセンター(THE 3RD PLANET)。地域最大級の「クレーンゲーム商店街」に、"
                    "10円で遊べる「拾円市場」、初心者向けの「爆獲横町」、メダルの銀座、キッズゲーム街まで揃う。"
                    "全日10:00〜23:00、無料駐車場400台。ベビーカー入店可(運営会社FAQ)。"
                    "⚠ゲームセンターなので福岡県の入場制限あり(" + AGE_RULE_FUKUOKA +
                    "。県内の万代・ラウンドワンの掲示と同じ基準。店舗の掲示は要確認)。TEL 092-410-4528。"),
        "video": {"youtube": None, "tiktok": None, "instagram": None},
        "thumb": None,
        "wish": True,
        "category": "play",
        "web": "https://3rd-planet.jp/sp-shingu/",
        "ages": ["baby", "toddler", "kids"],
        "ages_src": "auto",
    },
    {
        "id": "round1-kokura",
        "name": "ラウンドワンスタジアム 小倉店",
        "area": "西港町",
        "city": "北九州市小倉北区",
        "pref": "福岡県",
        "genre": "室内遊び場・スポッチャ",
        "lat": 33.897396,
        "lng": 130.85977,
        "address": "福岡県北九州市小倉北区西港町15-65",
        "visited": None,
        "with": "family",
        "kids": {"stroller": None, "diaper": True, "tatami": None,
                 "kidsChair": None, "serveMin": None, "noise": "ok"},
        "verdict": ("⭐スポッチャ設置店(福岡県内は小倉店と博多・半道橋店の2店のみ)。ボウリング・カラオケ・北九州最大級のアミューズメントも。"
                    "⭐スポッチャは2歳未満無料・2歳〜未就学児は未就学児料金(フリータイム1,050円〜)、小学生は学生・小学生料金。"
                    "未就学児連れの大人は「パパママ割」で子供と同額になるプランあり。キュービックキュービック(風船部屋)などキッズ向けアイテムも。"
                    "おむつ交換台・授乳室あり(公式店舗一覧)。駐車場415台(利用中無料)、小倉駅南口から無料シャトルバス。"
                    "⚠" + AGE_RULE_FUKUOKA + "(アミューズメント。小学生のみでのメダルゲームは不可)。"
                    "⚠スポッチャは改装工事で一部アイテムが使えない期間あり(2026年10月時点の告知)。営業時間は日により異なるので公式カレンダーで確認。TEL 093-562-8805。"),
        "video": {"youtube": None, "tiktok": None, "instagram": None},
        "thumb": None,
        "wish": True,
        "category": "play",
        "web": "https://www.round1.co.jp/shop/tenpo/fukuoka-kokura.html",
        "ages": ["baby", "toddler", "kids"],
        "ages_src": "auto",
    },
]

MANDAI_COMMON = ("キッズスペースあり・おむつ台設置・休憩所あり・車椅子可・駐車場完備(公式店舗ページ)。"
                 "⚠" + AGE_RULE_FUKUOKA + "(風営法・県条例による入場規制)。")

UPDATES = {
    "spac77bd6099": {
        "in": "toriushisayama",
        "address": "福岡県糟屋郡久山町山田1238-1 トリアスウエストモールD棟",
        "web": "https://shop.mandai-s.jp/detail/25/",
        "kids.diaper": True,
        "kids.noise": "ok",
        "verdict": ("⭐トリアス久山のウエストモールD棟。地域最大級320台以上のクレーンゲームに、10円から遊べるクレーンゲーム・"
                    "大型キッズスペースを完備した万代の九州1号店。" + MANDAI_COMMON +
                    "月〜日10:00〜22:00。福岡ICから車で10分。TEL 092-405-2365。"),
    },
    "spd33c1c75c6": {
        "address": "福岡県宗像市徳重2丁目4-1",
        "web": "https://shop.mandai-s.jp/detail/27/",
        "kids.diaper": True,
        "kids.noise": "ok",
        "verdict": ("⭐大型クレーンゲーム専門店(アミューズメントパーク万代の福岡2号店)。" + MANDAI_COMMON +
                    "月〜日10:00〜23:00。JR教育大前駅から徒歩20分。TEL 0940-72-8160。"),
    },
    "spdb79418865": {
        "address": "福岡県福岡市博多区半道橋2丁目2番8号",
        "kids.diaper": True,
        "verdict_append": (" ⭐スポッチャは2歳未満無料・2歳〜未就学児は未就学児料金(フリータイム1,050円〜)、未就学児連れの大人は「パパママ割」あり。"
                           "ふわふわドーム・ボールプール・ちびっこタッチ・お子様専用電動カートなどキッズ向けアイテムが多い。"
                           "おむつ交換台・授乳室あり(公式店舗一覧)。駐車場590台(利用中無料)、博多駅筑紫口から無料シャトルバス。"
                           "⚠" + AGE_RULE_FUKUOKA + "(アミューズメント。小学生のメダルゲームは保護者同伴時のみ22時まで)。"),
    },
    "spa1891e0d5d": {
        "kids.diaper": False,
        "verdict_replace": ("(スポッチャは半道橋店のみ)",
                            "(スポッチャは無し。県内のスポッチャは博多・半道橋店と小倉店)。⚠公式店舗一覧ではおむつ交換台・授乳室のアイコンなし"),
    },
}


def main():
    d = json.load(open(P, encoding='utf-8'))
    shutil.copy(P, P + '.bak_amusement_20261007')
    ids = {s['id'] for s in d}
    byid = {s['id']: s for s in d}
    names = {s['name'] for s in d}

    for n in NEW:
        if n['id'] in ids:
            sys.exit('id重複: ' + n['id'])
        if n['name'] in names:
            sys.exit('同名重複: ' + n['name'])
    if 'toriushisayama' not in ids:
        sys.exit('親 toriushisayama が無い')

    for sid, u in UPDATES.items():
        s = byid.get(sid)
        if not s:
            sys.exit('更新対象が無い: ' + sid)
        for k, v in u.items():
            if k.startswith('kids.'):
                if s.get('kids') is None:
                    s['kids'] = {"stroller": None, "diaper": None, "tatami": None,
                                 "kidsChair": None, "serveMin": None, "noise": None}
                s['kids'][k[5:]] = v
            elif k == 'verdict_append':
                if v.strip()[:20] not in (s.get('verdict') or ''):
                    s['verdict'] = (s.get('verdict') or '') + v
            elif k == 'verdict_replace':
                old, new = v
                if old in (s.get('verdict') or ''):
                    s['verdict'] = s['verdict'].replace(old, new)
                elif new not in (s.get('verdict') or ''):
                    sys.exit('置換元が見つからない: ' + sid)
            else:
                s[k] = v
        print('更新', sid, s['name'])

    for n in NEW:
        d.append(n)
        print('追加', n['id'], n['name'])

    # 整合チェック
    c = collections.Counter(s['id'] for s in d)
    dup = [k for k, v in c.items() if v > 1]
    bad = [s['id'] for s in d if s.get('wish') is True and any((s.get('video') or {}).values())]
    if dup or bad:
        sys.exit('整合NG dup=%s wish+video=%s' % (dup, bad))
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print('OK 件数', len(d))


if __name__ == '__main__':
    main()
