# -*- coding: utf-8 -*-
"""対象年齢(ages)をマップに足す【2026-10-01ユーザー確定】
   区分: baby=乳幼児(0〜2歳) / toddler=幼児(3〜6歳・未就学) / kids=小人(小学生)
   ・カードにバッジ  ・「年齢」絞り込み(複数選択=**全部に当てはまる所**。例: 乳幼児+小人 = 上の子も下の子も楽しめる)"""
import io, os, sys
sys.stdout.reconfigure(encoding='utf-8')
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'map', 'index.html')
t = io.open(P, encoding='utf-8').read()
R = [
 # CSS
 ("  .filter-btn.active {\n",
  "  /* 対象年齢(2026-10-01) */\n"
  "  .agefilters { margin-top: 6px; }\n"
  "  .age-label { font-size: 12px; color: var(--muted); margin-right: 2px; }\n"
  "  .age-btn { border: 1px solid var(--border); background: #fff; color: var(--text); padding: 6px 12px;\n"
  "             border-radius: 999px; font-size: 12.5px; white-space: nowrap; cursor: pointer; }\n"
  "  .age-btn.active { background: #2f7d5b; border-color: #2f7d5b; color: #fff; }\n"
  "  .b-age { display: inline-block; font-size: 11px; background: #e8f4ee; color: #2f6b50; border-radius: 999px;\n"
  "           padding: 2px 8px; margin: 0 4px 4px 0; }\n"
  "  .filter-btn.active {\n"),
 # HTML
 ("    <button class=\"filter-btn\" id=\"areaBtn\">市区で絞る</button>\n  </div>\n",
  "    <button class=\"filter-btn\" id=\"areaBtn\">市区で絞る</button>\n  </div>\n"
  "  <div class=\"filters agefilters\">\n"
  "    <span class=\"age-label\">年齢</span>\n"
  "    <button class=\"age-btn\" data-age=\"baby\">👶 乳幼児</button>\n"
  "    <button class=\"age-btn\" data-age=\"toddler\">🧒 幼児</button>\n"
  "    <button class=\"age-btn\" data-age=\"kids\">🎒 小人</button>\n"
  "  </div>\n"),
 # state
 ("  areas: new Set(),\n  areasDraft: new Set(),\n",
  "  areas: new Set(),\n  areasDraft: new Set(),\n  ages: new Set(),   // 対象年齢の絞り込み(選んだ区分を**全部**満たす所だけ)\n"),
 # filter
 ("    if (state.areas.size && !state.areas.has(s.city)) return false;\n    return true;\n",
  "    if (state.areas.size && !state.areas.has(s.city)) return false;\n"
  "    if (state.ages.size && ![...state.ages].every(a => (s.ages || []).includes(a))) return false;\n"
  "    return true;\n"),
 # deep-link reset
 ("    state.filter = \"all\";\n    state.areas = new Set();\n    updateAreaBtn();\n",
  "    state.filter = \"all\";\n    state.areas = new Set();\n    state.ages = new Set();\n"
  "    document.querySelectorAll(\".age-btn\").forEach(b => b.classList.remove(\"active\"));\n    updateAreaBtn();\n"),
 # handler
 ("document.querySelectorAll(\".filter-btn\").forEach(btn => {\n  btn.addEventListener(\"click\", () => {\n",
  "// 対象年齢: トグル式・複数選択可\n"
  "document.querySelectorAll(\".age-btn\").forEach(btn => {\n"
  "  btn.addEventListener(\"click\", () => {\n"
  "    const a = btn.dataset.age;\n"
  "    if (state.ages.has(a)) state.ages.delete(a); else state.ages.add(a);\n"
  "    btn.classList.toggle(\"active\", state.ages.has(a));\n"
  "    renderAll();\n"
  "  });\n"
  "});\n\n"
  "document.querySelectorAll(\".filter-btn\").forEach(btn => {\n  btn.addEventListener(\"click\", () => {\n"),
 # card badge (先頭のバッジ列の末尾=子連れOKの直前)
 ("${kidsOk ? `<div class=\"card-kids\">",
  "${ageBadgesHtml(spot)}${kidsOk ? `<div class=\"card-kids\">"),
 # helper
 ("function cardHtml(spot) {",
  "const AGE_LABEL = { baby: \"👶 乳幼児(0〜2歳)\", toddler: \"🧒 幼児(3〜6歳)\", kids: \"🎒 小人(小学生)\" };\n"
  "function ageBadgesHtml(spot) {\n"
  "  if (!Array.isArray(spot.ages) || !spot.ages.length) return \"\";\n"
  "  return `<div>${[\"baby\", \"toddler\", \"kids\"].filter(a => spot.ages.includes(a))\n"
  "    .map(a => `<span class=\"b-age\">${AGE_LABEL[a]}</span>`).join(\"\")}</div>`;\n"
  "}\n\n"
  "function cardHtml(spot) {"),
]
for a, b in R:
    assert t.count(a) == 1, ('件数≠1', t.count(a), a[:50])
    t = t.replace(a, b)
io.open(P, 'w', encoding='utf-8').write(t)
print('patched index.html')
