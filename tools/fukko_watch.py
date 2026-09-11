# -*- coding: utf-8 -*-
"""九州ふっこう応援割(2026-10-01 宿泊分〜)の対象宿を、じゃらんのページから検出して spots.json に書く。

■ なぜこれが要るか
  この事業は**宿ごとに参加登録する方式**で、同じ県でも参加していない宿は対象外になる。
  しかも**対象施設の公式リストは公表されない**(2026-09-11時点)。
  旅行会社の解説にも「予約サイトの通常プランを応援割の対象と判断することはできない」と明記がある。
  → 判定できる唯一の手がかりが「その宿のページに応援割プランが並んでいるか」なので、それを見に行く。

⚠**じゃらんは Shift_JIS/CP932**。utf-8 で decode(errors='replace') すると全部化けて
  キーワードが0件になり「対象なし」と誤判定する(2026-09-11に踏んだ)。必ず encoding を総当たりする。

■ 安全設計(monetize.py と同じ思想)
  ・**確証が取れた宿にだけ書く**。取れなければ何も書かない(未確認のまま)。
    誤って「対象」と出すと、割引が効かない宿に予約させてしまうため
  ・既に fukko がある宿は、--recheck を付けない限り触らない
  ・--apply を付けない限りドライラン
  ・アクセスは4秒間隔(相手サイトへの配慮。monetize.py と同じ)

使い方:
    python tools/fukko_watch.py                      # 全宿をドライランで確認
    python tools/fukko_watch.py --apply              # 書き込む
    python tools/fukko_watch.py --ids kamenoi-aso --apply
    python tools/fukko_watch.py --limit 20 --apply   # 20件だけ(様子見)
    python tools/fukko_watch.py --recheck --apply    # 既に付いている宿も見直す
"""
import json, io, os, re, sys, time, shutil, urllib.request, urllib.error
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'data', 'spots.json')

KYUSHU = {'福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県'}
RATE = {'熊本県': 60, '鹿児島県': 60,
        '福岡県': 50, '佐賀県': 50, '長崎県': 50, '大分県': 50, '宮崎県': 50}
WAIT = 4.0
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# 応援割プランの見出しに使われる語。表記ゆれを広めに拾う
HIT = re.compile(r'(ふっこう応援割|復興応援割|九州ふっこう|ふっこう割|全国旅行支援[^。]{0,6}九州)')
# 「対象外」「終了しました」等が近くにある場合は誤検出なので弾く
NEG = re.compile(r'(対象外|終了しました|受付を終了|販売を終了|対象ではありません)')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept-Language': 'ja,en;q=0.8'})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ('utf-8', 'shift_jis', 'cp932', 'euc-jp'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('cp932', 'replace')


def judge(html):
    """(対象か, 根拠の抜粋) を返す。判断できなければ (None, 理由)"""
    txt = re.sub(r'<[^>]+>', ' ', html)
    txt = re.sub(r'\s+', ' ', txt)
    m = HIT.search(txt)
    if not m:
        return None, '応援割の記載なし'
    around = txt[max(0, m.start() - 60):m.end() + 80]
    if NEG.search(around):
        return False, '「%s」と書かれている: %s' % (NEG.search(around).group(1), around[:90])
    return True, around[:110]


def main():
    a = sys.argv[1:]
    apply_ = '--apply' in a
    recheck = '--recheck' in a
    ids = None
    if '--ids' in a:
        i = a.index('--ids') + 1
        ids = []
        while i < len(a) and not a[i].startswith('--'):
            ids.append(a[i]); i += 1
    limit = None
    if '--limit' in a:
        limit = int(a[a.index('--limit') + 1])

    spots = json.load(io.open(P, encoding='utf-8'))
    tg = [s for s in spots
          if s.get('booking') and s.get('pref') in KYUSHU
          and (ids is None or s['id'] in ids)
          and (recheck or not s.get('fukko'))]
    if limit:
        tg = tg[:limit]

    print('=== 九州ふっこう応援割の対象判定 %s ===' % ('(書き込み)' if apply_ else '(ドライラン)'))
    print('対象候補: %d件 / じゃらんリンクを持つ九州の宿 %d件'
          % (len(tg), sum(1 for s in spots if s.get('booking') and s.get('pref') in KYUSHU)))
    print()
    ok = ng = err = 0
    today = date.today().isoformat()
    for i, s in enumerate(tg):
        if i:
            time.sleep(WAIT)
        # プラン名は宿トップに全部は出ないので /plan/ も見る(応援割プランは専用プランとして並ぶ)
        html = ''
        try:
            for u in (s['booking'].rstrip('/') + '/plan/', s['booking']):
                html += fetch(u)
                time.sleep(1.5)
        except Exception as e:
            if not html:
                print(' ! %-22s %-26s 取得できず: %s' % (s['id'][:22], s['name'][:26], e))
                err += 1
                continue
        hit, why = judge(html)
        if hit is True:
            ok += 1
            print(' ○ %-22s %-26s %d%%OFF  %s' % (s['id'][:22], s['name'][:26], RATE[s['pref']], why[:60]))
            if apply_:
                s['fukko'] = {'checked': today, 'url': s['booking']}
        else:
            ng += 1
            print(' × %-22s %-26s %s' % (s['id'][:22], s['name'][:26], why[:60]))

    print()
    print('対象と確認: %d / 確認できず: %d / 取得失敗: %d' % (ok, ng, err))
    if apply_ and ok:
        shutil.copy(P, P + '.bak_fukko')
        io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
        print('spots.json に書き込みました(バックアップ: .bak_fukko)')
        print('※ build_pages.py を回してから push すること')
    elif apply_:
        print('書き込むものがありませんでした')
    if not apply_:
        print('※ ドライランです。問題なければ --apply を付けて再実行してください')


if __name__ == '__main__':
    main()
