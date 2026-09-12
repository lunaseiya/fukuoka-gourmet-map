# -*- coding: utf-8 -*-
"""カルーセルに載せた期間限定イベントを **マップ(spots.json)へ登録する**。
【2026-09-13ユーザー確定「掲載した内容については期間限定イベントとしてMAP登録もされるように」】

投稿 → マップにも載る → プロフィールのリンクから見れる、の導線を閉じるための最後の一手。

■ 登録の形(map-spot スキル準拠)
  ・`category: "play"`(遊び場タブ) + `until` / `untilLabel`
    → **単発イベント扱い**。白地ピン+金リング+⏳ が付き、「⏳期間限定」タブに出る。
      **会期を過ぎたら地図から自動で消える**ので消し忘れが構造的に起きない
  ・`wish: true`(青ピン=未訪問) / `visited: null`
  ・⚠**常設店に until を付けてはいけない**。ここで登録するのは会期のあるイベントだけ
  ・未確認の項目は **null**。推測で埋めない
  ・書き換え前に spots.json をバックアップ

■ 鉄則
  ・**既存と重複させない**。名前一致と座標近傍(300m)の両方で照合する
  ・ジオコーディングは geocoding.jp を **10秒以上あけて** 叩く(住所で引く。名前では引かない)
  ・住所が取れていないイベントは**登録しない**(座標を推測しない)。一覧に理由を出す
  ・`--apply` なしはドライラン。一覧を見て承認をもらってから書く

使い方:
    python tools/event_to_map.py                    # ドライラン
    python tools/event_to_map.py --apply            # 実際に登録
"""
import argparse, io, json, math, os, re, shutil, sys, time, urllib.parse, urllib.request
from datetime import date, datetime

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
SPOTS = os.path.join(HERE, '..', 'data', 'spots.json')
CAND = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
UA = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ja'}
WK = '月火水木金土日'


def _geo1(addr):
    u = 'https://www.geocoding.jp/api/?q=' + urllib.parse.quote(addr)
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode('utf-8')
    except Exception:
        return None, None
    la = re.search(r'<lat>([\d.]+)</lat>', r)
    ln = re.search(r'<lng>([\d.]+)</lng>', r)
    if not (la and ln) or float(la.group(1)) == 0:
        return None, None
    return float(la.group(1)), float(ln.group(1))


def geocode(addr):
    """住所で引く。**イベントの住所は末尾に施設名がくっついていることが多い**ので
    (例「…津田1丁目4-7TNC住宅展示場きてミテ！小倉」)、失敗したら番地までで切って再試行する。
    2026-09-13: これが無いと陶芸教室・大野城心のふるさと館が両方 <lat>0</lat> で落ちた。"""
    cands = [addr]
    # 〒 と全角空白を落としたもの
    c = re.sub(r'^〒?\s*[0-9０-９]{3}-?[0-9０-９]{4}\s*', '', addr).replace('　', ' ').strip()
    if c != addr:
        cands.append(c)
    # 丁目/番地までで打ち切る(末尾の施設名・建物名・カッコ書きを落とす)
    m = re.match(r'(.*?[都道府県].*?[市区町村].*?[0-9０-９][0-9０-９\-ー丁目番地の／]*[0-9０-９])', c)
    if m and m.group(1) != c:
        cands.append(m.group(1))
    for n, q in enumerate(dict.fromkeys(cands)):
        if n:
            time.sleep(11)
            print('      ↳ 住所を詰めて再試行: %s' % q[:44])
        lat, lng = _geo1(q)
        if lat is not None:
            return lat, lng
    return None, None


def slug(t):
    """id は半角英数とハイフンのみ。日本語は使えないので日付+連番で作る"""
    s = re.sub(r'[^0-9A-Za-z]+', '-', t).strip('-').lower()
    return ('ev-' + s)[:40] if s else ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--json', default=CAND)
    a = ap.parse_args()
    D = json.load(io.open(a.json, encoding='utf-8'))
    by = {e['url']: e for e in D['events']}
    evs = [by[u] for u in D.get('selected', []) if u in by]
    sp = json.load(io.open(SPOTS, encoding='utf-8'))
    names = {re.sub(r'[\s　]+', '', s.get('name', '')) for s in sp}
    urls = set()
    for s in sp:
        for k in ('official', 'url'):
            if s.get(k):
                urls.add(s[k])

    plan, skip = [], []
    for i, e in enumerate(evs, 1):
        title = re.sub(r'\s+', ' ', e['title']).strip()
        key = re.sub(r'[\s　]+', '', title)
        if e.get('from_map'):
            skip.append((title, 'すでにマップ登録済み(この源から来ている)')); continue
        if key in names:
            skip.append((title, '同名がすでにある')); continue
        addr = e.get('addr') or ''
        borrow = None
        if not addr:
            # ★**会場が既にマップに登録済みなら、その座標と住所を借りる**
            #   (2026-09-13: ららぽーと福岡/キャナルシティ博多/イオンモール各館は登録済みで、
            #    住所が取れないだけで見送っていた。推測ではなく既存データの流用なので安全)
            vn = [e.get('place')] + list(e.get('venues') or [])
            for v in [x for x in vn if x]:
                vk = re.sub(r'[\s　]+', '', v)
                for t in sp:
                    tk = re.sub(r'[\s　]+', '', t.get('name', ''))
                    if tk and (tk == vk or (len(vk) >= 6 and vk in tk) or (len(tk) >= 6 and tk in vk))                             and t.get('lat') and t.get('lng'):
                        borrow = t
                        break
                if borrow:
                    break
        if not addr and not borrow:
            skip.append((title, '住所も会場の既存登録も無い(会場=%s)'
                         % (e.get('place') or (e.get('venues') or [''])[0])))
            continue
        end = e['span'][1]
        if not end:
            skip.append((title, '終了日が無い')); continue
        plan.append({'ev': e, 'title': title, 'addr': addr, 'until': end, 'borrow': borrow})

    print('=== マップ登録の計画 (%s) ===' % ('実行' if a.apply else 'ドライラン'))
    print('登録する: %d件 / 見送る: %d件' % (len(plan), len(skip)))
    print()
    for p in plan:
        e = p['ev']
        d = datetime.strptime(p['until'], '%Y-%m-%d').date()
        print('  ○ %s' % p['title'][:52])
        print('      会場 %s' % (e.get('place') or (e.get('venues') or ['-'])[0]))
        if p.get('borrow'):
            print('      座標 %s の登録を流用 (%.5f, %.5f)'
                  % (p['borrow']['name'][:26], p['borrow']['lat'], p['borrow']['lng']))
        else:
            print('      住所 %s' % p['addr'][:56])
        print('      until %s (%d月%d日まで)' % (p['until'], d.month, d.day))
    print()
    for t, r in skip:
        print('  × %-46s %s' % (t[:44], r))
    if not a.apply:
        print()
        print('※ --apply で実際に登録します')
        return

    shutil.copy(SPOTS, SPOTS + '.bak_events')
    added = 0
    for n, p in enumerate(plan):
        if p.get('borrow'):
            lat, lng = p['borrow']['lat'], p['borrow']['lng']
            p['addr'] = p['borrow'].get('address') or p['addr'] or None
        else:
            if n:
                time.sleep(11)        # geocoding.jp は10秒以上あける
            lat, lng = geocode(p['addr'])
        if lat is None:
            print('  ! ジオコーディング失敗、登録しない:', p['title'][:40]); continue
        # 座標の近傍300m に同じものが無いか(表記ゆれ対策)
        dup = None
        for s in sp:
            if s.get('lat') and s.get('lng'):
                dd = math.hypot((s['lat'] - lat) * 111000,
                                (s['lng'] - lng) * 111000 * math.cos(math.radians(lat)))
                if dd < 300 and s.get('until'):
                    dup = s['name']; break
        if dup:
            print('  ! 近傍300mに期間限定スポットあり、登録しない:', p['title'][:34], '≒', dup)
            continue
        e = p['ev']
        d = datetime.strptime(p['until'], '%Y-%m-%d').date()
        sid = slug(e.get('url', '').rsplit('/', 1)[-1]) or slug(str(n))
        while any(s['id'] == sid for s in sp):
            sid += 'x'
        sp.append({
            'id': sid, 'name': p['title'][:60],
            'area': e.get('place') or '', 'city': e.get('city') or '', 'pref': '福岡県',
            'genre': '期間限定イベント', 'lat': lat, 'lng': lng, 'address': p['addr'],
            'visited': None, 'with': 'family',
            'kids': {'stroller': None, 'diaper': None, 'tatami': None,
                     'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
            'verdict': (e.get('lead') or '')[:200] or None,
            'video': {'youtube': None, 'tiktok': None, 'instagram': None},
            'thumb': None, 'wish': True, 'category': 'play',
            'until': p['until'], 'untilLabel': '%d月%d日' % (d.month, d.day),
            'official': e.get('official') or e.get('url'),
        })
        added += 1
        print('  + %s (%s)' % (p['title'][:40], sid))
    io.open(SPOTS, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    import collections
    c = collections.Counter(s['id'] for s in sp)
    bad = [s['id'] for s in sp if s.get('wish') and any((s.get('video') or {}).values())]
    print()
    print('登録 %d件 / 総数 %d / id重複 %d / 青ピンに動画がある矛盾 %d'
          % (added, len(sp), len([k for k, v in c.items() if v > 1]), len(bad)))
    print('※ python tools/build_pages.py を回してから push すること')


if __name__ == '__main__':
    main()
