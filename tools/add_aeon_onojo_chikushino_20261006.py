# -*- coding: utf-8 -*-
"""イオン大野城SC(新規・親)とイオンモール筑紫野(既存親を更新)の子スポットを一括登録(2026-10-06)。
   調査メモ: data/候補_イオン大野城筑紫野_20261006.md / ユーザー決定(2026-10-06):
     1. aeononojo = 新規親・青ピン。子=モーリーファンタジー+飲食8店(kidsはnull・根拠なし)
     2. aeonmallchikushino = 訪問済みなので赤ピンのまま(visitedは不明なので触らない)。館内設備で更新。
        子=キッズパーク/モーリーファンタジー/トイザらス/ポポンデッタ+飲食35店(公式店舗ページの
        isKidsMenu=true → kids.kidsMenu=True、それ以外は kids=null)。猫カフェモカは公式ルールで verdict 更新
        閉店済みのファンタジーキッズリゾート筑紫野・キッズーナは登録しない
   飲食35店の階・区画・営業時間・TEL・席数・キッズメニュー可否は chikushino.aeonmall.jp/gourmet/<id> の
   埋め込みデータ(2026-10-06取得)から。子の座標は親と共有(館内)。
   大野城の親座標は geocoding.jp「福岡県大野城市錦町4丁目1-1」→ 33.53792,130.47558(2026-10-06)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_aeon_onojo_chikushino')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
names = {x['name'] for x in s}
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
added, skipped, changed = [], [], []


def kids_none():
    return {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None}


def kids_menu():
    k = kids_none(); k['kidsMenu'] = True; return k


def child(parent, sid, name, genre, category, verdict, kids=None, ages=None, web=None):
    p = by[parent]
    if sid in by:
        skipped.append((sid, 'id重複')); return
    if name in names:
        skipped.append((sid, '同名重複: ' + name)); return
    x = {'id': sid, 'name': name, 'area': None, 'city': p['city'], 'pref': '福岡県', 'genre': genre,
         'lat': p['lat'], 'lng': p['lng'], 'visited': None, 'with': 'family', 'kids': kids, 'verdict': verdict,
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': category, 'in': parent}
    if ages:
        x['ages'] = ages; x['ages_src'] = 'auto'
    if web:
        x['web'] = web
    s.append(x); by[sid] = x; names.add(name); added.append(sid)


# ================= 1. イオン大野城ショッピングセンター(新規親) =================
ON = 'aeononojo'
if ON not in by:
    o = {'id': ON, 'name': 'イオン大野城ショッピングセンター', 'area': None, 'city': '大野城市', 'pref': '福岡県',
         'genre': 'ショッピングセンター', 'lat': 33.53792, 'lng': 130.47558, 'address': '福岡県大野城市錦町4丁目1-1',
         'visited': None, 'with': 'family',
         'kids': {'stroller': None, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
         'verdict': '4層のイオン九州のSC(4Fイオンシネマ)。⭐3Fベビー用品売場の奥に赤ちゃん休憩室(授乳室2室・おむつ台4台・口コミ情報)、'
                    '1〜3Fのトイレ横に授乳スペース。⭐3Fにモーリーファンタジー。⭐駐車場は入庫3時間無料(以降60分300円・当日最大600円、'
                    '6:00〜24:30。映画館利用で+2時間)。⚠独立したフードコートは無く、飲食は1Fの専門店。9:00〜22:00。TEL 092-572-2100。',
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': 'play',
         'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'auto',
         'web': 'https://tenpo.aeon-kyushu.info/detail/onojo/'}
    s.append(o); by[ON] = o; names.add(o['name']); added.append(ON)
else:
    skipped.append((ON, 'id重複'))

TK = 'https://tenpo.aeon-kyushu.info/detail/onojo/'
ON_NOTE = '⚠未訪問。キッズチェア等の子連れ設備は未確認。おむつ替えは館内の赤ちゃん休憩室(3F)・授乳スペース(1〜3F)で。'
child(ON, 'onojo-mollyfantasy', 'モーリーファンタジー イオン大野城店', '室内遊び場', 'play',
      'イオン大野城SC 3Fの店内ゆうえんち。9:00〜21:00。TEL 070-3100-5334。公式店舗ページは「よくばりパス」のみ記載。'
      '⚠有料キッズスペース「わいわいぱーく」の有無は情報が割れている(要確認)。料金は2025-11-25に全店改定済み・店舗で異なる(要確認)。',
      web='https://www.fantasy.co.jp/molly-fantasy/shoplist/shop3712/')
for sid, nm, g, v in [
    ('onojo-saizeriya', 'サイゼリヤ イオン大野城店', 'イタリアン', '1F。11:00〜22:00。TEL 092-588-6330。'),
    ('onojo-omuraisutei', 'おむらいす亭 イオン大野城店', 'オムライス', '1F。11:00〜22:00(OS21:30)。'),
    ('onojo-yayoiken', 'やよい軒 イオン大野城店', '定食', '1F。10:00〜22:00(LO21:30)。TEL 092-588-7178。'),
    ('onojo-suraj', 'インドレストラン SURAJ イオン大野城店', 'インド料理', '1F。11:00〜22:00(LO21:30)。'),
    ('onojo-nokoudon', '能古うどん イオン大野城店', 'うどん', '1F。10:00〜22:00(LO21:00)。TEL 092-574-2232。'),
    ('onojo-mcdonalds', 'マクドナルド イオン大野城店', 'ハンバーガー', '1F。9:00〜22:00。TEL 092-513-5301。'),
    ('onojo-misterdonut', 'ミスタードーナツ イオン大野城ショップ', 'ドーナツ', '1F。9:00〜22:00。TEL 092-513-5677。'),
    ('onojo-baskinrobbins', 'サーティワンアイスクリーム イオン大野城店', 'アイスクリーム', '1F。9:00〜21:30。'),
]:
    child(ON, sid, nm, g, 'gourmet', 'イオン大野城SCの1F「グルメ&フード」区画。' + v.replace('1F。', '') + ON_NOTE)

# ================= 2. イオンモール筑紫野(既存親を更新・赤ピンのまま) =================
CH = 'aeonmallchikushino'
c = by[CH]
before = json.dumps(c, ensure_ascii=False, sort_keys=True)
c.update(address='福岡県筑紫野市立明寺434番地1',
         kids={'stroller': None, 'diaper': True, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None},
         ages=['baby', 'toddler', 'kids'], ages_src='auto', web='https://chikushino.aeonmall.jp/',
         verdict='専門店約210店の3層モール(蔦屋書店・イオンシネマ・トイザらス)。⭐赤ちゃんルームが1F(ウエストコート南入口近く)・'
                 '2F(クイックカラーQ近く)・3F(セイハ英語学院近く)の3か所(調乳用温水器・おむつ替えシート・授乳室)、'
                 'こどもトイレ(子供サイズのトイレ+おむつ替えシート)も1〜3Fのセントラルコートに。'
                 '⭐3Fフードコート「フードフォレスト」(1,100席)の近くに子供用テーブル・イスの「キッズダイニング」(アニメイト近く)、'
                 '3〜6歳の「キッズパーク」(だがし夢や近く・無料)。⭐キャラクターのキッズカート「キャラクルカート」(1Fウエストコート南入口・'
                 'イーストコート入口・数量限定)。ベビーカー貸出あり(口コミ情報・要確認)。駐車場約3,800台(料金は無料とされるが要確認)。'
                 '専門店10:00〜21:00/レストラン11:00〜22:00/フードコート10:00〜21:00/イオン9:00〜22:00。TEL 092-929-2300。')
assert c.get('wish') is False  # 訪問済み=赤ピンのまま
if json.dumps(c, ensure_ascii=False, sort_keys=True) != before:
    changed.append(CH)

nk = by.get('nekocafemocha_chikushino')
if nk:
    nk['verdict'] = ('⭐猫とふれあえるカフェ。イオンモール筑紫野2F[265]。10:00〜21:00(最終入店20:30)。TEL 092-710-1236。'
                     '⭐3歳以下は無料で入場できる。⚠小学生以下は保護者同伴が必要(公式店舗ページ)。猫を驚かせない配慮を。')
    changed.append(nk['id'])

GURL = 'https://chikushino.aeonmall.jp/gourmet/'
child(CH, 'chikushino-kidspark', 'キッズパーク(イオンモール筑紫野)', 'キッズスペース', 'play',
      '⭐イオンモール筑紫野3F(だがし夢や近く)の無料キッズスペース。対象3〜6歳(対象外の年齢の子の利用は控える)。'
      '⚠遊んでいる間は保護者が目を離さず付き添う。(公式「設備・サービス」)',
      kids={'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
      ages=['toddler'], web='https://chikushino.aeonmall.jp/guide/equipment')
child(CH, 'chikushino-mollyfantasy', 'モーリーファンタジー イオンモール筑紫野店', '室内遊び場', 'play',
      'イオンモール筑紫野3F[301]の店内ゆうえんち。9:00〜21:00。TEL 070-3100-4092。'
      '⭐有料プレイグラウンド「のびっこ」(0〜3歳向け・0歳と付き添いの大人は無料)があるとの情報(口コミ・要確認)。'
      '⚠料金は2025-11に全店改定済み・店舗で異なる(要確認)。',
      web='https://www.fantasy.co.jp/molly-fantasy/shoplist/shop3714/')
child(CH, 'chikushino-toysrus', 'トイザらス イオンモール筑紫野店', 'おもちゃ', 'play',
      'イオンモール筑紫野3F[314]のおもちゃ専門店(2026-06-05リニューアルオープン)。子供用自転車も扱う。10:00〜21:00。TEL 092-233-6898。')
child(CH, 'chikushino-popondetta', '電車のお店 ポポンデッタ イオンモール筑紫野店', '鉄道模型', 'play',
      '⭐イオンモール筑紫野3F[364]の電車グッズ・鉄道模型の店(2026-06-17オープン)。店内の巨大ジオラマで鉄道模型の体験運転ができる(有料)。'
      '10:00〜21:00。TEL 092-403-5713。')

FC = 'イオンモール筑紫野3Fフードコート「フードフォレスト」(1,100席)の[%s]区画。'
RS = 'イオンモール筑紫野1Fグルメストリートの[%s]区画。'
CF = 'イオンモール筑紫野%sの[%s]区画。'
KM = '⭐公式店舗ページで「キッズメニューあり」。'
FCK = '同じ3Fに子供用テーブル・イスの「キッズダイニング」(アニメイト近く)。'
NOTE = '⚠未訪問。キッズチェア等は要確認。'
# (id, 店名, genre, 区分テンプレ, 区画/階, 席数, 営業時間, TEL, kidsMenu, 補足)
FOOD = [
    # --- 3F フードフォレスト(13店) ---
    ('chikushino-fc-mcdonalds', 'マクドナルド イオンモール筑紫野店', 'ハンバーガー', FC, '354', None, '10:00〜21:00(LO20:45)', '092-929-6375', True, ''),
    ('chikushino-fc-kfc', 'ケンタッキーフライドチキン イオンモール筑紫野店', 'フライドチキン', FC, '349', None, '10:00〜21:00(LO20:30)', '092-918-3108', True, ''),
    ('chikushino-fc-kairikiya', '魁力屋 イオンモール筑紫野店', 'ラーメン', FC, '345', None, '10:00〜21:00', '092-403-4500', True, ''),
    ('chikushino-fc-marugame', '丸亀製麺 イオンモール筑紫野店', 'うどん', FC, '346', None, '10:00〜21:00(LO20:30)', '092-929-6280', None, ''),
    ('chikushino-fc-ringerhut', '長崎ちゃんぽん リンガーハット イオンモール筑紫野店', 'ちゃんぽん', FC, '347', None, '10:00〜21:00(LO20:30)', '092-918-3325', None, ''),
    ('chikushino-fc-pepperlunch', 'ペッパーランチ イオンモール筑紫野店', 'ステーキ', FC, '348', None, '10:00〜21:00(LO20:30)', '092-408-1030', None, ''),
    ('chikushino-fc-bibintei', 'ビビン亭 イオンモール筑紫野店', '韓国料理', FC, '343', None, '10:00〜21:00(LO20:30)', '092-918-3215', None, '石焼ビビンバ・冷麺・韓国定食。'),
    ('chikushino-fc-gindaco', '築地銀だこ イオンモール筑紫野店', 'たこ焼き', FC, '344', None, '10:00〜21:00(LO20:30)', '092-918-3318', None, ''),
    ('chikushino-fc-misterdonut', 'ミスタードーナツ イオンモール筑紫野ショップ', 'ドーナツ', FC, '353', None, '10:00〜21:00(LO20:30)', '092-929-6366', None, ''),
    ('chikushino-fc-baskinrobbins', 'サーティワンアイスクリーム イオンモール筑紫野店', 'アイスクリーム', FC, '342', None, '10:00〜21:00', '092-555-4631', None, ''),
    ('chikushino-fc-dipperdan', 'ディッパーダン イオンモール筑紫野店', 'クレープ', FC, '351', None, '10:00〜21:00(LO クレープ20:30)', '092-555-9896', None, ''),
    ('chikushino-fc-torimaru-tanita', '鳥〇食堂×タニタカフェ イオンモール筑紫野店', '定食', FC, '352', None, '10:00〜21:00(LO20:30)', '092-403-1150', None, '2026-04-16オープン。'),
    ('chikushino-fc-ringodou', '林檎堂 イオンモール筑紫野店', 'りんご飴', FC, '350', None, '10:00〜21:00', '080-4695-5578', None, 'りんご飴専門店。'),
    # --- 1F グルメストリート(15店) ---
    ('chikushino-burgerking', 'バーガーキング イオンモール筑紫野店', 'ハンバーガー', RS, '159', '56席', '10:00〜22:00(LO21:00)', '092-403-1083', True, ''),
    ('chikushino-rs-pietro', 'ピエトロ イオンモール筑紫野店', 'パスタ', RS, '165', '90席', '11:00〜22:00(LO21:00)', '092-918-3138', True, ''),
    ('chikushino-rs-umaya', 'うまや イオンモール筑紫野店', '牛たん', RS, '153', '60席', '11:00〜22:00(LO21:00)', '092-401-1245', True, '牛タン炭火焼と麦ご飯・とろろ。'),
    ('chikushino-rs-hamakatsu', 'とんかつ濱かつ イオンモール筑紫野店', 'とんかつ', RS, '163', '66席', '11:00〜22:00(LO21:00)', '092-918-3135', True, ''),
    ('chikushino-rs-benitora', '紅虎餃子房 イオンモール筑紫野店', '中華', RS, '161', '70席', '11:00〜22:00(LO21:15)', '092-401-1241', True, ''),
    ('chikushino-rs-hyakusai', '定食屋百菜 イオンモール筑紫野店', '定食', RS, '162', None, '11:00〜22:00(LO21:15)', '092-408-3998', True, ''),
    ('chikushino-rs-tenjinhorumon', '鉄板焼 天神ホルモン plus GOCHISOU イオンモール筑紫野店', '鉄板焼', RS, '156', '37席', '11:00〜22:00(LO21:00)', '092-408-2956', True, ''),
    ('chikushino-rs-konpeitei', 'こんぺい亭 イオンモール筑紫野店', 'チキン南蛮', RS, '152', None, '11:00〜22:00(LO21:15)', '092-710-3425', True, '宮崎・延岡発祥のチキン南蛮の店。'),
    ('chikushino-rs-aburihyakkan', 'ABURI百貫 イオンモール筑紫野店', '寿司', RS, '160', '84席', '11:00〜22:00(LO21:00)', '092-408-5353', True, ''),
    ('chikushino-rs-ryujinmaru', '龍神丸 イオンモール筑紫野店', '定食', RS, '151', None, '11:00〜22:00(LO21:00)', '092-555-9854', None, '一人一釜の炊き立てご飯とかつおのタタキの定食。'),
    ('chikushino-rs-inabaudon', '因幡うどん イオンモール筑紫野店', 'うどん', RS, '154', None, '11:00〜22:00(LO21:00)', '092-555-3883', None, '博多うどんの老舗。'),
    ('chikushino-rs-granbuffet', 'グランブッフェ イオンモール筑紫野店', 'ビュッフェ', RS, '155', '104席', '11:00〜22:00(ディナーLO21:30)', '092-918-2118', None, '和洋中約65種類のブッフェ。'),
    ('chikushino-rs-miyama', '美山 イオンモール筑紫野店', 'しゃぶしゃぶ', RS, '157', None, '11:00〜22:00(入店21:00まで)', '092-710-3395', None, '一人一鍋のしゃぶしゃぶ・すきやき食べ放題。'),
    ('chikushino-rs-tempuranakamura', '天ぷら那かむら イオンモール筑紫野店', '天ぷら', RS, '158', None, '11:00〜22:00(LO21:15)', '092-408-7588', None, ''),
    ('chikushino-rs-piasapido', 'ピアサピド イオンモール筑紫野店', 'イタリアン', RS, '164', None, '11:00〜22:00(LO21:00)', '092-408-2984', None, '自家製パン食べ放題のベーカリーレストラン。'),
    # --- カフェ・スイーツ(7店) ---
    ('chikushino-starbucks', 'スターバックス コーヒー イオンモール筑紫野店', 'カフェ', CF, ('1F', '113'), None, '10:00〜21:00', '092-918-3388', True, ''),
    ('chikushino-tullys', 'タリーズコーヒー イオンモール筑紫野店', 'カフェ', CF, ('2F', '221'), '60席', '10:00〜21:00', '092-918-3145', True, ''),
    ('chikushino-hoshino', '星乃珈琲店 イオンモール筑紫野店', 'カフェ', CF, ('2F', '269'), '68席', '10:00〜21:00(LO20:15)', '092-408-1500', True, ''),
    ('chikushino-elkpancake', 'elk pancake&cafe イオンモール筑紫野店', 'パンケーキ', CF, ('3F', '318'), None, '10:00〜21:00', None, None, '大阪発のパンケーキ専門店(新店)。'),
    ('chikushino-karin', '果汁工房果琳 イオンモール筑紫野店', 'ジュース', CF, ('2F', '203'), None, '10:00〜21:00(LO20:50)', '092-408-2807', None, 'フルーツ専門店のジュースバー。'),
    ('chikushino-teaway', 'Tea Way イオンモール筑紫野店', 'タピオカ', CF, ('1F', '101'), None, '9:00〜21:00', '092-929-6218', None, 'タピオカドリンク。'),
    ('chikushino-kudamonocafe', 'くだものかふぇ イオンモール筑紫野店', 'ジュース', CF, ('1F', '148'), None, '10:00〜21:00', '050-1809-4161', None, 'フレッシュフルーツジュース。'),
]
assert len(FOOD) == 35, len(FOOD)
for sid, nm, g, tpl, loc, seats, hrs, tel, km, extra in FOOD:
    head = tpl % (loc if isinstance(loc, tuple) else (loc,))
    v = head + extra + (KM if km else '') + hrs + '。' + (('TEL %s。' % tel) if tel else '') + (seats + '。' if seats else '')
    if tpl is FC:
        v += FCK
    v += NOTE
    child(CH, sid, nm, g, 'gourmet', v, kids=kids_menu() if km else None)

# ================= 整合チェック =================
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids)), 'id重複'
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())], 'wish=Trueに動画'
import re
assert all(re.fullmatch(r'[A-Za-z0-9_-]+', i) for i in added)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
cnt = {}
for i in added:
    k = by[i].get('in') or '(親)'; cnt[k] = cnt.get(k, 0) + 1
print('added', len(added), cnt)
print('changed', changed)
print('skipped', skipped)
print('IDS', ' '.join(added))
