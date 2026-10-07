# -*- coding: utf-8 -*-
"""すし酒場 さじ(sushisakaba-saji)が閉業していたため、マップから削除(2026-10-07ユーザー確認)
   写真・サムネも削除。詳細ページは build_pages.py が消す"""
import io, json, os, shutil, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SID = 'sushisakaba-saji'
shutil.copy(P, P + '.bak_remove_saji')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
n0 = len(spots)
assert not [s for s in spots if s.get('in') == SID], '子施設がある'
spots = [s for s in spots if s['id'] != SID]
assert len(spots) == n0 - 1, '対象が見つからない'
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
for f in glob.glob(os.path.join(R, 'map', 'photos', SID + '_*.jpg')) + glob.glob(os.path.join(R, 'map', 'thumbs', SID + '.jpg')):
    os.remove(f); print('削除', os.path.basename(f))
M = os.path.join(R, 'data', '投稿待ち.md')
t = io.open(M, encoding='utf-8').read()
keep = [l for l in t.split('\n') if 'すし酒場 さじ' not in l]
t = '\n'.join(keep).replace('## 反映済み(履歴)\n', '## 反映済み(履歴)\n'
     '- 2026-10-07 削除 | すし酒場 さじ(大名) sushisakaba-saji は閉業していたためマップから削除。動画は投稿せず保留フォルダへ\n', 1)
io.open(M, 'w', encoding='utf-8').write(t)
print('spots', n0, '->', len(spots))
