"""見納めウォッチ(閉店・営業終了・閉館・建て替え)。2026-11-17 ユーザー要望:
「クローズ、オープンがわかってて、今のうちに撮っておかなきゃっていうのをキャッチできますかな」

opening_watch.py は開業を拾い、閉店系の記事はわざと落としている(HIGASHI_DROP_RE)。こちらはその逆側。
Googleニュースの検索RSS(直近60日)を天神・博多・東区などで回し、閉店日・営業終了日を見出しから読む。
見納め回は「なくなる前に撮る」(パルコ・新天町・山ちゃんうどん跡)。撮りどきは終了日の4週前〜前日。

  python tools/closing_watch.py          … 巡回して data/見納めリスト.txt に書き出す(1〜2分)
  python tools/closing_watch.py --list   … 巡回せず、保存済みを出す
"""
import os, re, sys, json, time, random, html
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opening_watch as ow   # fetch / norm / DATE_RE / MD_RE / date_to_iso / md_to_iso を借りる

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, '..', 'data', 'closings.json')
OUT_TXT = os.path.join(HERE, '..', 'data', '見納めリスト.txt')
TODAY = date.today()

AREAS = ['天神', '博多', '中洲', '大名', '今泉', '薬院', '福岡市中央区', '福岡市博多区', '福岡市東区', '香椎', '箱崎',
         '千早', '福岡市', '新宮町', '古賀市']
WORDS = '(閉店 OR 営業終了 OR 閉館 OR 閉園 OR 建て替え OR 解体 OR 見納め OR ラストデー)'
CLOSE_RE = re.compile(r'(閉店|営業終了|閉館|閉園|建て替え|建替|解体|見納め|ラストデー|営業を終了|幕を閉じ|最後の営業|移転のため)')
FUKUOKA_RE = re.compile(r'(福岡|博多|天神|中洲|大名|今泉|薬院|香椎|箱崎|千早|新宮|古賀|糸島|春日|大野城)')
# 子連れ・観光・思い出に関係しないもの
DROP_RE = re.compile(r'(介護|老人|デイサービス|クリニック|歯科|病院|調剤|パチンコ|パチスロ|求人|採用|美容|サロン|脱毛|'
                     r'エステ|ネイル|ジム|オフィス|不動産|マンション|保険|銀行|ATM|証券|携帯|ショールーム|'
                     r'期間限定|ポップアップ|POP ?UP|催事|物産展|決算|株主|社長|就任|事件|逮捕|火災|事故|'
                     r'解体ショー|解体の技|さばき|【売買】|ヘリコプター)', re.I)
MD2_RE = re.compile(r'(?P<rel>来年|今年)?(?<!\d)(?P<m>1[0-2]|[1-9])月(?P<d>[1-9]|[12]\d|3[01])日')
# 見出しに福岡の文脈が無いもの(静岡の「天神屋」・和歌山の新宮・加古川の「さぬき大名」)を落とす
FUKUOKA_STRONG_RE = re.compile(r'(福岡|博多区|博多駅|中洲|新天町|キャナル|ソラリア|天神地下街|天神ビッグバン|香椎|箱崎|千早|'
                               r'糟屋|新宮町|古賀市|北九州|小倉)')
OTHER_PLACE_RE = re.compile(r'(静岡|新潟|和歌山|加古川|兵庫|大阪|東京|京都|愛知|天神屋)')
# 号外NET の他県版(【所沢市】寿町の《博多もつ鍋…》)を落とす
OTHER_PREF_RE = re.compile(r'【(?!福岡)[^】]*[市区町村]】')

# 手で入れる見納め(報道が古くRSSの60日に入らないもの)
SEEDS = [
    dict(name='福岡パルコ 閉館(新天町と一体の再開発)', when='2027年2月28日',
         note='工事中パトロール/09 で追っている。11/21から100日前カウントダウン・2/14セレモニー',
         url='https://news.tnc.co.jp/', area='福岡市中央区天神'),
    dict(name='ANAクラウンプラザホテル福岡 建て替え', when='', area='福岡市博多区博多駅前',
         note='福岡地所が2028年末完成目標で建替を計画と報道(西日本新聞 2021-12)。営業終了日は未発表=今も営業中。'
              '外観は今のうちに撮っておく(工事中パトロール/12 の H05)',
         url='https://www.nishinippon.co.jp/item/855730/'),
]


def when_of(title):
    """閉店語にいちばん近い日付を採る。「来年2月28日に閉館 11月21日から100日前」で 11/21 を掴まないため"""
    t = ow.norm(title)
    cands = []
    for m in ow.DATE_RE.finditer(t):
        r = ow.date_to_iso(m)
        if r:
            cands.append((m.start(), m.end(), r[0], r[1]))
    # ow.MD_RE は「年」の直後を除外するので「来年2月28日」を拾えない。こちらで読む
    for m in MD2_RE.finditer(t):
        if any(s <= m.start() < e for s, e, _, _ in cands):
            continue
        try:
            if m.group('rel') == '来年':
                iso = date(TODAY.year + 1, int(m.group('m')), int(m.group('d'))).isoformat()
            elif m.group('rel') == '今年':
                iso = date(TODAY.year, int(m.group('m')), int(m.group('d'))).isoformat()
            else:
                iso = ow.md_to_iso(m)
        except ValueError:
            iso = None
        if iso:
            cands.append((m.start(), m.end(), m.group(0), iso))
    if not cands:
        return '', ''
    cl = [m.start() for m in CLOSE_RE.finditer(t)]
    if cl:
        # 日付が閉店語の前(〜日に閉館)を優先し、距離の近いもの
        best = min(cands, key=lambda c: min((abs(p - c[1]) + (0 if p >= c[1] else 15)) for p in cl))
    else:
        best = cands[0]
    return best[2], best[3]


def crawl():
    seen, out = set(), []
    for a in AREAS:
        q = '%s %s when:60d' % (a, WORDS)
        url = 'https://news.google.com/rss/search?q=%s&hl=ja&gl=JP&ceid=JP:ja' % quote(q)
        # Googleニュースは連続で叩くと 429 を返す(2026-11-17 実測: 2〜3秒間隔で15本中8本が429)
        x = None
        for wait in (0, 45):
            time.sleep(wait)
            x = ow.fetch(url)
            if x:
                break
        time.sleep(random.uniform(6, 9))
        if not x:
            continue
        for it in re.findall(r'<item>(.*?)</item>', x, re.S):
            g = lambda tag: html.unescape((re.search(r'<%s[^>]*>(.*?)</%s>' % (tag, tag), it, re.S) or [None, ''])[1]).strip()
            title, link, pub, src = g('title'), g('link'), g('pubDate'), g('source')
            title = re.sub(r'\s+-\s+[^-]+$', '', title)   # 末尾の「 - 媒体名」
            key = re.sub(r'\W', '', ow.norm(title))[:40]
            if key in seen or not CLOSE_RE.search(title) or not FUKUOKA_RE.search(title) or DROP_RE.search(title) \
                    or OTHER_PREF_RE.search(title) or not FUKUOKA_STRONG_RE.search(title) \
                    or OTHER_PLACE_RE.search(title):
                continue
            seen.add(key)
            wtxt, wiso = when_of(title)
            try:
                pd = parsedate_to_datetime(pub).date().isoformat()
            except Exception:
                pd = ''
            out.append(dict(name=title, when=wtxt, when_iso=wiso, area='検索:' + a, url=link, src=src, pub=pd))
    return out


def show(items):
    lines = ['■ 見納めウォッチ(閉店・営業終了・閉館・建て替え)  作成 %s' % TODAY.isoformat(),
             '  撮りどき = 終了日の4週前〜前日。日付が読めないものは記事を開いて確認(見出しだけ・推測で日付を入れない)', '']
    fut = sorted([x for x in items if x.get('when_iso') and x['when_iso'] >= TODAY.isoformat()], key=lambda x: x['when_iso'])
    unk = [x for x in items if not x.get('when_iso')]
    lines.append('── 終了日が分かっているもの(%d件・近い順) ──' % len(fut))
    for x in fut:
        d = (date.fromisoformat(x['when_iso']) - TODAY).days
        lines.append('%s  あと%4d日  %-14s %s' % (x['when_iso'], d, x.get('area', ''), x['name']))
        if x.get('note'):
            lines.append('            %s' % x['note'])
    lines += ['', '── 日付未確認(%d件・記事の新しい順) ──' % len(unk)]
    for x in sorted(unk, key=lambda x: x.get('pub', ''), reverse=True):
        lines.append('%-10s  %-14s %s  (%s)' % (x.get('pub', '手動'), x.get('area', ''), x['name'], x.get('src', '')))
        if x.get('note'):
            lines.append('            %s' % x['note'])
    txt = '\n'.join(lines) + '\n'
    open(OUT_TXT, 'w', encoding='utf-8-sig').write(txt)
    print(txt)


def due(days=28):
    """撮影リストに必ず載せるもの(2026-11-17 ユーザー「撮れるタイミングがシビアなので、必ず本日の撮影リストに」)。
    shoot_conditions.py の最後から呼ばれる。終了日まで28日以内 + 日付未確認で記事が14日以内のもの"""
    items = json.load(open(OUT_JSON, encoding='utf-8')) if os.path.exists(OUT_JSON) else []
    t = TODAY.isoformat()
    hard = sorted([x for x in items if x.get('when_iso') and t <= x['when_iso'] and
                   (date.fromisoformat(x['when_iso']) - TODAY).days <= days], key=lambda x: x['when_iso'])
    soft = [x for x in items if not x.get('when_iso') and x.get('pub') and
            (TODAY - date.fromisoformat(x['pub'])).days <= 14]
    age = ''
    if os.path.exists(OUT_JSON):
        age = '(リスト更新 %s)' % datetime.fromtimestamp(os.path.getmtime(OUT_JSON)).strftime('%m/%d')
    print('\n■ 見納め(撮れるうちに必ず候補へ)%s' % age)
    if not hard and not soft:
        print('  なし')
    for x in hard:
        d = (date.fromisoformat(x['when_iso']) - TODAY).days
        print('  ★あと%d日(%s) %s' % (d, x['when_iso'], x['name']))
    for x in soft:
        print('  ?日付未確認(記事 %s) %s … 記事を開いて終了日を確認' % (x['pub'], x['name']))


def main():
    if '--due' in sys.argv:
        due()
        return
    old = json.load(open(OUT_JSON, encoding='utf-8')) if os.path.exists(OUT_JSON) else []
    items = old
    if '--list' not in sys.argv:
        got = crawl()
        known = {x['name'] for x in items}
        new = [x for x in got if x['name'] not in known]
        items = items + new
        print('取得 %d件 / 新規 %d件' % (len(got), len(new)))
    for s in SEEDS:
        if not any(x['name'] == s['name'] for x in items):
            items.append(dict(s, when_iso=ow.parse_when_str(s['when']) if s['when'] else '', src='manual', pub=''))
    # 終了日を過ぎたもの・60日より古い日付不明の記事は落とす
    cut = TODAY.toordinal() - 60
    items = [x for x in items if (x.get('when_iso') and x['when_iso'] >= TODAY.isoformat())
             or (not x.get('when_iso') and (x.get('src') == 'manual' or not x.get('pub')
                                            or date.fromisoformat(x['pub']).toordinal() >= cut))]
    json.dump(items, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    show(items)


if __name__ == '__main__':
    main()
