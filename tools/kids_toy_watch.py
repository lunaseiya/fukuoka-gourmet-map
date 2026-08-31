# -*- coding: utf-8 -*-
"""子供向けのおもちゃ企画(ハッピーセット / モスワイワイセット)を見張って、
チェーン全店に campaign として一括で付ける。

  python tools/kids_toy_watch.py            # 今マップに入っている状態と残り日数
  python tools/kids_toy_watch.py --watch    # PR TIMES から新しいリリースを拾う
  python tools/kids_toy_watch.py --apply    # 下の CURRENT を spots.json に書き込む

■ なぜ PR TIMES を見るのか
マクドナルドの公式ハッピーセットページは**完全にJS描画**で、生HTMLには何も入っていない。
モスの公式も同様。PR TIMES のキーワードページはサーバー描画なので、そこを見張る。
  https://prtimes.jp/topics/keywords/ハッピーセット
ただし**第三者の調査リリースや書籍の宣伝も混ざる**ので、拾えるのは候補まで。
会期は候補のタイトルからWeb検索で確定させて、下の CURRENT に手で書く。

■ なぜ全店に同じものを付けるのか
ハッピーセットもモスワイワイセットも**全国の店で同じおもちゃ**が配られる。
店ごとに違うコラボ(スシロー×キティ等)と違い、チェーン名で一括して構わない。

■ 入れ替わりが速い
ハッピーセットは**約2週間**で次のおもちゃに変わる。会期が切れると campaign は
マップ側で自動的に無効になる(金リングとバッジだけ消えてピンは残る)ので、
放置しても嘘は出ない。ただし新しいおもちゃは手で足す必要がある。
"""
import json, io, os, re, sys, time, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'data', 'spots.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

# 見張るキーワード(PR TIMES)
# (チェーン名, PR TIMESのキーワード, 題名に含まれていてほしい語)
#   キーワードは**実在を確認したものだけ**書くこと。
#   「モスワイワイセット」はキーワードページが無く404になる(2026-08-31実測)。
#   絞り込み語はチェーンごとに変える。マクドナルドは「ハッピーセット」で一本釣りできるが、
#   モスやケンタッキーは商品リリースが大量に出るので、子供向けの語で絞らないと埋もれる
WATCH = [
    ('マクドナルド',   'ハッピーセット', ['ハッピーセット']),
    ('モスバーガー',   'モスバーガー',   ['ワイワイ', 'おもちゃ', 'キッズ', 'お子さま']),
    ('くら寿司',       'ビッくらポン',   ['ビッくらポン']),
    ('ココス',         'ココス',         ['キッズ', 'おもちゃ', 'コラボ', 'お子さま']),
    ('ケンタッキー',   'ケンタッキー',   ['キッズ', 'おもちゃ', 'グッズ', 'こどもセット']),
]
# 題名にこれが入っていたら、企画そのものではなく調査・書籍・音楽の話とみなして落とす
# (「ハッピーセット」という名前のバンドのリリースまで引っかかるため)
DROP = ['調査', 'アンケート', '意識調査', 'ランキング', 'リリース！', 'バンド', '一曲', '楽曲']

# ── 今かかっている企画(会期を確認して手で書く) ────────────────────
#   name_match … spots.json の name に含まれていれば対象にする
CURRENT = [
    {
        'name_match': 'マクドナルド',
        'campaign': {
            'title': 'ハッピーセット パペットスンスン',
            'label': 'ハッピーセット',
            'note': 'おもちゃはオリジナルデザインのシールセット全4種(スンスン・ノンノン・ゾンゾン)',
            'from': '2026-08-28', 'fromLabel': '8月28日',
            'until': '2026-09-10', 'untilLabel': '9月10日ごろ',
            'url': 'https://www.mcdonalds.co.jp/family/happyset/',
        },
    },
    {
        'name_match': 'モスバーガー',
        'campaign': {
            'title': 'モスワイワイセット たまごっち 第2弾',
            'label': 'ワイワイセット',
            'note': 'おもちゃは4種(きらきらシール9枚セット / ミニクリアケース / おてがみバッグ / まめっちのボールペン)',
            'from': '2026-07-15', 'fromLabel': '7月15日',
            'until': '2026-09-30', 'untilLabel': '9月下旬',
            'url': 'https://www.mos.jp/',
        },
    },
]


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25)\
                         .read().decode('utf-8', 'replace')


def watch():
    for chain, kw, pick in WATCH:
        print('■ %s / キーワード「%s」' % (chain, kw))
        try:
            h = get('https://prtimes.jp/topics/keywords/' + urllib.parse.quote(kw))
        except Exception as e:
            print('   取得エラー', repr(e)[:60]); continue
        # 同じリリースURLが複数回出てくる(画像リンクとテキストリンク)。
        # 先に来るのは空タイトルのことが多いので、URLごとに**一番長いタイトル**を採る。
        # ここでURLを見た時点で弾くと、本命のタイトルまで捨ててしまう
        best = {}
        for m in re.finditer(r'href="(/main/html/rd/p/[^"]+)"[^>]*>(?:<[^>]+>)*([^<]{0,140})', h):
            url, title = 'https://prtimes.jp' + m.group(1), m.group(2).strip()
            if len(title) > len(best.get(url, '')):
                best[url] = title
        rows = []
        for url, title in best.items():
            if not any(p in title for p in pick):
                continue
            if any(d in title for d in DROP):
                continue
            rows.append((title, url))
        print('   候補 %d件' % len(rows))
        for t, u in rows[:8]:
            print('   ・%s' % t[:76])
            print('     %s' % u)
        time.sleep(1.0)
    print()
    print('※拾えるのは題名とURLまで。**会期はここでは分からない**。')
    print('  候補をWeb検索で確認して CURRENT に手で書き、--apply で反映すること')
    print('TOY_WATCH_DONE')


def show(sp):
    today = datetime.date.today()
    print('=== 今マップに入っている子供向け企画 ===')
    seen = {}
    for s in sp:
        c = s.get('campaign')
        if not c:
            continue
        k = c.get('title')
        seen.setdefault(k, [0, c])
        seen[k][0] += 1
    for k, (n, c) in seen.items():
        try:
            left = (datetime.date.fromisoformat(c['until']) - today).days
        except Exception:
            left = None
        state = ('あと%d日' % left) if (left is not None and left >= 0) else \
                ('%d日前に終了' % -left if left is not None else '期限不明')
        print('  %-34s %3d店  %s〜%s  %s'
              % (k[:34], n, c.get('fromLabel', '?'), c.get('untilLabel', c.get('until')), state))
    if not seen:
        print('  なし')


def apply(sp):
    n_all = 0
    for cur in CURRENT:
        hit = [s for s in sp if cur['name_match'] in s['name']]
        for s in hit:
            s['campaign'] = dict(cur['campaign'])
        print('  %-10s %3d店に付けた  %s' % (cur['name_match'], len(hit), cur['campaign']['title']))
        n_all += len(hit)
    return n_all


def main():
    if '--watch' in sys.argv:
        return watch()
    sp = json.load(io.open(MAP, encoding='utf-8'))
    if '--apply' in sys.argv:
        n = apply(sp)
        io.open(MAP, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print('書き込んだ(計%d店)' % n)
    show(sp)
    print('TOY_DONE')


if __name__ == '__main__':
    main()
