# -*- coding: utf-8 -*-
"""京鼎樓の店名・住所を公式で確定させ、食べログリンクを手で入れる【2026-09-16】

■ 店名
  レシート印字 … 「恵比寿 京鼎樓 JIN DIN ROU 福岡店」
  店頭看板     … 「恵比寿 京鼎樓 JIN DIN ROU」
  公式         … 「京鼎樓 ららぽーと福岡店」(ブランド名は「小籠包レストラン 恵比寿 京鼎樓」)
  食べログ     … 「京鼎樓 ららぽーと福岡店」
  → 両方を満たす **「恵比寿 京鼎樓 ららぽーと福岡店」** にする(検索性も上がる)

■ 住所【⚠訂正】
  当初 verdict/address に**レシートから読んだ「那珂6-351-1 3階」**を入れていたが、
  公式( https://jin-din-rou.net/fukuoka/ )と食べログはどちらも
  **「〒812-8627 福岡県福岡市博多区那珂6-23-1他 3階」**。
  「6-351-1」は那珂の地番の形として不自然で、**レシートの読み取り違い**と判断した。
  → 公式の住所に差し替える。座標は親施設(ららぽーと福岡)と共有しているので変わらない。

■ 食べログ【⚠monetize.py では付けられなかったので手で入れる】
  https://tabelog.com/fukuoka/A4001/A400202/40060477/ (京鼎樓 ららぽーと福岡店・竹下/小籠包)
  monetize.py には同日に見つけたバグを2件直してある(下記)が、
  この店は**食べログ上の店名に「恵比寿」が付かない**ため検索名が一致せず0件になる。
  ⚠自動照合で 群馬県高崎市のラーメン店「恵比寿」のURLが付きかけた。原因は
    ①`core = re.sub(r'\\s.*?店$', ...)` が「恵比寿 京鼎樓 福岡店」→「恵比寿」まで削っていた
    ②住所チェックの正規表現が**九州+山口の県名だけ**で、群馬県では addr=None になり
      市区チェックが `addr and …` で丸ごと飛ばされて素通りした
    ③`nc in n0core` の部分一致だけで strong 判定していた(「恵比寿」⊂「恵比寿京鼎樓福岡」)
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
ID = 'jindinrou'

s = json.load(io.open(P, encoding='utf-8'))
x = [y for y in s if y['id'] == ID]
if not x:
    raise SystemExit('!! %s が無い' % ID)
x = x[0]
before = {'wish': x.get('wish'), 'visited': x.get('visited'), 'lat': x.get('lat'), 'lng': x.get('lng')}

shutil.copy(P, P + '.bak_jindinrou_fix')
x['name'] = '恵比寿 京鼎樓 ららぽーと福岡店'
x['address'] = '福岡県福岡市博多区那珂6-23-1他 3階'
x['postal'] = '812-8627'
x['web'] = 'https://jin-din-rou.net/fukuoka/'
x['tabelog'] = 'https://tabelog.com/fukuoka/A4001/A400202/40060477/'
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))

s2 = json.load(io.open(P, encoding='utf-8'))
y = [z for z in s2 if z['id'] == ID][0]
after = {'wish': y.get('wish'), 'visited': y.get('visited'), 'lat': y.get('lat'), 'lng': y.get('lng')}
ids = [z['id'] for z in s2]
dup = [i for i in set(ids) if ids.count(i) > 1]
print('name    :', y['name'])
print('address :', y['address'], '(〒%s)' % y['postal'])
print('tabelog :', y['tabelog'])
print('件数 %d / id重複 %d件' % (len(s2), len(dup)))
print('ピン・座標  前 %s' % before)
print('            後 %s  %s' % (after, '変化なし ✓' if before == after else '⚠変わった'))
if dup or before != after:
    raise SystemExit('!! 検算NG')
print('OK')
