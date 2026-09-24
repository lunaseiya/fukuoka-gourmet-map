# -*- coding: utf-8 -*-
"""週末イベントまとめの**カルーセル画像**を作る(インスタ/TikTok用 1080x1350)。

`week_events.py` が書いた `data/_週末イベント候補.json` を読んで、
  1枚目 … 表紙(日付 + ◯選 + 県バッジ)
  2枚目〜 … 1イベント1枚(市区ピル / イベント名 / **ポスター画像** / 会期・時間・会場・料金 / 一言)
  最後 … 締め(マップ誘導)
を `data/carousel_<日付>/` に連番で出す。

■ ポスター画像の扱い【2026-09-12〜13 ユーザー確定】
  告知ポスターは「見せたいから作っている」ものなので**出典を明記し改変せずに貼る**。
  ・画像は**枠に収めるだけでトリミングしない**(改変にあたらないように)
  ・カード下部に**主催者/施設名を必ず出す**(出典明記)
  ・⚠**IPコラボ(ポケモン/プリキュア/サンリオ/ちいかわ等)は貼らない**。版元の権利が重なり
    施設側にも再配布権が無い。`week_events.poster_ok()` が False のものは
    ポスター枠の代わりに**テキストカード**にする

使い方:
    python tools/event_carousel.py                      # 直近の候補JSONから作る
    python tools/event_carousel.py --n 12 --title "9月14日(日) おでかけイベント"
"""
import argparse, io, json, os, re, sys, urllib.request
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import week_events as W
import noimg_icon as NOIMG

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
ASSETS = r'C:\Users\totor\.claude\skills\short-video\assets'
ROUND = os.path.join(ASSETS, 'MPLUSRounded1c-Black.ttf')
MEI = r'C:\Windows\Fonts\meiryo.ttc'
MEIB = r'C:\Windows\Fonts\meiryob.ttc'
W_, H_ = 1080, 1350
BG = (250, 247, 242)          # クリーム。白より写真が締まる
INK = (34, 32, 30)
SUB = (120, 114, 108)
PREF_RED = (206, 57, 52)      # 福岡。thumbs_build.py の PREF_COLOR と同じ
ICON_VARIANT = 'frame'        # IPで貼れない回のアイコン(--icon で切替)


def font(p, s):
    return ImageFont.truetype(p, s)


def rounded(size, r, fill):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    im = Image.new('RGBA', size, fill)
    im.putalpha(m)
    return im


def shadow(base, card, xy, blur=16, alpha=52, dy=6):
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    a = card.split()[-1].point(lambda v: int(v * alpha / 255))
    lay = Image.new('RGBA', card.size, (0, 0, 0, 255)); lay.putalpha(a)
    sh.paste(lay, (xy[0], xy[1] + dy), lay)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(card, xy)


def wrap(d, text, f, width, maxline=3):
    # ⚠maxline=0 を渡されると out が空のまま out[-1] で落ちる(2026-09-13に踏んだ)
    if maxline < 1 or not text:
        return []
    out, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=f) > width:
            out.append(cur); cur = ch
            if len(out) >= maxline:
                break
        else:
            cur += ch
    if cur and len(out) < maxline:
        out.append(cur)
    if len(out) == maxline and d.textlength(''.join(out), font=f) < d.textlength(text, font=f):
        out[-1] = out[-1][:-1] + '…'
    return out


# ★⚠**絵文字は Meiryo に字形が無いので□の豆腐になる**【2026-09-18に実機で発覚】
#   「✨観覧無料✨」が「□観覧無料□」と描かれていた。源のタイトルには
#   絵文字がそのまま入っていることがある(イオン九州の店舗お知らせは特に多い)ので、
#   **描く前に落とす**。⚠「〜」「㊏」「①」などは字形があるので消さないこと。
EMOJI = re.compile(
    '['
    '\U0001F000-\U0001FAFF'      # 絵文字・記号の主要ブロック
    '\U00002600-\U000027BF'      # ☀☂✂✨ など
    '\U00002B00-\U00002BFF'      # ⬆⭐ など
    '\U0000FE00-\U0000FE0F'      # 異体字セレクタ
    '\U0001F1E6-\U0001F1FF'      # 国旗
    ']+')


def deemoji(s):
    """絵文字を落として空白を詰める。豆腐(□)を出さないため"""
    return re.sub(r'\s{2,}', ' ', EMOJI.sub('', s or '')).strip(' 　')


def pill(text, fill, fs=34, pad=(22, 10)):
    f = font(MEIB, fs)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    w = int(d0.textlength(text, font=f)) + pad[0] * 2
    h = fs + pad[1] * 2
    im = rounded((w, h), h // 2, fill + (255,))
    ImageDraw.Draw(im).text((w // 2, h // 2), text, font=f, fill=(255, 255, 255, 255), anchor='mm')
    return im


CACHE = os.path.join(HERE, '..', 'data', '_poster_cache')
EXTRA = os.path.join(HERE, '..', 'data', '_イベント補足.json')


def load_extra():
    """手で読んだ事実を差し込むための補足ファイル(キー=イベントURL)。

    ⚠**IPコラボはポスターを貼れないぶん、情報量で勝たなければ負ける**
      (2026-09-13ユーザー指摘「グレーだけどポスター載せてる人がいたりとライバルに負ける」)。
      ポスター画像を**自分で読んで**時間・料金・内容を転記し、ここに置く。
      画像の再配布はしないが、そこに書かれている**情報は普通に書いてよい**"""
    try:
        return json.load(io.open(EXTRA, encoding='utf-8'))
    except Exception:
        return {}


def load_disp():
    """表示名と会場の上書き(キー=イベントURL)。`data/_イベント表示名.json`。

    生のイベント名は「9月18日（金）公開『映画…』映画公開記念 …」のように長く、
    カードに出すと3行に折り返して読めない。**正規表現で機械的に削ると壊れる**ので
    手で確定させたものをここから読む(キャプション側 event_caption.py と同じファイル)"""
    try:
        return json.load(io.open(os.path.join(os.path.dirname(EXTRA),
                                              '_イベント表示名.json'), encoding='utf-8'))
    except Exception:
        return {}


def get_poster(url):
    """ポスター画像を落としてくる(キャッシュする)。**リサイズ以外の加工はしない**"""
    if not url:
        return None
    os.makedirs(CACHE, exist_ok=True)
    key = re.sub(r'[^0-9a-zA-Z]', '_', url)[-90:]
    p = os.path.join(CACHE, key + '.img')
    if not os.path.exists(p):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=W.UA), timeout=30).read()
            io.open(p, 'wb').write(raw)
        except Exception as ex:
            print('  ! ポスター取得失敗 %s (%s)' % (url[:60], type(ex).__name__))
            return None
    try:
        return Image.open(p).convert('RGB')
    except Exception:
        return None


def outline(d, xy, text, f, fill, ow=7, oc=(0, 0, 0, 190), anchor='ma'):
    """白抜き文字に黒縁。写真の上に置くので縁が無いと読めない"""
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            if dx * dx + dy * dy <= ow * ow:
                d.text((x + dx, y + dy), text, font=f, fill=oc, anchor=anchor)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)


def cover(sub, n, total, hook=None, photo=None, tail=None, cta=None, badge_img=None):
    """表紙。**実写を背景に敷いて白抜きの大きなフックを乗せる**
    【2026-09-13ユーザーFB「シンプル過ぎてインパクトがない」で作り直し】
    ⚠人物が写る写真は**人混みが枠に入らない位置で切り出す**(モザイクより優先)。
      博多駅の縦写真(1170x2070)は上から4:5(1462px)で切ると撮影者本人だけになる"""
    if photo and os.path.exists(photo):
        src = ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
        ch = int(src.width * H_ / W_)
        src = src.crop((0, 0, src.width, min(ch, src.height)))   # 上から切る=人混みを外す
        im = src.resize((W_, H_), Image.LANCZOS).convert('RGBA')
        # 下半分に黒のグラデーションを敷いて文字を読ませる
        g = Image.new('L', (1, H_))
        for y in range(H_):
            t = max(0.0, (y / H_ - 0.34) / 0.66)
            g.putpixel((0, y), int(225 * (t ** 1.25)))
        sc = Image.new('RGBA', (W_, H_), (12, 10, 14, 255))
        sc.putalpha(g.resize((W_, H_)))
        im.alpha_composite(sc)
        fg, sub_c = (255, 255, 255, 255), (238, 232, 226, 255)
        ow = 6
    else:
        im = Image.new('RGBA', (W_, H_), BG + (255,))
        fg, sub_c, ow = INK + (255,), SUB + (255,), 0
    d = ImageDraw.Draw(im)
    # ★**県バッジは差し替えられる**【2026-09-16ユーザー指摘
    #   「福岡アイコンちっさすぎるので、サムネと同サイズにしましょう」】
    #   既定は小さいピルだが、`badge_img` を渡せば動画サムネと同じ3層バッジを
    #   同じ位置(1080x1350なら x45 y45 271x166 = thumbs_build の tiktok 実測値)に置く
    if badge_img is not None:
        shadow(im, badge_img, (45, 45), blur=18, alpha=70, dy=6)
    else:
        shadow(im, pill('福岡', PREF_RED, 40), (72, 86))
    hook = hook or 'まだ間に合う'
    # ⚠**下端は再生数の表示位置(グリッドの左下・下端から約110px)を避ける**。
    #   H_-500 だと「スワイプして見てね」のピルが y1208-1266 に来て**再生数と重なった**
    #   (2026-09-14 ユーザーのグリッド実機で発覚)。-580 にすると y1128-1186 で収まる
    y = H_ - 580
    f0 = font(MEIB, 48)
    outline(d, (W_ // 2, y), sub, f0, sub_c, ow) if ow else d.text((W_ // 2, y), sub, font=f0, fill=sub_c, anchor='ma')
    y += 74
    fh = font(ROUND, 132)
    while d.textlength(hook, font=fh) > W_ - 90 and fh.size > 70:
        fh = font(ROUND, fh.size - 4)
    outline(d, (W_ // 2, y), hook, fh, fg, ow + 3) if ow else d.text((W_ // 2, y), hook, font=fh, fill=PREF_RED + (255,), anchor='ma')
    y += fh.size + 26
    f2 = font(ROUND, 86)
    # ⚠**「子連れ」を必ず入れる**【2026-09-13ユーザー指摘「子連れという単語がタイトルにない」】
    #   誰向けの情報なのかが1枚目で伝わらないと、子育て世代に刺さらない
    tail = (tail or '福岡の子連れおでかけ %d選') % n if '%d' in (tail or '%d') else tail
    while d.textlength(tail, font=f2) > W_ - 110 and f2.size > 54:
        f2 = font(ROUND, f2.size - 3)
    outline(d, (W_ // 2, y), tail, f2, fg, ow) if ow else d.text((W_ // 2, y), tail, font=f2, fill=INK + (255,), anchor='ma')
    y += f2.size + 40
    # ⚠**リールに出すときは「スワイプ」と書かない**。動画なので操作が成立しない
    #   (2026-09-14ユーザー確認。YouTube版でも同じ指摘を受けている)
    pl = pill(cta or 'スワイプして見てね →', PREF_RED, 38)
    shadow(im, pl, ((W_ - pl.width) // 2, y))
    return im.convert('RGB')



# ⚠**イベント一覧の実物**に差し替え【2026-09-24ユーザー指示】。
#   マップの地図画面より、この投稿から実際に飛ぶ先(子連れイベントの一覧)を見せる
MAPCARD = r'C:\Users\totor\Dropbox\ショート動画用\5.共通素材\マップ操作_静止カード_イベント一覧.png'
# 左に置く「マップ画面(イベントタブを赤丸で囲んだもの)」【2026-09-24ユーザー提供】
MAPSHOT = r'C:\Users\totor\Dropbox\ショート動画用\5.共通素材\マップ操作_静止カード_マップ画面.jpg'
# 表紙の既定背景。博多駅の縦写真(1170x2070)。上から4:5で切ると人混みが枠外に出る
# ⚠**毎回同じ絵にしない**【2026-09-24ユーザー指摘「同じイベントリストに見える」】。
#   共通素材から回ごとに違う背景を選ぶ(--cover で明示指定できる)
COVER_DEFAULT = r'C:\Users\totor\Dropbox\ショート動画用\5.共通素材\表紙用_キャナル噴水_縦.jpg'


def closing():
    """締め。**マップ画面 → イベント一覧 の2枚を横並びにして矢印で結ぶ**
    【2026-09-24ユーザー指示】。1枚だけだと「どこを押せばこの一覧に行くのか」が
    伝わらない。左=マップでイベントタブを押すところ(赤丸付き) / 右=出てくる一覧。
    素材は 5.共通素材/マップ操作_静止カード_マップ画面.jpg と _イベント一覧.png"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((W_ // 2, 46), '気になったイベントは「検索」の言葉で調べられます',
           font=font(MEI, 30), fill=SUB + (255,), anchor='ma')
    d.text((W_ // 2, 96), '行った店も 今やってるイベントも', font=font(MEIB, 44),
           fill=INK + (255,), anchor='ma')
    d.text((W_ // 2, 152), 'マップにまとめてます', font=font(ROUND, 72),
           fill=PREF_RED + (255,), anchor='ma')
    y = 268
    shots = [(MAPSHOT, 'マップのイベントタブを押すと'), (MAPCARD, '今週のイベントが一覧で出ます')]
    have = [(a, b) for a, b in shots if os.path.exists(a)]
    if have:
        ch = 620
        gap = 96
        cws = []
        for a, _b in have:
            c = Image.open(a).convert('RGB')
            cws.append(round(c.width * ch / c.height))
        n = len(have)
        total = sum(cws) + gap * (n - 1) + 16 * n
        x = (W_ - total) // 2
        for k, ((a, cap), cw) in enumerate(zip(have, cws)):
            c = Image.open(a).convert('RGB')
            card = rounded((cw + 16, ch + 16), 18, (255, 255, 255, 255))
            card.paste(c.resize((cw, ch), Image.LANCZOS), (8, 8))
            shadow(im, card, (x, y), blur=20, alpha=66, dy=7)
            d.text((x + (cw + 16) // 2, y + ch + 34), cap, font=font(MEIB, 27),
                   fill=SUB + (255,), anchor='ma')
            if k < n - 1:
                ax = x + cw + 16 + 16
                ay = y + ch // 2
                aw = gap - 32
                d.rounded_rectangle((ax, ay - 11, ax + aw - 22, ay + 11), 10,
                                    fill=PREF_RED + (255,))
                d.polygon([(ax + aw - 28, ay - 28), (ax + aw, ay), (ax + aw - 28, ay + 28)],
                          fill=PREF_RED + (255,))
            x += cw + 16 + gap
        y += ch + 92
    for lb, dy in (('子供椅子で絞れる', 0), ('おむつ替えで絞れる', 56), ('期間限定も出る', 112)):
        t = pill(lb, (96, 90, 86), 28)
        im.alpha_composite(t, ((W_ - t.width) // 2, y + dy))
    y += 186
    pl = pill('プロフィールのリンクから見れます', PREF_RED, 38)
    shadow(im, pl, ((W_ - pl.width) // 2, y))
    d.text((W_ // 2, H_ - 50), '保存しておくと行くときに使えます',
           font=font(MEI, 28), fill=SUB + (255,), anchor='ma')
    return im.convert('RGB')


# 集約サイト名。会場として出さない
AGG_NAMES = ('いこーよ', '県公式')


def search_word(ev):
    """読み手がそのまま検索できる語を作る【2026-09-13ユーザーFB】
    「公式で確認」と書いても**どこを見ればいいのか分からない**と言われた。
    InstagramはキャプションのURLもリンクにならないので、**検索ワードを書く**のが確実。
    会場名 + イベント名の核(記号と長い枕を落としたもの)で組む"""
    t = ev.get('title', '')
    t = re.sub(r'^[【（(\[][^】）)\]]{0,20}[】）)\]]\s*', '', t)     # 先頭の【福岡】等を落とす
    t = re.sub(r'\s*(開催中|開催決定|のお知らせ|スタート|好評)+[！!]*$', '', t)
    t = re.sub(r'[『』「」【】（）()《》\[\]♪！!？?]', '', t)
    t = re.sub(r'[\s　]+', ' ', t).strip()
    # 副題(〜以降・「の巻」等)は検索の邪魔なので落とす。前半だけで十分当たる
    t = re.split(r'[〜～~\-–—:：]', t)[0].strip()
    if len(t) > 13:
        t = t[:13]
    # ⚠検索ワードの会場は **venue(施設名)** を使う。
    #   place(「プラネタリウム・4階天体観測広場」等)は**館内の場所**なので、
    #   これを先頭に置くと検索で当たらない(2026-09-13にカードに出してしまった)
    ven = [v for v in (ev.get('venues') or []) if v and v not in AGG_NAMES]
    place = ev.get('venue') or (ven[0] if ven else '') or ev.get('city') or ''
    place = re.sub(r'^福岡県(?=.)', '', place)
    # 館内の場所やフロア表記が付いていたら落とす
    place = re.split(r'\s+(?=[0-9０-９]+\s*[FＦ階]|特設|セントラル|イベントホール|会場)', place)[0].strip()
    return ('%s %s' % (place, t)).strip() if place and place not in t else t


# ─────────── 参考アカウントの見え方を取り入れた3要素【2026-09-17ユーザー要望】 ───────────
#   「有料・無料ラベル / ポスター / 左下に場所などの補足情報 / 右下のmemoで概ね何の企画か分かる /
#     タブで表示されていて、何日が対象かわかる」が見やすいという指摘。
#   ポスターと補足情報は既にあったので、**日付タブ・有料無料バッジ・memo枠**を足す。
TAB_H = 96                       # 日付タブの帯の高さ
TAB_ON = (255, 255, 255)         # 選択中のタブ(白く抜く)
TAB_OFF = [(246, 214, 220), (203, 227, 238), (206, 231, 199),
           (250, 231, 178), (225, 217, 212)]   # 曜日ごとに色を変える(参考と同じ考え方)


def daytabs(im, d, days, cur, hit=None):
    """上端に日付タブを描く。
    ⚠**「何の日付なのか分からない」【2026-09-24ユーザー指摘】**を受けて作り直した。
      ・左端に「開催日」のラベルを出す(タブだけでは何の日か伝わらない)
      ・**そのイベントが開催される日を全部**濃く塗る(`hit` = ISO の集合)。
        以前は1日だけ白抜きで、2日間開催なのに片方しか目立たず
        「26日なのか27日なのか両方なのか分からない」と言われた
      ・開催しない日は薄いグレーにして、文字も薄くする
    """
    if not days:
        return
    ds = list(days)
    if len(ds) > 5:
        i0 = ds.index(cur) if cur in ds else 0
        st = max(0, min(i0 - 2, len(ds) - 5))
        ds = ds[st:st + 5]
    hit = set(hit or ([cur] if cur else []))
    wk = '月火水木金土日'
    lab_w = 118                      # 左の「開催日」ラベルの幅
    gap = 6
    n = len(ds)
    bw = (W_ - lab_w - gap * n) // n
    d.rectangle((0, 0, W_, TAB_H), fill=(238, 235, 230, 255))
    d.text((lab_w // 2, TAB_H // 2 - 2), '開催日', font=font(MEIB, 30),
           fill=(120, 112, 104, 255), anchor='mm')
    for k, iso in enumerate(ds):
        dt = datetime.strptime(iso, '%Y-%m-%d').date()
        on = iso in hit
        x = lab_w + gap + k * (bw + gap)
        h = TAB_H - 12 if on else TAB_H - 30
        col = (PREF_RED + (255,)) if on else (222, 218, 212, 255)
        tab = rounded((bw, h + 26), 18, col)
        im.alpha_composite(tab, (x, TAB_H - h))
        w = wk[dt.weekday()]
        t = '%d/%d(%s)' % (dt.month, dt.day, w)
        fg = (255, 255, 255, 255) if on else (146, 140, 134, 255)
        ImageDraw.Draw(im).text((x + bw // 2, TAB_H - h // 2 - 4), t,
                                font=font(MEIB, 34 if on else 28), fill=fg, anchor='mm')


FREE_ENTRY = re.compile(r'(?:入場|観覧|入館|参加|見学)\s*(?:は)?\s*無料')
YEN = re.compile(r'[0-9０-９][0-9０-９,，]*\s*円')


def paidbadge(ev):
    """有料/無料のバッジ。⚠**料金が分からないものは出さない**(推測でラベルを貼らない)

    ⚠「入場無料(クレーンゲームは1回100円)」を**金額の記載だけで有料と出していた**
      (2026-09-18に実機で発覚)。入場・観覧・参加が無料なら利用者にとっては入場無料なので、
      **「入場無料」を先に見る**。「入場料 大人300円」は当たらない(「入場無料」ではない)。
    """
    p = str(ev.get('price') or '')
    if FREE_ENTRY.search(p):
        return pill('入場無料', (31, 122, 90), 34, (24, 12))
    if YEN.search(p):
        return pill('有料', (232, 163, 61), 34, (26, 12))
    if ev.get('free'):
        return pill('入場無料', (31, 122, 90), 34, (24, 12))
    return None


# ★memo から落とす行 / 先頭のラベルだけ外す行【2026-09-18に実機で発覚】
#   「日程：9/19（土）」が memo に残り、**情報行の「日程」と二重**になっていた。
#   ⚠「内容：…」は**中身が説明そのもの**なので行を捨てず、ラベルだけ外す。
MEMO_KILL = re.compile(r'^\s*(?:日程|日時|時間|開催日|開催時間|場所|会場|料金|参加費|費用|'
                       r'対象|定員|申込|申し込み|予約|受付|協力|主催|共催|後援|協賛)\s*[:：]')
MEMO_LABEL = re.compile(r'^\s*(?:内容|詳細|概要|イベント内容|備考)\s*[:：]\s*')


def memo_src(ev):
    """memo に出す文の並び。⚠**優先順を間違えると意味のない箱になる**【2026-09-18】
    1回目は `detail` → `lead` の順にしていて、detail が無い回は
    **lead の先頭(=タイトルそのもの)が memo に出てタイトルの繰り返し**になっていた。
    `memo` は源が「説明文だけ」を抜いて入れたものなので**これを最優先**にする。"""
    for k in ('memo', 'detail'):
        v = []
        for x in (ev.get(k) or []):
            s = str(x).strip()
            if not s or MEMO_KILL.match(s):      # 情報行と重複する行は捨てる
                continue
            s = MEMO_LABEL.sub('', s).strip('　 「」')
            if len(s) >= 6:
                v.append(s)
        if v:
            return v
    lead = (ev.get('lead') or '').strip()
    t = (ev.get('title') or '').strip()
    # lead はタイトルを含むことが多いので、**タイトルを削ってから**使う
    if t and len(t) >= 4:
        lead = lead.replace(t, ' ').strip()
    lead = re.sub(r'\s{2,}', ' ', lead)
    return [lead] if len(lead) >= 10 else []


MEMO_F, MEMO_PITCH = 29, 38      # memo の本文フォントと行送り


def memo_lines(ev, w):
    """memo の本文を**折り返し済みの行**で返す。⚠中身が無ければ空"""
    src = memo_src(ev)
    if not src:
        return []
    d = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    fm = font(MEI, MEMO_F)
    out = []
    for ln in src:
        out += wrap(d, deemoji(str(ln)), fm, w - 150, 2)
    return out


def memo_h(lines):
    return 18 + max(1, len(lines)) * MEMO_PITCH + 16


def memobox(ev, w, lines):
    """memo。⚠**ポスターの下に全幅で敷く**【2026-09-25ユーザー指摘】。
       以前は右下に幅330〜430pxの縦長の箱を置いていたが、1行が2〜3行に
       折り返して読めなかった。全幅なら1行=全角30字まで入るので折り返さない。
       見出しは左端に小さく置く(上に1行取ると高さのぶんポスターが縮むため)"""
    if not lines:
        return None
    h = memo_h(lines)
    c = rounded((w, h), 20, (253, 243, 231, 255))
    cd = ImageDraw.Draw(c)
    cd.rounded_rectangle([0, 0, w - 1, h - 1], 20, outline=(238, 220, 192, 255), width=2)
    cd.text((26, 16), 'memo', font=font(ROUND, 30), fill=(154, 106, 31, 255))
    fm = font(MEI, MEMO_F)
    yy = 18
    for ln in lines:
        cd.text((132, yy), '・' + ln if not ln.startswith('・') else ln,
                font=fm, fill=(74, 66, 56, 255))
        yy += MEMO_PITCH
    return c


def card(ev, idx, extra=None, days=None, cur=None):
    ex = (extra or {}).get(ev.get('url'), {})
    for k, v in ex.items():
        if not k.startswith('_') and v:
            ev[k] = v
    dp = load_disp().get(ev.get('url')) or {}
    if dp.get('name'):
        ev['title'] = dp['name']
    if dp.get('venue'):
        ev['venue'] = dp['venue']
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    # ★日付タブ(上端)。渡されなかった回は従来どおりタブ無しで描く
    top = 0
    if days:
        # ⚠**そのイベントが開催される日を全部**渡す(1日しか塗らないと2日間開催が伝わらない)
        # そのイベントの会期に入る日を全部濃くする(2日間開催なら2つとも濃くなる)
        sp = ev.get('span') or [None, None]
        hit = [x for x in days if sp[0] and sp[0] <= x <= (sp[1] or sp[0])] or [cur]
        daytabs(im, d, days, cur, hit)
        top = TAB_H
    # 市区ピル + ★有料/無料バッジ
    city = ev.get('city') or (ev.get('venues') or [''])[0] or '福岡県'
    cp = pill(city[:12], PREF_RED, 32)
    shadow(im, cp, (64, top + 34))
    pb = paidbadge(ev)
    if pb:
        shadow(im, pb, (64 + cp.width + 14, top + 34))
    d.text((W_ - 64, top + 48), '%d' % idx, font=font(ROUND, 52),
           fill=(216, 210, 202), anchor='ra')
    # イベント名
    f = font(MEIB, 52)
    y = top + 126
    for ln in wrap(d, deemoji(ev['title']), f, W_ - 128, 3):
        d.text((64, y), ln, font=f, fill=INK); y += 66
    y += 18
    # ポスター(IP絡みは貼らない)
    ok = W.poster_ok(ev['title'], ev.get('lead'))
    # ⚠**ポスターの高さは情報行のぶんを引いて決める**。固定560pxだと、
    #   縦長ポスター + 行数が多いカードで情報行がCTAバーに押し出され、
    #   **一番大事な「検索」が消える**(2026-09-13に踏んだ)。
    #   行数は日程/時間/場所/料金/検索(+注意/駐車)で最大7
    nrow = 4 + sum(1 for k in ('time', 'note') if ev.get(k)) \
             + (1 if (ev.get('park') or ev.get('parking')) else 0)
    # ★memo枠を右下に置くので、**情報行は左列に寄せて幅を狭める**
    # ⚠**memo欄が狭いと1行が3行に折り返して読めない**【2026-09-25ユーザー指摘】。
    #   330pxだと全角12字で折り返していた。430pxにして1行=全角16字前後が入るようにする
    MEMO_W = W_ - 128
    # ⚠ポスターが無い回は下の「どんなイベント？」カードが同じ内容を大きく出すので
    #   **memo枠は出さない**(1枚に同じ4行が二重に出ていた・2026-09-18に実機で発覚)。
    #   ポスターを貼れるかは poster_ok と画像の有無で決まるので、ここでは仮に持ち、
    #   ポスターを実際に描いたあとで確定させる
    has_memo = bool(memo_src(ev))
    mlines = memo_lines(ev, MEMO_W) if has_memo else []
    # ★memo のぶんの高さを**先に取ってから**ポスターの大きさを決める。
    #   あとから足すと情報行がCTAバーに押し出される
    box_h = max(210, min(560, H_ - 200 - y - nrow * 54
                         - (memo_h(mlines) + 22 if has_memo else 0)))
    img = get_poster(ev.get('poster')) if ok else None
    if img:
        s = min((W_ - 200) / img.width, box_h / img.height)
        pw, ph = max(1, int(img.width * s)), max(1, int(img.height * s))
        ph_im = img.resize((pw, ph), Image.LANCZOS)          # 縮小のみ。トリミングしない
        frame = rounded((pw + 24, ph + 24), 18, (255, 255, 255, 255))
        frame.paste(ph_im, (12, 12))
        shadow(im, frame, ((W_ - pw - 24) // 2, y))
        y += ph + 30
        mb = memobox(ev, MEMO_W, mlines)
        if mb:
            shadow(im, mb, (64, y), blur=12, alpha=40, dy=4)
            y += mb.height + 22
    else:
        # ⚠**ポスターを貼れないぶんは情報量で補う**
        #   (2026-09-13ユーザー指摘「グレーだけどポスター載せてる人がいてライバルに負ける」)。
        #   ポスター画像を自分で読んで data/_イベント補足.json の detail に転記しておく。
        #   画像の再配布はしないが、そこに書かれている**情報は普通に載せてよい**
        # ★ここは「どんなイベント？」カード = **実質これが memo**。
        #   だから右下の memo 枠は出さない(同じ内容が1枚に二重に出ていた)
        has_memo = False
        det = [deemoji(str(x)) for x in
               ([x for x in (ev.get('detail') or []) if x] or memo_src(ev))]
        det = [x for x in det if x][:4]
        # ★★**文字カードを画像に近い引きにする**【2026-09-18ユーザー確定】
        #   「よそのSNSでは画像を使っているところもある。その場合に文章だと負けます。
        #     かといって文章だけだと読めば伝わるが、読む段階にいたらない」
        #   ⚠**代替の会場写真は今は使えない**(2026-09-18実測):
        #     IPで貼れない会場(イオンモール/大丸/美術館)は自前写真を1枚も持っておらず、
        #     施設公式の og:image はイオンモール全館で同一のロゴ画像だった。
        #   → **可愛いアイコン + 大きな文字**で戦う。⚠文字にIP名を書くのは権利上問題ない。
        ICO = 210 if not ok else 150
        rows_ = det or ['詳細は公式サイトでご確認ください']
        fbig = font(MEIB, 38)
        cw = W_ - 128
        tw = cw - ICO - 84
        lines = []
        for x in rows_:
            lines += wrap(ImageDraw.Draw(Image.new('RGB', (1, 1))), x, fbig, tw, 2)
        # ⚠アイコンの下に注記を置くぶんの高さを足す。足さないと
        #   注記が本文の行に重なって読めなくなる(2026-09-18に実機で発覚)
        h2 = max(ICO + (180 if not ok else 84), 92 + len(lines) * 52 + 40)
        c = rounded((cw, h2), 22, (246, 240, 232, 255))
        cd = ImageDraw.Draw(c)
        cd.rounded_rectangle([0, 0, cw - 1, h2 - 1], 22, outline=(232, 214, 198, 255), width=3)
        cd.text((34, 26), 'どんなイベント？', font=font(MEIB, 34), fill=PREF_RED + (255,))
        # 権利で貼れない回は**照れ顔アイコン**を置き、理由を小さく添える
        if not ok:
            ic = NOIMG.make(ICO, ICON_VARIANT)
            iy = 62
            c.alpha_composite(ic, (cw - ICO - 30, iy))
            # ⚠注記は**アイコンの真下に2行で**置く。1行だとカードの右端で切れた
            #   (2026-09-18に実機で発覚)。中央寄せの基準はアイコンの中心
            # ⚠⚠**「なぜ写真が無いのか」が分かる文にする**【2026-09-18ユーザー確定】
            #   「ニコちゃんマークが基本的にはいいとは思っているものの、
            #     なんで写真がないのかっていうところがそれではわからないので
            #     文章補足をしていただければいい」
            #   旧文「ポスターは/権利の都合で非掲載」では理由が伝わらなかったので、
            #   **キャラクターの権利であること**を明示し、色も薄すぎない灰にする
            icx = cw - ICO // 2 - 30
            for k, ln in enumerate(('キャラクターの権利が', 'あるため、ポスターは',
                                    'お見せできません')):
                cd.text((icx, iy + ICO + 10 + k * 28), ln,
                        font=font(MEI, 22), fill=(138, 118, 108, 255), anchor='ma')
        yy = 92
        for ln in lines[:6]:
            cd.text((34, yy), ln, font=fbig, fill=INK + (255,))
            yy += 52
        shadow(im, c, (64, y))
        y += h2 + 30
    # 情報行
    fi = font(MEI, 38)
    fb = font(MEIB, 38)
    rows = []
    sp = ev.get('span') or [None, None]
    #  ⚠絵文字(📅🕐📍🅿)は **Meiryo に字形が無く□の豆腐になる**(2026-09-13に踏んだ)。
    #    PILはカラー絵文字フォント(seguiemj)も綺麗に出ないので、**日本語のラベル**にする
    if sp[0]:
        a = datetime.strptime(sp[0], '%Y-%m-%d').date()
        b = datetime.strptime(sp[1], '%Y-%m-%d').date() if sp[1] else a
        wk = '月火水木金土日'
        # マップ登録(until のみ)は開始日を持たないので「◯/◯まで」と出す
        txt = ('〜%d/%d(%s)まで' % (b.month, b.day, wk[b.weekday()]) if ev.get('nostart') else
               '%d/%d(%s)' % (a.month, a.day, wk[a.weekday()]) if a == b else
               '%d/%d(%s)〜%d/%d(%s)' % (a.month, a.day, wk[a.weekday()],
                                         b.month, b.day, wk[b.weekday()]))
        # 「すぐ行ける版」は**残り日数**が行く理由になる。終了が2週間以内のものだけ足す
        left = (b - date.today()).days
        if 0 <= left <= 14:
            txt += '  あと%d日' % (left + 1)
        rows.append(('日程', txt))
    if ev.get('time'):
        rows.append(('時間', re.sub(r'\s+', ' ', ev['time'])[:30]))
    # ⚠「いこーよ」「県公式」は**集約サイト名**なので会場欄に出してはいけない(2026-09-13に踏んだ)。
    #   会場が取れていなければ市区で代える
    AGG = ('いこーよ', '県公式')
    ven = [v for v in (ev.get('venues') or []) if v and v not in AGG]
    # 場所は **venue(施設名)が主**。place(館内の場所)は施設名のあとに足す。
    # place だけを出すと「プラネタリウム・4階天体観測広場」のように**どこの施設か分からない**
    fac = ev.get('venue') or (ven[0] if ven else '') or ''
    pl = ' '.join([x for x in (fac, ev.get('place') or '') if x]).strip()
    if len(pl) > 22:            # 入り切らないなら館内の場所を捨てて**施設名を残す**
        pl = fac or pl
    pl = pl or ev.get('city') or ''
    if pl:
        rows.append(('場所', pl[:24]))
    rows.append(('料金', '無料' if ev.get('free') else (ev.get('price') or '公式サイトで確認')))
    rows.append(('検索', search_word(ev)[:26]))
    if ev.get('note'):                      # 雨天中止・予約制など**行く前に効く注意**
        rows.append(('注意', ev['note'][:24]))
    if ev.get('park') or ev.get('parking'):
        rows.append(('駐車', (ev.get('park') or ev.get('parking'))[:22]))
    # ⚠**情報行は6行しか入らない**。7行にするとCTAピルと出典に重なる(2026-09-13に踏んだ)。
    #   並びは優先順なので、溢れるときに落ちるのは「駐車」。
    #   **「検索」は絶対に落とさない**(「どこを見ればいいか分からない」への回答そのもの)
    fl = font(MEIB, 27)
    # ★**右下に memo、左下に情報行**の2列にする【2026-09-17ユーザー要望】
    #   memo がある回は情報行の幅が狭くなるので、フォントも小さくする
    lab_w, lab_x, txt_x = 92, 68, 176
    txt_w = W_ - 64 - txt_x
    # ⚠**CTAバー(y=H_-156)までに入る行数だけ出す**。固定の上限だと、
    #   ポスターの高さで残り幅が変わるため6行目がCTAバーに上書きされて消える(2026-09-13に踏んだ)
    rh = 54
    fit = max(3, (H_ - 166 - y) // rh)
    if len(rows) > fit:
        print('    ※%s: 情報行が%d行入らず省いた(%s)'
              % (ev.get('title', '')[:16], len(rows) - fit,
                 '/'.join(r[0] for r in rows[fit:])))
    for ic, tx in rows[:fit]:
        lab = rounded((lab_w, 42), 10, (238, 230, 226, 255))
        ImageDraw.Draw(lab).text((lab_w // 2, 21), ic, font=fl,
                                 fill=PREF_RED + (255,), anchor='mm')
        im.alpha_composite(lab, (lab_x, y - 1))
        # ⚠狭い列に入り切らない値は**1行に収まる長さで切る**(はみ出して memo に重なるため)
        s = deemoji(tx)
        while s and d.textlength(s, font=fb) > txt_w:
            s = s[:-1]
        if s != deemoji(tx) and len(s) > 2:
            s = s[:-1] + '…'
        d.text((txt_x, y), s, font=fb, fill=INK)
        y += rh
    # 出典は**会場/主催者**を優先する。いこーよは集約サイトなので「◯◯(いこーよ掲載)」と書く
    if ven:
        srcname = ven[0]
    elif ev.get('place'):
        srcname = '%s(%s掲載)' % (ev['place'], ev.get('src', ''))
    else:
        srcname = '%s(%s掲載)' % (ev.get('city', '福岡県'), ev.get('src', ''))
    cta = rounded((W_ - 160, 66), 16, (246, 238, 236, 255))
    ImageDraw.Draw(cta).text(((W_ - 160) // 2, 33), 'リンクはキャプションに貼ってます',
                             font=font(MEIB, 32), fill=PREF_RED + (255,), anchor='mm')
    im.alpha_composite(cta, (80, H_ - 156))
    d.text((W_ // 2, H_ - 58), '情報・画像出典: %s' % srcname[:38],
           font=font(MEI, 28), fill=(160, 154, 148), anchor='ma')
    return im.convert('RGB')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=12)
    ap.add_argument('--title', default='')
    ap.add_argument('--json', default=SRC)
    ap.add_argument('--hook', default='', help='表紙の大見出し(既定「まだ間に合う」)')
    # ⚠**既定で写真を敷く**。--cover を渡し忘れると表紙が上2/3空白のクリーム一色になり、
    #   1枚目のインパクトが消える(2026-09-13に渡し忘れてユーザーに指摘された)
    ap.add_argument('--cover', default=COVER_DEFAULT,
                    help='表紙の背景写真。上から4:5で切るので人混みは下に置く。空文字で写真なし')
    ap.add_argument('--tail', default='福岡の子連れおでかけ %d選',
                    help='表紙の3行目。%%d が件数に置き換わる。**「子連れ」を必ず入れる**')
    ap.add_argument('--cta', default='',
                    help='表紙の最下段のピル。**リール用は「最後まで見てね →」**(動画はスワイプしない)')
    ap.add_argument('--out', default='', help='出力先。既定は data/carousel_<開始日>/')
    ap.add_argument('--no-tabs', action='store_true',
                    help='日付タブを出さない(1イベント1日の単発回など)')
    # ★収集の窓が広いときに、投稿1本ぶんの期間だけ切り出す
    ap.add_argument('--from', dest='f', default='', help='この日から(既定は候補JSONのfrom)')
    ap.add_argument('--to', dest='t', default='', help='この日まで(既定は候補JSONのto)')
    # ★IPで貼れない回のアイコン。frame=照れ顔+©バッジ / camera=カメラに斜線
    ap.add_argument('--icon', default='frame', choices=['frame', 'camera'],
                    help='権利で貼れない回のアイコン(既定 frame)')
    a = ap.parse_args()
    D = json.load(io.open(a.json, encoding='utf-8'))
    # ★**収集の窓とカルーセルの窓は別物**【2026-09-18】
    #   イベント一覧(マップ)のために収集は広く取る(48日など)ので、そのままだと
    #   日付タブが出ない(2〜8日のときだけ出す仕様)。投稿1本ぶんの期間を切り出せるようにする。
    f = datetime.strptime(a.f or D['from'], '%Y-%m-%d').date()
    t = datetime.strptime(a.t or D['to'], '%Y-%m-%d').date()
    fs, tsv = f.isoformat(), t.isoformat()

    def inwin(e):
        sp = e.get('span') or [None, None]
        return bool(sp[0]) and sp[0] <= tsv and (sp[1] or sp[0]) >= fs

    # week_events が選抜した順(源のラウンドロビン後)を優先する。
    # 無ければスコア順の先頭から取る
    if D.get('selected'):
        by = {e['url']: e for e in D['events']}
        evs = [by[u] for u in D['selected'] if u in by]
    else:
        evs = list(D['events'])
    if a.f or a.t:
        # ⚠絞った窓に入るものだけにする。選抜が足りなくなったら
        #   **スコア順の全件から補充する**(枠が空くほうが害が大きい)
        evs = [e for e in evs if inwin(e)]
        if len(evs) < a.n:
            have = {e['url'] for e in evs}
            evs += [e for e in D['events']
                    if e['url'] not in have and inwin(e)][:a.n - len(evs)]
        print('期間で絞り込み: %s〜%s → %d件' % (fs, tsv, len(evs)), file=sys.stderr)
    evs = evs[:a.n]
    # ⚠**選ばれた回にメモが入っているかを毎回ここで点検する**【2026-09-25】。
    #   同じイベントが会場違い・日程違いで複数URLあるため、書いたつもりのメモが
    #   別URLに入っていて、カードには元の告知文がそのまま出ていた(久留米/飯塚の
    #   リトルプラネット、キャナルお目覚めフェスで実際に踏んだ)。
    #   memo は data/_イベント補足.json の detail に**手で**書く。無ければ名前を出す。
    _ext = load_extra()
    _nomemo = [e['title'] for e in evs[:a.n]
               if not (_ext.get(e.get('url')) or {}).get('detail')]
    if _nomemo:
        print('※memo(detail)を書いていないイベント %d件 ← _イベント補足.json に足すこと:'
              % len(_nomemo))
        for x in _nomemo:
            print('   -', x)
    wk = '月火水木金土日'
    sub = a.title or (('%d月%d日(%s) の' % (f.month, f.day, wk[f.weekday()])) if f == t else
                      ('%d/%d(%s)〜%d/%d(%s) の' % (f.month, f.day, wk[f.weekday()],
                                                   t.month, t.day, wk[t.weekday()])))
    if not a.title:
        sub += 'おでかけイベント'
    out = a.out or os.path.join(HERE, '..', 'data', 'carousel_%s' % f.isoformat())
    os.makedirs(out, exist_ok=True)
    global ICON_VARIANT
    ICON_VARIANT = a.icon
    extra = load_extra()
    # ★**県バッジは動画サムネと同じ大きさにする**【2026-09-24ユーザー指示・2回目】。
    #   小さいピルだと1枚目で「福岡の情報」と伝わらない。thumbs_build のバッジを借りる
    badge = None
    try:
        sys.path.insert(0, os.path.join(os.path.expanduser('~'),
                                        '.claude', 'skills', 'short-video', 'assets'))
        import thumbs_build as TB
        bw, bh = TB.LAYOUT['tiktok'][1][2], TB.LAYOUT['tiktok'][1][3]
        badge = TB.make_badge(bw, bh, '福岡', TB.badge_color('福岡'))
    except Exception as ex:
        print('※県バッジを借りられなかったので小さいピルで出す: %s' % type(ex).__name__)
    pages = [('01_表紙', cover(sub, len(evs), len(evs), a.hook or None, a.cover or None,
                              a.tail, a.cta or None, badge_img=badge))]
    # ★日付タブに出す日の並び【2026-09-17ユーザー要望】
    #   対象期間の全日を並べる。⚠**8日を超える回はタブを出さない**
    #   (細くなって読めず、かえって見づらくなる。参考アカウントも5日だった)
    alld = [(f + timedelta(days=i)).isoformat() for i in range((t - f).days + 1)]
    use_tabs = not a.no_tabs and 2 <= len(alld) <= 8
    if not use_tabs and not a.no_tabs:
        print('※対象期間が%d日なので日付タブは出さない(2〜8日のときだけ出す)' % len(alld))
    for i, ev in enumerate(evs, 1):
        # そのイベントの「この回で見せる日」= 対象期間に入る最初の日
        sp = ev.get('span') or [None, None]
        cur = next((x for x in alld if sp[0] and sp[0] <= x <= (sp[1] or sp[0])), None)
        pages.append(('%02d_%s' % (i + 1, re.sub(r'[^\w一-龥ぁ-んァ-ヶー]', '', ev['title'])[:16]),
                      card(ev, i, extra, alld if use_tabs else None, cur)))
    pages.append(('%02d_締め' % (len(evs) + 2), closing()))
    for name, im in pages:
        p = os.path.join(out, name + '.jpg')
        im.save(p, quality=92)
    print('%d枚 → %s' % (len(pages), os.path.normpath(out)))
    ng = [e['title'] for e in evs if not W.poster_ok(e['title'], e.get('lead'))]
    if ng:
        print('※IP絡みでポスターを貼らなかったもの %d件:' % len(ng))
        for x in ng:
            print('   -', x[:60])


if __name__ == '__main__':
    main()
