"""工事現場の「公表の更新」ウォッチ(2026-11-20 ユーザー確定)

定点の再訪は「公表データが更新されたとき」か「現地で日付の決まった出来事があるとき」だけ。
前回から日が空いた、は再訪の理由にしない(工事中は目に留まる絵がほぼ撮れず、新しい情報が無いと載せるものが無い)。

見るもの(data/工事現場_公表ページ.json):
  pages … 公式ページ。本文(タグを落とした文字)が前回と変わったら「更新あり」。増えた行を控える
  news  … Googleニュース(直近7日)。must の語が題に入る、まだ見ていない記事を「報道」として控える
結果:
  data/工事現場_更新.json   … 更新の記録(新しい順)。撮影ボードの「工事の定点」に出る
  data/工事現場_ページ控え.json … ページ本文の控え(差分用)・既読の記事

使い方:  python -X utf8 tools/patrol_watch.py          週1回
         python -X utf8 tools/patrol_watch.py --done 10  その現場の「更新あり」を消す(撮りに行った/見て不要と判断した)
初回は控えを作るだけで、ページの更新は出ない(比べる相手が無い)。
"""
import os, re, sys, json, time, html, hashlib, datetime
from urllib.parse import quote
sys.path.insert(0, os.path.dirname(__file__))
import opening_watch as ow   # fetch を借りる

D = os.path.join(os.path.dirname(__file__), '..', 'data')
CONF = os.path.join(D, '工事現場_公表ページ.json')
SNAP = os.path.join(D, '工事現場_ページ控え.json')
LOG = os.path.join(D, '工事現場_更新.json')
TODAY = datetime.date.today().isoformat()
# 新しい情報らしい語(増えた行にこれがあれば上に出す)
HOT = re.compile(r'開業|オープン|開園|開通|供用|完成|竣工|着工|切替|切り替え|通行止め|規制|解除|決定|発表|テナント|出店|店舗|延期|変更|20\d\d年|令和\d+年|\d+月\d+日')

AD = re.compile(r'分譲|マンション|モデルルーム|賃貸|求人|採用|資料請求|来場予約|PR$|広告')


def jload(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


def jsave(p, o):
    json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def lines_of(h):
    """本文を行の並びにする。script/style と、アクセスのたびに変わる数字(時刻・カウンタ)は落とす"""
    h = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', h)
    h = re.sub(r'(?i)<(br|/p|/li|/tr|/h\d|/div|/dd|/dt)[^>]*>', '\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    out = []
    for ln in t.split('\n'):
        ln = re.sub(r'\s+', ' ', ln).strip()
        if len(ln) >= 6 and not re.fullmatch(r'[\d\s:/.,\-]+', ln):
            out.append(ln)
    return out


def check_page(url, snap):
    key = 'page:' + url
    if url.lower().endswith('.pdf'):
        b = ow.fetch(url, binary=True)
        if b is None:
            return None
        h = hashlib.md5(b).hexdigest()
        old = snap.get(key)
        snap[key] = dict(hash=h, at=TODAY)
        return ['(PDFが差し替わった)'] if old and old.get('hash') != h else []
    t = ow.fetch(url)
    if t is None:
        return None
    ls = lines_of(t)
    old = snap.get(key)
    snap[key] = dict(lines=ls, at=TODAY)
    if not old:
        return []
    seen = set(old.get('lines', []))
    # 記事ページは横の広告が毎回入れ替わる(分譲マンション等)。広告の行は更新に数えない
    new = [x for x in ls if x not in seen and not AD.search(x)]
    new.sort(key=lambda x: 0 if HOT.search(x) else 1)
    return new


def check_news(q, must, snap):
    url = 'https://news.google.com/rss/search?q=%s&hl=ja&gl=JP&ceid=JP:ja' % quote(q + ' when:7d')
    x = ow.fetch(url)
    if x is None:
        time.sleep(40)   # 429 は少し待てば通ることが多い。1回だけ引き直す
        x = ow.fetch(url)
    if x is None:
        return None
    seen = snap.setdefault('news_seen', {})
    out = []
    for it in re.findall(r'(?s)<item>(.*?)</item>', x):
        g = lambda tag: html.unescape((re.search(r'(?s)<%s[^>]*>(.*?)</%s>' % (tag, tag), it) or [0, ''])[1]).strip()
        title, link, pub = g('title'), g('link'), g('pubDate')
        if not re.search(must, title, re.I):
            continue
        k = re.sub(r'\s*[-｜|]\s*[^-｜|]+$', '', title)[:40]   # 媒体名を落とした題で同じ記事をまとめる
        if k in seen:
            continue
        seen[k] = TODAY
        out.append(dict(title=title, url=link, pub=pub[:16]))
    return out


def main():
    conf = jload(CONF, [])
    log = jload(LOG, [])
    if '--done' in sys.argv:
        no = sys.argv[sys.argv.index('--done') + 1]
        n = 0
        for e in log:
            if e['no'] == no and not e.get('done'):
                e['done'] = TODAY
                n += 1
        jsave(LOG, log)
        print('現場 %s の「更新あり」を %d 件 消した' % (no, n))
        return
    snap = jload(SNAP, {})
    first = not snap
    failed, found = [], []
    for s in conf:
        for u in s.get('pages', []):
            new = check_page(u, snap)
            time.sleep(2)
            if new is None:
                failed.append(u)
            elif new:
                found.append(dict(at=TODAY, no=s['no'], name=s['name'], kind='公式ページ', url=u,
                                  what=' / '.join(x[:70] for x in new[:4]), n=len(new)))
        for q in s.get('news', []):
            arts = check_news(q, s['must'], snap)
            time.sleep(10)   # Googleニュースは続けて引くと 429
            if arts is None:
                failed.append('ニュース: ' + q)
                continue
            if first:
                continue   # 初回は既読にするだけ(直近7日ぶんが全部「新着」になるのを避ける)
            for a in arts:
                found.append(dict(at=TODAY, no=s['no'], name=s['name'], kind='報道', url=a['url'], what=a['title'][:90], n=1))
    jsave(SNAP, snap)
    log = found + log
    jsave(LOG, log[:300])
    print('== 工事現場の公表ウォッチ %s ==' % TODAY)
    if first:
        print('初回: 控えを作った(次回から差分が出る)')
    for e in found:
        print('★更新 [%s %s] %s: %s\n    %s' % (e['no'], e['name'], e['kind'], e['what'], e['url']))
    print('更新: %d件' % len(found))
    opened = [e for e in log if not e.get('done')]
    if opened:
        print('未対応の更新がある現場: ' + '・'.join(sorted({e['no'] + ' ' + e['name'] for e in opened})))
    if failed:
        print('取れなかった(未確認): %d件' % len(failed))
        for f in failed:
            print('  - ' + f)


if __name__ == '__main__':
    main()
