# -*- coding: utf-8 -*-
"""アソビクル 福岡新宮店 を赤ピンで登録(2026-10-09)

- ユーザー実訪問(写真4枚・EXIFなし → visited=None)
- 店頭に「写真・動画撮影/SNSでのLIVE配信はお断り(要事前相談)」の掲示 → 現地写真は載せない。
  代わりに `python tools/make_icon_cards.py asobikuru-shingu` でアイコン案内カードを photos/thumb に入れる
- 住所・電話: 運営会社(マインズ)公式 https://mines-group.co.jp/am_store/hukuoka/
- 座標: geocoding.jp「福岡県糟屋郡新宮町三代999-1」(ロピア福岡新宮店と同番地・旧コーナン跡)
- ロピア/同じ敷地の商業施設は spots.json に未登録なので in 紐付けなし
"""
import json, os, shutil

P = os.path.join(os.path.dirname(__file__), '..', 'data', 'spots.json')
P = os.path.normpath(P)

SPOT = {
    "id": "asobikuru-shingu",
    "name": "アソビクル 福岡新宮店",
    "area": "三代",
    "city": "糟屋郡新宮町",
    "pref": "福岡県",
    "genre": "ゲームセンター",
    "lat": 33.703114,
    "lng": 130.45601,
    "address": "福岡県糟屋郡新宮町三代999-1",
    "visited": None,
    "with": "family",
    "kids": {"stroller": None, "diaper": None, "tatami": None,
             "kidsChair": None, "serveMin": None, "noise": "ok"},
    # 改行は表示されない(.card-verdict は white-space 指定なし)ので、⭐/⚠ + **見出し** で区切って箇条風にする
    "verdict": (
        "ロピア福岡新宮店の隣のゲームセンター。クレーンゲーム・音ゲー・ドライブゲーム・メダルゲーム。"
        " ⭐**キッズエリア「アソビクルひろば」**: 無料遊具コーナー(運営会社公式)。中はエアー遊具のジャングル風すべり台と"
        "ままごとハウス。小学生までとその保護者のみ入場・10:00〜19:45・靴を脱いで入る・保護者が必ず付き添い・"
        "飲食禁止・アクセサリー類は外す。"
        " ⚠**ひろば内にトイレなし**: 建物中央のトイレを利用。"
        " ⭐**無料ガラポン**: 小学6年生までは毎日1回(お菓子・クレーンゲーム無料券・増量券など)。"
        "誕生月のガラポンもあり(公的証明書が必要)。"
        " ⭐**10円から遊べるクレーンゲーム**: 1プレイ10円・20円・30円・40円の台あり。子供用の踏み台あり。"
        " ⚠**入店時間**: 中学生以下は18:00まで、保護者同伴なら20:00まで(条例)。"
        " ⚠**営業**: 10:00〜20:00(店頭掲示。公式サイトは20:30表記で要確認)・年中無休、メダルは閉店15分前まで。"
        "店内の飲食・飲酒はお断り。"
        " ⚠**店内撮影NG**: 写真・動画撮影やSNSのライブ配信はお断り(要事前相談)。"
        " TEL 092-410-6997。(2026-10 店内掲示・実訪問)"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": None,
    "wish": False,
    "category": "play",
    "ages": ["baby", "toddler", "kids"],
    "ages_src": "manual",
    "web": "https://mines-group.co.jp/am_store/hukuoka/",
    "added": "2026-10-09",
}


def main():
    bak = P + '.bak_asobikuru_shingu_20261009'
    if not os.path.exists(bak):          # 再実行しても最初の(登録前の)バックアップを潰さない
        shutil.copy(P, bak)
    with open(P, encoding='utf-8') as f:
        data = json.load(f)
    if any('アソビクル' in (s.get('name') or '') and s.get('id') != SPOT['id'] for s in data):
        raise SystemExit('same-name spot exists')
    old = next((s for s in data if s.get('id') == SPOT['id']), None)
    if old:                              # 再実行時は差し替え(make_icon_cards.py が入れた photos/thumb は残す)
        for k in ('photos', 'thumb'):
            if old.get(k):
                SPOT[k] = old[k]
        if '館内の写真は掲載せず' in (old.get('verdict') or ''):
            SPOT['verdict'] += ' ※施設の方針(館内撮影お断り)により、館内の写真は掲載せずアイコンで案内しています。'
        data[data.index(old)] = SPOT
    else:
        data.append(SPOT)
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)   # 元ファイルに合わせ末尾改行なし
    # 整合チェック
    ids = [s['id'] for s in data]
    dup = {i for i in ids if ids.count(i) > 1}
    bad = [s['id'] for s in data if s.get('wish') is True and any((s.get('video') or {}).values())]
    print('total', len(data), 'dup', dup or 0, 'wish+video', bad or 0)


if __name__ == '__main__':
    main()
