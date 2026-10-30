# -*- coding: utf-8 -*-
"""2026-10-30 天神ストリートパーク開業回(tenjin-street-park)の3媒体予約をマップへ反映
   YouTube vsW7yjE-nGk 10/30(金)17:00 / TikTok 7702351558842912007 10/30(金)19:00 / Instagram 10/30(金)21:00(URLは公開後)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261030_tsp')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}
s = by['tenjin-street-park']
assert not s['video'].get('youtube')
s['video']['youtube'] = 'https://youtube.com/shorts/vsW7yjE-nGk'
s['video']['tiktok'] = 'https://www.tiktok.com/@tencone/video/7702351558842912007'
s['posted'] = '2026-10-30'; s['wish'] = False
print('更新:', s['id'], s['posted'], s['video'])
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
