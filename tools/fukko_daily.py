# -*- coding: utf-8 -*-
"""九州ふっこう応援割の**動きを1日1回見張る**。変化があったときだけ報告する。

■ 何を見るか
  ① 県公式の一覧PDFの**版が上がったか** … 熊本は宿泊施設一覧と旅行事業者一覧の2本。
     ファイルのハッシュとサイズで比較する。**HTMLの表示状態に依存しないので確実**。
     旅行事業者一覧が増える = **新しい予約経路ができた**(いま熊本はじゃらんと楽天の2社だけ)
  ② 対象施設一覧に**宿が追加されたか** … マップの宿が後から載ることがある
     (公式が「掲載施設は順次更新」「準備が整った施設から順次販売開始」と明記)

■ ⚠**クーポンの残り枠は自動では読めない**(2026-09-15に両サイトで確認済み)
  ・**楽天トラベル**: 県別ページのHTMLに「獲得する」「獲得しました」「獲得済みです」
    「終了しました」「先着利用上限に達しました」の**5つのラベルが全部入っていて**、
    表示はJavaScriptで切り替わる。サーバー側HTMLから状態は判定できない。
  ・**じゃらん特設ページ**: JavaScript描画で、**生HTMLに県名が1つも出てこない**
    (24,890文字中ゼロ)。ステータスも当然読めない。
  ⚠**WebFetch(要約モデル)に読ませてはいけない**。2026-09-15に
    「全券種が配布中」「長崎は終了・熊本は受付中」と**根拠のない答えを2回返し**、
    それを信じて報告してユーザーに無駄足を踏ませた。
    枠の状況は**人がブラウザで見る**か、ブラウザ自動化で描画後のDOMを見るしかない。

使い方:
    python tools/fukko_daily.py            # 変化があれば表示
    python tools/fukko_daily.py --verbose  # 変化が無くても現状を表示
"""
import gzip, hashlib, io, json, os, re, sys, urllib.request, zlib
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, '..', 'data', 'fukko_state.json')
JST = timezone(timedelta(hours=9))

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# 版を見張るファイル。増えたら足す
WATCH_FILES = {
    '熊本_宿泊施設一覧': 'https://kumamoto-ouenwari.com/yoshiki/ichiran.pdf',
    '熊本_旅行事業者一覧': 'https://kumamoto-ouenwari.com/yoshiki/0914_sankakuryokou.pdf',
}
JALAN = 'https://www.jalan.net/kyushu-shien/'
PREFS = ['福岡', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島']


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept-Language': 'ja,en;q=0.9',
                                               'Accept-Encoding': 'gzip, deflate'})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
        enc = (r.headers.get('Content-Encoding') or '').lower()
    if 'gzip' in enc:
        raw = gzip.decompress(raw)
    elif 'deflate' in enc:
        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    if binary:
        return raw
    for e in ('utf-8', 'shift_jis', 'cp932', 'euc-jp'):
        try:
            return raw.decode(e)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def pdf_text(raw):
    """PDFの中の施設名を拾う。pypdf が無ければ空を返す(版の比較だけは効く)"""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        r = PdfReader(io.BytesIO(raw))
        return '\n'.join((p.extract_text() or '') for p in r.pages)
    except Exception:
        return None


def load():
    if os.path.exists(STATE):
        return json.load(io.open(STATE, encoding='utf-8'))
    return {}


def main():
    verbose = '--verbose' in sys.argv[1:]
    old = load()
    new = {'checked': datetime.now(JST).isoformat(timespec='seconds')}
    changes = []

    # --- ① 一覧PDFの版 ---------------------------------------------------
    new['files'] = {}
    for name, url in WATCH_FILES.items():
        try:
            raw = fetch(url, binary=True)
        except Exception as e:
            new['files'][name] = {'error': str(e)}
            changes.append('  ! %s を取得できなかった: %s' % (name, e))
            continue
        h = hashlib.sha256(raw).hexdigest()[:16]
        rec = {'sha': h, 'size': len(raw)}
        t = pdf_text(raw)
        if t is not None:
            lines = [l.strip() for l in t.split('\n') if l.strip()]
            rec['lines'] = len(lines)
            rec['names'] = lines
        new['files'][name] = rec
        o = (old.get('files') or {}).get(name) or {}
        if o.get('sha') and o['sha'] != h:
            changes.append('  ★ %s が更新された (行数 %s → %s)'
                           % (name, o.get('lines', '?'), rec.get('lines', '?')))
            if o.get('names') and rec.get('names'):
                added = [x for x in rec['names'] if x not in set(o['names'])]
                if added:
                    changes.append('     追加: %s' % ' / '.join(added[:20]))
        elif not o.get('sha'):
            changes.append('  ・%s を初回記録 (%s行)' % (name, rec.get('lines', '?')))

    io.open(STATE, 'w', encoding='utf-8').write(json.dumps(new, ensure_ascii=False, indent=1))

    print('=== 九州ふっこう応援割 見張り %s ===' % new['checked'])
    if changes:
        print('変化あり:')
        print('\n'.join(changes))
    else:
        print('変化なし')
    if verbose or changes:
        print()
        print('現状:')
        for name, rec in new['files'].items():
            print('  %-20s %s' % (name, rec.get('error') or '%s行 / %.0fKB'
                                  % (rec.get('lines', 0), rec['size'] / 1024)))
        print()
        print('  ⚠クーポンの残り枠は**このツールでは判定できない**(じゃらん・楽天とも JS描画)。')
        print('    手で見る: %s' % JALAN)
        print('             https://travel.rakuten.co.jp/special/kyushuouen/kumamoto/')
        print('  ⚠12月1日以降の宿泊分は**11月中旬以降に別枠で販売開始**予定。ここが本命')


if __name__ == '__main__':
    main()
