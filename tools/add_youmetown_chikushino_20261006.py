# -*- coding: utf-8 -*-
"""ゆめタウン筑紫野(新規・親・赤ピン)と館内の子スポット(青ピン)を一括登録(2026-10-06)。
   ユーザー決定(2026-10-06):
     - 親 yumetownchikushino = 以前訪問したが時期不明 → wish=False / visited=None
       (aeonmallchikushino と同じ扱い)。verdict に「以前訪問(時期不明)・情報はネット調べ」
     - 子 = ネット調査のみ → wish=True / visited=None / in=yumetownchikushino
   根拠(すべて 2026-10-06 取得):
     - 公式 https://www.izumi.jp/tenpo/chikushino/ (service / shop / shop/<cat>/<id>)
       赤ちゃんの部屋(2F)設備・本館1Fフードコート無料WiFi・営業時間・各店の階/営業時間/TEL、
       「キッズサービス飲食店」欄(CoCo壱/おむらいす亭/ナマステボス)・マクドナルドの取扱商品「お子様メニュー」
     - 子育て応援の店 福岡 https://kosodate-mise.pref.fukuoka.lg.jp/shop-detail?cd=442
       ベビーカー貸し出し・ベビーカート設置・赤ちゃんの部屋のミルク用お湯
     - 福岡県 大店立地法届出 https://www.pref.fukuoka.lg.jp/contents/yumetowntikusino2.html
       駐車場合計2,360台(2016年の届出。料金の記載なし)
   座標: geocoding.jp「福岡県筑紫野市針摺東3丁目3-1」→ 33.484195,130.538305。子は親と共有(館内)。
   重複: 同名なし・400m以内に既存スポットなし(最寄りは約2.9km)。
   飲食のうち持ち帰り専門の物販(ひよ子/千鳥屋/明月堂/湖月堂/かば田/唐十/漬物の垣添/Meat up!!/
   オーガニックパパキッチン/お菓子処しょうふく)は登録しない。"""
import io, json, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_youmetown_chikushino')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
names = {x['name'] for x in s}
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
added, skipped = [], []


def kids_none():
    return {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None}


def kids_menu(chair=None):
    k = kids_none(); k['kidsChair'] = chair; k['kidsMenu'] = True; return k


PID = 'yumetownchikushino'
LAT, LNG = 33.484195, 130.538305
OFF = 'https://www.izumi.jp/tenpo/chikushino/'
if PID in by:
    skipped.append((PID, 'id重複'))
elif 'ゆめタウン筑紫野' in names:
    skipped.append((PID, '同名重複'))
else:
    p = {'id': PID, 'name': 'ゆめタウン筑紫野', 'area': None, 'city': '筑紫野市', 'pref': '福岡県',
         'genre': 'ショッピングセンター', 'lat': LAT, 'lng': LNG, 'address': '福岡県筑紫野市針摺東3丁目3-1',
         'visited': None, 'with': 'family',
         'kids': {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
         'verdict': '以前訪問(時期不明)・情報はネット調べ。本館・別館・別棟からなるイズミのSC(ニトリ・コーナン・ゼビオ・ベスト電器)。'
                    '⭐2F「赤ちゃんの部屋」(おむつ交換ベッド・調乳用給湯器・授乳室・体重計・待合スペース。授乳室エリア以外は男性も可)、'
                    '本館2Fにアカチャンホンポ。⭐ベビーカー貸し出し・ベビーカートあり(子育て応援の店 福岡)。'
                    '⭐本館2Fにナムコ(子供向けの乗り物・キッズメダル)。本館1Fフードコートは無料WiFi。'
                    '駐車場は約2,360台(料金は要確認)。食品9:00〜21:00/専門店10:00〜20:00。TEL 092-924-9000。',
         'video': dict(VIDEO0), 'thumb': None, 'wish': False, 'category': 'play',
         'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'auto', 'web': OFF}
    s.append(p); by[PID] = p; names.add(p['name']); added.append(PID)


def child(sid, name, genre, category, verdict, kids=None, ages=None, web=None):
    p = by[PID]
    if sid in by:
        skipped.append((sid, 'id重複')); return
    if name in names:
        skipped.append((sid, '同名重複: ' + name)); return
    x = {'id': sid, 'name': name, 'area': None, 'city': p['city'], 'pref': '福岡県', 'genre': genre,
         'lat': p['lat'], 'lng': p['lng'], 'visited': None, 'with': 'family', 'kids': kids, 'verdict': verdict,
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': category, 'in': PID}
    if ages:
        x['ages'] = ages; x['ages_src'] = 'auto'
    if web:
        x['web'] = web
    s.append(x); by[sid] = x; names.add(name); added.append(sid)


# ---------- 遊び・子供向け ----------
child('ytchikushino-namco', 'ナムコ ゆめタウン筑紫野店', 'ゲームセンター', 'play',
      '⭐ゆめタウン筑紫野 本館2Fのアミューズメント。子供が楽しめる乗り物・キッズ用メダルゲーム・カードゲーム、'
      'クレーンゲーム、ガシャポン400面以上(公式店舗ページ)。10:00〜20:00。TEL 092-408-1432。⚠ゲームは有料。',
      kids={'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
      ages=['toddler', 'kids'], web=OFF + 'shop/service/namco')
child('ytchikushino-akachanhonpo', 'アカチャンホンポ ゆめタウン筑紫野店', 'ベビー用品', 'play',
      'ゆめタウン筑紫野 本館2Fのマタニティ・ベビー・キッズ用品店。10:00〜20:00。TEL 092-925-8511。'
      'おむつ替え・授乳は同じ2Fの「赤ちゃんの部屋」で。',
      ages=['baby'], web='https://stores.akachan.jp/232')

# ---------- 飲食(本館1F・別棟) ----------
NOTE = '⚠未訪問。キッズチェア等は要確認。'
SHOP = OFF + 'shop/food/'
# (id, 店名, genre, 場所, 営業時間, TEL, kids, 補足, 公式slug)
FOOD = [
    ('ytchikushino-namasteboss', 'ナマステ ボス ゆめタウン筑紫野店', 'インド料理', '本館1Fフードコート', '11:00〜20:00(OS19:30)', '092-928-7525',
     kids_menu(), '⭐「お子様セット」550円(税込)あり。カレーは中辛〜甘口寄りのマイルド(公式店舗ページ)。', 'namasteboss'),
    ('ytchikushino-okonomi1banchi', 'OKONOMI ICHIBANCHI ゆめタウン筑紫野店', 'お好み焼き', '本館1F', '10:00〜21:00', '092-924-9102',
     None, '広島お好み焼き・たこ焼き。持ち帰り可。', 'okonomi1banchi'),
    ('ytchikushino-komeda', 'コメダ珈琲店 ゆめタウン筑紫野店', 'カフェ', '別棟', '7:00〜20:00(OS19:30)', '092-923-7211',
     None, '100席。11:00までモーニングサービス。', 'komedacoffee'),
    ('ytchikushino-graindor', 'グレンドール ゆめタウン筑紫野店', 'パン', '本館1F', '9:00〜21:00', '092-919-6626',
     None, 'ベーカリー。', 'graindor'),
    ('ytchikushino-torimotto', 'とりモット ゆめタウン筑紫野店', '鶏料理', '本館1F', None, None,
     None, '熊本発の鶏と玉子の料理の店。営業時間は要確認。', 'torimotto'),
    ('ytchikushino-baskinrobbins', 'サーティワンアイスクリーム ゆめタウン筑紫野店', 'アイスクリーム', '本館1F', '10:00〜21:00', '050-1720-0413',
     None, '', '31ice'),
    ('ytchikushino-pizzahut', 'ピザハット ゆめタウン筑紫野店', 'ピザ', '本館1F(飲食街入口)', '11:00〜22:00(21時以降は宅配のみ)', '092-710-3573',
     None, '', 'pizzahut'),
    ('ytchikushino-misterdonut', 'ミスタードーナツ ゆめタウン筑紫野ショップ', 'ドーナツ', '本館1F', '10:00〜21:00', '092-920-1470',
     None, '', 'misterdonuts'),
    ('ytchikushino-mcdonalds', 'マクドナルド ゆめタウン筑紫野店', 'ハンバーガー', '本館1F', '9:30〜21:00', '092-920-1503',
     kids_menu(), '⭐公式店舗ページの取扱商品に「お子様メニュー」。', 'mcdonalds'),
    ('ytchikushino-sanmi', '元祖トマトラーメン三味 ゆめタウン筑紫野店', 'ラーメン', '本館1F', None, '092-403-4333',
     None, 'トマトと香味野菜のスープのラーメン。〆のチーズリゾットが名物。営業時間は要確認。', 'sanmi'),
    ('ytchikushino-osakaohsho', '大阪王将 ゆめタウン筑紫野店', '中華', '本館1F', '11:00〜21:00(OS20:30)', '092-919-5100',
     None, '餃子。持ち帰り可。', 'osakaohsho'),
    ('ytchikushino-hanamaru', 'はなまるうどん ゆめタウン筑紫野店', 'うどん', '本館1F', '10:30〜21:00(OS20:00)', '092-918-0870',
     None, 'セルフ式の讃岐うどん。', 'hanamaruudon'),
    ('ytchikushino-shouya', '庄屋 ゆめタウン筑紫野店', '和食', '本館1F', '11:00〜21:00', '050-8883-6328',
     None, '長崎発の和食レストラン。', 'shouya'),
    ('ytchikushino-takamotoya', '黒酢チキン南蛮定食たかもとや ゆめタウン筑紫野店', '定食', '別棟', '11:00〜21:00(2024年の店舗告知・要確認)', '092-924-2522',
     None, '黒酢チキン南蛮の定食。', 'takamotoya'),
    ('ytchikushino-cocoichi', 'CoCo壱番屋 ゆめタウン筑紫野店', 'カレー', '別棟', '11:00〜22:00', '092-928-7987',
     kids_menu(chair=True),
     '⭐公式店舗ページの「キッズサービス飲食店」欄にキッズチェア(ベルトあり・なし)・取り分け皿・キッズ用スプーンフォーク・'
     '離乳食持ち込みOK・キッズメニュー・アレルギー対応表。', 'cocoichibanya'),
    ('ytchikushino-omuraisutei', 'おむらいす亭 ゆめタウン筑紫野店', 'オムライス', '本館1F', '11:00〜20:00', '092-918-6132',
     kids_menu(),
     '⭐公式店舗ページの「キッズサービス飲食店」欄に取り分け皿・キッズ用スプーンフォーク・キッズメニュー・アレルギー対応表。', 'omuricetei'),
    ('ytchikushino-taiyaki', 'お伊勢たい焼き縁屋/太宰府の門前焼 穂彩堂 ゆめタウン筑紫野店', 'たい焼き', '本館1F', None, None,
     None, '餅入りの薄皮たい焼きと「太宰府の門前焼」。営業時間は要確認。', 'yukariya_suisaido'),
]
assert len(FOOD) == 17, len(FOOD)
for sid, nm, g, loc, hrs, tel, kids, extra, slug in FOOD:
    v = 'ゆめタウン筑紫野 %s。' % loc + extra + ((hrs + '。') if hrs else '') + (('TEL %s。' % tel) if tel else '')
    if not (kids and kids.get('kidsChair')):
        v += NOTE
    else:
        v += '⚠未訪問。'
    child(sid, nm, g, 'gourmet', v, kids=kids, web=SHOP + slug)

# ================= 整合チェック =================
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids)), 'id重複'
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())], 'wish=Trueに動画'
assert all(re.fullmatch(r'[A-Za-z0-9-]+', i) for i in added)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
cnt = {}
for i in added:
    k = by[i].get('in') or '(親)'; cnt[k] = cnt.get(k, 0) + 1
print('total', len(s), 'added', len(added), cnt)
print('skipped', skipped)
print('IDS', ' '.join(added))
