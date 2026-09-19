# -*- coding: utf-8 -*-
"""シルバーウィーク20選を**マップへ期間限定登録**するための住所補完【2026-09-19】

`event_to_map.py` は住所か「会場の既存登録」が無いイベントを見送る(座標を推測しないため)。
今回20件のうち**10件が住所なし**で落ちた(いこーよは一覧に住所を出さない・久留米市の源は
「城島・みづまエリア」のような広域名しか持たない)。掲載したのにマップに無い状態になるので、
**源のイベントページを1件ずつ開いて住所を転記**した。

⚠住所は**推測で書かない**。ここの値はすべて次の一次情報から取っている:
  ・いこーよの各イベントページの「開催場所の住所」
  ・welcome-kurume の各イベントページの会場・住所
  ・イオン九州の店舗ページ(イオン小郡)
  ・`_イベント補足.json` の place(ポスターから転記済みの分)
⚠`城島町楢津` は**番地の無い大字まで**しか公開されていない。地図上の位置は
  町名の代表点になるので、verdict に「会場は城島町民の森公園」と書いて補う。
"""
import io, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SRC = os.path.join(ROOT, 'data', '_sw_caption_src.json')

# _short → (住所, 会場名)
ADDR = {
 'OHORI':          ('福岡県福岡市中央区大濠公園1-2', '大濠公園'),
 '透視':            ('福岡県福岡市中央区今泉1-19-22', 'あすみん(西鉄天神クラス4F)'),
 'お箸づくり':        ('福岡県糟屋郡篠栗町彩り台1-1', '篠栗町'),
 '北九州 ０歳からの':  ('福岡県北九州市八幡西区黒崎三丁目15番3号', '黒崎 COMCITY 7階'),
 '西日本陶磁器フェスタ': ('福岡県北九州市小倉北区浅野3-8-1', '西日本総合展示場'),
 'ピザ作り':         ('福岡県北九州市小倉南区津田1丁目4-7', 'TNC住宅展示場きてミテ！小倉'),
 '城島ふるさと夢まつり': ('福岡県久留米市城島町楢津', '城島町民の森公園'),
 '子どもフェス':       ('福岡県久留米市六ツ門町8-1', '久留米シティプラザ'),
 '九州サーカス団':     ('福岡県小郡市大保字弓場110', 'イオン小郡ショッピングセンター'),
}


def main():
    D = json.load(io.open(SRC, encoding='utf-8'))
    n = 0
    for e in D['events']:
        a = ADDR.get(e.get('_short'))
        if not a or e.get('addr'):
            continue
        e['addr'], e['place'] = a[0], a[1]
        n += 1
    json.dump(D, io.open(SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('住所を補完: %d件' % n)
    subprocess.run([sys.executable, '-X', 'utf8',
                    os.path.join(HERE, 'event_to_map.py'), '--json', SRC]
                   + (['--apply'] if '--apply' in sys.argv else []), check=True)


if __name__ == '__main__':
    main()
