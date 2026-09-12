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
    r'ワンピース|呪術廻戦|鬼滅|ハイキュー|スパイファミリー|ウルトラマン|ゴジラ')


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
ENDED = re.compile(r'開催はありません|営業終了|終了しました|中止')
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
    if ENDED.search(t):
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
    ap.add_argument('--src', default='mall,lala,canal,icp,ie,kgk,map,ikoyo,pref')
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
                  ('ikoyo', lambda: from_ikoyo(f, t)), ('pref', from_pref)):
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
            same_city = (r1.get('city') or '') == (r2.get('city') or '') or not (r1.get('city') and r2.get('city'))
            if r1['span'] == r2['span'] and same_city and common_run(k1, k2):
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
        r['score'] = (M.kids_score(r['title'] + ' ' + (r.get('lead') or ''))
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
    def pick(cands, want, per_city=2, minscore=5):
        # ⚠源のラウンドロビンは**その源に良いものが無くても1枠使ってしまう**。
        #   スコア1の販促(「オープニング記念キャンペーン」)が入っていたので下限を設ける
        cands = [r for r in cands if r['score'] >= minscore] or cands
        buckets = {}
        for r in cands:
            buckets.setdefault(r['srcs'][0] if r['src'].startswith('イオン') is False else 'mall',
                               []).append(r)
        # 商業施設は館ごとに分かれるので1束にまとめる
        mall = [r for r in cands if r['src'].startswith('イオン')]
        others = {}
        for r in cands:
            if not r['src'].startswith('イオン'):
                others.setdefault(r['src'], []).append(r)
        order = [('商業施設', mall)] + sorted(others.items())
        out, city = [], {}
        while len(out) < want and any(v for _, v in order):
            for _, v in order:
                while v:
                    r = v.pop(0)
                    c = r.get('city') or '?'
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
