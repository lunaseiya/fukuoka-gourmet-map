# -*- coding: utf-8 -*-
"""館内モードのデータ(data/indoor.json)に、公式フロアマップから集めた事実をまとめる(2026-11-09)。

  python tools/indoor_merge.py <result*.json があるフォルダ>

result*.json の形: {"done": {id: {floors, amenities, tenants, source, checked}}, "failed": {id: 理由}}
- 公式の館内図の画像は持たない(著作権)。階・場所・設備という事実だけを持つ
- 地下街(kind=ug)の通路の形(corridor)など、手で書いた項目は上書きしない
- tenants は spots.json に実在する id だけ残す
- 取れなかった施設は data/indoor_取れなかった施設.md に書き出す(現地で館内図を撮ってもらう候補)
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'indoor.json')
src = sys.argv[1]

conf = json.load(open(P, encoding='utf-8'))
spots = json.load(open(os.path.join(ROOT, 'data', 'spots.json'), encoding='utf-8'))
ids = {s['id'] for s in spots}
name = {s['id']: s['name'] for s in spots}
name['ug-tenjin'] = '天神地下街'

done, failed = {}, {}
for f in sorted(glob.glob(os.path.join(src, 'result*.json'))):
    r = json.load(open(f, encoding='utf-8'))
    done.update(r.get('done') or {})
    failed.update(r.get('failed') or {})

for fid, d in done.items():
    if fid not in ids and fid not in conf:
        print('不明なid(飛ばす):', fid)
        continue
    e = conf.get(fid, {})
    if e.get('kind') != 'ug':
        e['kind'] = 'mall'
    if d.get('floors'):
        e['floors'] = d['floors']
    am = [a for a in (d.get('amenities') or []) if a.get('kind')]
    if am:
        e['amenities'] = [{k: a[k] for k in ('floor', 'kind', 'where') if a.get(k) is not None} for a in am]
    ten = {k: v for k, v in (d.get('tenants') or {}).items() if k in ids and v}
    if ten:
        e['tenants'] = ten
    e['source'] = d.get('source') or e.get('source')
    e['checked'] = d.get('checked') or '2026-11-09'
    conf[fid] = e
    failed.pop(fid, None)

json.dump(conf, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'indoor.json: {len(conf)}件(今回 取得{len(done)} / 取れず{len(failed)})')

md = ['# 館内図がWebで取れなかった施設(現地で館内図・フロアガイドを撮ってきてほしい候補)', '',
      f'更新: 2026-11-09 / 取れた施設は data/indoor.json', '']
for fid, why in sorted(failed.items(), key=lambda x: name.get(x[0], x[0])):
    md.append(f'- {name.get(fid, fid)}(`{fid}`): {why}')
open(os.path.join(ROOT, 'data', 'indoor_取れなかった施設.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
