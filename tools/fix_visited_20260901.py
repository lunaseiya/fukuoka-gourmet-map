# -*- coding: utf-8 -*-
"""visited(訪問日)の不整合を直す + 同種の不整合を監査する。

visited は**素材の撮影日**を使う(推測しない)というのが既存ルール。
2026-09-01 に8月ラーメンランキングの対象を洗い出す過程で、次の4件のズレが見つかった:
  ・山岡家 月隈店   visited が null(posted だけ入っていた)  → 撮影 2026-08-07
  ・資さんうどん和白 visited が null かつ wish も false(宙に浮いた状態) → 撮影 2026-08-06
  ・宇宙軒         visited が **投稿日** 2026-08-15 で埋まっていた → 撮影 2026-08-09
  ・とり恵びす      visited が 2026-08-19(1日ずれ)              → 撮影 2026-08-18

同じ壊れ方(visited==posted / wishでもvisitedでもない)が他にないかも数える。
"""
import json, io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

FIX = {
    'ramenyamaokayatsukiguma': ('2026-08-07', '素材12本すべて 2026-08-07 撮影'),
    'shisanudonwajiromise':    ('2026-08-06', '素材の最新訪問が 2026-08-06(GPS 33.6910/130.4323 = 和白店から8m)'),
}
# id が分からないものは名前で引く
FIX_BY_NAME = {
    '宇宙軒':     ('2026-08-09', '素材16本すべて 2026-08-09 撮影。旧値 2026-08-15 は投稿日'),
    'とり恵びす': ('2026-08-18', '素材13本すべて 2026-08-18 撮影。旧値は1日ずれ'),
}


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    changed = []
    for s in sp:
        tgt = None
        if s.get('id') in FIX:
            tgt = FIX[s['id']]
        else:
            for nm, v in FIX_BY_NAME.items():
                if nm in s.get('name', ''):
                    tgt = v
                    break
        if tgt and s.get('visited') != tgt[0]:
            changed.append((s['name'], s.get('visited'), tgt[0], tgt[1]))
            s['visited'] = tgt[0]
            s['wish'] = False          # 訪問済みなので青ピンではない

    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))

    print('=== 直した %d件 ===' % len(changed))
    for n, o, v, why in changed:
        print('  %-30s %s → %s' % (n[:30], o, v))
        print('     理由: %s' % why)

    # ── 監査 ────────────────────────────────────────────
    print()
    same = [s for s in sp if s.get('visited') and s.get('posted') and s['visited'] == s['posted']]
    print('■ visited と posted が同じ日 = 投稿日で埋めた疑い: %d件' % len(same))
    for s in same[:15]:
        print('   %s  %s' % (s['visited'], s['name'][:34]))

    floating = [s for s in sp if not s.get('visited') and s.get('wish') is False]
    print()
    print('■ visited が無いのに wish=false(赤でも青でもない): %d件' % len(floating))
    for s in floating[:15]:
        v = s.get('video') or {}
        print('   %-34s posted=%s video=%s' % (s['name'][:34], s.get('posted'), bool(any(v.values()))))

    red = [s for s in sp if s.get('visited')]
    blue = [s for s in sp if s.get('wish')]
    print()
    print('■ 集計: 赤ピン(visitedあり) %d件 / 青ピン(wish) %d件 / 全 %d件'
          % (len(red), len(blue), len(sp)))


if __name__ == '__main__':
    main()
