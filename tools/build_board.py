"""撮影ボード(ユーザー専用・非公開)を作る。2026-11-17 ユーザー確定
「テキストがバラバラのところにあって見にくい。私専用のページが欲しい。ブックマークする。
 何の撮影をしたほうが良いのか、撮影済みで投稿済みなのかも分かると良い」

  python tools/build_board.py      → ショート動画用/撮影ボード/撮影ボード.html(Dropbox。マップのリポジトリには置かない=公開しない)
  できたら Claude が Artifact で同じファイルを publish し直す(URL は memory project-shooting-board)

集めるもの: 見納め(closings.json) / 開店・開業予定(openings.json) / 速報ウォッチの候補(速報候補.json) /
           工事中パトロールのフォルダ / 投稿予定と投稿済み(呼び水コメント.json)
状態(未撮影・撮影済・予約済・投稿済): data/撮影ボード_状態.json で項目とフォルダ・投稿の題を結び、
  フォルダに素材があれば撮影済、呼び水台帳で予約中なら予約済、投稿が出ていれば投稿済。
⚠方針: 開店・閉店の一覧は公開しない(独占して先に撮るため)。マップには自分が投稿したものから載せる。
"""
import os, re, sys, json, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'data')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))   # ショート動画用
OUT = os.path.join(ROOT, '撮影ボード', '撮影ボード.html')
TODAY = datetime.date.today()
NOW = datetime.datetime.now()
MEDIA = re.compile(r'\.(mov|mp4|m4v|jpg|jpeg|heic|png)$', re.I)
NEAR = re.compile(r'福岡市|新宮|古賀|糟屋|粕屋|志免|宇美|須恵|篠栗|久山|春日|大野城|太宰府|筑紫野|那珂川|糸島|宗像|福津|博多|天神|中洲|香椎')


def jl(name, d):
    try:
        return json.load(open(os.path.join(D, name), encoding='utf-8'))
    except Exception:
        return d


def iso(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None


LEDGER = jl('撮影ボード_状態.json', [])
POSTS = jl('呼び水コメント.json', [])


def folder_info(rel):
    """素材の数と、いちばん新しい撮影日(ファイル名の日付 → 更新日時)。公表資料・完成フォルダは数えない"""
    p = os.path.join(ROOT, rel)
    if not os.path.isdir(p):
        return 0, None
    n, last = 0, None
    for dp, dns, fns in os.walk(p):
        dns[:] = [x for x in dns if not re.search(r'公表資料|完成|過去動画|00_', x)]
        for f in fns:
            if not MEDIA.search(f):
                continue
            n += 1
            m = re.search(r'(20\d\d)-(\d\d)-(\d\d)', f)
            d = datetime.date(*map(int, m.groups())) if m else None
            if d and (not last or d > last):
                last = d
    return n, last


def post_state(topic):
    rows = [e for e in POSTS if e['topic'] == topic]
    if not rows:
        return None
    done = sorted(e['publish_at'] for e in rows if e['status'] == 'done' or iso(e['publish_at']) and e['publish_at'] <= NOW.strftime('%Y-%m-%d %H:%M'))
    pend = sorted(e['publish_at'] for e in rows if e['publish_at'] > NOW.strftime('%Y-%m-%d %H:%M'))
    plats = sorted({e['platform'] for e in rows})
    return dict(done=done, pend=pend, plats=plats)


def status_of(name, flash=False):
    """→ (状態, 補足, フォルダ)。速報の見出しは地名で誤爆するので、店名で結んだ項目(flash: true)だけ見る"""
    for l in LEDGER:
        if (flash and not l.get('flash')) or not re.search(l['match'], name):
            continue
        if l.get('status') and not l.get('topic') and not l.get('folder'):
            return l['status'], l.get('note', ''), None
        ps = post_state(l['topic']) if l.get('topic') else None
        n, last = folder_info(l['folder']) if l.get('folder') else (0, None)
        note = l.get('note', '')
        if ps and ps['done']:
            extra = f"{ps['done'][0][5:10].replace('-', '/')} 投稿" + (f" / 次 {ps['pend'][0][5:10].replace('-', '/')}" if ps['pend'] else '')
            return '投稿済', (extra + ' ' + note).strip(), l.get('folder')
        if ps and ps['pend']:
            return '予約済', (f"{ps['pend'][0][5:10].replace('-', '/')} 公開予定 " + note).strip(), l.get('folder')
        if n:
            return '撮影済', (f"素材{n}本" + (f"・最終 {last.month}/{last.day}" if last else '') + ' ' + note).strip(), l.get('folder')
        return l.get('status', '未撮影'), note, l.get('folder')
    return '未撮影', '', None


def closings():
    out = []
    for x in jl('closings.json', []):
        d = iso(x.get('when_iso', ''))
        if d and d < TODAY:
            continue
        st, note, fd = status_of(x['name'])
        out.append(dict(name=x['name'], date=d.isoformat() if d else '', left=(d - TODAY).days if d else None,
                        when=x.get('when', ''), area=x.get('area', ''), url=x.get('url', ''), src=x.get('src', ''),
                        st=st, note=note, folder=fd or ''))
    out.sort(key=lambda r: (r['left'] is None, r['left'] if r['left'] is not None else 0, r['name']))
    return out


def openings():
    out = []
    for x in jl('openings.json', []):
        d = iso(x.get('when_iso', ''))
        if d and d < TODAY - datetime.timedelta(days=3):
            continue
        name = x.get('name') or x.get('title', '')
        area = x.get('area', '') or x.get('address', '')
        st, note, fd = status_of(name)
        out.append(dict(name=name, kind=x.get('kind', ''), date=d.isoformat() if d else '', left=(d - TODAY).days if d else None,
                        when=x.get('when', ''), area=area, url=x.get('src_url', ''), near=bool(NEAR.search(area + name)),
                        st=st, note=(note or x.get('note', '') or '')[:80], folder=fd or ''))
    out.sort(key=lambda r: (not r['near'], r['left'] is None, r['left'] if r['left'] is not None else 0))
    return out


def flashes():
    since = (NOW - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    out, seen = [], set()
    import news_watch as nw   # 同じ話題をまとめる判定(same_story)を借りる
    for e in reversed(jl('速報候補.json', [])):
        # fresh が無いのは基準を直す前(2026-11-17の初回)の記録。古い記事の再掲が混ざるので出さない
        if e.get('found', '') < since or e.get('fresh') is not True or any(nw.same_story(t, e['title']) for t in seen):
            continue
        seen.add(e['title'])
        st, note, _ = status_of(e['title'], flash=True)
        out.append(dict(name=e['title'], score=e.get('score', 0), at=e.get('at', ''), src=e.get('src', ''),
                        media=len(e.get('media', [])), url=e.get('url', ''), close=bool(e.get('close')), st=st, note=note,
                        places=e.get('places', [])))
    out.sort(key=lambda r: -r['score'])
    return out[:12]


def patrol():
    base = os.path.join(ROOT, '工事中パトロール')
    readme = open(os.path.join(base, 'README_一覧.txt'), encoding='utf-8', errors='ignore').read()
    out = []
    for f in sorted(os.listdir(base)):
        if not re.match(r'\d\d_', f) or not os.path.isdir(os.path.join(base, f)):
            continue
        m = re.search(re.escape(f) + r'\s*…\s*(.+)', readme)
        st, note, _ = status_of(f[3:])
        n, last = folder_info('工事中パトロール/' + f)
        out.append(dict(name=f[3:], no=f[:2], plan=(m.group(1).strip() if m else '')[:110], n=n,
                        last=last.isoformat() if last else '', since=(TODAY - last).days if last else None, st=st, note=note))
    return out


def schedule():
    rows = [e for e in POSTS if e['publish_at'] >= NOW.strftime('%Y-%m-%d %H:%M')]
    rows.sort(key=lambda e: e['publish_at'])
    return [dict(at=e['publish_at'], plat=e['platform'], topic=e['topic']) for e in rows[:24]]


def main():
    data = dict(built=NOW.strftime('%Y-%m-%d %H:%M'), today=TODAY.isoformat(), closings=closings(), openings=openings(),
                flashes=flashes(), patrol=patrol(), schedule=schedule())
    tpl = open(os.path.join(HERE, 'board_template.html'), encoding='utf-8').read()
    page = tpl.replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write(page)
    print(OUT, '見納め', len(data['closings']), '開店', len(data['openings']), '速報', len(data['flashes']),
          '工事', len(data['patrol']), '予定', len(data['schedule']))


if __name__ == '__main__':
    main()
