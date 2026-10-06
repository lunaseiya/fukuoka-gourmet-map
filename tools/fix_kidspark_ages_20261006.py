# -*- coding: utf-8 -*-
"""KIDS PARK(イオンモール福岡)の対象年齢を訂正(2026-10-06ユーザー指摘)
   0〜2歳のマットエリア(看板「対象年齢0〜2歳」)と、すべり台のある3〜6歳エリア(くつばこ「〜6さいまでのあそびば」)に分かれている"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_kidspark_ages')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}

k = by['kidspark-aeonmallfukuoka']
k['verdict'] = ('⭐0〜6歳の無料キッズスペース。**0〜2歳のマットエリア**(看板「対象年齢0〜2歳」・利用は9組まで)と、'
                '**すべり台のある3〜6歳のエリア**に分かれている(実写)。靴を脱いで遊ぶ。飲食・遊具の持ち込み不可。'
                '保護者の付き添いが必要。(2026-10-02実訪問)')
k['ages'] = ['baby', 'toddler']

p = by['aeonmallfukuoka']
old = '屋内に0〜2歳の「KIDS PARK」(無料)'
assert old in p['verdict']
p['verdict'] = p['verdict'].replace(old, '屋内に0〜2歳/3〜6歳のエリアに分かれた「KIDS PARK」(無料)')

io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('更新: kidspark-aeonmallfukuoka / aeonmallfukuoka')
