# -*- coding: utf-8 -*-
"""週次イベント告知の**キャプションを媒体別に書き出す**。
【2026-09-13: 手書きしていたキャプションが Instagram の2200字を418字超過して発覚】

■ 媒体でリンクの扱いを変える。これが分ける理由
  ・**Instagram / TikTok はキャプションのURLがタップできない**。貼っても読者は打ち直せないので
    **URLは載せず「検索ワード」に一本化**する。URL12本で1200字以上使っていたのが超過の主因
  ・**YouTube の概要欄はURLがクリックできる**ので、こちらには全部貼る(上限5000字)
  → カード14枚目の「リンクはキャプションに貼ってます」は **YouTube/プロフィールのマップ**を指す

■ 上限(実測値)
  Instagram 2200 / TikTok 2200 / YouTube 5000。**超えたら末尾を削るのではなく件数を減らす**
  (途中で切れたキャプションは読者に不親切なので、収まる件数だけ出して残りはマップへ誘導)

■ 壊れやすいところ
  ・会場は **`venue`(施設名)** を使う。`place`(「1階 セントラルコート」等)は館内の場所なので
    単体では会場にならない。検索ワードも `venue` 起点で作る
  ・「あと何日」の基準日は **投稿日**。`--today` で渡す(既定=掲載期間の開始日)
  ・駐車場・料金は**途中で切らない**。入り切らないなら項目ごと落とす

使い方:
    python tools/event_caption.py --dir data/carousel_2026-09-14
    python tools/event_caption.py --dir ... --today 2026-09-14 --title "今週行ける"
"""
import argparse, io, json, os, re, sys
from datetime import date, datetime

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
OVER = os.path.join(HERE, '..', 'data', '_イベント表示名.json')
EVENTS_URL = 'https://lunaseiya.github.io/fukuoka-gourmet-map/map/events.html'   # マップの「⏳イベント」一覧(export_events.py)
WK = '月火水木金土日'
LIMIT = {'instagram': 2200, 'tiktok': 2200, 'youtube': 5000}
MARGIN = 80          # 上限ぴったりを狙うと弾かれるので手前で止める


def clen(s):
    """⚠**SNSの文字数は UTF-16 のコードユニットで数える**【2026-09-16に投稿が弾かれた】
      Python の len() はコードポイント数で、**絵文字(🔎📍📅🅿📌🗺)が1として数えられる**。
      Instagram 側はサロゲートペアで2として数えるため、
      len()=2190 で「OK」と出していたキャプションの実体は **2219** で上限超過だった。
      絵文字は1件ごとに複数入るので、件数が増えるほどズレる"""
    return len(s.encode('utf-16-le')) // 2


def d(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def md(x):
    return '%d/%d(%s)' % (x.month, x.day, WK[x.weekday()])


def disp(ev, ov):
    """表示名と会場。生のイベント名は前置きと煽りで長いので、URLキーの上書き表を優先する。
    **機械的な正規表現で削ると名前が壊れる**(2026-09-13に「『映画名探偵プリキュア」を作った)ので
    上書きは手で確定させる。表に無いものは生のまま(長ければ後段で丸める)。"""
    o = ov.get(ev['url']) or {}
    name = o.get('name') or re.sub(r'\s+', ' ', ev['title']).strip()
    venue = o.get('venue') or ev.get('venue') or ev.get('place') or ''
    return name, venue


def span_txt(ev, today):
    a, b = ev['span']
    b = d(b)
    if ev.get('nostart') or not a:
        s = '〜%sまで' % md(b)
    else:
        a = d(a)
        s = md(a) if a == b else '%s〜%s' % (md(a), md(b))
    left = (b - today).days
    if 0 <= left <= 7:
        s += ' ★あと%d日' % (left + 1)
    return s


def fee_txt(ev):
    # 料金は 補足の free → price → 不明 の順(2026-10-16: price を見ておらず「公式で確認」ばかりだった)
    pr = (ev.get('price') or '').strip()
    return '¥無料' if ev.get('free') else ('¥' + pr if pr and len(pr) <= 18 else '¥有料(料金は公式で確認)')


def block(ev, i, ov, today, with_url):
    """1件 = 2行。**場所と無料/有料だけ**【2026-10-23ユーザー確定】
    「検索ワードは使うことはおそらくない。日時もカードを見てもらうのでいらない。
     つまり場所と、無料有料しか載せません」
    → 🔎検索ワード・📅日程・🕐時間・🅿駐車は落とした(全部カードに書いてある)。
      YouTube だけはカードが無いので 📅 と公式URLを残す。"""
    name, venue = disp(ev, ov)
    L = ['%d. %s' % (i, name[:46])]
    line = '   📍%s' % (venue or ev.get('city') or '')
    if ev.get('city') and ev['city'] not in line:
        line += '(%s)' % ev['city']
    line += ' ' + fee_txt(ev)
    if with_url:
        line += '  📅' + span_txt(ev, today)
    L.append(line)
    # 要予約のものは**申込の動線**を1行足す(2026-10-23ユーザー「LINE予約のやり方わかる動線載せられますか」)。
    # `_イベント補足.json` の reserve(文)/reserve_url(YouTube用)に書く
    if ev.get('reserve'):
        L.append('   📲要予約: ' + ev['reserve'])
        if with_url and ev.get('reserve_url'):
            L.append('   ' + ev['reserve_url'])
    if with_url:
        L.append('   ' + (ev.get('official') or ev['url']))
    return '\n'.join(L)


IP_RE = re.compile(r'ポケモン|ピカチュウ|プリキュア|サンリオ|ちいかわ|おぱんちゅ|ピングー|デュエル|アンパンマン|'
                   r'ディズニー|すみっコ|パウ・?パトロール|鬼滅|仮面ライダー|ウルトラマン|トミカ|プラレール|'
                   r'おでかけ情報')   # 最後は福岡市の週報ページ(イベント名ではない)


def clean_title(t):
    """「【10/24(土)博多】無料ハロウィン撮影会🎃」→「無料ハロウィン撮影会」。
    先頭の【】・末尾の絵文字・半端な副題を落として22字まで(語の区切りで切る)"""
    t = re.sub(r'^\s*[【\[][^】\]]*[】\]]\s*', '', t)
    t = re.sub(r'[\U0001F300-\U0001FAFF☀-➿]+', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) <= 22:
        return t
    core, n = '', 0
    for w in re.split(r'[ 　/／・「」『』（）()]', t):
        if not w:
            continue
        if n and n + len(w) > 22:
            break
        core, n = (core + ' ' + w).strip(), n + len(w)
    return core or t[:22]


def teaser(D, evs, ov, frm, to, n):
    """★カルーセルに載せなかったイベントの**タイトルだけ5件**【2026-10-23ユーザー発案】
    「その代わり、他にもこんなイベントありますよという、タイトルだけを5件ほど並べましょう。
     それが誘導になるかもしれません」
    - 候補JSONに `teaser`(URLの配列)があればそれを使う(手で選んだ回)
    - 無ければ自動: 窓に掛かる未掲載イベントをスコア順、IP・週報ページを除き、
      **同じ市区は1件まで**(福岡市中心の本編に対して北九州・久留米など別エリアが混ざるほうが
      「マップには他のエリアもある」と伝わる)。選んだURLは JSON の `teaser` に書き戻す"""
    used = {e['url'] for e in evs}
    if D.get('teaser'):
        # 項目は URL か **タイトルの先頭**。⚠福岡市の週報ページは複数イベントが同じURLなので
        #   URLだと別のイベント(オクトーバーフェスト)を掴む。そういうものはタイトルで書く
        picked = []
        for s in D['teaser']:
            e = next((x for x in D['events'] if (x['url'] == s or x['title'].startswith(s))
                      and x['url'] not in used), None)
            if e and e not in picked:
                picked.append(e)
    else:
        fs, ts = frm.isoformat(), to.isoformat()
        cand = [e for e in D['events'] if e['url'] not in used and (e.get('span') or [None])[0]
                and e['span'][0] <= ts and (e['span'][1] or e['span'][0]) >= fs
                and not IP_RE.search(e['title']) and not e.get('nostart')]
        cand.sort(key=lambda e: -e.get('score', 0))
        picked, cities, names = [], set(), set()
        for e in cand:
            c = e.get('city') or ''
            nm = clean_title(disp(e, ov)[0])
            if c in cities or nm in names:
                continue
            picked.append(e); cities.add(c); names.add(nm)
            if len(picked) >= n:
                break
        D['teaser'] = [e['url'] for e in picked]
    return [clean_title(disp(e, ov)[0]) for e in picked[:n]]


def count_in_window(D, frm, to):
    """窓に掛かるイベントの件数(マップの「⏳イベント」に出る数の目安)"""
    fs, ts = frm.isoformat(), to.isoformat()
    return sum(1 for e in D['events'] if (e.get('span') or [None])[0]
               and e['span'][0] <= ts and (e['span'][1] or e['span'][0]) >= fs)


def build(evs, plat, ov, today, frm, to, lead_title, more=(), total=0):
    # ★1行目は「ほか◯件はマップに」【2026-10-23ユーザー確定】。
    #   フィードでは1〜2行しか見えないので、タイトル行より先にマップの存在と件数を出す
    head = []
    if total:
        head.append('🗺福岡の子連れイベント、今週末は約%d件。ここには%d件だけ載せてます'
                    % (round(total, -1), len(evs)))
    head += ['【福岡】%s〜%s %s 子連れおでかけ%d選'
             % (md(frm), md(to), lead_title, len(evs)), '']
    # ★マップ誘導は**最初**に置く(2026-10-22ユーザー指示「後ろになっていたはずなので、最初にmap誘導」)。
    #   載せきれなかったイベントがマップのイベント一覧にあることを、本文を読む前に伝える
    rest = ('残り約%d件は' % round(total - len(evs), -1)) if total else 'ここに載せきれなかった分も含めて、福岡の子連れイベントは全部'
    if plat == 'youtube':
        head += [rest + 'この一覧に載せてます(毎日更新・日付で絞れます)🗺', EVENTS_URL, '']
    else:
        head += [rest + 'プロフィールのマップ →「⏳イベント」に載せてます(日付で絞れます)🗺', '']
    head += ['家族で行けるところを今週分まとめました。',
             '日程・時間・何ができるかは各カードに書いてます。', '']
    if plat == 'youtube':
        head += ['各イベントの公式リンクは下に全部貼っています。', '']
    body = [block(e, i, ov, today, plat == 'youtube') for i, e in enumerate(evs, 1)]
    tail = ['──────────']
    if more:
        tail += ['🗺ほかにもこんなイベントがあります(載せきれなかった%sから5つ)'
                 % (('約%d件' % round(total - len(evs), -1)) if total else '分')] + ['・' + t for t in more] \
              + ['→ 全部プロフィールのマップ →「⏳イベント」に載せてます' if plat != 'youtube'
                 else '→ 全部ここに載せてます ' + EVENTS_URL, '']
    tail += ['保存しておくと行くときに使えます📌', '',
             '※画像は各主催者・施設の告知物です(出典は各カードに記載)',
             '※キャラクター作品の画像は権利の都合で掲載していません',
             '※お出かけ前に公式サイトで最新情報をご確認ください', '',
             '#福岡イベント #福岡おでかけ #子連れおでかけ #福岡ママ #福岡子連れ']
    return '\n'.join(head) + '\n' + '\n\n'.join(body) + '\n\n' + '\n'.join(tail) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--json', default=CAND)
    ap.add_argument('--today', default='')
    ap.add_argument('--title', default='今週行ける')
    # ★event_carousel.py と同じ窓で絞る(2026-10-10 連休後半だけの出し直しで、
    #   カードは13件なのにキャプションに土曜だけの5件まで載っていた)
    ap.add_argument('--from', dest='f', default='')
    ap.add_argument('--to', dest='t', default='')
    ap.add_argument('--teaser', type=int, default=5, help='末尾に並べる「ほかにもこんなイベント」の件数(0で出さない)')
    a = ap.parse_args()
    D = json.load(io.open(a.json, encoding='utf-8'))
    by = {e['url']: e for e in D['events']}
    evs = [by[u] for u in D['selected'] if u in by]
    ov = json.load(io.open(OVER, encoding='utf-8')) if os.path.exists(OVER) else {}
    # ★`_イベント補足.json`(手で裏取りした time/free/price/parking)をカードと同じく差し込む
    #   【2026-10-16】これが無く、カードは「無料」なのにキャプションは「料金は公式で確認」、
    #   時間は源の生文字列(「10:00～17:00（②③は10:30～14:30）」)が出ていた
    exp = os.path.join(os.path.dirname(OVER), '_イベント補足.json')
    ext = json.load(io.open(exp, encoding='utf-8')) if os.path.exists(exp) else {}
    for e in evs:
        for k, v in (ext.get(e['url']) or {}).items():
            if not k.startswith('_') and v:
                e[k] = v
    frm, to = d(a.f or D['from']), d(a.t or D['to'])
    if a.f or a.t:
        fs, ts = frm.isoformat(), to.isoformat()
        evs = [e for e in evs if (e.get('span') or [None])[0]
               and e['span'][0] <= ts and (e['span'][1] or e['span'][0]) >= fs]
    today = d(a.today) if a.today else frm
    more = teaser(D, evs, ov, frm, to, a.teaser) if a.teaser else []
    total = count_in_window(D, frm, to)
    if more:
        print('ほかにもこんなイベント:', ' / '.join(more))
        if not a.f and not a.t:
            io.open(a.json, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1))

    os.makedirs(a.dir, exist_ok=True)
    for plat in ('instagram', 'youtube'):
        use = list(evs)
        # **上限を超えたら件数を減らす**。末尾を切ると読者に不親切
        while True:
            s = build(use, plat, ov, today, frm, to, a.title, more, total)
            if clen(s) <= LIMIT[plat] - MARGIN or len(use) <= 6:
                break
            use = use[:-1]
        p = os.path.join(a.dir, '_キャプション_%s.txt' % plat)
        # BOM付き(utf-8-sig)で書く。BOM無しだとDropboxのプレビュー等がShift_JISと誤判定して文字化けする(2026-10-23)
        io.open(p, 'w', encoding='utf-8-sig').write(s)
        print('%-10s %4d字(UTF-16) / 上限%d  %s  掲載%d件%s'
              % (plat, clen(s), LIMIT[plat], 'OK' if clen(s) <= LIMIT[plat] else '超過!',
                 len(use), '' if len(use) == len(evs) else ' (%d件は入らず省いた)' % (len(evs) - len(use))))
    # TikTokはInstagramと同文でよい
    ig = io.open(os.path.join(a.dir, '_キャプション_instagram.txt'), encoding='utf-8-sig').read()
    io.open(os.path.join(a.dir, '_キャプション_tiktok.txt'), 'w', encoding='utf-8-sig').write(ig)
    print('%-10s %4d字(UTF-16) / 上限%d  OK  (Instagramと同文)'
          % ('tiktok', clen(ig), LIMIT['tiktok']))


if __name__ == '__main__':
    main()
