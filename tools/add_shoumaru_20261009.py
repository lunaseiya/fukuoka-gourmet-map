# -*- coding: utf-8 -*-
"""博多ラーメン 将丸(LA-麺HOUSE 将丸)を赤ピンで登録(2026-10-09)

- 実訪問(素材 ショート動画用/居酒屋 将丸/ の .mov。撮影 2023-04-05、動画GPS 33.5930,130.3945)
- 住所・電話・営業時間: 食べログ https://tabelog.com/fukuoka/A4001/A400103/40022324/ (営業中表示)
- 座標: geocoding.jp「福岡県福岡市中央区舞鶴1-8-2」→ 33.593048,130.394578(動画GPSと一致)
- 同行者は素材から判別できないので with/kids は null(推測で埋めない)
- 2023年素材なので価格は書かない。メニュー写真も価格の行が入らない上側だけを切り出す
- 写真は動画からフレーム抜き(1本ずつ順番に。並列にしない)。人の写るカット(1922/1928)は使わない
  ※1926 は依頼メモの秒数(4/18/37)と実際の絵がずれていたので、目視で 6s=黒ラーメン/24s=チャーシュー/34s=麺 に決めた
"""
import json, os, shutil, subprocess, tempfile

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\居酒屋 将丸'
FF = (r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages'
      r'\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe')
ID = 'hakataramen-shoumaru'

# (素材, 秒, 出力名, 切り出し box or None)。ffmpeg は回転メタデータを自動適用 → 1080x1920
THUMB = ('未使用_1915_123s.mov', 110, None, (0, 160, 1080, 1510))   # 看板「将丸」+赤提灯+暖簾(4:5)
GALLERY = [
    ('未使用_1926_50s.mov', 6, '01_黒ラーメン', None),
    ('未使用_1926_50s.mov', 24, '02_チャーシュー', None),
    ('未使用_1926_50s.mov', 34, '03_麺リフト', None),
    ('未使用_1925_50s.mov', 2, '04_焼き餃子', None),
    ('未使用_1917_9s.mov', 4, '05_メニュー', (0, 60, 1080, 1290)),     # 価格行(750円〜)の手前で切る
]

SPOT = {
    "id": ID,
    "name": "博多ラーメン 将丸",
    "area": "舞鶴",
    "city": "福岡市中央区",
    "pref": "福岡県",
    "address": "福岡県福岡市中央区舞鶴1-8-2",
    "genre": "ラーメン",
    "lat": 33.593048,
    "lng": 130.394578,
    "visited": "2023-04-05",
    "with": None,
    "kids": None,
    "verdict": (
        "親不孝通りの裏路地、赤提灯と赤い暖簾が目印の博多ラーメン店(LA-麺HOUSE 将丸)。"
        "ラーメンは白(純豚骨)・黒(焦がしにんにくマー油)・赤(辛味噌)・和(鰹出汁+豚骨)の4系統。"
        " ⭐**黒(マー油)**: 香ばしいマー油の豚骨に、炙った分厚いチャーシュー。替玉あり・卓上にごま。店内に漫画あり。"
        " ⚠**深夜営業のラーメン店**: 夜がメインで子連れ向きではない。"
        " ⚠**営業**: 月水木 11:30〜14:00/18:30〜翌3:00、火 11:30〜14:00/19:00〜翌3:00、"
        "金 11:30〜14:00/18:30〜翌5:00、土 18:30〜翌5:00、日祝 18:30〜翌3:00・不定休(食べログ。要確認)。"
        " TEL 092-714-3939。(2023-04 実訪問)"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": ID + '.jpg',
    "photos": [f'{ID}_{g[2]}.jpg' for g in GALLERY],
    "wish": False,
    "category": "gourmet",
    "tabelog": "https://tabelog.com/fukuoka/A4001/A400103/40022324/",
    "added": "2026-10-09",
}


def grab(mov, sec, out, box, size=None):
    # 一時ファイルは Dropbox 外に置く(Dropbox が掴んで削除できないことがある)
    tmp = os.path.join(tempfile.gettempdir(), 'shoumaru_grab.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(sec), '-i', os.path.join(SRC, mov),
                    '-frames:v', '1', '-q:v', '2', tmp], check=True)   # 1本ずつ同期実行
    with Image.open(tmp) as im0:
        im = im0.convert('RGB')
    if box:
        im = im.crop(box)
    if size:
        im = im.resize(size, Image.LANCZOS)
    elif im.width != 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    im.save(out, quality=88)
    os.remove(tmp)


def main():
    grab(THUMB[0], THUMB[1], os.path.join(ROOT, 'map', 'thumbs', SPOT['thumb']), THUMB[3], (240, 300))
    for mov, sec, name, box in GALLERY:
        grab(mov, sec, os.path.join(ROOT, 'map', 'photos', f'{ID}_{name}.jpg'), box)

    bak = P + '.bak_shoumaru_20261009'
    if not os.path.exists(bak):          # 再実行しても登録前のバックアップを潰さない
        shutil.copy(P, bak)
    with open(P, encoding='utf-8') as f:
        data = json.load(f)
    if any('将丸' in (s.get('name') or '') and s.get('id') != ID for s in data):
        raise SystemExit('same-name spot exists')
    old = next((s for s in data if s.get('id') == ID), None)
    if old:
        data[data.index(old)] = SPOT
    else:
        data.append(SPOT)
    with open(P, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    ids = [s['id'] for s in data]
    dup = {i for i in ids if ids.count(i) > 1}
    bad = [s['id'] for s in data if s.get('wish') is True and any((s.get('video') or {}).values())]
    print('total', len(data), 'dup', dup or 0, 'wish+video', bad or 0)


if __name__ == '__main__':
    main()
