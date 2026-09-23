# -*- coding: utf-8 -*-
"""イベント一覧の更新をこれ1本にまとめる【2026-09-23ユーザー確定】

   python tools/refresh_events.py          … 必要なら収集し直してから書き出す
   python tools/refresh_events.py --force  … 古くなくても必ず収集し直す
   python tools/refresh_events.py --no-collect … 収集せず書き出しだけ(旧 export_events.py 相当)

なぜ要るか:
  `export_events.py` は **既にある候補ファイル(_週末イベント候補.json)から書き出すだけ**。
  収集(`week_events.py`)を回さない限り、新しく始まったイベントは永久に一覧に出ない。
  実際 2026-09-23 に「木の葉モールのこどもえんにち(9/12〜9/27)が一覧に無い」とユーザー指摘。
  原因は候補ファイルが 9/22 のもので、しかも **across / branch / konoha / ezo / yume の
  5源が回っていなかった**こと。書き出しだけ毎回やっても直らない種類の事故なので、
  「古かったら収集からやる」をスクリプト側の既定にした。

判定(どちらかに当たれば収集する):
  ① 候補ファイルが STALE_DAYS 日より古い
  ② 既定の情報源のうち、候補ファイルに記録が無いものがある(=回っていない源がある)
"""
import argparse, json, os, subprocess, sys
from datetime import date, datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.join(ROOT, 'data', '_週末イベント候補.json')
STALE_DAYS = 3          # これより古かったら収集からやる
WINDOW_DAYS = 13        # 収集する窓(今日 + 13日 = 14日間。events.json の窓と同じ)

NEED = ['mall', 'lala', 'canal', 'icp', 'ie', 'kgk', 'map', 'ikoyo', 'pref',
        'daimaru', 'hankyu', 'yokanavi', 'kurume', 'torius', 'hkc', 'aeonkyushu',
        'across', 'branch', 'konoha', 'ezo', 'yume', 'manual']


def cand_state():
    """(何日前か, 抜けている源) を返す。ファイルが無ければ (None, NEED)"""
    if not os.path.exists(CAND):
        return None, list(NEED)
    age = (date.today() - date.fromtimestamp(os.path.getmtime(CAND))).days
    try:
        d = json.load(open(CAND, encoding='utf-8'))
        missing = [s for s in NEED if s not in (d.get('sources') or {})]
    except Exception:
        missing = list(NEED)
    return age, missing


def run(cmd):
    print('$ ' + ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit('!! 失敗: %s' % ' '.join(cmd))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='古くなくても収集し直す')
    ap.add_argument('--no-collect', action='store_true', help='収集せず書き出しだけ')
    a = ap.parse_args()

    age, missing = cand_state()
    print('候補ファイル: %s / 抜けている源: %s'
          % ('%d日前' % age if age is not None else '無し', missing or 'なし'))

    need_collect = a.force or age is None or age > STALE_DAYS or bool(missing)
    if a.no_collect:
        need_collect = False
    if need_collect:
        f = date.today()
        t = f + timedelta(days=WINDOW_DAYS)
        print('→ 収集からやり直します(%s〜%s・5〜10分)' % (f, t))
        run([sys.executable, 'tools/week_events.py',
             '--from', f.isoformat(), '--to', t.isoformat(), '--n', '12'])
        age2, missing2 = cand_state()
        if missing2:
            print('⚠収集後もまだ抜けている源があります: %s' % missing2)
    else:
        print('→ 候補は新しいので収集は省略(%d日前)' % age)

    run([sys.executable, 'tools/export_events.py'])

    ev = os.path.join(ROOT, 'map', 'events.json')
    d = json.load(open(ev, encoding='utf-8'))
    rows = d['events'] if isinstance(d, dict) else d
    today = date.today().isoformat()
    print('events.json: %s〜%s / %d件 / 今日の分 %d件'
          % (d.get('from'), d.get('to'), len(rows),
             sum(1 for e in rows if today in (e.get('days') or []))))


if __name__ == '__main__':
    main()
