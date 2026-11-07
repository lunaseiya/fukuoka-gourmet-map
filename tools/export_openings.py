# -*- coding: utf-8 -*-
"""開業予定リスト(data/openings_list.json)を検証して map/openings.json を書き出す(2026-11-08 新設)。
⚠ data/openings.json は opening_watch.py(巡回ツール)の保存先で別物。手で選んだ公開用の正本は data/openings_list.json。

  python tools/export_openings.py          # 書き出し
  python tools/export_openings.py --check  # 検証だけ

方針(2026-11-08 ユーザー確定):
  - 公開するのは公表資料にあるものだけ。「場所・用途・時期」まで。現場の進み具合の読みは動画側に残す
  - kids_note(子連れの一言)が書けるものが「子連れ」欄、書けないものは「すべて」欄だけ
  - status: planned(工事中・年/季節まで) / dated(開業日や月が決まった) / open(開業済み・opened 必須) / tbd(時期未定)
  - 開業済みは opened から90日で一覧から落とす(データは残す)。30日以内は NEW
  - spots.json の id を持つものは詳細ページへリンクする(存在しない id は警告)
"""
import json, os, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'openings_list.json')
OUT = os.path.join(ROOT, 'map', 'openings.json')
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
STATUS = {'planned', 'dated', 'open', 'tbd'}


def main():
    check = '--check' in sys.argv
    doc = json.load(open(SRC, encoding='utf-8'))
    items = doc['items']
    spot_ids = {s['id'] for s in json.load(open(SPOTS, encoding='utf-8'))}
    today = datetime.date.today()
    seen, out, warn = set(), [], []
    for it in items:
        for k in ('id', 'name', 'kind', 'city', 'status', 'when', 'when_text', 'sources', 'updated'):
            assert k in it, (it.get('id'), k)
        assert it['status'] in STATUS, (it['id'], it['status'])
        assert it['id'] not in seen, it['id']; seen.add(it['id'])
        if it['status'] == 'open':
            assert it.get('opened'), (it['id'], 'open には opened が要る')
        if it.get('spot') and it['spot'] not in spot_ids:
            warn.append(f"spot id が無い: {it['id']} -> {it['spot']}")
        for s in it['sources']:
            assert 't' in s and 'd' in s, (it['id'], s)
        when = datetime.date.fromisoformat(it['when'])
        rec = dict(it)
        rec['kids'] = bool(it.get('kids_note'))
        if it['status'] == 'open':
            od = datetime.date.fromisoformat(it['opened'])
            age = (today - od).days
            if age > 90:
                continue                      # 一覧からは落とす(データは残す)
            rec['new'] = age <= 30
            rec['days'] = -age
        else:
            rec['days'] = (when - today).days
            # 開業予定日を過ぎたのに open になっていないものは「要確認」の印を付ける(自動で開業済みにはしない)
            rec['overdue'] = it['status'] == 'dated' and when < today
        out.append(rec)
    # 並び: 開業済み(新しい順) → 時期が近い順。tbd は when(近似)で並ぶ
    out.sort(key=lambda r: (0 if r['status'] == 'open' else 1, r['days'] if r['status'] != 'open' else -r['days']))
    for w in warn:
        print('WARN', w)
    kids = sum(1 for r in out if r['kids'])
    print(f"{len(items)}件のうち一覧に出すのは {len(out)}件(子連れ {kids} / すべて {len(out)}) / 開業済み {sum(1 for r in out if r['status']=='open')}")
    if check:
        return
    res = {'generated': today.isoformat(), 'items': out}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
