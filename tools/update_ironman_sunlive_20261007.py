# -*- coding: utf-8 -*-
"""2026-10-07 マップ更新(1回の書き込みで2件)
1. ironman-koga … 現地素材(アイアンマン古賀店/ の写真4枚+動画19本)からサムネ+写真5枚を追加し、
   素材で新たに分かったこと(ベビー椀・料金・テイクアウト・キャッシュレス券売機)を verdict に追記。
   ※素材フォルダは読むだけ。移動・リネームしない(後で動画にする)
   ※動画は全て bt709(SDR)なので tonemap 不要(ffprobe で確認済み)
   ※店頭の外観カット(12 08 24 の 1.0秒)はガラス扉の奥に店員が写るのでモザイク
2. サンリブ古賀フードコート3店を赤ピン化(wish=False)。kids は既存のまま。
   - firstkitchen: visited 2026-10-07(当日注文)
   - kfc / kogashokudou: 以前利用(時期不明)→ visited None
   ※サンリブは館内撮影禁止なので、当日の写真はマップに載せない
"""
import json, os, shutil, subprocess, sys
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
PHOTOS = os.path.join(ROOT, 'map', 'photos')
THUMBS = os.path.join(ROOT, 'map', 'thumbs')
REVIEW = os.path.join(ROOT, 'thumbs_review', 'ironman-koga')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\アイアンマン古賀店'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
TMP = os.path.join(os.environ.get('TEMP', ROOT), 'ironman_koga_frames')
ID = 'ironman-koga'


def frame(fname, t):
    """動画から1フレーム(フル解像度・自動回転)。写真ならexif_transposeして読む"""
    p = os.path.join(SRC, fname)
    if fname.lower().endswith('.jpg'):
        return ImageOps.exif_transpose(Image.open(p)).convert('RGB')
    os.makedirs(TMP, exist_ok=True)
    o = os.path.join(TMP, f'{abs(hash((fname, t)))}.jpg')
    subprocess.run([FF, '-y', '-v', 'error', '-ss', str(t), '-i', p, '-frames:v', '1', '-q:v', '2', o], check=True)
    return Image.open(o).convert('RGB')


def mosaic(im, box, block=16):
    """box=(x0,y0,x1,y1)。縮小→最近傍拡大でブロックモザイク。座標はグリッド焼き込み画像で実測済み"""
    x0, y0, x1, y1 = box
    reg = im.crop(box)
    small = reg.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)), Image.BILINEAR)
    im.paste(small.resize(reg.size, Image.NEAREST), (x0, y0))
    return im


def to_w1080(im):
    if im.width != 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    return im


def save(im, path):
    im.save(path, quality=88)
    shutil.copy(path, os.path.join(REVIEW, os.path.basename(path)))
    print('wrote', os.path.relpath(path, ROOT), im.size)


def make_images():
    os.makedirs(REVIEW, exist_ok=True)
    # 外観(店名ののれん・提灯・縦看板)。扉ガラス越しの店員(x1340-1470, y1960-2560)をモザイク
    store = frame('動画 2026-10-07 12 08 24.mov', 1.0)          # 2160x3840
    store = mosaic(store, (1330, 1950, 1480, 2570), block=18)
    # サムネ 240x300(4:5)
    th = store.crop((0, 500, 2160, 3200)).resize((240, 300), Image.LANCZOS)
    save(th, os.path.join(THUMBS, f'{ID}.jpg'))
    photos = []
    p = os.path.join(PHOTOS, f'{ID}_01_外観.jpg')
    save(to_w1080(store.crop((0, 300, 2160, 3180))), p); photos.append(os.path.basename(p))
    # スタミナ鉄板(こだわり豚+キャベツ)
    dish = frame('動画 2026-10-07 12 20 33.mov', 11.2)
    p = os.path.join(PHOTOS, f'{ID}_02_スタミナ鉄板(豚肉とキャベツ).jpg')
    save(to_w1080(dish.crop((0, 400, 2160, 3280))), p); photos.append(os.path.basename(p))
    # 店内のボックス席(無人)
    seat = frame('動画 2026-10-07 12 12 31.mov', 2.0)
    p = os.path.join(PHOTOS, f'{ID}_03_店内の板張りボックス席.jpg')
    save(to_w1080(seat.crop((0, 300, 2160, 3180))), p); photos.append(os.path.basename(p))
    # 子供用カトラリー+ベビー椀(「取り皿/ベビー椀 ご自由にお取り下さい」)を左右に並べる
    k1 = frame('動画 2026-10-07 12 12 00.mov', 1.5).crop((0, 0, 2160, 3840))
    k2 = frame('動画 2026-10-07 12 12 00.mov', 8.5).crop((0, 0, 2160, 3840))
    k1 = k1.resize((540, 960), Image.LANCZOS); k2 = k2.resize((540, 960), Image.LANCZOS)
    kid = Image.new('RGB', (1080, 960)); kid.paste(k1, (0, 0)); kid.paste(k2, (540, 0))
    p = os.path.join(PHOTOS, f'{ID}_04_子供用フォーク・スプーンとベビー椀(セルフ).jpg')
    save(kid, p); photos.append(os.path.basename(p))
    # 店頭のメニュー看板(料金は2026-10-07時点の現行価格)
    menu = frame('写真 2026-10-07 12 08 18.jpg', 0)
    p = os.path.join(PHOTOS, f'{ID}_05_店頭のメニュー(2026年10月).jpg')
    save(to_w1080(menu), p); photos.append(os.path.basename(p))
    return photos


IRONMAN_VERDICT = (
    "⚠子連れ向きとは言いにくい。子供椅子・キッズメニューなし、席は板張りのボックス席(座敷・個室なし)。"
    "豚肉とキャベツの鉄板にご飯・味噌汁の定食スタイルなので、小学生くらいで取り分けるならOK。"
    "⭐子供用のフォーク・スプーン・取り皿・ベビー椀あり(セルフで自由に取れる・2026-10-07現地確認)、駐車場あり、店内全面禁煙(屋外に喫煙所)。"
    "スタミナ鉄板 普通盛り1,030円(1.5倍1,430円/2倍1,820円/3倍2,690円・税込、ランチ11:00-15:00はごはん・みそ汁付)・持ち帰り可(電話予約可)(2026-10-07店頭)。"
    "11:00-15:00/17:00-21:00・不定休、食券制(タッチパネル券売機・クレジットカード/電子マネー/QR決済対応)、44席(カウンターあり)。"
    "JR古賀駅から徒歩約9分。TEL 092-692-7529。"
)


def main():
    with open(SPOTS, encoding='utf-8') as f:
        data = json.load(f)
    by = {s['id']: s for s in data}
    for k in (ID, 'sunlivekoga-firstkitchen', 'sunlivekoga-kfc', 'sunlivekoga-kogashokudou'):
        assert k in by, k
    old_iron = by[ID]['verdict']
    assert '子供用のフォーク・スプーン・取り皿あり' in old_iron, 'verdict が想定と違う'

    shutil.copy(SPOTS, SPOTS + '.bak_ironman_sunlive_20261007')

    photos = make_images()
    s = by[ID]
    s['thumb'] = f'{ID}.jpg'
    s['photos'] = photos
    s['verdict'] = IRONMAN_VERDICT

    fk = by['sunlivekoga-firstkitchen']
    fk['wish'] = False
    fk['visited'] = '2026-10-07'
    fk['verdict'] = fk['verdict'].rstrip() + '2026-10-07にタピオカドリンク(巨峰)とフレーバーポテト(焦がしバター醤油)を注文。'

    for k, old in (('sunlivekoga-kfc', '⚠未訪問。'), ('sunlivekoga-kogashokudou', '⚠未訪問(食事はまだ)。')):
        sp = by[k]
        assert old in sp['verdict'], k
        sp['verdict'] = sp['verdict'].replace(old, '以前利用(時期不明)。')
        sp['wish'] = False
        sp['visited'] = None

    # 整合チェック
    ids = [x['id'] for x in data]
    assert len(ids) == len(set(ids)), 'id重複'
    bad = [x['id'] for x in data if x.get('wish') is True and any((x.get('video') or {}).values())]
    assert not bad, bad

    with open(SPOTS, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('spots.json updated')


if __name__ == '__main__':
    main()
