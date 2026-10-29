# -*- coding: utf-8 -*-
"""2026-10-30 初代秀ちゃん ラーメンスタジアム店(canalcity_02)の3媒体予約をマップへ反映
   YouTube AE6R5Exq0ts 11/1(日)07:00 / TikTok 7702139023007026440 11/5(木)18:00 / Instagram 11/1(日)21:00(URLは公開後)
   posted = YouTube公開日 2026-11-01"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20261030')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'
s = by['canalcity_02']
s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
assert not s['video'].get('youtube'), 'canalcity_02 に既にYouTubeがある'
s['video']['youtube'] = 'https://youtube.com/shorts/AE6R5Exq0ts'
s['video']['tiktok'] = 'https://www.tiktok.com/@tencone/video/7702139023007026440'
s['posted'] = '2026-11-01'
s['wish'] = False
print('更新:', s['id'], s['name'], s['posted'], s['video'])
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('spots.json 保存')
