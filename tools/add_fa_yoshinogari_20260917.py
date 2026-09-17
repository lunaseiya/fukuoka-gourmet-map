# -*- coding: utf-8 -*-
"""フォレストアドベンチャー・吉野ヶ里 を青ピンで登録する【2026-09-17】

ユーザーが Instagram の紹介投稿を見て「青ピン登録願います」。
既に美里(熊本)・添田(福岡)が入っているのでフォレストアドベンチャーは3つ目。
命名と項目の並びは `forest-adventure-soeda` に合わせた。

■ 裏取りは**公式サイト**(https://foret-aventure.jp/park/fa-yoshinogari/ 2026-09-17実測)
  ・住所 〒842-0104 佐賀県神埼郡吉野ヶ里町三津2753 アドベンチャーバレーSAGA内
  ・9:00〜17:00(最終受付15:00)※季節・天候により変動あり / 定休日は記載なし
  ・コースと料金(**6コース**):
      キッズコース          ¥1,900  身長90cm以上・小学3年生まで
      ネットコース          ¥2,200  身長90cm以上(60分間)
      ジップトリップコース  ¥2,700  小学4年生以上または身長140cm以上
      キャノピーコース      ¥3,200  身長110cm以上
      アドベンチャー(標準)  ¥4,200  小学4年生以上または身長140cm以上
      アドベンチャー(エキサイト) ¥6,000  同上
  ・無料駐車場 / 更衣室 / コインロッカー / 休憩所 / 喫煙所 / ペットOK
  ・公式サイトからの前日までの予約を推奨
  ⚠**Web検索の要約に出てきた「アドベンチャーコース¥3,800」は古い**。
    公式の現行価格は¥4,200。ユーザーが見せてくれた Instagram の料金と一致した。
    (スキルの優先順位どおり**公式 > まとめサイト**で採った)

■ 座標
  geocoding.jp に住所で投げて 33.366494 / 130.390076。
  「三津2753」「三津2753番地」の2表記で同じ値が返ったので採用。

■ ピンの色
  **青(wish=True / visited=None)**。まだ行っていない。
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')
spots = json.load(io.open(P, encoding='utf-8'))
by_id = {x['id']: x for x in spots}

NEW = {
    'id': 'forest-adventure-yoshinogari',
    'name': 'フォレストアドベンチャー・吉野ヶ里',
    'area': 'アドベンチャーバレーSAGA内',
    'city': '神埼郡吉野ヶ里町',
    'pref': '佐賀県',
    'genre': 'アスレチック・ジップライン',
    'address': '佐賀県神埼郡吉野ヶ里町三津2753 アドベンチャーバレーSAGA内',
    'postal': '842-0104',
    'lat': 33.366494,
    'lng': 130.390076,
    'visited': None,
    'with': 'family',
    'kids': {
        'stroller': None,      # 森の中の樹上コース。ベビーカーの可否は未確認
        'diaper': None,
        'tatami': None,
        'kidsChair': None,
        'serveMin': None,
        'noise': 'ok',         # 屋外のアウトドアパーク
    },
    'verdict': ('⭐**身長90cmから遊べる**ので小さい子でも入れる('
                'フォレストアドベンチャーの中でも**キッズコースは九州で唯一**)。'
                'コースは6つで年齢・身長で分かれる: '
                '**キッズ1,900円**(身長90cm以上〜小学3年生) / '
                '**ネットコース2,200円**(身長90cm以上・60分間のネットの空中遊び場) / '
                '**ジップトリップ2,700円**(小4以上か140cm以上・3本のジップスライドで最長約270m) / '
                '**キャノピー3,200円**(身長110cm以上) / '
                '**アドベンチャー4,200円**(小4以上か140cm以上)・エキサイト6,000円。'
                '⭐**無料駐車場**・更衣室・コインロッカー・休憩所あり。ペットOK。'
                '⚠**最終受付15:00**(営業9:00〜17:00・季節と天候で変動)。'
                '⚠**公式サイトから前日までの予約が推奨**。'
                '命綱をつけて渡る・登る・飛ぶ樹上アスレチックで、'
                '最後はジップラインで森を滑り降りる。(2026-09-17時点の公式情報)'),
    'video': {'youtube': None, 'tiktok': None, 'instagram': None},
    'thumb': None,
    'wish': True,
    'category': 'play',
    'web': 'https://foret-aventure.jp/park/fa-yoshinogari/',
}

if NEW['id'] in by_id:
    raise SystemExit('!! 既に登録済み: ' + NEW['id'])
same = [x for x in spots if x['name'] == NEW['name']]
if same:
    raise SystemExit('!! 同名が居る: ' + same[0]['id'])

shutil.copy(P, P + '.bak_fayoshinogari')
spots.append(NEW)
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

back = json.load(io.open(P, encoding='utf-8'))
ids = [x['id'] for x in back]
names = [x['name'] for x in back]
print('登録: %s (%s)' % (NEW['name'], NEW['id']))
print('  %s / %s %s' % (NEW['address'], NEW['lat'], NEW['lng']))
print('  スポット数 %d → %d' % (len(spots) - 1, len(back)))
print('  id重複 %s / 同名重複 %s'
      % ([i for i in set(ids) if ids.count(i) > 1] or 'なし ✓',
         [n for n in set(names) if names.count(n) > 1] or 'なし ✓'))
bad = [x['id'] for x in back if x.get('wish') and any((x.get('video') or {}).values())]
print('  青ピンに動画URLがある矛盾: %s' % (bad or 'なし ✓'))
print('  フォレストアドベンチャー: %s'
      % [x['name'] for x in back if 'フォレストアドベンチャー' in x['name']])
