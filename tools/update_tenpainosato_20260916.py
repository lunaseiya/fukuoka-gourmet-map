# -*- coding: utf-8 -*-
"""筑紫野 天拝の郷 の家族風呂情報を公式ページで裏取りして厚くする【2026-09-16ユーザー依頼】
  「天拝の郷 / 家族風呂に乳幼児用シャンプー・ボディソープ等を用意している
    らしいとのことですが、調べて登録しておいてもらえますか」
出典 = 公式 https://tenpainosato.com/familybath-2 (2026-09-16 閲覧)
  ・「**乳幼児用シャンプー、ボディソープ、保湿ゲル**は各浴室にご用意しております」
  ・お子様用に「**メリットキッズ シャンプー&コンディショナー**」も用意
  ・全6室。浴槽(小)『大城』1室 / (中)『岩屋』『宝満』『三郡』『大根地』4室 / (大)『天拝』1室
  ・各室に**休憩室(和室)とトイレ**付き。タオルは各部屋2枚
  ・60分 平日 3,000/3,400/3,800円(小/中/大)、土日祝は+1,000円、大人6名以上は1名+500円。
    120分・180分コースもあり。受付は 10:30〜24:00(家族風呂の受付は23:00まで)
  ・予約は**1ヶ月前から**電話・Webで
⚠**ピンの色(wish)と visited は触らない**(鉄則)。書き換えるのは verdict / bathAge / web だけ。
⚠旧 verdict に「和室10畳付」と書いていたが、**公式は畳数を書いていない**ので
  「休憩室(和室)+トイレ付」に直す(集約サイトの「約10畳」は断定しない)。
⚠旧 verdict の「料金は要問合せ」は解消できたので実額に差し替える。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
ID = 'chikushinotenhainosato'

VERDICT = (
    "⭐**家族風呂が全6室**。各室に休憩室(和室)とトイレが付き、地下1,500mから湧く天然温泉100%掛け流し。"
    "⭐**乳幼児用のシャンプー・ボディソープ・保湿ゲルが各浴室に常備**されていて、"
    "さらにお子様用に「メリットキッズ シャンプー&コンディショナー」も置いてある。"
    "**赤ちゃん連れで洗面用具を持ち込まなくていい**のがこの施設の一番強いところ。"
    "◆家族風呂の料金(60分): 平日は浴槽(小)『大城』3,000円 / (中)『岩屋』『宝満』『三郡』『大根地』3,400円 / "
    "(大)『天拝』3,800円。**土日祝は+1,000円**、大人6名以上は1名あたり+500円。"
    "120分・180分コースもあり(倍数計算)。タオルは各部屋2枚。"
    "予約は**1ヶ月前から**電話・Webで受付。"
    "◆営業 10:30〜24:00(**家族風呂の受付は23:00まで**)。休は原則第2火曜。大浴場・自然食ブッフェもある。"
    "⚠**連休の繁忙期は家族風呂が追加料金**になる(シルバーウィークは+1,200円だった)。"
    "⚠天拝山の中腹にあるので車が前提。"
)
BATHAGE = ("オムツ未使用児は大浴場の浴槽に入れない(ベビーバスあり)。7歳以上は混浴不可(条例)。"
           "幼児4-6歳490円。**家族風呂なら乳幼児用シャンプー・ボディソープ・保湿ゲルが各室に常備**")

s = json.load(io.open(P, encoding='utf-8'))
hit = [x for x in s if x['id'] == ID]
if not hit:
    raise SystemExit('!! %s が無い' % ID)
x = hit[0]
before = {'wish': x.get('wish'), 'visited': x.get('visited'), 'lat': x.get('lat'), 'lng': x.get('lng')}
print('更新前 verdict:', (x.get('verdict') or '')[:70])

shutil.copy(P, P + '.bak_tenpainosato')
x['verdict'] = VERDICT
x['bathAge'] = BATHAGE
x.setdefault('web', 'https://tenpainosato.com/familybath-2')
x['web'] = 'https://tenpainosato.com/familybath-2'
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

# ── 検算: ピンの色・座標・件数が動いていないこと ─────────────────
s2 = json.load(io.open(P, encoding='utf-8'))
y = [z for z in s2 if z['id'] == ID][0]
after = {'wish': y.get('wish'), 'visited': y.get('visited'), 'lat': y.get('lat'), 'lng': y.get('lng')}
dup = [i for i in {z['id'] for z in s2} if sum(1 for z in s2 if z['id'] == i) > 1]
bad = [z['id'] for z in s2
       if z.get('wish') and any((z.get('video') or {}).get(k) for k in ('youtube', 'tiktok', 'instagram'))]
print('件数 %d / id重複 %d件 / wish=trueなのに動画URLあり %d件' % (len(s2), len(dup), len(bad)))
print('ピン・座標  前 %s' % before)
print('            後 %s  %s' % (after, '変化なし ✓' if before == after else '⚠変わった'))
if before != after or dup or bad:
    raise SystemExit('!! 検算NG')
print('OK  天拝の郷の家族風呂情報を更新した')
