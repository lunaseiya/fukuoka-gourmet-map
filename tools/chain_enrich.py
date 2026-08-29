# -*- coding: utf-8 -*-
"""chain_cache.json の設備欄(食べログ実データ)を spots.json に反映する。

  python tools/chain_enrich.py            # 何が変わるかを出すだけ
  python tools/chain_enrich.py --apply    # 実際に書き込む

先に `python tools/chain_collect.py --refresh` で設備欄を取得しておくこと。

■ 何を埋めるか
  食べログの「席・設備」に書かれている**実データだけ**を使う。チェーンの一般論では埋めない。
    席数の内訳に 座敷/掘りごたつ/小上がり がある  → kids.tatami = True
    お子様連れ欄に「ベビーカー入店可」            → kids.stroller = True
  個室・駐車場・お子様連れの文言は verdict に文章で足す(フィルタ条件には使わない)。

■ 上書きしない
  すでに True/False が入っている項目は触らない。
  赤ピンは現地で見て記録した値のほうが正しいので、ネットの情報で塗り替えてはいけない。
"""
import json, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'data', 'spots.json')
CACHE = os.path.join(ROOT, 'data', 'chain_cache.json')
MARK = '食べログの店舗情報では'


def main():
    apply = '--apply' in sys.argv
    sp = json.load(io.open(MAP, encoding='utf-8'))
    cache = json.load(io.open(CACHE, encoding='utf-8'))
    by_url = {s.get('tabelog'): s for s in sp if s.get('tabelog')}

    n_tatami = n_stroller = n_verdict = 0
    rows = []
    for url, d in cache.items():
        s = by_url.get(url)
        if not s or 'kidsline' not in d:
            continue
        k = s.setdefault('kids', {})
        changed = []
        if d.get('tatami') and k.get('tatami') is None:
            k['tatami'] = True; n_tatami += 1; changed.append('座敷')
        kl = d.get('kidsline') or ''
        if 'ベビーカー' in kl and k.get('stroller') is None:
            k['stroller'] = True; n_stroller += 1; changed.append('ベビーカー')
        # 食べログの「お子様連れ」欄は 子供可 / 子供可、お子様メニューあり の2種類しか入っていない。
        # 「子供可」だけでは設備が分からない(どの店も書ける)のでフィルタには使わず verdict に留める。
        # 「お子様メニューあり」は具体的なサービスなので kidsMenu に上げる
        if 'お子様メニュー' in kl and k.get('kidsMenu') is None:
            k['kidsMenu'] = True; changed.append('キッズメニュー')

        # 設備の文章。すでに足してあるなら作り直す(再実行しても増えない)
        bits = []
        if d.get('tatami'):
            bits.append('座敷あり')
        if d.get('private') == '有':
            bits.append('個室あり')
        if d.get('parking') == '有':
            bits.append('駐車場あり')
        if kl:
            bits.append('お子様連れ:' + kl)
        if d.get('seatnote'):
            sn = re.sub(r'\s+', '', d['seatnote']).replace('|', ' ')
            sn = re.sub(r'（+', '(', sn).replace('）', ')').replace('))', ')')
            bits.append('席数' + sn)
        if bits:
            base = re.split(re.escape(MARK), s.get('verdict') or '')[0].rstrip()
            # 設備が1つでも判明したら「子連れ設備は未確認」は嘘になるので消す
            if d.get('tatami') or 'お子様メニュー' in kl:
                base = base.replace('子連れ設備は未確認。', '').strip()
            s['verdict'] = re.sub(r'\s+', ' ', base + ' ' + MARK + '、'.join(bits) + '。').strip()
            n_verdict += 1
        if changed:
            rows.append((s['name'], s.get('city') or '', '+'.join(changed)))

    print('=== 食べログの設備欄から埋めた ===')
    for n, c, ch in sorted(rows, key=lambda r: r[0]):
        print('  %-32s %-12s %s' % (n[:32], c, ch))
    print()
    print('座敷(tatami=True) %d件 / ベビーカー(stroller=True) %d件 / verdict更新 %d件'
          % (n_tatami, n_stroller, n_verdict))

    ok = sum(1 for s in sp if s.get('wish') and any(
        (s.get('kids') or {}).get(x) is True
        for x in ['stroller', 'diaper', 'tatami', 'kidsChair', 'kidsMenu']))
    print('反映後、子連れOKで出る青ピン %d件' % ok)

    if apply:
        io.open(MAP, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print('書き込んだ')
    else:
        print('※ドライラン。実際に書くには --apply')
    print('ENRICH_DONE')


if __name__ == '__main__':
    main()
