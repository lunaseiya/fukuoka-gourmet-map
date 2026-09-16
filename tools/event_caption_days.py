# -*- coding: utf-8 -*-
"""**日別カルーセル(event_daycards.py)専用のキャプション**を媒体別に書き出す。
【2026-09-16】

■ なぜ event_caption.py を使い回せないか
  `event_caption.py` は週次12選用で、候補JSONの **`selected`(12件)** を読む。
  日別カルーセルは「この日だけ / 2〜3日だけ / 連休中ずっと」で**30件以上**を載せており、
  selected とは中身が一致しない。**カードに書いてあるものとキャプションが違う**のは
  読者にとって一番たちが悪いので、**カードと同じ load() から作る**。

■ 媒体で分ける理由(event_caption.py と同じ)
  ・Instagram / TikTok は**キャプションのURLがタップできない** → URLを貼らず検索ワードに一本化
  ・YouTube の概要欄はクリックできる → 公式リンクを貼る(上限5000字)
  上限(実測) Instagram 2200 / TikTok 2200 / YouTube 5000。
  **超えたら末尾を切らずに件数を減らす**(途中で切れた文は不親切)

■ 構成はカードの並びに揃える
  表紙 → 日別(この日だけ) → 2〜3日だけ → 連休中ずっと → 締め

使い方:
    python tools/event_caption_days.py --dir data/carousel_sw \
        --from 2026-09-19 --to 2026-09-23 --hook シルバーウィーク
"""
import argparse, io, os, re, sys
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import event_daycards as D

LIMIT = {'instagram': 2200, 'tiktok': 2200, 'youtube': 5000}


def md(x):
    return '%d/%d(%s)' % (x.month, x.day, D.WD[x.weekday()])


# ⚠**会場欄に日付が入っていることがある**(久留米観光の「久留米・9/20㊐」)。
#   会場として出すと嘘になるので落とす。event_daycards の venue() は
#   「タイトルとかぶる文字列」しか弾いていないのでここで追加の網をかける
BADV = re.compile(r'[0-9０-９]{1,2}\s*[/／月]\s*[0-9０-９]{1,2}|[㊊-㊐]|\([日月火水木金土]\)')


def vshort(v):
    """会場は**施設名だけ**にする。「イオン甘木店 2階 楽市楽座横」まで入れると検索で出ない"""
    v = (v or '').strip()
    if not v or BADV.search(v):
        return ''
    return re.split(r'\s+(?=[0-9０-９]+\s*[FＦ階]|特設|セントラル|イベントホール|会場)', v)[0].strip()


def title_core(t, lim=18):
    """検索ワード用にタイトルの核だけ取る。**語の区切りで切る**(字数で機械的に切ると
    「キャナルお目覚めフェス zo」のように途中で切れて検索できない)。
    「!」は名前の一部(「チン!するレストラン」)なので消さない"""
    s = re.sub(r'[【】『』（）()\[\]★☆♪～~/・]+', ' ', t)
    # ⚠日本語は**空白が無いタイトルが普通**なので、語区切りだけだと切れずに全文が出る
    #   (「マジック！？科学！？見えないものが見える「透視」のナゾを実験しよう！」が
    #     そのまま検索ワードになっていた)。**句読点・記号も区切りとして扱う**
    if len(re.sub(r'\s+', '', s)) > lim and ' ' not in re.sub(r'\s+', ' ', s).strip():
        for ch in re.split(r'[！!？?、。「」×＆&：:]+', s):
            ch = ch.strip()
            if len(ch) >= 6:
                s = ch
                break
    out, n = '', 0
    for w in re.sub(r'\s+', ' ', s).strip().split(' '):
        if n and n + 1 + len(w) > lim:
            break
        out, n = (out + ' ' + w).strip(), n + (1 if n else 0) + len(w)
    return out or re.sub(r'\s+', ' ', s).strip()[:lim]


def kw(ev):
    """検索ワード。会場名がイベント名に含まれていれば会場は付けない(重複を避ける)"""
    c = title_core(ev['t'])
    sv = vshort(ev.get('v'))
    # 市区名が会場欄に入っている場合、タイトル側に同じ地名があれば重ねない
    # (「筑紫野市 イオンモール筑紫野」を作らない)
    stem = re.sub(r'[都道府県市区町村郡]$', '', sv)
    if sv and (sv in c or (len(stem) >= 2 and stem in c)):
        return c
    return ('%s %s' % (sv, c)).strip()


def line(ev, url):
    """1件ぶん。⚠料金・時間は**途中で切らない**。入らないなら項目ごと落とす"""
    L = ['・%s' % re.sub(r'\s+', ' ', ev['t']).strip()[:42]]
    b = [x for x in (vshort(ev.get('v')), ev.get('time') or '', ev.get('price') or '') if x]
    if b:
        L.append('  ' + ' ／ '.join(b))
    L.append('  🔎「%s」' % kw(ev))
    if url:
        L.append('  ' + ev['url'])
    return '\n'.join(L)


def build(groups, plat, hook, tail, frm, to, total):
    u = (plat == 'youtube')
    L = ['【福岡】%s %s' % (hook, tail),
         '%s〜%s ／ 全%d件' % (md(frm), md(to), total), '']
    # ⚠SNSのキャプションは**マークダウンが効かない**。`**強調**` は記号がそのまま出る
    L += ['連休のどこかで使えるものを、日付ごとにまとめました。', '']
    L += (['各イベントの公式リンクは下に全部貼っています。', '']
          if u else
          ['🔎の言葉で検索すると一番早く出てきます。',
           '(インスタはキャプションのリンクがタップできないので検索ワードにしています)', ''])
    for head, evs in groups:
        if not evs:
            continue
        L.append('──── %s ────' % head)
        L += [line(e, u) for e in evs]
        L.append('')
    L += ['──────────',
          '保存しておくと連休中に使えます📌',
          '期間限定イベントはプロフィールのマップにも載せてます🗺', '',
          '※画像は各主催者・施設の告知物です(出典は各カードに記載)',
          '※キャラクター作品の画像は権利の都合で掲載していません',
          '※お出かけ前に公式サイトで最新情報をご確認ください', '',
          '#福岡イベント #シルバーウィーク #福岡おでかけ #子連れおでかけ',
          '#福岡ママ #福岡子連れ #連休の過ごし方']
    return '\n'.join(L) + '\n'


def trim(groups, n):
    """入り切らないときの削り方。
    ⚠**最後のグループから順に空にしてはいけない**(2026-09-16の初回出力で踏んだ)。
      「2〜3日だけ」「連休中ずっと」が1件ずつに潰れ、**カードに8件載っているのに
      キャプションは1件**という不整合になった。
    → **件数が多いグループの末尾から1件**削る(全グループを均して減らす)。
      各グループは最低1件は残す"""
    g = [(h, list(e)) for h, e in groups]
    for _ in range(n):
        cand = [i for i in range(len(g)) if len(g[i][1]) > 1]
        if not cand:
            break
        g[max(cand, key=lambda i: len(g[i][1]))][1].pop()
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--from', dest='f', required=True)
    ap.add_argument('--to', dest='t', required=True)
    ap.add_argument('--per-day', type=int, default=5)
    ap.add_argument('--per-multi', type=int, default=8)
    ap.add_argument('--ever', type=int, default=6)
    ap.add_argument('--hook', default='シルバーウィーク')
    ap.add_argument('--tail', default='子連れイベント大集合')
    a = ap.parse_args()
    f, t = date.fromisoformat(a.f), date.fromisoformat(a.t)
    ev, span = D.load(f, t)
    T1 = [x for x in ev if x['n'] == 1]
    T2 = [x for x in ev if 2 <= x['n'] <= 3]
    T3 = [x for x in ev if x['n'] >= 4]
    groups = []
    for iso in span:
        dt = date.fromisoformat(iso)
        h = '%s%s この日だけ' % (md(dt), ('・' + D.HOL[iso]) if iso in D.HOL else '')
        groups.append((h, [x for x in T1 if iso in x['days']][:a.per_day]))
    groups.append(('2〜3日だけ', T2[:a.per_multi]))
    groups.append(('連休中ずっと', T3[:a.ever]))
    total = len(ev)

    os.makedirs(a.dir, exist_ok=True)
    for plat in ('instagram', 'youtube'):
        cut = 0
        while True:
            g = trim(groups, cut)
            s = build(g, plat, a.hook, a.tail, f, t, total)
            if len(s) <= LIMIT[plat] or cut > 60:
                break
            cut += 1
        p = os.path.join(a.dir, '_キャプション_%s.txt' % plat)
        io.open(p, 'w', encoding='utf-8').write(s)
        n = sum(len(e) for _, e in g)
        print('%-10s %4d字 / 上限%d  %s  掲載%d件%s'
              % (plat, len(s), LIMIT[plat], 'OK' if len(s) <= LIMIT[plat] else '超過!',
                 n, '' if not cut else ' (%d件はキャプションから省いた)' % cut))
    ig = io.open(os.path.join(a.dir, '_キャプション_instagram.txt'), encoding='utf-8').read()
    io.open(os.path.join(a.dir, '_キャプション_tiktok.txt'), 'w', encoding='utf-8').write(ig)
    print('%-10s %4d字 / 上限%d  OK  (Instagramと同文)' % ('tiktok', len(ig), LIMIT['tiktok']))


if __name__ == '__main__':
    main()
