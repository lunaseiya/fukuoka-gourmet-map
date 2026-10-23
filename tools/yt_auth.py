# -*- coding: utf-8 -*-
"""YouTube への初回認証。ブラウザが開くので @tencone のアカウントで許可する。

一度成功すると tools/yt_token.json に refresh token が保存され、
以降は yt_upload.py がそれを使って自動でアップロードできる(再認証は不要)。

⚠ yt_client_secret.json と yt_token.json は**認証情報そのもの**なので
   共有・コミットしないこと(Dropbox配下だが .gitignore で除外する)。
"""
import os, json

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

HERE = os.path.dirname(os.path.abspath(__file__))
SECRET = os.path.join(HERE, 'yt_client_secret.json')
TOKEN = os.path.join(HERE, 'yt_token.json')
# アップロード / 自分のチャンネル情報 / アナリティクス(視聴者の年齢層まで)。
# yt-analytics.readonly は yt_report.py が使う。2026-09-10 に追加したので、
# それ以前に作った yt_token.json では 403 になる → このスクリプトで再認証すること
# youtube.force-ssl は videos().update(予約時刻の変更 = yt_reschedule.py)に要る。
# 2026-10-23 追加。無いと 403 insufficientPermissions(2026-09-14 実測)
SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/youtube.force-ssl',
          'https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/yt-analytics.readonly']

# ⚠【2026-10-23 判明】refresh token が 7日で失効していた(invalid_grant)。
#   2026-09-10 02:28 に発行 → 09-16 まで動作 → 以降ずっと失敗。
#   原因は Google Cloud の OAuth 同意画面が「テスト」状態のままだと、
#   発行される refresh token の寿命が 7日に固定されること(Google の仕様)。
#   恒久対策: Cloud Console → APIs & Services → OAuth consent screen →
#   「アプリを公開」(Publishing status を Testing → In production)。
#   自分のアカウントで使うだけなら審査は不要(警告画面が出るが「続行」で通る)。
#   公開後にこのスクリプトで再認証した token は失効しなくなる。


def main():
    flow = InstalledAppFlow.from_client_secrets_file(SECRET, SCOPES)
    # ブラウザが開く。ローカルの空きポートで受け取る
    # 'select_account' を付けないと、ログイン済みの既定チャンネルに黙って繋がる。
    # このアカウントには複数チャンネル(ルナログ・ゲームズ / tencone)があるので毎回選ばせる
    creds = flow.run_local_server(port=0, prompt='select_account consent',
                                  authorization_prompt_message='ブラウザで許可してください: {url}',
                                  success_message='認証できました。このタブは閉じて構いません。')
    with open(TOKEN, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())
    print('token を保存しました:', TOKEN)

    # 誰として認証できたか確認する(チャンネルを取り違えていないかの検算)
    yt = build('youtube', 'v3', credentials=creds)
    r = yt.channels().list(part='snippet,statistics', mine=True).execute()
    for it in r.get('items', []):
        s = it['snippet']; st = it.get('statistics', {})
        print('チャンネル :', s['title'])
        print('チャンネルID:', it['id'])
        print('登録者     :', st.get('subscriberCount', '?'))
        print('動画数     :', st.get('videoCount', '?'))


if __name__ == '__main__':
    main()
