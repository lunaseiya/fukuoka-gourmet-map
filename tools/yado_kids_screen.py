# -*- coding: utf-8 -*-
"""九州の宿を「子連れで使えるか」で機械的にふるいにかけ、マップ登録の候補を出す。

■ なぜこれが要るか
  九州ふっこう応援割(2026-10-01〜)が始まると対象宿が大量に出てくる。
  ただし**全部載せるとマップがホテル名鑑になり、「子連れで実際に使える宿」という強みが消える**。
  そこで「子連れ設備が1つ以上確認できた宿」だけを候補にする。
  主観の良し悪しではなく**客観的な設備の有無**で切るので、行かなくても検証できる。
  (実際に泊まった評価は visited を入れる赤ピンだけが持てばよい)

■ じゃらんの取り扱い【重要】
  ・**ページは Shift_JIS/CP932**。utf-8 で decode(errors='replace') すると全部化けて
    キーワードが0件になり「設備なし」と誤判定する(2026-09-11に踏んだ)
  ・宿トップ + /plan/ + /kuchikomi/ の3枚を見る。設備はトップ、子連れプランはplan、
    実際に子連れが泊まったかは口コミに出る
  ・アクセスは4秒間隔

使い方:
    # ① エリアから宿を集める(県コード: 福岡400000 佐賀410000 長崎420000
    #    熊本430000 大分440000 宮崎450000 鹿児島460000)
    python tools/yado_kids_screen.py --collect 430000 --out data/_yado_kumamoto.json

    # ② 集めた宿をふるいにかける
    python tools/yado_kids_screen.py --screen data/_yado_kumamoto.json

    # ③ 既にマップにある宿の子連れ設備を埋める
    python tools/yado_kids_screen.py --existing --limit 20
"""
import json, io, os, re, sys, time, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
WAIT = 4.0
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# 子連れ設備のシグナル。点数が高いほど「子連れで使える」証拠として強い
SIGNALS = [
    (5, 'ウェルカムベビー', r'ウェルカムベビーのお宿|ウェルカムベビー'),
    (4, 'キッズスペース',   r'キッズ(ルーム|スペース|コーナー|パーク|ガーデン|広場)'),
    (3, '貸切風呂',         r'貸切(風呂|露天|温泉|湯)|家族風呂'),
    (3, '添い寝無料',       r'添い寝(無料|可|OK)'),
    (3, 'ベビーベッド',     r'ベビーベッド|ベビーガード|ベビーバス'),
    (3, '離乳食',           r'離乳食'),
    (2, 'お子様メニュー',   r'お子様(ランチ|メニュー|定食|料理|プレート)'),
    (2, 'おむつ',           r'おむつ(替え|交換|バケツ)?'),
    (2, '子供用アメニティ', r'子供用(浴衣|スリッパ|歯ブラシ|食器)|お子様用(浴衣|スリッパ)'),
    (2, '子連れプラン',     r'(お子様|こども|子供|ファミリー)[^。<]{0,10}(歓迎|プラン)'),
    (1, 'ファミリー',       r'ファミリー'),
]
MIN_SCORE = 4     # これ未満は候補にしない(単に「ファミリー」と書いてあるだけ等を弾く)


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja'})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ('utf-8', 'shift_jis', 'cp932', 'euc-jp'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('cp932', 'replace')


def plain(html):
    t = re.sub(r'<script[\s\S]*?</script>', ' ', html)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t)


def collect(pref_code, out):
    """県のエリアページを辿って宿ID・宿名を集める"""
    seen = {}
    top = fetch('https://www.jalan.net/%s/' % pref_code)
    time.sleep(WAIT)
    lrgs = sorted(set(re.findall(r'/%s/(LRG_\d+)/' % pref_code, top)))
    print('大エリア %d件: %s' % (len(lrgs), ', '.join(lrgs[:8])))
    pages = ['https://www.jalan.net/%s/' % pref_code] + \
            ['https://www.jalan.net/%s/%s/' % (pref_code, g) for g in lrgs]
    for i, u in enumerate(pages):
        try:
            h = fetch(u)
        except Exception as e:
            print('  ! %s %s' % (u, e)); continue
        for m in re.finditer(r'href="[^"]*?/yad(\d+)/"[^>]*>([^<]{2,60})</a>', h):
            yid, nm = m.group(1), m.group(2).strip()
            if yid not in seen and not nm.startswith('<'):
                seen[yid] = nm
        print('  %2d/%d %-34s 累計 %d件' % (i + 1, len(pages), u.split('/')[-2], len(seen)), flush=True)
        time.sleep(WAIT)
    rows = [{'yad': k, 'name': v, 'url': 'https://www.jalan.net/yad%s/' % k}
            for k, v in sorted(seen.items())]
    io.open(out, 'w', encoding='utf-8').write(json.dumps(rows, ensure_ascii=False, indent=1))
    print('集めた宿: %d件 → %s' % (len(rows), out))


def score_of(url):
    """宿トップ + plan + kuchikomi を見て、子連れ設備の点数と根拠を返す"""
    txt = ''
    for suf in ('', 'plan/', 'kuchikomi/'):
        try:
            txt += plain(fetch(url.rstrip('/') + '/' + suf))
        except Exception:
            pass
        time.sleep(1.5)
    sc, hits = 0, []
    for pt, lab, pat in SIGNALS:
        if re.search(pat, txt):
            sc += pt
            hits.append(lab)
    return sc, hits


def screen(path):
    rows = json.load(io.open(path, encoding='utf-8'))
    spots = json.load(io.open(P, encoding='utf-8'))
    known = {s.get('booking', '').rstrip('/') for s in spots if s.get('booking')}
    print('=== 子連れ設備のスクリーニング (%d件) ===' % len(rows))
    print('しきい値: %d点以上を候補にする' % MIN_SCORE)
    print()
    out = []
    for i, r in enumerate(rows):
        if r['url'].rstrip('/') in known:
            print(' - %-30s 既にマップに登録済み' % r['name'][:30]); continue
        sc, hits = score_of(r['url'])
        mark = '○' if sc >= MIN_SCORE else '×'
        print(' %s %-30s %2d点  %s' % (mark, r['name'][:30], sc, '/'.join(hits) or '—'), flush=True)
        if sc >= MIN_SCORE:
            out.append(dict(r, score=sc, kids=hits))
        time.sleep(WAIT)
    o = path.replace('.json', '_候補.json')
    io.open(o, 'w', encoding='utf-8').write(json.dumps(
        sorted(out, key=lambda x: -x['score']), ensure_ascii=False, indent=1))
    print()
    print('候補 %d / %d件 → %s' % (len(out), len(rows), o))
    print('※ このあと必ずユーザーに一覧を見せて承認をもらってから登録すること(map-spot スキルの鉄則)')


def existing(limit):
    spots = json.load(io.open(P, encoding='utf-8'))
    tg = [s for s in spots if s.get('booking')][:limit]
    print('=== 登録済みの宿の子連れ設備を確認 (%d件) ===' % len(tg))
    for s in tg:
        sc, hits = score_of(s['booking'])
        print(' %-28s %2d点  %s' % (s['name'][:28], sc, '/'.join(hits) or '—'), flush=True)
        time.sleep(WAIT)
    print()
    print('※ 表示のみ。spots.json は書き換えない(kids の解釈は人が決める)')


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--collect' in a:
        i = a.index('--collect')
        out = a[a.index('--out') + 1] if '--out' in a else 'data/_yado.json'
        collect(a[i + 1], out)
    elif '--screen' in a:
        screen(a[a.index('--screen') + 1])
    elif '--existing' in a:
        existing(int(a[a.index('--limit') + 1]) if '--limit' in a else 10)
    else:
        print(__doc__)
