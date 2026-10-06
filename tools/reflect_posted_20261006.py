# -*- coding: utf-8 -*-
"""2026-10-06 千屋(QI0znVEMjNQ)・ざいとん(WiXnaVJsqZY)の投稿をマップへ反映
   posted は yt-dlp の %(timestamp)s を JST に変換した日付"""
import io, json, os, shutil, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261006')
raw = io.open(P, encoding='utf-8-sig').read()
spots = json.loads(raw)
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'
for sid, vid, posted in [('sp84245d44b1', 'QI0znVEMjNQ', '2026-10-05'),    # 千屋 10/05 17:30 JST
                         ('spc4bd06a47d', 'WiXnaVJsqZY', '2026-10-06')]:   # ざいとん 10/06 09:00 JST
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    assert not s['video'].get('youtube'), sid + ' に既にYouTubeがある'
    s['video']['youtube'] = 'https://youtube.com/shorts/%s' % vid
    s['posted'] = posted
    s['wish'] = False
    assert s.get('visited'), sid + ' に visited が無い'
    print('更新:', sid, s['name'], posted)
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

M = os.path.join(R, 'data', '投稿待ち.md')
t = io.open(M, encoding='utf-8').read()
lines = t.split('\n')
keep = [l for l in lines if not (l.startswith('| 2026-10-05 | 麺どころ 千屋') or l.startswith('| 2026-10-05 | らーめん・まぜそば ざいとん'))]
t = '\n'.join(keep)
t = t.replace('## 反映済み(履歴)\n', '## 反映済み(履歴)\n'
              '- 2026-10-06 反映 | 麺どころ 千屋 sp84245d44b1 QI0znVEMjNQ posted=2026-10-05 / '
              'ざいとん 香椎本店 spc4bd06a47d WiXnaVJsqZY posted=2026-10-06(TikTok/IGのURLは未取得)\n', 1)
io.open(M, 'w', encoding='utf-8').write(t)
print('投稿待ち.md 更新 (%d行削除)' % (len(lines) - len(keep)))
