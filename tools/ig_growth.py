"""Instagram リールの伸び方台帳(data/IG伸び台帳.json)。2026-11-17 ユーザー確定:
「呼び水のついでに取得し、どういうものが伸びるのかの相談材料にする」

公開 3時間 / 24時間 / 72時間 の3回、投稿インサイト(Web)の数字を貯めて、
初速の割合(保存率・シェア率・いいね率)と、最終の到達の関係を見る。

  python tools/ig_growth.py due                          … 今すぐ取る投稿(yobimizu.py からも呼ばれる)
  python tools/ig_growth.py add CODE "題" "YYYY-MM-DD HH:MM" 型   … 投稿を台帳に足す(公開時刻はJST)
  python tools/ig_growth.py snap CODE FILE|-             … インサイトの innerText を読んで記録(- は標準入力)
  python tools/ig_growth.py report                       … 割合の表と、3h時点の割合 → 72h到達の並び

取り方: https://www.instagram.com/lunamasao/reel/<CODE>/ を開き「インサイトを見る」をJSでclick →
/insights/media/<id>/ に遷移するので document.body.innerText をそのまま snap に渡す。
平均視聴時間はWebに出ない(アプリのみ)。型: 工事・再開発 / 見納め・跡地 / IPイベント / 新店・施設 / 宿 / 単店 / ニュース / イベント
"""
import json, sys, os, re, datetime

P = os.path.join(os.path.dirname(__file__), '..', 'data', 'IG伸び台帳.json')
YOBI = os.path.join(os.path.dirname(__file__), '..', 'data', '呼び水コメント.json')
# 取る時点と、その時点として受け付ける経過時間の幅(時間)
CHECKS = [(3, 2, 11), (24, 18, 40), (72, 60, 110)]   # 21時公開の3h時点は 23:17 の定期確認(2.3h)で取る
LABELS = {'ビュー': 'views', '閲覧者': 'reach', 'インタラクション': 'inter', '「いいね！」': 'likes',
          'コメント': 'comments', '保存数': 'saves', 'シェア数': 'shares', 'フォロー数': 'follows',
          'プロフィールのアクティビティ': 'profile'}


def load():
    return json.load(open(P, encoding='utf-8')) if os.path.exists(P) else {}


def save(d):
    open(P, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')


def pt(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M')


def num(s):
    s = s.strip().replace(',', '')
    m = re.match(r'([\d.]+)\s*(万)?', s)
    if not m:
        return None
    v = float(m.group(1)) * (10000 if m.group(2) else 1)
    return int(round(v))


def parse(txt):
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    out = {}
    for i, l in enumerate(lines):
        k = LABELS.get(l)
        if not k or k in out:
            continue
        # ラベル直後の最初の数値行(「ビュー\nビュー\n642」のように見出しが重なる)
        for nxt in lines[i + 1:i + 3]:
            v = num(nxt)
            if v is not None and not nxt.endswith('%'):
                out[k] = v
                break
    m = re.search(r'ビュー\n(?:ビュー\n)?[\d,.万]+\nフォロワー\n([\d.]+)%', '\n'.join(lines))
    if m:
        out['follower_pct'] = float(m.group(1))
    return out


def age(e, now=None):
    return ((now or datetime.datetime.now()) - pt(e['publish_at'])).total_seconds() / 3600


def due():
    d = load()
    now = datetime.datetime.now()
    rows = []
    for code, e in d.items():
        h = age(e, now)
        for c, lo, hi in CHECKS:
            if lo <= h < hi and not any(lo <= s['h'] < hi for s in e.get('snaps', [])):
                rows.append(f"[{code}] {e['topic']} … {c}h時点(経過{h:.1f}h)")
    # 呼び水台帳にあって伸び台帳にまだ無いIGリール(codeが分からないので先に add する)
    known = [e['topic'] for e in d.values()]
    try:
        for y in json.load(open(YOBI, encoding='utf-8')):
            if y['platform'] != 'instagram' or 'カルーセル' in y.get('where', '') \
                    or any(y['topic'] in k or k in y['topic'] for k in known):
                continue
            h = (now - pt(y['publish_at'])).total_seconds() / 3600
            if 2.5 <= h < 110:
                rows.append(f"[code未登録] {y['topic']}(公開 {y['publish_at']}・経過{h:.1f}h)→ /lunamasao/reels/ で code を引いて add")
    except Exception:
        pass
    print(f'== 今すぐ取る(IG計測): {len(rows)}件 ==')
    for r in rows:
        print(r)


def rate(s, k):
    if k == 'shares':
        # ⚠Web の「シェア数」は九大跡地(インタラクション2,964)でも0と出る=Webでは数えていない。
        #   インタラクション − いいね − コメント − 保存 の残り(シェア+リポスト)で代用する
        if s.get('inter') is None or None in (s.get('likes'), s.get('comments'), s.get('saves')) or not s.get('reach'):
            return None
        return (s['inter'] - s['likes'] - s['comments'] - s['saves']) / s['reach'] * 100
    if s.get(k) is None or not s.get('reach'):
        return None
    return s[k] / s['reach'] * 100


def f(v, w=6, p=2):
    return ' ' * (w - 1) + '-' if v is None else f'{v:{w}.{p}f}'


def at_check(e, c):
    for cc, lo, hi in CHECKS:
        if cc == c:
            ss = [s for s in e.get('snaps', []) if lo <= s['h'] < hi]
            return min(ss, key=lambda s: abs(s['h'] - c)) if ss else None


def report():
    d = load()
    print('割合はすべて ÷閲覧者(%)。最新の計測を表示')
    print(f"{'題':22} {'型':8} {'経過h':>6} {'閲覧者':>8} {'保存%':>6} {'ｼｪｱ%':>6} {'いいね%':>6} {'ｺﾒﾝﾄ%':>6} {'ﾌｫﾛｰ%':>6}")
    rows = []
    for code, e in d.items():
        if not e.get('snaps'):
            continue
        s = max(e['snaps'], key=lambda s: s['h'])
        rows.append((s.get('reach') or 0, e, s))
    for _, e, s in sorted(rows, key=lambda x: -x[0]):
        print(f"{e['topic'][:22]:22} {e.get('type', '')[:8]:8} {s['h']:6.1f} {s.get('reach') or 0:8d} "
              f"{f(rate(s, 'saves'))} {f(rate(s, 'shares'))} {f(rate(s, 'likes'))} {f(rate(s, 'comments'))} {f(rate(s, 'follows'), p=3)}")
    # 初速 → 72h の並び(3h と 72h の両方がある投稿だけ)
    pair = [(e, at_check(e, 3), at_check(e, 72)) for e in d.values()]
    pair = [(e, a, b) for e, a, b in pair if a and b]
    print(f'\n== 3h時点の割合 → 72h時点の閲覧者({len(pair)}本。15本を超えたら目安の線を引く) ==')
    for e, a, b in sorted(pair, key=lambda x: -(x[2].get('reach') or 0)):
        print(f"{e['topic'][:22]:22} 3h閲覧者{a.get('reach') or 0:7d} 保存{f(rate(a, 'saves'))} シェア{f(rate(a, 'shares'))} "
              f"いいね{f(rate(a, 'likes'))} → 72h {b.get('reach') or 0:8d}")


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else 'due'
    if cmd == 'due':
        due()
    elif cmd == 'add':
        d = load()
        code, topic, pub = a[1], a[2], a[3]
        d.setdefault(code, {'topic': topic, 'publish_at': pub, 'type': a[4] if len(a) > 4 else '', 'snaps': []})
        save(d)
        print('added', code, topic)
    elif cmd == 'snap':
        d = load()
        code = a[1]
        txt = sys.stdin.read() if a[2] == '-' else open(a[2], encoding='utf-8').read()
        v = parse(txt)
        if not v.get('views'):
            sys.exit('ビューが読めない: ' + txt[:200])
        e = d[code]
        now = datetime.datetime.now()
        v.update(taken_at=now.strftime('%Y-%m-%d %H:%M'), h=round(age(e, now), 1))
        e['snaps'].append(v)
        save(d)
        print(code, e['topic'], v)
    elif cmd == 'report':
        report()


main()
