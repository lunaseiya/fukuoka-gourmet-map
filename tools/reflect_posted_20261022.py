# -*- coding: utf-8 -*-
"""2026-10-22 check_upload_sync で検出した未反映2本をマップへ反映(posted = 一覧の [YYYY-MM-DD](JST))
   GRANDMIRAGE WHOLE NOTE CAFE rVu3CgHq46k / ピエトロ イオンモール筑紫野店 eKpESNIrmKk(どちらも 2026-10-21)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261022')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'
for sid, vid, posted in [('hp7f973060a7', 'rVu3CgHq46k', '2026-10-21'),
                         ('chikushino-rs-pietro', 'eKpESNIrmKk', '2026-10-21')]:
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    assert not s['video'].get('youtube'), sid + ' に既にYouTubeがある'
    s['video']['youtube'] = 'https://youtube.com/shorts/%s' % vid
    s['posted'] = posted
    s['wish'] = False
    print('更新:', sid, s['name'], posted)
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('spots.json 保存')
