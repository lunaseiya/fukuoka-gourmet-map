# -*- coding: utf-8 -*-
"""サンリブ古賀 実訪問(2026-10-07)の反映。

⛔ 館内に「撮影禁止」の掲示あり → ユーザーの写真はマップに一切載せない(thumb/photos は触らない)。
写真は情報の読み取りにのみ使用:
  - 2Fフロアガイド: ベビー休憩室・ガチャポン売場・ふぇすたらんど が隣接
  - ベビールーム入口「男女ご利用いただけます」/ 奥に「女性用授乳室」(個室)
  - フードコートの木製子供椅子(ベルトなし)
  - Niko Niko Garden 券売機の料金
  - 古賀食堂 券売機の営業時間掲示(11:00〜16:00 / LO15:30 / 水曜定休)
  - 子供用カート(アンパンマン等の車型・ベビーシート付き)
"""
import json, shutil, os

P = os.path.join(os.path.dirname(__file__), '..', 'data', 'spots.json')
P = os.path.abspath(P)
shutil.copy(P, P + '.bak_sunlivekoga_visit_20261007')
d = json.load(open(P, encoding='utf-8'))
by = {s['id']: s for s in d}

V = "2026-10-07"

# ---- 親: サンリブ古賀(赤ピン) ----
s = by['sunlivekoga']
s['wish'] = False
s['visited'] = V
s['kids']['diaper'] = True
s['kids']['kidsChair'] = True   # 1Fフードコートの共用子供椅子
s['verdict'] = (
    "JR古賀駅西口から徒歩約3分のサンリブのSC。"
    "⭐2Fベビー休憩室(ふぇすたらんど横): 入口は男女とも利用OKで、おむつ替え台・洗い場あり。"
    "奥に女性用授乳室(個室)があり、調乳用のお湯はその中なので⚠男性はおむつ替えスペースまでで、パパだけでミルクを作るのは難しい。"
    "⭐1Fフードコート(ファーストキッチン・ケンタッキー・古賀食堂)に木製の子供椅子あり(ベルトなしタイプ)。"
    "⭐ベビー休憩室を出た所にガチャポン売場がずらり。2Fのゲームコーナー「ふぇすたらんど」は幼児向けの乗り物からUFOキャッチャー・小学生向けまで、屋内遊び場Niko Niko Garden(0〜8歳)も。"
    "子供が乗れる車型カート・ベビーシート付きカートあり。2Fに西松屋。"
    "駐車場1,450台(料金は要確認)。9:30〜20:00。TEL 092-943-0088。"
    "⚠館内に撮影禁止の掲示あり(動画・SNS用の撮影は不可)。(2026-10-07実訪問)"
)

# ---- ふぇすたらんど(赤ピン) ----
s = by['sunlivekoga-festaland']
s['wish'] = False
s['visited'] = V
s['ages'] = ['toddler', 'kids']
s['ages_src'] = 'manual'
s['verdict'] = (
    "⭐サンリブ古賀2Fのゲームコーナー。アンパンマンの乗り物など幼児向けから、ポケモン等のキッズゲーム、UFOキャッチャー、小学生向けまで揃う。"
    "⭐同じ区画に屋内遊び場Niko Niko Garden: こども 平日フリー500円/土日祝60分500円・フリー800円、おとな入場300円、2人目以降の0歳児は無料(店内掲示 2026-10-07)。"
    "すぐ横にベビー休憩室とガチャポン売場。9:30〜20:00。TEL 092-943-1300。"
    "⚠ゲームは有料。⚠館内に撮影禁止の掲示あり。(2026-10-07実訪問)"
)

# ---- Niko Niko Garden: 料金が券売機と一致したことだけ追記(ピンは青のまま) ----
s = by['sunlivekoga-nikonikogarden']
if '券売機' not in s['verdict']:
    s['verdict'] += "(料金は店内券売機の表示と一致 2026-10-07)"

# ---- フードコート3店(青ピンのまま。共用の子供椅子・ベビー休憩室は建物内) ----
FC_NOTE = "フードコート共通の子供椅子あり(ベルトなし)(2026-10-07現地確認)。"

def fc_kids(s):
    if not s.get('kids'):
        s['kids'] = {"stroller": None, "diaper": None, "tatami": None,
                     "kidsChair": None, "serveMin": None, "noise": None}
    s['kids']['kidsChair'] = "facility"
    s['kids']['diaper'] = "facility"   # 2Fベビー休憩室

s = by['sunlivekoga-firstkitchen']
fc_kids(s)
s['verdict'] = (
    "サンリブ古賀 1Fフードコート内(ウェンディーズ・ファーストキッチン)。⭐キッズセットあり(公式)。"
    "⭐" + FC_NOTE + "レジ前に子供向けのおもちゃのカゴあり(2026-10-07)。サンリブ商品券が使える。"
    "フードコートは225席。9:30〜20:00(LO19:30)。TEL 092-410-2922。"
)

s = by['sunlivekoga-kfc']
fc_kids(s)
s['verdict'] = (
    "サンリブ古賀 1F(フードコート)。⭐" + FC_NOTE +
    "9:30〜20:00。TEL 092-943-1711。⚠未訪問。"
)

s = by['sunlivekoga-kogashokudou']
fc_kids(s)
s['verdict'] = (
    "サンリブ古賀 1Fフードコート内の食券制の食堂(旧ハッピーメイト跡・2023年9月オープン)。日替り定食・ラーメン・ちゃんぽん・カレー等。"
    "11:00〜16:00(LO15:30)・水曜定休(店頭の券売機掲示 2026-10-07。現地で店舗の存続を確認)。"
    "⭐" + FC_NOTE + "⚠未訪問(食事はまだ)。"
)

# ---- 書き戻し + 整合チェック ----
ids = [x['id'] for x in d]
assert len(ids) == len(set(ids)), 'id重複'
bad = [x['id'] for x in d if x.get('wish') and any((x.get('video') or {}).values())]
assert not bad, f'wish=Trueなのに動画あり: {bad}'
with open(P, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print('OK', len(d))
