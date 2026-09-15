# -*- coding: utf-8 -*-
"""**県が公表している公式の対象宿泊施設一覧**と spots.json を突合して `fukko` を書く。

■ なぜ fukko_watch.py と別に要るか【2026-09-15に判明】
  fukko_watch.py は「じゃらんの宿ページに応援割プランが並んでいるか」で判定するが、
  **じゃらんは特設ページ型**(対象宿を選ぶと支払画面で自動割引)で、
  宿ページに「ふっこう応援割」の文字が出ない。
  そのため熊本15件のうち14件を「記載なし」と誤判定した(実際は13件が対象)。
  → 県が一覧を公表している場合は**そちらを正**とする。こちらのほうが確実で速い。

■ 公表状況(2026-09-15)
  熊本県: https://kumamoto-ouenwari.com/yoshiki/ichiran.pdf  … 295施設。公表あり
  長崎県: https://www.nagasaki-tabinet.com/feature/ouenwari … 一覧の公表なし
  ⚠memory の「対象施設の公式リストは公表されない」は**熊本については誤り**だった

■ 突合の注意(両方向で外した)
  ・取りこぼし: 「清流荘」は3文字。「4文字以上」の条件を付けると
    公式の「菊池温泉　旅館　清流荘」に当たらない
  ・誤マッチ: 「亀の井ホテル 阿蘇」が公式の「亀の井ホテル阿蘇パークリゾート」に
    部分一致して対象になった。**この2つは別ホテル**(2026-09-15ユーザー確定)
  → このスクリプトは**id を明示した対応表**で書く。名寄せは候補出しまでに留める

使い方:
    python tools/fukko_apply_official.py            # ドライラン
    python tools/fukko_apply_official.py --apply
"""
import io, json, os, shutil, sys
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

SRC_KUMAMOTO = 'https://kumamoto-ouenwari.com/yoshiki/ichiran.pdf'

# id → 公式一覧での表記。**公式PDFを人が読んで確定した対応表**
# (名前の自動照合だけに任せると上の2種類の事故が起きるため、ここに固定する)
OFFICIAL = {
    # ⚠id は28文字で切り詰められている。フルスペルで書くと「spots.json に無い」になる
    'asouchimakionsenyunoyadoirif':    '湯の宿入船',
    'stay7886375829':                  '阿蘇リゾートグランヴィリオホテル',
    'stay298de35348':                  'ホテル角萬',
    'spfc736bcead':                    '阿蘇内牧温泉　湯巡追荘',
    'stay1e73c478d1':                  '亀の井ホテル阿蘇パークリゾート',
    'minamiasofiirudohoteru':          '南阿蘇フィールドホテル',
    'tsuetate-hizenya':                'つえたて温泉ひぜんや',
    'yamamizuki':                      '山あいの宿　山みず木',
    'ikoiryokan':                      '黒川温泉　いこい旅館',
    'seiryuusou':                      '菊池温泉　旅館　清流荘',
    'stay0279fbae65':                  '湯本の荘 夢ほたる',
    'hoteruareguriagaadenzuamakus':    'ホテルアレグリアガーデンズ天草',
    'stay95124bf207':                  'ホテル竜宮',
}

# ⚠公式一覧に**載っていない**と確認したもの。間違って足さないよう明示して残す
NOT_LISTED = {
    'kamenoi-aso': '亀の井ホテル 阿蘇 … 公式一覧にあるのは「亀の井ホテル阿蘇パークリゾート」だけ。別ホテル',
    'tochigionsenoyamaryokan': '栃木温泉 小山旅館 … 公式に「鮎返りの滝を望む宿　小山旅館」があり同一の可能性。名称が違うため保留',
}

NOTE = '熊本県公式の宿泊施設一覧に掲載(2026-09-15確認)。クーポン枠は県単位で変動する'


def main():
    apply_ = '--apply' in sys.argv[1:]
    spots = json.load(io.open(P, encoding='utf-8'))
    by = {s['id']: s for s in spots}
    today = date.today().isoformat()

    print('=== 公式一覧に基づく fukko の付与 %s ===' % ('(書き込み)' if apply_ else '(ドライラン)'))
    print('出典: %s' % SRC_KUMAMOTO)
    print()
    miss = [i for i in OFFICIAL if i not in by]
    if miss:
        print('!! spots.json に無い id: %s' % ' '.join(miss))
        print('   (id が変わっている可能性。対応表を直してから再実行)')
        return

    n = skip = 0
    for i, official_name in OFFICIAL.items():
        s = by[i]
        if s.get('pref') != '熊本県':
            print(' !! %-26s pref=%s で熊本県ではない。飛ばす' % (s['name'][:26], s.get('pref')))
            skip += 1
            continue
        had = 'fukko' in s
        print(' ○ %-24s %-9s → 公式「%s」%s'
              % (s['name'][:24], s.get('city', ''), official_name, ' (既にfukko有り・上書き)' if had else ''))
        if apply_:
            s['fukko'] = {'checked': today,
                          'url': s.get('booking') or '',
                          'official': official_name,
                          'source': SRC_KUMAMOTO,
                          'note': NOTE}
        n += 1

    print()
    print('=== 対象にしないもの ===')
    for i, why in NOT_LISTED.items():
        s = by.get(i)
        print(' × %-24s %s' % ((s['name'][:24] if s else i), why))

    if not apply_:
        print()
        print('※ ドライランです。--apply を付けて再実行してください')
        return

    # --- 書き込み前のバックアップと、書き込み後の検算 -----------------------
    shutil.copy(P, P + '.bak_fukko_official')
    io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
    print()
    print('spots.json に %d件 書き込みました (バックアップ: .bak_fukko_official)' % n)

    chk = json.load(io.open(P, encoding='utf-8'))
    ids = [s['id'] for s in chk]
    dup = {i for i in ids if ids.count(i) > 1}
    # ⚠`(s.get('video') or {}).values()` だけでは判定にならない。
    #   {'youtube': None} の values() は**要素があるので truthy**。
    #   2026-09-15にこれで1177件の誤警告を出した。必ず any() で中身を見る
    bad = [s['id'] for s in chk
           if s.get('wish') and any(v for v in (s.get('video') or {}).values())]
    fk = [s for s in chk if s.get('fukko')]
    print('検算: 件数 %d / id重複 %d / wish=trueなのに動画URL %d / fukko付き %d'
          % (len(chk), len(dup), len(bad), len(fk)))
    if dup:
        print('  !! id重複: %s' % ' '.join(sorted(dup)))
    if bad:
        print('  !! wish=true なのに動画URLがある: %s' % ' '.join(bad[:20]))
    print('※ build_pages.py を回してから push すること')


if __name__ == '__main__':
    main()
