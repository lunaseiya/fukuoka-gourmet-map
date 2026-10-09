# -*- coding: utf-8 -*-
"""THE OUTLETS KITAKYUSHU 実訪問(2026-10-08)の反映。

素材: ショート動画用/ジアウトレット/(写真70枚 + 動画40本・全て bt709 SDR なので tonemap 不要)
      ※素材フォルダは読むだけ。移動・リネームしない(動画にも使う)
撮影ルール: アウトレット本体=記載なし(✅) / スペースLABO=個人撮影OK /
            KGG(KITAKYUSHU GLOBAL GATEWAY)=商業目的の撮影禁止 → KGGの写真は使わない(素材にも写っていない)

1. theoutletskitakyushu … visited=2026-10-08。サムネ+写真8枚、kids、verdict を現地情報で充実
2. masumoto-theoutletskitakyushu(新規・赤)… 元祖辛麺屋 桝元。動画 12 25 34 / 12 26 26 の丼に「桝元」ロゴ=ここで食事
3. curryhonpo-theoutletskitakyushu(新規・赤)… 伽喱本舗。12:29 の動画で焼きカレー(ご飯+カレー+チーズ+卵を
   焼いたもの)を食べている。FOOD FOREST で焼きカレーを出すのは伽喱本舗だけ(フロアマップ 1001〜1013 で確認)、
   12 02 49 に店頭を撮影、12 29 28 の写真は「福神漬け」のあるセルフコーナー → 伽喱本舗と判断
4. asoble-theoutletskitakyushu(新規・赤)… 屋内アミューズメント ASOBLE(入場無料)。遊具・ドームで遊んだ動画あり
5. in 紐付け: 極味や(sp3c07c7fde2・フロアマップ 1011 で営業確認)/スペースLABO(G-SITE 2601)/
   KGGハロウィン(ev-602195-kgg・G-SITE 2103 の KGG で開催)→ theoutletskitakyushu
座標: FOOD FOREST の2店は既存の極味や(同じフードコート)と同じ点、ASOBLE は親施設の代表点を共有(近似)。
人の映り込み: 人が枠に入らない位置で切り出す。桝元・伽喱本舗の店頭は店員の顔にモザイク(座標はグリッド焼き込みで実測)。
"""
import json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
PHOTOS = os.path.join(ROOT, 'map', 'photos')
THUMBS = os.path.join(ROOT, 'map', 'thumbs')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\ジアウトレット'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
TMP = os.path.join(os.environ.get('TEMP', ROOT), 'outlets_kk_frames')
V = '2026-10-08'
PID = 'theoutletskitakyushu'
MID = 'masumoto-theoutletskitakyushu'
CID = 'curryhonpo-theoutletskitakyushu'
AID = 'asoble-theoutletskitakyushu'


def photo(ts):
    return ImageOps.exif_transpose(Image.open(os.path.join(SRC, f'写真 2026-10-08 {ts}.jpg'))).convert('RGB')


def frame(ts, t):
    """動画から1フレーム(フル解像度 2160x3840)。ffmpeg は1本ずつ順番に"""
    os.makedirs(TMP, exist_ok=True)
    o = os.path.join(TMP, ts.replace(' ', '') + f'_{t}.jpg')
    subprocess.run([FF, '-v', 'error', '-y', '-ss', str(t), '-i', os.path.join(SRC, f'動画 2026-10-08 {ts}.mov'),
                    '-frames:v', '1', '-q:v', '2', o], check=True)
    im = Image.open(o).convert('RGB'); im.load()
    return im


def rc(im, x0, y0, x1, y1):
    """比率で切り出し"""
    w, h = im.size
    return im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))


def mosaic(im, box, block=16):
    x0, y0, x1, y1 = box
    reg = im.crop(box)
    small = reg.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)), Image.BILINEAR)
    im.paste(small.resize(reg.size, Image.NEAREST), (x0, y0))
    return im


def w1080(im):
    if im.width != 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    return im


def put(sid, items):
    """items = [(内容, PIL.Image)] → map/photos/<id>_NN_内容.jpg と thumbs_review/<id>/ に保存"""
    rev = os.path.join(ROOT, 'thumbs_review', sid)
    os.makedirs(rev, exist_ok=True)
    names = []
    for k, (lab, im) in enumerate(items, 1):
        nm = f'{sid}_{k:02d}_{lab}.jpg'
        im = w1080(im)
        im.save(os.path.join(PHOTOS, nm), quality=86)
        shutil.copy(os.path.join(PHOTOS, nm), os.path.join(rev, nm))
        names.append(nm); print('photo', nm, im.size)
    return names


def thumb(sid, im):
    t = ImageOps.fit(im, (240, 300), Image.LANCZOS)
    t.save(os.path.join(THUMBS, sid + '.jpg'), quality=88)
    rev = os.path.join(ROOT, 'thumbs_review', sid)
    os.makedirs(rev, exist_ok=True)
    t.save(os.path.join(rev, 'thumb.jpg'), quality=88)
    print('thumb', sid)


def make_images():
    out = {}
    # ---- 親: アウトレット ----
    ext = frame('11 57 17', 1.6)          # ガラス面の「THE OUTLETS」。人(x≈700,y≈2350〜)は切り落とす
    thumb(PID, ext.crop((100, 300, 1700, 2300)))
    out[PID] = put(PID, [
        ('外観', ext.crop((0, 200, 2160, 2300))),
        ('ベビールームの入口', photo('12 05 11')),
        ('授乳ブースとおむつ替え台', photo('12 05 27')),
        ('調乳用温水器と離乳食用の電子レンジ', rc(photo('12 05 22'), 0, 0.15, 1, 0.85)),
        ('トイレの設備案内(オムツ替え台・ベビーカー同伴ブース・ベビーチェア)', rc(photo('12 05 46'), 0.25, 0.2, 0.95, 0.65)),
        ('フードコートのベルト付き子供椅子', photo('12 01 44')),
        ('授乳ポッドmamaro', photo('13 13 03')),
        ('屋外の3〜6歳向け丸太の遊び場', frame('13 27 15', 2).crop((0, 800, 2160, 3840))),
    ])
    # ---- 元祖辛麺屋 桝元 ----
    m = photo('12 03 41')                 # 3024x4032
    mosaic(m, (1600, 2200, 1850, 2420))   # 厨房の店員
    thumb(MID, rc(m, 0.3, 0.05, 1.0, 0.6))
    out[MID] = put(MID, [
        ('店頭', rc(m, 0.08, 0.05, 1.0, 0.6)),
        ('ジュニアラーメンの案内(小学生以下)', rc(photo('12 03 41'), 0.3, 0.4, 0.56, 0.52)),
        ('子供用の箸・スプーン・フォークとおもちゃ', photo('12 24 52')),
        ('辛麺', frame('12 25 34', 3.5).crop((0, 400, 2160, 3440))),
    ])
    # ---- 伽喱本舗 ----
    c = photo('12 02 49')
    mosaic(c, (850, 2100, 1080, 2420)); mosaic(c, (2050, 2100, 2300, 2420))   # カウンター内の店員
    mosaic(c, (1240, 2130, 1460, 2420))   # 奥の店員(マスク姿)
    thumb(CID, rc(c, 0.17, 0.08, 0.77, 0.6))
    out[CID] = put(CID, [
        ('店頭', rc(c, 0.0, 0.08, 1.0, 0.6)),
        ('焼きカレー', frame('12 30 57', 2.4).crop((0, 300, 2160, 3340))),
        ('セルフコーナーの子供用取り皿', photo('12 29 28')),
    ])
    # ---- ASOBLE ----
    a = frame('11 59 19', 2.7)
    thumb(AID, a.crop((0, 500, 2160, 3200)))
    out[AID] = put(AID, [
        ('入口', a.crop((0, 600, 2160, 2800))),
        ('ふわふわドーム', frame('13 22 17', 0.9).crop((0, 1250, 2160, 3600))),
        ('発電ブランコ', frame('13 08 31', 4).crop((0, 200, 2160, 3400))),
        ('スベリほう台', frame('13 07 19', 3).crop((0, 0, 2160, 3200))),
        ('迷宮の壁', frame('13 09 10', 3).crop((0, 0, 2160, 3200))),
        ('遊具は6〜12歳の掲示', rc(photo('13 12 19'), 0.15, 0, 0.9, 0.95)),
        ('ミニトレイン', rc(photo('13 06 33'), 0, 0.1, 0.78, 1)),
        ('カフェのベビーチェア', photo('13 05 37')),
        ('ベビーカー置き場', rc(photo('13 12 09'), 0.45, 0.0, 1, 0.4)),
        ('GEAR KINGの料金(2026年10月)', rc(photo('13 05 57'), 0.4, 0.3, 1, 0.8)),
    ])
    return out


PARENT_VERDICT = (
    "スペースワールド跡地のアウトレット。イオンモール八幡東と連絡ブリッジでつながる。"
    "⭐ベビールーム(公式は3か所): 個室の授乳ブースとおむつ替え台、調乳用温水器、離乳食用の電子レンジあり。"
    "館内トイレにオムツ替え台・ベビーカー同伴可能ブース・ベビーチェアの案内、授乳ポッド「mamaro」もある(2026-10-08現地確認)。"
    "⭐ベビーカー無料貸出(1Fインフォメーション 10:00〜19:30・生後1ヶ月〜48か月・予約不可)、遊具の貸出(2時間まで・雨天なし)。"
    "⭐1F FOOD FOREST(13店)にベルト付きの木製子供椅子。"
    "⭐屋内の遊び場ASOBLE(入場無料・遊具は6〜12歳)、屋外に3〜6歳向けの丸太の遊び場、芝生の丘(HILLSIDE PLAZA)、"
    "3〜6歳の「みずべのあそびば」(⚠オムツ着用では利用不可・訪問日はメンテナンス中)。"
    "敷地内にスペースLABO(北九州市科学館)と英語体験施設KGG(⚠KGGは商業目的の撮影禁止)。"
    "営業 アウトレット10:00〜20:00/FOOD FOREST 10:00〜21:00/レストラン・カフェ11:00〜21:00。全館禁煙。"
    "駐車場無料(約4,500台)。JRスペースワールド駅から徒歩約2分。(2026-10-08実訪問)"
)

FC_KIDS = {"stroller": True, "diaper": "facility", "tatami": None, "kidsChair": "facility", "serveMin": None, "noise": "ok"}


def main():
    with open(SPOTS, encoding='utf-8') as f:
        data = json.load(f)
    by = {s['id']: s for s in data}
    for k in (PID, 'sp3c07c7fde2', 'spacelabo-kitakyushu', 'ev-602195-kgg'):
        assert k in by, k
    for k in (MID, CID, AID):
        assert k not in by, k
    assert not [s for s in data if 'ASOBLE' in s['name'] or '伽喱本舗' in s['name'] or '伽哩本舗' in s['name']]

    shutil.copy(SPOTS, SPOTS + '.bak_outlets_kitakyushu_20261008')
    imgs = make_images()

    # ---- 親 ----
    p = by[PID]
    p.update({
        'wish': False, 'visited': V, 'with': 'family', 'category': 'play',
        'address': '福岡県北九州市八幡東区東田4-1-1',
        'kids': {"stroller": True, "diaper": True, "tatami": None, "kidsChair": True, "serveMin": None, "noise": "ok"},
        'verdict': PARENT_VERDICT,
        'thumb': PID + '.jpg', 'photos': imgs[PID],
        'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'manual',
        'web': 'https://the-outlets-kitakyushu.aeonmall.com/',
    })
    lat, lng = p['lat'], p['lng']
    fc_lat, fc_lng = by['sp3c07c7fde2']['lat'], by['sp3c07c7fde2']['lng']   # FOOD FOREST(極味やと同じフードコート)

    base = {'area': '東田', 'city': '北九州市八幡東区', 'pref': '福岡県',
            'address': '福岡県北九州市八幡東区東田4-1-1(THE OUTLETS KITAKYUSHU)',
            'with': 'family', 'wish': False, 'visited': V, 'in': PID,
            'video': {'youtube': None, 'tiktok': None, 'instagram': None}}

    data.append(dict(base, **{
        'id': MID, 'name': '元祖辛麺屋 桝元 ジ アウトレット北九州店', 'genre': '辛麺',
        'lat': fc_lat, 'lng': fc_lng, 'category': 'gourmet', 'kids': dict(FC_KIDS),
        'verdict': (
            "THE OUTLETS KITAKYUSHU 1F FOOD FOREST(1010)。"
            "⭐小学生以下向けの「ジュニアラーメン」(中華麺・たまご・チャーシュー・コーン)単品500円/ごはん・ふりかけ・おもちゃ付きセット700円"
            "(2026-10-08店頭の掲示。キャンペーン価格の表記あり)。"
            "⭐受け取り口に子供用の箸・スプーン・フォーク・小さいお椀と、子供向けのおもちゃのカゴ(2026-10-08現地確認)。"
            "フードコート共用のベルト付き子供椅子・ベビールームあり。⚠辛麺は辛さを選べるが大人向け。"
            "10:00〜21:00(L.O.20:30)。TEL 093-616-8484。(2026-10-08実訪問)"),
        'tabelog': 'https://tabelog.com/fukuoka/A4004/A400403/40060600/',
        'thumb': MID + '.jpg', 'photos': imgs[MID],
    }))
    data.append(dict(base, **{
        'id': CID, 'name': '伽喱本舗 THE OUTLETS KITAKYUSHU店', 'genre': '焼きカレー',
        'lat': fc_lat, 'lng': fc_lng, 'category': 'gourmet', 'kids': dict(FC_KIDS),
        'verdict': (
            "THE OUTLETS KITAKYUSHU 1F FOOD FOREST(1004)の門司港焼きカレー。ご飯にカレー・チーズ・卵をのせて焼き上げる。"
            "⭐キッズセット680円(選べるおもちゃ・ポテト・ドリンク付き/公式)。"
            "⭐セルフコーナーに子供用の取り皿あり(2026-10-08現地確認)。フードコート共用のベルト付き子供椅子・ベビールームあり。"
            "⚠焼きたての器は熱いので子供の手元に注意。10:00〜21:00(L.O.20:30)。TEL 093-661-2720。(2026-10-08実訪問)"),
        'tabelog': 'https://tabelog.com/fukuoka/A4004/A400403/40060598/',
        'thumb': CID + '.jpg', 'photos': imgs[CID],
    }))
    data.append(dict(base, **{
        'id': AID, 'name': 'ASOBLE(アソブル)ジ アウトレット北九州店', 'genre': '屋内アミューズメント・遊び場',
        'lat': lat, 'lng': lng, 'category': 'play',
        'kids': {"stroller": True, "diaper": "facility", "tatami": None, "kidsChair": True, "serveMin": None, "noise": "ok"},
        'ages': ['toddler', 'kids'], 'ages_src': 'manual',
        'verdict': (
            "THE OUTLETS KITAKYUSHU 1F(G-SITE)の屋内アミューズメント。⭐入場無料。"
            "⭐無料の遊具: ふわふわドーム、スベリほう台(ボルダリング付きの坂)、迷宮の壁、発電ブランコ・発電シーソー・発電スピナー。"
            "⚠無料遊具は6〜12歳用(小さい子は保護者同伴)。人工芝の「PLAY!」広場は小さい子もゴロゴロできる。訪問日は発電スピナーが使用禁止だった。"
            "有料: ミニトレイン、メガクレーン番長500円、AR体験アニマルニア1プレイ500円(5歳以上)、"
            "砂場ラジコン GEAR KING(20分+ドリンク700円/+ポップコーン900円)(2026-10-08店内掲示)。"
            "⭐カフェ(ASOBLE Cafe&Foods)に木製のベビーチェア、遊具エリアの階段前にベビーカー置き場あり。"
            "10:00〜21:00(ふわふわドーム最終入場20:30)・年中無休。TEL 093-482-7715。(2026-10-08実訪問)"),
        'web': 'https://asoble.jp/shop/the-outlets-kitakyushu/',
        'thumb': AID + '.jpg', 'photos': imgs[AID],
    }))

    # ---- in 紐付け ----
    by['sp3c07c7fde2']['in'] = PID
    if 'フロアマップ' not in by['sp3c07c7fde2']['verdict']:
        by['sp3c07c7fde2']['verdict'] += "(館内フロアマップ 1011 に掲載・2026-10-08時点で営業)"
    by['spacelabo-kitakyushu']['in'] = PID
    by['ev-602195-kgg']['in'] = PID

    # ---- 整合チェック ----
    ids = [x['id'] for x in data]
    assert len(ids) == len(set(ids)), 'id重複'
    bad = [x['id'] for x in data if x.get('wish') is True and any((x.get('video') or {}).values())]
    assert not bad, bad
    names = [x['name'] for x in data]
    assert len([n for n in names if n in (by[PID]['name'],)]) == 1
    with open(SPOTS, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('spots.json updated', len(data))


if __name__ == '__main__':
    main()
