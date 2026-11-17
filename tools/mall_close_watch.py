"""モール公式の「閉店のお知らせ」ウォッチ(さよならシリーズ用・2026-11-17 ユーザー確定)
「なくなった後に気づいても意味がない」「報道やお知らせを拾うくらいが数字を狙える」
→ 閉店日つきで事前に出る、モール公式のお知らせを毎日見る。

  python tools/mall_close_watch.py          … 新しく見つかった閉店(閉店日が今日以降)を出し、見納めリストへ足す
  python tools/mall_close_watch.py --all    … いま各モールに載っている閉店を全部出す(既読も)

既読は data/モール閉店_既読.json。お知らせは閉店後に消えるモールが多いので、毎日見て記録する。
調べた結果(13/24館が取れる・取れない館の理由)は docstring の末尾。
"""
import os, re, sys, json, datetime, html
sys.path.insert(0, os.path.dirname(__file__))
import requests
import opening_watch as ow
import closing_watch as cw

D = os.path.join(os.path.dirname(__file__), '..', 'data')
SEEN = os.path.join(D, 'モール閉店_既読.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36'}
TODAY = datetime.date.today()


def get(url, **kw):
    try:
        r = requests.get(url, headers={**UA, **kw.pop('headers', {})}, timeout=30, **kw)
        r.encoding = r.apparent_encoding if r.encoding in (None, 'ISO-8859-1') else r.encoding
        return r if r.status_code == 200 else None
    except Exception as e:
        print('  !', url, e)
        return None


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def ymd(s):
    """「2026年11月15日」「2026.9.27」「11/30」「9月24日」 → date。年なしは今年(半年以上前なら来年)"""
    s = ow.norm(s) if hasattr(ow, 'norm') else s
    m = re.search(r'(20\d\d)\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})', s)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.search(r'(?<!\d)(\d{1,2})\s*[月/]\s*(\d{1,2})(?!\d)', s)
        if not m:
            return None
        mo, d = map(int, m.groups())
        y = TODAY.year
        try:
            if datetime.date(y, mo, d) < TODAY - datetime.timedelta(days=180):
                y += 1
        except ValueError:
            return None
    try:
        return datetime.date(y, mo, d)
    except ValueError:
        return None


def near_close_date(page):
    """詳細ページの本文から、閉店・営業終了に一番近い日付"""
    t = text(page)
    best = None
    for m in re.finditer(r'閉店|営業終了|最終営業日|をもちまして', t):
        seg = t[max(0, m.start() - 60):m.end() + 40]
        d = ymd(seg)
        if d:
            return d
    return best


# ---- 館ごとの読み取り(各関数は [dict(mall, shop, close, url)] を返す) ----

def tenchika():
    r = get('https://www.tenchika.com/new-close/')
    if not r:
        return []
    sec = re.search(r'id="close".*', r.text, re.S)
    out = []
    # li の中に入れ子の li があるので、</li> ではなく次の項目の頭で切る
    for it in (sec.group(0) if sec else '').split('<li class="c-shop-card__item"')[1:]:
        head = text((re.search(r'p-card-head[^"]*">(.*?)</div>', it, re.S) or [0, ''])[1])
        name = text((re.search(r'c-shop-card__name[^"]*">(.*?)</p>', it, re.S) or [0, ''])[1])
        loc = text((re.search(r'c-shop-card__location">(.*?)</p>', it, re.S) or [0, ''])[1])
        if name:
            out.append(dict(mall='天神地下街', shop=f'{name}({loc})', close=ymd(head), url='https://www.tenchika.com/new-close/'))
    return out


def amu():
    r = get('https://www.jrhakatacity.com/floor/open_close/')
    if not r:
        return []
    sec = re.search(r'class="openclose-block" id="close".*', r.text, re.S)
    out = []
    for it in re.findall(r'<div class="box">.*?</dl>', sec.group(0) if sec else '', re.S):
        g = lambda c: text((re.search(r'class="%s">(.*?)</d' % c, it, re.S) or [0, ''])[1])
        dd = text((re.search(r'<dd>(.*?)</dd>', it, re.S) or [0, ''])[1])
        if g('shop'):
            out.append(dict(mall='JR博多シティ(' + g('facility') + ')', shop=f"{g('shop')}({g('floor')})", close=ymd(dd),
                            url='https://www.jrhakatacity.com/floor/open_close/'))
    return out


def amu_open():
    """JR博多シティの NEW OPEN 欄。跡地ウォッチ(data/跡地ウォッチ.json)と同じ館・階なら「跡地に入る店」として出す
    (2026-11-17 ユーザー: だるまデイトス店の後も、たぶんラーメン屋。チェックしたい)"""
    r = get('https://www.jrhakatacity.com/floor/open_close/')
    sec = re.search(r'class="openclose-block" id="open"(.*?)class="openclose-block"', r.text if r else '', re.S)
    out = []
    for it in re.findall(r'<div class="box">.*?</dl>', sec.group(1) if sec else '', re.S):
        g = lambda c: text((re.search(r'class="%s">(.*?)</d' % c, it, re.S) or [0, ''])[1])
        dd = text((re.search(r'<dd>(.*?)</dd>', it, re.S) or [0, ''])[1])
        if g('shop'):
            out.append(dict(mall='JR博多シティ(' + g('facility') + ')', facility=g('facility'), floor=g('floor'),
                            shop=g('shop'), open=ymd(dd), note=dd, url='https://www.jrhakatacity.com/floor/open_close/'))
    return out


def atochi_report(show_all):
    """跡地ウォッチ: 閉店した店の館・階に、新しく入る店が出たら知らせる"""
    watch = cw_json(os.path.join(D, '跡地ウォッチ.json'), [])
    seen_p = os.path.join(D, 'モール開店_既読.json')
    seen = set(cw_json(seen_p, []))
    rows = []
    for e in amu_open():
        key = e['mall'] + '|' + e['shop']
        if key in seen and not show_all:
            continue
        seen.add(key)
        if e['open'] and e['open'] < TODAY - datetime.timedelta(days=7):
            continue
        hit = [w for w in watch if w['facility'] in e['facility'] and w['floor'] == e['floor']]
        rows.append((e, hit))
    if not show_all:
        json.dump(sorted(seen), open(seen_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return rows


def daimaru():
    r = get('https://www.daimaru-fukuoka.jp/shopblog/search/?keyword=%E9%96%89%E5%BA%97')
    out = []
    for href, body in re.findall(r'<a href="(/shopblog/detail/[^"]+)"(.*?)</a>', r.text if r else '', re.S):
        title = text((re.search(r'class="title">(.*?)</div>', body, re.S) or [0, ''])[1])
        if re.search(r'【\s*閉\s*店\s*の\s*お\s*知\s*ら\s*せ\s*】', title):
            out.append(dict(mall='大丸福岡天神店', shop=re.sub(r'【.*?】', '', title).strip(), close=None,
                            url='https://www.daimaru-fukuoka.jp' + html.unescape(href), detail=True))
    return out


def konoha():
    r = get('https://konohamall.com/news/infomation/')
    out = []
    m = re.search(r'閉店店舗のお知らせ.*?(?=<h3|\Z)', r.text if r else '', re.S)
    if m:
        # 本文は色付きの span が入れ子なので、タグを外してから「■フロア 「店名」 日付 営業終了」で読む
        for floor, name, when in re.findall(r'■([^■「]*)「([^」]+)」([^■]*?営業終了)', text(m.group(0))):
            out.append(dict(mall='木の葉モール橋本', shop=f'{name.strip()}({floor.strip()})', close=ymd(when),
                            url='https://konohamall.com/news/infomation/'))
    return out


def canal():
    r = get('https://canalcity.co.jp/shopsearch/category')
    out = []
    for href, body in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r.text if r else '', re.S):
        lab = text((re.search(r'c-post__label">(.*?)</p>', body, re.S) or [0, ''])[1])
        if lab.startswith('【閉店】'):
            out.append(dict(mall='キャナルシティ博多', shop=lab.replace('【閉店】', '').strip(), close=None,
                            url=href if href.startswith('http') else 'https://canalcity.co.jp' + href, detail=True))
    return out


def lalaport():
    base = 'https://mitsui-shopping-park.com'
    r = get(base + '/lalaport/fukuoka/openrenewal/')
    out = []
    for href, body in re.findall(r'<a href="(/lalaport/fukuoka/openrenewal/\d+\.html)"(.*?)</a>', r.text if r else '', re.S):
        title = text((re.search(r'md-col4_04__box__title">(.*?)</p>', body, re.S) or [0, ''])[1])
        if '閉店' in title:
            out.append(dict(mall='ららぽーと福岡', shop=re.sub(r'閉店のお知らせ', '', title).strip(), close=ymd(title), url=base + href))
    return out


def islandeye():
    r = get('https://island-eye.com/topics')
    out = []
    for href, title in re.findall(r'<a href="(https://island-eye.com/topics/\d+)"[^>]*>(.*?)</a>', r.text if r else '', re.S):
        title = text(title)
        if '閉店' in title:
            out.append(dict(mall='アイランドアイ', shop=title.replace('閉店のお知らせ', '').strip(), close=None, url=href, detail=True))
    return out


def marui():
    r = get('https://www.0101.co.jp/contents2/storenews/090/store_article_list.json')
    out = []
    try:
        arts = r.json()['store_article_list']['store_article']
    except Exception:
        return out
    for a in arts:
        if '閉店' not in a.get('title', ''):
            continue
        body = a.get('text_2', '') or ''
        for blk in re.split(r'●', body)[1:]:
            t = text(blk)
            name = re.split(r'閉店日', t)[0].strip()
            out.append(dict(mall='博多マルイ', shop=name[:60], close=ymd(t.split('閉店日')[-1]) if '閉店日' in t else None,
                            url='https://www.0101.co.jp/090/'))
    return out


def aeon(slug, code, name):
    r = get(f'https://{slug}.aeonmall.jp/api/external-api?endpoint=news&limit=200&mall_code={code}',
            headers={'x-internal-request': 'true'})
    out = []
    try:
        items = r.json()['news']['items']
    except Exception:
        return out
    for it in items:
        cat = (it.get('newsCategory') or {}).get('name', '')
        title = it.get('title', '')
        if cat == '閉店' or '閉店' in title:
            out.append(dict(mall=name, shop=title.replace('閉店のお知らせ', '').strip(), close=ymd(title),
                            url=f"https://{slug}.aeonmall.jp/news/renewal/{it.get('id', '')}", detail=not ymd(title)))
    return out


SOURCES = [tenchika, amu, daimaru, konoha, canal, lalaport, islandeye, marui,
           lambda: aeon('fukuoka', 1016, 'イオンモール福岡'), lambda: aeon('chikushino', 1131, 'イオンモール筑紫野')]


def main():
    show_all = '--all' in sys.argv
    seen = set(cw_json(SEEN, []))
    found, errors = [], []
    for fn in SOURCES:
        try:
            got = fn()
        except Exception as e:
            errors.append(f'{getattr(fn, "__name__", "aeon")}: {e}')
            continue
        found += got
    new = []
    for e in found:
        key = e['mall'] + '|' + e['shop']
        if key in seen and not show_all:
            continue
        if e.get('detail') and not e['close']:
            r = get(e['url'])
            e['close'] = near_close_date(r.text) if r else None
        seen.add(key)
        # 閉店日が過ぎたものは見納めにならない。日付不明は残す(記事で確認)
        if e['close'] and e['close'] < TODAY:
            continue
        new.append(e)
    if not show_all:
        json.dump(sorted(seen), open(SEEN, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        add_to_closings(new)
    new.sort(key=lambda e: e['close'] or datetime.date(2100, 1, 1))
    opens = atochi_report(show_all)
    open_lines = [f"  {'★跡地(' + h[0]['after'] + 'の後)' if h else '開店'} {e['note']} {e['mall']} {e['floor']} / {e['shop']}"
                  for e, h in opens]
    if '--quiet' in sys.argv:
        # タスクスケジューラ(news_watch --quiet から1日1回)。速報の受け箱に足し、Windowsの通知を出す
        if open_lines:
            import news_watch as nw
            with open(nw.INBOX, 'a', encoding='utf-8') as f:
                f.write(f"--- {datetime.datetime.now():%Y-%m-%d %H:%M} JR博多シティの開店 ---\n" + '\n'.join(open_lines) + '\n')
            hits = [(e, h) for e, h in opens if h]
            if hits:
                nw.toast('跡地に入る店', f"{hits[0][1][0]['after']}の後: {hits[0][0]['shop']}"[:60])
        if new:
            import news_watch as nw
            with open(nw.INBOX, 'a', encoding='utf-8') as f:
                f.write(f"--- {datetime.datetime.now():%Y-%m-%d %H:%M} モールの閉店のお知らせ ---\n" + '\n'.join(
                    f"  [見納め] {e['close'] or '日付は詳細で'} {e['mall']} / {e['shop']}  {e['url']}" for e in new) + '\n')
            nw.toast('さよなら候補 %d件' % len(new), f"{new[0]['mall']} / {new[0]['shop']}"[:60])
        return
    print(f'== モールの閉店のお知らせ(新着・閉店日が今日以降): {len(new)}件 ==')
    for e in new:
        left = f"あと{(e['close'] - TODAY).days}日" if e['close'] else '閉店日は詳細で確認'
        print(f"  {e['close'] or '----------'}  {left:8} {e['mall']} / {e['shop']}\n      {e['url']}")
    print(f'== JR博多シティの開店(新着・跡地ウォッチ照合): {len(open_lines)}件 ==')
    print('\n'.join(open_lines))
    if errors:
        print('  ! 読めなかった館:', ' / '.join(errors))


def cw_json(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


def add_to_closings(rows):
    """見納めリスト(closings.json → 見納めリスト.txt・撮影先の提案の見納め枠)に足す"""
    if not rows:
        return
    items = cw_json(cw.OUT_JSON, [])
    known = {x['name'] for x in items}
    for e in rows:
        name = f"{e['shop']} 閉店({e['mall']})"
        if name in known:
            continue
        items.append(dict(name=name, when=f"{e['close'].year}年{e['close'].month}月{e['close'].day}日" if e['close'] else '',
                          when_iso=e['close'].isoformat() if e['close'] else '', area=e['mall'], url=e['url'],
                          src='モール公式', pub=TODAY.isoformat()))
    json.dump(items, open(cw.OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    real, sys.stdout = sys.stdout, open(os.devnull, 'w', encoding='utf-8')
    try:
        cw.show(items)
    finally:
        sys.stdout = real


if __name__ == '__main__':
    main()

# 調べた結果(2026-11-17)
#  取れる: 天神地下街 /new-close/ ・アミュ(JR博多シティ) /floor/open_close/ ・大丸 shopblog検索「閉店」・木の葉モール橋本
#          ・キャナル(店舗一覧の【閉店】ラベル)・ららぽーと福岡 /openrenewal/ ・アイランドアイ /topics
#          ・博多マルイ(store_article_list.json の「閉店ショップのご案内」)・イオンモール福岡/筑紫野(external-api・x-internal-request)
#  載らない/取れない: 博多阪急・岩田屋・ソラリア・ミーナ・ワンビル・ゆめタウン博多(閉店のお知らせを出さない)
#          ・パルコ(建物ごと2027/2閉館)・KITTE博多(古い例のみ)・MARK IS(POST API・閉店の例なし)・トリアス(RSSあり・例なし)
#          ・イオンモール香椎浜/福岡伊都(新ドメインのslug不明)・BRANCH(公式なし)
