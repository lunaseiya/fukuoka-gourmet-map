# -*- coding: utf-8 -*-
"""サンリブ古賀(新規・親・青ピン)と館内の子スポット(青ピン)を一括登録(2026-10-07)。
   ユーザー呼称「古賀のサンリブ」。登録はユーザー事前承認済み。ネット調査のみ → 親子とも wish=True / visited=None。
   根拠(すべて 2026-10-07 取得):
     - サンリブ公式 店舗ページ https://www.sunlive.co.jp/shop/サンリブ古賀/
       店名「サンリブ古賀」・住所 古賀市天神2-5-1・TEL 092-943-0088・9:30〜20:00・駐車場1,450台(料金記載なし)、
       設備に「授乳室」「多目的トイレ」「エレベーター」「車椅子貸し出し」。
       専門店: 2F 西松屋/Seria/ふぇすたらんど(プレイランド)… 1F ファーストキッチン/ケンタッキー/ハースブラウン/唐十/かば田/ひよ子…
     - ふぇすたらんど公式 https://www.luluarq.co.jp/festaweb/land-koga.html (9:30〜20:00・TEL 092-943-1300)
     - Niko Niko Garden 公式 https://www.luluarq.co.jp/festaweb/playground-nikonikogarden.html
       古賀店: 9:30〜19:00(最終受付18:30)・対象0〜8歳・こども 平日フリータイム500円/土日祝60分500円・フリータイム800円・
       2人目以降の0歳無料・おとな一律300円(途中交代OK)
     - 子育て応援の店 福岡 https://kosodate-mise.pref.fukuoka.lg.jp/shop-detail?cd=33643 (ふぇすたらんど古賀店)
       おむつ替え・授乳/搾乳スペース・多目的トイレ・ベビーカー貸出/ベビーカート
     - いこーよ https://iko-yo.net/facilities/19696 (ニコニコ・ガーデン古賀店: 靴下着用・指定場所で飲食可)
     - ファーストキッチン公式 https://www.first-kitchen.co.jp/shop/map.php?shopid=154
       「古賀サンリブ」1Fフードコート内・9:30〜20:00(LO19:30)・225席・キッズセットあり・TEL 092-410-2922
     - KFC公式 https://search.kfc.co.jp/map/7044 (9:30〜20:00・TEL 092-940-1711)
     - 食べログ 古賀食堂 https://tabelog.com/fukuoka/A4003/A400302/40065533/ (1F・11:00〜18:00・2023/9/18オープン。
       サンリブ公式の専門店一覧には載っていない → 営業状況は要確認と明記)
     - 食べログ ハースブラウン https://tabelog.com/fukuoka/A4003/A400302/40032441/ (10:00〜21:00・TEL 092-944-6079)
   座標: geocoding.jp「福岡県古賀市天神2丁目5-1」→ 33.734517,130.466432。子は親と共有(館内)。
   重複: 同名なし。400m以内の既存は「博多豚骨ラーメン 三八」(約300m・別店)のみ。
   ユーザーの「バースキッチン」= ファーストキッチン(1Fフードコート)と判断。
   登録しない: 唐十/かば田/ひよ子(持ち帰り専門の物販)。
     食べログの館内一覧にある キーコーヒー/キッチンあしたば/ひので家/いちばんどり は
     サンリブ公式の専門店一覧に無い(閉店・撤退の可能性)ため登録しない。旧フードコート「ハッピーメイト」は閉店済み。"""
import io, json, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_sunlive_koga')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
names = {x['name'] for x in s}
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
added, skipped = [], []


def kids_none():
    return {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None}


PID = 'sunlivekoga'
LAT, LNG = 33.734517, 130.466432
OFF = 'https://www.sunlive.co.jp/shop/%E3%82%B5%E3%83%B3%E3%83%AA%E3%83%96%E5%8F%A4%E8%B3%80/'
if PID in by:
    skipped.append((PID, 'id重複'))
elif 'サンリブ古賀' in names:
    skipped.append((PID, '同名重複'))
else:
    p = {'id': PID, 'name': 'サンリブ古賀', 'area': None, 'city': '古賀市', 'pref': '福岡県',
         'genre': 'ショッピングセンター', 'lat': LAT, 'lng': LNG, 'address': '福岡県古賀市天神2丁目5-1',
         'visited': None, 'with': 'family',
         'kids': {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
         'verdict': 'JR古賀駅西口から徒歩約3分のサンリブのSC。⭐授乳室あり(公式)、2Fのふぇすたらんどにおむつ替え・授乳スペース・'
                    'ベビーカー貸出/ベビーカート(子育て応援の店 福岡)。⭐2Fに屋内遊び場「Niko Niko Garden」(0〜8歳)とゲームコーナー、西松屋。'
                    '1Fフードコートにファーストキッチン(キッズセットあり)・ケンタッキー・古賀食堂。'
                    '駐車場1,450台(料金は要確認)。9:30〜20:00。TEL 092-943-0088。⚠未訪問(ネット調べ)。',
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': 'play',
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


# ---------- 遊び・子供向け(2F) ----------
child('sunlivekoga-nikonikogarden', 'Niko Niko Garden 古賀店', '室内遊び場', 'play',
      '⭐サンリブ古賀2F・ふぇすたらんど内の屋内遊具施設(0〜8歳)。跳ねる・回る系のキッズアスレチック。'
      'こども 平日フリータイム500円/土日祝60分500円・フリータイム800円、2人目以降の0歳無料、おとな一律300円(途中交代OK)。'
      '9:30〜19:00(最終受付18:30)。TEL 092-943-1300。⚠靴下着用・保護者付き添い必須。'
      'おむつ替え・授乳スペース・ベビーカー貸出あり(子育て応援の店 福岡)。',
      kids={'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
      ages=['baby', 'toddler', 'kids'], web='https://www.luluarq.co.jp/festaweb/playground-nikonikogarden.html')
child('sunlivekoga-festaland', 'ふぇすたらんど古賀店', 'ゲームセンター', 'play',
      'サンリブ古賀2Fのアミューズメント。キッズアスレチック・メダルゲーム・景品ゲーム・キッズカードゲーム(いこーよ)。'
      '9:30〜20:00。TEL 092-943-1300。⚠ゲームは有料。屋内遊び場はNiko Niko Garden(別料金)。',
      kids={'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
      ages=['toddler', 'kids'], web='https://www.luluarq.co.jp/festaweb/land-koga.html')
child('sunlivekoga-nishimatsuya', '西松屋 サンリブ古賀店', 'ベビー用品', 'play',
      'サンリブ古賀2Fのベビー・子供用品店(サンリブ公式の専門店一覧)。営業時間は要確認。',
      ages=['baby'], web=OFF)

# ---------- 飲食(1F) ----------
NOTE = '⚠未訪問。キッズチェア等は要確認。'
child('sunlivekoga-firstkitchen', 'ファーストキッチン 古賀サンリブ店', 'ハンバーガー', 'gourmet',
      'サンリブ古賀 1Fフードコート内。⭐キッズセットあり(公式)。フードコートは225席。9:30〜20:00(LO19:30)。TEL 092-410-2922。' + NOTE,
      kids={'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None, 'kidsMenu': True},
      web='https://www.first-kitchen.co.jp/shop/map.php?shopid=154')
child('sunlivekoga-kfc', 'ケンタッキーフライドチキン サンリブ古賀店', 'フライドチキン', 'gourmet',
      'サンリブ古賀 1F(フードコート)。9:30〜20:00。TEL 092-940-1711。' + NOTE,
      web='https://search.kfc.co.jp/map/7044')
child('sunlivekoga-kogashokudou', '古賀食堂', '食堂', 'gourmet',
      'サンリブ古賀 1Fフードコート内(旧ハッピーメイト跡・2023年9月オープン)。日替わりランチ・ちゃんぽん・チャーハン等。'
      '11:00〜18:00。⚠サンリブ公式の専門店一覧に記載が無く営業状況は要確認。' + NOTE,
      web='https://tabelog.com/fukuoka/A4003/A400302/40065533/')
child('sunlivekoga-hearthbrown', 'ハースブラウン サンリブ古賀店', 'パン', 'gourmet',
      'サンリブ古賀 1Fのベーカリー。イートインは同じフロアのフードコートを利用。10:00〜21:00(食べログ)。TEL 092-944-6079。' + NOTE,
      web='https://tabelog.com/fukuoka/A4003/A400302/40032441/')

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
