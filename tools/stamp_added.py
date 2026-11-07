# -*- coding: utf-8 -*-
"""新しく増えたピンに `added`(マップに載った日)を自動で押す安全網(2026-11-08 新設)。

マップ上部の「今週 +N件」「今週増えたお店」は spots.json の各ピンの `added` で数える。
取り込みツール(SNS・ホットペッパー・手動登録など)が `added` を書き忘れると、増やしても数字に乗らない。
→ 前回 commit した spots.json(git HEAD)に無かった id で `added` が空のものに、今日の日付を押す。

  python tools/stamp_added.py          # 押す(build_pages.py の先頭から自動で呼ばれる)
  python tools/stamp_added.py --check  # 押さずに件数だけ

⚠ 既存のピンには触らない(過去に added が無いピンを今日にすると「今週」が水増しになる)。
"""
import json, os, sys, subprocess, datetime, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')


def head_ids():
    try:
        out = subprocess.run(['git', 'show', 'HEAD:data/spots.json'], cwd=ROOT,
                             capture_output=True, check=True).stdout
        return {s['id'] for s in json.loads(out.decode('utf-8'))}
    except Exception as e:
        print('stamp_added: git HEAD の spots.json を読めないので何もしない:', e)
        return None


def stamp(check=False):
    old = head_ids()
    if old is None:
        return 0
    spots = json.load(open(P, encoding='utf-8'))
    today = datetime.date.today().isoformat()
    hit = [s for s in spots if s['id'] not in old and not s.get('added')]
    new_total = sum(1 for s in spots if s['id'] not in old)
    if hit and not check:
        shutil.copy(P, P + '.bak_stamp_added')
        for s in hit:
            s['added'] = today
        json.dump(spots, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'stamp_added: 前回pushから増えたピン {new_total}件 / うち added を押した {len(hit)}件({today})')
    return len(hit)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    stamp('--check' in sys.argv)
