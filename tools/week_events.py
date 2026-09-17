# -*- coding: utf-8 -*-
"""週1回の『週末イベント◯選』投稿のネタを**3つの情報源から集めて1本に束ねる**。

■ 情報源(2026-09-12 実測。どれも静的HTMLで会期が取れる)
  mall  … 商業施設の公式イベントページ(イオンモール6館)  → tools/mall_event_watch.py
            週189件。会期は確実。**時間・場所はイオン九州の館しか取れない**(他はJS描画)
  ikoyo … いこーよ  https://iko-yo.net/events?prefecture_ids[]=40
            ⚠必ず `prefecture_ids[]` 形式。`?prefecture=40` は黙って全国版を返す
            **サーバ側で日付を絞れる**(start_date[y/m/d] / end_date[y/m/d])。
            1ページ15件・`page=N`。市区・完全無料ラベル・リード文まで取れて情報が一番濃い
  pref  … クロスロードふくおか(福岡県公式観光)          → tools/event_watch.py
            自治体・神社・公園など**商業施設に出てこない行事**が入る
  torius… トリアス久山 https://torius.com/event_cal/  【2026-09-17追加】
            糟屋郡久山町。**日程がISO(2026-10-03 / 2026-09-05～2026-09-23)で入っており
            全源の中で一番確実**。ユーザーが現地チラシを持ってきて漏れが判明した源
  hkc   … JR博多シティ こどもCITY HAKATA              【2026-09-17追加】
            /kids/category/?category=kidsevent。**屋上つばめの杜ひろばで月次に
            子連れイベントを回している**(マリオ工作・こども専門学校は毎月/収穫体験/天体観測)。
            日付が `2026/10/13〜2026/10/13` で機械可読。館全体の /newsevent/ は
            セールと営業案内が大半なので**使わない**
  manual… data/_手動イベント.json                      【2026-09-17追加】
            **公式サイトにイベント一覧が無い主催**(万代など)を現地チラシから手で書く。
            ファイルが無ければ0件で通る

■ 選別の考え方(3源合わせると300件超。12選に対して25倍あるので絞るほうが本質)
  ①会期が対象期間にかかるものだけ残す
  ②除外ルールで販促・相談会・物販を落とす(ただし強い子連れ語があれば救う)
  ③タイトルを正規化して同一イベントを束ねる(館ごとに表記がぶれる)
  ④子連れ語＋短期開催＋複数会場＋無料 で並べる
  2026-09-11の県公式87件の検証で、除外ルールがスコアリングを完全に包含した。だから
  「まず除外、次に並べる」の順序を崩さない。

使い方:
    python tools/week_events.py                                  # 次の土日・全源
    python tools/week_events.py --from 2026-09-19 --to 2026-09-21 --n 12
    python tools/week_events.py --src ikoyo,pref                 # 源を選ぶ
    python tools/week_events.py --all                            # 落とした分も見る
"""
import argparse, html, io, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
import mall_event_watch as M       # 除外ルール・子連れ語・正規化を再利用する
import event_watch as X            # クロスロードふくおかのタイルパーサを再利用する

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
# ポスターを読んで手で足した情報(キー=イベントURL)。`kids_add` がスコアに効く。
# ⚠**無ければ空**で動く。カルーセル側も同じファイルを price/place/time/detail に使う
SUPP_PATH = os.path.join(HERE, '..', 'data', '_イベント補足.json')
try:
    SUPP = json.load(io.open(SUPP_PATH, encoding='utf-8'))
except Exception:
    SUPP = {}
UA = M.UA
IKO = 'https://iko-yo.net'


def n(s):
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s))).strip()


# ───────── ポスター画像を使ってよいかの目印【2026-09-12ユーザー方針】─────────
# 告知ポスターは「見せたいから作っている」ものなので、**出典を明記し改変しなければ
# 貼って進める**方針。ただし**版元の権利が重なるIPコラボだけは外す**。
# モール側にキャラクタービジュアルの再配布権が無く、削除要請が来るのはこの層。
IP = re.compile(
    r'ポケモン|ピカチュウ|イーブイ|プリキュア|サンリオ|ハローキティ|キティ|クロミ|マイメロ|'
    r'ちいかわ|アンパンマン|ドラえもん|クレヨンしんちゃん|すみっコ|コナン|ジブリ|トトロ|'
    r'ディズニー|ミッフィー|スヌーピー|リラックマ|シナモロール|ぐでたま|'
    r'仮面ライダー|戦隊|プリチャン|プリマジ|たまごっち|パウ.?パトロール|きかんしゃトーマス|'
    r'ワンピース|呪術廻戦|鬼滅|ハイキュー|スパイファミリー|ウルトラマン|ゴジラ|'
    # ⚠**任天堂系が抜けていた**【2026-09-17に発覚】。大丸福岡天神店の
    #   「星のカービィ デデデ★デパート」のポスターを**自前で保持してしまっていた**
    #   (ポスターに © Nintendo / HAL Laboratory, Inc. の表記あり)。
    #   IPコラボのポスターは版元の権利が重なり施設側にも再配布権が無いので持たない方針
    r'カービィ|デデデ|ワドルディ|メタナイト|マリオ|ルイージ|ゼルダ|リンク|ピクミン|'
    r'スプラトゥーン|どうぶつの森|あつまれどうぶつ|星のカービィ|ニンテンドー|任天堂|'
    # そのほか子連れイベントで実際に見かけるIP
    r'トミカ|プラレール|シルバニア|リカちゃん|ミニオン|スティッチ|'
    r'妖怪ウォッチ|しまじろう|ドゲンジャーズ|ムーミン|バーバパパ|'
    r'パンダコパンダ|トム.?ジェリー|ミッキー|ドラゴンボール|NARUTO|ナルト')


def poster_ok(title, lead=''):
    """ポスターを貼ってよいか。IPキャラが絡むものは False(テキストカードで代替する)"""
    return not IP.search(re.sub(r'[\s　]+', '', (title or '') + (lead or '')))



# ──────────────── 日本語の会期表記パーサ【2026-09-12 実測して作り直し】────────────────
# 県公式(クロスロードふくおか)は 160件中14件が読めていなかった。実際に落ちていた表記:
#   「2026年8⽉4⽇（火）〜16⽇（日）」   ← **康熙部首**の ⽉(U+2F8C)/⽇(U+2F47)。月日と別文字
#   「2026年7月上旬～9月中旬（予定）」   ← 上旬/中旬/下旬で日付が無い
#   「2026年見ごろ：9月」               ← 月だけ
#   「ぶどう：8月中旬〜9月中旬 …」       ← 年が無い + 複数レンジ
#   「2026年3月～11月の第2日曜 ※3月8日、4月12日…」 ← 特定日の列挙(レンジ扱いは誤り)
#   「2025年以降の開催はありません」「【営業終了】」 ← 終了。落とすのが正しい
# ⚠個別に文字を置換しようとして**コードポイントを間違えた**(U+2F8C は「食」で「月」ではない)。
#   康熙部首・全角英数・互換漢字はまとめて **unicodedata.normalize('NFKC')** に任せるのが正解
DASH = str.maketrans({'～': '〜', '~': '〜', '－': '-', '−': '-', '–': '-', '—': '-'})
JUN = {'上旬': 5, '中旬': 15, '下旬': 25}
ENDED = re.compile(r'開催はありません|営業終了|終了しました|終了いたしました|中止')
# ⚠**素の「中止」で終了判定してはいけない**【2026-09-16に発覚・わっしょい百万夏まつりが消えていた】
#   屋外の祭り・花火の会期表記には「**雨天決行、荒天中止（予定）**」がほぼ必ず付く。
#   これを ENDED が拾って ('ended') を返していたため、
#   **kids_score が最大(12点)の大祭・花火が丸ごと収集から消えていた**。
#   → 天候の注記が入っている節を**先に丸ごと落としてから** ENDED を当てる。
#     ただし本当の中止(「開催中止」「中止となりました」)は天候の節にあっても拾う
WEATHER = re.compile(r'[^。\n]*(?:雨天|荒天|悪天候|小雨|強風|降雨|荒天時)[^。\n]*')
ENDED_HARD = re.compile(r'開催中止|中止となり|中止しま|中止いたし|中止です|中止になり|中止に決定|中止させて|開催を中止|延期となり|延期しま')
# ★**タイトルや説明に中止と書いてあるものは出さない**【2026-09-16に公開ページで発覚】
#   「令和8年度 小石原焼窯元展**＜中止になりました＞**」がイベント一覧に出ていた。
#   jspan() は**会期表記の文字列にしか当たらない**ので、タイトル側は素通りしていた。
#   ⚠「雨天中止」「荒天中止」は屋外イベントにほぼ必ず付く注記なので**除外の対象にしない**
CANCELED = re.compile(r'中止|延期|開催見送り')


def canceled(*texts):
    """タイトル・説明が「中止/延期」を言っているか。天候の注記は先に落とす"""
    for x in texts:
        if x and CANCELED.search(WEATHER.sub('', x)):
            return True
    return False
# 「9月19日（土）**・20日（日）**」のように**日だけが追記される**形。
# ⚠これを拾えず、2日間の祭りが**初日1日だけ**の会期になっていた(同日発覚)。
#   土日版のように窓が狭い回だと、2日目しか掛からない祭りが期間外で落ちる
DAY_MORE = re.compile(r'[・、,]\s*(\d{1,2})\s*日')
YMD_J = re.compile(r'(?:(\d{4})年)?\s*(\d{1,2})月\s*(\d{1,2})日')
YM_JUN = re.compile(r'(?:(\d{4})年)?\s*(\d{1,2})月(上旬|中旬|下旬)')
YM_ONLY = re.compile(r'(?:(\d{4})年)?\s*(\d{1,2})月(?!\s*\d|上旬|中旬|下旬)')
# キャナルシティ「2026.9.19(土) ～ 9.23(水・祝)」/ IC中央公園「2026.9.27 開催」形式。
# ⚠曜日の括弧を必須にしていたら「2026.9.27 開催」が読めず0件になった(2026-09-13に踏んだ)。
#   4桁の年が付いているものは括弧なしでも受ける。年が無い場合だけ括弧を要求する
YMD_DOT = re.compile(r'(\d{4})[./](\d{1,2})[./](\d{1,2})|()(\d{1,2})[./](\d{1,2})\s*[(（]')


def _mk(y, m, d, base):
    """年が無い表記の年を推定する。基準日より3ヶ月以上前なら翌年とみなす"""
    if not y:
        y = base.year
        try:
            if date(y, m, min(d, 28)) < base - timedelta(days=95):
                y += 1
        except ValueError:
            pass
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def jspan(text, base=None):
    """日本語の会期表記を (開始, 終了, 特定日リスト) にする。
    読めなければ (False, False, None)、終了済みなら ('ended', ...) を返す"""
    base = base or date.today()
    t = unicodedata.normalize('NFKC', text or '').translate(DASH)
    # ⚠天候の注記(「雨天決行、荒天中止」)を落としてから終了判定する。上の WEATHER のコメント参照
    if ENDED_HARD.search(t) or ENDED.search(WEATHER.sub('', t)):
        return ('ended', 'ended', None)
    # 先頭に出てくる「20XX年」を既定の年にする。
    #   ⚠これが無いと「2026年3月〜11月の第2日曜 ※3月8日…」の ※以降に年が無いため、
    #     3月が基準日より前だからと**翌年(2027)と誤推定**した(2026-09-12に踏んだ)
    y0 = re.search(r'(20\d{2})年', t)
    ds, y = [], int(y0.group(1)) if y0 else None
    for yy, mm, dd in YMD_J.findall(t):
        y = int(yy) if yy else y
        v = _mk(y or None, int(mm), int(dd), base)
        if v:
            ds.append(v)
            y = v.year
    # 「※3月8日、4月12日、…」のように**特定日が3つ以上**列挙されていれば、
    #   min〜max のレンジにすると「その間ずっと開催」と誤読するので日リストとして扱う
    if len(ds) >= 3 and re.search(r'第\d+(日曜|土曜|週)|※', t):
        return (min(ds), max(ds), sorted(set(ds)))
    if not ds:
        for g in YMD_DOT.findall(t):
            yy, mm, dd = (g[0], g[1], g[2]) if g[1] else (g[3], g[4], g[5])
            y = int(yy) if yy else y
            v = _mk(y or None, int(mm), int(dd), base)
            if v:
                ds.append(v)
                y = v.year
    if ds:
        e = ds[-1] if len(ds) > 1 else ds[0]
        # 「2026年8月4日(火)〜16日(日)」のように**終了側が日だけ**の表記を拾う
        m = re.search(r'〜\s*(\d{1,2})\s*日', t)
        if m and len(ds) == 1:
            v = _mk(ds[0].year, ds[0].month, int(m.group(1)), base)
            if v and v >= ds[0]:
                e = v
        # 「9月19日（土）・20日（日）」= **開催日2つ**。日だけの追記を開催日として足す。
        #   ⚠ここを入れる前は初日1日だけの会期になっていた(2026-09-16発覚)
        if len(ds) == 1 and e == ds[0]:
            extra = [_mk(ds[0].year, ds[0].month, int(x), base) for x in DAY_MORE.findall(t)]
            vs = sorted(set([ds[0]] + [v for v in extra if v and v >= ds[0]]))
            if len(vs) > 1:
                return (vs[0], vs[-1], vs)
        return (ds[0], e, None)
    # 上旬/中旬/下旬
    for yy, mm, jj in YM_JUN.findall(t):
        v = _mk(int(yy) if yy else None, int(mm), JUN[jj], base)
        if v:
            ds.append(v)
    if ds:
        return (min(ds), max(ds), None)
    # 月だけ → その月いっぱい
    mo = YM_ONLY.findall(t)
    if mo:
        vs = []
        for yy, mm in mo:
            a = _mk(int(yy) if yy else None, int(mm), 1, base)
            if a:
                nx = date(a.year + (a.month == 12), a.month % 12 + 1, 1)
                vs += [a, nx - timedelta(days=1)]
        if vs:
            return (min(vs), max(vs), None)
    return (False, False, None)


# ───────────────────────── いこーよ ─────────────────────────
ITEM = re.compile(r'<li class="p-index-list-item">([\s\S]*?)</li>')
JDATE = re.compile(r'(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日')


def iko_span(s):
    a, b, _ = jspan(s)
    return (False, False) if a in (False, 'ended') else (a, b)


def from_ikoyo(f, t, maxpage=6):
    q = {'prefecture_ids[]': '40',
         'start_date[year]': f.year, 'start_date[month]': f.month, 'start_date[day]': f.day,
         'end_date[year]': t.year, 'end_date[month]': t.month, 'end_date[day]': t.day}
    rows, seen = [], set()
    for pg in range(1, maxpage + 1):
        qq = dict(q, **({'page': pg} if pg > 1 else {}))
        try:
            h = M.fetch(IKO + '/events?' + urllib.parse.urlencode(qq))
        except Exception as ex:
            print('  ! いこーよ %dページ目 %s' % (pg, type(ex).__name__), file=sys.stderr)
            break
        new = 0
        for m in ITEM.finditer(h):
            b = m.group(1)
            u = re.search(r'href="(/events/\d+)"', b)
            ti = re.search(r'__heading">([\s\S]*?)</h3>', b)
            if not (u and ti) or u.group(1) in seen:
                continue
            seen.add(u.group(1)); new += 1
            ad = re.search(r'__address__ellipsis">([\s\S]*?)</span>', b)
            dt = re.search(r'__meta__text">([\s\S]*?)</div>', b)
            ld = re.search(r'__lead">([\s\S]*?)</div>', b)
            labs = [n(x) for x in re.findall(r'__label--\w+">([\s\S]*?)</div>', b)]
            addr = n(ad.group(1)) if ad else ''
            city = (re.sub(r'^福岡県', '', addr.split('/')[0]).strip() or '福岡県')
            pi = re.search(r'class="p-index-list-item__img"[^>]*src="([^"]+)"', b)
            pu = None
            if pi:
                # サムネ指定(&w=140&h=112)を外すと元サイズが返る
                pu = re.sub(r'[&?]w=\d+|[&?]h=\d+', '', html.unescape(pi.group(1)))
                pu = ('https:' + pu) if pu.startswith('//') else pu
            rows.append({'src': 'いこーよ', 'title': n(ti.group(1)), 'poster2': pu,
                         'city': city, 'venue': '', 'url': IKO + u.group(1),
                         'span': iko_span(n(dt.group(1)) if dt else ''),
                         'raw': n(dt.group(1)) if dt else '',
                         'free': '完全無料' in labs, 'lead': n(ld.group(1)) if ld else '',
                         'poster': pu})
        print('  いこーよ %dページ目 +%d (累計%d)' % (pg, new, len(rows)), file=sys.stderr)
        if not new or not re.search(r'rel="next"', h):
            break
        time.sleep(M.WAIT)
    return rows


IKO_TH = re.compile(r'<th[^>]*>([\s\S]{0,40}?)</th>\s*<td[^>]*>([\s\S]{0,400}?)</td>')


def iko_detail(url):
    """いこーよの個別ページから会場・時間・駐車場を取る【2026-09-12 実装】

    詳細ページは <th>ラベル</th><td>値</td> の表になっていて、一覧より情報が濃い:
      イベント名 / イベント名かな / **開催場所の住所** / **交通**(【駐車場台数】【駐車場備考】入り)
      / 問い合わせ先 / **開催日時**(例「2026/09/20(日) 11:00-16:30」) / 予約/応募 / 備考
    ⚠一覧ページには市区までしか無く**会場名が取れない**ので、採用分はここを開く"""
    try:
        h = M.fetch(url)
    except Exception:
        return {}
    d, tbl = {}, {}
    for k, v in IKO_TH.findall(h):
        tbl[n(k)] = n(v)
    if tbl.get('開催場所の住所'):
        d['addr'] = tbl['開催場所の住所']
    if tbl.get('開催日時'):
        # 「2026/09/20(日) 11:00-16:30※ 詳しい開催日は…」から時刻だけ抜く
        m = re.search(r'(\d{1,2}:\d{2}\s*[-〜]\s*\d{1,2}:\d{2})', tbl['開催日時'])
        if m:
            d['time'] = m.group(1)
    if tbl.get('交通'):
        m = re.search(r'【駐車場台数】\s*([0-9,]+)', tbl['交通'])
        free = '【駐車場備考】' in tbl['交通'] and '無料' in tbl['交通'].split('【駐車場備考】')[-1]
        if m:
            d['park'] = '%s台%s' % (m.group(1), '・無料' if free else '')
        m2 = re.search(r'(「[^」]+」から徒歩約?\d+分)', tbl['交通'])
        if m2:
            d['access'] = m2.group(1)
    if tbl.get('問い合わせ先'):
        m = re.search(r'Tel[:：]?\s*([0-9\-]{9,14})', tbl['問い合わせ先'])
        if m:
            d['tel'] = m.group(1)
    # 会場名はタイトル側の 【…】/（…）/＠… に入っていることが多いので住所の末尾で補う
    if d.get('addr'):
        # 住所の**末尾の番地より後ろ**が会場名。「…天神2-9 新天町地下ファーボ」→「新天町地下ファーボ」
        m = re.search(r'[0-9](?:[-−ー丁目番地の0-9]*)\s*([^\s0-9][^0-9]{1,24})$', d['addr'])
        if m and not re.fullmatch(r'[都道府県市区町村丁目番地\s]+', m.group(1)):
            d['place'] = m.group(1).strip()
    return d


# ───────────────────── ららぽーと福岡 ─────────────────────
#  <li><a href="/lalaport/fukuoka/event/NNNN.html">
#    <div class="cont-photo"><img data-src="/resize/376_376/.../image1.jpg"></div>
#    <p class="cont-ttl">タイトル</p>
#    <p class="cont-date">2026/9/27(日)</p>  ※範囲は「2026/9/29(火)～10/14(水)」
LALA = 'https://mitsui-shopping-park.com'
LALA_BLK = re.compile(r'<li><a href="(/lalaport/fukuoka/event/\d+\.html)"([\s\S]{0,1600}?)</a></li>')


def from_lalaport():
    rows = []
    try:
        h = M.fetch(LALA + '/lalaport/fukuoka/event/')
    except Exception as ex:
        print('  ! ららぽーと福岡 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for m in LALA_BLK.finditer(h):
        b = m.group(2)
        ti = re.search(r'class="cont-ttl">([\s\S]*?)</p>', b)
        dt = re.search(r'class="cont-date">([\s\S]*?)</p>', b)
        im = re.search(r'data-src="([^"]+)"', b)
        if not ti:
            continue
        a, e, days = jspan(n(dt.group(1)) if dt else '')
        if a == 'ended':
            continue
        rows.append({'src': 'ららぽーと福岡', 'title': n(ti.group(1)),
                     'city': '福岡市博多区', 'venue': 'ららぽーと福岡',
                     'url': LALA + m.group(1), 'span': (a, e), 'days_list': days,
                     'raw': n(dt.group(1)) if dt else '', 'free': False, 'lead': '',
                     'poster': (LALA + im.group(1)) if im else None})
    print('  ららぽーと福岡 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────────────────── キャナルシティ博多 ─────────────────────
#  <li class="c-post"><a href="/event/detail/NNN...">
#    <p class="c-post__category cat-xxx">カテゴリ</p>
#    <div class="c-post__title"><p>タイトル</p></div>
#    <div class="c-post__date">…<p>2026.9.19(土) ～ 9.23(水・祝)、2026.9.26(土) ～ 9.27(日)</p></div>
CANAL = 'https://canalcity.co.jp'
CANAL_BLK = re.compile(r'<li class="c-post">([\s\S]{0,2200}?)</li>')


def from_canal():
    rows = []
    try:
        h = M.fetch(CANAL + '/event')
    except Exception as ex:
        print('  ! キャナルシティ %s' % type(ex).__name__, file=sys.stderr)
        return rows
    seen = set()
    for m in CANAL_BLK.finditer(h):
        b = m.group(1)
        u = re.search(r'href="([^"]*?/event/detail/\d+[^"]*)"', b)
        ti = re.search(r'c-post__title"[^>]*>\s*<p>([\s\S]*?)</p>', b)
        dt = re.search(r'c-post__date"[\s\S]{0,260}?<p>([\s\S]*?)</p>', b)
        cat = re.search(r'c-post__category[^>]*>([\s\S]*?)</p>', b)
        im = re.search(r'<img[^>]+src="([^"]+\.(?:jpg|jpeg|png|webp))"', b)
        if not (u and ti):
            continue
        url = u.group(1) if u.group(1).startswith('http') else CANAL + u.group(1)
        if url.split('?')[0] in seen:
            continue
        seen.add(url.split('?')[0])
        a, e, days = jspan(n(dt.group(1)) if dt else '')
        if a == 'ended':
            continue
        rows.append({'src': 'キャナルシティ博多', 'title': n(ti.group(1)),
                     'city': '福岡市博多区', 'venue': 'キャナルシティ博多',
                     'url': url, 'span': (a, e), 'days_list': days,
                     'raw': n(dt.group(1)) if dt else '', 'free': False,
                     'lead': n(cat.group(1)) if cat else '',
                     'poster': (im.group(1) if im.group(1).startswith('http') else CANAL + im.group(1)) if im else None})
    print('  キャナルシティ博多 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── アイランドシティ中央公園 / アイランドアイ(福岡市東区・地元)【2026-09-12追加】─────────
#  ユーザーの生活圏。イオン系だけだと独自性が出ないので地元の施設を足す。
#  IC中央公園 https://ic-centralpark.jp/events/ は構造が素直:
#    <div class="eventsCard__itemThumb"><img src="…"></div>
#    <span class="eventsCard__itemDate">2026.9.27 開催</span>
#    <h3 class="eventsCard__itemTtl">タイトル</h3>
ICP = 'https://ic-centralpark.jp'
ICP_BLK = re.compile(r'eventsCard__itemThumb"([\s\S]{0,900}?)eventsCard__itemTtl">([\s\S]*?)</h3>')


def from_iccentral():
    rows = []
    try:
        h = M.fetch(ICP + '/events/')
    except Exception as ex:
        print('  ! IC中央公園 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for m in ICP_BLK.finditer(h):
        mid, title = m.group(1), n(m.group(2))
        dt = re.search(r'eventsCard__itemDate">([\s\S]*?)</span>', mid)
        im = re.search(r'<img src="([^"]+)"', mid)
        a, e, days = jspan(n(dt.group(1)) if dt else title)
        if a in (False, 'ended') or not title:
            continue
        rows.append({'src': 'アイランドシティ中央公園', 'title': title,
                     'city': '福岡市東区', 'venue': 'アイランドシティ中央公園',
                     'url': ICP + '/events/', 'span': (a, e), 'days_list': days,
                     'raw': n(dt.group(1)) if dt else '', 'free': False, 'lead': '',
                     'poster': im.group(1) if im else None})
    print('  アイランドシティ中央公園 %d件' % len(rows), file=sys.stderr)
    return rows


# アイランドアイ https://island-eye.com/topics
#  ⚠一覧に出ている日付は **投稿日**(HTMLコメント <!--2026/09/09-->)で**会期ではない**。
#    会期はタイトルに入っていることが多い(「8/1（土）・8/2（日）アイランドシティ夏まつり開催」)。
#    読めないものだけ個別ページを開く。カテゴリは お知らせ / イベント / アイアイロード
IE = 'https://island-eye.com'
# ⚠一覧の構造は **dl/dt/dd**(2026-09-13に実測し直した)。
#   <dl class="event"><dt>2026/08/20<span>イベント</span></dt>
#     <dd><a href=".../topics/1353">《8/22(土)・23(日)》ハチャメチャフェスティバル開催！</a></dd></dl>
#   最初は <a>…<p>タイトル</p> を探していて**30ブロック取れているのに全件タイトル取れず**だった
#   (トップページは <p> 構造で、/topics とは別だった)
IE_BLK = re.compile(r'<dl class="([^"]*)">\s*<dt>([0-9/]{8,10})\s*<span>([^<]*)</span></dt>\s*'
                    r'<dd>\s*<a href="([^"]*?/topics/\d+)"[^>]*>([\s\S]*?)</a>')


def from_islandeye():
    rows = []
    try:
        h = M.fetch(IE + '/topics')
    except Exception as ex:
        print('  ! アイランドアイ %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for cls, posted, cat, url, ti in IE_BLK.findall(h):
        title = n(ti)
        if not title:
            continue
        # 一覧の日付は**投稿日**で会期ではない。会期はタイトルに入っていることが多い
        a, e, days = jspan(title)
        if a is False and ('イベント' in cat or cls == 'event'):
            try:                                   # タイトルに無いものだけ本文を見る
                a, e, days = jspan(n(M.fetch(url))[:2000])
                time.sleep(M.WAIT)
            except Exception:
                pass
        if a in (False, 'ended'):
            continue
        rows.append({'src': 'アイランドアイ', 'title': title, 'city': '福岡市東区',
                     'venue': 'アイランドアイ', 'url': url, 'span': (a, e),
                     'days_list': days, 'raw': '%s / %s' % (posted, cat),
                     'free': False, 'lead': n(cat), 'poster': None})
    print('  アイランドアイ %d件' % len(rows), file=sys.stderr)
    return rows


# ─────────────────── トリアス久山(TORIUS) ───────────────────
#  【2026-09-17ユーザー確定「源にトリアス久山と万代を追加」】
#  ユーザーが現地でチラシを拾ってきて「源に入ってますか？」と聞かれ、**入っていなかった**。
#  実測すると「くらしを運ぶ!はたらくトラックフェスタ2026(10/3)」は公式に載っていたので、
#  源が無かったことによる取りこぼしだった。
#
#  ⚠**/event/ ではなく /event_cal/ を使う**。一覧(/event/)はページ送り式で会期が
#    本文にしかないが、カレンダーは開催中のイベントを週ごとに並べた静的HTMLで、
#    翌月ぶんまで入っている。**同じイベントが週の数だけ重複して出るのでURLで潰す**。
#  ⚠会期は**個別ページが最も確実**。
#      <div class="schedule"><span class="ttl">日程</span>
#        <span class="txt">2026-10-03</span>          ← 単日
#        <span class="txt">2026-09-05～2026-09-23</span> ← 期間
#    **全源の中でここだけ日付がISOで機械可読**なので、タイトルからの推測(jspan)は
#    個別ページが開けなかったときの保険にしか使わない。
#  ⚠ポスター画像は無い(og:image も本文画像も出ていない)。poster は常に None。
#  ⚠**万代(大縁日)はここには載らない**。万代は店舗側のイベントで、
#    調べた限り静的HTMLでイベントと会期を出しているページが無かった(下のコメント参照)。
TRS = 'https://torius.com'
TRS_LINK = re.compile(r'<a class="event_link cat\d+" href="(https://torius\.com/event/\d+/)">'
                      r'([^<]*)</a>')
TRS_DATE = re.compile(r'class="schedule">\s*<span class="ttl">日程</span>\s*'
                      r'<span class="txt">(\d{4}-\d{2}-\d{2})(?:\s*[～~]\s*(\d{4}-\d{2}-\d{2}))?')
#  ⚠会場は `[開催場所]` の直後だが、**タグを除去すると改行が消えて後続の
#    タイムテーブルまで繋がる**ので、区切り語と長さで必ず打ち切る
TRS_PLACE = re.compile(r'\[\s*(?:開催|展示)場所\s*\]\s*([^\[]{2,60})')
TRS_CUT = re.compile(r'\s*(?:タイムテーブル|タイム\s*テーブル|プログラム|※|【|\[|｜)')
TRS_NOTE = re.compile(r'[（(][^（）()]*(?:場合|変更|予定|中止|雨天)[^（）()]*[）)]\s*$')


def _iso(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def from_torius():
    rows = []
    try:
        h = M.fetch(TRS + '/event_cal/')
    except Exception as ex:
        print('  ! トリアス久山 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    uniq = {}
    for url, ti in TRS_LINK.findall(h):
        uniq.setdefault(url, n(ti))       # ★週ごとの重複をURLで潰す
    for url, title in uniq.items():
        if not title:
            continue
        a = e = None
        body = ''
        try:
            d = M.fetch(url)
            time.sleep(M.WAIT)
            md = TRS_DATE.search(d)
            if md:
                a = _iso(md.group(1))
                e = _iso(md.group(2)) or a
            plain = n(re.sub(r'<[^>]+>', ' ',
                             re.sub(r'<(script|style)[\s\S]*?</\1>', '', d)))
            # ⚠先頭はヘッダのナビ(館内MAP/アクセス/ショップガイド…)なので
            #   **日程の後ろ**を本文にする。先頭200字だとナビしか入らない。
            #   開始日で探すと期間表記の途中で切れるので**終了日**の直後から取る
            k = plain.find(str(e)) if e else -1
            body = (plain[k + 10:k + 800] if k >= 0 else plain[-800:]).strip()
        except Exception as ex:
            print('  ! トリアス久山 個別 %s %s' % (url, type(ex).__name__), file=sys.stderr)
        if not a:                          # 個別が開けなかったときだけタイトルから読む
            a, e, _ = jspan(title)
            if a in (False, 'ended'):
                continue
        if canceled(title, body):
            continue
        venue = 'トリアス久山'
        pl = TRS_PLACE.search(body)
        if pl:
            v = TRS_NOTE.sub('', TRS_CUT.split(n(pl.group(1)))[0]).strip(' 　')
            if len(v) >= 2:
                venue = v[:30]
        rows.append({'src': 'トリアス久山', 'title': title, 'city': '糟屋郡久山町',
                     'venue': venue, 'url': url, 'span': (a, e), 'days_list': None,
                     'raw': '%s〜%s' % (a, e), 'free': '入場無料' in body,
                     'lead': body[:300], 'poster': None})
    print('  トリアス久山 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────────────────── 万代(アミューズメントパーク万代) ─────────────────────
#  【2026-09-17】ユーザー指示で源に足そうとしたが、**足せるページが無かった**。
#  調べた3ドメインの実測:
#    shop.mandai-s.jp/detail/25/ … トリアス久山店の店舗ページ。イベント欄なし(「縁日」0件)
#    mandai-s.jp/news/           … **買取・入荷情報のフィード**(古着/CD/お酒/おもちゃ)で、
#                                  アダルト商材の記事も混ざる。イベントは載らず「大縁日」も0件。
#                                  **子連れマップの源にしてはいけない**
#    mandai.ne.jp/information/   … 遊べるスーパー万代の公式。サイトリニューアル直後で記事2本のみ
#  「秋まつり 大縁日 2026(9/19〜9/23・トリアス久山店ほか・300円で1回)」は
#  **店頭のチラシと公式LINEでしか出ていない**。自動では拾えないので、
#  この手のものは下の **data/_手動イベント.json** に書く。
#  → 万代側にイベント一覧ページができたらここに from_mandai() を作る。


# ─────────────────── 現地チラシなど手で足すイベント ───────────────────
#  【2026-09-17】ユーザーが出先でチラシを拾ってくる運用が定着したので受け皿を作った。
#  ⚠**_イベント補足.json では新規イベントを作れない**。あれはイベントURLをキーに、
#    **既存の行へ** price/place/time/detail/kids_add を足すだけのファイル。
#    公式サイトにイベント一覧が無い主催(万代など)はこちらに書く。
#  data/_手動イベント.json は配列。1件のキーは:
#      title city venue from to url  [src free lead detail kids_add _memo]
#    from / to は **ISO(YYYY-MM-DD)**。to を省くと単日扱い。
#  ⚠price/place/time/detail をカードに出したいときは、**同じ url をキーにして
#    _イベント補足.json にも書く**(既存の源と同じ経路で export_events.py が読む)。
#  ⚠ファイルが無くても**静かに0件**で通す。他の源を止めないため。
MAN_PATH = os.path.join(HERE, '..', 'data', '_手動イベント.json')


def from_manual():
    rows = []
    try:
        man = json.load(io.open(MAN_PATH, encoding='utf-8'))
    except FileNotFoundError:
        return rows
    except Exception as ex:
        print('  ! 手動イベントが読めない %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for m in man:
        a, e = _iso(m.get('from')), _iso(m.get('to') or m.get('from'))
        if not a:
            print('  ! 手動 日付が読めないので飛ばす: %s' % m.get('title'), file=sys.stderr)
            continue
        lead = m.get('lead') or '　'.join(m.get('detail') or [])
        rows.append({'src': m.get('src') or 'チラシ(手動)', 'title': n(m.get('title') or ''),
                     'city': m.get('city') or '', 'venue': m.get('venue') or '',
                     'url': m.get('url') or '', 'span': (a, e or a), 'days_list': None,
                     'raw': '%s〜%s' % (a, e or a), 'free': bool(m.get('free')),
                     'lead': n(lead)[:300], 'poster': None})
    print('  手動(チラシ) %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── JR博多シティ こどもCITY HAKATA(屋上つばめの杜ひろば) ─────────
#  【2026-09-17ユーザー確定】ユーザーが「10月屋上つばめの杜ひろばイベント」の告知を
#  見つけて「定期的にやってる？源に入れるべきか」と聞いてきた。実測したら**完全に定例**で、
#  子連れ向けとしては屈指の濃さだった:
#    ・「◯月屋上つばめの杜ひろばイベント」が9月号・10月号とも掲載 → **月次のまとめ記事**
#    ・スーパーマリオトレイン ペーパークラフト教室 … レポートに6月・7月 → **月1回の定例**
#    ・福岡こども専門学校のイベント              … レポートに6月・7月 → **月1回の定例**
#    ・収穫体験(サツマイモ/イチゴ/ゴマ)・天体観測・ミニ動物園・昆虫展
#    ・季節行事(節分鬼祓い祭り/イースター/春の運動会/ホタル放流会/秋の大収穫祭)
#
#  ⚠**/newsevent/ ではなく /kids/category/?category=kidsevent を使う**。
#    館全体のニュース欄はセール・営業時間・カード入会が大半で子連れ向けが埋もれる。
#    kids 側は `kidsevent`(予告) / `kidsnews`(屋上の営業情報) / `kidsreport`(開催済み)に
#    分かれていて、**イベントだけを確実に取れる**。
#  ⚠**カードの構造が /newsevent/ と違う**。kids 側は `<div class="detail">` の中に
#    `txt01`(カテゴリ)が無く、`date` → `txt02`(タイトル) の順。
#    newsevent 用の正規表現を流用すると**0件になる**(最初に踏んだ)。
#  ⚠**レポートの終了日は `9999/12/31`** というセンチネル。混ぜると永久に残るので開始日に潰す。
#  ⚠**まとめ記事の日付は「掲載期間」で会期ではない**。
#    「10月屋上つばめの杜ひろばイベント」の date は `2026/09/01〜2026/11/03` だった。
#    個別の日時は本文の `〇タイトル/【日時】/【対象】` にしか無いので、
#    **まとめ記事は本文を割って、個別カードに無いものだけ拾う**
#    (マリオ工作・天体観測・こども専門学校は個別カードもあるので二重に出さない)。
HKC = 'https://www.jrhakatacity.com'
# ⚠**カード全体**を掴む(画像は <div class="detail"> の外にあるので、
#   detail だけ切り出すとポスターが取れない)
HKC_CARD = re.compile(r'<li class="cmn-card01">\s*<a href="(/kids/detail/\?cd=(\d+))"'
                      r'([\s\S]*?)</a>')
HKC_DATE = re.compile(r'class="date">\s*(\d{4})/(\d{1,2})/(\d{1,2})'
                      r'(?:\s*[〜~～]\s*(\d{4})/(\d{1,2})/(\d{1,2}))?')
HKC_TXT = re.compile(r'class="txt02">([\s\S]*?)</div>')
HKC_IMG = re.compile(r'<img[^>]+src="(/uploads/[^"]+)"')
HKC_ROUNDUP = re.compile(r'^\s*\d{1,2}月\s*屋上つばめの杜ひろばイベント')
# 本文の 〇見出し + 【日時】 + 【対象】
HKC_BLOCK = re.compile(r'[〇○]\s*([^\n【]{2,50}?)\s*\n?\s*【日時】\s*([^\n【]{2,90})'
                       r'(?:\s*\n?\s*【対象】\s*([^\n※]{1,40}))?')
HKC_FIELD = re.compile(r'\n\s*(時間|場所)\s*\n\s*([^\n]{1,60})')


def _plain(h):
    """<br> を改行に変えてタグを落とす(【日時】ブロックを行で拾うため)"""
    b = re.sub(r'<(script|style)[\s\S]*?</\1>', '', h)
    b = re.sub(r'<br[^>]*>', '\n', b)
    b = re.sub(r'<[^>]+>', '', b).replace('&nbsp;', ' ')
    b = html.unescape(b)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t]+', ' ', b))


def _hkc_venue(place):
    """⚠会場名を **spots.json のスポット名と完全一致させる**【2026-09-17】
    詳細ページの「場所」は「屋上つばめの杜ひろば」で、スポット名
    `JR博多シティ 屋上つばめの杜ひろば` と一致しないため、export_events.py 側の
    完全一致チェックを通らず**会場スポットへのリンクが付かなかった**(座標だけ借りる状態)。
    この源は月ごとにイベントURLが変わるので `_イベント会場.json` に手で足す運用は続かない。
    → 施設名を前置して**毎月自動で紐付く**ようにする。"""
    p = n(place or '').strip('　 ')
    p = re.sub(r'^屋上\s+', '屋上', p)          # 「屋上 つばめの杜ひろば」の表記ゆれ
    if not p:
        return 'JR博多シティ 屋上つばめの杜ひろば'
    if '博多シティ' in p:
        return p
    return 'JR博多シティ ' + p


def from_hakatacity():
    rows, roundups = [], []
    try:
        h = M.fetch(HKC + '/kids/category/?category=kidsevent')
    except Exception as ex:
        print('  ! JR博多シティ %s' % type(ex).__name__, file=sys.stderr)
        return rows
    cards = []
    for path, cd, blk in HKC_CARD.findall(h):
        md, mt = HKC_DATE.search(blk), HKC_TXT.search(blk)
        if not (md and mt):
            continue
        title = n(re.sub(r'<[^>]+>', '', mt.group(1)))
        # カードの画像をポスターにする(IP絡みは poster_ok が後で弾く)
        mi = HKC_IMG.search(blk)
        a = _mk(md.group(1), md.group(2), md.group(3), date.today())
        e = (_mk(md.group(4), md.group(5), md.group(6), date.today())
             if md.group(4) else a)
        if e and e.year >= 9999:        # レポートのセンチネル
            e = a
        if not a:
            continue
        cards.append((HKC + path, title, a, e or a,
                      (HKC + mi.group(1)) if mi else None))

    def detail(url):
        """(場所, 時間, 本文プレーンテキスト)"""
        try:
            d = M.fetch(url)
            time.sleep(M.WAIT)
        except Exception as ex:
            print('  ! JR博多シティ 個別 %s %s' % (url, type(ex).__name__), file=sys.stderr)
            return ('', '', '')
        p = _plain(d)
        f = dict((k, n(v)) for k, v in HKC_FIELD.findall(p))
        return (f.get('場所', ''), f.get('時間', ''), p)

    for url, title, a, e, img in cards:
        if HKC_ROUNDUP.match(title):
            roundups.append((url, title, a, e))
            continue
        place, tm, body = detail(url)
        # 対象欄をリードに入れる。**kids_score は「対象: 未就学児〜小学生」で加点される**
        tg = re.search(r'【対象】\s*([^\n※]{1,40})', body)
        lead = ' '.join(x for x in [title, place, tm,
                                    ('対象 ' + n(tg.group(1))) if tg else ''] if x)
        rows.append({'src': 'JR博多シティ', 'title': title, 'city': '福岡市博多区',
                     'venue': _hkc_venue(place),
                     'url': url, 'span': (a, e), 'days_list': None,
                     'raw': '%s〜%s' % (a, e), 'free': '無料' in body,
                     'lead': n(lead)[:300], 'poster': img})
    # ── まとめ記事を割る。**個別カードに既にあるものは飛ばす** ──────────
    # ⚠main() の core() はローカル関数なのでここでは使えない。同じ正規化を持たせる
    def _core(x):
        # 「10月◯◯」の月の見出しを落としてから比べる(個別カードは月が付く)
        x = re.sub(r'^\s*\d{1,2}月\s*', '', x or '')
        return re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ヶー]', '', x)

    def _same(x, y):
        """⚠**前方8文字の一致か、短い方が前方一致**で同一とみなす【実測で決めた】
        まとめ記事側は表記がぶれる(「イチゴの苗植え🍓」/「イチゴの苗植え体験」、
        サイト側の誤字「ペーパーグラフト」/「ペーパークラフト」)ので、
        完全一致や固定長の前方一致だけでは**同じ催しが二重に出る**"""
        if not x or not y:
            return False
        if x.startswith(y) or y.startswith(x):
            return True
        return len(x) >= 8 and len(y) >= 8 and x[:8] == y[:8]

    have = [_core(r['title']) for r in rows]
    for url, title, a, e in roundups:
        place, tm, body = detail(url)
        for name, when, tgt in HKC_BLOCK.findall(body):
            nm = n(re.sub(r'[^\w\sぁ-んァ-ヶ一-龥ー・「」『』（）()＆&+\-/]', '', name)).strip('　 ')
            if not nm or any(_same(_core(nm), hv) for hv in have):
                continue
            # ⚠年が書いていないので**掲載日を基準に**推定する
            #   (12月に出る「1月号」を当年と誤らせないため)
            sa, se, _ = jspan(when, a)
            if sa in (False, 'ended'):
                continue
            have.append(_core(nm))
            lead = ' '.join(x for x in [nm, place, when,
                                        ('対象 ' + n(tgt)) if tgt else ''] if x)
            rows.append({'src': 'JR博多シティ', 'title': nm, 'city': '福岡市博多区',
                         'venue': _hkc_venue(place),
                         'url': url, 'span': (sa, se or sa), 'days_list': None,
                         'raw': n(when)[:60], 'free': '無料' in (tgt or ''),
                         'lead': n(lead)[:300], 'poster': None})
    print('  JR博多シティ %d件(個別%d + まとめ割り%d)'
          % (len(rows), len(cards) - len(roundups), len(rows) - (len(cards) - len(roundups))),
          file=sys.stderr)
    return rows


# ───────────────────── 福岡市科学館(六本松) ─────────────────────
#  【2026-09-13ユーザー確定「科学館も追加しておきましょう」】
#  ⚠/event と /events は404。**/news/ が使える**(/activity/ は1.6MBで2021年の
#    コロナ告知が残っており日付が信用できない)。
#  構造: <a href=".../news/YYYY/MM/xxx.html"><article> … <div class="description">
#          9/13(日) 博物館実習生によるオリジナルテーブルサイエンス実施！ 科学館からのお知らせ 2026.09.10
#        </div></article>
#  **末尾の 2026.09.10 は投稿日**で会期ではない。会期はタイトル先頭に入っている
KGK = 'https://www.fukuokacity-kagakukan.jp'
KGK_BLK = re.compile(r'<a href="(https://www\.fukuokacity-kagakukan\.jp/news/\d{4}/\d{2}/[^"]+)"'
                     r'[^>]*>\s*<article>([\s\S]{0,1400}?)</article>')


def from_kagakukan():
    rows = []
    try:
        h = M.fetch(KGK + '/news/')
    except Exception as ex:
        print('  ! 福岡市科学館 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for url, b in KGK_BLK.findall(h):
        de = re.search(r'class="description">([\s\S]{0,500}?)</div>', b)
        if not de:
            continue
        t = n(de.group(1))
        t = re.sub(r'\s*科学館からのお知らせ\s*[0-9]{4}\.[0-9]{2}\.[0-9]{2}\s*$', '', t)  # 投稿日を落とす
        t = re.sub(r'\s*[0-9]{4}\.[0-9]{2}\.[0-9]{2}\s*$', '', t).strip()
        if not t:
            continue
        a, e, days = jspan(t)
        if a in (False, 'ended'):
            continue
        im = re.search(r'<img src="([^"]+)"', b)
        rows.append({'src': '福岡市科学館', 'title': t, 'city': '福岡市中央区',
                     'venue': '福岡市科学館', 'url': url, 'span': (a, e),
                     'days_list': days, 'raw': '', 'free': False,
                     'lead': '', 'place': '福岡市科学館(六本松)',
                     'poster': im.group(1) if im else None})
    print('  福岡市科学館 %d件' % len(rows), file=sys.stderr)
    return rows


# ─────────── マップ(spots.json)に自分で登録した期間限定スポット ───────────
#  【2026-09-13ユーザー指摘「チン!するレストランが入ってこないのは？」で追加】
#  「チン!するレストラン in FUKUOKA」(until=2026-09-23 / 福岡アイランドシティフォーラム)は
#  **ユーザーが手でマップに登録していた**もので、アイランドアイのトピックスには載っていなかった。
#  自分で登録した until / campaign 付きスポットは**最も質の高い情報源**なので源に加える。
SPOTS = os.path.join(HERE, '..', 'data', 'spots.json')


def from_spots():
    rows = []
    try:
        sp = json.load(io.open(SPOTS, encoding='utf-8'))
    except Exception as ex:
        print('  ! spots.json %s' % type(ex).__name__, file=sys.stderr)
        return rows

    def dt(x):
        try:
            return datetime.strptime(x, '%Y-%m-%d').date()
        except Exception:
            return None
    for s in sp:
        # ⚠**until だけを採る**。campaign(常設店のコラボ)は「おでかけイベント」ではなく、
        #   同じキャンペーンが多店舗に登録されているので12選が
        #   モスバーガー3件で埋まった(2026-09-13に踏んだ)。
        #   until = スポット自体が期間限定 = 企画展・単発イベント なのでこれが正しい
        end = dt(s.get('until') or '')
        if not end:
            continue
        # 福岡の投稿なので県外(山口・佐賀のジブリ展等)は出さない
        if (s.get('pref') or '福岡県') != '福岡県':
            continue
        rows.append({'src': 'マップ登録', 'title': s.get('name', ''),
                     'city': s.get('city') or '', 'venue': s.get('name') or '',
                     'url': 'https://lunaseiya.github.io/fukuoka-gourmet-map/#spot=' + s.get('id', ''),
                     # 開始日は持っていないので「ずっと前から」として扱う(会期の重なり判定用)
                     # 開始日は持っていないので「ずっと前から」として重なり判定する。
                     # 表示では nostart を見て「◯/◯まで」と出す
                     'span': (date(2000, 1, 1), end), 'days_list': None, 'nostart': True,
                     'raw': s.get('untilLabel') or camp.get('untilLabel') or '',
                     'free': False, 'lead': (s.get('verdict') or '')[:120],
                     'place': s.get('name'), 'poster': None, 'from_map': True})
    print('  マップ登録(期間限定) %d件' % len(rows), file=sys.stderr)
    return rows


# ──────────────────── クロスロードふくおか(県公式) ────────────────────
PREF_TH = re.compile(r'<th[^>]*>([\s\S]{0,40}?)</th>\s*<td[^>]*>([\s\S]{0,400}?)</td>')
CITY = re.compile(r'福岡県\s*([^\s0-9０-９]{2,6}?(?:市[^\s0-9]{0,4}区|市|郡[^\s0-9]{2,5}町|郡[^\s0-9]{2,5}村|町|村))')


def pref_detail(url):
    """県公式の個別ページから会場情報を取る【2026-09-13 実装】

    一覧タイルにはタイトルと会期しか無く、**市区が空のまま**だったので
    検索ワードが「いっしょにワクワクしよう」のように弱くなっていた(ユーザー指摘)。
    詳細ページは <th>ラベル</th><td>値</td> の表で、次が取れる:
      住所(〒付き) / 電話番号 / 開催日 / 駐車場 / アクセス情報 / ウェブサイト
    ⚠**ウェブサイトは <td> が空で、値はリンクの href にある**ので別途拾う"""
    try:
        h = M.fetch(url)
    except Exception:
        return {}
    tbl = {n(k): n(v) for k, v in PREF_TH.findall(h)}
    d = {}
    ad = tbl.get('住所', '')
    if ad:
        d['addr'] = ad
        m = CITY.search(ad)
        if m:
            d['city'] = m.group(1)
        # 住所の末尾が会場名になっていることが多い(「…浅野2-14-5 あるあるCity5F」)。
        # ⚠文字クラスで番地を削ると「番地」の"地"が効いて**地行浜→行浜**のように
        #   町名の頭を1文字食う(2026-09-13に踏んだ)。町名+番地をまとめて1回で削る
        t = re.sub(r'^〒[0-9\-]+\s*', '', ad)
        t = re.sub(r'^福岡県\s*', '', t)
        t = re.sub(r'^[^\s0-9]{2,6}?(?:市[^\s0-9]{0,4}区|市|郡[^\s0-9]{2,5}[町村]|町|村)', '', t).strip()
        tail = re.sub(r'^[^\s]*?[0-9０-９][0-9０-９\-−ー丁目番地号の]*\s*', '', t).strip() or t
        if len(tail) >= 2 and not re.fullmatch(r'[0-9０-９\-\sFf階]+', tail):
            d['place'] = tail[:24]
    if tbl.get('駐車場'):
        d['park'] = tbl['駐車場'][:24]
        # 「約20台（平原歴史公園）」のように括弧内が会場名のことがある
        m = re.search(r'[（(]([^）)]{2,20})[）)]', tbl['駐車場'])
        if m and not d.get('place'):
            d['place'] = m.group(1)
    if tbl.get('電話番号'):
        m = re.search(r'([0-9][0-9\-]{8,13})', tbl['電話番号'])
        if m:
            d['tel'] = m.group(1)
    if tbl.get('開催日'):
        d['raw'] = tbl['開催日']
    # ウェブサイト(公式)は href から。キャプションはこちらを出したほうが親切
    m = re.search(r'ウェブサイト[\s\S]{0,300}?href="(https?://[^"]+)"', h)
    if m and 'crossroadfukuoka.jp' not in m.group(1):
        d['official'] = m.group(1)
    return d
def from_pref():
    rows = []
    try:
        tiles = X.collect_tiles()
    except Exception as ex:
        print('  ! 県公式 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    ended = 0
    for v in tiles.values():
        s, e, days = jspan(v['span_raw'])
        if s == 'ended':
            ended += 1
            continue
        rows.append({'src': '県公式', 'title': v['title'], 'city': '', 'venue': '',
                     'url': v['url'], 'span': (s, e), 'days_list': days,
                     'raw': v['span_raw'], 'free': False,
                     'lead': v.get('desc', ''), 'poster': v.get('img')})
    if ended:
        print('  (終了済みの表記 %d件を除外)' % ended, file=sys.stderr)
    return rows


# ───────────── 百貨店【2026-09-16追加】────────────────────────
#  ユーザーの持ち込み(9月の連休の実イベント12件)と突合したら、
#  **百貨店の催事が1件も拾えていなかった**(ちいかわぽけっと POP UP STORE /
#  星のカービィ デデデ★デパート = どちらも大丸福岡天神店 本館8階催場)。
#  ユーザーいわく「大丸は**肉フェスや北海道展**みたいなこともやってた記憶」= 催事は継続的にある。
#
#  ⚠**大丸は全社サイト www.daimaru.co.jp が bot 遮断(403)で取れない**。
#    ブラウザで開くと 403 ではなく 404 が返る = URL が違うだけで、実体は
#    **店舗の独自ドメイン www.daimaru-fukuoka.jp**。こちらは素の urllib で 200 が返る。
#    (ヘッダを完全にブラウザ風にしても www.daimaru.co.jp は 403 のまま。WAF のTLS判定なので
#     ヘッダでは越えられない。**手動しかない、ではなく別ドメインを見るのが正解**)
#  構造:
#    <section class="event-contents" id="itemNNNN">
#      <div class="floor-ttl"><p>本館8階催場</p></div>
#      <ul class="event-list">
#        <li><a href="URL"><div class="img-area"><img src="..."></div>
#            <div class="title">タイトル</div><div class="date">9月2日(水)～9月21日(月)</div></a></li>
#  ⚠date に**年が入っていない**ので jspan の年推定に任せる(基準日から3ヶ月以上前なら翌年)
DMF = 'https://www.daimaru-fukuoka.jp'
DMF_SEC = re.compile(r'<section class="event-contents"[\s\S]*?floor-ttl"><p>([\s\S]*?)</p>'
                     r'([\s\S]*?)</section>')
DMF_LI = re.compile(r'<li>\s*<a href="([^"]+)"([\s\S]*?)</a>\s*</li>')


def from_daimaru():
    rows = []
    try:
        h = M.fetch(DMF + '/eventinformation/')
    except Exception as ex:
        print('  ! 大丸福岡天神 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    for floor, body in DMF_SEC.findall(h):
        for url, b in DMF_LI.findall(body):
            ti = re.search(r'class="title">([\s\S]*?)</div>', b)
            dt = re.search(r'class="date">([\s\S]*?)</div>', b)
            im = re.search(r'<img[^>]+src="([^"]+)"', b)
            if not ti:
                continue
            a, e, days = jspan(n(dt.group(1)) if dt else '')
            if a == 'ended':
                continue
            rows.append({'src': '大丸福岡天神', 'title': n(ti.group(1)),
                         'city': '福岡市中央区', 'venue': '大丸福岡天神店',
                         'place': n(floor), 'url': url if url.startswith('http') else DMF + url,
                         'span': (a, e), 'days_list': days,
                         'raw': n(dt.group(1)) if dt else '', 'free': False, 'lead': '',
                         'poster': (im.group(1) if im.group(1).startswith('http')
                                    else DMF + im.group(1)) if im else None})
    print('  大丸福岡天神 %d件' % len(rows), file=sys.stderr)
    return rows


#  博多阪急。1週間ごとの見出し + <article> の繰り返し。
#    <p class="o-event-list__title">9月16日（水）～9月22日（火・休日）</p>
#    <article><div class="o-event" data-place="sj"><a href="URL"><figure><img src="..."></figure>
#      <div class="o-event__inner"><p class="o-event__title">タイトル</p></div></a>
#      <div class="o-event__detail o-event__inner"><p>●9月17日（木）～22日（火・休日）<br>●8階 催場</p>
#  ⚠会期は**o-event__detail の最初の <p>** から取る。o-event-list__title は
#    「その週の一覧」の見出しなので、個別イベントの会期ではない
HKQ = 'https://www.hankyu-dept.co.jp'
HKQ_ART = re.compile(r'<article>([\s\S]*?)</article>')


def from_hankyu():
    rows = []
    try:
        h = M.fetch(HKQ + '/hakata/event/')
    except Exception as ex:
        print('  ! 博多阪急 %s' % type(ex).__name__, file=sys.stderr)
        return rows
    seen = set()
    for b in HKQ_ART.findall(h):
        ti = re.search(r'o-event__title">([\s\S]*?)</p>', b)
        de = re.search(r'o-event__detail[^>]*>\s*<p>([\s\S]*?)</p>', b)
        u = re.search(r'<a href="([^"]+)"', b)
        im = re.search(r'<img[^>]+src="([^"]+)"', b)
        if not ti:
            continue
        # ⚠一覧の見出し(「9月16日（水）～22日（火・休日）の博多阪急イベント」
        #   「9〜10月の博多阪急イベント一覧」)も <article> に入っている。**イベントではない**
        if re.search(r'の博多阪急イベント|イベント一覧', n(ti.group(1))):
            continue
        url = (u.group(1) if u else HKQ + '/hakata/event/')
        if url in seen:
            continue
        seen.add(url)
        raw = n(re.sub(r'<br\s*/?>', ' / ', de.group(1))) if de else ''
        a, e, days = jspan(raw)
        if a == 'ended':
            continue
        # 「● 8階 催場」の部分を place に回す(会場の階)
        pl = ''
        for part in raw.split('/'):
            if re.search(r'\d+階|催場|ホール', part):
                pl = part.strip(' ●')
                break
        rows.append({'src': '博多阪急', 'title': n(ti.group(1)),
                     'city': '福岡市博多区', 'venue': '博多阪急', 'place': pl,
                     'url': url, 'span': (a, e), 'days_list': days,
                     'raw': raw, 'free': False, 'lead': '',
                     'poster': (im.group(1) if im and im.group(1).startswith('http') else None)})
    print('  博多阪急 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── よかなび(福岡市公式観光)【2026-09-16追加】─────────
#  **福岡市内の公園・広場で開かれる民間イベント**の源。イオン系・県公式のどちらにも出てこない。
#  取りこぼしていた「第3回福岡からあげフェス2026(舞鶴公園 三の丸広場)」がここにある。
#  構造:
#    <div class="card-list__item" data-rspec="event"><div class="card">
#      <a class="card-img" href="/events/NNNN"><img src="..."></a>
#      <a class="card-title" href="/events/NNNN"> タイトル </a>
#      <div class="card-description">…</div>
#      <p class="card-period"><span class="icon">…</span><span class="txt">会期</span></p>
#      <div class="card-area"><div class="card-area-list"><a class="txt">…エリア</a></div></div>
#  ⚠`<svg>` が大量に埋まっているので**先に svg を落とす**。class の抽出が svg 側に当たる
#  ⚠card-period は**「●本祭」「●前夜祭」の複数ブロック**が <br> で並ぶ。
#    そのまま jspan に渡すと日付が3つ以上になり「特定日リスト」と誤判定され、
#    **連続開催の中日(9/21)が抜ける**。→ 最初の日付を含むブロックだけを取り、
#    さらに「※」以降(注記)を落としてからレンジとして読む
YOKA = 'https://yokanavi.com'
YOKA_CARD = re.compile(r'<div class="card-list__item" data-rspec="event">'
                       r'([\s\S]*?)(?=<div class="card-list__item"|</section>)')


def yoka_span(txt):
    t = re.sub(r'<br\s*/?>', ' ', txt)
    t = n(t)
    for part in [p for p in t.split('●') if re.search(r'\d{1,2}月\s*\d{1,2}日', p)]:
        return jspan(part.split('※')[0])
    return jspan(t.split('※')[0])


def from_yokanavi(maxpage=3):
    rows = []
    for pg in range(1, maxpage + 1):
        u = YOKA + '/event/' + ('' if pg == 1 else '?page=%d' % pg)
        try:
            h = re.sub(r'<svg[\s\S]*?</svg>', '', M.fetch(u))
        except Exception as ex:
            print('  ! よかなび %s %s' % (u, type(ex).__name__), file=sys.stderr)
            break
        got = 0
        for b in YOKA_CARD.findall(h):
            ti = re.search(r'class="card-title" href="([^"]+)">([\s\S]*?)</a>', b)
            pe = re.search(r'class="card-period">([\s\S]*?)</p>', b)
            de = re.search(r'class="card-description">([\s\S]*?)</div>', b)
            ar = re.search(r'card-area-list">\s*<a[^>]*>([\s\S]*?)</a>', b)
            im = re.search(r'class="card-img"[\s\S]{0,200}?src="([^"]+)"', b)
            if not ti:
                continue
            a, e, days = yoka_span(pe.group(1)) if pe else (False, False, None)
            if a == 'ended':
                continue
            rows.append({'src': 'よかなび', 'title': n(ti.group(2)),
                         'city': '福岡市', 'venue': n(ar.group(1)) if ar else '',
                         'url': YOKA + ti.group(1), 'span': (a, e), 'days_list': days,
                         'raw': n(pe.group(1)) if pe else '', 'free': False,
                         'lead': n(de.group(1))[:260] if de else '',
                         'poster': im.group(1) if im else None})
            got += 1
        print('  よかなび %dページ目 +%d (累計%d)' % (pg, got, len(rows)), file=sys.stderr)
        if not got:
            break
        time.sleep(M.WAIT)
    return rows


# ───────── 久留米公式観光「ほとめきの街」【2026-09-16追加】─────────
#  ⚠**県公式(クロスロードふくおか)の久留米は会期が去年のまま**のことがある
#    (「久留米市城島 ふるさと夢まつり」が 2025年9月20日・21日 と書かれていた。実際は2026年9月19-20日)。
#    久留米の一次情報はこちらを見る。
#  ⚠ドメインは **welcome-kurume.com**。`kurume-hotomeki.jp` は別会社のページが出る(タイトルが
#    「株式会社ナレッジソースワークス」)。踏まないこと。
#  構造:
#    <li><a href="/events/detail/UUID"><figure class="pht-contain">…<img src="…"></figure></a>
#      <div class="txt"><span class="link-event"><a href="…">タイトル</a></span>
#        <span class="spot-areaNN">エリア</span>
#        <span class="event-date"> 2026年9月19日(土)･20日(日)<br>… </span>
#  ⚠会期の中点が**半角カタカナ中点「･」(U+FF65)**。jspan は NFKC を通すので「・」になり
#    DAY_MORE が拾える(2026-09-16に実測で確認)
KRM = 'https://welcome-kurume.com'
KRM_LI = re.compile(r'<li>\s*<a href="(/events/detail/[^"]+)"([\s\S]*?)</li>')


def from_kurume(maxpage=3):
    rows = []
    seen = set()
    for pg in range(1, maxpage + 1):
        u = KRM + '/events' + ('' if pg == 1 else '?page=%d' % pg)
        try:
            h = M.fetch(u)
        except Exception as ex:
            print('  ! 久留米観光 %s %s' % (u, type(ex).__name__), file=sys.stderr)
            break
        got = 0
        for url, b in KRM_LI.findall(h):
            if url in seen:
                continue
            ti = re.search(r'class="link-event"><a[^>]*>([\s\S]*?)</a>', b)
            dt = re.search(r'class="event-date">([\s\S]*?)</span>', b)
            ar = re.search(r'class="spot-area\d+">([\s\S]*?)</span>', b)
            im = re.search(r'<img src="([^"]+)"', b)
            if not ti:
                continue
            seen.add(url)
            raw = n(re.sub(r'<br\s*/?>', ' ', dt.group(1))) if dt else ''
            a, e, days = jspan(raw)
            if a == 'ended':
                continue
            rows.append({'src': '久留米観光', 'title': n(ti.group(1)),
                         'city': '久留米市', 'venue': n(ar.group(1)) if ar else '久留米市',
                         'url': KRM + url, 'span': (a, e), 'days_list': days,
                         'raw': raw, 'free': False, 'lead': '',
                         'poster': (KRM + im.group(1)) if im else None})
            got += 1
        print('  久留米観光 %dページ目 +%d (累計%d)' % (pg, got, len(rows)), file=sys.stderr)
        if not got:
            break
        time.sleep(M.WAIT)
    return rows


# ⚠**キャナルシティの「期間限定ショップ」は源にできない**【2026-09-16に実測して断念】
#   ユーザー要望で「テレ東本舗。WITH テレQ」(2026/9/18〜2027/2/7)を拾えるようにしようとしたが、
#   ①`/event` の一覧に入らない(あれは**イベント**枠。テレ東はトップのカルーセルにだけ出て
#     リンク先は `/shop/detail/10510404` = **ショップ**枠)
#   ②`/shopnews`(20件)は店舗の販促ブログで**会期を持たない**(「新作入荷」「ダイヤモンドネックレス」等)
#   ③`/shopsearch`(191店)は店名一覧で会期なし
#   ④**個別の `/shop/detail/…` を開いても会期が書かれていない**(本文に「期間限定出店」とあるだけで
#     2027/2/7 の文字列がページ内に存在しない)
#   → 会期が取れないものは登録できない(推測で埋めない)ので、**期間限定ショップは追わない**。
#     もっとも、5か月弱の会期は `left > 90` で -6点が付く「実質常設」扱いなので、
#     週次告知の趣旨からも外れている。


# ───────────────────────── 商業施設 ─────────────────────────
def from_mall():
    rows = []
    for r in M.collect():
        rows.append({'src': r['mall'], 'title': r['title'], 'city': r['city'],
                     'venue': r['mall'], 'url': r['url'], 'span': r['span'],
                     'raw': r['info'], 'free': False, 'lead': '',
                     'poster': r.get('poster'), 'kyushu': r.get('kyushu')})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='f')
    ap.add_argument('--to', dest='t')
    ap.add_argument('--n', type=int, default=12)
    ap.add_argument('--src', default='mall,lala,canal,icp,ie,kgk,map,ikoyo,pref,'
                                     'daimaru,hankyu,yokanavi,kurume,torius,hkc,manual')
    ap.add_argument('--detail', action='store_true', help='採用分の個別ページも開く(商業施設のみ)')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()

    if a.f:
        f = datetime.strptime(a.f, '%Y-%m-%d').date()
    else:
        today = date.today()
        f = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    t = datetime.strptime(a.t, '%Y-%m-%d').date() if a.t else f + timedelta(days=1)
    srcs = [s.strip() for s in a.src.split(',')]
    print('対象期間: %s 〜 %s / 情報源: %s' % (f, t, ' '.join(srcs)), file=sys.stderr)

    rows, per = [], {}
    for s, fn in (('mall', from_mall), ('lala', from_lalaport), ('canal', from_canal),
                  ('icp', from_iccentral), ('ie', from_islandeye),
                  ('kgk', from_kagakukan), ('map', from_spots),
                  ('ikoyo', lambda: from_ikoyo(f, t)), ('pref', from_pref),
                  # 【2026-09-16追加】百貨店2館 + 福岡市の公園/広場 + 久留米
                  ('daimaru', from_daimaru), ('hankyu', from_hankyu),
                  ('yokanavi', from_yokanavi), ('kurume', from_kurume),
                  # 【2026-09-17追加】トリアス久山(糟屋郡久山町)。日付がISOで最も確実
                  ('torius', from_torius),
                  # 【2026-09-17追加】JR博多シティ こどもCITY(屋上つばめの杜ひろば)。
                  # 月次で子連れイベントを回している、この源で一番濃いところ
                  ('hkc', from_hakatacity),
                  # 公式にイベント一覧が無い主催のぶん(現地チラシから手で書く)
                  ('manual', from_manual)):
        if s in srcs:
            print('[%s] 収集中...' % s, file=sys.stderr)
            got = fn()
            per[s] = len(got)
            rows += got
    print('生データ 合計 %d件 %s' % (len(rows), per), file=sys.stderr)

    # ⚠会期が読めなかったものは落としている(推測しない)。何件落ちたかは必ず出す。
    #   県公式は年間のイベントが並ぶので、会期が読めないと丸ごと消える
    unread = [r for r in rows if r['span'][0] is False]
    if unread:
        bysrc = {}
        for r in unread:
            bysrc[r['src']] = bysrc.get(r['src'], 0) + 1
        print('会期が読めず除外: %d件 %s' % (len(unread), bysrc), file=sys.stderr)
    def in_window(r):
        dl = r.get('days_list')
        if dl:            # 特定日の列挙はレンジで見ない(「3月〜11月の第2日曜」を毎日扱いしない)
            return any(f <= d <= t for d in dl)
        return M.overlaps(r['span'], f, t)
    inwin = [r for r in rows if in_window(r)]

    def drop_it(r):
        s = re.sub(r'[\s　]+', '', r['title'])
        if M.DROP_HARD.search(s):      # 子連れ語でも救わない区分(旅行商品・募集等)
            return True
        return bool(M.DROP.search(s)) and not M.SAVE.search(s)
    dropped = [r for r in inwin if drop_it(r)]
    keep = [r for r in inwin if not drop_it(r)]
    print('会期が対象期間にかかる %d件 → 除外 %d件 → %d件'
          % (len(inwin), len(dropped), len(keep)), file=sys.stderr)

    grp = {}
    for r in keep:
        grp.setdefault(M.norm_title(r['title']), []).append(r)

    # ⚠タイトル正規化だけでは**同じイベントの表記違い**を束ねられない(2026-09-13に踏んだ)。
    #   「【BOSS E・ZO FUKUOKA 】魔法の美術館」/「魔法の美術館」/
    #   「【福岡】BOSS E・ZO FUKUOKAで「魔法の美術館」開催！」が3件に分かれて3枠を占めた。
    #   **会期が完全に一致し、かつタイトルに5文字以上の共通部分がある**ものを2段目で束ねる
    def core(t):
        return re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ヶー]', '', t)

    def common_run(a, b, need=6):
        """共通部分文字列が need 文字以上あるか。
        ⚠5文字だと「ワークショップ」等の一般語で**無関係なイベントが誤結合**する。
          6文字 + 同一市区 + 同一会期 の3条件をそろえて初めて同一とみなす。
          ⚠7文字にしていたら「筥崎宮放生会」(6文字)が いこーよ版/県公式版で束ならず、
            同じ祭りが2件に分かれて票が割れていた(2026-09-13に踏んだ)"""
        a, b = core(a), core(b)
        if len(a) > len(b):
            a, b = b, a
        for ln in range(len(a), need - 1, -1):
            for i in range(len(a) - ln + 1):
                if a[i:i + ln] in b:
                    return True
        return False

    keys = list(grp)
    merged_keys = {}
    for i, k1 in enumerate(keys):
        if k1 in merged_keys:
            continue
        for k2 in keys[i + 1:]:
            if k2 in merged_keys:
                continue
            r1, r2 = grp[k1][0], grp[k2][0]
            c1, c2 = r1.get('city') or '', r2.get('city') or ''
            # ⚠**市区は前方一致も同一とみなす**【2026-09-16に発覚】
            #   源によって粒度が違う。いこーよは「福岡市東区」、よかなびは「福岡市」。
            #   完全一致だけで見ていたため、**筥崎宮 放生会が会期完全一致・タイトル共通6文字
            #   なのに束ならず、12枠のうち2枠を同じ祭りで使っていた**
            #   (#1 いこーよ/マップ score31 と #6 よかなび score25)。
            same_city = (not (c1 and c2) or c1 == c2
                         or c1.startswith(c2) or c2.startswith(c1))
            # ⚠**開始日が不明(nostart)なものは終了日だけで会期一致を見る**(同日に発覚)
            #   マップ登録の until 持ちスポットは開始が無いので span が
            #   (None, 終了) になり、同じイベントのいこーよ版と一致しなかった
            #   (アクティブ・キッズ-LABO- が 朝倉市で2枠を使っていた)
            if r1.get('nostart') or r2.get('nostart'):
                same_span = r1['span'][1] == r2['span'][1]
            else:
                same_span = r1['span'] == r2['span']
            if same_span and same_city and common_run(k1, k2):
                print('  束ね: %s ← %s' % (k1[:26], k2[:26]), file=sys.stderr)
                grp[k1] += grp[k2]
                merged_keys[k2] = k1
    for k in merged_keys:
        grp.pop(k, None)
    if merged_keys:
        print('表記違いで束ねた: %d件' % len(merged_keys), file=sys.stderr)
    merged = []
    for k, v in grp.items():
        # ⚠代表を v[0] にすると、先に入った**情報の薄い側**(集約サイトの短いタイトル)が
        #   採用されてスコアも下がる。ポスター有無→リードの長さ→タイトルの長さで選ぶ
        v = sorted(v, key=lambda x: (bool(x.get('poster')), len(x.get('lead') or ''),
                                     len(x.get('title') or '')), reverse=True)
        r = dict(v[0])
        r['venues'] = sorted({x['venue'] or x['src'] for x in v})
        r['srcs'] = sorted({x['src'] for x in v})
        d = M.run_days(r['span'])
        r['days'] = d
        # ⚠**終わりが遠すぎるものは「期間限定」の趣旨に合わない**(2026-09-13ユーザー指摘)。
        #   「ポップジェット噴水ショー(4/25〜翌3/31)」のような通年の常設プログラムが
        #   上位に来ていた。会期の長さではなく**終了までの残り日数**で減点する
        e, st = r['span'][1], r['span'][0]
        left = (e - date.today()).days if hasattr(e, 'year') else 9999
        # **始まってからの日数**。負なら「これから始まる」
        since = (date.today() - st).days if hasattr(st, 'year') else 9999
        r['left'], r['since'] = left, since
        # ★**ポスターを読んで付けた加点**を足す【2026-09-16ユーザー確定の新工程】
        #   ⚠**スコアはタイトルの文字列だけで計算していて、商業施設の源は lead が空**なので、
        #     価値がポスターにしか書かれていないものは0点になる。
        #     実測(9/19-23の候補172件)では score<=8 が64件あり、うち**63件はポスター画像を持っていた**。
        #     61枚読んだら**3件が大当たり**だった:
        #       「シルバーウィークナイトシネマ」8→28(4夜すべて子供向けアニメの野外上映・入場無料)
        #       「電車と遊ぼう!!ワイワイ鉄道まつり」7→23(ミニ新幹線に乗れる・プラレールで遊べる)
        #       「ポケモンカードストア」8→18(無料のポケカ教室を毎日開催)
        #   → 読んだ結果は `data/_イベント補足.json` の **`kids_add`** に保存し、ここで足す。
        #     0 を入れてあるものは「読んだが加点しないと判断した」記録(再読の無駄を省く)
        r['kids_add'] = int((SUPP.get(r['url']) or {}).get('kids_add') or 0)
        r['score'] = (M.kids_score(r['title'] + ' ' + (r.get('lead') or ''))
                      + r['kids_add']
                      + (4 if d <= 3 else 2 if d <= 9 else 0)
                      + (2 if len(r['venues']) >= 3 else 0)
                      # ★**複数の情報源に載っている=規模が大きい**という代理指標。
                      #   固有名をハードコードしなくても大型行事を拾える
                      + (5 if len(r.get('srcs') or []) >= 2 else 0)
                      + (2 if r.get('free') else 0)
                      + (3 if 0 <= left <= 7 else 0)      # 今週で終わる=行く理由が強い
                      # ★**はじまりたては加点**【2026-09-13ユーザー指摘。それまで入れていなかった】
                      #   始まった直後は他がまだ投稿していない=情報としての新規性がある。
                      #   これから始まるもの(negative since)も告知価値があるので同じ枠で見る
                      + (3 if -7 <= since <= 7 else 1 if 8 <= since <= 14 else 0)
                      # ★**自分でマップに登録した期間限定スポットは下駄を履かせる**
                      #   (載せる価値があると自分で判断済みのもの。最も質が高い情報源)
                      + (5 if r.get('from_map') else 0)
                      - (6 if left > 90 else 0))          # 実質常設は落とす
        merged.append(r)
    # スコアが0以下になったもの(実質常設・販促)は採用しない
    merged = [r for r in merged if r['score'] > 0]
    # ★**「見るだけの展示」は子連れのおでかけとして弱い**【2026-09-13ユーザー指摘】
    #   「杉本さなえ個展『こどもとまほう』」が、タイトルの"こども"だけで+6点入って8位にいた。
    #   実態は駐車場2台の小さなギャラリーの個展で、子供が遊べるものではない。
    #   個展/作品展/成果展/写真展 のような**鑑賞のみの発表系は減点**する。
    #   ただし「体験」「参加型」「さわれる」等があるものは体験型なので減点しない
    #   (「こどもの視展〜こどもになる12の体験〜」「パンダコパンダ展(体験型展覧会)」は残す)
    # ⚠語を1つずつ足すと必ず漏れる(「イラスト展」「にがお絵展」「似顔絵展」で漏れた)。
    #   **「◯◯展」を包括で取り、体験型だけ救う**形にする(展望/展開 等は除外)
    MITAKE = re.compile(r'展(?![望開開示会性])|個展|作品展|成果展|ギャラリー')
    TAIKEN = re.compile(r'体験|参加型|さわれる|触れ|遊べる|遊ぼう|ワークショップ|つくろう|作ろう')
    for r in merged:
        blob = re.sub(r'[\s　]+', '', r['title'] + (r.get('lead') or ''))
        if MITAKE.search(blob) and not TAIKEN.search(blob):
            r["score"] -= 8
            r['note_mitake'] = True
    merged = [r for r in merged if r['score'] > 0]
    merged.sort(key=lambda r: (-r['score'], M.run_days(r['span'])))

    # ★情報源ごとに持ち回りで採る【2026-09-12】
    #   純粋なスコア順にすると**いこーよが10/12を占めて、地元の祭りが全部落ちる**。
    #   「秋季大祭」「かすり祭」は子連れ語を持たないのでスコア8止まりだが、
    #   モールにもいこーよにも出てこない**その地域だけの行事**で、記事としては一番強い。
    #   ゆめはぴの12選も会場が宗像/福岡/香椎浜/粕屋/福津/久留米/柳川に散っていた。
    #   なので **源をラウンドロビンで回し、同じ市区も2件までに抑える**
    def pick(cands, want, per_city=2, minscore=5, top_slots=3):
        # ⚠源のラウンドロビンは**その源に良いものが無くても1枠使ってしまう**。
        #   スコア1の販促(「オープニング記念キャンペーン」)が入っていたので下限を設ける
        cands = [r for r in cands if r['score'] >= minscore] or cands
        # ★**先頭 top_slots 枠は「源を問わずスコア上位」で埋める**【2026-09-16ユーザー確定】
        #   源が13に増えた結果、**12枠に対して13バケツ=1源1枠でラウンドロビンが飽和し、
        #   スコアが選抜にほぼ効かなくなった**。実害:
        #     採用8枠目 = ちいかわPOP UP(score 9) / 4枠目 = 走り方教室(score 15)
        #     採用外    = わっしょい百万夏まつり(score 19・第39回・2日間・2源掲載)
        #   「各源の1位が無条件で入る」ので、**規模の大きい行事が小さい販促に負ける**。
        #   → 上位3枠だけスコアで確定させ、残りは従来どおりラウンドロビンにする。
        #     源の散らしは9枠で十分に効く(ゆめはぴの12選も会場は7〜8市区に散っていた)。
        #   ⚠**市区上限はこの3枠にも数える**。同じ市区の大型行事3連発を防ぐため
        out, city = [], {}
        head = set()
        for r in cands[:]:                       # cands はスコア降順で渡ってくる
            if len(out) >= min(top_slots, want):
                break
            c = r.get('city') or ''
            if c and city.get(c, 0) >= per_city:
                continue
            if c:
                city[c] = city.get(c, 0) + 1
            out.append(r)
            head.add(r['url'])
        cands = [r for r in cands if r['url'] not in head]

        # 商業施設は館ごとに分かれるので1束にまとめる
        mall = [r for r in cands if r['src'].startswith('イオン')]
        others = {}
        for r in cands:
            if not r['src'].startswith('イオン'):
                others.setdefault(r['src'], []).append(r)
        order = [('商業施設', mall)] + sorted(others.items())
        while len(out) < want and any(v for _, v in order):
            for _, v in order:
                while v:
                    r = v.pop(0)
                    if r['url'] in head:        # 上位3枠で既に採ったもの
                        continue
                    # ⚠**city が空のものを '?' でまとめてはいけない**【2026-09-16に発覚】
                    #   県公式(クロスロードふくおか)は一覧に市区が出ないので city='' になる。
                    #   '?' に寄せると**県公式の全件が1つのバケツ**になり、
                    #   per_city=2 が「県公式は2件まで」として効いてしまっていた。
                    #   実害: 「わっしょい百万夏まつり」(北九州の第39回・2日間・2源掲載/score19)が
                    #   宮地嶽神社と他1件に枠を取られ、score20未満なので上限も超えられず落ちていた。
                    #   市区上限は**地域を散らすため**のものなので、市区が不明なものは対象外にする
                    c = r.get('city') or ''
                    if not c:
                        out.append(r)
                        break
                    # ⚠市区の上限が**大型行事を弾いていた**(2026-09-13)。
                    #   「筥崎宮 放生会」(21点/博多三大祭り)が、福岡市東区の枠を
                    #   キッズモデル体験とチン!するレストランに取られて入れなかった。
                    #   **スコア20以上は上限を超えてよい**(それだけ強いものは載せるべき)
                    if city.get(c, 0) >= per_city and r['score'] < 20:
                        continue
                    city[c] = city.get(c, 0) + 1
                    out.append(r)
                    break
                if len(out) >= want:
                    break
        return out
    top = pick(list(merged), a.n) if len(srcs) > 1 else merged[:a.n]

    if a.detail:
        print('採用%d件の個別ページを開いています...' % len(top), file=sys.stderr)
        for r in top:
            if r['src'] == 'いこーよ':
                r.update(iko_detail(r['url'])); time.sleep(M.WAIT)
            elif r['src'] == '県公式':
                r.update(pref_detail(r['url'])); time.sleep(M.WAIT)
            elif r.get('kyushu'):
                r.update(M.detail(r)); time.sleep(M.WAIT)

    def span_str(r):
        s, e = r['span']
        if r.get('nostart') and e:
            w = '月火水木金土日'
            return '〜%d/%d(%s)まで' % (e.month, e.day, w[e.weekday()])
        if s is None:
            return '毎日'
        w = '月火水木金土日'
        return ('%d/%d(%s)' % (s.month, s.day, w[s.weekday()]) if s == e else
                '%d/%d(%s)〜%d/%d(%s)' % (s.month, s.day, w[s.weekday()],
                                          e.month, e.day, w[e.weekday()]))

    print()
    print('=== %s〜%s の週末イベント %d選 (候補%d件から) ===' % (f, t, len(top), len(merged)))
    for i, r in enumerate(top, 1):
        v = r['venues'][0] if len(r['venues']) == 1 else '%s ほか%d会場' % (r['venues'][0], len(r['venues']) - 1)
        print('%2d. [%s] %s' % (i, '/'.join(r['srcs'])[:14], r['title']))
        print('    📍%s%s  📅%s  スコア%d%s'
              % (v, ('(%s)' % r['city']) if r['city'] else '', span_str(r), r['score'],
                 '  ¥無料' if r.get('free') else ''))
        for k, lb in (('time', '🕐'), ('price', '¥'), ('place', '📌'), ('addr', '🏠'),
                      ('park', '🅿'), ('access', '🚃'), ('tel', '☎'), ('note', 'ℹ')):
            if r.get(k):
                print('    %s %s' % (lb, r[k]))
        if r.get('lead'):
            print('    « %s' % r['lead'][:74])
        if r.get('poster'):
            ok = poster_ok(r['title'], r.get('lead'))
            print('    🖼 %s %s' % ('貼ってOK' if ok else '⚠IP絡み→貼らない', r['poster'][:88]))
        elif not r.get('poster'):
            print('    🖼 ポスター画像URL未取得')
        print('    %s' % r['url'])
    if a.all:
        print()
        print('--- 除外ルールで落とした %d件 ---' % len(dropped))
        for r in dropped:
            print('  x [%s] %s' % (r['src'][:10], r['title'][:52]))
        print()
        print('--- 残ったが下位 %d件 ---' % max(0, len(merged) - len(top)))
        for r in merged[len(top):]:
            print('  - [%2d][%s] %s' % (r['score'], r['src'][:10], r['title'][:50]))

    for r in merged:
        s, e = r['span']
        r['span'] = [s.isoformat() if s else None, e.isoformat() if e else None]
        # ⚠date は json に直接書けない。特定日リストもISO文字列に落とす(2026-09-12に踏んだ)
        if r.get('days_list'):
            r['days_list'] = [d.isoformat() for d in r['days_list']]
    # ⚠**採用した12件(ラウンドロビン後)の順番を保存する**。
    #   merged はスコア順なので、これを保存するだけだとカルーセル側が
    #   源の偏りを直す前の並びを使ってしまう(2026-09-13に踏んだ)
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        {'from': f.isoformat(), 'to': t.isoformat(), 'sources': per,
         'selected': [r['url'] for r in top], 'events': merged},
        ensure_ascii=False, indent=1))
    print()
    print('→ %s に %d件保存' % (os.path.normpath(OUT), len(merged)))


if __name__ == '__main__':
    main()
