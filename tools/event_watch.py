# -*- coding: utf-8 -*-
"""期間限定イベントを自動で集めて、マップ未登録のものを候補として出す。

■ なぜこれが要るか
  期間限定イベントは**会期が短いほど価値が高く、過ぎると無価値になる**。
  ところが「今どこで何をやっているか」を人力で追うのは続かない。
  SNSを一件ずつ見るより、**会期が構造化されて載っている公式サイトを機械で舐める**ほうが
  網羅性も鮮度も上になる。

■ 情報源(静的HTMLで会期が取れることを実測して選んだ)
  ・クロスロードふくおか(福岡県公式観光サイト) … /event/<id> 形式。会期表記あり
  ・いこーよ … 子連れ向けイベントに強い(map-spot スキルにも「施設系はここが一番強い」と記載)
  ⚠ウォーカープラスとアソビューのイベント一覧URLは404だった(2026-09-11実測)。使うなら要再調査

■ 出力
  ・`data/_events_候補.json` … マップ未登録で、会期が未来のものだけ
  ・**登録はしない**。一覧をユーザーに見せて承認をもらってから `until`/`untilLabel` を付けて登録する
    (map-spot スキルの鉄則。会期を過ぎたスポットは地図から自動で消える設計)

使い方:
    python tools/event_watch.py                 # 収集して候補を出す
    python tools/event_watch.py --detail 20     # 上位20件は個別ページも開いて会場・料金まで取る
"""
import json, io, os, re, sys, time, urllib.request
from datetime import date, datetime

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
OUT = os.path.join(HERE, '..', 'data', '_events_候補.json')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')
WAIT = 3.0
BASE = 'https://www.crossroadfukuoka.jp'


def fetch(u):
    r = urllib.request.Request(u, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    raw = urllib.request.urlopen(r, timeout=30).read()
    for e in ('utf-8', 'shift_jis', 'cp932', 'euc-jp'):
        try:
            return raw.decode(e)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def plain(h):
    t = re.sub(r'<script[\s\S]*?</script>', ' ', h)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t)


DATE = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')


def parse_span(txt):
    """本文から会期(開始, 終了)を ISO で返す。終了が無ければ開始のみ"""
    ds = DATE.findall(txt)
    if not ds:
        return None, None
    def iso(d):
        return '%04d-%02d-%02d' % (int(d[0]), int(d[1]), int(d[2]))
    if len(ds) == 1:
        return iso(ds[0]), None
    return iso(ds[0]), iso(ds[1])


def collect_tiles():
    """一覧ページを **タイトルを起点に前後へ遡って** パースする。
       ⚠タイル全体を1本の正規表現で取ろうとすると0件になる(2026-09-11に踏んだ)。
         リンクが相対/絶対で混在し、要素の順序も一定でないため。
       実際の並びは <a href> … <dd>会期</dd> … <h2 class="o-digest--tile__title">名前</h2>
                    … <p class="…__description">説明</p> … </a>
       会期はタイルの中に入っているので、個別ページを開かなくてよい(40件が1リクエストで取れる)。"""
    out = {}
    for pg in range(1, 10):
        u = BASE + '/event' + ('' if pg == 1 else '?page=%d' % pg)
        try:
            h = fetch(u)
        except Exception as e:
            print('  ! %s %s' % (u, e)); break
        new = 0
        for m in re.finditer(r'o-digest--tile__title">([^<]+)</h2>', h):
            back = h[max(0, m.start() - 2200):m.start()]
            fwd = h[m.end():m.end() + 500]
            ids = re.findall(r'/event/(\d+)', back + fwd)
            dds = re.findall(r'<dd[^>]*>([\s\S]{0,160}?)</dd>', back)
            de = re.search(r'o-digest--tile__description[^>]*>([^<]*)</p>', fwd)
            title = m.group(1).strip()
            key = ids[-1] if ids else title           # id が取れなければ名前をキーにする
            if key in out:
                continue
            span = re.sub(r'<[^>]+>', ' ', dds[-1]) if dds else ''
            out[key] = {'id': ids[-1] if ids else '', 'title': title,
                        'url': (BASE + '/event/' + ids[-1]) if ids else BASE + '/event',
                        'desc': (de.group(1).strip() if de else ''),
                        'span_raw': re.sub(r'\s+', ' ', span).strip()[:140]}
            new += 1
        print('  %d ページ目: +%d (累計 %d)' % (pg, new, len(out)), flush=True)
        if not new:
            break
        time.sleep(WAIT)
    return out


def main():
    spots = json.load(io.open(P, encoding='utf-8'))
    names = [s['name'] for s in spots]
    print('=== クロスロードふくおか(福岡県公式)からイベントを収集 ===')
    tiles = collect_tiles()
    print('イベント %d件' % len(tiles))
    print()
    today = date.today().isoformat()
    rows = []
    for t in sorted(tiles.values(), key=lambda x: x['id']):
        frm, to = parse_span(t['span_raw'])
        end = to or frm
        if end and end < today:
            status = '終了'
        elif frm and frm > today:
            status = 'これから'
        elif frm:
            status = '開催中'
        else:
            status = '会期不明'
        hit = next((nm for nm in names if len(nm) >= 4 and nm in (t['title'] + t['desc'])), None)
        rows.append(dict(t, **{'from': frm, 'until': to, 'status': status, 'mapped': hit}))
        print(' %-5s %-34s %s〜%s  %s' % (status, t['title'][:34], frm or '?', to or '', hit or ''))
    live = [r for r in rows if r['status'] in ('開催中', 'これから', '会期不明') and not r['mapped']]
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        sorted(live, key=lambda x: x['until'] or x['from'] or '9999'), ensure_ascii=False, indent=1))
    print()
    print('収集 %d件 / 要検討(開催中・これから・会期不明 かつ未登録) %d件 → %s'
          % (len(rows), len(live), OUT))
    print('※ 登録はしていません。一覧を見て採否を決めてから until/untilLabel を付けて登録すること')


if __name__ == '__main__':
    main()
