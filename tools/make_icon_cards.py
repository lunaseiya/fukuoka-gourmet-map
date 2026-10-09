# -*- coding: utf-8 -*-
"""撮影禁止の施設用「アイコン案内カード」(写真の代わり)【2026-10-02ユーザー確定】
   施設が館内撮影を禁止している場合、写真を外して設備をアイコン+文字のカードで示す。
   python tools/make_icon_cards.py  → map/photos/<id>_iconNN_<内容>.jpg を作り、spots.json の photos を差し替える"""
import io, json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
EMOJI = r'C:\Windows\Fonts\seguiemj.ttf'
FONT = r'C:\Users\totor\.claude\skills\short-video\assets\MPLUSRounded1c-Black.ttf'
MEI = r'C:\Windows\Fonts\meiryo.ttc'
NOTE = '※施設の方針により館内の写真は掲載していません'

# id: (サムネ用の1枚目index, [(絵文字, 見出し, 説明, 背景色)], 外す写真, 残す写真)
CARDS = {
 'branchfukuokashimobaru': (0, [
   ('🚼', 'ベビールーム(2階)', 'おむつ替え台2台・幼児用便座のある個室', (232, 244, 238)),
   ('🍼', '調乳用のお湯', '浄水給湯器(約79℃)とシンク', (255, 243, 224)),
   ('🚹', '男性トイレにも', 'おむつ替えシートあり。パパだけでも安心', (226, 238, 252)),
   ('🤱', '授乳室', '女性専用(パパは入れない)・空室表示あり', (252, 232, 240)),
   ('♿', '多目的トイレ', 'ベビーチェア・フィッティングシートの表示あり', (238, 238, 245)),
  ], ['branch_03.jpg', 'branch_04_2階トイレの入口と利用時間の掲示.jpg', 'branch_05_多目的トイレ.jpg',
      'branch_06_授乳室は女性専用.jpg', 'branch_07_調乳専用の給湯器とシンク.jpg',
      'branch_08_おむつ替え台2台と幼児用便座.jpg', 'branch_09_男性トイレにもおむつ替え.jpg'],
  ['branch_01.jpg', 'branch_02.jpg']),
 'acrossmall-kasuga': (0, [
   ('🚼', 'ベビールーム', '授乳室・おむつ替えあり', (232, 244, 238)),
   ('🍼', '調乳用のお湯', '体重計もある', (255, 243, 224)),
   ('🪑', 'キッズチェア', 'フードコートに木製キッズチェア', (238, 238, 245)),
   ('🎈', 'こどもひろば どれみ', '2階の屋内あそび場(0〜12歳)', (226, 238, 252)),
   ('🎰', 'ガチャ・ゲームセンター', 'ガシャポン専門店・駄菓子屋も', (252, 232, 240)),
  ], [], []),
 'doremi-acrossmall-kasuga': (0, [
   ('🎈', 'こどもひろば どれみ', '0〜12歳の屋内あそび場(アクロスモール春日2F)', (226, 238, 252)),
   ('🔵', 'ボールプール', 'エアートランポリンも', (232, 244, 238)),
   ('🧗', 'ボルダリング', 'ままごとキッチンも', (255, 243, 224)),
   ('👶', 'ハイハイマット', '赤ちゃん専用のエリア', (252, 232, 240)),
   ('💴', 'こども1時間600円', 'おとな200円・0歳は無料(年齢確認)', (255, 250, 210)),
  ], [], []),
 # 店頭掲示「写真、動画撮影やSNS等でのLIVE配信はお断り」(2026-10-09 ユーザー実訪問・掲示の内容から)
 'asobikuru-shingu': (0, [
   ('🎈', 'アソビクルひろば', '無料のキッズエリア・小学生までと保護者', (226, 238, 252)),
   ('🌴', 'エアー遊具とままごと', 'ジャングル風すべり台・ままごとハウス', (232, 244, 238)),
   ('🎁', '無料ガラポン', '小学6年生まで毎日1回・誕生月ガラポンも', (255, 243, 224)),
   ('🧸', '10円からのクレーンゲーム', '10〜40円の台あり・子供用の踏み台あり', (252, 232, 240)),
   ('🕕', '中学生以下は18時まで', '保護者同伴なら20時まで', (238, 238, 245)),
  ], [], []),
}
# 引数で id を渡すとその施設だけ作る(既存施設のカードを作り直さないため)
if len(sys.argv) > 1:
    CARDS = {k: v for k, v in CARDS.items() if k in sys.argv[1:]}


def card(emoji, title, sub, bg, out):
    W, H = 1080, 1080
    im = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 40, W - 40, H - 40], 60, outline=(200, 200, 205), width=6, fill=(255, 255, 255))
    em = Image.new('RGBA', (320, 320), (0, 0, 0, 0))
    ImageDraw.Draw(em).text((0, 0), emoji, font=ImageFont.truetype(EMOJI, 109), embedded_color=True)
    em = em.crop(em.getbbox()); k = 360 / max(em.size); em = em.resize((max(1, int(em.width * k)), max(1, int(em.height * k))), Image.LANCZOS)   # 縦長の絵文字も 360x360 の枠に収める
    im.paste(em, ((W - em.width) // 2, 170 + (360 - em.height) // 2), em)
    f1 = ImageFont.truetype(FONT, 88)
    while d.textlength(title, font=f1) > W - 160: f1 = ImageFont.truetype(FONT, f1.size - 4)
    d.text(((W - d.textlength(title, font=f1)) / 2, 600), title, font=f1, fill=(30, 30, 35))
    f2 = ImageFont.truetype(MEI, 46)
    while d.textlength(sub, font=f2) > W - 160: f2 = ImageFont.truetype(MEI, f2.size - 2)
    d.text(((W - d.textlength(sub, font=f2)) / 2, 730), sub, font=f2, fill=(80, 80, 90))
    f3 = ImageFont.truetype(MEI, 30)
    d.text(((W - d.textlength(NOTE, font=f3)) / 2, 950), NOTE, font=f3, fill=(150, 150, 155))
    im.save(out, quality=88)
    return im


s = json.load(io.open(P, encoding='utf-8'))
shutil.copy(P, P + '.bak_iconcards')
by = {x['id']: x for x in s}
for sid, (ti, items, drop, keep) in CARDS.items():
    x = by[sid]
    names = []
    for i, (e, t, sb, bg) in enumerate(items, 1):
        nm = '%s_icon%02d_%s.jpg' % (sid, i, t.replace(' ', '').replace('/', ''))
        im = card(e, t, sb, bg, os.path.join(PH, nm)); names.append(nm)
        if i - 1 == ti:
            th = im.resize((300, 300), Image.LANCZOS).crop((30, 0, 270, 300)); th.save(os.path.join(TH, sid + '.jpg'), quality=88)
    for f in drop:
        fp = os.path.join(PH, f)
        if os.path.exists(fp): os.remove(fp)
    x['photos'] = keep + names
    x['thumb'] = sid + '.jpg'
    v = x.get('verdict') or ''
    v = v.replace(' ※施設が館内でのSNS投稿目的の撮影を禁止しているため(要事前許可・TEL 092-284-0855)、写真は掲載していません。', '')
    v = v.replace('(写真あり)', '')
    if '館内の写真は掲載していません' not in v:
        v += ' ※施設の方針(館内撮影お断り)により、館内の写真は掲載せずアイコンで案内しています。'
    x['verdict'] = v
    print(sid, '→', len(names), 'cards / keep', keep)
# 屋外あそび場は写真を残す(branch_01/02は屋外)
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
