# -*- coding: utf-8 -*-
"""イオンモール八幡東 実訪問(2026-10-08)の反映 + 館内の子スポット追加。

使い方:
  python tools/add_aeon_yahatahigashi_20261008.py            … 写真・サムネの生成だけ(spots.json は触らない)
  python tools/add_aeon_yahatahigashi_20261008.py --apply    … 写真生成 + spots.json 書き込み
  (書き込み後は monetize.py --ids <新規id> --apply と build_pages.py を回す)

素材: ショート動画用/イオンモール八幡東/ (写真48枚+動画1本・2026-10-08撮影)。読むだけ。移動・リネームしない。
  動画は bt709(SDR)・3840x2160→自動回転で 2160x3840。tonemap 不要。

撮影ルール(2026-10-08 curl で原文確認):
  yahatahigashi.aeonmall.jp の トップ/モールガイド/営業時間/アクセス/設備・サービス/キッズガイド に
  「撮影」「SNS」の禁止・制限の記載なし(「撮影」はスタジオアリス・証明写真機の文脈のみ)。
  館内写真にも撮影禁止の掲示は写っていない → 写真はそのまま使う(⚠未確認扱い・🟢禁止表示なし)。

根拠:
  - 公式 設備・サービス/キッズガイド(https://yahatahigashi.aeonmall.jp/guide/equipment, /kids):
    赤ちゃんルーム=1F島村楽器裏(オムツ替えルームのみ男性可)/3Fダイソー裏(男性不可)/3F直営ベビー用品売場内。
    授乳室・調乳用浄水器付シンク(調乳に適したお湯)・哺乳瓶洗浄シンク・オムツ替えベッド。おむつ替えベッドは全ての女性・男性トイレ。
    mamaro(ライトオン横)。Kids Garden(3F FOOD FOREST内・お子さま向けイス/テーブル・対面型カウンター)、
    フードフォレスト内3ヵ所にベビーチェア。フードコート約720席。キャラクター付きカート11種150台。
    お子さま用洗面台(全トイレ)・補助便座。
  - 公式 アクセス: 駐車場2,000台・全て無料。TEL 093-663-7111。住所 福岡県北九州市八幡東区東田3丁目2-102。
  - 公式 営業時間: 専門店10:00〜21:00 / FOOD FOREST 10:00〜21:00 / 1Fレストラン街 11:00〜22:00 /
    モーリーファンタジー 9:00〜21:00(16歳未満18:00以降入場不可・保護者同伴は21:00まで)/ のびっこ 10:00〜18:00(最終受付17:30)
  - 公式 グルメ一覧: 1Fレストラン街13店・3F FOOD FOREST(マクドナルド/KFC/リンガーハット/伊吹や製麺/ミスド/サーティワン/
    ペッパーランチ/パルメナーラ/笑たこ/ディッパーダン)
  - 公式 しゃぶ菜ページ: 1F 118・11:00〜22:00(LO21:30・入店21:00まで)・TEL 093-671-1895
  - 現地写真(2026-10-08):
    P27 1F ファミリールーム(男性入室可)/授乳室(男性入室不可)・「さく乳でもご利用ください」/ P28 調乳用お湯・シンク・電子レンジ
    P07 男性トイレ「オムツ替え台/ベビーカー同伴可能ブース/ベビーチェア」/ P03 ベビーシート付きカート / P22 キャラクターカート
    P37 3Fフードコートの家族専用カウンター(はめ込み式ベビーチェア)/ P38 子供用ハイチェア / P48 3F赤ちゃん休憩室(直営おもちゃ売場横)
    P46 のびっこ 料金・営業時間・入場の注意(0歳〜小学2年生・16歳以上の保護者付き添い・飲食授乳不可)
    P18 しゃぶ菜 店頭の料金(小学生未満無料・小学生899円(税込988円))
  - 食べた店は写真から特定できない(料理写真なし)→ 館内の飲食店はどれも赤にしない。
    子スポット(のびっこ/モーリーファンタジー/トイザらス/しゃぶ菜)は店構え・掲示を撮っただけなので青ピン。
  - 人の映り込み: のびっこの幼児(他人の子・ユーザーの子ではない)/モーリーファンタジー奥の人 → モザイク。
    キャラクターカート(奥のエスカレーターの人)・フードコート(KFC前の人)は人が入らない位置で切り出し。
    ユーザーの子どもが写った素材は無し → 子供達フォルダへのコピーは無し。
  - 近くの スシロー 八幡東田店(spb4b3a4647f)は館外なので触らない。THE OUTLETS KITAKYUSHU は別エージェント担当。
  - 子の座標は親と共有(館内)。
"""
import io, json, os, re, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOTS = os.path.join(ROOT, 'data', 'spots.json')
PHOTOS = os.path.join(ROOT, 'map', 'photos')
THUMBS = os.path.join(ROOT, 'map', 'thumbs')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\イオンモール八幡東'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
TMP = os.path.join(os.environ.get('TEMP', ROOT), 'aeon_yahatahigashi_frames')
PID = 'aeonmallyahatahigashi'
V = '2026-10-08'
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}


def photo(t):
    """写真 'HH MM SS' → exif_transpose 済み RGB(3024x4032)"""
    p = os.path.join(SRC, f'写真 2026-10-08 {t}.jpg')
    return ImageOps.exif_transpose(Image.open(p)).convert('RGB')


def vframe(t):
    """動画から1フレーム(自動回転・フル解像度)。ffmpeg は1本ずつ"""
    os.makedirs(TMP, exist_ok=True)
    o = os.path.join(TMP, f'v_{t}.jpg')
    subprocess.run([FF, '-y', '-v', 'error', '-ss', str(t), '-i', os.path.join(SRC, '動画 2026-10-08 13 47 08.mov'),
                    '-frames:v', '1', '-q:v', '2', o], check=True)
    return Image.open(o).convert('RGB')


def mosaic(im, box, block=16):
    """box=(x0,y0,x1,y1) 元解像度の座標。グリッドを焼いた縮小画像で実測済み"""
    x0, y0, x1, y1 = box
    reg = im.crop(box)
    small = reg.resize((max(1, (x1 - x0) // block), max(1, (y1 - y0) // block)), Image.BILINEAR)
    im.paste(small.resize(reg.size, Image.NEAREST), (x0, y0))
    return im


def w1080(im):
    if im.width != 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
    return im


def thumb45(im, box):
    """box を 4:5 に合わせて 240x300"""
    return im.crop(box).resize((240, 300), Image.LANCZOS)


def save(im, path, review):
    os.makedirs(review, exist_ok=True)
    im.save(path, quality=88)
    shutil.copy(path, os.path.join(review, os.path.basename(path)))
    print('wrote', os.path.relpath(path, ROOT), im.size)


def put_photos(sid, items):
    """items=[(内容, PIL画像)] → map/photos/<sid>_NN_内容.jpg"""
    review = os.path.join(ROOT, 'thumbs_review', sid)
    names = []
    for i, (label, im) in enumerate(items, 1):
        fn = f'{sid}_{i:02d}_{label}.jpg'
        save(w1080(im), os.path.join(PHOTOS, fn), review)
        names.append(fn)
    return names


def put_thumb(sid, im):
    save(im, os.path.join(THUMBS, f'{sid}.jpg'), os.path.join(ROOT, 'thumbs_review', sid))
    return f'{sid}.jpg'


# ---------------- 子スポット ----------------
NOBICCO = 'yahatahigashi-nobicco'
MOLLY = 'yahatahigashi-mollyfantasy'
TOYS = 'yahatahigashi-toysrus'
SHABU = 'yahatahigashi-shabusai'


def make_images():
    out = {}
    # ===== 親: イオンモール八幡東 =====
    ext = vframe(3.5)                                         # 2160x3840。THE OUTLETS 側から見た建物(AEON ロゴ)。人なし
    th = put_thumb(PID, thumb45(ext, (300, 1250, 1700, 3000)))
    p27 = photo('14 02 55')                                   # ファミリールーム入口(人なし)
    p28 = photo('14 03 38')                                   # 調乳コーナー(人なし)
    p07 = photo('13 53 20')                                   # 男性トイレの設備表示(人なし)
    p22 = photo('13 58 17')                                   # キャラクターカート。上部 y<730 にエスカレーターの人 → y>=820 で切る
    p03 = photo('13 49 48')                                   # ベビーシート付きカート(人なし)
    p37 = photo('14 11 07')                                   # 家族専用カウンター。上部(y<920)のKFC前に人 → y>=980 で切る
    p38 = photo('14 11 14')                                   # 子供用ハイチェア。左上(x<260,y<650)に客 → y>=700 で切る
    p48 = photo('14 15 57')                                   # 3F 赤ちゃん休憩室(人なし)
    out[PID] = {'thumb': th, 'photos': put_photos(PID, [
        ('外観(THE OUTLETS側から)', ext.crop((300, 1000, 2160, 3300))),
        ('1Fファミリールーム(男性OK)と女性専用授乳室', p27.crop((300, 300, 3024, 3700))),
        ('調乳用のお湯・シンク・電子レンジ', p28.crop((0, 600, 3024, 3100))),
        ('男性トイレにもおむつ替え台とベビーチェア', p07.crop((0, 300, 3024, 3400))),
        ('キャラクターカート', p22.crop((0, 820, 3024, 4032))),
        ('ベビーシート付きカート', p03),
        ('3Fフードコートの家族専用カウンター(ベビーチェア)', p37.crop((0, 980, 3024, 4032))),
        ('フードコートの子供用ハイチェア', p38.crop((0, 700, 3024, 4032))),
        ('3F赤ちゃん休憩室', p48),
    ])}

    # ===== のびっこ =====
    p47 = photo('14 15 30')                                   # 店内全景。幼児(他人の子)と奥の人にモザイク
    mosaic(p47, (2540, 2200, 2900, 2720), block=18)
    mosaic(p47, (330, 1620, 640, 1920), block=16)
    p46 = photo('14 15 25')                                   # 料金・営業時間の掲示。幼児(x565-790,y1150-1520)は範囲外で切る
    out[NOBICCO] = {'thumb': put_thumb(NOBICCO, thumb45(p47, (400, 1032, 2800, 4032))),
                    'photos': put_photos(NOBICCO, [
                        ('ごっこ遊びのエリア', p47.crop((0, 1000, 3024, 4032))),
                        ('料金と営業時間(2026年10月)', p46.crop((1000, 1500, 3024, 3830))),
                    ])}

    # ===== モーリーファンタジー =====
    p45 = photo('14 15 16')
    mosaic(p45, (2290, 2080, 2680, 2440), block=16)          # 奥の通路の人(右のグループ)
    mosaic(p45, (2010, 2090, 2230, 2260), block=16)          # 中央のゲーム機前の人
    mosaic(p45, (1350, 2150, 1520, 2540), block=16)          # 左のゲーム機前の人と子供
    out[MOLLY] = {'thumb': put_thumb(MOLLY, thumb45(p45, (400, 700, 2800, 3700))),
                  'photos': put_photos(MOLLY, [('入口と幼児向けの乗り物', p45.crop((0, 700, 3024, 4032)))])}

    # ===== トイザらス・ベビーザらス =====
    p21 = photo('13 57 30')                                   # 壁面ロゴ(人なし)
    out[TOYS] = {'thumb': put_thumb(TOYS, thumb45(p21, (200, 500, 3024, 4030))),
                 'photos': put_photos(TOYS, [('入口のロゴ', p21.crop((0, 300, 3024, 3900)))])}

    # ===== しゃぶ菜 =====
    p18 = photo('13 56 30')                                   # 店頭の料金ボード。左の客席(x<1300)に客 → x>=1340 で切る
    board = p18.crop((1340, 1411, 2268, 2822))
    out[SHABU] = {'thumb': put_thumb(SHABU, thumb45(p18, (1340, 1420, 2268, 2580))),
                  'photos': put_photos(SHABU, [('店頭の料金(小学生未満無料・2026年10月)', board)])}
    return out


# ---------------- verdict ----------------
PARENT_VERDICT = (
    "イオン八幡東店を核にした3フロアのモール(隣はTHE OUTLETS KITAKYUSHU)。"
    "⭐1F島村楽器裏の赤ちゃんルームは、男性も入れるファミリールーム(おむつ替え)と女性専用の授乳室(さく乳OK)に分かれていて、"
    "調乳用のお湯・シンク・電子レンジあり。3Fダイソー裏(男性不可)と3F直営ベビー用品売場の「赤ちゃん休憩室」にも。"
    "おむつ替え台は男性トイレを含む全トイレにあり、ベビーカーごと入れる個室も。授乳室mamaro(ライトオン横)。"
    "⭐3Fフードコート「FOOD FOREST」(約720席・マクドナルド/ケンタッキー/リンガーハット/伊吹や製麺/ミスド/サーティワン等)に"
    "子連れ家族専用のカウンター席「Kids Garden」(はめ込み式ベビーチェア・対面で食べさせられる)と子供用ハイチェア。"
    "⭐キャラクターカート(11種150台)とベビーシート付きカート。"
    "⭐3Fにモーリーファンタジーと室内遊び場「のびっこ」(0歳〜小学2年生)、1Fにトイザらス・ベビーザらス。"
    "1Fレストラン街はびっくりドンキー・資さんうどん・しゃぶ菜(小学生未満無料)など13店。"
    "駐車場2,000台・無料。10:00〜21:00(レストラン街11:00〜22:00)。TEL 093-663-7111。(2026-10-08実訪問)"
)

CHILDREN = [
    dict(id=NOBICCO, name='のびっこ イオンモール八幡東店', genre='室内遊び場', category='play',
         ages=['baby', 'toddler', 'kids'],
         kids={'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
         web='https://yahatahigashi.aeonmall.jp/guide/hours',
         verdict=(
             "⭐イオンモール八幡東3F・モーリーファンタジー内の室内遊び場(0歳〜小学2年生)。人工芝の上にお好み焼き屋・花屋などのごっこ遊びの屋台。"
             "一般料金: 平日 最初の30分500円・延長10分ごと100円・平日1日フリー700円/土日祝 最初の30分500円・最初の60分700円・延長10分ごと100円。"
             "⭐0歳と保護者は全日無料。トットット会員は割引(平日30分300円・平日1日フリー600円・土日祝60分600円)。スクールホリデー期間は休日料金。"
             "10:00〜18:00(最終受付17:30)。AEON Pay・PayPay可。"
             "⚠16歳以上の保護者の付き添い必須・中での飲食と授乳は不可・混雑時は入場制限あり(料金と注意は2026-10-08店頭掲示)。"
             "おむつ替え・授乳は同じ3Fの赤ちゃん休憩室へ。")),
    dict(id=MOLLY, name='モーリーファンタジー イオンモール八幡東店', genre='ゲームセンター', category='play',
         ages=['toddler', 'kids'], kids=None,
         web='https://yahatahigashi.aeonmall.jp/guide/hours',
         verdict=(
             "イオンモール八幡東3Fのゲームコーナー。幼児向けの乗り物(ワニワニ等)・お菓子すくい・クレーンゲーム・メダル。"
             "奥に室内遊び場「のびっこ」(別料金)。9:00〜21:00。"
             "⚠16歳未満は18:00以降、保護者同伴でないと入場不可(条例)。ゲームは有料。")),
    dict(id=TOYS, name='トイザらス・ベビーザらス イオンモール八幡東店', genre='おもちゃ・ベビー用品', category='play',
         ages=['baby', 'toddler', 'kids'], kids=None,
         web='https://yahatahigashi.aeonmall.jp/access',
         verdict=(
             "イオンモール八幡東1Fのおもちゃ・ベビー用品店(トイザらスとベビーザらスの併設)。"
             "店の前の下りエスカレーター横にキャラクターカート置き場、1Fタクシー乗り場もこの前の出入口。営業時間は要確認(モールは10:00〜21:00)。")),
    dict(id=SHABU, name='しゃぶ菜 イオンモール八幡東店', genre='しゃぶしゃぶ', category='gourmet',
         ages=None, kids=None,
         web='https://yahatahigashi.aeonmall.jp/gourmet/c3597e06-8020-44e9-a415-ff2345548227',
         verdict=(
             "イオンモール八幡東1Fレストラン街のしゃぶしゃぶ・すき焼き食べ放題(野菜バー)。"
             "⭐小学生未満は無料、小学生899円(税込988円)。大人は豚ロース1,868円/ダブル豚2,198円/スタンダード2,638円(税込)。"
             "寿司付き・ドリンクバーは追加料金(料金は2026-10-08店頭)。"
             "11:00〜22:00(LO21:30・入店21:00まで)。TEL 093-671-1895。⚠未訪問(店頭の掲示を見ただけ)。キッズチェア等は要確認。")),
]


def main(apply):
    imgs = make_images()
    if not apply:
        print('\n[images only] spots.json は未変更。--apply で書き込み')
        return
    with open(SPOTS, encoding='utf-8') as f:
        data = json.load(f)
    by = {x['id']: x for x in data}
    names = {x['name'] for x in data}
    assert PID in by, PID
    p = by[PID]
    assert p.get('visited') is None and not p.get('photos'), '親が想定と違う(先に誰かが更新した?)'
    shutil.copy(SPOTS, SPOTS + '.bak_aeon_yahatahigashi_20261008')

    # ---- 親(赤ピン・訪問済み) ----
    p['wish'] = False
    p['visited'] = V
    p['address'] = '福岡県北九州市八幡東区東田3丁目2-102'
    p['web'] = 'https://yahatahigashi.aeonmall.jp/'
    p['kids'] = {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None}
    p['verdict'] = PARENT_VERDICT
    p['thumb'] = imgs[PID]['thumb']
    p['photos'] = imgs[PID]['photos']
    p['ages'] = ['baby', 'toddler', 'kids']
    p['ages_src'] = 'manual'

    # ---- 子(青ピン・館内) ----
    added, skipped = [], []
    for c in CHILDREN:
        if c['id'] in by:
            skipped.append((c['id'], 'id重複')); continue
        if c['name'] in names:
            skipped.append((c['id'], '同名重複')); continue
        x = {'id': c['id'], 'name': c['name'], 'area': None, 'city': p['city'], 'pref': '福岡県', 'genre': c['genre'],
             'lat': p['lat'], 'lng': p['lng'], 'visited': None, 'with': 'family', 'kids': c['kids'],
             'verdict': c['verdict'], 'video': dict(VIDEO0), 'thumb': imgs[c['id']]['thumb'],
             'photos': imgs[c['id']]['photos'], 'wish': True, 'category': c['category'], 'in': PID, 'web': c['web']}
        if c['ages']:
            x['ages'] = c['ages']; x['ages_src'] = 'manual'
        data.append(x); by[x['id']] = x; names.add(x['name']); added.append(x['id'])

    # ---- 整合チェック ----
    ids = [x['id'] for x in data]
    assert len(ids) == len(set(ids)), 'id重複'
    bad = [x['id'] for x in data if x.get('wish') is True and any((x.get('video') or {}).values())]
    assert not bad, f'wish=Trueなのに動画あり: {bad}'
    assert all(re.fullmatch(r'[A-Za-z0-9-]+', i) for i in added)
    for x in [p] + [by[i] for i in added]:
        assert x['category'] in ('gourmet', 'onsen', 'play'), x['id']
        for fn in [x['thumb']]:
            assert os.path.exists(os.path.join(THUMBS, fn)), fn
        for fn in x.get('photos') or []:
            assert os.path.exists(os.path.join(PHOTOS, fn)), fn
    with open(SPOTS, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('spots.json updated. total', len(data), 'added', added, 'skipped', skipped)
    print('IDS', PID, ' '.join(added))


if __name__ == '__main__':
    main('--apply' in sys.argv)
