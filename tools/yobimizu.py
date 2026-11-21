"""呼び水コメントの台帳(data/呼び水コメント.json)を見る。

  python tools/yobimizu.py            … 公開済みで未投稿(=今すぐ書くもの)と、次の予定を出す
  python tools/yobimizu.py done N     … N番(0始まり)を投稿済みにする
  python tools/yobimizu.py all        … 全件

運用(2026-11-11 ユーザー確定): 予約したら必ずここに1行足し、予約の報告で文面を見せる。
公開後に Chrome から自分のアカウントでコメント → ピン留め(IG/TikTok)/固定(YouTube) → done。
"""
import json, sys, datetime, os

P = os.path.join(os.path.dirname(__file__), '..', 'data', '呼び水コメント.json')


def load():
    return json.load(open(P, encoding='utf-8'))


def save(d):
    open(P, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')


def at(e):
    return datetime.datetime.strptime(e['publish_at'], '%Y-%m-%d %H:%M')


def show(i, e):
    print(f"[{i}] {e['publish_at']} {e['platform']:9} {e['topic']} / {e['where']} ({e['status']})")
    print('    ' + e['text'].replace('\n', '\n    '))


def main():
    d = load()
    a = sys.argv[1:]
    if a[:1] == ['done']:
        for n in a[1:]:
            d[int(n)]['status'] = 'done'
            d[int(n)]['posted_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        save(d)
        print('done:', a[1:])
        return
    now = datetime.datetime.now()
    rows = list(enumerate(d))
    if a[:1] == ['all']:
        for i, e in rows:
            show(i, e)
        return
    due = [(i, e) for i, e in rows if e['status'] == 'pending' and at(e) <= now]
    nxt = sorted([(i, e) for i, e in rows if e['status'] == 'pending' and at(e) > now], key=lambda x: at(x[1]))
    print(f'== 今すぐ書く: {len(due)}件 ==')
    for i, e in due:
        show(i, e)
    print(f'== 次の予定: {len(nxt)}件 ==')
    for i, e in nxt[:5]:
        print(f"[{i}] {e['publish_at']} {e['platform']} {e['topic']}")
    # 週末カルーセルの出し忘れ防止(2026-11-21 ユーザー確定)。木曜19時〜土曜に、
    # その週末(土曜始まり)の data/carousel_<土曜> が無ければ知らせる。連休で日付をずらした回は直近5日のフォルダも見る
    wd = now.weekday()
    if (wd == 3 and now.hour >= 19) or wd in (4, 5):
        sat = now.date() + datetime.timedelta(days=(5 - wd))
        base = os.path.join(os.path.dirname(__file__), '..', 'data')
        near = [(sat + datetime.timedelta(days=k)).isoformat() for k in range(-3, 3)]
        if not any(os.path.isdir(os.path.join(base, 'carousel_' + x)) for x in near):
            print(f'== ⚠週末カルーセルが未作成({sat.month}/{sat.day}の週末) ==')
            print('    weekly-event-post スキルで候補20件を収集して一覧を出し、PushNotification でユーザーに知らせる')
    # ついでに IG の伸び方を 3h/24h/72h で取る(2026-11-17 ユーザー確定)
    import subprocess
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(os.path.dirname(__file__), 'ig_growth.py'), 'due'])
    # 速報ウォッチ(PR TIMES・Googleニュース)。新着の候補だけ出る(2026-11-17 ユーザー確定)
    if '--no-news' not in sys.argv:
        sys.stdout.flush()
        subprocess.run([sys.executable, '-X', 'utf8', os.path.join(os.path.dirname(__file__), 'news_watch.py')])
    # 撮影ボード(ユーザー専用の非公開ページ)を作り直す。Claude は同じファイルを Artifact で publish し直す
    sys.stdout.flush()
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(os.path.dirname(__file__), 'build_board.py')])
    print('→ 撮影ボードを作り直した。Artifact を同じファイル(ショート動画用/撮影ボード/撮影ボード.html)で publish し直す')


main()
