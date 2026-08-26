# -*- coding: utf-8 -*-
"""spots.json から SEO 用の静的ページを生成する。

なぜ必要か:
  マップ(map/index.html)は1枚のSPAで、スポットはJSで描画される。
  検索エンジンから見える実質的なページがトップ1枚しかなく、
  「別府 子連れ 日帰り温泉」のような検索の受け皿が存在しない。
  スポットごとに実体のあるHTMLを置いて、入口を1,000以上に増やすのが目的。

生成物:
  /s/<id>.html        … スポット個別ページ
  /area/<slug>.html   … 市区別の一覧ページ
  /sitemap.xml, /robots.txt

方針:
  - 本文は「子連れ情報」を主役にする。Googleマップにも食べログにも無い一次情報で、
    ここでしか読めないから検索で拾われる価値がある
  - 予約リンク(booking/asoview)は個別ページにも置く。SEO流入がそのまま収益導線になる
  - 各ページからマップ本体へ導線を張り、回遊させる
"""
import json, io, os, re, html, datetime, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
SITE = 'https://lunaseiya.github.io/fukuoka-gourmet-map'
TODAY = datetime.date.today().isoformat()

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def slug(s):
    """市区名 → URLに使える文字列。日本語は残すとURLエンコードが汚いのでローマ字化はせず連番的に扱う"""
    s = re.sub(r'[^\w一-龠ぁ-んァ-ヶー]', '', str(s or ''))
    return s

KIDS_LABEL = [
    ('stroller',  'ベビーカー入店', 'OK', '不可'),
    ('diaper',    'おむつ替え台',   'あり', 'なし'),
    ('tatami',    '座敷・小上がり', 'あり', 'なし'),
    ('kidsChair', 'キッズチェア',   'あり', 'なし'),
]
NOISE = {'ok': '子どもの声はあまり気にならない', 'careful': '静かめ。声のボリュームに配慮を',
         'ng': '静かな店。小さい子連れは要検討'}

def kids_rows(spot):
    k = spot.get('kids') or {}
    rows = []
    for key, label, yes, no in KIDS_LABEL:
        v = k.get(key)
        if v is True:   rows.append((label, yes))
        elif v is False: rows.append((label, no))
    if k.get('serveMin'):
        rows.append(('提供までの目安', '約%d分' % k['serveMin']))
    if k.get('noise') in NOISE:
        rows.append(('客層・騒がしさ', NOISE[k['noise']]))
    return rows

def page_title(s):
    city = s.get('city') or s.get('pref') or '福岡'
    genre = s.get('genre') or 'お店'
    return '%s（%s）| 子連れで行ける%s' % (s['name'], city, genre)

def meta_desc(s):
    v = re.sub(r'\s+', ' ', str(s.get('verdict') or '')).strip()
    v = re.sub(r'[⭐⚠]', '', v)
    base = '%s（%s・%s）の子連れ情報。' % (s['name'], s.get('city') or '', s.get('genre') or '')
    rows = kids_rows(s)
    if rows:
        base += '／'.join('%s:%s' % r for r in rows[:3]) + '。'
    return (base + v)[:158]

def jsonld(s):
    d = {
        '@context': 'https://schema.org',
        '@type': 'LocalBusiness',
        'name': s['name'],
        'url': '%s/s/%s.html' % (SITE, s['id']),
    }
    if s.get('genre'):   d['description'] = str(s.get('verdict') or s['genre'])[:300]
    addr = {'@type': 'PostalAddress', 'addressCountry': 'JP'}
    if s.get('pref'): addr['addressRegion'] = s['pref']
    if s.get('city'): addr['addressLocality'] = s['city']
    if s.get('address'): addr['streetAddress'] = s['address']
    d['address'] = addr
    if s.get('lat') and s.get('lng'):
        d['geo'] = {'@type': 'GeoCoordinates', 'latitude': s['lat'], 'longitude': s['lng']}
    return json.dumps(d, ensure_ascii=False)

CSS = """
body{margin:0;font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic",Meiryo,sans-serif;color:#222;background:#fafafa;line-height:1.75}
.wrap{max-width:720px;margin:0 auto;padding:16px 16px 48px}
header a{color:#d63031;text-decoration:none;font-weight:700}
h1{font-size:22px;margin:14px 0 4px}
.sub{color:#767676;font-size:13px;margin-bottom:14px}
.card{background:#fff;border:1px solid #e5e5e5;border-radius:10px;padding:14px 16px;margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:7px 4px;border-bottom:1px solid #f0f0f0}
th{width:42%;color:#555;font-weight:600}
.btns{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.btn{display:inline-block;padding:10px 14px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;border:1px solid #ddd;color:#222;background:#fff}
.btn.map{background:#d63031;color:#fff;border-color:#d63031}
.btn.jalan{background:#f36f21;color:#fff;border-color:#f36f21}
.btn.aso{background:#00a5a0;color:#fff;border-color:#00a5a0}
.pr{font-size:11px;color:#767676;border:1px solid #e5e5e5;border-radius:4px;padding:1px 5px;align-self:center}
.verdict{white-space:pre-wrap}
footer{margin-top:28px;font-size:12px;color:#767676}
.rel a{display:inline-block;margin:0 10px 8px 0;font-size:14px;color:#d63031;text-decoration:none}
"""

SPOT_TPL = """<!DOCTYPE html>
<html lang="ja"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}/s/{id}.html">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/s/{id}.html">
<link rel="icon" type="image/png" sizes="32x32" href="../icons/favicon-32.png">
<style>{css}</style>
<script type="application/ld+json">{ld}</script>
</head><body><div class="wrap">
<header><a href="../index.html">ふくおか、こそだてグルメ。</a></header>
<h1>{name}</h1>
<div class="sub">{genre}／{city}{area}</div>
{kids_block}
{verdict_block}
<div class="btns">
<a class="btn map" href="../map/index.html#spot={id}">地図で見る</a>
{links}
</div>
{rel_block}
<footer>
情報は掲載時点のものです。最新の営業状況・価格は店舗の公式情報をご確認ください。<br>
<a href="../index.html">ふくおか、こそだてグルメ。</a> ／ <a href="../about.html">このサイトについて</a>
</footer>
</div></body></html>
"""

AREA_TPL = """<!DOCTYPE html>
<html lang="ja"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}/area/{slug}.html">
<link rel="icon" type="image/png" sizes="32x32" href="../icons/favicon-32.png">
<style>{css}</style>
</head><body><div class="wrap">
<header><a href="../index.html">ふくおか、こそだてグルメ。</a></header>
<h1>{city}の子連れで行けるお店・おでかけ {n}件</h1>
<div class="sub">ベビーカーで入れるか、おむつ替え台があるか、キッズチェアがあるか。実際に行って確かめた情報です。</div>
{list_html}
<div class="btns"><a class="btn map" href="../map/index.html">地図で探す</a></div>
<footer><a href="../index.html">ふくおか、こそだてグルメ。</a></footer>
</div></body></html>
"""

def build():
    spots = json.load(io.open(SPOTS, encoding='utf-8'))
    sdir = os.path.join(ROOT, 's'); adir = os.path.join(ROOT, 'area')
    # 作業ディレクトリが Dropbox 配下にあり、同期プロセスがファイルを掴んでいて
    # rmtree が PermissionError(WinError 32) で落ちる。ディレクトリは消さず、
    # 中身を上書きし、最後に「今回作らなかった古いファイル」だけ消す方式にする。
    for d in (sdir, adir):
        os.makedirs(d, exist_ok=True)
    written = {sdir: set(), adir: set()}

    by_city = {}
    for s in spots:
        by_city.setdefault(s.get('city') or 'その他', []).append(s)

    urls = [(SITE + '/', '1.0'), (SITE + '/map/index.html', '0.9')]

    # 1〜2件しかない市区は中身が薄く、低品質ページの量産になる。
    # 3件以上の市区だけ個別ページにし、薄い分は県別ページに集約する。
    # ★スポット個別ページのリンク先もこの集約結果を見る必要があるので、先に決めておく
    #  (先に個別ページを書くと、集約で消えた市区ページへのリンクが切れる)
    MIN_PER_PAGE = 3
    thin = {c: v for c, v in by_city.items() if len(v) < MIN_PER_PAGE}
    pages = {c: v for c, v in by_city.items() if len(v) >= MIN_PER_PAGE}
    for c, v in thin.items():
        for x in v:
            pages.setdefault('%s（その他の市町）' % (x.get('pref') or 'その他'), []).append(x)
    # スポットid -> (一覧ページの表示名, slug)
    listing_of = {}
    for cname, items in pages.items():
        for x in items:
            listing_of[x['id']] = (cname, slug(cname))

    # ---- スポット個別 ----
    for s in spots:
        rows = kids_rows(s)
        kids_block = ''
        if rows:
            trs = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (esc(a), esc(b)) for a, b in rows)
            kids_block = ('<div class="card"><strong>子連れ情報</strong>'
                          '<table>%s</table></div>' % trs)
        verdict_block = ''
        if s.get('verdict'):
            verdict_block = '<div class="card verdict">%s</div>' % esc(s['verdict'])

        links = []
        if s.get('booking'):
            links.append('<a class="btn jalan" href="%s" rel="nofollow noopener" target="_blank">じゃらんで予約</a><span class="pr">PR</span>' % esc(s['booking']))
        if s.get('asoview'):
            links.append('<a class="btn aso" href="%s" rel="nofollow noopener" target="_blank">チケットを買う</a><span class="pr">PR</span>' % esc(s['asoview']))
        if s.get('web'):
            links.append('<a class="btn" href="%s" rel="nofollow noopener" target="_blank">公式サイト</a>' % esc(s['web']))
        v = s.get('video') or {}
        for key, label in (('youtube', 'YouTube'), ('tiktok', 'TikTok'), ('instagram', 'Instagram')):
            if v.get(key):
                links.append('<a class="btn" href="%s" target="_blank" rel="noopener">%s で見る</a>' % (esc(v[key]), label))

        # 関連スポット(内部リンク。回遊とクロール促進)。リンク先は集約後の一覧ページ
        lname, lslug = listing_of.get(s['id'], (s.get('city') or 'その他', slug(s.get('city') or 'その他')))
        sibs = [x for x in pages.get(lname, []) if x['id'] != s['id']][:8]
        rel_block = ''
        if sibs:
            rel_block = ('<div class="card rel"><strong>%s の他のスポット</strong><br>%s<br>'
                         '<a href="../area/%s.html">%s の一覧をすべて見る</a></div>'
                         % (esc(lname),
                            ''.join('<a href="%s.html">%s</a>' % (esc(x['id']), esc(x['name'])) for x in sibs),
                            esc(lslug), esc(lname)))

        htmlstr = SPOT_TPL.format(
            title=esc(page_title(s)), desc=esc(meta_desc(s)), site=SITE, id=esc(s['id']),
            css=CSS, ld=jsonld(s), name=esc(s['name']), genre=esc(s.get('genre') or ''),
            city=esc(s.get('city') or ''), area=('／' + esc(s['area'])) if s.get('area') else '',
            kids_block=kids_block, verdict_block=verdict_block,
            links=''.join(links), rel_block=rel_block)
        fn = s['id'] + '.html'
        io.open(os.path.join(sdir, fn), 'w', encoding='utf-8').write(htmlstr)
        written[sdir].add(fn)
        urls.append(('%s/s/%s.html' % (SITE, s['id']), '0.7'))

    # ---- 一覧ページ ----
    for city, items in sorted(pages.items(), key=lambda x: -len(x[1])):
        sg = slug(city)
        lis = ''.join(
            '<div class="card"><a href="../s/%s.html"><strong>%s</strong></a>'
            '<div class="sub">%s%s</div>%s</div>'
            % (esc(x['id']), esc(x['name']), esc(x.get('genre') or ''),
               ('／' + esc(x['area'])) if x.get('area') else '',
               ('<div>' + esc(re.sub(r'\s+', ' ', str(x.get('verdict'))[:110])) + '…</div>') if x.get('verdict') else '')
            for x in sorted(items, key=lambda y: y['name']))
        htmlstr = AREA_TPL.format(
            title=esc('%s の子連れで行けるお店・おでかけ %d件' % (city, len(items))),
            desc=esc('%s で子連れでも行けるお店とおでかけ先を%d件。ベビーカー可否・おむつ替え台・キッズチェアの有無つき。'
                     % (city, len(items))),
            site=SITE, slug=esc(sg), css=CSS, city=esc(city), n=len(items), list_html=lis)
        io.open(os.path.join(adir, sg + '.html'), 'w', encoding='utf-8').write(htmlstr)
        written[adir].add(sg + '.html')
        urls.append(('%s/area/%s.html' % (SITE, sg), '0.8'))

    # 今回生成しなかった残骸を削除(スポットを消したときにページが残らないように)
    removed = 0
    for d, keep in written.items():
        for fn in os.listdir(d):
            if fn.endswith('.html') and fn not in keep:
                try:
                    os.remove(os.path.join(d, fn)); removed += 1
                except OSError:
                    pass
    if removed:
        print('  古いページを削除', removed, '件')

    # ---- sitemap / robots ----
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr in urls:
        sm.append('<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>'
                  % (html.escape(u), TODAY, pr))
    sm.append('</urlset>')
    io.open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm))
    io.open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n' % SITE)

    print('スポットページ %d枚 / 一覧 %d枚 / sitemap %d URL'
          % (len(spots), len(pages), len(urls)))
    print('  ※1〜2件の市区 %d件は県別ページに集約' % len(thin))

if __name__ == '__main__':
    build()
