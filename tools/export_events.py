# -*- coding: utf-8 -*-
"""イベント一覧画面(map/events.html)用の `map/events.json` を書き出す。

【なぜ作るか・2026-09-16ユーザー確定】
  「これを機にイベントが見やすくなるマップ(もしくは別画面)でも作りますか？
    イメージではマップ画面を使わずリストを全画面表示で良くて、
    例えば1日〜14日までの2週間のイベントを表示していくとか」
  → マップのピンではなく**全画面のリスト**。既定は**今日から14日間**。

【データ源は2つ。⚠必ず区別して出す(ユーザー選択の「C. 両方＋区別」)】
  ① spots.json の `until` 持ち … **こちらで裏取り済み**(会場・料金・座標を1件ずつ確認)。
                                 `verified: true`。マップのスポットページへリンクできる
  ② _週末イベント候補.json    … 週次収集の全件。**裏取りしていない**(集約サイトの転記)。
                                 `verified: false`。**出典URLを必ず添えて「要確認」と出す**
  ⚠混ぜて「同じ品質」に見せてはいけない。1,636件を1件ずつ裏取りして積み上げた
    マップの信頼性を、未確認の転記で損なわないため。

【子連れ/すべての切り替え・2026-09-16ユーザー要望】
  「子連れオススメ、じゃないのも登録しておけば役に立つのではないかなと。
    基本は子連れ、子連れ以外も含む、みたいな切り替えが欲しいですね」
  → 各件に `kids`(真偽) を持たせ、画面側で切り替える。
    判定は**総合スコアではなく kids_score + ポスター加点**で見る。
    総合スコアには「今週で終わる」「複数源」などの新規性ボーナスが混ざっていて、
    子連れ向きかどうかとは別物だから。**しきい値は6**(子連れ語1つ or 体験語で届く)。

【ポスターは自前で持つ・2026-09-16ユーザー確定】
  「イベント一覧では、子連れの内容のみでもポスターをつけていけませんか？メインですので。
    その代わりイベントは過ぎたら削除が可能です。」→ **全件(201件)自前**で持つことに決定。
  実測: 生画像は平均156KB(最大1.9MB)だが、**幅480pxのJPEG(q78)にすると1枚40〜60KB**。
        201件で約10MB。リポジトリは現在294MB / Pages上限1,024MB なので余裕がある。
  ⚠**会期が過ぎたものは毎回消す**(prune)。放置しないから常時この規模で頭打ちになる。
  ⚠**IPコラボは持たない**(poster_ok で弾く)。版元の権利が重なり施設側にも再配布権が無い。
    その代わり料金・時間・内容を厚めに出す。
  ⚠**縮小のみ。トリミングしない**(出典の写真は無改変が原則)。出典URLを必ず添える。

【収益の動線・2026-09-16ユーザーの懸念への答え】
  「マップが収益のキッカケです。別画面とすると収益につながるキッカケが減りませんかね？」
  → イベント自体は収益にならない(食べログもアソビューもじゃらんも付かない)。
    なので**会場の座標から近隣の「収益リンクを持つスポット」を3件まで**引いて
    `near` に入れ、画面側で「近くのお店を見る」として出す。収益スポットは539件ある。
  ⚠座標は ①裏取り済みは spots の lat/lng ②未裏取りは**会場名を spots.json と突合**して借りる。
    どちらも取れないものは `near` を空にする(**推測で座標を作らない**)。

使い方:
    python tools/export_events.py                       # 今日から14日 + ポスター取得
    python tools/export_events.py --days 21 --no-posters
"""
import argparse, io, json, math, os, re, sys
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mall_event_watch as M
import week_events as W

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
CAND = os.path.join(ROOT, 'data', '_週末イベント候補.json')
EXTRA = os.path.join(ROOT, 'data', '_イベント補足.json')
OUT = os.path.join(ROOT, 'map', 'events.json')
PDIR = os.path.join(ROOT, 'map', 'eventposters')
KIDS_TH = 6
AGG = ('いこーよ', '県公式', 'よかなび', '久留米観光', 'マップ登録')
PW, PQ = 480, 78          # ポスターの幅とJPEG品質(1枚40〜60KBに収まる)
NEAR_KM, NEAR_N = 2.0, 3  # 近隣スポットを探す半径と件数


def km(a, b, c, e):
    return math.hypot((a - c) * 111.0, (b - e) * 111.0 * math.cos(math.radians(a)))


# ⚠**行政区画名だけの「会場」で突合してはいけない**【2026-09-16に発覚】
#   会場が分からないイベントは venue() が市区名を代わりに入れる。それで名前突合すると
#   「久留米市」→**久留米市美術館**、「太宰府市」→**太宰府市立プール**を会場と見なし、
#   座標も「この近くのお店」も**別の場所のもの**になっていた。
#   ⚠「町」「村」は施設名の語尾にも出る(能古島キャンプ**村**)ので入れない
ADMIN = re.compile(r'^[一-龥ぁ-んァ-ヶー]{2,6}[都道府県市区]$')


def venue_coords(spots, vname, city):
    """会場名を spots.json と突合して座標を借りる。
    ⚠**取れなければ None を返す**。推測で座標を作らない(map-spot スキルの鉄則)"""
    if not vname:
        return None
    if ADMIN.match(vname.strip()) or (city and core(vname) == core(city)):
        return None
    cv = core(vname)
    if len(cv) < 2:
        return None
    best = None
    for s in spots:
        if s.get('lat') is None or s.get('lng') is None:
            continue
        cs = core(s.get('name'))
        if not cs:
            continue
        # ⚠**完全一致に長さ制限をかけてはいけない**【2026-09-16に踏んだ】
        #   `len(cv) < 4` で弾いていたため、**「筥崎宮」(3文字)を登録したのに突合できず**、
        #   放生会の座標が空のままだった。完全一致なら3文字でも別施設ではない
        if cs == cv:
            return (s['lat'], s['lng'], s.get('name'), s['id'])
        # 部分一致は誤爆しやすいので4文字以上を要求し、**短い名前(=館そのもの)**を優先する
        if len(cv) >= 4 and (cv in cs or cs in cv) and len(cs) >= 4:
            if best is None or len(cs) < len(best[2] or ''):
                best = (s['lat'], s['lng'], s.get('name'), s['id'])
    return best


# ★**タイトルに施設名が書いてあるものを拾う**【2026-09-16】
#   会場欄が市区名しか無いのに、タイトルに会場が書いてあるものが多かった:
#     「**BOSS E・ZO FUKUOKA**で「魔法の美術館」開催！」
#     「パンダコパンダ展 **北九州市漫画ミュージアム**の巻」
#     「初めてのDIY体験！ ＠**カインズ福岡新宮店**」「**宗像ユリックス**プラネタリウム」
#   spots の名前がタイトルに含まれていれば会場と断言できる。
#   ⚠**6文字以上(記号を除いた文字数)だけ**を対象にする。短い名前は別物に当たる
TITLE_MIN = 6


def title_venue(spots, title):
    """タイトルに含まれる施設名で会場を決める。**最長一致**を採る
    (館名とテナント名が両方入っている場合に館を選ぶため)"""
    ct = core(title)
    if len(ct) < TITLE_MIN:
        return None
    best = None
    for s in spots:
        if s.get('lat') is None or s.get('lng') is None:
            continue
        if s.get('until'):          # 期間限定イベントのスポットは会場ではない
            continue
        cs = core(s.get('name'))
        if len(cs) < TITLE_MIN or cs not in ct:
            continue
        if best is None or len(cs) > len(core(best[2])):
            best = (s['lat'], s['lng'], s.get('name'), s['id'])
    return best


def near_spots(spots, lat, lng):
    """収益リンクを持つスポットだけを近い順に。★これがイベント一覧の収益導線"""
    out = []
    for s in spots:
        if s.get('lat') is None or s.get('lng') is None:
            continue
        if not (s.get('tabelog') or s.get('asoview') or s.get('booking')):
            continue
        dd = km(lat, lng, s['lat'], s['lng'])
        if dd > NEAR_KM:
            continue
        out.append((dd, s))
    out.sort(key=lambda z: z[0])
    res = []
    for dd, s in out[:NEAR_N]:
        res.append({'id': s['id'], 'name': s.get('name') or '',
                    'genre': s.get('genre') or '', 'km': round(dd, 2),
                    'tabelog': s.get('tabelog'), 'asoview': s.get('asoview'),
                    'booking': s.get('booking')})
    return res


def save_poster(url, eid):
    """⚠**縮小のみ**。トリミングしない。出典は画面側でリンクとして出す"""
    from PIL import Image
    import event_carousel as EC
    fn = eid + '.jpg'
    p = os.path.join(PDIR, fn)
    if os.path.exists(p):
        return fn
    im = EC.get_poster(url)
    if im is None:
        return None
    if im.width > PW:
        im = im.resize((PW, max(1, round(im.height * PW / im.width))), Image.LANCZOS)
    try:
        im.convert('RGB').save(p, quality=PQ, optimize=True)
    except Exception:
        return None
    return fn


def core(s):
    return re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ヶー]', '', s or '')


BRACKET = re.compile(r'【([^】]{2,22})】')
# ⚠**「◯◯エリア」は源サイトの地域カテゴリで、会場ではない**【2026-09-16に公開ページで発覚】
#   よかなびの `venues` は ['EAST COAST(志賀島)エリア', 'いこーよ', '筥崎宮 放生会'] のような順で、
#   3番目の本物がタイトルとかぶるため捨てられ、**1番目の地域カテゴリが会場として出ていた**。
#   放生会は東区箱崎なので「志賀島エリア」は**嘘**。18件が同じ形だった
AREA = re.compile(r'エリア')
# 【】の中身を会場として採れるかの判定。施設らしい語尾を持つものだけ通す。
# (【FaN Week 2026】【福岡検定合格者限定】のようなイベント名・ラベルを会場にしないため)
VENUEISH = re.compile(r'館|宮|寺|神社|公園|ホール|センター|ドーム|モール|ぽーと|広場|'
                      r'スタジアム|アリーナ|城|駅|市場|キャンプ|タワー|プラザ|ビル|会館|'
                      r'劇場|美術|博物|科学|動物|水族|植物|温泉|海浜|埠頭|ふ頭|港|'
                      r'小学校|中学校|高校|大学|公民館|図書館|体育館|球場|遊園')


def clean(t):
    """タイトルを整えつつ、**文中どこにあっても【】を会場候補として抜き出す**。
    ⚠以前は**先頭の【】しか見ていなかった**ので
      「筥崎宮『放生会』**【筥崎宮】**2026年…」「特別展「…」**【福岡市科学館】**」の
      会場を取りこぼし、代わりに地域カテゴリが会場として出ていた(2026-09-16)"""
    t = t or ''
    heads = [h.strip() for h in BRACKET.findall(t)]
    rest = BRACKET.sub(' ', t)
    rest = re.sub(r'\s*[～~][^～~]{18,}$', '', rest)
    return re.sub(r'\s+', ' ', rest).strip(), heads


def venue(r, tt, heads):
    """会場を決める。優先順は ①タイトルの【施設名】 ②venues の非かぶり候補
       ③venues のかぶり候補 ④市区。
    ⚠**かぶる候補を捨てて次に進んではいけない**。捨てた結果、誤った候補(地域カテゴリ)に
      流れるほうが害が大きい。かぶりは「最後の手段」として残す"""
    ct = core(tt)

    def dup(v):
        cv = core(v)
        return any(cv[i:i + 6] in ct for i in range(max(0, len(cv) - 5)))

    for h in heads:
        if h and not any(a in h for a in AGG) and len(core(h)) <= 26 and VENUEISH.search(h):
            return h
    later = []
    for v in (r.get('venues') or []):
        if not v or any(a in v for a in AGG) or AREA.search(v):
            continue
        if len(core(v)) > 26:
            continue
        if dup(v):
            later.append(v)
            continue
        return v
    return (later[0] if later else '') or (r.get('city') or '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=14, help='今日から何日ぶんを出すか')
    ap.add_argument('--today', help='基準日(既定は今日)')
    ap.add_argument('--no-posters', action='store_true',
                    help='ポスターの取得と掃除をしない(データだけ作り直すとき)')
    a = ap.parse_args()
    t0 = date.fromisoformat(a.today) if a.today else date.today()
    t1 = t0 + timedelta(days=a.days - 1)
    span = [(t0 + timedelta(days=i)).isoformat() for i in range(a.days)]

    supp = json.load(io.open(EXTRA, encoding='utf-8')) if os.path.exists(EXTRA) else {}
    spots = json.load(io.open(SPOTS, encoding='utf-8'))
    by_id = {x['id']: x for x in spots}
    out, seen = [], {}

    # ── ① 裏取り済み(spots.json の until 持ち) ────────────────────
    for s in spots:
        u = s.get('until')
        if not u:
            continue
        try:
            e = date.fromisoformat(u)
        except Exception:
            continue
        if e < t0:                      # 会期が過ぎたものは出さない(until と同じ考え方)
            continue
        st = s.get('from') or None      # 開始が入っていれば使う。無ければ「〜◯日まで」表示
        days = [x for x in span
                if (not st or st <= x) and x <= u]
        if not days:
            continue
        ks = M.kids_score((s.get('name') or '') + ' ' + (s.get('genre') or '')
                          + ' ' + (s.get('verdict') or ''))
        rec = {'id': s['id'], 'title': s.get('name') or '', 'venue': s.get('area') or '',
               'city': s.get('city') or '', 'pref': s.get('pref') or '',
               'start': st, 'end': u, 'untilLabel': s.get('untilLabel') or '',
               'days': days, 'n': len(days), 'url': s.get('web') or '',
               'poster': None, 'price': None, 'time': None,
               'verified': True, 'spot': s['id'],
               'lat': s.get('lat'), 'lng': s.get('lng'),
               'kids': ks >= KIDS_TH, 'ks': ks, 'score': None}
        out.append(rec)
        seen[core(rec['title'])[:10]] = rec

    # ── ② 週次収集の全件(未裏取り) ───────────────────────────
    if os.path.exists(CAND):
        cand = json.load(io.open(CAND, encoding='utf-8'))
        for r in cand.get('events') or []:
            sp = supp.get(r['url']) or {}
            ka = int(sp.get('kids_add') or 0)
            dl = r.get('days_list')
            if dl:
                days = [x for x in dl if x in span]
                st, en = (min(dl) if dl else None), (max(dl) if dl else None)
            else:
                st, en = r['span'][0], r['span'][1]
                if not st:
                    continue
                days = [x for x in span if st <= x <= (en or st)]
            if not days:
                continue
            tt, head = clean(r['title'])
            k = core(tt)[:10]
            if k and k in seen:         # 裏取り済みと同じものは**裏取り側を残す**
                seen[k]['poster'] = seen[k]['poster'] or (
                    r.get('poster') if W.poster_ok(r['title'], r.get('lead')) else None)
                seen[k]['price'] = seen[k]['price'] or sp.get('price')
                seen[k]['time'] = seen[k]['time'] or sp.get('time')
                continue
            ks = M.kids_score(r['title'] + ' ' + (r.get('lead') or '')) + ka
            out.append({
                'id': 'c' + re.sub(r'[^0-9a-zA-Z]', '', r['url'])[-14:],
                'title': tt, 'venue': venue(r, tt, head), 'city': r.get('city') or '',
                'pref': '', 'start': st, 'end': en, 'untilLabel': '',
                'days': days, 'n': len(days), 'url': r['url'],
                # ⚠IPコラボのポスターは参照しない(貼れない回)
                'poster': r.get('poster') if W.poster_ok(r['title'], r.get('lead')) else None,
                'price': sp.get('price') or None, 'time': sp.get('time') or None,
                'verified': False, 'spot': None, 'lat': None, 'lng': None,
                'kids': ks >= KIDS_TH, 'ks': ks, 'score': r['score'] + ka,
                'src': r['src']})

    # ── ③ 座標を埋めて、近隣の収益スポットを付ける ─────────────────
    # ★**まず `in`(会場スポット)を見る**【2026-09-16に追加】
    #   会場が確定していれば、座標もそこから取れるし、**会場自身の収益リンク**を
    #   近隣リストより前に出せる(「魔法の美術館 → BOSS E・ZO FUKUOKA のチケット」)。
    #   ⚠会場名の文字列突合は area に館内の場所が混ざると当たらない(90/220件しか取れなかった)。
    #     `in` がある分はそちらを正とする
    for r in out:
        vid = (by_id.get(r['id']) or {}).get('in') if r['verified'] else None
        v = by_id.get(vid) if vid else None
        if not v:
            continue
        r['venueSpot'] = v['id']
        r['venueName'] = v.get('name') or ''
        if r['lat'] is None and v.get('lat') is not None:
            r['lat'], r['lng'] = v['lat'], v['lng']
        if v.get('tabelog') or v.get('asoview') or v.get('booking'):
            r['venueLinks'] = {'id': v['id'], 'name': v.get('name') or '',
                               'genre': v.get('genre') or '',
                               'tabelog': v.get('tabelog'), 'asoview': v.get('asoview'),
                               'booking': v.get('booking')}
    def fix(r, g, sure):
        """突合で見つかった施設を反映する。`sure=True` のものだけ「会場」として出す"""
        r['lat'], r['lng'] = g[0], g[1]
        r['venueMatch'] = g[3]
        if not sure:
            return
        sp = by_id.get(g[3]) or {}
        r['venueSpot'] = g[3]
        r['venueName'] = g[2] or ''
        if not r['venue'] or ADMIN.match((r['venue'] or '').strip()):
            r['venue'] = g[2] or r['venue']     # 市区名しか無かった会場欄を施設名で埋める
        if sp.get('tabelog') or sp.get('asoview') or sp.get('booking'):
            r['venueLinks'] = {'id': g[3], 'name': g[2] or '',
                               'genre': sp.get('genre') or '',
                               'tabelog': sp.get('tabelog'), 'asoview': sp.get('asoview'),
                               'booking': sp.get('booking')}

    vc, tc = {}, {}
    for r in out:
        if r['lat'] is None:
            key = (r['venue'], r['city'])
            if key not in vc:
                vc[key] = venue_coords(spots, r['venue'], r['city'])
            g = vc[key]
            if g:
                # ⚠部分一致は**名前の文字列突合による推測**なので `venueMatch` に留める。
                #   座標を借りて近隣スポットを引くためだけに使い、「会場」としては出さない。
                # ★**名前が完全一致するなら同じ施設**なので会場として扱ってよい。
                #   「筥崎宮」「はかた伝統工芸館」のように会場名がそのまま spots にあるものは、
                #   `in` を1件ずつ手で付けるのと同じ結果になる。
                #   ⚠部分一致は昇格させない(「久留米市」→久留米市美術館のような事故が起きる)
                fix(r, g, core(g[2]) == core(r['venue']))
        if r['lat'] is None:
            # ★最後に**タイトルに書かれている施設名**で拾う。ここまで来たものは
            #   会場欄が市区名しか無いか空なので、タイトルが唯一の手がかり
            if r['title'] not in tc:
                tc[r['title']] = title_venue(spots, r['title'])
            g = tc[r['title']]
            if g:
                fix(r, g, True)
        r['near'] = near_spots(spots, r['lat'], r['lng']) if r['lat'] is not None else []
        # 会場そのものは「近くのお店」に重複して出さない(会場枠で先に出しているため)
        skip = {r.get('venueSpot'), r.get('venueMatch'), r.get('spot')} - {None}
        r['near'] = [n for n in r['near'] if n['id'] not in skip]

    # ── ④ ポスターを自前で持つ(縮小のみ) + 会期切れの掃除 ────────────
    os.makedirs(PDIR, exist_ok=True)
    if a.no_posters:
        # ⚠**取得はしないが、既にあるファイルは必ず参照する**(2026-09-16に踏んだ)。
        #   ここを飛ばすと JSON から img が全部消えて、画面から絵が無くなる
        have = set(os.listdir(PDIR))
        n2 = 0
        for r in out:
            if r['poster'] and (r['id'] + '.jpg') in have:
                r['img'] = r['id'] + '.jpg'
                n2 += 1
        print('  ポスターは取得せず既存 %d枚を参照(--no-posters)' % n2)
    else:
        got = 0
        for r in out:
            if not r['poster']:
                continue
            fn = save_poster(r['poster'], r['id'])
            if fn:
                r['img'] = fn
                got += 1
    if not a.no_posters:
        keep = {r.get('img') for r in out if r.get('img')}
        gone = 0
        for f2 in os.listdir(PDIR):
            if f2 not in keep:
                try:
                    os.remove(os.path.join(PDIR, f2)); gone += 1
                except Exception:
                    pass
        tot = sum(os.path.getsize(os.path.join(PDIR, f2)) for f2 in os.listdir(PDIR))
        print('  ポスター %d枚を自前で保持 / 会期切れ %d枚を削除 / 合計 %.1f MB'
              % (got, gone, tot / 1048576))

    # ⚠**並び順**【2026-09-16の検品で直した】
    #   旧: `-(score or 99)` … 裏取り済みは score=None なので -99 になり、
    #       **12件が全14日ぶんの先頭を独占**していた。その結果
    #       ①各日の上位6件が常に同じ顔ぶれ ②「すべて」に切り替えても見た目が変わらない
    #       ③裏取り済みはポスターを持たないものが多いので**絵が出ない**(上位6件中4件だけ)
    #   新: 裏取り済みは ks(子連れ度)を代理スコアにして +6、さらに信頼できるぶん +3 だけ優遇。
    #       これで未裏取りの高スコア(ナイトシネマ28点など)と混ざって並ぶ
    def rank(x):
        base = x['score'] if x['score'] is not None else (x['ks'] + 6)
        return base + (3 if x['verified'] else 0)
    out.sort(key=lambda x: (x['days'][0], -rank(x), -x['ks']))
    doc = {'generated': date.today().isoformat(),
           'from': t0.isoformat(), 'to': t1.isoformat(),
           'kids_threshold': KIDS_TH, 'events': out}
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    kid = sum(1 for x in out if x['kids'])
    ver = sum(1 for x in out if x['verified'])
    pos = sum(1 for x in out if x['poster'])
    print('%s 〜 %s の %d日間' % (t0, t1, a.days))
    print('  書き出し %d件 (子連れ向け %d / それ以外 %d)' % (len(out), kid, len(out) - kid))
    print('  裏取り済み %d件 / 未裏取り %d件' % (ver, len(out) - ver))
    print('  ポスター画像あり %d件 / 自前保持 %d件' % (pos, sum(1 for x in out if x.get('img'))))
    print('  座標が取れた %d件 / 近隣の収益スポットが付いた %d件'
          % (sum(1 for x in out if x['lat'] is not None),
             sum(1 for x in out if x['near'])))
    print('  会場が確定(in) %d件 / うち会場自身に収益リンク %d件 / 名前突合で座標だけ借りた %d件'
          % (sum(1 for x in out if x.get('venueSpot')),
             sum(1 for x in out if x.get('venueLinks')),
             sum(1 for x in out if x.get('venueMatch'))))
    print('  → %s (%.0f KB)' % (os.path.normpath(OUT), os.path.getsize(OUT) / 1024))
    # 日別の件数も出す(画面の見え方の見当がつく)
    for x in span:
        n = sum(1 for e in out if x in e['days'])
        nk = sum(1 for e in out if x in e['days'] and e['kids'])
        print('    %s  全%3d件 / 子連れ%3d件' % (x[5:], n, nk))


if __name__ == '__main__':
    main()
