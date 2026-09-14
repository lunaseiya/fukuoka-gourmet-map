# -*- coding: utf-8 -*-
"""**予約公開の時刻だけ**を変更する。動画は上げ直さない。

yt_upload.py は「アップロード+予約」の道具なので、上げたあとに時刻を変えたいときに使う。
【2026-09-14ユーザー指示「めんちゃんのアップ時間、18時で」】
  締めラーメンの回が朝7時公開だと題材と時間帯が噛み合わない。枠の自動割り当ては
  「直近の空き枠」を採るので、**題材と時間帯が合わないことがある**。そのときはこれで直す。

⚠**publishAt は未来時刻でなければ API が失敗する**。
⚠status を送るときは **privacyStatus も一緒に送らないと public に戻る**ことがあるので必ず併記する。

使い方: python tools/yt_reschedule.py --id 3uHi2Tf-z5k --at "2026-09-15 18:00"
        python tools/yt_reschedule.py --id 3uHi2Tf-z5k --at "..." --go
"""
import argparse, os, sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, 'yt_token.json')
JST = timezone(timedelta(hours=9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--id', required=True)
    ap.add_argument('--at', required=True, help='JSTで "YYYY-MM-DD HH:MM"')
    ap.add_argument('--go', action='store_true')
    a = ap.parse_args()

    at = datetime.strptime(a.at, '%Y-%m-%d %H:%M').replace(tzinfo=JST)
    now = datetime.now(JST)
    if at <= now:
        sys.exit('!! 指定時刻(%s)が現在(%s)より前。publishAt は未来でなければ失敗する'
                 % (at.strftime('%Y-%m-%d %H:%M'), now.strftime('%Y-%m-%d %H:%M')))

    creds = Credentials.from_authorized_user_file(TOKEN)
    yt = build('youtube', 'v3', credentials=creds)
    r = yt.videos().list(part='snippet,status', id=a.id).execute()
    if not r.get('items'):
        sys.exit('!! 動画が見つからない: ' + a.id)
    v = r['items'][0]
    cur = v['status'].get('publishAt')
    print('動画   : %s' % v['snippet']['title'][:60])
    print('現在   : privacyStatus=%s / publishAt=%s' % (v['status']['privacyStatus'], cur))
    if cur:
        print('         (JSTで %s)'
              % datetime.fromisoformat(cur.replace('Z', '+00:00')).astimezone(JST).strftime('%Y-%m-%d %H:%M'))
    print('変更後 : publishAt=%s (JST %s)'
          % (at.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), at.strftime('%Y-%m-%d %H:%M')))
    if not a.go:
        print()
        print('※ドライランです。--go を付けて再実行してください。')
        return

    # ⚠privacyStatus を併記する。status を部分的に送ると既定値で上書きされる
    body = {'id': a.id,
            'status': {'privacyStatus': 'private',
                       'publishAt': at.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                       'selfDeclaredMadeForKids': v['status'].get('selfDeclaredMadeForKids', False)}}
    out = yt.videos().update(part='status', body=body).execute()
    pa = out['status'].get('publishAt')
    print()
    print('完了: privacyStatus=%s / publishAt=%s' % (out['status']['privacyStatus'], pa))
    print('      JSTで %s'
          % datetime.fromisoformat(pa.replace('Z', '+00:00')).astimezone(JST).strftime('%Y-%m-%d %H:%M'))


if __name__ == '__main__':
    main()
