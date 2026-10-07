# -*- coding: utf-8 -*-
"""ブロンコビリー 福岡県内の全6店舗を青ピンで登録(2026-10-07)。ユーザー事前承認済み。ネット調査のみ → wish=True / visited=None。
   既存: spots.json に「ブロンコ」を含む店は無し(新規)。閉店扱いの店は無し(公式店舗一覧の福岡県=6店すべて掲載中)。
   根拠(すべて 2026-10-07 取得):
     共通(子連れ・公式):
     - 食べ放題ブロンコビュッフェの基本情報(2026-04-01) https://www.bronco.co.jp/feature/enjoy/20260401_bronco_buffet_kihon/
       「12歳までのお子様がご注文いただける『おこさまメニュー』は全て食べ放題ブロンコビュッフェ付き」
       「2歳以下のお子様は無料で食べ放題ブロンコビュッフェをご利用いただけます」/ ビュッフェの取り分けは禁止
     - おこさまハンバーグセット https://www.bronco.co.jp/menu/kids/okosama_hamburg/ 580円(税込638円)・12歳まで
     - 小さな子供を連れて行っても大丈夫?(2017-09-15) https://www.bronco.co.jp/feature/enjoy/20170915_okosama_sirvice/
       2才以下は注文なしでもビュッフェ・プレミアムドリンクバー・ジェラートバー無料 / お子様専用のスプーン・フォーク・取り皿 /
       お子様専用の椅子 / 12才までおもちゃプレゼント(※2017年記事。現行かは未確認なので verdict には書かない)
     - キッズクラブQ&A https://www.bronco.co.jp/kids/qa/ 0〜12歳(小6まで)・無料・アプリ登録・誕生日の前後30日にケーキ+フォトフレーム写真
     店舗(公式店舗ページ。設備アイコン「ベビーチェア」「ベビーシート」「多目的トイレ」「段差なし」等):
     - 大野城御笠川店 https://www.bronco.co.jp/shop/fukuoka/oonojoumikasagawa/
     - 古賀店 https://www.bronco.co.jp/shop/fukuoka/koga/
     - ゆめモール那珂川店 https://www.bronco.co.jp/shop/fukuoka/yumemall_nakagawa/
     - 飯塚カホテラス店 https://www.bronco.co.jp/shop/fukuoka/iizuka_kahoterras/
     - 久留米店 https://www.bronco.co.jp/shop/fukuoka/kurume/
     - 八幡青山店 https://www.bronco.co.jp/shop/fukuoka/yahataaoyama/
   kids の判断:
     kidsChair=True(公式: お子様専用の椅子 + 各店ベビーチェア)/ kidsMenu=True /
     diaper=True(各店の設備欄「ベビーシート」=おむつ交換台の一般呼称。verdict では原語「ベビーシート」で書く)/
     stroller=None(「段差なし」はあるがベビーカー可の明記なし)/ tatami=None / noise=None
     ソファ席/ボックス席: 公式に記載なし → 書かない(口コミのみ)。
   座標: geocoding.jp(住所で引いた)
     大野城 御笠川2丁目1-4 → 33.54523,130.483059 / 古賀 天神4-9-40 → 33.737004,130.465158(「4丁目9-40」表記は0が返った)
     那珂川 道善5丁目68-5 は 0/None → 「ゆめモール那珂川」(道善5丁目68-28)の代表点 33.512471,130.420143 を使用(モール内のため近似)
     飯塚 鶴三緒1151-1 → 33.627306,130.700587(既存 kahoterras と同一点 → in='kahoterras')
     久留米 野伏間1丁目7-33 → 33.285779,130.510519 / 八幡西 青山3丁目2-54 → 33.85867,130.754199
   食べログ: グループ一覧 https://tabelog.com/grouplst/G00133/fukuoka/ ほか(手で確認。monetize.py の食べログ検索は壊れているため)"""
import io, json, os, re, shutil, sys, time
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
# 他エージェントの書き込み直後でないこと(mtime 2分以上安定)を確認
assert time.time() - os.path.getmtime(P) > 120, 'spots.json が直近2分以内に更新されている'
shutil.copy(P, P + '.bak_broncobilly')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
names = {x['name'] for x in s}
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
added, skipped = [], []

COMMON = ('⭐12歳までのおこさまメニューは全て食べ放題ブロンコビュッフェ(サラダバー)付き(おこさまハンバーグセット税込638円)、'
          '⭐2歳以下は料理の注文なしでもビュッフェ・ドリンクバー・ジェラートバーが無料(公式)。'
          'お子様用スプーン・フォーク・取り皿と子供椅子あり、店舗設備にベビーチェア・ベビーシート{extra}(公式)。'
          'キッズクラブ(0〜12歳・無料・公式アプリ)で誕生日前後30日にケーキと記念写真。')
TAIL = '⚠ビュッフェの取り分けは禁止。未訪問(ネット調べ)。'

STORES = [
    dict(id='broncobilly-onojomikasagawa', name='ブロンコビリー 大野城御笠川店', area='御笠川', city='大野城市',
         address='福岡県大野城市御笠川2丁目1-4', lat=33.54523, lng=130.483059, extra='・多目的トイレ・段差なし',
         store='11:00〜23:00(土日祝10:45〜、LO22:30、ランチ〜16:00)・不定休。130席・全席禁煙・駐車場41台。TEL 092-504-4129。',
         web='https://www.bronco.co.jp/shop/fukuoka/oonojoumikasagawa/', tabelog='https://tabelog.com/fukuoka/A4003/A400301/40061910/'),
    dict(id='broncobilly-koga', name='ブロンコビリー 古賀店', area='古賀', city='古賀市',
         address='福岡県古賀市天神4丁目9-40', lat=33.737004, lng=130.465158, extra='・多目的トイレ・段差なし',
         store='11:00〜23:00(LO22:30、ランチ〜16:00)・不定休。112席・全席禁煙・駐車場512台(共有)。TEL 092-944-6083。',
         web='https://www.bronco.co.jp/shop/fukuoka/koga/', tabelog='https://tabelog.com/fukuoka/A4003/A400302/40072558/'),
    dict(id='broncobilly-yumemallnakagawa', name='ブロンコビリー ゆめモール那珂川店', area='道善', city='那珂川市',
         address='福岡県那珂川市道善5丁目68-5', lat=33.512471, lng=130.420143, extra='・多目的トイレ・段差なし',
         store='ゆめモール那珂川の敷地内。11:00〜22:00(LO21:30、ランチ〜16:00)・不定休。112席・全席禁煙・駐車場410台(共有)。TEL 092-952-0029。',
         web='https://www.bronco.co.jp/shop/fukuoka/yumemall_nakagawa/', tabelog='https://tabelog.com/fukuoka/A4003/A400301/40073015/'),
    dict(id='broncobilly-iizukakahoterras', name='ブロンコビリー 飯塚カホテラス店', area='鶴三緒', city='飯塚市',
         address='福岡県飯塚市鶴三緒1151-1', lat=33.627306, lng=130.700587, extra='・多目的トイレ・段差なし', parent='kahoterras',
         store='KAHO TERRAS内(2023年6月オープン)。11:00〜22:00(LO21:30、ランチ〜16:00)・不定休。130席・全席禁煙・駐車場400台(共有)。TEL 0948-23-4129。',
         web='https://www.bronco.co.jp/shop/fukuoka/iizuka_kahoterras/', tabelog='https://tabelog.com/fukuoka/A4007/A400702/40064680/'),
    dict(id='broncobilly-kurume', name='ブロンコビリー 久留米店', area='野伏間', city='久留米市',
         address='福岡県久留米市野伏間1丁目7-33', lat=33.285779, lng=130.510519, extra='・段差なし',
         store='11:00〜23:00(LO22:30、ランチ〜16:00)・不定休。106席・全席禁煙・駐車場80台(共有)。TEL 0942-27-0529。',
         web='https://www.bronco.co.jp/shop/fukuoka/kurume/', tabelog='https://tabelog.com/fukuoka/A4008/A400801/40064018/'),
    dict(id='broncobilly-yahataaoyama', name='ブロンコビリー 八幡青山店', area='青山', city='北九州市八幡西区',
         address='福岡県北九州市八幡西区青山3丁目2-54', lat=33.85867, lng=130.754199, extra='・多目的トイレ・段差なし',
         store='11:00〜23:00(LO22:30、ランチ〜16:00)・不定休。130席・駐車場83台(共有)。TEL 093-632-2029。',
         web='https://www.bronco.co.jp/shop/fukuoka/yahataaoyama/', tabelog='https://tabelog.com/fukuoka/A4004/A400404/40062565/'),
]

for st in STORES:
    if st['id'] in by:
        skipped.append((st['id'], 'id重複')); continue
    if st['name'] in names:
        skipped.append((st['id'], '同名重複')); continue
    x = {'id': st['id'], 'name': st['name'], 'area': st['area'], 'city': st['city'], 'pref': '福岡県',
         'genre': 'ステーキ・ハンバーグ', 'address': st['address'], 'lat': st['lat'], 'lng': st['lng'],
         'visited': None, 'with': 'family',
         'kids': {'stroller': None, 'diaper': True, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None,
                  'kidsMenu': True},
         'verdict': COMMON.format(extra=st['extra']) + st['store'] + TAIL,
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': 'gourmet',
         'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'auto',
         'web': st['web'], 'tabelog': st['tabelog']}
    if st.get('parent'):
        assert st['parent'] in by, st['parent']
        x['in'] = st['parent']
    s.append(x); by[x['id']] = x; names.add(x['name']); added.append(x['id'])

# ================= 整合チェック =================
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids)), 'id重複'
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())], 'wish=Trueに動画'
assert all(re.fullmatch(r'[A-Za-z0-9-]+', i) for i in added)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('total', len(s), 'added', len(added))
print('skipped', skipped)
print('IDS', ' '.join(added))
