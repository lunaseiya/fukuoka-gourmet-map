# -*- coding: utf-8 -*-
"""2026-09-30 投稿2本(初音荘・魁龍)をマップへ紐付け"""
import io, json, os, re, shutil, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20260930')
spots = json.load(io.open(P, encoding='utf-8'))
by = {s['id']: s for s in spots}
JST = datetime.timezone(datetime.timedelta(hours=9))
for sid, vid, ts in [('stayc3f0c48796', 'losoGpqyF0c', 1790729430),
                     ('dotonkotsuraamenkairyuuhakat', 'wftX7TRaUBA', 1790767836)]:
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    s['video']['youtube'] = 'https://youtube.com/shorts/%s' % vid
    s['posted'] = datetime.datetime.fromtimestamp(ts, JST).strftime('%Y-%m-%d')
    s['wish'] = False
    print(sid, s['name'], s['posted'])
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

M = os.path.join(R, 'data', '投稿待ち.md')
t = io.open(M, encoding='utf-8').read()
lines = t.split('\n')
keep = [l for l in lines if not (l.startswith('| 2026-09-30 | **魁龍') or l.startswith('| 2026-09-29 | **旅館初音荘'))]
t = '\n'.join(keep)
t = t.replace('## 反映済み(履歴)\n', '## 反映済み(履歴)\n'
              '- 2026-09-30 反映 | 旅館初音荘 stayc3f0c48796 losoGpqyF0c / 魁龍 博多本店 dotonkotsuraamenkairyuuhakat wftX7TRaUBA\n'
              '    ※初音荘は IG 3.9万閲覧・保存710 / TikTok 2.1万再生(投稿当日時点)。宿系の好成績\n', 1)
io.open(M, 'w', encoding='utf-8').write(t)
print('投稿待ち.md 更新 (%d行削除)' % (len(lines) - len(keep)))
