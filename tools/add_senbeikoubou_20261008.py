# -*- coding: utf-8 -*-
"""せんべい工房(熊本県山鹿市山鹿1799)を新規・青ピン(wish=True)登録
   きっかけ: TikTok「こなつ|福岡子連れおでかけ」の投稿(同投稿の CAFE BANANA は今回登録しない)
   座標: geocoding.jp(住所「熊本県山鹿市山鹿1799」で取得 33.011794,130.688058。
         菊池川流域日本遺産サイトの地図座標 33.01178,130.68821 とも一致)
   営業中確認: 公式Instagram @senbeikoubou の最新投稿 2026-10-07 / 食べログに閉店・移転表記なし
   裏取り:
     - 山鹿探訪なび(山鹿市観光) https://yamaga-tanbou.jp/spot/4371/ … 9:00〜16:00・火水定休・TEL
     - 食べログ https://tabelog.com/kumamoto/A4303/A430301/43014365/ … 火水定休・駐車場なし・カード/電子マネー/QR可
     - KBCアサデス。7(2025-03-12放送) … せんべい焼き体験「無料」
     - 食べログ口コミ(2025年10月訪問) … 手焼き体験200円・お店の人に焼いてもらうと100円
       → 料金は食い違うので断定せず(要確認)
     - 肥後ジャーナル(2017) … 専用釜で芯棒を回して約2秒で焼く・希望者はその場で体験
     - ゆこゆこ … 専用駐車場なし・声をかければ付近の駐車場(2か所)を利用可
   体験の所要時間・対象年齢・予約要否は公式な記載なし → 書かない / ages は付けない
   kids: 個人店で設備は確認できず全項目 null
   写真: 他人の投稿(TikTok・公式Instagram)の画像は使わない → thumb=None"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_senbeikoubou')
s = json.load(io.open(P, encoding='utf-8'))
SID = 'senbeikoubou-yamaga'
assert SID not in {x['id'] for x in s}
assert not [x for x in s if 'せんべい工房' in x['name']]

s.append({'id': SID, 'name': 'せんべい工房', 'area': '山鹿', 'city': '山鹿市', 'pref': '熊本県',
    'genre': '米せんべい・手焼き体験', 'lat': 33.011794, 'lng': 130.688058,
    'address': '熊本県山鹿市山鹿1799',
    'visited': None, 'with': 'family', 'category': 'play', 'wish': True,
    'kids': {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None,
             'serveMin': None, 'noise': None},
    'verdict': '⭐店の窯に生米をのせて約2秒で焼き上げる、米せんべいの手焼き体験ができる山鹿の手焼き米せんべい店。'
               '希望すればその場で体験できる(事前予約の記載は見当たらない)。山鹿米せんべいは全16種。'
               '⚠体験料金は情報源で差がある(KBC 2025年3月放送=無料/食べログ口コミ 2025年10月=自分で焼く200円・'
               'お店の人に焼いてもらうと100円)(要確認)。所要時間・対象年齢の記載はなし。'
               '9:00〜16:00、火・水定休(不定休とするサイトもあり)。TEL 0968-43-3158。'
               '⚠専用駐車場なし(近隣の駐車場を利用)。支払いは現金・PayPay等。',
    'web': 'https://www.instagram.com/senbeikoubou/',
    'tabelog': 'https://tabelog.com/kumamoto/A4303/A430301/43014365/',
    'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': None})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok', SID, len(s))
