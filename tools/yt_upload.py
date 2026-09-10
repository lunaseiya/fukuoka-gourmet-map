# -*- coding: utf-8 -*-
"""YouTube へ予約公開でアップロードする。

使い方(まずは必ずドライランで中身を確認してから --go を付ける):
    python yt_upload.py --script "<台本のパス>" --video "<mp4のパス>" --kids ng
    python yt_upload.py --script ... --video ... --kids ng --go

・タイトルと説明は**台本(ネット収集.txt / テロップ台本_*.txt)から自動で抜く**。
  「■ YouTube ...」セクション = 説明、「■ 動画タイトル案」の1本目 = タイトル。
  二重管理を避けるため、ここでも台本を唯一の正とする。
・公開は privacyStatus=private + publishAt で**予約**する。時刻は下記ルール。

【予約時刻のルール】2026-09-07 ユーザー確定
  直近の 07:00 → 過ぎていれば 10:00 → それも過ぎていれば
    子連れOKを扱う回   → 21:00  ← 2026-09-10ユーザー確定(20:00から変更)
    子連れ非推奨の回   → 18:00
  全部過ぎていたら**翌日の07:00**。
  子連れの別は --kids ok / --kids ng で渡す(店の実態で決める)。
"""
import argparse, os, re, sys
from datetime import datetime, timedelta, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.path.join(HERE, 'yt_token.json')
# Windows に tzdata が無いので固定オフセットで持つ(日本はDSTが無いので問題ない)
JST = timezone(timedelta(hours=9), 'JST')


def next_slot(kids_ok, now=None):
    """次に来る投稿枠を返す"""
    now = now or datetime.now(JST)
    # 子連れOK回の夜枠は21:00。20:00だと子供の寝かしつけ真っ只中で親が見られない
    # (2026-09-10ユーザー確定。アイランドシティ中央公園回の20:00投稿のあとに指摘)
    evening = 21 if kids_ok else 18
    for h in (7, 10, evening):
        t = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t > now:
            return t
    return (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)


def parse_script(path):
    """台本から YouTube 用のタイトル・説明・タグを抜く"""
    s = open(path, encoding='utf-8').read()
    lines = s.split('\n')

    def section(pattern):
        """「■ <pattern>」から次の「■」or 区切り線までを返す"""
        out, on = [], False
        for ln in lines:
            if ln.startswith('■'):
                if on:
                    break
                on = bool(re.match(r'■\s*' + pattern, ln))
                continue
            if on:
                if set(ln.strip()) and set(ln.strip()) <= set('─-—'):
                    break
                out.append(ln)
        return '\n'.join(out).strip('\n')

    desc = section(r'YouTube')
    if not desc:
        sys.exit('!! 台本に「■ YouTube ...」のセクションが見つからない: ' + path)

    titles = section(r'動画タイトル案')
    title = ''
    for ln in titles.split('\n'):
        ln = ln.strip().lstrip('・').strip()
        if ln:
            title = ln
            break
    if not title:
        sys.exit('!! 台本に「■ 動画タイトル案」が見つからない')

    tags = [t.lstrip('#') for t in re.findall(r'#\S+', desc)]
    # 重複を消しつつ順序は保つ
    tags = list(dict.fromkeys(tags))
    return title.strip(), desc.strip(), tags


SPOTS = os.path.join(HERE, '..', 'data', 'spots.json')


def find_location(script_text):
    """台本の「id=xxxx」からマップのスポットを引いて、撮影場所を組み立てる。

    YouTube の recordingDetails は API から設定できる。座標も住所も
    すでに spots.json に入っているので、**二重入力せずマップを使い回す**。
    """
    import json
    m = re.search(r'【マップ】\s*id=([A-Za-z0-9_-]+)', script_text) or         re.search(r'id=([A-Za-z0-9_-]{6,})', script_text)
    if not m:
        return None, None
    sid = m.group(1)
    try:
        spots = json.load(open(SPOTS, encoding='utf-8'))
    except Exception:
        return sid, None
    for sp in spots:
        if sp.get('id') == sid:
            rec = {}
            desc = sp.get('address') or ' '.join(
                x for x in (sp.get('pref'), sp.get('city'), sp.get('area')) if x)
            if desc:
                rec['locationDescription'] = desc
            if sp.get('lat') and sp.get('lng'):
                rec['location'] = {'latitude': float(sp['lat']),
                                   'longitude': float(sp['lng'])}
            if sp.get('visited'):
                rec['recordingDate'] = str(sp['visited']) + 'T00:00:00Z'
            return sid, (rec or None)
    return sid, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--script', required=True, help='台本のパス')
    ap.add_argument('--video', required=True, help='アップロードする mp4')
    ap.add_argument('--kids', choices=['ok', 'ng'], required=True,
                    help='子連れOKを扱う回なら ok(夕方枠が20時)/ 非推奨なら ng(18時)')
    ap.add_argument('--at', help='予約時刻を直接指定 "2026-09-08 19:00"(ルールを上書き)')
    ap.add_argument('--no-schedule', action='store_true',
                    help='予約せず**非公開のまま**上げる(テスト用/既に別途投稿済みの回)')
    ap.add_argument('--go', action='store_true', help='実際にアップロードする(既定はドライラン)')
    a = ap.parse_args()

    title, desc, tags = parse_script(a.script)
    sid, rec = find_location(open(a.script, encoding='utf-8').read())
    if a.at:
        when = datetime.strptime(a.at, '%Y-%m-%d %H:%M').replace(tzinfo=JST)
    else:
        when = next_slot(a.kids == 'ok')

    size = os.path.getsize(a.video) / 1024 / 1024
    print('=' * 60)
    print('動画    :', os.path.basename(a.video), '(%.1f MB)' % size)
    print('タイトル:', title, '(%d文字)' % len(title))
    print('タグ    :', ', '.join(tags) or '(なし)')
    if rec:
        print('撮影場所:', rec.get('locationDescription', '?'),
              rec.get('location', ''), '/ 撮影日', rec.get('recordingDate', '-')[:10])
    elif sid:
        print('撮影場所: !! 台本のid=%s が spots.json に見つからない' % sid)
    else:
        print('撮影場所: (台本にマップIDの記載が無いので設定しない)')
    if a.no_schedule:
        print('予約公開: なし(**非公開のまま**。手動で公開するまで誰にも見えない)')
    else:
        print('予約公開:', when.strftime('%Y-%m-%d %H:%M'), 'JST')
        print('公開設定: private + publishAt(指定時刻に自動公開)')
    print('-' * 60)
    print(desc)
    print('=' * 60)
    if len(title) > 100:
        sys.exit('!! タイトルが100文字を超えている(YouTubeの上限)')
    if not a.go:
        print('※ドライランです。問題なければ --go を付けて再実行してください。')
        return

    creds = Credentials.from_authorized_user_file(TOKEN)
    yt = build('youtube', 'v3', credentials=creds)
    ch = yt.channels().list(part='snippet', mine=True).execute()['items'][0]
    print('投稿先:', ch['snippet']['title'], ch['snippet'].get('customUrl', ''))

    body = {
        'snippet': {
            'title': title,
            'description': desc,
            'tags': tags[:15],
            'categoryId': '19',          # Travel & Events
            'defaultLanguage': 'ja',
        },
        'status': {
            'privacyStatus': 'private',
            'selfDeclaredMadeForKids': False,
        },
    }
    if rec:
        body['recordingDetails'] = rec
    if not a.no_schedule:
        body['status']['publishAt'] = when.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    media = MediaFileUpload(a.video, chunksize=8 * 1024 * 1024, resumable=True,
                            mimetype='video/mp4')
    parts = 'snippet,status' + (',recordingDetails' if rec else '')
    req = yt.videos().insert(part=parts, body=body, media_body=media)
    res = None
    while res is None:
        status, res = req.next_chunk()
        if status:
            print('  アップロード %d%%' % int(status.progress() * 100), flush=True)
    vid = res['id']
    print('完了 videoId:', vid)
    print('URL :', 'https://youtu.be/' + vid)
    print('管理:', 'https://studio.youtube.com/video/%s/edit' % vid)


if __name__ == '__main__':
    main()
