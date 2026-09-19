# -*- coding: utf-8 -*-
"""シルバーウィーク版カルーセル13枚を書き出す【2026-09-19】

構成(ユーザー確定):
  01 表紙
  02〜11 イベントカード(**2件/枚** / 上部にエリアタブ / 各件に memo とデータ)
  12 **早見表**(「シルバーウィーク計画に役立ててね」) ← 最後から2番目
  13 締め(マップ案内「その他もイベント多数あり、詳しくはプロフィール欄をご覧ください」)

⚠**エリア順に並べる**。日付順にすると会期が連休全期間のイベント(4件)が何枚にも出て
  20件が10枚に収まらない。日付はカード内の赤字と早見表で補う。
"""
import datetime, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw
import carousel2 as C2
import event_carousel as EC
from event_carousel import font, rounded, shadow, wrap, deemoji, pill, ROUND, MEI, MEIB
from carousel2 import W_, H_, BG, INK, SUB, AREAS, area_of, sw_days, daylabel

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'data', 'carousel_sw_2026-09-19')
WD = '月火水木金土日'

# ── 20件の指定(タイトルの一部で引く。エリア順) ────────────────
PICK = [
 # 福岡市
 'キッズモデル体験', 'シルバーウィークナイトシネマ', 'デデデ', 'OHORI', '魔法の美術館', '透視',
 # 市の周辺
 '万代 秋まつり', '防災ポーチ', 'お箸づくり', 'ドラえもん', '手作りカフェ', 'こどもの視展',
 # 北九州・筑豊
 # ⚠**同名のイベントが福岡公演と北九州公演の2つある**(2026-09-19に取り違えた)。
 #   北九州枠なので「北九州 ０歳からの」で引く
 '縁日パラダイス', '北九州 ０歳からの', '西日本陶磁器フェスタ', 'ピザ作り',
 # 筑後
 '城島ふるさと夢まつり', '子どもフェス', 'アクティブ・キッズ', '九州サーカス団',
]
# 市区が空の回はここで補う(エリアタブの判定に必要)
CITY_FIX = {
 'OHORI': '福岡市中央区', '魔法の美術館': '福岡市中央区', '透視': '福岡市中央区',
 'キッズアクション': '福岡市東区', 'こどもの視展': '大野城市',
 '北九州 ０歳からの': '北九州市八幡西区', '西日本陶磁器フェスタ': '北九州市小倉北区',
 'ピザ作り': '北九州市小倉南区', 'アクティブ・キッズ': '朝倉市', '九州サーカス団': '小郡市',
 'シルバーウィークナイトシネマ': '福岡市博多区', 'キッズモデル体験': '福岡市東区',
 'デデデ': '福岡市中央区', '城島ふるさと夢まつり': '久留米市', '子どもフェス': '久留米市',
}


# ── 表紙の背景とバッジ ────────────────────────────────────
#   ユーザー指示【2026-09-19】「表示が空白なので背景設定しましょう。
#     共通素材からとるようにしましょうか、ガンダムあたりとかどうでしょ？」
#     「あと福岡のアイコン小さいです」
#   ⚠**県バッジが小さいという指摘は2回目**(2026-09-16「福岡アイコンちっさすぎるので
#     サムネと同サイズにしましょう」)。`cover()` は `badge_img` を渡せば
#     動画サムネと同じ3層バッジになるのに、渡していなかった。
SHARED = os.path.join(os.path.expanduser('~'), 'Dropbox', 'ショート動画用', '5.共通素材')
FF = (r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages'
      r'\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe'
      r'\ffmpeg-8.1.2-full_build\bin')
ASSETS = r'C:\Users\totor\.claude\skills\short-video\assets'
# ららぽーと福岡の実物大νガンダム。**全身が引きで入り、人が写っていない**コマを選んだ
COVER_MOV = os.path.join(SHARED, 'ららぽーと福岡_ガンダム', '動画 2026-09-08 11 08 02.mov')
COVER_SS = 1.5


def cover_photo():
    """共通素材のガンダムから表紙の背景を作る。
    ⚠`cover()` は渡した写真を**上から4:5で切る**ので、ガンダムの全身が入るように
      こちら側で窓を決めてから渡す(スキルのサムネと同じ考え方)。"""
    import subprocess
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, '_cover_src.png')
    subprocess.run([os.path.join(FF, 'ffmpeg'), '-y', '-hide_banner', '-loglevel', 'error',
                    '-ss', str(COVER_SS), '-i', COVER_MOV, '-frames:v', '1', tmp],
                   capture_output=True)
    if not os.path.exists(tmp):
        print('!! 表紙の背景が作れない:', COVER_MOV)
        return None
    im = Image.open(tmp).convert('RGB')
    # 2160×3840 の縦。4:5(=0.8)の窓を**全身が収まる位置**で切る
    ww = im.width
    hh = int(round(ww / 0.8))
    y0 = max(0, min(im.height - hh, int(im.height * 0.06)))
    c = im.crop((0, y0, ww, y0 + hh))
    p = os.path.join(OUT, '_cover.jpg')
    c.save(p, quality=92)
    os.remove(tmp)
    return p


def pref_badge():
    """動画サムネと同じ3層バッジ(福岡県/福岡)。`cover()` の badge_img に渡す"""
    if ASSETS not in sys.path:
        sys.path.insert(0, ASSETS)
    import thumbs_build as TB
    bw, bh = TB.badge2_size('tiktok', '福岡')
    return TB.make_badge2(bw, bh, '福岡県', '福岡', TB.badge_color('福岡'))


SW_ALL = ['2026-09-%d' % d for d in (19, 20, 21, 22, 23)]


def sheet(evs):
    """12枚目: 早見表。**日付ごとにどれが行けるか**を一覧にする。

    ⚠**日付ごとに素直に並べると入り切らない**(2026-09-19ユーザー「なんか切れてますね」)。
      原因は①**会期が連休全期間のイベント4件が5日分すべてに重複して出る**ため
      実質29行になる ②1列だと1行1件で縦に伸びる。
      → ①「連休ずっと」を**先に1ブロックへ括り出す**(重複25行→16行相当)
        ②**2列**にする ③描く前に総高を計算して 1350px に収まることを確認する。
    """
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    d.text((W_ // 2, 40), 'シルバーウィーク 早見表', font=font(ROUND, 62),
           fill=INK + (255,), anchor='ma')
    d.text((W_ // 2, 114), '計画に役立ててね', font=font(MEIB, 32),
           fill=(206, 57, 52, 255), anchor='ma')

    PAD, GAP = 40, 20
    CW = (W_ - PAD * 2 - GAP) // 2          # 列幅 490
    PILL_H, ROW_H, BGAP = 56, 38, 12
    fn, fc = font(MEI, 28), font(MEI, 22)

    # 連休ずっと行ける分を括り出す
    full = [e for e in evs if all(x in sw_days(e) for x in SW_ALL)]
    blocks = [('連休ずっと行ける', (196, 124, 40), full)]
    for i in range(5):
        day = datetime.date(2026, 9, 19) + datetime.timedelta(days=i)
        iso = day.isoformat()
        g = [e for e in evs if iso in sw_days(e) and e not in full]
        # ⚠**9/19〜9/23 は5日とも休み**。これがシルバーウィークになる理由:
        #   9/21(月)=敬老の日、9/23(水)=秋分の日、その間の **9/22(火)=国民の休日**。
        #   平日扱い(青)にすると「火曜は仕事」と読まれてしまう(2026-09-19に一度そう描いた)
        hol = {'2026-09-21': '祝', '2026-09-22': '休', '2026-09-23': '祝'}.get(iso)
        col = (206, 57, 52) if (WD[day.weekday()] in '土日' or hol) else (52, 96, 168)
        lab = '9/%d(%s%s)' % (day.day, WD[day.weekday()], '・' + hol if hol else '')
        blocks.append((lab, col, g))

    y = 166
    need = sum(PILL_H + 8 + ((len(g) + 1) // 2) * ROW_H + BGAP for _, _, g in blocks)
    if y + need > H_ - 20:
        print('!! 早見表がはみ出す: 必要%dpx / 空き%dpx' % (need, H_ - 20 - y))
    for lab, col, g in blocks:
        head = rounded((W_ - PAD * 2, PILL_H), 14, col + (255,))
        im.alpha_composite(head, (PAD, y))
        hd = ImageDraw.Draw(im)
        hd.text((PAD + 22, y + PILL_H // 2), lab, font=font(MEIB, 34),
                fill=(255, 255, 255, 255), anchor='lm')
        hd.text((W_ - PAD - 22, y + PILL_H // 2), '%d件' % len(g), font=font(MEIB, 30),
                fill=(255, 255, 255, 235), anchor='rm')
        y += PILL_H + 8
        for k, e in enumerate(g):
            x = PAD + 8 + (k % 2) * (CW + GAP)
            ry = y + (k // 2) * ROW_H
            t = '・' + deemoji(e.get('_short') or e.get('title') or '')
            d.text((x, ry), t, font=fn, fill=INK + (255,))
            # 市区は入るときだけ足す(入らないなら落とす。途中で切らない)
            city = (e.get('city') or '').replace('福岡市', '').replace('北九州市', '')
            wn = d.textlength(t, font=fn)
            if city and wn + 10 + d.textlength(city, font=fc) <= CW - 8:
                d.text((x + wn + 10, ry + 6), city, font=fc, fill=SUB + (255,))
        y += ((len(g) + 1) // 2) * ROW_H + BGAP
    return im


# **本人のアカウントのプロフィール写真**。ユーザーが実物を指定した(2026-09-19
#   「アイコンはこれです」)。スクショから円に抜いて `assets/profile_avatar.png` に置いてある。
#   汎用の人型線画では「どのアカウントを見ればいいか」が伝わらないので実物を使う。
AVATAR = os.path.join(ROOT, 'assets', 'profile_avatar.png')
HANDLE = 'るな@福岡子育てグルメ'


def profile_icon(size):
    """プロフィール写真を円で返す。無ければ None(締めは文字だけになる)"""
    if not os.path.exists(AVATAR):
        print('!! プロフィール写真が無い:', AVATAR)
        return None
    return Image.open(AVATAR).convert('RGBA').resize((size, size), Image.LANCZOS)


#   ユーザーが一覧ページのスクショを渡してきた(2026-09-19「締め、これ使うと画面大きいですが。。
#   縮小して使いますが？」)。
#   ⚠**全体を縮小して貼らない**。2140px の縦長を1枚に収めると文字が10px以下になって
#     何のページか読めず、ただの「細長い何か」になる。**上から688pxだけ切って横幅を使う**
#     (見出し・日付タブ・エリアタブが入る=「日付とエリアで絞れる一覧」だと一目で分かる範囲)。
#     エリアタブの行で切っているのは、次の行を半分だけ見せると「切れている」ように見えるから。
PAGE_SHOT = os.path.join(ROOT, 'assets', 'profile_page_shot.png')


def closing():
    """13枚目: 締め。文言はユーザー指定"""
    im = Image.new('RGBA', (W_, H_), BG + (255,))
    d = ImageDraw.Draw(im)
    y = 52
    for ln in ('その他も', 'イベント多数あり'):
        d.text((W_ // 2, y), ln, font=font(ROUND, 66), fill=INK + (255,), anchor='ma')
        y += 82
    y += 22

    # 一覧ページのスクショ(角丸+影)
    if os.path.exists(PAGE_SHOT):
        sh = Image.open(PAGE_SHOT).convert('RGBA')
        SW = W_ - 70 * 2
        sh = sh.resize((SW, int(round(sh.height / sh.width * SW))), Image.LANCZOS)
        card = rounded((SW, sh.height), 22, (255, 255, 255, 255))
        card.paste(sh, (0, 0), rounded((SW, sh.height), 22, (255, 255, 255, 255)))
        shadow(im, card, (70, y), blur=20, alpha=56, dy=7)
        y += sh.height + 34
    else:
        print('!! 一覧ページのスクショが無い:', PAGE_SHOT)

    d.text((W_ // 2, y), '日付とエリアで絞れる一覧です', font=font(MEIB, 38),
           fill=SUB + (255,), anchor='ma')
    y += 60
    d.text((W_ // 2, y), '詳しくはプロフィール欄をご覧ください', font=font(MEI, 32),
           fill=SUB + (255,), anchor='ma')
    y += 66

    # プロフィール写真とアカウント名を横並びで(誰を見ればいいか分かるように)
    S = 118
    ic = profile_icon(S)
    tw = d.textlength(HANDLE, font=font(MEIB, 40))
    x0 = int((W_ - (S + 22 + tw)) // 2)
    if ic is not None:
        im.alpha_composite(ic, (x0, y))
    else:
        print('!! プロフィール写真が無い:', AVATAR)
        x0 -= S + 22
    d.text((x0 + S + 22, y + S // 2), HANDLE, font=font(MEIB, 40),
           fill=INK + (255,), anchor='lm')
    y += S + 30

    # マップ本体の案内(イベント一覧の隣にある、もう半分の中身)
    box = rounded((W_ - 160, 164), 26, (255, 255, 255, 255))
    shadow(im, box, (80, y), blur=18, alpha=48, dy=6)
    bd = ImageDraw.Draw(im)
    bd.text((W_ // 2, y + 44), '福岡こそだてグルメマップ', font=font(ROUND, 46),
            fill=(206, 57, 52, 255), anchor='ma')
    bd.text((W_ // 2, y + 106), '子供椅子・おむつ替え・座敷で絞り込めます',
            font=font(MEI, 26), fill=SUB + (255,), anchor='ma')
    y += 164
    if y > H_ - 20:
        print('!! 締めがはみ出す: %dpx / 上限%dpx' % (y, H_ - 20))
    return im


def main():
    C = json.load(io.open(os.path.join(ROOT, 'data', '_週末イベント候補.json'), encoding='utf-8'))
    X = json.load(io.open(os.path.join(ROOT, 'data', '_イベント補足.json'), encoding='utf-8'))
    evs = []
    for k in PICK:
        hit = [r for r in C['events'] if k in r['title']]
        if not hit:
            print('!! 候補に無い:', k)
            continue
        r = dict(hit[0])
        if not r.get('city'):
            r['city'] = CITY_FIX.get(k, '')
        r['_short'] = k
        evs.append(r)
    os.makedirs(OUT, exist_ok=True)
    # ⚠**毎回クリアする**。枚数や配分が変わると前回のファイルが残って混在する
    #   (2026-09-19に 05_福岡市 と 05_市の周辺 が両方残った)
    for f in os.listdir(OUT):
        if f.lower().endswith('.jpg'):
            os.remove(os.path.join(OUT, f))
    pages = []
    # 01 表紙。
    # ⚠長いフック文は cover() で1行のまま描かれて**左右が切れる**(2026-09-19)ので短く。
    # ⚠`cover()` は hook の下に tail(既定「福岡の子連れおでかけ N選」)も描くので、
    #   hook に「〜20選」と入れると**20選が2回**出る。
    #   → hook は「シルバーウィーク」、下段(tail)を「福岡の子連れおでかけ 20選」にする
    #     (2026-09-19ユーザー確定)
    pages.append(('01_表紙', EC.cover(
        '9/19(土)〜9/23(水・祝)', len(evs), len(evs),
        hook='シルバーウィーク',
        photo=cover_photo(), badge_img=pref_badge())))
    # 02〜11 エリアごとに2件/枚
    n = 2
    for lab, _test, _col in AREAS:
        g = [e for e in evs if area_of(e.get('city')) == lab]
        for i in range(0, len(g), 2):
            pair = g[i:i + 2]
            pages.append(('%02d_%s' % (n, lab.replace('・', '')), C2.card2(pair, lab, X)))
            n += 1
    pages.append(('%02d_早見表' % n, sheet(evs))); n += 1
    pages.append(('%02d_締め' % n, closing()))
    for name, im in pages:
        p = os.path.join(OUT, name + '.jpg')
        im.convert('RGB').save(p, quality=92)
    # ⚠**表紙の背景に使った中間ファイルを残さない**。
    #   後工程(tiktok_9x16 / スライドショー)が *.jpg を全部拾うので14枚になる(2026-09-19)
    tmp = os.path.join(OUT, '_cover.jpg')
    if os.path.exists(tmp):
        os.remove(tmp)
    print('%d枚 → %s' % (len(pages), os.path.normpath(OUT)))
    for lab, _t, _c in AREAS:
        print('  %-12s %d件' % (lab, sum(1 for e in evs if area_of(e.get('city')) == lab)))


if __name__ == '__main__':
    main()
