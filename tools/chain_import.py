# -*- coding: utf-8 -*-
"""chain_cache.json に集めたチェーン店を spots.json に青ピンで登録する。

  python tools/chain_import.py            # 何が入るかを出すだけ(ドライラン)
  python tools/chain_import.py --apply    # 実際に書き込む

■ 子連れ設備の扱い【重要】
ユーザーの体感(「焼肉と回転寿司はボックス席や子供椅子があることが多い」)は正しいが、
**推測でフラグを立てない**のがこのマップの原則。よって下の CHAIN_KIDS には
**公式サイトで明記を確認できたチェーンだけ** true を入れている。
裏が取れなかったチェーンは全部 None のままにする(=子連れOKフィルタには出ない)。
実際に行って確認できたら、その店だけ後から true に上げる。

■ 赤/青
すべて wish=True(青ピン)。ユーザーが行っていない店を赤にしてはいけない。
既に赤で入っている店は座標・店名で照合してスキップする。
"""
import json, io, os, re, sys, hashlib, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'data', 'spots.json')
CACHE = os.path.join(ROOT, 'data', 'chain_cache.json')

# 公式の記載を実際に読んで確認したものだけ true にする(2026-08-29 確認)
CHAIN_KIDS = {
    'スシロー': dict(
        kids=dict(kidsChair=True, diaper=True, kidsMenu=None),
        note='公式FAQに「子供椅子、おむつ台はありますか？→設置しております」と明記。'),
    'くら寿司': dict(
        kids=dict(kidsChair=True, diaper=True, kidsMenu=True),
        note='ベビーチェア・おむつ交換台あり(訪問済みの同チェーン5店で実地確認)。お子様応援セットあり。'),
    'はま寿司': dict(
        kids=dict(kidsChair=True, diaper=None, kidsMenu=True),
        note='公式FAQに「お子様用の補助いすは全店舗にご用意しております」と明記。キッズメニュー「はまっこセット」あり。'),
    '焼肉きんぐ': dict(
        kids=dict(kidsChair=True, diaper=True, kidsMenu=False),
        note='公式「お子様連れのお客様へ」に赤ちゃん用イス・おむつ交換台の用意を明記(取扱いの無い店舗もあり)。'
             '専用キッズメニューは無いと公式に明記。食べ放題。'),
    '牛角': dict(
        kids=dict(kidsChair=None, diaper=None, kidsMenu=True),
        note='公式メニューにキッズ9品(キッズプレート480円・キッズカレープレート480円等)。子供椅子は公式に記載なし。'),
    # --- 以下は公式の明記を確認できなかったので子連れフラグを立てない ---
    'かっぱ寿司': dict(kids={}, note='回転寿司チェーン。子連れ設備は未確認。'),
    '魚べい': dict(kids={}, note='回転寿司チェーン(元気寿司グループ)。子連れ設備は未確認。'),
    '焼肉なべしま': dict(kids={}, note='九州の焼肉チェーン。サラダバーあり。子連れ設備は未確認。'),
    'ワンカルビ': dict(kids={}, note='焼肉食べ放題チェーン。子連れ設備は未確認。'),
    'すたみな太郎': dict(kids={}, note='焼肉・寿司のバイキングチェーン。子連れ設備は未確認。'),
}
KIDS_KEYS = ['stroller', 'diaper', 'tatami', 'kidsChair', 'serveMin', 'noise']


# 食べログのタイトルに混ざる余計な文字。店名として出す前に落とす
def clean_name(s):
    s = s or ''
    s = re.sub(r'【旧店名】.*$', '', s)
    s = re.sub(r'\s*（[ァ-ヶー・\s]+）\s*$', '', s)   # （ギュウカク）等のカタカナ読み
    s = re.sub(r'（.*?）|\(.*?\)', '', s)
    s = re.sub(r'[（(].*$', '', s)                    # 閉じ括弧が無いまま切れている分
    s = re.sub(r'のご予約\s*$', '', s)                # 予約ページのタイトルを拾った分
    s = re.sub(r'^無添\s*', '', s)                    # 「無添くら寿司」→「くら寿司」
    s = re.sub(r'^あきんど(?=スシロー)', '', s)        # 「あきんどスシロー」→「スシロー」
    return re.sub(r'\s+', ' ', s).strip()


def norm(s):
    return re.sub(r'\s|　|・|-|ー', '', clean_name(s)).replace('ヶ', 'ケ')


# 同じチェーンだと分かるための別名。座標が近いだけの別テナントを同一視しないために使う
ALIAS = {
    'くら寿司': ['くら寿司'], 'スシロー': ['スシロー'], 'はま寿司': ['はま寿司'],
    'かっぱ寿司': ['かっぱ寿司'], '魚べい': ['魚べい', '元気寿司'],
    '焼肉きんぐ': ['焼肉きんぐ', '焼肉キング'], '牛角': ['牛角'],
    '焼肉なべしま': ['なべしま'], 'ワンカルビ': ['ワンカルビ'], 'すたみな太郎': ['すたみな太郎'],
}


def dist_m(a, b, c, d):
    if None in (a, b, c, d):
        return 9e9
    return math.hypot((a - c) * 111000, (b - d) * 92000)


def area_of(addr, city):
    """住所から町名だけを取り出して area にする(丁目・番地は落とす)"""
    if not addr:
        return None
    t = addr
    for p in ('福岡県',):
        t = t.replace(p, '')
    if city:
        t = t.replace(city, '')
    t = re.sub(r'[0-9０-９].*$', '', t)          # 丁目以降を落とす
    t = re.sub(r'(大字|字)', '', t)
    # 「前津土地区画整理事業区域内」のような役所文言は地名として意味がないので切る
    t = re.split(r'土地区画整理|区域内|地内', t)[0].strip()
    return (t[:8] or None) if t else None        # 小字が延々続く住所があるので8字で止める


def main():
    apply = '--apply' in sys.argv
    sp = json.load(io.open(MAP, encoding='utf-8'))
    cache = json.load(io.open(CACHE, encoding='utf-8'))
    have_tabelog = {s.get('tabelog') for s in sp if s.get('tabelog')}

    add, skip_dup, skip_closed, skip_pref = [], [], [], []
    for url, d in sorted(cache.items(), key=lambda kv: (kv[1]['chain'], kv[1].get('name') or '')):
        if d.get('closed'):
            skip_closed.append(d); continue
        if not d.get('lat') or not d.get('addr'):
            skip_closed.append(d); continue
        if '福岡県' not in d['addr']:
            skip_pref.append(d); continue
        if url in have_tabelog:
            skip_dup.append((d, '同じ食べログURLで登録済み')); continue
        # 重複判定。座標が近いだけでは同一視しない
        #   商業施設や繁華街では120m以内に別テナントがいくらでもあり、
        #   座標だけで弾くと「スシロー伊都店＝資さんうどん伊都店」のような誤爆が出る。
        #   よって「店名が一致」か「座標が近い かつ 同じチェーン名を含む」の時だけ重複とする。
        hit, why = None, ''
        alias = ALIAS.get(d['chain'], [d['chain']])
        for s in sp:
            if norm(s['name']) == norm(d['name']):
                hit, why = s, '店名一致'; break
            near = dist_m(d['lat'], d['lng'], s.get('lat'), s.get('lng')) < 150
            if near and any(a in s['name'] for a in alias):
                hit, why = s, '同チェーンが至近(%dm)' % dist_m(
                    d['lat'], d['lng'], s.get('lat'), s.get('lng')); break
        if hit:
            skip_dup.append((d, '既存「%s」と重複(%s)' % (hit['name'], why))); continue

        cfg = CHAIN_KIDS.get(d['chain'], dict(kids={}, note=''))
        kids = {k: None for k in KIDS_KEYS}
        kids.update({k: v for k, v in cfg['kids'].items() if k in KIDS_KEYS})
        if cfg['kids'].get('kidsMenu') is not None:
            kids['kidsMenu'] = cfg['kids']['kidsMenu']
        name = clean_name(d['name'])
        add.append({
            'id': 'sp' + hashlib.md5(url.encode()).hexdigest()[:10],
            'name': name,
            'area': area_of(d['addr'], d.get('city')),
            'city': d.get('city'),
            'pref': '福岡県',
            'genre': d.get('genre') or d['chain'],
            'lat': d['lat'], 'lng': d['lng'],
            'address': d['addr'],
            'visited': None,
            'with': 'family',
            'kids': kids,
            'verdict': cfg['note'],
            'video': {'youtube': None, 'tiktok': None, 'instagram': None},
            'thumb': None,
            'wish': True,
            'tabelog': url,
        })

    import collections
    print('=== 追加する %d件 ===' % len(add))
    for k, v in collections.Counter(x['genre'] for x in add).most_common():
        print('   %-28s %d件' % (k, v))
    print()
    for k, v in collections.Counter(
            (x['verdict'][:12] or '?') for x in add).most_common():
        pass
    for a in add:
        kk = ','.join(k for k, v in a['kids'].items() if v is True) or '子連れ情報なし'
        print('  + %-30s %-12s %-26s [%s]' % (a['name'][:30], a['city'] or '', (a['area'] or '')[:26], kk))
    print()
    print('=== スキップ: 重複 %d / 閉店・座標なし %d / 県外 %d ===' %
          (len(skip_dup), len(skip_closed), len(skip_pref)))
    for d, why in skip_dup:
        print('  - %-32s %s' % ((d.get('name') or '?')[:32], why))
    for d in skip_closed:
        print('  x %-32s 閉店 or 座標/住所なし' % ((d.get('name') or '?')[:32]))

    if apply:
        sp += add
        io.open(MAP, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print()
        print('書き込んだ。spots.json は %d件になった' % len(sp))
    else:
        print()
        print('※ドライラン。実際に書くには --apply を付ける')
    print('CHAIN_IMPORT_DONE')


if __name__ == '__main__':
    main()
