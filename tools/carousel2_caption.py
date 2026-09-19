# -*- coding: utf-8 -*-
"""シルバーウィーク20選のキャプションを媒体別に書き出す【2026-09-19】

`event_caption.py` は候補JSONの `selected` を読むが、今回のカルーセルは
`carousel2_build.PICK` の20件を**エリア順**に並べている。カードとキャプションで
並びや件数が食い違うと読者が照合できないので、**同じ20件・同じ順**の中間JSONを作って渡す。

⚠**Instagram/TikTok は2200字**しかないので20件は入らない(1件≒110字)。
  `event_caption.py` は入らない分を末尾から落とす作りだが、それだと
  **筑後(最後のエリア)だけ丸ごと消える**。エリアで偏るのは不公平なので、
  SNS向けは**1件1行の短い形**にして20件全部を載せる(検索ワードはカード側にある)。
  YouTube は5000字あるので従来の詳しい形+公式URLのまま。
"""
import io, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
import carousel2_build as CB
from carousel2 import area_of, daylabel

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = CB.OUT
FROM, TO = '2026-09-19', '2026-09-23'
LIMIT = 2200
MARGIN = 80


def clen(s):
    """SNSの字数は UTF-16 のコードユニット(絵文字=2)で数える"""
    return len(s.encode('utf-16-le')) // 2


def pick(C):
    evs = []
    for k in CB.PICK:
        hit = [r for r in C['events'] if k in r['title']]
        if not hit:
            print('!! 候補に無い:', k)
            continue
        r = dict(hit[0])
        if not r.get('city'):
            r['city'] = CB.CITY_FIX.get(k, '')
        r['_short'] = k
        evs.append(r)
    evs.sort(key=lambda e: [a[0] for a in
             __import__('carousel2').AREAS].index(area_of(e.get('city'))))
    return evs


def sns(evs, ov):
    """Instagram / TikTok 用。1件1行で20件全部載せる"""
    L = ['【福岡】シルバーウィーク 子連れおでかけ20選', '9/19(土)〜9/23(水・祝)', '',
         '連休どこ行く？のためにまとめました。',
         '画像に会場・時間・料金・検索ワードを入れてます。', '']
    cur = ''
    for i, e in enumerate(evs, 1):
        ar = area_of(e.get('city'))
        if ar != cur:
            L.append('▼%s' % ar)
            cur = ar
        o = ov.get(e['url']) or {}
        name = (o.get('name') or e['title']).strip()
        venue = (o.get('venue') or e.get('venue') or '').strip()
        # 館内の場所は落として施設名だけにする
        venue = venue.split(' ')[0] if venue else (e.get('city') or '')
        L.append('%d. %s / %s / %s%s'
                 % (i, name[:26], venue[:16], daylabel(e),
                    '' if not e.get('free') else ' 無料'))
    L += ['', '──────────',
          '保存して連休の計画に使ってね📌',
          '期間限定イベントはプロフィールのマップにも載せてます🗺', '',
          '※画像は各主催者・施設の告知物です(出典は各カードに記載)',
          '※キャラクター作品の画像は権利の都合で掲載していません',
          '※お出かけ前に公式サイトで最新情報をご確認ください', '',
          '#福岡イベント #シルバーウィーク #子連れおでかけ #福岡ママ #福岡子連れ']
    return '\n'.join(L) + '\n'


def main():
    C = json.load(io.open(os.path.join(ROOT, 'data', '_週末イベント候補.json'),
                          encoding='utf-8'))
    OV = os.path.join(ROOT, 'data', '_イベント表示名.json')
    ov = json.load(io.open(OV, encoding='utf-8')) if os.path.exists(OV) else {}
    evs = pick(C)

    # ── YouTube は event_caption.py に任せる(URLがクリックできるので全部貼る) ──
    tmp = os.path.join(ROOT, 'data', '_sw_caption_src.json')
    json.dump({'from': FROM, 'to': TO, 'events': evs,
               'selected': [e['url'] for e in evs]},
              io.open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, '-X', 'utf8',
                    os.path.join(HERE, 'event_caption.py'),
                    '--dir', OUT, '--json', tmp,
                    '--today', FROM, '--title', 'シルバーウィーク'],
                   check=True)

    # ── Instagram / TikTok は短い形で上書きして20件全部載せる ──
    s = sns(evs, ov)
    for p in ('instagram', 'tiktok'):
        io.open(os.path.join(OUT, '_キャプション_%s.txt' % p), 'w',
                encoding='utf-8').write(s)
    print('%-10s %4d字(UTF-16) / 上限%d  %s  掲載%d件(全件)'
          % ('ig/tiktok', clen(s), LIMIT,
             'OK' if clen(s) <= LIMIT - MARGIN else '超過!', len(evs)))
    # ハッシュタグは**5個**(タイトル4/キャプション5/概要欄5)。毎回数える
    print('ハッシュタグ %d個' % s.count('#'))


if __name__ == '__main__':
    main()
