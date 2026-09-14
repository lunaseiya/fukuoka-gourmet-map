# -*- coding: utf-8 -*-
"""【検証】動物園・水族館系を情報源に足していたら何が拾えていたか。
2026-09-13ユーザー指摘「動物園などのイベントってカウントされてましたかね？
シャボン玉の企画とか動物との触れ合いイベントが体験として入りそう」に対する実測。

収集済み122件を 動物園|水族館|ふれあい|シャボン玉|えさやり… で検索したら **0件**だった。
KIDSスコアには `動物園|植物園|水族館`+4 / `ふれあい`+5 が入っているのに、
**源が無いので届いていなかった**。本スクリプトで3源を実装して差分を出す。

■ 構造の実測(2026-09-13)
  福岡市動物園   `div.eventlistBox id='day_N'` = **1日分**のブロック。
                 中の `<li><a href="/events/detail/N">タイトル</a>` を拾い、
                 **同じタイトルが出てくる日の min/max を会期にする**(会期が正確に取れる)
  到津の森公園   `div.entry-list-item` … category / title+a / date / **term(=会期そのもの)** /
                 excerpt(リード) が全部分離している。最も理想的
  マリンワールド  `div.item clearfix` … span.date(掲載日) / span.label / h3(タイトル)。
                 会期は本文にしかない。訃報・休止のお知らせも混ざるので label と語で除外
■ 取れなかったもの
  海の中道海浜公園  /event/ は 200 だが**日付表記が0=JSで描画**。静的HTMLからは取れない
  響灘グリーンパーク ドメイン不明(hibikinadagreenpark.jp / www付き / .com すべて URLError)
  大牟田市動物園    HTTP 526(SSL証明書エラー)でこちらからは取得できない

使い方: python tools/zoo_probe.py --from 2026-09-14 --to 2026-09-20
"""
import collections, html, io, json, os, re, sys, urllib.request
from datetime import date, datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import week_events as W
import mall_event_watch as M

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    'Chrome/126.0 Safari/537.36',
      'Accept': 'text/html,*/*;q=0.8', 'Accept-Language': 'ja'}


def get(u):
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
    m = re.search(rb'charset=["\']?([\w-]+)', b[:3000])
    return b.decode(m.group(1).decode() if m else 'utf-8', 'replace')


def n(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s or ''))).strip()


# ───────── 福岡市動物園 ─────────
def from_zoo():
    """日別ブロックなので、**同じタイトルが載っている日の最小/最大を会期にする**"""
    rows = []
    try:
        h = get('https://zoo.city.fukuoka.lg.jp/events/')
    except Exception as ex:
        print('  ! 福岡市動物園 %s' % type(ex).__name__, file=sys.stderr); return rows
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)
    seen = {}
    for blk in re.split(r'<div class="eventlistBox"', h)[1:]:
        dm = re.search(r'<h3>(\d{4})年(\d{1,2})月(\d{1,2})日', blk)
        if not dm:
            continue
        d0 = date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
        for u, t in re.findall(r'<a href="(/events/detail/\d+)">([^<]+)</a>', blk):
            t = n(t)
            if not t:
                continue
            r = seen.setdefault(t, {'url': 'https://zoo.city.fukuoka.lg.jp' + u, 'days': []})
            r['days'].append(d0)
    for t, v in seen.items():
        rows.append({'src': '福岡市動物園', 'title': t, 'city': '福岡市中央区',
                     'venue': '福岡市動物園', 'url': v['url'],
                     'span': (min(v['days']), max(v['days'])), 'days_list': None,
                     'raw': '%s〜%s' % (min(v['days']), max(v['days'])), 'free': False,
                     'lead': '', 'place': '福岡市動物園(南公園)', 'poster': None})
    print('  福岡市動物園 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── 到津の森公園(北九州) ─────────
NEWSY = re.compile(r'亡くなり|訃報|休園|休止|中止|臨時|工事|コロナ|募集終了|台風')


def from_itozu():
    rows = []
    try:
        h = get('https://itozu-zoo.jp/event/')
    except Exception as ex:
        print('  ! 到津の森 %s' % type(ex).__name__, file=sys.stderr); return rows
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)
    for blk in re.split(r'<div class="entry-list-item', h)[1:]:
        tm = re.search(r'entry-list-title"><a href="([^"]+)">([^<]+)</a>', blk)
        if not tm:
            continue
        t = n(tm.group(2))
        if NEWSY.search(t):
            continue
        term = n((re.search(r'entry-list-term">([\s\S]{0,300}?)</div>', blk) or ['', ''])[1])
        lead = n((re.search(r'entry-list-excerpt">([\s\S]{0,600}?)</div>', blk) or ['', ''])[1])
        # 会期は term を優先。読めなければタイトル(「（９月１９日～９月２７日）」等)から
        a, e, days = W.jspan(term or t)
        if a in (False, 'ended'):
            a, e, days = W.jspan(t)
        if a in (False, 'ended'):
            continue
        im = re.search(r"<img src='([^']+)'", blk) or re.search(r'<img src="([^"]+)"', blk)
        rows.append({'src': '到津の森公園', 'title': t, 'city': '北九州市小倉北区',
                     'venue': '到津の森公園', 'url': tm.group(1), 'span': (a, e),
                     'days_list': days, 'raw': term, 'free': False, 'lead': lead,
                     'place': '到津の森公園', 'poster': im.group(1) if im else None})
    print('  到津の森公園 %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── マリンワールド海の中道 ─────────
def from_marine():
    rows = []
    try:
        h = get('https://marine-world.jp/news/')
    except Exception as ex:
        print('  ! マリンワールド %s' % type(ex).__name__, file=sys.stderr); return rows
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)
    for blk in re.split(r'<div class="item clearfix', h)[1:]:
        um = re.search(r'<a href="([^"]+)"', blk)
        tm = re.search(r'<h3>([\s\S]{0,300}?)</h3>', blk)
        if not (um and tm):
            continue
        t = n(tm.group(1))
        if not t or NEWSY.search(t):
            continue
        a, e, days = W.jspan(t)
        if a in (False, 'ended'):
            continue
        rows.append({'src': 'マリンワールド', 'title': t, 'city': '福岡市東区',
                     'venue': 'マリンワールド海の中道', 'url': um.group(1), 'span': (a, e),
                     'days_list': days, 'raw': '', 'free': False, 'lead': '',
                     'place': 'マリンワールド海の中道', 'poster': None})
    print('  マリンワールド %d件' % len(rows), file=sys.stderr)
    return rows


# ───────── 本体 ─────────
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='f', required=True)
    ap.add_argument('--to', dest='t', required=True)
    a = ap.parse_args()
    F = datetime.strptime(a.f, '%Y-%m-%d').date()
    T = datetime.strptime(a.t, '%Y-%m-%d').date()

    rows = from_zoo() + from_itozu() + from_marine()
    print()
    print('=== 3源で拾えた生の件数: %d ===' % len(rows))

    # 期間の重なりで絞る(既存フローと同じ考え方)
    hit = []
    for r in rows:
        s, e = r['span']
        if not (hasattr(s, 'year') and hasattr(e, 'year')):
            continue
        if e < F or s > T:
            continue
        hit.append(r)
    print('=== 9/%d〜9/%d に重なるもの: %d件 ===' % (F.day, T.day, len(hit)))
    print()

    # 既存と同じスコア式
    for r in hit:
        d = M.run_days(r['span'])
        s0, e0 = r['span']
        left = (e0 - date.today()).days
        since = (date.today() - s0).days
        r['score'] = (M.kids_score(r['title'] + ' ' + (r.get('lead') or ''))
                      + (4 if d <= 3 else 2 if d <= 9 else 0)
                      + (2 if r.get('free') else 0)
                      + (3 if 0 <= left <= 7 else 0)
                      + (3 if -7 <= since <= 7 else 1 if 8 <= since <= 14 else 0)
                      - (6 if left > 90 else 0))
        r['left'], r['since'], r['days'] = left, since, d

    hit.sort(key=lambda r: -r['score'])
    for r in hit:
        print('  score=%-3s %-12s %-46s %s〜%s (残%d日)'
              % (r['score'], r['src'][:10], re.sub(r'\s+', ' ', r['title'])[:44],
                 r['span'][0], r['span'][1], r['left']))

    # 既存の選抜12件と比べてどこに入るか
    cand = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
    if os.path.exists(cand):
        D = json.load(io.open(cand, encoding='utf-8'))
        by = {e['url']: e for e in D['events']}
        cur = [(by[u]['score'], by[u]['title']) for u in D['selected'] if u in by]
        print()
        print('=== 既存の選抜12件のスコア分布 ===')
        for i, (sc, t) in enumerate(cur, 1):
            print('  %2d. %-3s %s' % (i, sc, re.sub(r'\s+', ' ', t)[:44]))
        lo = min(s for s, _ in cur)
        win = [r for r in hit if r['score'] > lo]
        print()
        print('=== 判定 ===')
        print('  既存12件の最低スコアは %d。それを上回る新規は **%d件**' % (lo, len(win)))
        for r in win:
            rank = sum(1 for s, _ in cur if s > r['score']) + 1
            print('     %d位相当  score=%-3s %s'
                  % (rank, r['score'], re.sub(r'\s+', ' ', r['title'])[:44]))


if __name__ == '__main__':
    main()
