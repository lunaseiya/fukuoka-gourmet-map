# -*- coding: utf-8 -*-
"""対象年齢(ages)の自動付与【第1段階: 遊び場・宿/温泉のみ。2026-10-01】
   区分: baby=乳幼児(0〜2歳) / toddler=幼児(3〜6歳) / kids=小人(小学生)
   ・**根拠がある区分だけ**付ける(説明文・設備に明記されたもの)。推測で埋めない
   ・手で付けた ages は上書きしない(ages_src=='manual')
   python tools/assign_ages.py          … ドライラン(件数と例)
   python tools/assign_ages.py --apply  … 書き込み
"""
import io, json, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
APPLY = '--apply' in sys.argv

# 実際に行って確かめたもの(手で付ける)
MANUAL = {
 'kidsland-978': ['baby', 'toddler', 'kids'],          # USキッズMAX久山: 0〜3歳ベビーコーナー+乳幼児ゾーン+恐竜ライド等
 'stayc3f0c48796': ['baby', 'toddler', 'kids'],        # 旅館初音荘: ベビーバス・離乳食・キッズルーム・駄菓子/ガチャ
 'merittakidstakeo': ['baby', 'toddler', 'kids'],      # メリッタKid's TAKEO: 「乳幼児から小学生まで」(9/29投稿)
}

RANGE_ALL = re.compile(r'([0０]|[1１])歳(から|〜|~|～|ー|-)?(小学生|小学|12歳)')
P_BABY = re.compile(r'乳幼児|赤ちゃん|ベビー(コーナー|エリア|ルーム|バス|カー貸|カー貸出|休憩|ゾーン)|0歳|０歳|1歳|１歳|2歳|２歳|ハイハイ|おむつ替え|授乳')
P_TOD = re.compile(r'幼児|未就学|[3-6３-６]歳|幼稚園|保育園|ふわふわ|ボールプール|メリーゴーランド|砂場|キッズルーム')
P_KIDS = re.compile(r'小学生|小学|児童|アスレチック|ボルダリング|ジップライン|トランポリン|工作|自由研究|小人')


# ジャンルによる既定値(ドライランで「おむつ替えがある=乳幼児だけ」と読めてしまい、
#   ハウステンボスに👶しか付かない等の誤解を生んだため追加)
#   ・家族向けの一般施設 → 幼児以上は普通に楽しめる(toddler+kids)。乳幼児は根拠がある時だけ
#   ・子供専用の屋内遊び場(キッズパーク) → 0歳〜小学生が対象の業態なので3区分すべて
G_FAMILY = re.compile(r'テーマパーク|遊園地|動物園|水族館|博物館|科学館|美術館|資料館|ミュージアム|記念館|公園|牧場|'
                      r'道の駅|展望|プール|レジャー|体験|観光|植物園|自然|キャンプ')
G_KIDSPARK = re.compile(r'室内遊び場|キッズパーク|屋内遊び場|プレイランド|あそび場|遊び場|キッズランド|ネバーランド|'
                        r'ザキッズ|メリッタ|ルクルパーク|モーリーファンタジー|ちきゅうパーク|あそぼっちゃ')


def judge(s):
    txt = ' '.join(str(s.get(k) or '') for k in ('name', 'genre', 'verdict', 'bathAge'))
    k = s.get('kids') or {}
    out = set()
    gn = (s.get('genre') or '') + ' ' + (s.get('name') or '')
    if G_KIDSPARK.search(gn):
        out |= {'baby', 'toddler', 'kids'}
    elif G_FAMILY.search(gn):
        out |= {'toddler', 'kids'}
    if RANGE_ALL.search(txt):
        out |= {'baby', 'toddler', 'kids'}
    if P_BABY.search(txt) or k.get('diaper') is True:
        out.add('baby')
    if P_TOD.search(txt):
        out.add('toddler')
    if P_KIDS.search(txt):
        out.add('kids')
    return [a for a in ('baby', 'toddler', 'kids') if a in out]


def target(s):
    cats = s.get('cats') or [s.get('category')]
    return any(c in ('play', 'onsen') for c in cats)


spots = json.load(io.open(P, encoding='utf-8'))
n_new = n_manual = 0
dist = {}
ex = []
for s in spots:
    if s['id'] in MANUAL:
        if APPLY: s['ages'] = MANUAL[s['id']]; s['ages_src'] = 'manual'
        n_manual += 1; continue
    if s.get('ages_src') == 'manual' or not target(s):
        continue
    a = judge(s)
    if not a:
        continue
    key = '+'.join(a); dist[key] = dist.get(key, 0) + 1
    if len(ex) < 25: ex.append((s['name'], key))
    if APPLY: s['ages'] = a; s['ages_src'] = 'auto'
    n_new += 1
tot = sum(1 for s in spots if target(s))
print('対象(遊び場・宿/温泉) %d件 → 自動付与 %d件 / 手動 %d件' % (tot, n_new, n_manual))
for k, v in sorted(dist.items(), key=lambda x: -x[1]): print('  %-20s %d' % (k, v))
for nm, k in ex: print('   例:', nm, '→', k)
if APPLY:
    shutil.copy(P, P + '.bak_ages')
    io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
    print('書き込み完了')
