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
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import week_events as W

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


def cover(sub, n, total, hook=None, photo=None, tail=None):
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
    shadow(im, pill('福岡', PREF_RED, 40), (72, 86))
    hook = hook or 'まだ間に合う'
    y = H_ - 500
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
    pl = pill('スワイプして見てね →', PREF_RED, 38)
    shadow(im, pl, ((W_ - pl.width) // 2, y))
    return im.convert('RGB')



MAPCARD = r'C:\Users\totor\Dropbox\ショート動画用\5.共通素材\マップ操作_静止カード.png'


def closing():
    """締め。**動画で使っている枠付きカードの実物を貼ってマップを見せる**
    【2026-09-13ユーザー確定「動画で使ってるカードでサンプル表示しよう」】
    素材は 5.共通素材/マップ操作_枠のみ_4.4秒.mp4 の3.3秒を、
    ぼけていない領域(x231-848 / y241-1325 = 617x1084)で切り出して静止画にしたもの。
    5.共通素材/マップ操作_静止カード.png として保存済み"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((W_ // 2, 54), '気になったイベントは「検索」の言葉で調べられます',
           font=font(MEI, 32), fill=SUB + (255,), anchor='ma')
    d.text((W_ // 2, 110), '行った店は全部', font=font(MEIB, 50), fill=INK + (255,), anchor='ma')
    d.text((W_ // 2, 172), 'マップにまとめてます', font=font(ROUND, 76),
           fill=PREF_RED + (255,), anchor='ma')
    y = 282
    if os.path.exists(MAPCARD):
        c = Image.open(MAPCARD).convert('RGB')
        ch = 810
        cw = round(c.width * ch / c.height)
        card = rounded((cw + 20, ch + 20), 20, (255, 255, 255, 255))
        card.paste(c.resize((cw, ch), Image.LANCZOS), (10, 10))
        left = (W_ - cw - 20) // 2
        shadow(im, card, (left, y), blur=22, alpha=70, dy=8)
        # 両脇が寂しいので「何ができるか」をピルで出す
        for lb, dy in (('子供椅子で絞れる', 120), ('おむつ替えで絞れる', 330),
                       ('期間限定も出る', 540)):
            t = pill(lb, (96, 90, 86), 28)
            im.alpha_composite(t, (max(8, left - t.width - 16), y + dy))
        y += ch + 46
    pl = pill('プロフィールのリンクから見れます', PREF_RED, 38)
    shadow(im, pl, ((W_ - pl.width) // 2, y))
    d.text((W_ // 2, H_ - 52), '保存しておくと行くときに使えます', font=font(MEI, 34),
           fill=SUB + (255,), anchor='ma')
    return im.convert('RGB')


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
    ven = [v for v in (ev.get('venues') or []) if v and v not in AGG_NAMES]
    place = ev.get('place') or (ven[0] if ven else '') or ev.get('city') or ''
    place = re.sub(r'^福岡県', '', place)
    return ('%s %s' % (place, t)).strip() if place and place not in t else t


def card(ev, idx, extra=None):
    ex = (extra or {}).get(ev.get('url'), {})
    for k, v in ex.items():
        if not k.startswith('_') and v:
            ev[k] = v
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    # 市区ピル
    city = ev.get('city') or (ev.get('venues') or [''])[0] or '福岡県'
    shadow(im, pill(city[:12], PREF_RED, 32), (64, 60))
    d.text((W_ - 64, 74), '%d' % idx, font=font(ROUND, 52), fill=(216, 210, 202), anchor='ra')
    # イベント名
    f = font(MEIB, 52)
    y = 152
    for ln in wrap(d, ev['title'], f, W_ - 128, 3):
        d.text((64, y), ln, font=f, fill=INK); y += 66
    y += 18
    # ポスター(IP絡みは貼らない)
    ok = W.poster_ok(ev['title'], ev.get('lead'))
    box_h = 560
    img = get_poster(ev.get('poster')) if ok else None
    if img:
        s = min((W_ - 200) / img.width, box_h / img.height)
        pw, ph = max(1, int(img.width * s)), max(1, int(img.height * s))
        ph_im = img.resize((pw, ph), Image.LANCZOS)          # 縮小のみ。トリミングしない
        frame = rounded((pw + 24, ph + 24), 18, (255, 255, 255, 255))
        frame.paste(ph_im, (12, 12))
        shadow(im, frame, ((W_ - pw - 24) // 2, y))
        y += ph + 44
    else:
        # ⚠**ポスターを貼れないぶんは情報量で補う**
        #   (2026-09-13ユーザー指摘「グレーだけどポスター載せてる人がいてライバルに負ける」)。
        #   ポスター画像を自分で読んで data/_イベント補足.json の detail に転記しておく。
        #   画像の再配布はしないが、そこに書かれている**情報は普通に載せてよい**
        det = [x for x in (ev.get('detail') or []) if x]
        h2 = 104 + (len(det) * 56 if det else 56)
        c = rounded((W_ - 128, h2), 22, (243, 237, 229, 255))
        cd = ImageDraw.Draw(c)
        cd.text((36, 28), 'どんなイベント？', font=font(MEIB, 36), fill=PREF_RED + (255,))
        if not ok:
            cd.text((W_ - 128 - 32, 34), 'キャラクター画像は権利の都合で非掲載',
                    font=font(MEI, 23), fill=(170, 162, 154, 255), anchor='ra')
        yy = 88
        if det:
            for ln in det[:5]:
                cd.text((36, yy), ln if ln.startswith('※') else ('・' + ln),
                        font=font(MEI, 31), fill=INK + (255,)); yy += 56
        else:
            cd.text((36, yy), '詳細は公式サイトでご確認ください',
                    font=font(MEI, 31), fill=SUB + (255,))
        shadow(im, c, (64, y))
        y += h2 + 34
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
    pl = ev.get('place') or (ven[0] if ven else '') or ev.get('city') or ''
    if pl:
        rows.append(('場所', pl[:26]))
    rows.append(('料金', '無料' if ev.get('free') else (ev.get('price') or '公式サイトで確認')))
    if ev.get('park'):
        rows.append(('駐車', ev['park'][:22]))
    rows.append(('検索', search_word(ev)[:26]))
    fl = font(MEIB, 30)
    for ic, tx in rows[:6]:
        lab = rounded((92, 44), 10, (238, 230, 226, 255))
        ImageDraw.Draw(lab).text((46, 22), ic, font=fl, fill=PREF_RED + (255,), anchor='mm')
        im.alpha_composite(lab, (68, y - 2))
        d.text((176, y), tx, font=fb, fill=INK); y += 58
    # 一言 + 出典
    # ⚠リードがCTAバー(y=H_-156)に潜り込んで文字が切れていた(2026-09-13に踏んだ)。
    #   入る行数だけ出す
    if ev.get('lead'):
        y += 10
        room = max(0, (H_ - 176 - y) // 46)
        for ln in wrap(d, ev['lead'], font(MEI, 34), W_ - 140, min(2, room)):
            d.text((70, y), ln, font=font(MEI, 34), fill=SUB); y += 46
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
    ap.add_argument('--cover', default='', help='表紙の背景写真。上から4:5で切るので人混みは下に置く')
    ap.add_argument('--tail', default='福岡の子連れおでかけ %d選',
                    help='表紙の3行目。%%d が件数に置き換わる。**「子連れ」を必ず入れる**')
    a = ap.parse_args()
    D = json.load(io.open(a.json, encoding='utf-8'))
    # week_events が選抜した順(源のラウンドロビン後)を優先する。
    # 無ければスコア順の先頭から取る
    if D.get('selected'):
        by = {e['url']: e for e in D['events']}
        evs = [by[u] for u in D['selected'] if u in by][:a.n]
    else:
        evs = D['events'][:a.n]
    f = datetime.strptime(D['from'], '%Y-%m-%d').date()
    t = datetime.strptime(D['to'], '%Y-%m-%d').date()
    wk = '月火水木金土日'
    sub = a.title or (('%d月%d日(%s) の' % (f.month, f.day, wk[f.weekday()])) if f == t else
                      ('%d/%d(%s)〜%d/%d(%s) の' % (f.month, f.day, wk[f.weekday()],
                                                   t.month, t.day, wk[t.weekday()])))
    if not a.title:
        sub += 'おでかけイベント'
    out = os.path.join(HERE, '..', 'data', 'carousel_%s' % D['from'])
    os.makedirs(out, exist_ok=True)
    extra = load_extra()
    pages = [('01_表紙', cover(sub, len(evs), len(evs), a.hook or None, a.cover or None, a.tail))]
    for i, ev in enumerate(evs, 1):
        pages.append(('%02d_%s' % (i + 1, re.sub(r'[^\w一-龥ぁ-んァ-ヶー]', '', ev['title'])[:16]),
                      card(ev, i, extra)))
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
