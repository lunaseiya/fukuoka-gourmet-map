# -*- coding: utf-8 -*-
"""2026-10-05 check_upload_sync.py で出た未反映4本の反映
   - ボッチャーノ(xho8mRCWlrI)・キッズランドUS MAX(NXVk3hATQmc)をマップへ紐付け
   - 9月ラーメンランキング(8NJyizzbnio)は店舗単体ではないので 照合除外.txt へ
   - アイランドシティ中央公園リニューアル回(tNMoMLQguK8)は ic-centralpark に既に nmE5hMNO2BI があり
     video.youtube は1本しか持てないので**触らない**(差し替えるかはユーザー判断待ち)
   posted は yt-dlp の %(timestamp)s を JST に変換した日付(upload_date(UTC)は使わない)
"""
import io, json, os, shutil, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261005')
spots = json.load(io.open(P, encoding='utf-8'))
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'
JST = datetime.timezone(datetime.timedelta(hours=9))
YT = 'https://youtube.com/shorts/%s'
for sid, vid, ts in [('da-bocciano-tenjin', 'xho8mRCWlrI', 1791019836),   # 2026-10-03 18:30 JST
                     ('kidsland-978',       'NXVk3hATQmc', 1790942415)]:  # 2026-10-02 21:00 JST
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    assert not s['video'].get('youtube'), sid + ' に既にYouTubeがある'
    s['video']['youtube'] = YT % vid
    s['posted'] = datetime.datetime.fromtimestamp(ts, JST).strftime('%Y-%m-%d')
    s['wish'] = False
    assert s.get('visited'), sid + ' に visited が無い'
    print('更新:', sid, s['name'], s['posted'])
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

# ── 照合除外 ──
X = os.path.join(R, 'data', '照合除外.txt')
x = io.open(X, encoding='utf-8').read()
if '8NJyizzbnio' not in x:
    if not x.endswith('\n'):
        x += '\n'
    x += '8NJyizzbnio  # 9月ラーメン勝手にランキングTOP3(店舗単体ではない) 2026-10-02\n'
    io.open(X, 'w', encoding='utf-8').write(x)
    print('照合除外.txt に 8NJyizzbnio を追加')

# ── 投稿待ち.md ──
M = os.path.join(R, 'data', '投稿待ち.md')
t = io.open(M, encoding='utf-8').read()
lines = t.split('\n')
keep = [l for l in lines if not l.startswith('| 2026-10-01 | **キッズランドUS MAX')]
t = '\n'.join(keep)
t = t.replace('## 反映済み(履歴)\n', '## 反映済み(履歴)\n'
              '- 2026-10-05 反映 | ダ・ボッチャーノ 天神店 da-bocciano-tenjin xho8mRCWlrI posted=2026-10-03 / '
              'キッズランドUS MAX 福岡久山店 kidsland-978 NXVk3hATQmc posted=2026-10-02\n'
              '    9月ラーメン勝手にランキングTOP3(8NJyizzbnio・10/02)は店舗単体ではないので 照合除外.txt へ\n'
              '    ⚠アイランドシティ中央公園リニューアル回(tNMoMLQguK8・10/04)は **未紐付け**。ic-centralpark には既に'
              ' nmE5hMNO2BI(9/10)があり video.youtube は1本しか持てない。差し替えるかユーザー判断待ち'
              '(このままだと check_upload_sync.py に毎回出る)\n', 1)
io.open(M, 'w', encoding='utf-8').write(t)
print('投稿待ち.md 更新 (%d行削除)' % (len(lines) - len(keep)))
