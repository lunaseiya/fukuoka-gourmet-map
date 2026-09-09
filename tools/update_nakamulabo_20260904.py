# -*- coding: utf-8 -*-
"""ナカムラボ(福岡空港店)を1st STEPで赤ピンに更新する(2026-09-04)。

・visited を撮影日にする
・メニュー価格を正しい3本柱(鶏白湯SOBA/和風醤油SOBA/担々麺)に修正
  (先の verdict 更新で「2本柱」と書いたのは誤り。看板メニューを再確認して訂正)
・写真3枚(着丼/メニュー看板/ラーメン滑走路の通路)を追加
"""
import os, io, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')

VERDICT = (
    '福岡空港 国内線ターミナル3F(保安検査通過前)。ラーメン滑走路「SECTION 16」内にある鶏sobaの店。'
    'ラーメンは**3本柱**: 鶏白湯SOBA ¥950(特製¥1,550)・和風醤油SOBA ¥900(特製¥1,500)・'
    '担々麺 ¥980。替え玉¥150、トッピング焼豚¥450/煮玉子¥180/のり・メンマ各¥150。'
    'サイドは焼豚丼¥500・白飯¥150・餃子¥350。製麺屋慶史の麺を使用。カウンター主体。'
    '座面をかさ上げする補助クッションの用意はあるが、**ベビーチェアと呼べるものではない**(現地確認)。'
)


def main():
    sp = json.load(io.open(P, encoding='utf-8'))
    x = next(s for s in sp if s['id'] == 'ap64f6682535')
    x['visited'] = '2026-09-03'
    x['wish'] = False
    x['verdict'] = VERDICT
    names = ['nakamulabo_01_ラーメン.jpg', 'nakamulabo_02_メニュー.jpg', 'nakamulabo_03_看板.jpg']
    x['photos'] = names
    x['thumb'] = 'nakamulabo.jpg'
    io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
    print('更新:', x['name'], '/ visited=', x['visited'], '/ wish=', x['wish'])


if __name__ == '__main__':
    main()
