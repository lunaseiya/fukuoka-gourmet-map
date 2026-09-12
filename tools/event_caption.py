# -*- coding: utf-8 -*-
"""週次イベント告知の**キャプションを媒体別に書き出す**。
【2026-09-13: 手書きしていたキャプションが Instagram の2200字を418字超過して発覚】

■ 媒体でリンクの扱いを変える。これが分ける理由
  ・**Instagram / TikTok はキャプションのURLがタップできない**。貼っても読者は打ち直せないので
    **URLは載せず「検索ワード」に一本化**する。URL12本で1200字以上使っていたのが超過の主因
  ・**YouTube の概要欄はURLがクリックできる**ので、こちらには全部貼る(上限5000字)
  → カード14枚目の「リンクはキャプションに貼ってます」は **YouTube/プロフィールのマップ**を指す

■ 上限(実測値)
  Instagram 2200 / TikTok 2200 / YouTube 5000。**超えたら末尾を削るのではなく件数を減らす**
  (途中で切れたキャプションは読者に不親切なので、収まる件数だけ出して残りはマップへ誘導)

■ 壊れやすいところ
  ・会場は **`venue`(施設名)** を使う。`place`(「1階 セントラルコート」等)は館内の場所なので
    単体では会場にならない。検索ワードも `venue` 起点で作る
  ・「あと何日」の基準日は **投稿日**。`--today` で渡す(既定=掲載期間の開始日)
  ・駐車場・料金は**途中で切らない**。入り切らないなら項目ごと落とす

使い方:
    python tools/event_caption.py --dir data/carousel_2026-09-14
    python tools/event_caption.py --dir ... --today 2026-09-14 --title "今週行ける"
"""
import argparse, io, json, os, re, sys
from datetime import date, datetime

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
OVER = os.path.join(HERE, '..', 'data', '_イベント表示名.json')
WK = '月火水木金土日'
LIMIT = {'instagram': 2200, 'tiktok': 2200, 'youtube': 5000}


def d(s):
    return datetime.strptime(s, '%Y-%m-%d').date()


def md(x):
    return '%d/%d(%s)' % (x.month, x.day, WK[x.weekday()])


def disp(ev, ov):
    """表示名と会場。生のイベント名は前置きと煽りで長いので、URLキーの上書き表を優先する。
    **機械的な正規表現で削ると名前が壊れる**(2026-09-13に「『映画名探偵プリキュア」を作った)ので
    上書きは手で確定させる。表に無いものは生のまま(長ければ後段で丸める)。"""
    o = ov.get(ev['url']) or {}
    name = o.get('name') or re.sub(r'\s+', ' ', ev['title']).strip()
    venue = o.get('venue') or ev.get('venue') or ev.get('place') or ''
    return name, venue


def span_txt(ev, today):
    a, b = ev['span']
    b = d(b)
    if ev.get('nostart') or not a:
        s = '〜%sまで' % md(b)
    else:
        a = d(a)
        s = md(a) if a == b else '%s〜%s' % (md(a), md(b))
    left = (b - today).days
    if 0 <= left <= 7:
        s += ' ★あと%d日' % (left + 1)
    return s


def block(ev, i, ov, today, with_url):
    name, venue = disp(ev, ov)
    L = ['%d. %s' % (i, name[:46])]
    line = '   📍%s' % (venue or ev.get('city') or '')
    if ev.get('city') and ev['city'] not in line:
        line += '(%s)' % ev['city']
    L.append('%s  📅%s' % (line, span_txt(ev, today)))
    # 時間・料金・駐車は**入り切らないなら項目ごと落とす**。途中で切らない
    bits = []
    if ev.get('time'):
        bits.append('🕐' + ev['time'])
    bits.append('¥無料' if ev.get('free') else '¥料金は公式で確認')
    pk = (ev.get('parking') or '').strip()
    if pk and len(pk) <= 18:
        bits.append('🅿' + pk)
    L.append('   ' + ' '.join(bits))
    # 検索ワードは施設名 + タイトルの核。**壊れた会場名を混ぜない**
    # タイトルの核。**語の区切りで切る**。字数で機械的に切ると
    # 「キャナルお目覚めフェス zo」「イオンモールでプリキュアを探」のように途中で切れて検索できない。
    # 「!」は名前の一部(「チン!するレストラン」「もっと！こどもの視展」)なので消さない
    t = re.sub(r'[【】『』（）()\[\]★☆♪～~/・]+', ' ', name)
    core, n = '', 0
    for w in re.sub(r'\s+', ' ', t).strip().split(' '):
        if n and n + 1 + len(w) > 18:
            break
        core, n = (core + ' ' + w).strip(), n + (1 if n else 0) + len(w)
    core = core or re.sub(r'\s+', ' ', t).strip()[:18]
    # 検索ワードの会場は**館内の場所を落として施設名だけ**にする。
    # 「イオン甘木店 2階 楽市楽座横」まで入れると検索でヒットしない
    sv = re.split(r'\s+(?=[0-9０-９]+\s*[FＦ階]|特設|セントラル|イベントホール|会場)',
                  venue or '')[0].strip()
    # 施設名がタイトルに既に入っているなら重ねない(「筥崎宮 筥崎宮 放生会」を作らない)
    kw = core if (sv and sv in core) else ('%s %s' % (sv or ev.get('city') or '', core)).strip()
    L.append('   🔎「%s」で検索' % kw)
    if with_url:
        L.append('   ' + (ev.get('official') or ev['url']))
    return '\n'.join(L)


def build(evs, plat, ov, today, frm, to, lead_title):
    head = ['【福岡】%s〜%s %s 子連れおでかけ%d選'
            % (md(frm), md(to), lead_title, len(evs)), '']
    head += ['家族で行けるところを今週分まとめました。',
             '★は今週で終わるものです。', '']
    if plat == 'youtube':
        head += ['各イベントの公式リンクは下に全部貼っています。', '']
    else:
        head += ['🔎の言葉で検索すると一番早く出てきます。',
                 '(インスタはキャプションのリンクがタップできないので検索ワードにしています)', '']
    body = [block(e, i, ov, today, plat == 'youtube') for i, e in enumerate(evs, 1)]
    tail = ['──────────',
            '保存しておくと行くときに使えます📌',
            '期間限定イベントはプロフィールのマップにも載せてます🗺', '',
            '※画像は各主催者・施設の告知物です(出典は各カードに記載)',
            '※キャラクター作品の画像は権利の都合で掲載していません',
            '※お出かけ前に公式サイトで最新情報をご確認ください', '',
            '#福岡イベント #福岡おでかけ #子連れおでかけ #福岡ママ #福岡子連れ']
    return '\n'.join(head) + '\n' + '\n\n'.join(body) + '\n\n' + '\n'.join(tail) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--json', default=CAND)
    ap.add_argument('--today', default='')
    ap.add_argument('--title', default='今週行ける')
    a = ap.parse_args()
    D = json.load(io.open(a.json, encoding='utf-8'))
    by = {e['url']: e for e in D['events']}
    evs = [by[u] for u in D['selected'] if u in by]
    ov = json.load(io.open(OVER, encoding='utf-8')) if os.path.exists(OVER) else {}
    frm, to = d(D['from']), d(D['to'])
    today = d(a.today) if a.today else frm

    os.makedirs(a.dir, exist_ok=True)
    for plat in ('instagram', 'youtube'):
        use = list(evs)
        # **上限を超えたら件数を減らす**。末尾を切ると読者に不親切
        while True:
            s = build(use, plat, ov, today, frm, to, a.title)
            if len(s) <= LIMIT[plat] or len(use) <= 6:
                break
            use = use[:-1]
        p = os.path.join(a.dir, '_キャプション_%s.txt' % plat)
        io.open(p, 'w', encoding='utf-8').write(s)
        print('%-10s %4d字 / 上限%d  %s  掲載%d件%s'
              % (plat, len(s), LIMIT[plat], 'OK' if len(s) <= LIMIT[plat] else '超過!',
                 len(use), '' if len(use) == len(evs) else ' (%d件は入らず省いた)' % (len(evs) - len(use))))
    # TikTokはInstagramと同文でよい
    ig = io.open(os.path.join(a.dir, '_キャプション_instagram.txt'), encoding='utf-8').read()
    io.open(os.path.join(a.dir, '_キャプション_tiktok.txt'), 'w', encoding='utf-8').write(ig)
    print('%-10s %4d字 / 上限%d  OK  (Instagramと同文)' % ('tiktok', len(ig), LIMIT['tiktok']))


if __name__ == '__main__':
    main()
