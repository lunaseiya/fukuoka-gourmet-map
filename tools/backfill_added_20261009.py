# -*- coding: utf-8 -*-
"""spots.json に「登録日」 added(YYYY-MM-DD) を付ける(2026-10-09)。
   リストで「最近登録した青ピンを NEW の次に出す」ため。git の履歴から各 id が初めて現れたコミット日を取る。
   - 2026-09-20 以降のコミットだけ遡る(それより前からある id は added を付けない=古い扱い)
   - まだコミットされていない id(作業中の追加分)は今日の日付
   以後の新規登録は build_pages.py が added の無い id に当日の日付を自動で付ける"""
import io, json, os, subprocess, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SINCE = '2026-09-20'


def ids_at(rev):
    try:
        t = subprocess.run(['git', '-C', R, 'show', '%s:data/spots.json' % rev],
                           capture_output=True, check=True).stdout.decode('utf-8-sig')
        return {s['id'] for s in json.loads(t)}
    except Exception:
        return set()


log = subprocess.run(['git', '-C', R, 'log', '--reverse', '--since=' + SINCE, '--format=%H %ad',
                      '--date=short', '--', 'data/spots.json'], capture_output=True, text=True).stdout.split('\n')
log = [l.split() for l in log if l.strip()]
base = subprocess.run(['git', '-C', R, 'rev-list', '-1', '--before=' + SINCE, 'HEAD'],
                      capture_output=True, text=True).stdout.strip()
seen = ids_at(base) if base else set()
first = {}
for h, dt in log:
    cur = ids_at(h)
    for i in cur - seen:
        first.setdefault(i, dt)
    seen |= cur
today = datetime.date.today().isoformat()
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
n = 0
for s in spots:
    if s.get('added'):
        continue
    if s['id'] in first:
        s['added'] = first[s['id']]; n += 1
    elif s['id'] not in seen:
        s['added'] = today; n += 1
io.open(P + '.bak_added', 'w', encoding='utf-8').write(io.open(P, encoding='utf-8-sig').read())
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
w = [s for s in spots if s.get('wish') and s.get('added')]
print('added を付けた:', n, '/ うち青ピン', len(w))
for d in sorted({s['added'] for s in w})[-6:]:
    print(' ', d, sum(1 for s in w if s['added'] == d))
