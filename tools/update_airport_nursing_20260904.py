# -*- coding: utf-8 -*-
"""福岡空港 国内線旅客ターミナルに、授乳室・おむつ交換台の実写を追加する(2026-09-04)。

diaper は既に true だったが、「どこにあるか」の裏付けが無かった。
授乳ブース(個室2つ)・おむつ交換台・「男女トイレにもオムツ替え設備がございます」の
掲示を実写で確認できたので、写真とverdictに反映する。
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

ADD = ('⭐**授乳ブース**(個室2つ・給湯器とシンク付き)と**おむつ交換台**を実写で確認(2026-09-03)。'
       '男女どちらのトイレにもおむつ交換台があり、館内のトイレ案内図にも明記されている。')
PHOTOS = ['fukuokaairport_07_授乳ブース.jpg', 'fukuokaairport_08_おむつ交換台.jpg',
          'fukuokaairport_09_おむつ替え設備案内.jpg']


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    x = next(s for s in sp if s['id'] == 'fukuokaairportdomestic')
    if '授乳ブース' not in (x.get('verdict') or ''):
        x['verdict'] = (x.get('verdict') or '') + ' ' + ADD
    ph = x.get('photos') or []
    for p in PHOTOS:
        if p not in ph:
            ph.append(p)
    x['photos'] = ph
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('更新:', x['name'], '/ 写真', len(x['photos']), '枚')


if __name__ == '__main__':
    main()
