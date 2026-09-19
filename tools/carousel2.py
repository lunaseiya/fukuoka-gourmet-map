# -*- coding: utf-8 -*-
"""シルバーウィーク版カルーセル: **1枚に2イベント + 上部にエリアタブ**【2026-09-19】

ユーザー要望:
  「こないだ見せたタブが上にあり、各イベントごとにメモとデータを補足する形で、
    ２イベント1枚ずつのチラシをセットで合計20イベントくらいに」
  「日付で分ける場合はタブで二日あれば二日タブをハイライトみたいな形になるかと思います。
    でも２枚ずつ表示してるから組み合わせが難しそうですよね。。
    であれば最後から2番目に早見表を置いていきますか。シルバーウィーク計画に役立ててね。」
  「最後のマップ案内ではその他もイベント多数あり、詳しくはプロフィール欄をご覧ください」

■ なぜ日付タブではなくエリアタブにしたか
  ・会期が連休全期間のイベントが**4件**ある(万代/縁日パラダイス/陶磁器フェスタ/こどもの視展)。
    日付で束ねると同じイベントが何枚にも出て、20件が10枚に収まらない。
  ・日付タブは全期間のイベントをどのタブに置くか決まらない。エリアなら必ず1つに属する。
  ・「遠いところは行かん」(2026-09-18ユーザー)に直接効く。
  → 日付は**カード内に赤字で大きく**入れ、**最後から2番目に早見表**を置いて補う。

■ 構成(13枚)
  01 表紙 / 02〜11 イベントカード(2件/枚) / 12 早見表 / 13 締め(マップ案内)

⚠既存 event_carousel.py の部品(pill/wrap/shadow/memo_src/get_poster 等)を import して使う。
  同じロジックを二重に持たない。
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont, ImageOps
import event_carousel as EC
from event_carousel import (font, rounded, shadow, wrap, deemoji, pill, get_poster,
                            memo_src, load_extra, load_disp, ROUND, MEI, MEIB,
                            BG, INK, SUB, W_, H_, FREE_ENTRY, YEN)

HERE = os.path.dirname(os.path.abspath(__file__))

# ── エリアの区分(events.html と同じ) ───────────────────────
AROUND = ['春日市', '大野城市', '太宰府市', '筑紫野市', '那珂川市', '古賀市', '福津市',
          '宗像市', '糸島市', '宇美町', '篠栗町', '志免町', '須惠町', '新宮町', '久山町', '粕屋町']
KITA = ['中間市', '宮若市', '直方市', '飯塚市', '田川市', '嘉麻市', '行橋市', '豊前市',
        '芦屋町', '水巻町', '岡垣町', '遠賀町', '小竹町', '鞍手町', '桂川町', '香春町',
        '添田町', '糸田町', '川崎町', '大任町', '赤村', '福智町', '苅田町', 'みやこ町',
        '吉富町', '上毛町', '築上町']
CHIKUGO = ['久留米市', '大牟田市', '柳川市', '八女市', '筑後市', '大川市', '小郡市',
           'うきは市', '朝倉市', 'みやま市', '大刀洗町', '大木町', '広川町', '筑前町', '東峰村']
# (ラベル, 判定, 帯の色) ― 参考アカウントのようにエリアごとに色を変える
AREAS = [
    ('福岡市',      lambda c: c.startswith('福岡市'),                    (232, 150, 160)),
    ('市の周辺',     lambda c: any(x in c for x in AROUND),              (140, 196, 214)),
    ('北九州・筑豊',  lambda c: c.startswith('北九州市') or any(x in c for x in KITA),
                                                                        (232, 196, 108)),
    ('筑後',        lambda c: any(x in c for x in CHIKUGO),             (154, 200, 130)),
]
WD = '月火水木金土日'


def area_of(city):
    c = city or ''
    for lab, test, _ in AREAS:
        if test(c):
            return lab
    return '福岡市'


def tabs(im, cur):
    """上部のエリアタブ。**現在のエリアを前面に出す**(参考アカウントと同じ見せ方)"""
    d = ImageDraw.Draw(im)
    n = len(AREAS)
    gap = 8
    w = (W_ - gap * (n + 1)) // n
    H = 96
    for i, (lab, _, col) in enumerate(AREAS):
        on = (lab == cur)
        x = gap + i * (w + gap)
        y = 0 if on else 14
        h = H if on else H - 14
        t = rounded((w, h + 30), 26, col + (255 if on else 190,))
        im.alpha_composite(t, (x, y))
        f = font(MEIB, 38 if on else 33)
        dd = ImageDraw.Draw(im)
        dd.text((x + w // 2, y + h // 2 + (2 if on else 0)), lab, font=f,
                fill=(255, 255, 255, 255) if on else (255, 255, 255, 215), anchor='mm')
    return H + 14


SW_FROM, SW_TO = '2026-09-19', '2026-09-23'


def sw_days(ev):
    """連休(9/19〜23)のうち開催している日を返す。
    ⚠**候補JSONの `days` は「日数」(int)**で、日付のリストは `days_list`。
      間違えると 'int' object is not iterable で落ちる(2026-09-19に踏んだ)。
      `days_list` が無いものは `span` から日付を展開する。"""
    import datetime
    ds = ev.get('days_list')
    if not ds:
        sp = ev.get('span') or []
        if not sp or not sp[0]:
            return []
        a = str(sp[0])[:10]
        b = str(sp[1] or sp[0])[:10]
        try:
            d0 = datetime.date(*map(int, a.split('-')))
            d1 = datetime.date(*map(int, b.split('-')))
        except Exception:
            return []
        ds = [(d0 + datetime.timedelta(days=i)).isoformat()
              for i in range((d1 - d0).days + 1)]
    return sorted(set(str(x)[:10] for x in ds if SW_FROM <= str(x)[:10] <= SW_TO))


def daylabel(ev):
    """連休のどこで行けるかを1行で。**ここが一番大事なので赤字で大きく出す**"""
    ds = sw_days(ev)
    if not ds:
        return '期間中'
    ds = sorted(set(ds))
    if len(ds) >= 5:
        return '連休ずっと'
    def f(x):
        import datetime
        dt = datetime.date(*map(int, x.split('-')))
        return '%d/%d(%s)' % (dt.month, dt.day, WD[dt.weekday()])
    if len(ds) == 1:
        return f(ds[0]) + 'だけ'
    if len(ds) == 2:
        return f(ds[0]) + '・' + f(ds[1])
    return f(ds[0]) + '〜' + f(ds[-1])


def feetext(ev, ex=None):
    # ⚠**補足ファイル(_イベント補足.json)の price を先に見る**。
    #   源が price を持たない回が7件あり、情報行が空になっていた(2026-09-19)
    p = str((ex or {}).get('price') or ev.get('price') or '')
    if FREE_ENTRY.search(p) or (ev.get('free') and not YEN.search(p)):
        return '入場無料', (206, 57, 52)
    if p:
        return re.sub(r'\s+', ' ', p).strip(), INK
    return '', INK


def slot(ev, col, extra):
    """イベント1件ぶんの枠(1080×612)。帯 + ポスター + 情報3行 + memo"""
    SW, SH = W_, 612
    im = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ex = (extra or {}).get(ev.get('url'), {})
    disp = load_disp().get(ev.get('url'), {})
    title = deemoji(disp.get('name') or ev.get('title') or '')
    venue = disp.get('venue') or ev.get('venueName') or ev.get('venue') or ''

    # ① 帯: 📍市区ピル + イベント名(参考アカウントの見せ方)
    band = rounded((SW - 40, 84), 18, col + (255,))
    im.alpha_composite(band, (20, 0))
    bd = ImageDraw.Draw(im)
    # ⚠**pill() は文字色が白固定**なので、白い市区ピルに使うと文字が消える
    #   (2026-09-19の試作で「久山町」が白抜けした)。ここは自前で描く
    city = (ev.get('city') or '').replace('福岡市', '').replace('北九州市', '') or '福岡'
    fc = font(MEIB, 30)
    cw = int(bd.textlength(city, font=fc)) + 36
    cpill = rounded((cw, 46), 23, (255, 255, 255, 255))
    im.alpha_composite(cpill, (36, 19))
    bd.text((36 + cw // 2, 42), city, font=fc, fill=col + (255,), anchor='mm')
    tx = 36 + cw + 16
    ft = font(MEIB, 46)
    tw = SW - 40 - tx - 24
    lines = wrap(bd, title, ft, tw, 1)
    bd.text((tx, 42), lines[0] if lines else title, font=ft,
            fill=(255, 255, 255, 255), anchor='lm')

    # ② ポスター(左) 300×400
    PW, PH = 300, 400
    py = 104
    # ★**手元の写真を優先する**(`img_local`)【2026-09-19】
    #   源が告知画像を持っていない回は、ユーザーが現地で撮ったポスター写真を使う。
    #   万代の秋まつり大縁日がこれ(他アカウントの画像ではなく自分で撮ったものなので使える)
    pim = None
    loc = ex.get('img_local')
    if loc:
        cand = loc if os.path.isabs(loc) else os.path.join(HERE, '..', loc)
        if os.path.exists(cand):
            pim = Image.open(cand).convert('RGB')
    if pim is None and ev.get('poster'):
        # ⚠**IPコラボのポスターは貼らない**(方針)。poster_ok を通さずに
        #   get_poster していて、カービィのポスターを貼ってしまっていた(2026-09-19)
        import week_events as _W0
        if _W0.poster_ok(ev.get('title'), ev.get('lead')):
            pim = get_poster(ev['poster'])
    if pim is not None:
        box = ImageOps.contain(pim, (PW, PH), Image.LANCZOS)
        ph = rounded((box.width, box.height), 14, (255, 255, 255, 255))
        ph.paste(box.convert('RGB'), (0, 0))
        ph.putalpha(rounded((box.width, box.height), 14, (255, 255, 255, 255)).split()[-1])
        shadow(im, ph, (30, py + (PH - box.height) // 2), blur=12, alpha=44, dy=4)
    else:
        # ポスターが無い/貼れない回は照れ顔アイコン(events.html と同じ考え方)
        ic = rounded((PW, PW), 40, (247, 240, 233, 255))
        icd = ImageDraw.Draw(ic)
        icd.rounded_rectangle([2, 2, PW - 3, PW - 3], 40, outline=(226, 190, 178, 255), width=6)
        for cx in (PW * 0.34, PW * 0.66):
            icd.arc([cx - PW * .15, PW * .34, cx + PW * .15, PW * .34 + PW * .22],
                    start=200, end=340, fill=(92, 74, 66, 255), width=8)
        icd.arc([PW * .40, PW * .50, PW * .60, PW * .64], start=20, end=160,
                fill=(92, 74, 66, 255), width=8)
        shadow(im, ic, (30, py), blur=12, alpha=40, dy=4)
        icd2 = ImageDraw.Draw(im)
        # ⚠**理由で文言を分ける**。万代のようにIPではなく**源が画像を持っていない**回に
        #   「キャラクターの権利が…」と出すのは嘘になる(2026-09-19の試作で発覚)
        import week_events as _W
        if ev.get('poster') and not _W.poster_ok(ev.get('title'), ev.get('lead')):
            note = ('キャラクターの権利が', 'あるため、ポスターは', 'お見せできません')
        else:
            note = ('告知の画像が', '公開されていません', '(詳細は主催ページで)')
        for k, ln in enumerate(note):
            icd2.text((30 + PW // 2, py + PW + 12 + k * 26), ln, font=font(MEI, 21),
                      fill=(168, 150, 140, 255), anchor='ma')

    # ③ 右側: 日付(赤で大きく) → 会場 → 料金 → memo
    rx = 30 + PW + 26
    rw = SW - rx - 30
    y = py + 2
    dl = daylabel(ev)
    d.text((rx, y), dl, font=font(ROUND, 52), fill=(206, 57, 52, 255))
    y += 66
    if venue:
        for ln in wrap(d, deemoji(str(venue)), font(MEIB, 30), rw, 2):
            d.text((rx, y), ln, font=font(MEIB, 30), fill=INK + (255,))
            y += 38
    ft2, fc2 = feetext(ev, ex)
    if ft2:
        for ln in wrap(d, ft2, font(MEIB, 30), rw, 2):
            d.text((rx, y), ln, font=font(MEIB, 30), fill=fc2 + (255,))
            y += 38
        y += 6
    tm = ex.get('time') or ev.get('time')
    if tm:
        for ln in wrap(d, deemoji(str(tm)), font(MEI, 27), rw, 2):
            d.text((rx, y), ln, font=font(MEI, 27), fill=SUB + (255,))
            y += 34
    # memo(何をするか)。⚠**参加動機にあたる一番大事な部分**なので必ず出す
    mh = SH - y - 16
    if mh >= 96:
        ev2 = dict(ev)
        for k in ('memo', 'detail', 'lead'):
            if ex.get(k) and not ev2.get(k):
                ev2[k] = ex[k]
        if ex.get('detail'):
            ev2['detail'] = ex['detail']
        # ⚠memo の1項目が長いと枠内で「…」に切れて意味が通らなくなる
        #   (試作で「300円の支払いで縁…」になった)。**句点/読点で切って詰める**
        src = memo_src(ev2)
        fixed = []
        for s in src:
            s = str(s).strip()
            while len(s) > 42:
                cut = max(s.rfind('。', 0, 42), s.rfind('、', 0, 42), s.rfind(')', 0, 42))
                if cut < 12:
                    cut = 42
                fixed.append(s[:cut + 1].rstrip('、。'))
                s = s[cut + 1:]
            if len(s) >= 6:
                fixed.append(s)
        ev2['memo'] = fixed[:5]
        ev2.pop('detail', None)
        ev2.pop('lead', None)
        mb = EC.memobox(ev2, (rw, mh))
        if mb is not None:
            im.alpha_composite(mb, (rx, y))
    return im


def card2(pair, cur, extra):
    """1枚に2イベント"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    top = tabs(im, cur)
    y = top + 10
    for ev in pair:
        col = next(c for l, t, c in AREAS if l == cur)
        im.alpha_composite(slot(ev, col, extra), (0, y))
        y += 624
    return im
