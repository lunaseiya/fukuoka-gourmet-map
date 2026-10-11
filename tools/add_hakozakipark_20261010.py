# -*- coding: utf-8 -*-
"""箱崎公園(福岡市東区原田4-33)を赤ピンで登録(2026-10-10)

- 実訪問(素材 ショート動画用/箱崎公園/ の .mov。撮影 2024-03-31、動画GPS 33.6219,130.4421)
- id は hakozakipark 固定(キャプションの概要欄が s/hakozakipark.html を参照済み)
- 座標: geocoding.jp は住所(原田4-33 / 4丁目33)だと error 001。
  「箱崎公園 福岡市東区」で 33.62154,130.441707(動画GPSと一致)を採用
- 駐車場: 福岡市緑のまちづくり協会の公園ページ
  https://www.midorimachi.jp/park/access.php?code=104003
  「20台 無料 野球場利用者専用 / 70台 無料 一般利用者用」
- トイレ・おむつ替え: 協会ページ(詳細/ご利用案内/交通)に記載なし → kids.diaper は null、verdict は(要確認)
- ベビーカー: いこーよ https://iko-yo.net/facilities/21325 の「ベビーカーOK」
- 写真は動画からフレーム抜き(1本ずつ順番に。並列にしない)。4K HLG なのでトーンマップしてから抜く
- 人の顔: 遠景の豆粒は可。大きめに写る人(娘・他の子・大人)はモザイクか切り出しで外す。
  モザイク座標は 1080 幅に縮めた後の座標(グリッドを焼いた画像で実測)
"""
import json, os, shutil, subprocess, tempfile

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
P = os.path.join(ROOT, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\箱崎公園'
FF = (r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages'
      r'\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe')
VF = ('zscale=t=linear:npl=203,tonemap=hable:desat=0,'
      'zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p,scale=1080:-2')
ID = 'hakozakipark'

# (素材, 秒, 出力名, モザイク box のリスト, 切り出し box or None)。回転は ffmpeg が自動適用 → 1080x1920
THUMB = ('未使用_6519_23s.mov', 1.5, None, [], (0, 560, 1080, 1910))   # 波打つすべり台の全景(4:5)。人は豆粒
GALLERY = [
    # ワイドすべり台(下から見上げ)。上の踊り場の人の頭だけモザイク
    ('未使用_6520_13s.mov', 3, '01_波打つワイドすべり台',
     [(430, 660, 830, 805)], None),
    # ローラーすべり台。すべっている娘・上の子・後ろの列・階段の人をモザイク
    ('未使用_6524_21s.mov', 0.8, '02_ローラーすべり台',
     [(488, 718, 595, 815), (492, 650, 560, 728), (398, 760, 455, 815), (305, 815, 365, 870),
      (560, 810, 910, 885), (960, 690, 1065, 750), (910, 825, 970, 885)], None),
    # 恐竜すべり台。娘は足だけ。右端に写る髪は切り落とす
    ('未使用_6532_24s.mov', 11.5, '03_恐竜のすべり台', [], (0, 0, 1030, 1920)),
    # ロープジム(ピラミッド型)。登っている子の頭をモザイク
    ('未使用_6536_21s.mov', 4.5, '04_ロープジム',
     [(398, 668, 462, 722), (380, 872, 448, 938), (495, 950, 565, 1005), (748, 960, 815, 1015),
      (132, 1000, 197, 1055), (342, 1000, 392, 1050)], None),
    # 砂場とベンチ。奥の遊具まわりの人と右端の子が入らない位置で切り出す
    ('未使用_6526_3s.mov', 0.5, '05_砂場とベンチ', [], (0, 620, 1020, 1440)),
]

SPOT = {
    "id": ID,
    "name": "箱崎公園",
    "area": "原田",
    "city": "福岡市東区",
    "pref": "福岡県",
    "address": "福岡県福岡市東区原田4-33",
    "genre": "公園",
    "lat": 33.62154,
    "lng": 130.441707,
    "visited": "2024-03-31",
    "with": "family",
    "kids": {
        "stroller": True,
        "diaper": None,
        "tatami": None,
        "kidsChair": None,
        "serveMin": None,
        "noise": None,
    },
    "verdict": (
        "⭐**名物は波打つワイドすべり台**。横に広く、何人も並んで何回でもすべれる(実訪問)。"
        "⭐**すべり台だらけの公園**: ほかにローラーすべり台・恐竜のすべり台・小さい子用のすべり台、"
        "黄色いらせんすべり台のある複合遊具も。"
        "⭐ロープジム(ピラミッド型)・ブランコ・砂場(そばにベンチ)あり。"
        "⭐常時開園・入園無料。⭐**駐車場は無料**(一般用70台+野球場利用者専用20台・福岡市緑のまちづくり協会)。"
        "野球場あり。桜の名所。"
        "⚠トイレ・おむつ替えは公式ページに記載なし(要確認)。"
        "⚠撮影は2024年3月。遊具は変わっている場合があります。"
    ),
    "video": {"youtube": None, "tiktok": None, "instagram": None},
    "thumb": ID + '.jpg',
    "photos": [f'{ID}_{g[2]}.jpg' for g in GALLERY],
    "wish": False,
    "category": "play",
    "web": "https://www.midorimachi.jp/park/access.php?code=104003",
    "ages": ["baby", "toddler", "kids"],   # 小さい子用すべり台〜大型遊具(実訪問)
    "ages_src": "manual",
}


def mosaic(im, box, block=16):
    reg = im.crop(box)
    w, h = reg.size
    small = reg.resize((max(1, w // block), max(1, h // block)), Image.BILINEAR)
    im.paste(small.resize((w, h), Image.NEAREST), box[:2])


def grab(mov, sec, out, mosaics, box, size=None):
    # 一時ファイルは Dropbox 外に置く(Dropbox が掴んで削除できないことがある)
    tmp = os.path.join(tempfile.gettempdir(), 'hakozakipark_grab.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(sec), '-i', os.path.join(SRC, mov),
                    '-frames:v', '1', '-vf', VF, '-q:v', '2', tmp], check=True)   # 1本ずつ同期実行
    with Image.open(tmp) as im0:
        im = im0.convert('RGB')
    for m in mosaics:
        mosaic(im, m)
    if box:
        im = im.crop(box)
    if size:
        im = im.resize(size, Image.LANCZOS)
    elif im.width != 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    im.save(out, quality=88)
    os.remove(tmp)


def main():
    grab(THUMB[0], THUMB[1], os.path.join(ROOT, 'map', 'thumbs', SPOT['thumb']), THUMB[3], THUMB[4], (240, 300))
    for mov, sec, name, mos, box in GALLERY:
        grab(mov, sec, os.path.join(ROOT, 'map', 'photos', f'{ID}_{name}.jpg'), mos, box)

    bak = P + '.bak_hakozakipark_20261010'
    if not os.path.exists(bak):          # 再実行しても登録前のバックアップを潰さない
        shutil.copy(P, bak)
    with open(P, encoding='utf-8') as f:
        data = json.load(f)
    if any((s.get('name') or '') == '箱崎公園' and s.get('id') != ID for s in data):
        raise SystemExit('same-name spot exists')
    old = next((s for s in data if s.get('id') == ID), None)
    if old:
        if old.get('added'):
            SPOT['added'] = old['added']
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
