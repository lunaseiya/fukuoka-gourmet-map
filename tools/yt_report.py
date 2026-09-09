# -*- coding: utf-8 -*-
"""YouTube の投稿別成績と視聴者の年齢層を取り出して 1.傾向分析用 に貯める。

なぜ必要か:
  再生数だけ見ていると「2万回ったから成功」と誤読する。実際には泰洋軒(IG 2万)の
  視聴者は45歳以上が65.6%で、子連れマップの客層(25〜44)とはズレていた。
  **どの層に配られたか**を毎回自動で記録して、企画判定の材料にするのが目的。

使い方(リポジトリルートから):
  python tools/yt_report.py                 # 直近30日ぶんを取得して表示
  python tools/yt_report.py --days 90       # 期間を変える
  python tools/yt_report.py --csv           # 1.傾向分析用/youtube_成績.csv に追記保存

⚠ yt-analytics.readonly スコープが要る。403 が出たら tools/yt_auth.py で再認証する。
"""
import os, sys, csv, json, argparse, datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, 'yt_token.json')
OUTDIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), '1.傾向分析用')
JST = datetime.timezone(datetime.timedelta(hours=9))

# 子連れマップの客層。ここの合計が高い回が「マップに効いた回」
CORE_AGES = ('age25-34', 'age35-44')


def creds():
    if not os.path.exists(TOKEN):
        sys.exit('!! yt_token.json が無い。先に python tools/yt_auth.py を実行する')
    c = Credentials.from_authorized_user_file(TOKEN)
    if c.expired and c.refresh_token:
        c.refresh(Request())
        open(TOKEN, 'w', encoding='utf-8').write(c.to_json())
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=30, help='何日ぶんを対象にするか')
    ap.add_argument('--csv', action='store_true', help='1.傾向分析用 にCSVで保存する')
    a = ap.parse_args()

    c = creds()
    yt = build('youtube', 'v3', credentials=c)
    ya = build('youtubeAnalytics', 'v2', credentials=c)

    today = datetime.datetime.now(JST).date()
    start = (today - datetime.timedelta(days=a.days)).isoformat()
    end = today.isoformat()

    # ---- 対象期間の投稿を集める(uploads プレイリスト経由) ----
    ch = yt.channels().list(part='contentDetails,snippet', mine=True).execute()['items'][0]
    uploads = ch['contentDetails']['relatedPlaylists']['uploads']
    print('チャンネル:', ch['snippet']['title'], '/ 期間:', start, '〜', end)

    vids, page = [], None
    while True:
        r = yt.playlistItems().list(part='contentDetails,snippet', playlistId=uploads,
                                    maxResults=50, pageToken=page).execute()
        for it in r['items']:
            pub = it['contentDetails'].get('videoPublishedAt')
            if not pub:
                continue
            d = datetime.datetime.fromisoformat(pub.replace('Z', '+00:00')).astimezone(JST).date()
            if d.isoformat() >= start:
                vids.append((it['contentDetails']['videoId'], it['snippet']['title'], d.isoformat()))
        page = r.get('nextPageToken')
        # プレイリストは新しい順なので、期間より古いものが出たら打ち切ってよい
        if not page or (r['items'] and not vids):
            break
        if vids and len(vids) >= 200:
            break
    if not vids:
        sys.exit('対象期間に投稿がない')

    rows = []
    for vid, title, pub in vids:
        # 基本指標
        m = ya.reports().query(
            ids='channel==MINE', startDate=start, endDate=end,
            metrics='views,estimatedMinutesWatched,averageViewPercentage,likes,comments,shares',
            filters='video==' + vid).execute()
        base = (m.get('rows') or [[0, 0, 0, 0, 0, 0]])[0]

        # 視聴者の年齢層(viewerPercentage は合計100になる)
        g = ya.reports().query(
            ids='channel==MINE', startDate=start, endDate=end,
            metrics='viewerPercentage', dimensions='ageGroup',
            filters='video==' + vid).execute()
        ages = {r[0]: r[1] for r in (g.get('rows') or [])}
        # 年齢層はある程度の視聴数がないと YouTube 側が返さない。
        # 返らなかったときに 0.0% と出すと「25-44に1人も配られなかった」と誤読するので
        # None にして「—」で表示する(実際 300再生前後の回は軒並み空だった)
        core = round(sum(ages.get(k, 0) for k in CORE_AGES), 1) if ages else None

        rows.append({
            '投稿日': pub, '動画ID': vid, 'タイトル': title[:40],
            '再生': int(base[0]), '平均視聴率%': round(base[2], 1),
            'いいね': int(base[3]), 'コメント': int(base[4]), 'シェア': int(base[5]),
            '25-44%': core,
            **{k.replace('age', ''): round(v, 1) for k, v in sorted(ages.items())},
        })

    rows.sort(key=lambda r: r['投稿日'], reverse=True)
    print()
    print('%-11s %7s %6s %6s %6s  %s' % ('投稿日', '再生', '25-44%', 'いいね', '保持%', 'タイトル'))
    for r in rows:
        core = '   —  ' if r['25-44%'] is None else '%5.1f%%' % r['25-44%']
        print('%-11s %7d %s %6d %5.1f%%  %s'
              % (r['投稿日'], r['再生'], core, r['いいね'], r['平均視聴率%'], r['タイトル']))

    print()
    print('※25-44% = 子連れマップの客層に配られた割合。再生数より先にここを見る')
    print('※「—」は年齢層データが返らなかった回。視聴数が少ないと YouTube が出さない')
    print('※直近1〜2日の投稿は集計が追いついておらず再生0と出る(異常ではない)')

    if a.csv:
        os.makedirs(OUTDIR, exist_ok=True)
        p = os.path.join(OUTDIR, 'youtube_成績.csv')
        keys = list(rows[0].keys())
        new = not os.path.exists(p)
        with open(p, 'a', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            if new:
                w.writeheader()
            w.writerows(rows)
        print('保存:', p)


if __name__ == '__main__':
    main()
