# -*- coding: utf-8 -*-
"""福岡(福岡市・近郊・北九州を含む福岡県)で「これから開業・竣工・供用開始する住宅以外の建物」を集める。
商業施設・ホテル・公園・複合ビル・空港施設などが対象。マンション等の住宅専用は除外する。

  set PYTHONIOENCODING=utf-8
  python tools/opening_watch.py            # 全源を巡回 → data/openings.json に追記 → 近い順に一覧
  python tools/opening_watch.py --list     # 巡回せず、保存済みの openings.json を一覧だけ出す
  python tools/opening_watch.py --list --kind 公園   # 種別で絞る(商業/ホテル/公園/複合/その他)
  python tools/opening_watch.py --deep     # 見出しに日付が無い記事は本文も開いて日付を探す(アクセス数が増える)
  python tools/opening_watch.py --all      # 開業日を過ぎたものも一覧に出す
  python tools/opening_watch.py --areas    # 巡回せず、同じエリアに今日以降の予定が2件以上あるところを近い順に出す

■ エリア集約(area)
  単発の小売は弱いが「同じエリアに2件以上」はまちが変わるサイン(例: 新宮町下府 = 新宮ファッションモール+
  マックスバリュ+ケーズデンキが同時期)。area は「市区町村+町名」程度で、大店立地法の所在地から切り出す
  (福岡県糟屋郡新宮町下府土地区画整理事業15街区 → 糟屋郡新宮町下府)。所在地が無い見出し由来の案件は空のまま
  (名前からは推定しない)。手で入れた area は上書きしない(自動で切り出したものは area_src='auto' が付き、
  切り出しルールを直したら次の実行で計算し直す)。手動シードは所在が明らかなものだけ area を持つ

■ 巡回元と、何が取れて何が取れないか
  1. 福岡市 大規模小売店舗立地法 届出ページ(「新設」の各リンク先)
       取れる : 店名 / 所在地 / 届出日
       取れない: 開店予定日。詳細ページには無く「届出内容(PDF)」の中だが、そのPDFは画像で文字が抜けない
                → **届出日+8か月を推定開店日**として入れる(法律上、届出から8か月は開店できないため最短ライン)
       注意   : 店舗面積1,000㎡超の小売店だけが届出対象。ホテル・公園・飲食専門ビルは載らない。
                掲載は新設届出から縦覧4か月程度。古い届出はページから消える
  2. 福岡県 大規模小売店舗立地法 届出一覧表(daiten<西暦>.html = その年度。福岡市・北九州市・久留米市以外の県内)
       取れる : 店名 / 所在地 / 届出日(「第5条第1項(新設)」の表だけ)
       取れない: 開店予定日(同上。届出日+8か月で推定)
       注意   : 北九州市・久留米市は政令市/中核市で独自ページ。ここには載らない
  3. フクリパ(fukuoka-leapup.jp/biz) 記事一覧 2ページ分
       取れる : 見出し + 見出しに書かれた時期(「2027年春開業へ」等)
       取れない: 見出しに時期が無い記事の時期(--deep で本文を見に行く)
  4. 再開発調査兵団(view.tokyo) 福岡県カテゴリ(?cat=774) 2ページ分
       取れる : 見出し + 抜粋に書かれた時期。撮影日(「2026年5月撮影」)は時期扱いしない
  5. saitoshika-west.com 福岡カテゴリ 2ページ分
       取れる : 見出しに書かれた時期(「【2028年度竣工予定】」等)
  6. 福岡市 記者発表資料(月別ページ、今月から6か月分)
       取れる : PDFの題名に 開園/供用開始/開業/竣工 等を含むもの。PDFが文字PDFなら本文から日付も引く
       取れない: 民間施設の開業(市の発表に載るのは市の公園・市施設が中心)。
                公園の供用開始は数週間前に出ることが多く、「2027年3月」のような長期予定は別途公式サイトで確認
  7. 福岡市「魅力あふれる公園づくり」(Park-PFI 7公園) + 各公園の個別ページ
       取れる : 本文の「令和8年4月には東平尾公園…がオープンしました」「今後も…順次オープンする予定」の文から、
                公園ごとの オープン済み月 / 未定(整備中)。個別ページに供用開始の月があればそれを優先
       取れない: 整備中の公園の具体的な月(市ページは「順次オープン」としか書かない)。
                → 報道ベースの予定は手動シード(SEEDS)で持つ。県営の西公園もシード(plantec のニュース)

■ ウォッチ対象(data/openings_watch.json)
  {"name","aliases":[],"kind","note"} の配列。巡回したページ(見出し・抜粋・記事本文・PDF本文)に name/alias が
  出たら、その近く(前後150文字)の「時期+イベント語」を拾い、openings.json の該当エントリに反映する。
    ・該当エントリ = name が一致(なければ alias を含む)もの。無ければ新規に作る(src='watch')
    ・時期が空か「未定」なら新しい時期で埋める。既に時期があり表記が違えば **history に追記するだけ**
      (古い記事の古い日付で上書きしないため。一覧では ★ と history 件数で分かる)
  見出しに alias があって時期が取れない記事は、本文を開く(1回の実行で最大 WATCH_FETCH_BUDGET 本)

■ 共通の限界
  ・「名前」は見出しから「」『』内を優先して切り出す。無ければ見出しを刈り込んだものなので、手で直す前提
  ・時期は「2027年夏」「2027年3月」「2028年度」のような文字列のまま保存し、並べ替え用に近似日付(ISO)を付ける
      春=4月 / 夏=7月 / 秋=10月 / 冬=12月 / 末=12月 / 年度=翌年3月 / 月不明=7月 / 日不明=1日
      年なし「9月11日」=今年(240日以上前なら来年) / 「来春」「年内」等の相対表記も今日基準で近似
      「未定」は when='未定' のまま持ち、一覧では末尾の「未定・不明」に出す
  ・時期は「イベント語(開業/竣工等)の前後6文字以内」にある日付だけを結び付ける。
      見出しに「2026年5月撮影」のような撮影日があっても時期扱いしない
  ・「開業の4週前」「竣工の2〜3か月前」は近似日付から逆算した目安(撮影・投稿の仕込み時期の当たり)
  ・spots.json には何も書かない。候補を見てマップに載せるかは人が決める

■ 保存先 data/openings.json(追記型、同じ 名前+出典URL は重複させない。手動シードは名前で照合)
  {"name","kind","when","when_iso","event","title","address","src","src_url","found","note","history":[...]}
"""
import io, json, os, random, re, sys, time, unicodedata
from datetime import date, timedelta

import requests

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', 'openings.json')
WATCH_FILE = os.path.join(HERE, '..', 'data', 'openings_watch.json')
TODAY = date.today()

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      'Accept-Language': 'ja,en;q=0.8'}
WAIT = (2.0, 4.0)   # 外部アクセスの間隔(秒)。相手サイトへの配慮
WATCH_FETCH_BUDGET = 15

CITY_DAITEN = ('https://www.city.fukuoka.lg.jp/business/sangyoushinkou/'
               'jigyousyounei-kigyou-rittishien/daikibokouritenporittihou.html')
PREF_DAITEN = 'https://www.pref.fukuoka.lg.jp/contents/daiten%d.html'
LEAPUP      = ['https://fukuoka-leapup.jp/biz', 'https://fukuoka-leapup.jp/biz/page/2']
VIEWTOKYO   = ['https://view.tokyo/?cat=774', 'https://view.tokyo/?cat=774&paged=2']
SAITOSHIKA  = ['https://saitoshika-west.com/blog-entry-category/kyuusyuu/fukuoka',
               'https://saitoshika-west.com/blog-entry-category/kyuusyuu/fukuoka/page/2']
CITY_PRESS  = 'https://www.city.fukuoka.lg.jp/shisei/kouhou-hodo/hodo-happyo/%d/%s.html'
CITY_PARKS  = 'https://www.city.fukuoka.lg.jp/jutaku-toshi/midorikatuyou/shisei/miryokuahurerukouendukuri.html'
PARKS = ['東平尾公園', '明治公園', '清流公園', '香椎浜北公園', '長垂海浜公園', '音羽公園', '今泉公園']

# 見出しに含まれていれば「これから出来る建物」の記事とみなす語
EVENT_RE = re.compile(r'(グランドオープン|供用開始|街開き|まちびらき|開業|開園|開館|開店|開設|竣工|完成|オープン|着工)')
# 住宅専用は除外(複合・商業・ホテルを伴うものは残す)
HOUSING_RE = re.compile(r'(マンション|分譲|レジデンス|住宅|戸建)')
NONHOUSE_RE = re.compile(r'(複合|商業|ホテル|店舗|オフィス|公園|広場|緑地|施設|ビル|空港|駅)')
# 「開業50周年」のような記念記事は除外
ANNIV_RE = re.compile(EVENT_RE.pattern + r'\s*\d*\s*(周年|記念)')
# 建物ではないもの(冊子・計画書・募集など)の「完成」「開設」を除外
NOISE_RE = re.compile(r'(副読本|冊子|パンフレット|ガイドブック|マップ|動画|計画書|報告書|調査結果|'
                      r'募集|公募|選定|戦略|策定|システム|サイト|アプリ|窓口|相談|講座|教室|'
                      r'ツアー|イベント|フェア|キャンペーン|セール|公演|展示会|ワークショップ|'
                      r'冷房|空調|夜間開館|延長開館|営業時間)')
# 記者発表は市の施設が中心なので、イベント語をやや狭める(「完成」「開設」は冊子・制度にも使われる)
PRESS_EVENT_RE = re.compile(r'(供用開始|開園|開業|開館|竣工|オープン|着工)')

# 時期の表記。「2027年夏」「2027年3月」「26年8月」「令和8年8月6日」「2028年度」「2031年末」
DATE_RE = re.compile(
    r'(?:(?P<era>令和|平成)(?P<ey>元|\d{1,2})|(?P<y4>20\d{2})|(?<![\d.])(?P<y2>[2-3]\d)(?=年\d{1,2}月))年'
    r'(?P<fy>度)?'
    r'(?:(?P<m>1[0-2]|[1-9])月(?:(?P<d>[1-9]|[12]\d|3[01])日)?'
    r'|(?P<season>初頭|初め|春|夏|秋|冬|末|上期|下期|上半期|下半期|前半|後半|内|中))?(?!間)')   # 「20年間」は期間
SEASON_MONTH = {'初頭': 1, '初め': 1, '春': 4, '夏': 7, '秋': 10, '冬': 12, '末': 12,
                '上期': 6, '上半期': 6, '前半': 6, '下期': 12, '下半期': 12, '後半': 12,
                '内': 7, '中': 7}
# 年なしの「9月11日」。直近の年を当てる
MD_RE = re.compile(r'(?<![\d年月])(?P<m>1[0-2]|[1-9])月(?P<d>[1-9]|[12]\d|3[01])日')
# 相対表記。「来春」「年内」「来年度」
REL_RE = re.compile(r'(来春|来夏|来秋|来冬|今春|今夏|今秋|今冬|年内|来年度|来年|今年度|年度内)')


def rel_to_iso(word):
    y, fy = TODAY.year, (TODAY.year if TODAY.month >= 4 else TODAY.year - 1)
    tbl = {'来春': (y + 1, 4), '来夏': (y + 1, 7), '来秋': (y + 1, 10), '来冬': (y + 1, 12),
           '今春': (y, 4), '今夏': (y, 7), '今秋': (y, 10), '今冬': (y, 12), '年内': (y, 12),
           '来年': (y + 1, 7), '来年度': (fy + 2, 3), '今年度': (fy + 1, 3), '年度内': (fy + 1, 3)}
    yy, mm = tbl[word]
    return date(yy, mm, 1).isoformat()


def md_to_iso(m):
    """年なし月日 → 今年。今日より240日以上前なら来年扱い"""
    try:
        d = date(TODAY.year, int(m.group('m')), int(m.group('d')))
    except ValueError:
        return None
    if (TODAY - d).days > 240:
        d = date(TODAY.year + 1, d.month, d.day)
    return d.isoformat()


# ---------------------------------------------------------------- 手動シード(報道ベースの予定。巡回では取れないもの)
SEED_FOUND = '2026-10-11'
_LEAP52246 = 'https://fukuoka-leapup.jp/biz/202505.52246'
_KYUDAI = 'https://fukuoka-leapup.jp/biz/202601.71308'
SEEDS = [
    # (名前, 種別, 時期, 出典URL, イベント語, note, エリア)  ※エリアは所在が明らかなものだけ手で入れる
    ('清流公園 北側プロムナード・橋上広場', '公園', '2026年9月', CITY_PARKS, '供用開始', 'オープン済み(2026年9月11日供用開始)',
     '福岡市中央区清川'),
    ('清流公園 南端広場', '公園', '未定', CITY_PARKS, '開園', '整備中。市ページでは「今後順次オープン」', '福岡市中央区清川'),
    ('香椎浜北公園', '公園', '未定', _LEAP52246, '開園', '報道では2026年7月予定。市ページでは整備中', '福岡市東区香椎浜'),
    ('長垂海浜公園', '公園', '2027年3月', _LEAP52246, '開園', '', '福岡市西区今宿'),
    ('須崎公園 2期(市民会館跡)', '公園', '2027年3月', 'https://fukuoka-leapup.jp/biz/202212.1027', '開園', '', '福岡市中央区天神'),
    ('東平尾公園 全域(山頂広場・ローラーすべり台・展望デッキ)', '公園', '2027年春', _LEAP52246, '開園',
     '大谷広場は2026年4月オープン済み', '福岡市博多区東平尾公園'),
    ('西公園 中央展望広場(県営・カフェ・展望デッキ)', '公園', '2027年5月', 'https://plantec.co.jp/news/260318', '開園', '福岡県営',
     '福岡市中央区西公園'),
    ('音羽公園(森・水遊びの浅瀬・飲食6店)', '公園', '2027年冬', 'https://news.tnc.co.jp/news/articles/NID2025081826809', '開園', '',
     '福岡市博多区博多駅南'),
    ('アイランドシティはばたき公園 全面開園(西側芝生広場・築山)', '公園', '2027年度',
     'https://fukuoka-leapup.jp/biz/202405.30561', '開園', '', '福岡市東区香椎照葉'),
    ('今泉公園(Park-PFI・2027年度着工)', '公園', '2028年度', 'https://fukuoka-leapup.jp/biz/202604.76514', '開園', '',
     '福岡市中央区今泉'),
    ('東消防署アイランドシティ出張所', 'その他', '2027年', 'https://note.com/fukunaman/n/n1e7a69a836d1', '開設', '',
     '福岡市東区香椎照葉'),
    ('九州大学箱崎キャンパス跡地 第1期まちびらき(BOX FUKUOKA・フクオカサスティナブルフードパーク・ライフスタイルセンター)',
     '複合', '2028年度', _KYUDAI, 'まちびらき', '', '福岡市東区箱崎'),
    ('九州大学箱崎キャンパス跡地 概成', '複合', '2036年度', _KYUDAI, '完成', '', '福岡市東区箱崎'),
]

# ウォッチ対象の初期値(data/openings_watch.json が無いときに書き出す)
WATCH_DEFAULT = [
    {'name': 'アイランドシティはばたき公園', 'aliases': ['はばたき公園'], 'kind': '公園', 'note': '全面開園 2027年度'},
    {'name': '九州大学箱崎キャンパス跡地', 'aliases': ['九大跡地', '箱崎キャンパス跡地', 'BOX FUKUOKA'], 'kind': '複合',
     'note': '第1期まちびらき 2028年度'},
    {'name': '福岡空港国内線複合施設', 'aliases': ['国内線複合施設', '福岡空港 国内線'], 'kind': '複合', 'note': '2027年夏'},
    {'name': '三井アウトレットパーク福岡', 'aliases': ['マリノアシティ跡', '三井アウトレット'], 'kind': '商業', 'note': '2027年春'},
    {'name': '須崎公園', 'aliases': [], 'kind': '公園', 'note': '2期 2027年3月'},
    {'name': '音羽公園', 'aliases': [], 'kind': '公園', 'note': '2027年冬'},
    {'name': '西公園', 'aliases': ['西公園中央展望広場'], 'kind': '公園', 'note': '県営 2027年5月'},
    {'name': '東平尾公園', 'aliases': [], 'kind': '公園', 'note': '全域 2027年春'},
    {'name': '長垂海浜公園', 'aliases': [], 'kind': '公園', 'note': '2027年3月'},
    {'name': '今泉公園', 'aliases': [], 'kind': '公園', 'note': '2028年度'},
    {'name': '香椎浜北公園', 'aliases': [], 'kind': '公園', 'note': '未定'},
    {'name': '清流公園', 'aliases': [], 'kind': '公園', 'note': '南端広場 未定'},
    {'name': '天神大樹', 'aliases': ['エースホテル福岡', 'エースホテル', '天神1-7計画', 'イムズ跡'], 'kind': '複合',
     'note': '2027年5月完成。エースホテル福岡が入る'},
]
WATCH = []            # 実行時に読み込む
WATCH_HITS = {}       # name → [(when, iso, event, url, src)]
_watch_budget = WATCH_FETCH_BUDGET


# ---------------------------------------------------------------- 取得まわり
def pause():
    time.sleep(random.uniform(*WAIT))


def fetch(url, binary=False):
    """失敗したら None。文字コードは meta charset → utf-8 の順で決める
    (福岡市サイトはヘッダに charset が無く、requests の自動判定だと化ける)"""
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200:
            print('  ! HTTP %d %s' % (r.status_code, url))
            return None
        if binary:
            return r.content
        b = r.content
        m = re.search(rb'charset=["\']?([\w-]+)', b[:4000], re.I)
        enc = m.group(1).decode('ascii', 'ignore') if m else 'utf-8'
        try:
            return b.decode(enc)
        except Exception:
            return b.decode('utf-8', 'replace')
    except Exception as e:
        print('  ! %s %s' % (url, repr(e)[:80]))
        return None


def strip_tags(h):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = t.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&#038;', '&')
    return re.sub(r'\s+', ' ', t).strip()


def norm(s):
    """全角数字・全角英字を半角に(令和８年８月６日 → 令和8年8月6日)。カナはそのまま"""
    return unicodedata.normalize('NFKC', s)


def abs_url(href, base):
    if href.startswith('http'):
        return href
    root = re.match(r'(https?://[^/]+)', base).group(1)
    return root + href if href.startswith('/') else base.rsplit('/', 1)[0] + '/' + href


def pdf_text(data):
    try:
        import pypdf
        rd = pypdf.PdfReader(io.BytesIO(data))
        return norm(' '.join((p.extract_text() or '') for p in rd.pages))
    except Exception:
        return ''


# ---------------------------------------------------------------- 時期の解釈
def date_to_iso(m):
    """DATE_RE のマッチ → (表記そのまま, ISO近似)。解釈できなければ None"""
    g = m.groupdict()
    if g['era']:
        n = 1 if g['ey'] == '元' else int(g['ey'])
        year = (2018 if g['era'] == '令和' else 1988) + n
    elif g['y4']:
        year = int(g['y4'])
    else:
        year = 2000 + int(g['y2'])
    if not (TODAY.year - 10 <= year <= TODAY.year + 12):
        return None
    if g['m']:
        month, day = int(g['m']), int(g['d'] or 1)
    elif g['season']:
        month, day = SEASON_MONTH[g['season']], 1
    elif g['fy']:
        year, month, day = year + 1, 3, 1       # 年度 = 翌年3月
    else:
        month, day = 7, 1                        # 月不明 = 年央
    try:
        return m.group(0), date(year, month, day).isoformat()
    except ValueError:
        return None


def parse_when_str(s):
    """「2027年春」「2028年度」「未定」→ ISO近似('未定'や解釈不能は '')"""
    m = DATE_RE.search(norm(s))
    r = date_to_iso(m) if m else None
    return r[1] if r else ''


def find_when(text):
    """見出し/本文から「時期 + イベント語」を探す。
    返り値 (時期の表記, ISO, イベント語) か (None, None, イベント語 or None)"""
    t = norm(text)
    # 「2026年5月撮影」「2026年5月2日撮影」は撮影日。時期扱いしないので消す
    t = re.sub(DATE_RE.pattern + r'(上旬|中旬|下旬|頃)?\s*(に)?撮影', ' ', t)
    best = None
    for ev in EVENT_RE.finditer(t):
        if ANNIV_RE.match(t, ev.start()):
            continue
        # 時期 → イベント語(「2027年夏開業」「2026年8月に開園へ」「2028年度竣工予定」)
        for dm in DATE_RE.finditer(t[:ev.start()]):
            gap = t[dm.end():ev.start()]
            if len(gap) <= 6 and not re.search(r'[。、!！?？]', gap):
                r = date_to_iso(dm)
                if r:
                    best = (r[0], r[1], ev.group(1))
        if best:
            return best
        # イベント語 → 時期(「開業予定:2027年3月」「開園は2027年春」)
        tail = t[ev.end():ev.end() + 14]
        dm = DATE_RE.search(tail)
        if dm and not re.search(r'[。、!！?？]', tail[:dm.start()]):
            r = date_to_iso(dm)
            if r:
                return (r[0], r[1], ev.group(1))
    # 年なしの「9月11日供用開始」、相対の「来春オープン」
    for ev in EVENT_RE.finditer(t):
        if ANNIV_RE.match(t, ev.start()):
            continue
        win = t[max(0, ev.start() - 14):ev.start()]
        mm = list(MD_RE.finditer(win))
        if mm and len(win) - mm[-1].end() <= 6:
            iso = md_to_iso(mm[-1])
            if iso:
                return (mm[-1].group(0), iso, ev.group(1))
        # 相対表記は珍しい語なので、少し離れていても(24文字以内)結び付ける
        win2 = t[max(0, ev.start() - 24):ev.start()]
        rm = list(REL_RE.finditer(win2))
        if rm and not re.search(r'[。!！?？]', win2[rm[-1].end():]):
            return (rm[-1].group(0), rel_to_iso(rm[-1].group(0)), ev.group(1))
    ev = EVENT_RE.search(t)
    if ev:
        # イベント語はあるが時期が結び付かない。見出しに時期が1つだけならそれを採用
        ds = [date_to_iso(m) for m in DATE_RE.finditer(t)]
        ds = [d for d in ds if d and d[1] >= TODAY.isoformat()]
        if len(ds) == 1:
            return (ds[0][0], ds[0][1], ev.group(1))
        return (None, None, ev.group(1))
    return (None, None, None)


def add_months(d, n):
    y, m = d.year, d.month + n
    while m > 12:
        y, m = y + 1, m - 12
    return date(y, m, min(d.day, 28))


def parse_jdate(s):
    """「令和8年8月6日」「2026年8月6日」→ date。無理なら None"""
    m = DATE_RE.search(norm(s))
    if not m or not m.group('d'):
        return None
    r = date_to_iso(m)
    return date.fromisoformat(r[1]) if r else None


# ---------------------------------------------------------------- 名前・種別
def guess_kind(text):
    t = text
    if re.search(r'(公園|緑地|広場|開園)', t):
        return '公園'
    if re.search(r'(複合|空港|ターミナル|駅ビル|再開発)', t):
        return '複合'
    if re.search(r'(ホテル|HOTEL|Hotel|リゾート|旅館|宿泊)', t):
        return 'ホテル'
    if re.search(r'(アウトレット|モール|商業|ショッピング|百貨店|ストア|ドラッグ|スーパー|デンキ|'
                 r'マーケット|ファッション|店|ららぽーと|MARK IS|プラザ)', t):
        return '商業'
    if re.search(r'(ビル|タワー|計画|センター|跡地|跡|延床|地上\d+階|高さ\d+m)', t):
        return '複合'
    return 'その他'


def area_from_address(addr):
    """所在地 → エリア(市区町村+町名程度)。取れなければ ''(名前からは推定しない)
      福岡県糟屋郡新宮町下府土地区画整理事業15街区 → 糟屋郡新宮町下府
      福岡市東区和白1丁目1506ー1他               → 福岡市東区和白
      大野城市つつじヶ丘一丁目6番1               → 大野城市つつじヶ丘
      田川市大字伊田52番                         → 田川市伊田"""
    a = re.sub(r'^[\s​]*福岡県[\s​]*', '', norm(addr or '')).strip(' ​')
    m = re.match(r'((?:[^\s\d郡市町村]{1,6}郡)?[^\s\d郡市町村]{1,8}[市町村])(.*)$', a)
    if not m:
        return ''
    muni, rest = m.group(1), m.group(2).strip()
    # 区は政令市(福岡市・北九州市)だけ。「新宮町下府土地区画整理事業」の「区」を区名にしない
    if muni in ('福岡市', '北九州市'):
        k = re.match(r'([^\s\d区]{1,4}区)(.*)$', rest)
        if k:
            muni, rest = muni + k.group(1), k.group(2).strip()
    rest = re.sub(r'^大字', '', rest)
    t = re.match(r'(.+?)(?=\d|[一二三四五六七八九十]+丁目|字|番|土地区画|ほか|他|外|\s|$)', rest)
    town = t.group(1) if t else ''
    if len(town) > 12 or not town:
        return muni
    return muni + town


def is_noise(title):
    """建物の開業記事ではないもの: 周年記念・冊子/制度の「完成」・住宅専用"""
    if ANNIV_RE.search(norm(title)) or NOISE_RE.search(title):
        return True
    return bool(HOUSING_RE.search(title) and not NONHOUSE_RE.search(title))


def guess_name(title):
    """見出しから施設名らしい部分を切り出す。「」『』内を最優先"""
    t = title
    m = re.search(r'[「『]([^」』]{2,40})[」』]', t)
    if m:
        name = m.group(1)
        # 「(仮称)○○」の前に付いた規模(21階約91m)は落とす
        return re.sub(r'^\d+階[^「」]*?[m㎡]\s*', '', name).strip()
    m = re.search(r'[『「]?((?:\(仮称\)|（仮称）)[^、。！!｜|」』]{2,30})', t)
    if m:
        return m.group(1).strip()
    # 括弧無し: 先頭の「2027年夏開業！」等と、末尾の「の最新状況｜…」「の様子 …」「の供用開始について」等を刈る
    n = norm(t).rstrip('!！。 ')
    n = re.sub(r'(の|を)?(' + EVENT_RE.pattern + r')(予定)?(について|のお知らせ|します|しました|へ)?$', '', n)
    n = re.sub(r'^[【〖][^】〗]*[】〗]', '', n)
    n = re.sub(r'^(' + DATE_RE.pattern + r')?[^、。！!｜|]{0,4}' + EVENT_RE.pattern + r'[へ!！、]*', '', n)
    n = re.split(r'(の最新状況|の様子|を現地撮影|の建設状況|が始動|が着工|着工|が[^、]{0,3}初進出|が進出|'
                 r'が建て替え|が開業|が竣工|｜|\||！|!|、|。)', n)[0]
    n = re.sub(r'^(着工してた、|完成してた、|建物の外観が見えてきた、|解体工事中の、|)', '', n)
    n = re.sub(r'^\d+階約?\d+m', '', n).strip(' 、「」')
    return (n or t)[:40]


# ---------------------------------------------------------------- ウォッチ対象
def load_watch():
    global WATCH
    if not os.path.exists(WATCH_FILE):
        with open(WATCH_FILE, 'w', encoding='utf-8') as f:
            json.dump(WATCH_DEFAULT, f, ensure_ascii=False, indent=1)
        print('ウォッチ対象の初期値を書き出した → %s' % os.path.relpath(WATCH_FILE, os.path.join(HERE, '..')))
    with open(WATCH_FILE, encoding='utf-8') as f:
        WATCH = json.load(f)


def watch_terms(w):
    return [w['name']] + list(w.get('aliases') or [])


def watch_of(name):
    """エントリ名がどのウォッチ対象に当たるか(無ければ None)"""
    n = norm(name)
    for w in WATCH:
        if any(norm(a) in n for a in watch_terms(w)):
            return w
    return None


def watch_mentioned(text):
    """テキストに name/alias が出ているウォッチ対象の一覧"""
    t = norm(text)
    return [w for w in WATCH if any(norm(a) in t for a in watch_terms(w))]


def watch_scan(text, url, src):
    """ページ本文の alias と同じ文(。!?】で区切る)にある時期を拾って WATCH_HITS に溜める。拾えた対象名を返す。
    文で区切るのは、サイドバーの関連記事一覧で隣の見出しの日付を拾わないため
    (「『天神1-7計画』は2027年5月末に完成【中央区】 … 音羽公園が…」で音羽公園に2027年5月が付いた事故があった)"""
    t = norm(text)
    got = []
    for w in WATCH:
        for a in watch_terms(w):
            a = norm(a)
            for m in re.finditer(re.escape(a), t):
                s = max((t.rfind(c, 0, m.start()) for c in '。!！?？】\n'), default=-1) + 1
                e = min((i for i in (t.find(c, m.end()) for c in '。!！?？【\n') if i >= 0), default=len(t))
                win = t[max(s, m.start() - 200):min(e, m.end() + 200)]
                when, iso, ev = find_when(win)
                if iso:
                    hits = WATCH_HITS.setdefault(w['name'], [])
                    if not any(h[0] == when and h[3] == url for h in hits):
                        hits.append((when, iso, ev, url, src))
                    got.append(w['name'])
                    break
            if w['name'] in got:
                break
    return got


def watch_article(text_for_match, href, src):
    """見出し/抜粋に alias があるのに時期が取れないとき、本文を開く(予算内で)"""
    global _watch_budget
    ws = watch_mentioned(text_for_match)
    if not ws:
        return
    if watch_scan(text_for_match, href, src):
        return
    if _watch_budget <= 0:
        return
    _watch_budget -= 1
    pause()
    body = fetch(href)
    if body:
        got = watch_scan(strip_tags(body), href, src)
        print('  ★ 本文を確認 %s → %s' % (href[:70], '/'.join(got) if got else '時期なし'))


def apply_watch(items):
    """WATCH_HITS を openings.json のエントリに反映"""
    for w in WATCH:
        hits = WATCH_HITS.get(w['name'])
        if not hits:
            continue
        # 該当エントリ: 手動シード > 名前一致 > alias を含むもの
        cands = [x for x in items if any(norm(a) in norm(x['name']) for a in watch_terms(w))]
        cands.sort(key=lambda x: (0 if x.get('src') == 'manual' else 1,
                                  0 if norm(x['name']) == norm(w['name']) else 1))
        if cands:
            x = cands[0]
        else:
            x = dict(name=w['name'], kind=w.get('kind') or guess_kind(w['name']), event='', when='', when_iso='',
                     title='', address='', src='watch', src_url=hits[0][3], found=TODAY.isoformat(),
                     note=w.get('note', ''))
            items.append(x)
        hist = x.setdefault('history', [])
        for when, iso, ev, url, src in hits:
            if when == x.get('when') or any(h['when'] == when for h in hist):
                continue
            if iso < TODAY.isoformat() and x.get('when_iso'):
                continue   # 古い記事の過去日付は、既に時期があるなら別表記として残さない
            if not x.get('when') or x.get('when') == '未定':
                if x.get('when') == '未定' and iso < TODAY.isoformat():
                    pass   # 「未定」を過去の日付で上書きしない(古い報道)
                else:
                    x.update(when=when, when_iso=iso, event=ev or x.get('event', ''))
                    print('  ★ %s: 時期を「%s」に設定 (%s)' % (x['name'], when, url[:60]))
                    continue
            hist.append(dict(found=TODAY.isoformat(), when=when, when_iso=iso, event=ev or '', src=src, src_url=url))
            print('  ★ %s: 別の時期表記「%s」を history に追記 (現在「%s」) %s' % (x['name'], when, x.get('when'), url[:60]))


# ---------------------------------------------------------------- 各源
def src_city_daiten(deep):
    """福岡市 大店立地法: 一覧 → 「新設」各リンク → 店名/所在地/届出日"""
    out = []
    h = fetch(CITY_DAITEN)
    if not h:
        return out
    i = h.find('>新設<')
    j = h.find('>変更等<', i)
    sec = h[i:j] if i > 0 and j > 0 else h
    links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*<span[^>]*>\s*<span[^>]*>([^<]*新設[^<]*)</span>', sec)
    print('  新設リンク %d件' % len(links))
    for href, label in links:
        pause()
        u = abs_url(href, CITY_DAITEN)
        d = fetch(u)
        if not d:
            continue
        t = norm(strip_tags(d))
        m = re.search(r'1\s*[.．]\s*大規模小売店舗の名称及び所在地\s*(.+?)\s*2\s*[.．]\s*届出日\s*(.+?)\s*3\s*[.．]', t)
        if not m:
            print('  ? 書式が違う %s' % u)
            continue
        name_addr, todoke = m.group(1), m.group(2)
        am = re.search(r'(福岡[市県].*)$', name_addr)
        name = name_addr[:am.start()].strip() if am else name_addr.strip()
        addr = am.group(1).strip() if am else ''
        td = parse_jdate(todoke)
        est = add_months(td, 8) if td else None
        out.append(dict(name=name, kind=guess_kind(name), event='開店',
                        when=('%d年%d月頃(推定)' % (est.year, est.month)) if est else '',
                        when_iso=est.isoformat() if est else '',
                        title=label.strip(), address=addr, area=area_from_address(addr), area_src='auto',
                        src='福岡市 大店立地法', src_url=u,
                        note='届出日 %s +8か月の推定。実際の開店日は届出内容PDF(画像)参照' % (td or todoke)))
    return out


def src_pref_daiten(deep):
    """福岡県 大店立地法 届出一覧表: 「第5条第1項(新設)」の表。今年度と前年度の2ページ"""
    out = []
    fy = TODAY.year if TODAY.month >= 4 else TODAY.year - 1
    for y in (fy, fy - 1):
        u = PREF_DAITEN % y
        h = fetch(u)
        pause()
        if not h:
            continue
        m = re.search(r'<table[^>]*>\s*<caption>\s*<h2[^>]*>[^<]*新設[^<]*</h2>\s*</caption>(.*?)</table>', h, re.S)
        if not m:
            print('  ? 新設の表が見つからない %s' % u)
            continue
        n = 0
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1), re.S):
            cells = [norm(strip_tags(c)) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S)]
            if len(cells) < 3 or '届出日' in cells[0]:
                continue
            td = parse_jdate(cells[0])
            if not td:
                continue
            est = add_months(td, 8)
            name = cells[1].strip('​ ')
            out.append(dict(name=name, kind=guess_kind(name), event='開店',
                            when='%d年%d月頃(推定)' % (est.year, est.month), when_iso=est.isoformat(),
                            title='%s 新設届出 %s' % (name, cells[0].strip('​ ')), address=cells[2].strip('​ '),
                            area=area_from_address(cells[2]), area_src='auto',
                            src='福岡県 大店立地法(令和%d年度)' % (y - 2018), src_url=u,
                            note='届出日 %s +8か月の推定' % td))
            n += 1
        print('  %s 新設 %d件' % (u.rsplit('/', 1)[1], n))
    return out


def _headline_source(label, pages, item_re, title_re, date_hint_re=None, deep=False):
    """見出し一覧型の源(フクリパ / view.tokyo / saitoshika)の共通処理"""
    out = []
    for u in pages:
        h = fetch(u)
        pause()
        if not h:
            continue
        n = 0
        for m in item_re.finditer(h):
            href, block = m.group(1), m.group(2)
            tm = title_re.search(block)
            if not tm:
                continue
            title = strip_tags(tm.group(1))
            snippet = strip_tags(date_hint_re.search(block).group(1)) if date_hint_re and date_hint_re.search(block) else ''
            # ウォッチ対象が見出し/抜粋に出ていれば、イベント語の有無に関係なく時期を探す
            watch_article(title + ' ' + snippet, href, label)
            if not EVENT_RE.search(title) or is_noise(title):
                continue
            when, iso, ev = find_when(title)
            if not iso and snippet:
                when, iso, ev2 = find_when(snippet)
                ev = ev or ev2
            if not iso and deep:
                pause()
                body = fetch(href)
                if body:
                    when, iso, ev2 = find_when(strip_tags(body)[:6000])
                    ev = ev or ev2
            out.append(dict(name=guess_name(title), kind=guess_kind(title), event=ev or '',
                            when=when or '', when_iso=iso or '', title=title, address='',
                            src=label, src_url=href, note=''))
            n += 1
        print('  %s 見出しヒット %d件' % (u, n))
    return out


def src_leapup(deep):
    return _headline_source(
        'フクリパ', LEAPUP,
        re.compile(r'<li class="c-list-post__item[^"]*">\s*<a href="([^"]+)"(.*?)</li>', re.S),
        re.compile(r'<h2 class="c-list-post__title">(.*?)</h2>', re.S), deep=deep)


def src_viewtokyo(deep):
    return _headline_source(
        '再開発調査兵団', VIEWTOKYO,
        re.compile(r'<a href="([^"]+)" class="entry-card-wrap[^"]*"[^>]*>(.*?)</article>', re.S),
        re.compile(r'<h2 class="entry-card-title[^"]*"[^>]*>(.*?)</h2>', re.S),
        re.compile(r'<div class="entry-card-snippet[^"]*">(.*?)</div>', re.S), deep=deep)


def src_saitoshika(deep):
    return _headline_source(
        'saitoshika-west', SAITOSHIKA,
        re.compile(r'<a class="c_linkto" href="([^"]+)">(.*?)</a>', re.S),
        re.compile(r'<h2>(.*?)</h2>', re.S), deep=deep)


def src_city_press(deep):
    """福岡市 記者発表(月別ページ)。題名に開園/供用開始等を含むPDFを拾い、文字PDFなら本文から時期を引く"""
    out = []
    months = []
    y, mo = TODAY.year, TODAY.month
    for _ in range(6):
        months.append((y, mo))
        y, mo = (y, mo - 1) if mo > 1 else (y - 1, 12)
    pdf_budget = 10
    for y, mo in months:
        h = None
        for mm in (str(mo), '%02d' % mo):
            u = CITY_PRESS % (y, mm)
            h = fetch(u)
            pause()
            if h:
                break
        if not h:
            continue
        n = 0
        # 日付見出し(h2「10月9日」)と、その後に続くPDFリンク
        pos_dates = [(m.start(), norm(strip_tags(m.group(1)))) for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', h, re.S)]
        for m in re.finditer(r'<a class="pdf" href="([^"]+)">(.*?)</a>', h, re.S):
            title = re.sub(r'\s*[（(]PDF[：:][^）)]*[）)]\s*$', '', strip_tags(m.group(2)))
            title = re.sub(r'\s*[（(][^（）()]*(局|課|室|協会)[^（）()]*[）)]\s*$', '', title)   # 末尾の(担当部署)
            href = abs_url(m.group(1), u)
            watched = watch_mentioned(title)
            if (not PRESS_EVENT_RE.search(title) or is_noise(title)) and not watched:
                continue
            pdate = ''
            for p, d in pos_dates:
                if p < m.start():
                    pdate = d
            when, iso, ev = find_when(title)
            body = ''
            if (not iso or watched) and pdf_budget > 0:
                pause()
                pdf_budget -= 1
                data = fetch(href, binary=True)
                if data:
                    body = pdf_text(data)[:8000]
                    if not iso:
                        when, iso, ev2 = find_when(body)
                        ev = ev or ev2
            if watched:
                watch_scan(title + ' ' + body, href, '福岡市 記者発表')
            if not PRESS_EVENT_RE.search(title) or is_noise(title):
                continue
            out.append(dict(name=guess_name(title), kind=guess_kind(title), event=ev or '',
                            when=when or '', when_iso=iso or '', title=title, address='',
                            src='福岡市 記者発表', src_url=href, note='発表 %d年%s' % (y, pdate)))
            n += 1
        print('  %d年%d月 ヒット %d件' % (y, mo, n))
    return out


def src_city_parks(deep):
    """福岡市「魅力あふれる公園づくり」(Park-PFI 7公園)。
    本文の「令和8年4月には東平尾公園…がオープンしました」「今後も…順次オープンする予定」を文単位で読む。
    個別ページ(/jutaku-toshi/park-pfi/shisei/*.html)に供用開始の月があればそれを優先"""
    out = {}
    h = fetch(CITY_PARKS)
    pause()
    if not h:
        return []
    t = norm(strip_tags(h))
    watch_scan(t, CITY_PARKS, '福岡市 公園づくり')
    for sent in re.split(r'[。]', t):
        if not re.search(r'(オープン|供用開始|開園)', sent):
            continue
        opened = bool(re.search(r'(しました|済み)', sent))
        planned = bool(re.search(r'(予定|進め)', sent))
        year = None
        for p in PARKS:
            for m in re.finditer(re.escape(p) + r'(\([^)]{1,30}\))?', sent):
                name = m.group(0)
                before = sent[:m.start()]
                # この公園より前に出た最後の年を引き継ぐ(「令和8年4月には A、8月に B」)
                ys = list(DATE_RE.finditer(before))
                if ys:
                    r = date_to_iso(ys[-1])
                    if r:
                        year = int(r[1][:4])
                near = before[-12:]
                dms = list(re.finditer(r'(?:(令和|平成)(\d{1,2})年|(20\d{2})年)?(1[0-2]|[1-9])月(?!\d)', near))
                dm = dms[-1] if dms else None     # 「8月に明治公園、9月に清流公園」→ 直前の月を取る
                if dm and year:
                    mo = int(dm.group(4))
                    yy = year
                    if dm.group(2):
                        yy = (2018 if dm.group(1) == '令和' else 1988) + int(dm.group(2))
                    elif dm.group(3):
                        yy = int(dm.group(3))
                    when = '%d年%d月' % (yy, mo)
                    out[name] = dict(name=name, kind='公園', event='オープン', when=when,
                                     when_iso=date(yy, mo, 1).isoformat(), title=sent[:80], address='',
                                     src='福岡市 公園づくり', src_url=CITY_PARKS,
                                     note='オープン済み' if opened else '')
                elif planned and name not in out:
                    out[name] = dict(name=name, kind='公園', event='開園', when='未定', when_iso='',
                                     title=sent[:80], address='', src='福岡市 公園づくり', src_url=CITY_PARKS,
                                     note='整備中。市ページでは「順次オープンする予定」')
    print('  一覧ページ: %d公園(%s)' % (len(out), ', '.join('%s=%s' % (k, v['when']) for k, v in out.items())))
    # 個別ページ
    links = sorted(set(re.findall(r'href="(/jutaku-toshi/park-pfi/shisei/[^"]+\.html)"', h)))
    for href in links:
        pause()
        u = abs_url(href, CITY_PARKS)
        d = fetch(u)
        if not d:
            continue
        td = norm(strip_tags(d))
        watch_scan(td, u, '福岡市 Park-PFI')
        for p in PARKS:
            if p not in td:
                continue
            found = None
            for m in re.finditer(r'(供用開始|開園|オープン)', td):
                win = td[max(0, m.start() - 40):m.end() + 40]
                if re.search(r'(予定|します|開始日は|日から)', win):
                    when, iso, ev = find_when(win)
                    if iso and iso >= TODAY.isoformat():
                        found = (when, iso, ev)
                        break
            if found:
                key = next((k for k in out if k.startswith(p)), p)
                cur = out.get(key)
                if not cur or cur['when'] == '未定':
                    out[key] = dict(name=key, kind='公園', event=found[2] or '開園', when=found[0], when_iso=found[1],
                                    title='%s 個別ページ' % p, address='', src='福岡市 Park-PFI', src_url=u, note='')
                    print('  %s: 個別ページから「%s」' % (p, found[0]))
            break
    return list(out.values())


SOURCES = [
    ('福岡市 大店立地法(新設)',   src_city_daiten),
    ('福岡県 大店立地法(新設)',   src_pref_daiten),
    ('フクリパ /biz',             src_leapup),
    ('再開発調査兵団 福岡県',     src_viewtokyo),
    ('saitoshika-west 福岡',      src_saitoshika),
    ('福岡市 記者発表',           src_city_press),
    ('福岡市 公園づくり(Park-PFI)', src_city_parks),
]


# ---------------------------------------------------------------- 保存・表示
def load():
    if os.path.exists(OUT):
        with open(OUT, encoding='utf-8') as f:
            return json.load(f)
    return []


def save(items):
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def name_key(name):
    """名前照合用。空白・括弧を落とす(「清流公園(南端広場)」=「清流公園 南端広場」)"""
    return re.sub(r'[\s()（）・]', '', norm(name))


def merge(items, new):
    """名前+出典URL で重複排除。既存に時期が無く新規にあれば時期だけ補う。
    手動シード(manual)と同名のものは出典が違っても別エントリにしない(時期だけ補う)"""
    idx = {(x['name'], x['src_url']): x for x in items}
    manual = {name_key(x['name']): x for x in items if x.get('src') == 'manual'}
    added = 0
    for n in new:
        k = (n['name'], n['src_url'])
        hit = idx.get(k) or manual.get(name_key(n['name']))
        if hit:
            if (not hit.get('when_iso') or hit.get('when') == '未定') and n.get('when_iso'):
                hit.update(when=n['when'], when_iso=n['when_iso'], event=n['event'] or hit.get('event', ''))
            continue
        n['found'] = TODAY.isoformat()
        items.append(n)
        idx[k] = n
        added += 1
    return added


def merge_seeds(items):
    """手動シード。同名があれば時期と note だけ補う"""
    byname = {norm(x['name']): x for x in items}
    added = 0
    for name, kind, when, url, ev, note, area in SEEDS:
        x = byname.get(norm(name))
        if x:
            if not x.get('when'):
                x.update(when=when, when_iso=parse_when_str(when), event=ev)
            if not x.get('note') and note:
                x['note'] = note
            if not x.get('area') and area:
                x['area'] = area
            continue
        x = dict(name=name, kind=kind, event=ev, when=when, when_iso=parse_when_str(when), title=name, address='',
                 area=area, src='manual', src_url=url, found=SEED_FOUND, note=note)
        items.append(x)
        byname[norm(name)] = x
        added += 1
    return added


def lead_note(x):
    """撮影・投稿の仕込み目安: 竣工系は2〜3か月前、開業系は4週前が今日から何日後か"""
    if not x.get('when_iso'):
        return ''
    d = date.fromisoformat(x['when_iso'])
    if x.get('event') in ('竣工', '完成', '着工'):
        a, b = (d - timedelta(days=90) - TODAY).days, (d - timedelta(days=60) - TODAY).days
        return '竣工2〜3か月前=%d〜%d日後' % (a, b)
    return '開業4週前=%d日後' % (d - timedelta(days=28) - TODAY).days


def backfill_area(items):
    """所在地があって area が空のエントリに area を埋める(area_src='auto' を付ける)。
    手で入れた area(area_src 無し or 'manual')は上書きしない。auto のものは切り出しルールの改善を反映する"""
    n = 0
    for x in items:
        if not x.get('address'):
            continue
        if x.get('area') and x.get('area_src') != 'auto':
            continue
        a = area_from_address(x['address'])
        if a and a != x.get('area'):
            x['area'], x['area_src'] = a, 'auto'
            n += 1
    return n


def show_areas(items):
    """area ごとに集計。今日以降の予定が2件以上あるエリアを、最も近い時期の順に出す"""
    groups = {}
    for x in items:
        if x.get('area') and x.get('when_iso') and x['when_iso'] >= TODAY.isoformat():
            groups.setdefault(x['area'], []).append(x)
    hot = [(a, sorted(xs, key=lambda x: x['when_iso'])) for a, xs in groups.items() if len(xs) >= 2]
    hot.sort(key=lambda g: g[1][0]['when_iso'])
    print()
    print('■ 同じエリアに2件以上の予定があるところ(%dエリア、今日以降、近い順) — まちが変わるサイン' % len(hot))
    for a, xs in hot:
        first = xs[0]
        left = (date.fromisoformat(first['when_iso']) - TODAY).days
        print('%-22s %d件  最短 %s(%d日後)' % (a, len(xs), first['when'], left))
        for x in xs:
            star = '★' if watch_of(x['name']) else ' '
            print('    %s%-42s %-14s %s' % (star, x['name'][:42], x['when'][:14], x['src']))
    single = sum(1 for xs in groups.values() if len(xs) == 1)
    noarea = sum(1 for x in items if not x.get('area') and x.get('when_iso') and x['when_iso'] >= TODAY.isoformat())
    print('(1件だけのエリア %d / エリア不明(所在地なし) %d件 — 見出し由来の案件は所在地が無いので手で area を入れると集計に乗る)' % (single, noarea))


def show(items, show_all, kind=None):
    if kind:
        items = [x for x in items if x.get('kind') == kind]
    rows = [x for x in items if x.get('when_iso')]
    if not show_all:
        rows = [x for x in rows if x['when_iso'] >= TODAY.isoformat()]
    rows.sort(key=lambda x: x['when_iso'])
    unknown = [x for x in items if not x.get('when_iso')]
    print()
    print('■ 開業・竣工予定が近い順(%d件%s%s)  ★=ウォッチ対象' % (
        len(rows), '' if show_all else '、今日以降', '、種別=%s' % kind if kind else ''))
    print('%-10s %6s  %-5s %-14s %-16s %-36s %-26s %s' % ('近似日付', '残り日', '種別', '時期', 'エリア', '名前', '仕込み目安', '出典'))
    for x in rows:
        left = (date.fromisoformat(x['when_iso']) - TODAY).days
        star = '★' if watch_of(x['name']) else ' '
        hist = ' [別表記%d]' % len(x['history']) if x.get('history') else ''
        print('%-10s %5d日  %-5s %-14s %-16s %s%-35s %-26s %s%s' % (
            x['when_iso'], left, x['kind'], x['when'][:14], (x.get('area') or '-')[:16], star, x['name'][:35],
            lead_note(x), x['src'], hist))
        print('%s%s' % (' ' * 12, x['src_url']))
        for hh in x.get('history') or []:
            print('%s別表記「%s」 %s %s' % (' ' * 12, hh['when'], hh.get('src', ''), hh.get('src_url', '')[:70]))
    if unknown:
        print()
        print('■ 未定・時期が取れなかったもの(%d件) — --deep で本文を見に行くか、手で確認' % len(unknown))
        for x in unknown:
            star = '★' if watch_of(x['name']) else ' '
            print('  %-5s %s%-40s %-8s %s' % (x['kind'], star, (x['name'] or x['title'])[:40],
                                              x.get('when') or '(取れず)', x['src_url']))


def main():
    args = sys.argv[1:]
    kind = args[args.index('--kind') + 1] if '--kind' in args and args.index('--kind') + 1 < len(args) else None
    load_watch()
    items = load()
    seeded = merge_seeds(items)
    if seeded:
        print('手動シード %d件を追加' % seeded)
    filled = backfill_area(items)
    if filled:
        print('所在地から area を補完 %d件' % filled)
    if '--areas' in args:
        save(items)
        show_areas(items)
        print('OPENING_WATCH_DONE')
        return
    if '--list' not in args:
        deep = '--deep' in args
        total = 0
        for label, fn in SOURCES:
            print('■ %s' % label)
            try:
                got = fn(deep)
            except Exception as e:
                print('  ! この源はスキップ: %s' % repr(e)[:100])
                got = []
            added = merge(items, got)
            total += added
            print('  取得 %d件 / 新規 %d件' % (len(got), added))
            pause()
        print('■ ウォッチ対象の反映(%d対象にヒット)' % len(WATCH_HITS))
        apply_watch(items)
        print()
        print('新規 %d件を追記 → %s(累計 %d件)' % (total, os.path.relpath(OUT, os.path.join(HERE, '..')), len(items)))
    save(items)
    show(items, '--all' in args, kind)
    print('OPENING_WATCH_DONE')


if __name__ == '__main__':
    main()
