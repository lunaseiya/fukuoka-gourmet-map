# -*- coding: utf-8 -*-
"""**連休の日別まとめ**カルーセルを作る(インスタ/TikTok用 1080x1350)。

【なぜ別スクリプトにしたか・2026-09-16ユーザー確定】
  既存の `event_carousel.py` は **1枚=1イベント**の「◯◯選」型。
  連休(シルバーウィーク等)は「**どの日に何があるか**」が知りたい情報なので、
  ユーザーから「日付ごとにオススメ作ってくれるの、すごい便利」と評価された
  **1枚=1日**の型を別に用意する。表紙・締め・フォント・部品は event_carousel から借りる。

【⚠キッズモデルのように複数日あるものをどう切り分けるか・ユーザーの質問への答え】
  「キッズモデルって20日もありますよね？そういうのはどう切り分けようかな」
  → **開催日数で3層に分ける**。予定は「日付が動かせないもの」から埋めるのが効率的なので:
     ① この日だけ(1日開催)      … その日のカードに**橙**で大きく出す。最優先
     ② 連休のうち2〜3日          … その日のカードに**緑**で出し、「20日も」と併記する
     ③ 連休中ずっと(4〜5日)      … 日別には出さず、**専用の1枚**にまとめる
  こうすると同じイベントが5枚に重複せず、かつ取りこぼしもない。

使い方:
    python tools/event_daycards.py --from 2026-09-19 --to 2026-09-23 --out data/carousel_sw
"""
import argparse, io, json, os, re, sys
from datetime import date, timedelta
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import event_carousel as C
import week_events as W          # poster_ok(IPコラボのポスター可否判定)を借りる
# ★**県バッジは動画サムネと同じものを使う**【2026-09-16ユーザー指摘
#   「福岡アイコンちっさすぎるので、サムネと同サイズにしましょう」】
#   thumbs_build.py の make_badge(白枠→座布団→白抜きの丸ゴシック極太の3層)を借りる。
#   1080x1350 は thumbs_build の 'tiktok' と同寸なので、実測値 **271x166 @ (45,45)** を使う
sys.path.insert(0, os.path.join(os.path.expanduser('~'), '.claude', 'skills',
                                'short-video', 'assets'))
import thumbs_build as TB
BADGE_W, BADGE_H = 271, 166

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
EXTRA = os.path.join(HERE, '..', 'data', '_イベント補足.json')
W_, H_ = C.W_, C.H_
BG, INK, SUB, RED = C.BG, C.INK, C.SUB, C.PREF_RED
HOT = (194, 65, 12)          # 「この日だけ」の橙(秋)
GRN = (15, 110, 92)          # 「2〜3日」の緑
WD = {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
# 祝日名。⚠**推測で埋めない**。分かっているものだけ書く
HOL = {'2026-09-21': '敬老の日', '2026-09-22': '国民の休日', '2026-09-23': '秋分の日'}
AGG = ('いこーよ', '県公式', 'よかなび', '久留米観光', 'マップ登録')


# ⚠**168pxだと1枚に3件しか入らず「2〜3日」枠が0件になった**(2026-09-16の検品)。
#   ポスターは「絵がある」ことが効くので、**小さくして件数を確保する**方を選ぶ
THW = 126             # ポスターサムネの1辺(px)
_TC = {}


def _thumb(url):
    """ポスターを正方形のサムネにする。⚠**リサイズと中央切り出しだけ**。
      トリミングで意味が変わる加工はしない(出典の写真は縮小のみが原則)"""
    if url in _TC:
        return _TC[url]
    im = C.get_poster(url)
    if im is None:
        _TC[url] = None
        return None
    w, h = im.size
    s = max(THW / w, THW / h)
    im = im.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS)
    left = (im.width - THW) // 2
    top = (im.height - THW) // 2
    out = im.crop((left, top, left + THW, top + THW)).convert('RGBA')
    _TC[url] = out
    return out


def core(s):
    return re.sub(r'[^0-9A-Za-z一-龥ぁ-んァ-ヶー]', '', s or '')


def clean(t):
    """先頭の【施設名】は**会場**なので落とすだけでなく拾う。末尾の長い煽り文は削る"""
    m = re.match(r'^【([^】]{1,18})】(.*)$', t)
    head, rest = (m.group(1), m.group(2)) if m else ('', t)
    rest = re.sub(r'\s*[～~][^～~]{14,}$', '', rest)
    return re.sub(r'\s+', ' ', rest).strip(), head


def venue(r, tt, head):
    """⚠会場欄に**集約サイト名やイベント名そのもの**が入る。タイトルと6文字以上
       かぶるものは会場ではないので市区に落とす(2026-09-16に踏んだ)"""
    ct = core(tt)
    for v in (r.get('venues') or []):
        if not v or any(a in v for a in AGG):
            continue
        cv = core(v)
        if len(cv) > 22 or any(cv[i:i + 6] in ct for i in range(max(0, len(cv) - 5))):
            continue
        return v
    return head or (r.get('city') or '')


def load(f, t):
    d = json.load(io.open(SRC, encoding='utf-8'))
    supp = json.load(io.open(EXTRA, encoding='utf-8')) if os.path.exists(EXTRA) else {}
    span = []
    a = f
    while a <= t:
        span.append(a.isoformat()); a += timedelta(days=1)
    out = []
    for r in d['events']:
        sp = supp.get(r['url']) or {}
        ka = int(sp.get('kids_add') or 0)
        sc = r['score'] + ka
        dl = r.get('days_list')
        if dl:
            dd = [x for x in dl if x in span]
        else:
            s0, e0 = r['span'][0], r['span'][1]
            if not s0:
                continue
            s1, e1 = date.fromisoformat(s0), date.fromisoformat(e0 or s0)
            dd = [x for x in span if s1 <= date.fromisoformat(x) <= e1]
        if sc < 13 or not dd:
            continue
        # ⚠中止・延期が明記されているものはカードにも載せない(2026-09-16)
        if W.canceled(r['title'], r.get('lead')):
            continue
        tt, head = clean(r['title'])
        # ⚠**IPコラボのポスターは貼らない**(ポケモン/プリキュア/サンリオ/ちいかわ/
        #   パウ・パトロール等。版元の権利が重なり施設側にも再配布権が無い)。
        #   判定は week_events.poster_ok() を使う。貼れない回は**情報量で補う**
        po = r.get('poster') if W.poster_ok(r['title'], r.get('lead')) else None
        out.append({'sc': sc, 'ka': ka, 'days': dd, 'n': len(dd), 't': tt,
                    'v': venue(r, tt, head), 'price': sp.get('price') or '',
                    'time': sp.get('time') or '', 'url': r['url'], 'poster': po})
    out.sort(key=lambda x: -x['sc'])
    return out, span


def rowblock(im, d, y, ev, color, cur=None, maxw=None, dry=False, thumb=True):
    """1イベント=1行ブロック。タイトル(最大2行)+ 会場/時間/料金 + 「◯日も」
    ⚠`dry=True` は**描かずに高さだけ返す**。見出しの「◯件」を
      「実際に載せた数」にするために、先に測ってから描く2パスで使う"""
    x = 74
    if dry:
        class _N:
            def text(self, *a, **k): pass
            def rounded_rectangle(self, *a, **k): pass
            def textlength(self, *a, **k): return d.textlength(*a, **k)
        d2 = _N()
    else:
        d2 = d
    # ★**ポスターのサムネを左に置く**【2026-09-16ユーザー指摘
    #   「小さくしても良いのでポスターもいれてもらえますか？文字だけだと見る気になれない」】
    #   ⚠**IPコラボは貼らない**(load() で poster=None にしてある)。
    #     貼れない回は色帯だけにして、料金や内容の行で情報量を補う
    # ⚠**ポスターは「この日だけ」枠にだけ置く**(2026-09-16の検品で決めた)。
    #   全部に置くと1枚に3件しか入らず「2〜3日」枠が0件になった。
    #   絵が効くのは**行くかどうかを決める枠**なので、そこに寄せる
    th = None
    if thumb and ev.get('poster'):
        th = _thumb(ev['poster'])
    if th is not None and not dry:
        card = C.rounded((THW + 12, THW + 12), 14, (255, 255, 255, 255))
        card.paste(th, (6, 6))
        C.shadow(im, card, (x, y), blur=12, alpha=44, dy=4)
    if th is not None:
        tx = x + THW + 34
        maxw = W_ - tx - 74 + 26
    else:
        d2.rounded_rectangle([x, y + 6, x + 9, y + 56], 4, fill=color + (255,))
        tx = x + 26
        maxw = W_ - 150
    ytop = y
    ft = C.font(C.MEIB, 42)
    lines = C.wrap(d, ev['t'], ft, maxw - 26, maxline=2)
    for ln in lines:
        d2.text((tx, y), ln, font=ft, fill=INK + (255,))
        y += 50
    bits = []
    if ev['v']:
        bits.append(ev['v'])
    if ev['time']:
        bits.append(ev['time'])
    meta = ' / '.join(bits)
    if meta:
        fm = C.font(C.MEI, 30)
        for ln in C.wrap(d, meta, fm, maxw - 26, maxline=1):
            d2.text((tx, y + 2), ln, font=fm, fill=SUB + (255,))
        y += 36
    if ev['price']:
        fp = C.font(C.MEIB, 30)
        for ln in C.wrap(d, ev['price'], fp, maxw - 26, maxline=1):
            d2.text((tx, y), ln, font=fp, fill=HOT + (255,))
        y += 36
    if cur is not None and ev['n'] > 1:
        o = '・'.join(x2[-2:].lstrip('0') for x2 in ev['days'] if x2 != cur)
        fa = C.font(C.MEIB, 28)
        d2.text((tx, y), '%s日も開催' % o, font=fa, fill=GRN + (255,))
        y += 34
    # サムネのほうが背が高いときは、その高さを確保する
    if th is not None:
        y = max(y, ytop + THW + 12)
    return y + 14


def header(im, d, iso):
    """日付の見出し。数字を大きく、曜日と祝日名を添える"""
    dt = date.fromisoformat(iso)
    wd = WD[dt.weekday()]
    fn = C.font(C.ROUND, 168)
    d.text((72, 58), str(dt.day), font=fn, fill=INK + (255,))
    nx = 72 + int(d.textlength(str(dt.day), font=fn)) + 14
    d.text((nx, 150), '日', font=C.font(C.MEIB, 46), fill=SUB + (255,))
    wcol = (36, 96, 143) if wd == '土' else ((169, 58, 58) if wd == '日' else INK)
    d.text((nx + 62, 96), wd, font=C.font(C.ROUND, 64), fill=wcol + (255,))
    if HOL.get(iso):
        d.text((nx + 62, 172), HOL[iso], font=C.font(C.MEIB, 30), fill=SUB + (255,))
    d.line([(72, 244), (W_ - 72, 244)], fill=INK + (255,), width=5)
    return 274


def sect(im, d, y, num, label, cnt, note, color):
    t = C.rounded((46, 46), 12, color + (255,))
    ImageDraw.Draw(t).text((23, 23), str(num), font=C.font(C.ROUND, 34),
                           fill=(255, 255, 255, 255), anchor='mm')
    im.alpha_composite(t, (72, y))
    d.text((132, y + 2), label, font=C.font(C.ROUND, 50), fill=INK + (255,))
    d.text((W_ - 72, y + 12), '%d件' % cnt, font=C.font(C.MEIB, 32),
           fill=SUB + (255,), anchor='ra')
    y += 58
    d.text((74, y), note, font=C.font(C.MEI, 28), fill=SUB + (255,))
    return y + 48


SECT_H = 106          # sect() が消費する高さ(見出し58 + 注記48)


def fit(im, d, y, evs, color, limit, cur=None, thumb=True):
    """⚠**入る件数を先に測る**。見出しの「◯件」を宣言してから描くと、
      入り切らなかったぶんとの食い違いが出る(2026-09-16の検品で「3件」と書いて1件しか
      載っていなかった)。スキルの「黙って切ると全部載っているように見える」に反するので、
      ①dryで測って入る数を確定 ②その数で見出しを描く ③あふれたぶんは「ほかN件」と明示"""
    kept, yy = [], y
    for ev in evs:
        ny = rowblock(im, d, yy, ev, color, cur=cur, dry=True, thumb=thumb)
        if ny > limit:
            break
        kept.append(ev); yy = ny
    return kept, yy


def more(d, y, n):
    if n > 0:
        d.text((100, y), 'ほか%d件はマップで' % n, font=C.font(C.MEIB, 28), fill=SUB + (255,))
        return y + 38
    return y


def daycard(iso, only):
    """⚠**日別カードは「この日だけ」に集中させる**【2026-09-16ユーザー確定】
      当初は1枚に「この日だけ」+「2〜3日」を両方入れていたが、ポスターを足したら
      「2〜3日」枠が1〜2件あふれた。ユーザーの判断で**「2〜3日」は専用の1枚**にまとめ、
      日別はポスターを大きく使える構成にした(計9枚)"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    y0 = header(im, d, iso)
    k1, _ = fit(im, d, y0 + SECT_H, only, HOT, H_ - 130)
    n1 = len(only) - len(k1)
    y = sect(im, d, y0, 1, 'この日だけ', len(k1),
             '他の日にはありません。ここから決めるのが効率的', HOT)
    if k1:
        for ev in k1:
            y = rowblock(im, d, y, ev, HOT)
    else:
        d.text((74, y), 'この日だけの催しはありません', font=C.font(C.MEI, 32), fill=SUB + (255,))
        y += 60
    more(d, y, n1)
    return im.convert('RGB'), len(k1), n1


def multicard(multi):
    """「連休のうち2〜3日」を1枚にまとめる。各件に**開催日を全部**書く。
    cur='-' を渡すと rowblock が「◯・◯日も開催」を出すので、
    どの日に行けるかがこの1枚で分かる"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((72, 62), '2〜3日だけ', font=C.font(C.ROUND, 92), fill=INK + (255,))
    d.text((72, 158), 'やってる', font=C.font(C.ROUND, 92), fill=GRN + (255,))
    d.line([(72, 276), (W_ - 72, 276)], fill=INK + (255,), width=5)
    y = 306
    d.text((74, y), '日付を選べるもの。「この日だけ」を埋めた残りに',
           font=C.font(C.MEI, 30), fill=SUB + (255,))
    y += 54
    k, _ = fit(im, d, y, multi, GRN, H_ - 130, cur='-')
    for ev in k:
        y = rowblock(im, d, y, ev, GRN, cur='-')
    n = len(multi) - len(k)
    more(d, y, n)
    return im.convert('RGB'), len(k), n


def evercard(ever):
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((72, 62), '連休中', font=C.font(C.ROUND, 92), fill=INK + (255,))
    d.text((72, 158), 'ずっとやってる', font=C.font(C.ROUND, 92), fill=RED + (255,))
    d.line([(72, 276), (W_ - 72, 276)], fill=INK + (255,), width=5)
    y = 306
    d.text((74, y), 'どの日でも開いています。日別を埋めた残りの時間に',
           font=C.font(C.MEI, 30), fill=SUB + (255,))
    y += 54
    k, _ = fit(im, d, y, ever, SUB, H_ - 130)
    for ev in k:
        y = rowblock(im, d, y, ev, SUB)
    n = len(ever) - len(k)
    more(d, y, n)
    return im.convert('RGB'), len(k), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='f', required=True)
    ap.add_argument('--to', dest='t', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--per-day', type=int, default=5, help='「この日だけ」の最大件数')
    ap.add_argument('--per-multi', type=int, default=8, help='「2〜3日だけ」の最大件数(専用1枚)')
    ap.add_argument('--ever', type=int, default=6)
    # ⚠**「5日間の使い方」ではなく企画名を主役にする**【2026-09-16ユーザー確定
    #   「ターゲットをシルバーウィークにせっかく絞ってるので、5日間の使い方というより
    #     シルバーウィーク中の子連れイベント大集合！みたいな感じでいきませんか、
    #     日付は補足で良いと思います」】
    #   → hook(最大)=企画名 / tail(大)=誰向けか / sub(小)=日付と件数
    ap.add_argument('--hook', default='シルバーウィーク')
    ap.add_argument('--tail', default='子連れイベント大集合')
    ap.add_argument('--pref', default='福岡県', help='県バッジの文言')
    a = ap.parse_args()
    f = date.fromisoformat(a.f); t = date.fromisoformat(a.t)
    ev, span = load(f, t)
    T1 = [x for x in ev if x['n'] == 1]
    T2 = [x for x in ev if 2 <= x['n'] <= 3]
    T3 = [x for x in ev if x['n'] >= 4]
    os.makedirs(a.out, exist_ok=True)
    n = 0
    # 表紙
    # 日付は**補足**なので小さい行(sub)に回す
    sub = '%d/%d(%s)〜%d/%d(%s) ・ 全%d件' % (f.month, f.day, WD[f.weekday()],
                                           t.month, t.day, WD[t.weekday()], len(ev))
    badge = TB.make_badge(BADGE_W, BADGE_H, a.pref)
    cv = C.cover(sub, len(ev), len(ev), hook=a.hook, photo=C.COVER_DEFAULT,
                 tail=a.tail, cta='スワイプして見てね →', badge_img=badge)
    n += 1; cv.save(os.path.join(a.out, '%02d_表紙.jpg' % n), quality=92)
    print('  %02d_表紙.jpg' % n)
    # 日別
    for iso in span:
        only = [x for x in T1 if iso in x['days']][:a.per_day]
        dt = date.fromisoformat(iso)
        p = os.path.join(a.out, '%02d_%02d日.jpg' % (n + 1, dt.day))
        img, c1, o1 = daycard(iso, only)
        img.save(p, quality=92)
        n += 1
        # ⚠**入り切らなかった件数は必ず出す**。黙って切ると「全部載っている」ように見える
        print('  %s  この日だけ%d件%s'
              % (os.path.basename(p), c1, ('(+%d件あふれ)' % o1) if o1 else ''))
    # 2〜3日だけやってる(専用の1枚)
    p = os.path.join(a.out, '%02d_2〜3日だけ.jpg' % (n + 1))
    img, mk, mo = multicard(T2[:a.per_multi])
    img.save(p, quality=92); n += 1
    print('  %s  %d件%s' % (os.path.basename(p), mk, ('(+%d件あふれ)' % mo) if mo else ''))
    # 連休中ずっと
    p = os.path.join(a.out, '%02d_連休中ずっと.jpg' % (n + 1))
    img, ck, ok = evercard(T3[:a.ever])
    img.save(p, quality=92); n += 1
    print('  %s  %d件%s' % (os.path.basename(p), ck, ('(+%d件あふれ)' % ok) if ok else ''))
    # 締め
    p = os.path.join(a.out, '%02d_クロージング.jpg' % (n + 1))
    C.closing().save(p, quality=92); n += 1
    print('  %s' % os.path.basename(p))
    print('計 %d枚 → %s  (Instagramカルーセルは20枚まで)' % (n, os.path.normpath(a.out)))


if __name__ == '__main__':
    main()
