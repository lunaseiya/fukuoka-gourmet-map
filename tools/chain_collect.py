# -*- coding: utf-8 -*-
"""食べログのチェーン店一覧から、指定都道府県の全店舗を集めてキャッシュに貯める。

  python tools/chain_collect.py G00237 焼肉きんぐ          # 1チェーン
  python tools/chain_collect.py --all                      # CHAINS に書いた全部

食べログの店舗ページには JSON-LD が入っていて、名前・住所・緯度経度が全部取れる。
geocoding.jp を叩く必要がないのでここで座標まで確定させる。

出力: data/chain_cache.json
  { "<tabelog店舗URL>": {name, chain, addr, city, lat, lng, genre, tel} }

※チェーンのグループIDは tabelog.com/grouplst/<ID>/fukuoka/ の <ID> 部分。
  推測で書かない。「tabelog grouplst <チェーン名> 福岡県」で検索して実物を確認すること。
"""
import json, io, os, re, sys, time, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'data', 'chain_cache.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
PREF = 'fukuoka'

# (グループID, チェーン名) — すべて実際に tabelog で存在を確認したもの
CHAINS = [
    ('G00237', '焼肉きんぐ'),
    ('G01641', '焼肉なべしま'),
    ('G00012', '牛角'),
    ('G00074', 'スシロー'),
    ('G00075', 'くら寿司'),
    ('G00080', 'かっぱ寿司'),
    ('G01214', '魚べい'),
    ('G00169', 'はま寿司'),
    ('G02196', 'ワンカルビ'),
    ('G00187', 'すたみな太郎'),
]

def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30)\
                         .read().decode('utf-8', 'replace')

def list_shops(gid):
    """グループ一覧をページ送りしながら店舗URLを集める"""
    urls, page = [], 1
    while page <= 12:
        u = 'https://tabelog.com/grouplst/%s/%s/' % (gid, PREF)
        if page > 1:
            u += '%d/' % page
        try:
            h = get(u)
        except Exception as e:
            print('  一覧取得エラー p%d %r' % (page, e)); break
        found = re.findall(r'href="(https://tabelog\.com/%s/A\d+/A\d+/\d+/)"' % PREF, h)
        new = [x for x in dict.fromkeys(found) if x not in urls]
        if not new:
            break
        urls += new
        print('  p%d: +%d件 (計%d)' % (page, len(new), len(urls)))
        page += 1
        time.sleep(1.0)
    return urls

def shop_detail(u):
    h = get(u)
    def one(p, s=h):
        m = re.search(p, s)
        return m.group(1).strip() if m else None
    name = one(r'<title>(.*?)\s*-\s*[^-]*?\|\s*食べログ</title>')
    lat, lng = one(r'"latitude"\s*:\s*"?([\d.]+)'), one(r'"longitude"\s*:\s*"?([\d.]+)')
    city, street = one(r'"addressLocality"\s*:\s*"([^"]+)'), one(r'"streetAddress"\s*:\s*"([^"]+)')
    region = one(r'"addressRegion"\s*:\s*"([^"]+)')
    # 閉店・移転はここで弾く
    closed = bool(re.search(r'(閉店しました|移転しました|<span[^>]*>閉店</span>)', h))
    return {
        'name': name,
        'addr': ((region or '') + (city or '') + (street or '')) or None,
        'city': city,
        'lat': float(lat) if lat else None,
        'lng': float(lng) if lng else None,
        'genre': one(r'"servesCuisine"\s*:\s*"([^"]+)'),
        'tel': one(r'"telephone"\s*:\s*"([^"]+)'),
        'closed': closed,
    }

def search_shops(kw):
    """食べログにグループ登録が無いローカルチェーン用。県内をキーワード検索して拾う。
    玄風館のような老舗チェーンはグループ化されていないのでこちらを使う。"""
    urls, page = [], 1
    while page <= 6:
        u = 'https://tabelog.com/%s/rstLst/%s/?sw=%s' % (
            PREF, page if page > 1 else '', urllib.parse.quote(kw))
        try:
            h = get(u)
        except Exception as e:
            print('  検索エラー p%d %r' % (page, e)); break
        found = re.findall(r'href="(https://tabelog\.com/%s/A\d+/A\d+/\d+/)"' % PREF, h)
        new = [x for x in dict.fromkeys(found) if x not in urls]
        if not new:
            break
        urls += new
        print('  p%d: +%d件 (計%d)' % (page, len(new), len(urls)))
        page += 1
        time.sleep(1.0)
    return urls


def main():
    cache = json.load(io.open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
    # --kw <検索語> <チェーン名> [店名フィルタの正規表現]
    #   食べログのキーワード検索は関連の薄い店も混ぜて返す(「玄風館」で とよ唐亭 等が出る)。
    #   店名がフィルタに一致したものだけ採る。省略時は検索語そのもの
    name_re = None
    if '--kw' in sys.argv:
        i = sys.argv.index('--kw')
        targets = [('KW:' + sys.argv[i + 1], sys.argv[i + 2])]
        name_re = re.compile(sys.argv[i + 3] if len(sys.argv) > i + 3 else re.escape(sys.argv[i + 1]))
    elif '--all' in sys.argv:
        targets = CHAINS
    else:
        targets = [(sys.argv[1], sys.argv[2])]
    for gid, chain in targets:
        print('■ %s (%s)' % (chain, gid))
        urls = search_shops(gid[3:]) if gid.startswith('KW:') else list_shops(gid)
        print('  一覧 %d件' % len(urls))
        got = 0
        for u in urls:
            if u in cache:
                continue
            try:
                d = shop_detail(u)
            except Exception as e:
                print('    詳細エラー %s %r' % (u, e)); time.sleep(1.0); continue
            if name_re and not name_re.search(d.get('name') or ''):
                continue    # 検索が拾った無関係な店
            d['chain'] = chain
            d['tabelog'] = u
            cache[u] = d
            got += 1
            flag = ' ※閉店' if d['closed'] else ''
            print('    %-34s %s%s' % ((d['name'] or '?')[:34], (d['addr'] or '住所なし')[:30], flag))
            time.sleep(1.2)
        print('  新規 %d件 / キャッシュ計 %d件' % (got, len(cache)))
        io.open(CACHE, 'w', encoding='utf-8').write(json.dumps(cache, ensure_ascii=False, indent=1))
    print('CHAIN_COLLECT_DONE')

if __name__ == '__main__':
    main()
