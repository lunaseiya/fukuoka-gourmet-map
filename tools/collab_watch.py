# -*- coding: utf-8 -*-
"""子連れでよく行く&コラボを頻繁にやるチェーン10社のニュース欄を見張る。

  python tools/collab_watch.py           # 各社のニュース見出しから「コラボらしき」ものを拾う
  python tools/collab_watch.py --all     # コラボ判定に関係なく見出しを全部出す

拾えるのは「見出しとURL」まで。**会期と対象店舗はここでは分からない**ので、
候補が出たらWeb検索で会期を確認し、spots.json の該当店に campaign を付ける:

  "campaign": {"title":"ハローキティ コラボ", "label":"キティコラボ",
               "until":"2026-09-06", "untilLabel":"9月6日", "url":"..."}

campaign は until を過ぎるとマップ側で自動的に無効になり、
ピンの金リングとバッジだけが消える(スポット自体は赤/青のまま残る)。
"""
import re, sys, time, urllib.request, urllib.error

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

# 子連れで行く × コラボ頻度が高い10社(2026-08-28ユーザー確定)
SITES = [
 ('くら寿司',        'https://www.kurasushi.co.jp/news/'),
 ('スシロー',        'https://www.akindo-sushiro.co.jp/news/'),
 ('はま寿司',        'https://www.hamazushi.com/topics/'),
 ('マクドナルド',    'https://www.mcdonalds.co.jp/'),
 ('ミスタードーナツ','https://www.misterdonut.jp/whatsnew/'),
 ('サーティワン',    'https://www.31ice.co.jp/'),
 ('ケンタッキー',    'https://japan.kfc.co.jp/news/'),
 ('モスバーガー',    'https://www.mos.jp/'),
 ('ガスト(すかいらーく)','https://www.skylark.co.jp/company/news/'),
 ('丸亀製麺',        'https://www.marugame-seimen.com/news/'),
]
COLLAB = ['コラボ','×','ハローキティ','サンリオ','ちいかわ','ポケモン','すみっコ',
          'ディズニー','ジブリ','マリオ','リラックマ','ミッフィー','スヌーピー',
          'ドラえもん','アンパンマン','プリキュア','仮面ライダー','戦隊',
          'キャンペーン','期間限定','フェア','限定','おもちゃ','ハッピーセット']

def fetch(u):
    try:
        return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20)\
                             .read().decode('utf-8', 'replace')
    except Exception as e:
        return 'ERR:' + repr(e)[:70]

def headlines(html, base):
    out = []
    # <a> のテキストを見出しとして拾う。装飾タグは落とす
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        href, txt = m.group(1), re.sub(r'<[^>]+>', '', m.group(2))
        txt = re.sub(r'\s+', ' ', txt).strip()
        if 6 <= len(txt) <= 90:
            if href.startswith('/'):
                href = re.match(r'(https?://[^/]+)', base).group(1) + href
            out.append((txt, href))
    # 重複を落として順序は保つ
    seen, uniq = set(), []
    for t, h in out:
        if t in seen: continue
        seen.add(t); uniq.append((t, h))
    return uniq

def main():
    show_all = '--all' in sys.argv
    total = 0
    for name, url in SITES:
        h = fetch(url)
        if h.startswith('ERR'):
            print('■ %-14s %s' % (name, h)); time.sleep(1); continue
        hs = headlines(h, url)
        hit = [x for x in hs if any(k in x[0] for k in COLLAB)]
        rows = hs[:12] if show_all else hit[:8]
        print('■ %-14s 見出し%d件 / コラボらしき%d件' % (name, len(hs), len(hit)))
        for t, u in rows:
            print('    %-58s %s' % (t[:58], u[:74]))
        total += len(hit)
        time.sleep(1.2)
    print()
    print('コラボらしき見出し 合計 %d件' % total)
    print('※会期と対象店舗はここでは分からない。候補をWeb検索で確認して campaign を付けること')
    print('COLLAB_WATCH_DONE')

if __name__ == '__main__':
    main()
