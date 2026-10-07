# -*- coding: utf-8 -*-
"""2026-10-07 投稿3本をマップへ反映(posted = yt-dlp timestamp の JST 日付)
   笑伝 春吉店 9sVHWiJZVHo / 久原本家 総本店 cFO-auUZcik / イオンモール福岡の遊び場 FyTNFsqOnJM(親に紐付け)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261007')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'
for sid, vid, posted in [('shoden-haruyoshi', '9sVHWiJZVHo', '2026-10-07'),
                         ('kubara-honke-souhonten', 'cFO-auUZcik', '2026-10-07'),
                         ('aeonmallfukuoka', 'FyTNFsqOnJM', '2026-10-06')]:
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    assert not s['video'].get('youtube'), sid + ' に既にYouTubeがある'
    s['video']['youtube'] = 'https://youtube.com/shorts/%s' % vid
    s['posted'] = posted
    s['wish'] = False
    print('更新:', sid, s['name'], posted)
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

M = os.path.join(R, 'data', '投稿待ち.md')
t = io.open(M, encoding='utf-8').read()
lines = t.split('\n')
drop = ('笑伝', '久原本家 総本店', 'イオンモール福岡の遊び場')
keep = [l for l in lines if not (l.startswith('| 2026-10-0') and any(k in l for k in drop))]
t = '\n'.join(keep).replace('## 反映済み(履歴)\n', '## 反映済み(履歴)\n'
     '- 2026-10-07 反映 | 笑伝 春吉店 shoden-haruyoshi 9sVHWiJZVHo posted=2026-10-07 / '
     '久原本家 総本店 kubara-honke-souhonten cFO-auUZcik posted=2026-10-07 / '
     'イオンモール福岡の遊び場 → 親 aeonmallfukuoka FyTNFsqOnJM posted=2026-10-06(TikTok/IGは未取得)\n', 1)
io.open(M, 'w', encoding='utf-8').write(t)
print('投稿待ち.md (%d行削除)' % (len(lines) - len(keep)))
