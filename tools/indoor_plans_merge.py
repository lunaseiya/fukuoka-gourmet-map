# -*- coding: utf-8 -*-
"""簡易フロア図(data/indoor_plans.json)に、施設ごとの図の座標をまとめる(2026-11-09)。

  python tools/indoor_plans_merge.py <plans*.json があるフォルダ>

- 公式の館内図はなぞらない。位置関係だけを自前の図形で描くための座標を持つ
- 範囲外の点・存在しない spot id のピン・長すぎるラベルは直すか落として、その件数を出す
- 図を作れなかった施設は data/indoor_図が無い施設.md に書き出す
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'indoor_plans.json')
plans = json.load(open(P, encoding='utf-8'))
spots = json.load(open(os.path.join(ROOT, 'data', 'spots.json'), encoding='utf-8'))
ids = {s['id'] for s in spots}
name = {s['id']: s['name'] for s in spots}

failed, fixed = {}, 0


def clamp(v, hi):
    return max(0, min(hi, v))


for f in sorted(glob.glob(os.path.join(sys.argv[1], 'plans*.json'))):
    r = json.load(open(f, encoding='utf-8'))
    failed.update(r.get('_failed') or {})
    for fid, floors in r.items():
        if fid.startswith('_') or not isinstance(floors, dict):
            continue
        good = {}
        for fl, F in floors.items():
            if fl.startswith('_') or not isinstance(F, dict):
                continue
            W, H = F.get('w', 1000), F.get('h', 600)
            for a in F.get('areas', []):
                for k, hi in (('x', W), ('y', H)):
                    if not 0 <= a.get(k, 0) <= hi:
                        a[k] = clamp(a.get(k, 0), hi); fixed += 1
                a['w'] = min(a.get('w', 0), W - a['x']); a['h'] = min(a.get('h', 0), H - a['y'])
                if len(a.get('label', '')) > 12:
                    a['label'] = a['label'][:12]; fixed += 1
            for key in ('icons', 'pins', 'labels'):
                for q in F.get(key, []):
                    if not (0 <= q.get('x', 0) <= W and 0 <= q.get('y', 0) <= H):
                        q['x'] = clamp(q.get('x', 0), W); q['y'] = clamp(q.get('y', 0), H); fixed += 1
            n0 = len(F.get('pins', []))
            F['pins'] = [q for q in F.get('pins', []) if q.get('id') in ids]
            fixed += n0 - len(F['pins'])
            if F.get('areas'):
                good[fl] = F
        if good:
            plans[fid] = good
            failed.pop(fid, None)

json.dump(plans, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'indoor_plans.json: {len(plans)}施設 / 直した・落とした点 {fixed}件 / 図なし {len(failed)}件')
md = ['# 簡易フロア図を作れなかった施設(公式の図が無い・形が読めない)', '',
      '館内モードの文字の一覧(設備とお店の階)はこれらの施設でも出ている。図が欲しい施設は、現地の館内フロアガイドを撮ってくれば描ける。', '']
for fid, why in sorted(failed.items(), key=lambda x: name.get(x[0], x[0])):
    md.append(f'- {name.get(fid, fid)}(`{fid}`): {why}')
open(os.path.join(ROOT, 'data', 'indoor_図が無い施設.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
