# -*- coding: utf-8 -*-
"""ホットペッパーグルメ グルメサーチAPIで、spots.json の飲食店に店舗ページURLを埋める。

    エンドポイント : https://webservice.recruit.co.jp/hotpepper/gourmet/v1/
    APIキー取得    : https://webservice.recruit.co.jp/register/ (メールアドレスだけ・無料)

使い方:
    set HOTPEPPER_KEY=xxxxxxxxxxxx
    python fill_hotpepper.py            # ドライラン(書き込まない。照合結果だけ出す)
    python fill_hotpepper.py --write    # spots.json に hotpepper フィールドを書き込む
    python fill_hotpepper.py --limit 30 # 件数を絞って試す

やり方:
  緯度経度(range=1=300m)で近所の店を引き、**店名の一致で確定する**。
  座標だけ・店名だけのどちらか一方では別店を掴むので、必ず両方で照合する。
  同名チェーンが多いので、名前が曖昧なものは**採用せず保留**にして目視に回す。

規約まわり(2026-09-02時点で確認):
  ・APIの利用規約に「APIを利用しているページには**API毎に指定されたクレジットを記載**」とある。
    データを反映したら map/index.html のフッターにクレジットを出すこと(--write が警告する)。
  ・広告主(リクルート)の提携条件に「**クーポン詳細画面への直接リンク**」の禁止がある。
    リンク先は urls.pc(店舗ページ)だけにする。クーポンページのURLは入れない。
  ・「毎日情報更新」を求められているので、閉店・移転に追随するため定期的に再実行する。
"""
import os, sys, io, json, time, urllib.parse, urllib.request, unicodedata, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'data', 'spots.json')
EP = 'https://webservice.recruit.co.jp/hotpepper/gourmet/v1/'
KEY = os.environ.get('HOTPEPPER_KEY', '').strip()
WAIT = 1.0          # 1秒に1回まで。相手のサーバに迷惑をかけない


def norm(s):
    """店名の表記ゆれを寄せる。全角半角・カタカナ/ひらがな・記号・空白を落とす。"""
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)
    return re.sub(r'[\s・･ー\-()（）「」【】\'"’”,.、。/]', '', s)


def api(**kw):
    kw.update(key=KEY, format='json')
    url = EP + '?' + urllib.parse.urlencode(kw)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))['results']


def find(spot):
    """近所の店を引いて店名で確定する。戻り値 (URL, 店名, 判定理由)。"""
    try:
        res = api(lat=spot['lat'], lng=spot['lng'], range=1, count=100)
    except Exception as e:
        return None, None, 'APIエラー: %s' % e
    shops = res.get('shop') or []
    if not shops:
        return None, None, '300m以内に掲載店なし'

    want = norm(spot['name'])
    exact = [s for s in shops if norm(s['name']) == want]
    if len(exact) == 1:
        return exact[0]['urls']['pc'], exact[0]['name'], '店名が完全一致'
    if len(exact) > 1:
        return None, None, '同名が%d件(要目視)' % len(exact)

    part = [s for s in shops if want and (want in norm(s['name']) or norm(s['name']) in want)]
    if len(part) == 1:
        return part[0]['urls']['pc'], part[0]['name'], '店名が部分一致'
    if len(part) > 1:
        return None, None, '部分一致が%d件(要目視)' % len(part)
    return None, None, '近所に%d件あるが名前が合わない' % len(shops)


def main():
    if not KEY:
        raise SystemExit('環境変数 HOTPEPPER_KEY が未設定です。\n'
                         'キーは https://webservice.recruit.co.jp/register/ で無料発行できます。')
    write = '--write' in sys.argv
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    sp = json.load(io.open(P, encoding='utf-8'))
    # 飲食として出るスポットのうち、まだURLが無いものだけ
    todo = [x for x in sp
            if 'gourmet' in (x.get('cats') or ([x.get('category')] if x.get('category') else ['gourmet']))
            or not x.get('category')]
    todo = [x for x in todo if x.get('category') not in ('play', 'onsen') or x.get('cats')]
    todo = [x for x in todo if not x.get('hotpepper') and x.get('lat') and x.get('lng')]
    if limit:
        todo = todo[:limit]

    print('対象 %d件 / %s' % (len(todo), '書き込みモード' if write else 'ドライラン'))
    print('-' * 74)
    hit = miss = 0
    for i, x in enumerate(todo, 1):
        url, name, why = find(x)
        if url:
            hit += 1
            mark = 'OK '
            if write:
                x['hotpepper'] = url
        else:
            miss += 1
            mark = '-- '
        print('%s%3d/%d %-26s %s' % (mark, i, len(todo), x['name'][:26],
                                     ('→ %s' % name) if url else why))
        sys.stdout.flush()
        time.sleep(WAIT)

    print('-' * 74)
    print('一致 %d件 / 未確定 %d件' % (hit, miss))
    if write and hit:
        io.open(P, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print('spots.json に書き込みました。')
        print()
        print('★ APIの規約でクレジット表記が要ります。map/index.html のフッターに')
        print('  「Powered by ホットペッパー Webサービス」+ https://webservice.recruit.co.jp/ へのリンク')
        print('  を入れてください(未対応ならこのあと追加します)。')
    elif not write:
        print('※書き込んでいません。よければ --write を付けて再実行してください。')


if __name__ == '__main__':
    main()
