# -*- coding: utf-8 -*-
"""ららぽーと福岡×京鼎樓 回の投稿をマップに反映する【2026-09-16】

YouTube: https://youtu.be/_ZBdF3T9RRQ (private + publishAt 2026-09-16 07:00 JST の予約)

■ 紐付け先は**2スポット**
  この回は台本で「**主役は店ではなく ららぽーと福岡**」と決めている(子連れ設備が半分を占める)。
  京鼎樓はその具体例なので、**両方に同じ動画を付ける**。
  どちらも既に赤ピン(訪問済み)なので、足すのは video.youtube と posted だけ。

⚠`posted` は本来 `yt-dlp --print upload_date` で実投稿日を取る決まりだが、
  **予約投稿(private)の段階では取得できない**。予約時刻の日付(2026-09-16)を入れておき、
  公開後に `check_upload_sync.py` で突合して確認する(はま寿司回・めんちゃん回と同じ運用)。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

URL = 'https://youtu.be/_ZBdF3T9RRQ'
POSTED = '2026-09-16'          # 予約時刻の日付。公開後に突合で確認する
TARGETS = ['jindinrou', 'lalaportfukuoka']

s = json.load(io.open(P, encoding='utf-8'))
shutil.copy(P, P + '.bak_post_jindinrou')
before = {}
for i in TARGETS:
    x = [y for y in s if y['id'] == i]
    if not x:
        raise SystemExit('!! %s が無い' % i)
    x = x[0]
    before[i] = {'wish': x.get('wish'), 'visited': x.get('visited'),
                 'lat': x.get('lat'), 'lng': x.get('lng')}
    v = x.get('video') or {'youtube': None, 'tiktok': None, 'instagram': None}
    if v.get('youtube'):
        print('  ⚠%s は既に YouTube URL あり: %s (上書きしない)' % (i, v['youtube']))
    else:
        v['youtube'] = URL
        x['video'] = v
        print('  %s ← %s' % (i, URL))
    x['posted'] = POSTED
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算 ──────────────────────────────────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
ids = [z['id'] for z in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
bad = [z['id'] for z in s2
       if z.get('wish') and any((z.get('video') or {}).get(k) for k in ('youtube', 'tiktok', 'instagram'))]
ng = []
for i in TARGETS:
    y = [z for z in s2 if z['id'] == i][0]
    after = {'wish': y.get('wish'), 'visited': y.get('visited'),
             'lat': y.get('lat'), 'lng': y.get('lng')}
    if after != before[i]:
        ng.append(i)
    print('  %-18s posted=%s youtube=%s ピン/座標=%s'
          % (i, y.get('posted'), (y.get('video') or {}).get('youtube'),
             '変化なし ✓' if after == before[i] else '⚠変わった'))
print('件数 %d / id重複 %d件 / wish=trueなのに動画URLあり %d件' % (len(s2), len(dup), len(bad)))
if dup or bad or ng:
    raise SystemExit('!! 検算NG %s %s %s' % (dup[:3], bad[:3], ng))
print('OK')
