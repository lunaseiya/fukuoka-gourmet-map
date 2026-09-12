# -*- coding: utf-8 -*-
"""商業施設の公式イベントページから「週末に開催されている子連れ向けイベント」を集める。
週1回の『週末イベント◯選』投稿のネタ出し用。

■ なぜ商業施設を主軸にするか(2026-09-12 実測)
  イオンモール系は **HTMLが構造化されていて会期がそのまま取れる**:
    <li class="result-box event"><a href="/event/<uuid>">
      <p class="name">タイトル</p><p class="info">2026/09/01 (火) - 2026/09/29 (火)</p>
  さらに埋め込みJSONに eventStartAt / eventEndAt が ISO で入っている。
  イオンモール社(<slug>-aeonmall.com)とイオン九州(<slug>.aeon-kyushu.info)で**同じ構造**。
  福岡県6館で**週189件**取れる(筑紫野39/福岡37/大牟田37/福津33/直方29/香椎浜14)。

■ 設計の要点: ボトルネックは収集ではなく選別
  12選に対して189件=25倍あるので、**除外ルールで落とすほうが効く**。
  2026-09-11の県公式87件の検証で、除外ルール(87件)がスコアリング(19件)を完全に包含し、
  スコアリングだけで拾えるものは0件だった。だから「まず除外、次に子連れ語で並べる」。

■ 出力
  一覧で候補を出すだけ。**開催時間・料金・館内の会場・対象年齢は一覧ページに無い**ので、
  `--detail` を付けると**採用分だけ**個別ページを開いて取る(189件全部取るのは無駄)。

使い方:
    python tools/mall_event_watch.py                      # 次の土日を対象に12件
    python tools/mall_event_watch.py --from 2026-09-19 --to 2026-09-21
    python tools/mall_event_watch.py --n 12 --detail      # 採用分の詳細も取る
    python tools/mall_event_watch.py --all                # 除外されたものも見る(ルール調整用)
"""
import argparse, html, io, json, os, re, sys, time, urllib.error, urllib.request
from datetime import date, datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'data', '_週末イベント候補.json')
UA = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
      'Accept-Language': 'ja'}
WAIT = 2.0

# (表示名, 市区, イベント一覧のURL)
#  ⚠**パスが2系統ある**(2026-09-12に踏んだ):
#     イオンモール社 <slug>-aeonmall.com は **/news/event**
#     イオン九州     <slug>.aeon-kyushu.info は **/event**
#   片方に揃えると、もう片方が黙って0件になる(HTTP 200 で空ページが返る)
#   2026-09-12 に実測して生きている館だけ載せている。
#   ⚠八幡東/鹿児島/長崎/佐賀大和/下関/三光 は <slug>-aeonmall.com がDNSで引けなかった(slug違い)。
#     熊本・宇城はページは200だが result-box が無い。いずれも要調査
MALLS = [
    ('イオンモール福岡',   '糟屋郡粕屋町', 'https://fukuoka-aeonmall.com/news/event'),
    ('イオンモール香椎浜', '福岡市東区',   'https://kashiihama.aeon-kyushu.info/event'),
    ('イオンモール福津',   '福津市',       'https://fukutsu-aeonmall.com/news/event'),
    ('イオンモール筑紫野', '筑紫野市',     'https://chikushino-aeonmall.com/news/event'),
    ('イオンモール直方',   '直方市',       'https://nogata-aeonmall.com/news/event'),
    ('イオンモール大牟田', '大牟田市',     'https://omuta-aeonmall.com/news/event'),
]

# ───────── 除外ルール(これで落とす。実測189件の中身から作った) ─────────
#  販促・物販・相談会・金融・車関係は「おでかけ」にならない
DROP = re.compile(
    r'受注会|展示販売|展示会|即売|買取|査定|下取り|相談会|無料相談|見学会|内覧|'
    r'ガソリン|洗車|車検|タイヤ|保険|リフォーム|不動産|住宅|墓|仏壇|'
    r'求人|採用|アルバイト|パート募集|'
    r'決算|歳末|感謝祭|周年.{0,6}(セール|キャンペーン|お得)|クリアランス|'
    # ⚠「2,000ポイントプレゼントキャンペーン」が {0,4} では届かず生き残り、
    #   カルーセルの7枚目に載って「イベントとは呼べない」と指摘された(2026-09-13)
    r'クレジット|カード.{0,8}(入会|募集|キャンペーン)|ポイント.{0,8}(アップ|キャンペーン|プレゼント|進呈)|'
    r'アプリ.{0,8}(登録|ダウンロード|キャンペーン)|抽選で.{0,8}プレゼント|'
    r'お買い上げ|お買い物.{0,6}(キャンペーン|で)|税込\d|円以上|'
    # 同日に追加で見つかった販促(「Oisix定期便のご案内」「500円OFFクーポンがもらえる！」)
    r'定期便|ご案内$|のご案内|勧誘|試供品|サンプル配布|お試しセット|'
    r'クーポン.{0,8}(もらえる|プレゼント|進呈|配布|付き)|[0-9]+円?OFF|[0-9]+%OFF|'
    r'スクラッチ|福引|くじ引き|三角くじ|レシート|'
    # ⚠「プレゼントキャンペーン」「大抽選会」は ポイント.{0,8} では届かない位置に出る。
    #   単独の語として落とす。あわせて KIDS から「抽選」を外した(販促を加点していた)
    r'プレゼントキャンペーン|抽選会|大抽選|応募券|先着プレゼント|'
    # 「手作り品販売」は体験ではなく物販。「手作り」が体験系+9で拾われていた
    r'手作り品販売|ハンドメイド販売|作品販売|手づくり品販売|'
    r'夜得|お得に|記念キャンペーン|オープニング記念|リニューアル|営業再開|'

    r'補聴器|メガネ|眼鏡|宝石|毛皮|着物|振袖|呉服|寝具|布団|印鑑|'
    r'健康チェック|測定会|骨密度|血管|肌診断|'
    r'チラシ|配布中|お知らせ|営業時間|臨時休業|駐車場.{0,6}(変更|工事)|'
    # ⚠「◯◯体験販売会」「ネスカフェ ドルチェ グスト 体験会」のような**販促の体験会**が
    #   「体験」で子連れ度+6を稼いで上位に来ていた(2026-09-12に踏んだ)。会が付く形は落とす
    r'販売会|体験会|試飲|試食会|モデルハウス|商談')

# 除外語があっても**強い子連れ語**があれば残す。「親子体験会」を落とさないための逃げ道
SAVE = re.compile(r'こども|子ども|子供|キッズ|親子|お子さま|お子様|小学生|幼児|ベビー')

# ⚠**SAVE で救ってはいけない区分**【2026-09-13に踏んだ】
#   「親子で学ぶ韓国・釜山4日間」が"親子"で救われて12選に残っていた。
#   旅行商品・求人・金融は子連れ語が付いていても「おでかけ情報」ではない。
#   「ツアー」単独では落とさない(館内の「わくわくトレインツアー」が消える)
DROP_HARD = re.compile(r'[0-9]日間|海外(?:デビュー|旅行|研修)|宿泊プラン|旅行(?:商品|代金|券)|'
                       r'バスツアー|添乗員|募集人員|説明会|内覧会|モデル募集|オーディション|'
                       # 教室・塾の入会勧誘(「幼児教室コペル…新しい学びを始めませんか？」)
                       r'幼児教室|学習塾|英会話|そろばん教室|体験レッスン|無料体験|'
                       r'入会|入園|入学|生徒募集|受講')

# ───────── 子連れ度(並べ替えに使う。落とすためには使わない) ─────────
KIDS = [
    (6, r'こども|子ども|子供|キッズ|親子|ファミリー|お子さま|お子様'),
    # ★**体験系を最優先に**【2026-09-13ユーザー確定「マルシェや販売系より体験のほうが強い」】
    #   それまで マルシェ(+4) が積み上がって「森のマルシェ」が29点で最高になり、
    #   「魔法の美術館」(体験型)より上に来ていた
    (9, r'ワークショップ|体験|参加型|工作|つくろう|つくり|作ろう|手づくり|手作り|'
        r'粘土|キャンドル|スライム|ペイント|絵付け|陶芸|はんこ|アクセサリー|'
        r'つかまえ|さがせ|探せ|さわれる|乗れる|試乗|なりきり'),
    # ★「遊べる」「◯◯館」系を足した【2026-09-13ユーザー指摘】
    #   「【BOSS E・ZO FUKUOKA】魔法の美術館」(リード=見て触れて遊ぶ！超体験型)が
    #   子連れ語を持たないためスコア6止まりで12枠に入れなかった。
    #   体験施設は子連れの行き先そのものなので加点する
    (5, r'遊べる|遊ぶ|あそべる|あそぼう|さわれる|触れ|自由に'),
    (4, r'美術館|博物館|科学館|水族館|動物園|植物園|天文台|プラネタリウム|こども館|児童館'),
    (5, r'ふれあい|撮影会|握手|ショー|ステージ|ヒーロー|戦隊|仮面ライダー|プリキュア|'
        r'ポケモン|ちいかわ|サンリオ|アンパンマン|しまじろう|ドゲンジャーズ|ドラえもん'),
    (4, r'無料|参加費.{0,4}無料|入場無料'),
    # ★**規模の大きい伝統行事・大型催事**を強く加点【2026-09-13ユーザー指摘】
    #   「筥崎宮 放生会」(博多三大祭り)が「祭」+4しか付かず14点で12枠に入れなかった。
    #   スコアに"規模"の概念が無かったのが原因
    # +7では足りなかった。放生会(21点)が陶芸教室(25点)に負けて12選に入れなかったので
    # **+12** にした。博多三大祭り級は福岡の「おでかけ」で最も強いコンテンツ
    (12, r'大祭|例大祭|三大祭|放生会|山笠|どんたく|くんち|おくんち|花火大会|'
         r'大祭典|大花火|灯明|燈籠|神幸|祇園'),
    (5, r'フェスタ|大会$|選手権'),
    (4, r'縁日|まつり|祭|フェス|恐竜|動物|水族|昆虫|科学|プラネタリウム|'
        r'トレイン|電車|ミニ.{0,2}(SL|新幹線)|ふわふわ|バルーン|風船|工事車両|はたらく車'),
    # マルシェ・市・物販は「買い物」寄りなので弱くする(0では拾えなくなるので1)
    (1, r'マルシェ|マーケット|市$|フェア|物産|販売|出店|グルメ'),
    (3, r'敬老の日|こどもの日|ハロウィン|クリスマス|七夕|お正月|節分|ひなまつり'),
    (3, r'スタンプラリー|ラリー|クイズ|宝探し'),
    (2, r'展'),
]


def norm_title(t):
    """同じ全国キャンペーンを束ねるための正規化。
    ⚠館ごとに表記がぶれる。「ポケモンしんかラリー第2弾」/「『ポケモンしんかラリー』第2弾
      スタート！！」/「ポケモンしんかラリー」が別件として3枠を占めていた(2026-09-12に踏んだ)"""
    t = re.sub(r'[\s　]+', '', t)
    # ⚠**カタカナの長音「ー」を消してはいけない**。消すと「スタート」→「スタト」になって
    #   下の末尾除去が効かず、「ポケモンしんかラリー第2弾」と
    #   「『ポケモンしんかラリー』第2弾スタート！！」が別件のまま2枠を占める(2026-09-13に踏んだ)
    t = re.sub(r'[『』「」【】（）()《》\[\]♪！!？?・､、。,.~〜\-–—]', '', t)
    t = re.sub(r'第\d+弾|vol\.?\d+|Vol\.?\d+', '', t)
    t = re.sub(r'(スタート|開催中|開催決定|開催|のお知らせ|好評|新登場|登場)+$', '', t)
    return t[:22]


def run_days(span):
    s, e = span
    return 999 if s is None else (e - s).days + 1


def fetch(u):
    raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
    for e in ('utf-8', 'shift_jis', 'cp932'):
        try:
            return raw.decode(e)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def txt(s):
    # ⚠html.unescape を通す。通さないと「ピカチュウ&amp;イーブイ」のまま出る(2026-09-12に踏んだ)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s))).strip()


BLK = re.compile(r'<li class="result-box event"><a href="(/event/[^"]+)"'
                 r'([\s\S]{0,2500}?)<p class="name">([\s\S]*?)</p>'
                 r'[\s\S]{0,600}?<p class="info">([\s\S]*?)</p>')
IMG = re.compile(r'<img src="([^"]+)"')
YMD = re.compile(r'(\d{4})/(\d{1,2})/(\d{1,2})')


def parse_span(info):
    """<p class="info"> から (開始, 終了) を date で返す。
    「毎日」「常時」は通年扱いで (None, None) を返す"""
    ds = [date(int(a), int(b), int(c)) for a, b, c in YMD.findall(info)]
    if not ds:
        return (None, None) if re.search(r'毎日|常時|通年|随時', info) else (False, False)
    return (ds[0], ds[-1] if len(ds) > 1 else ds[0])


def overlaps(span, f, t):
    s, e = span
    if s is False:
        return False            # 会期が読めないものは落とす(推測しない)
    if s is None:
        return True             # 毎日開催
    return s <= t and e >= f


def kids_score(title):
    # ⚠**空白を潰してから当てる**。「ワーク ショップ」のように全角/半角スペースが
    #   混ざっているタイトルが実在し、そのままだと語にヒットしない(2026-09-12に踏んだ)
    t = re.sub(r'[\s　]+', '', title)
    return sum(w for w, p in KIDS if re.search(p, t))


def collect():
    rows = []
    for name, city, url in MALLS:
        base = re.match(r'https?://[^/]+', url).group(0)
        try:
            h = fetch(url)
        except Exception as ex:
            print('  ! %s 取得失敗 (%s)' % (name, type(ex).__name__), file=sys.stderr)
            continue
        seen = set()
        for m in BLK.finditer(h):
            href, t, info = m.group(1), txt(m.group(3)), txt(m.group(4))
            if href in seen or not t:
                continue
            seen.add(href)
            im = IMG.search(m.group(2))
            rows.append({'title': t, 'info': info, 'mall': name, 'city': city,
                         'url': base + href, 'span': parse_span(info),
                         'poster': html.unescape(im.group(1)) if im else None,
                         'kyushu': 'aeon-kyushu.info' in base})
        print('  %-20s %3d件' % (name, len(seen)), file=sys.stderr)
        time.sleep(WAIT)
    return rows


TD = re.compile(r'<td[^>]*>([\s\S]{0,40}?)</td>\s*<td[^>]*>([\s\S]{0,200}?)</td>')


def detail(r):
    """個別ページから時間・場所・料金を取る(採用分だけ呼ぶ)。

    ⚠**イオン九州の館しか自動で取れない**(2026-09-12実測):
      ・イオン九州(<slug>.aeon-kyushu.info) … 詳細ページに
          <td>日程</td><td>2026/09/19 (土) - 2026/09/20 (日)</td>
          <td>時間</td><td>10:30～17:30</td><td>場所</td><td>1階 セントラルコート</td>
        のテーブルがあるので確実に取れる
      ・イオンモール社(<slug>-aeonmall.com) … 詳細ページは**完全にJS描画**で、
        静的HTMLにイベント本文が1文字も無い(タイトルすら出ない)。一覧の埋め込みJSONにも
        title/eventStartAt/eventEndAt/eventMediaFile1 しか無く**時間・場所・料金は入っていない**。
        → ここは「要確認」として**ポスター画像のURLを出す**。会期以外はポスターを見て埋める
      ⚠以前は本文から最初の「HH:MM〜HH:MM」を拾っていたが、それは**モールの営業時間
        (10:00-21:00)**で、全イベントが同じ時間になっていた。誤情報なのでやめた"""
    if not r.get('kyushu'):
        return {'need_check': '時間・場所はJS描画のため未取得。ポスターか個別ページで確認'}
    try:
        h = fetch(r['url'])
    except Exception:
        return {}
    d = {}
    for k, v in TD.findall(h):
        k, v = txt(k), txt(v)
        if k in ('時間', '開催時間'):
            d['time'] = v
        elif k in ('場所', '会場'):
            d['place'] = v
        elif k in ('料金', '参加費', '費用'):
            d['price'] = v
        elif k in ('先着人数', '定員', '対象'):
            d.setdefault('note', []).append('%s:%s' % (k, v))
    if isinstance(d.get('note'), list):
        d['note'] = ' / '.join(d['note'])
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='f', help='対象開始 YYYY-MM-DD (既定=次の土曜)')
    ap.add_argument('--to', dest='t', help='対象終了 YYYY-MM-DD (既定=次の日曜)')
    ap.add_argument('--n', type=int, default=12)
    ap.add_argument('--detail', action='store_true', help='採用分の個別ページも開く')
    ap.add_argument('--all', action='store_true', help='除外分も表示(ルール調整用)')
    a = ap.parse_args()

    if a.f:
        f = datetime.strptime(a.f, '%Y-%m-%d').date()
    else:
        today = date.today()
        f = today + timedelta(days=(5 - today.weekday()) % 7 or 7)   # 次の土曜
    t = datetime.strptime(a.t, '%Y-%m-%d').date() if a.t else f + timedelta(days=1)
    print('対象期間: %s 〜 %s' % (f, t), file=sys.stderr)
    print('収集中...', file=sys.stderr)
    rows = collect()
    print('  ── 生データ %d件' % len(rows), file=sys.stderr)

    inwin = [r for r in rows if overlaps(r['span'], f, t)]
    def drop_it(r):
        t = re.sub(r'[\s　]+', '', r['title'])
        return bool(DROP.search(t)) and not SAVE.search(t)
    dropped = [r for r in inwin if drop_it(r)]
    keep = [r for r in inwin if not drop_it(r)]
    print('  会期が対象期間にかかる: %d件 → 除外ルールで %d件落として %d件'
          % (len(inwin), len(dropped), len(keep)), file=sys.stderr)

    # 同じ全国キャンペーンが複数館に出るのでタイトルで束ねる
    grp = {}
    for r in keep:
        k = norm_title(r['title'])
        grp.setdefault(k, []).append(r)
    merged = []
    for k, v in grp.items():
        r = dict(v[0])
        r['malls'] = sorted({x['mall'] for x in v})
        # 会期が短いものほど「その週末に行く理由」になるので加点する
        #   (ゆめはぴの12選も8件が週末限定・4件が長期開催だった)
        d = run_days(r['span'])
        r['days'] = d
        r['score'] = kids_score(r['title']) + (4 if d <= 3 else 2 if d <= 9 else 0)
        # 複数館でやっている全国キャンペーンは「どこでも行ける」ので少し加点
        if len(r['malls']) >= 3:
            r['score'] += 2
        merged.append(r)
    merged.sort(key=lambda r: (-r['score'], run_days(r['span'])))

    top = merged[:a.n]
    if a.detail:
        print('  採用%d件の個別ページを開いています...' % len(top), file=sys.stderr)
        for r in top:
            r.update(detail(r))
            time.sleep(WAIT)

    def span_str(r):
        s, e = r['span']
        if s is None:
            return '毎日'
        w = '月火水木金土日'
        return ('%d/%d(%s)' % (s.month, s.day, w[s.weekday()]) if s == e else
                '%d/%d(%s)〜%d/%d(%s)' % (s.month, s.day, w[s.weekday()],
                                          e.month, e.day, w[e.weekday()]))

    print()
    print('=== %s〜%s の週末イベント %d選 (候補%d件から) ===' % (f, t, len(top), len(merged)))
    for i, r in enumerate(top, 1):
        ml = r['malls'][0] if len(r['malls']) == 1 else '%s ほか%d館' % (r['malls'][0], len(r['malls']) - 1)
        print('%2d. %s' % (i, r['title']))
        print('    📍%s(%s)  📅%s  スコア%d' % (ml, r['city'], span_str(r), r['score']))
        for k, lb in (('time', '🕐'), ('price', '¥'), ('place', '📌'), ('note', 'ℹ')):
            if r.get(k):
                print('    %s %s' % (lb, r[k]))
        if r.get('need_check'):
            print('    ⚠ %s' % r['need_check'])
            if r.get('poster'):
                print('    🖼 %s' % r['poster'])
        print('    %s' % r['url'])
    if a.all:
        print()
        print('--- 除外ルールで落とした %d件 ---' % len(dropped))
        for r in dropped:
            print('  x %s (%s)' % (r['title'][:50], r['mall']))
        print()
        print('--- 残ったが下位だった %d件 ---' % max(0, len(merged) - len(top)))
        for r in merged[len(top):]:
            print('  - [%d] %s (%s)' % (r['score'], r['title'][:46], r['malls'][0]))

    for r in merged:
        s, e = r['span']
        r['span'] = [s.isoformat() if s else None, e.isoformat() if e else None]
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps(
        {'from': f.isoformat(), 'to': t.isoformat(), 'events': merged},
        ensure_ascii=False, indent=1))
    print()
    print('→ %s に %d件保存' % (os.path.normpath(OUT), len(merged)))


if __name__ == '__main__':
    main()
