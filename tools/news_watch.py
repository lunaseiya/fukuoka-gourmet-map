"""速報ウォッチ(2026-11-17 ユーザー確定「ニュース速報回はやる価値ありそう・いかにキャッチして自動でレビュー」)

成城石井 九州初出店は PR TIMES 14:00 → LINEニュース 15:48 → こちらの投稿 17:10 だった。
LINEニュースの元は PR TIMES なので、PR TIMES の全件RSSを直接見張れば約2時間先に気づける。

  python tools/news_watch.py          … 新着の候補を出す(yobimizu.py からも呼ばれる。既読は data/速報_既読.json)
  python tools/news_watch.py --quiet  … タスクスケジューラ用(受け箱に貯めて、強い候補はWindowsの通知)
  python tools/news_watch.py --all    … 既読も含めて、いまRSSにある候補を全部出す(基準の調整用)

源: ① PR TIMES 全件RSS(https://prtimes.jp/index.rdf ・約200件=直近2〜3時間ぶん → 1時間ごとに回せば取りこぼさない)
    ② Googleニュース(自治体・新聞発のもの。PR TIMES に出ないもの)
点数: 下の SCORE。SHOW_MIN 以上を「速報候補」として出す。最終判断(誰でも知っている店か・素材があるか)は Claude が見て決める。
"""
import os, re, sys, json, time, random, html, datetime
from urllib.parse import quote
sys.path.insert(0, os.path.dirname(__file__))
if '--quiet' in sys.argv:
    # pythonw(タスクスケジューラ)は stdout が無く、print で落ちる(LastTaskResult=1)。ログへ逃がす
    sys.stdout = sys.stderr = open(os.path.join(os.path.dirname(__file__), '..', 'data', '速報_実行ログ.txt'), 'a', encoding='utf-8')
    print(f'--- {datetime.datetime.now():%Y-%m-%d %H:%M} ---')
import opening_watch as ow   # fetch を借りる
import closing_watch as cw   # 閉店の日付読み(when_of)・除外語・見納めリスト(closings.json)

D = os.path.join(os.path.dirname(__file__), '..', 'data')
SEEN = os.path.join(D, '速報_既読.json')
LOG = os.path.join(D, '速報候補.json')
PLACES = os.path.join(D, '速報_場所素材.json')
INBOX = os.path.join(D, '速報_受け箱.txt')   # --quiet(タスクスケジューラ)の結果を貯め、次の手動/定期確認で出して空にする

# 必須: 福岡の地名 + 開業・閉店系の語
AREA_RE = re.compile(r'福岡|博多|天神|北九州|小倉|久留米|糸島|太宰府|筑紫野|春日市|大野城|宗像|福津|古賀|新宮|粕屋|志免|飯塚|大牟田|柳川|行橋|九州')
OPEN_RE = re.compile(r'出店|オープン|開業|上陸|新店|開店|誕生|グランドオープン|リニューアル|移転|進出|閉店|閉館|営業終了|建て替え|開園|開館|買収|子会社化|グループ入り|全株式|傘下入り|事業承継')
# ↑ 買収系は 2026-11-23 追加: 博多一幸舎の買収(11/13発表)を拾えなかった。開店/閉店の語が無い記事は入口で落ちていた
# 買収の記事は「買い手がどういう会社か」を必ず表示する(ユーザー 2026-11-23: 本業が金融なので、ファンド・投資会社が絡む話は動画にしない。飲食業どうしなら可)
MA_RE = re.compile(r'買収|子会社化|グループ入り|全株式|傘下入り|事業承継')
FUND_RE = re.compile(r'ファンド|投資会社|投資顧問|キャピタル|Capital|CAPITAL|パートナーズ|Partners|プライベート・?エクイティ|PE|アセット|インベストメント|Investment|証券|銀行|リース')
FOOD_BUYER_RE = re.compile(r'すかいらーく|ゼンショー|コロワイド|吉野家|トリドール|ロイヤル|クリエイト・レストランツ|物語コーポレーション|力の源|一蘭|JR九州|西鉄|ピエトロ|外食|飲食')

# 除外: 開業ニュースではないもの
DROP_RE = re.compile(r'採用|決算|人事|求人|セミナー|説明会|ウェビナー|資金調達|業務提携|株主|募集|キャンペーン|プレゼント|抽選|ポイント|'
                     r'クーポン|調査|アンケート|ランキング発表|受賞|就任|お詫び|オンライン|EC|通販|ふるさと納税|物件|分譲|マンション|賃貸|オフィス')
# 九州でも福岡以外の県が主役なら弱い
OTHER_PREF_RE = re.compile(r'熊本|佐賀|長崎|大分|宮崎|鹿児島|沖縄|山口')

SCORE = [
    (r'九州初|福岡初|九州1号店|福岡1号店|九州一号店|初出店|初上陸|九州上陸|福岡上陸', 5),
    (r'天神|博多駅|アミュ|キャナル|ららぽーと|マリノア|ソラリア|大丸|岩田屋|PayPayドーム|イオンモール|ワン・?フクオカ|ONE FUKUOKA|天神地下街|博多マルイ|KITTE|博多バスターミナル|デイトス|DEITOS|博多阪急|新天町|ゆめタウン博多|マークイズ|MARK IS|香椎|アイランドシティ|照葉|新宮|古賀|和白|千早|粕屋|国道3号|3号線', 3),
    (r'カフェ|レストラン|スイーツ|ベーカリー|パン|スーパー|バーガー|ラーメン|らーめん|拉麺|うどん|油そば|焼肉|寿司|ドーナツ|食堂|グルメ|フード', 2),
    (r'こども|子ども|キッズ|親子|ファミリー|遊び場|公園|ポケモン|サンリオ|任天堂|ディズニー', 2),
    (r'20\d\d年\s*\d+月|\d+月\d+日|春|夏|秋|冬', 1),
    (r'閉店|閉館|営業終了', 2),   # 見納めも速報になる
    (r'買収|子会社化|グループ入り|全株式|傘下入り', 4),   # 地元の店が買われる話(資さん・ShinShin・一幸舎)
]
SHOW_MIN = 5
GNEWS_Q = ['福岡 (初出店 OR 九州初 OR 福岡初 OR 初上陸)', '博多 (オープン OR 開業 OR 出店)', '天神 (オープン OR 開業 OR 出店)',
           # なくなる店(さよならシリーズ)。新しく開く店があれば消える店もある(2026-11-17 ユーザー)
           # 地元(東区・新宮・古賀・香椎)はロードサイドの小さな新店が多い。PR TIMES に出ない店はブログ・ローカル紙で拾う
           #   (2026-11-17 バーガーキング3号新宮店・うちだ屋新宮店を取りこぼした)
           '(新宮 OR 古賀 OR 香椎 OR 和白 OR 千早 OR 粕屋) (オープン OR 開店 OR 出店 OR 新店)',
           '(福岡 OR 博多) (買収 OR 子会社化 OR グループ入り) (ラーメン OR うどん OR 飲食 OR 外食 OR 老舗)',
           '福岡 (閉店 OR 閉館 OR 営業終了)', '天神 (閉店 OR 閉館 OR 営業終了)', '博多 (閉店 OR 閉館 OR 営業終了)']
CLOSE_RE = re.compile(r'閉店|閉館|閉園|営業終了|営業を終了|幕を閉じ|見納め|ラストデー|建て替え|建替')
# 閉店の記事は1媒体だけのことが多い。地元の報道なら1媒体でも新しい話として扱う
LOCAL_SRC_RE = re.compile(r'LOG FUKUOKA|ゆるなご|いこーよ|ふくおかナビ|西日本新聞|ファンファン福岡|号外NET|JC-NET|TNC|KBC|RKB|FBS|TVQ|NHK|福岡経済|フクリパ|データ・マックス|みんなの経済新聞')


def jload(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


def jsave(p, v):
    open(p, 'w', encoding='utf-8').write(json.dumps(v, ensure_ascii=False, indent=1) + '\n')


def tag(it, t):
    m = re.search(r'<%s[^>]*>(.*?)</%s>' % (t, t), it, re.S)
    return html.unescape(m.group(1)).strip() if m else ''


def score(text):
    # 成城石井の見出しは「九州・福岡に“初”出店！」= 引用符を外さないと初出店に当たらない
    text = re.sub(r'[“”"「」『』]', '', text)
    if not AREA_RE.search(text) or not OPEN_RE.search(text) or DROP_RE.search(text):
        return 0, []
    s, why = 0, []
    for pat, p in SCORE:
        m = re.search(pat, text)
        if m:
            s += p
            why.append(m.group(0))
    # 「九州」しか地名が無く、九州初でもない → 福岡の話とは限らない
    if not re.search(r'福岡|博多|天神|北九州|小倉|久留米|糸島|太宰府|新宮|古賀|香椎|粕屋|糟屋', text) and '九州初' not in text and '九州上陸' not in text:
        s -= 3
    if OTHER_PREF_RE.search(text) and not re.search(r'福岡|博多|天神', text):
        s -= 4
    if CLOSE_RE.search(text) and cw.DROP_RE.search(text):   # 病院・パチンコ・解体ショー等は見納めにならない
        return 0, []
    return s, why


def places(text):
    """手元に素材がある場所(data/速報_場所素材.json のキー)"""
    return [k for k, v in jload(PLACES, {}).items() if re.search(v.get('match', k), text)]


def from_prtimes():
    x = ow.fetch('https://prtimes.jp/index.rdf')
    out = []
    for it in re.findall(r'<item .*?</item>', x or '', re.S):
        title, desc = tag(it, 'title'), tag(it, 'description')
        out.append(dict(src='PR TIMES', title=title, corp=tag(it, 'dc:corp'), url=tag(it, 'link'),
                        at=tag(it, 'dc:date')[:16].replace('T', ' '), text=title + ' ' + desc))
    return out


def from_gnews():
    out = []
    for q in GNEWS_Q:
        url = 'https://news.google.com/rss/search?q=%s&hl=ja&gl=JP&ceid=JP:ja' % quote(q + ' when:1d')
        x = None
        for wait in (0, 45):   # 連続で叩くと429(closing_watch と同じ)。1回だけ待って取り直す
            time.sleep(wait)
            x = ow.fetch(url)
            if x:
                break
        time.sleep(random.uniform(6, 9))
        for it in re.findall(r'<item>(.*?)</item>', x or '', re.S):
            title = re.sub(r'\s+-\s+[^-]+$', '', tag(it, 'title'))
            try:
                from email.utils import parsedate_to_datetime
                at = parsedate_to_datetime(tag(it, 'pubDate')).astimezone().strftime('%Y-%m-%d %H:%M')
            except Exception:
                at = ''
            out.append(dict(src='Google:' + tag(it, 'source'), title=title, corp='', url=tag(it, 'link'), at=at, text=title))
    return out


GENERIC_RE = re.compile(r'スーパー|ラーメン|カフェ|ショップ|ストア|専門店|直営店|九州初|福岡初|初出店|初上陸|初進出|出店|オープン|開業|上陸|福岡|博多駅?|天神|アミュプラザ|20\d\d年|来年|春|新店舗|画像|速報|ニュース|[\W\d]')


def same_story(a, b):
    """同じ話題か = 地名・定型句を抜いた見出しに、共通の4文字以上(「成城石井」が4文字)がある(成城石井は1日で9媒体に出た)"""
    from difflib import SequenceMatcher
    x, y = GENERIC_RE.sub('', a), GENERIC_RE.sub('', b)
    m = SequenceMatcher(None, x, y).find_longest_match(0, len(x), 0, len(y))
    return m.size >= 4


def cluster(rows):
    """同じ話題を1件にまとめ、載った媒体の数を点に足す(多くの媒体が拾う=規模の目安)"""
    out = []
    for e in sorted(rows, key=lambda e: e['at'] or '9'):
        for g in out:
            if same_story(g['title'], e['title']):
                g['media'].append(e['src'])
                break
        else:
            e['media'] = [e['src']]
            out.append(e)
    for g in out:
        g['score'] += min(len(g['media']) - 1, 4)
    return out


def on_map(title):
    """見出しの店名(カタカナ・英字3文字以上/「」の中身)がマップに既にあるか。
    2026-11-17: Googleニュースが「カインズが九州初進出！福岡・新宮に3月オープン」(数年前の記事)を当日付で返した。
    カインズ 福岡新宮店はマップにある = 古い記事の再掲と分かる"""
    global _NAMES
    if '_NAMES' not in globals():
        _NAMES = [s['name'] for s in jload(os.path.join(D, 'spots.json'), [])]
    names = _NAMES
    words = set(re.findall(r'「([^」]{2,20})」', title) + re.findall(r'[ァ-ヶー]{3,}|[A-Za-z][A-Za-z&. ]{2,}[A-Za-z]', title))
    words = {w.strip() for w in words if len(w.strip()) >= 4 and not re.fullmatch(r'オープン|ニューオープン|グランドオープン|リニューアル|スーパー|ラーメン|カフェ|ショップ|ストア|フード|グルメ|スイーツ|ベーカリー|レストラン|ステーキ|ビストロ|サウナ|スパ|ホテル|パン|ニュース|デザイン|.*(アミュ|イオン|ららぽーと|キャナル|パルコ|マルイ|ソラリア|大丸|岩田屋|公園|駅|モール|プラザ|シティ|ビル).*', w.strip())}
    # 店名はマップ側の名前の「頭」と一致したときだけ(「マリノア」が日産マリノア店に、「オランダ」が別店に当たった)
    hit = [(w, n) for w in words for n in names if n.lower().startswith(w.lower())]
    return hit[0] if hit else None


def main():
    show_all = '--all' in sys.argv
    seen = set(jload(SEEN, []))
    log = jload(LOG, [])
    rows, keys = [], set()
    for e in from_prtimes() + from_gnews():
        key = re.sub(r'\W', '', e['title'])[:30]
        if key in keys:
            continue
        keys.add(key)
        # ウォーカープラスの「＜画像8 / 8＞」は過去記事の写真ページが当日付で出てくるだけ(カインズ・キットカットで実測)
        if re.search(r'画像\s*\d+\s*/\s*\d+', e['title']):
            continue
        s, why = score(e['text'])
        if s < SHOW_MIN - 4 or (not show_all and (e['url'] in seen or key in seen)):
            continue
        hit = on_map(e['title'])
        if hit and not CLOSE_RE.search(e['title']):
            s += 4   # 行ったことのある店(マップにある店)の新店は、見てくれる人が知っている
            why.append('マップの店「%s」' % hit[1])
        if s < SHOW_MIN:
            continue
        if MA_RE.search(e['text']):
            if FUND_RE.search(e['text']):
                why.insert(0, '【買収・買い手=ファンド/金融系 → 動画にしない(報告だけ)】')
            elif FOOD_BUYER_RE.search(e['text']):
                why.insert(0, '【買収・買い手=飲食などの事業会社 → 動画にしてよい】')
            else:
                why.insert(0, '【買収・買い手の種類は未判定 → 記事で買い手を確認してから】')
        e.update(map=hit, score=s, why=why, places=places(e['text']), found=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))
        rows.append(e)
        seen.update([e['url'], key])
    rows = cluster(rows)
    # 直近14日に一度出した話題は続報なので候補にしない(成城石井が翌日も別媒体で出続ける)
    since = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    old = [g['title'] for g in log if g.get('found', '') >= since]
    if not show_all:
        rows = [e for e in rows if not any(same_story(t, e['title']) for t in old)]
    # 確からしさ: PR TIMES(当日のリリース)か、Googleで2媒体以上 = 新しい話。Googleで1媒体だけ = 古い記事の再掲が混ざる
    #   (2026-11-17 ユーザー指摘: カインズ新宮もウルフギャング(グランドハイアット)も前からある)
    today = datetime.date.today().isoformat()
    for e in rows:
        e['fresh'] = any(m.endswith('PR TIMES') for m in e['media']) or len(e['media']) >= 2
        e['close'] = bool(CLOSE_RE.search(e['title']))
        if e['close']:
            e['when'], e['when_iso'] = cw.when_of(e['title'])
            # 閉店日が未来 or 地元の報道 = 新しい話(過去の日付なら、もう閉まっている)
            if e['when_iso']:
                e['fresh'] = e['when_iso'] >= today
            elif LOCAL_SRC_RE.search(' '.join(e['media'])):
                e['fresh'] = True
        # マップに既にある店の名前 = 古い記事の再掲か、知っている店の新店のどちらか。
        # PR TIMES・地元の報道なら新店(2026-11-17 ざいとん博多バスターミナル店を取りこぼした)、それ以外は要確認
        if e['map'] and not (any(m.endswith('PR TIMES') for m in e['media']) or LOCAL_SRC_RE.search(' '.join(e['media']))):
            e['fresh'] = False
    rows.sort(key=lambda e: -e['score'])
    if not show_all:
        jsave(SEEN, sorted(seen))
        log += [{k: v for k, v in e.items() if k != 'text'} for e in rows]
        jsave(LOG, log[-500:])
    if not show_all:
        add_closings([e for e in rows if e['close'] and e['fresh']])
    main_rows = [e for e in rows if e['fresh']]
    weak = [e for e in rows if not e['fresh']]
    out = []
    for e in main_rows:
        if e['close']:
            out.append(f"[見納め{e['score']}点] {e['at']} {e['src']} 閉店日:{e['when'] or '未読(記事で確認)'}\n    {e['title'][:90]}\n    {e['url']}")
            continue
        pl = ' / 素材あり: ' + '・'.join(e['places']) if e['places'] else ' / 場所の素材なし'
        more = f" ほか{len(e['media']) - 1}媒体" if len(e['media']) > 1 else ''
        out.append(f"[{e['score']}点] {e['at']} {e['src']}{more} {e['corp']}\n    {e['title'][:90]}\n    {'・'.join(e['why'])}{pl}\n    {e['url']}")
    for e in weak:
        why = f"マップに既存「{e['map'][1]}」" if e['map'] else '1媒体のみ'
        out.append(f"  (要確認・{why}) {e['src']} {e['title'][:70]}")
    if '--quiet' in sys.argv:
        # タスクスケジューラから(セッションが閉じていても回る)。受け箱に貯め、強い候補はWindowsの通知を出す
        if out:
            with open(INBOX, 'a', encoding='utf-8') as f:
                f.write(f"--- {datetime.datetime.now():%Y-%m-%d %H:%M} ---\n" + '\n'.join(out) + '\n')
        if main_rows:
            toast('速報候補 %d件' % len(main_rows), main_rows[0]['title'][:60])
        # 見納めウォッチの全件巡回(60日・15エリア・2〜3分)は1日1回
        if not os.path.exists(cw.OUT_JSON) or time.time() - os.path.getmtime(cw.OUT_JSON) > 20 * 3600:
            import subprocess
            sys.stdout.flush()
            subprocess.run([sys.executable.replace('pythonw', 'python'), '-X', 'utf8', cw.__file__],
                           stdout=sys.stdout, stderr=sys.stdout, creationflags=0x08000000)   # CREATE_NO_WINDOW
            # モール公式の「閉店のお知らせ」も1日1回(tools/mall_close_watch.py)
            subprocess.run([sys.executable.replace('pythonw', 'python'), '-X', 'utf8',
                            os.path.join(os.path.dirname(__file__), 'mall_close_watch.py'), '--quiet'],
                           stdout=sys.stdout, stderr=sys.stdout, creationflags=0x08000000)
        return
    # 受け箱(スケジューラが拾ったぶん)を先に出して空にする
    box = open(INBOX, encoding='utf-8').read().strip() if os.path.exists(INBOX) else ''
    if box:
        print('== 受け箱(タスクスケジューラが拾った候補) ==\n' + box)
        if not show_all:
            os.remove(INBOX)
    print(f'== 速報候補(新着): {len(main_rows)}件 ==')
    print('\n'.join(out))


def add_closings(rows):
    """新しい閉店ニュースを見納めリスト(closings.json / 見納めリスト.txt)に足す。
    撮影リスト(shoot_conditions.py → closing_watch --due)に必ず載る = 撮りどきを逃さない"""
    if not rows:
        return
    items = jload(cw.OUT_JSON, [])
    known = {x['name'] for x in items}
    for e in rows:
        name = re.sub(r'\s+-\s+[^-]+$', '', e['title'])
        if name in known or any(same_story(name, k) for k in known):
            continue
        items.append(dict(name=name, when=e['when'], when_iso=e['when_iso'], area='速報ウォッチ', url=e['url'],
                          src=e['src'].replace('Google:', ''), pub=(e['at'] or '')[:10]))
    json.dump(items, open(cw.OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    real = sys.stdout
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')   # show() は一覧を print するので黙らせる
    try:
        cw.show(items)
    finally:
        sys.stdout = real


def toast(title, body):
    """Windows 10 のトースト通知(追加モジュール不要)"""
    import subprocess
    esc = lambda t: html.escape(t).replace("'", "''")
    ps = ("[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]>$null;"
          "$x=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
          f"$t=$x.GetElementsByTagName('text');$t.Item(0).InnerText='{esc(title)}';$t.Item(1).InnerText='{esc(body)}';"
          "$n=[Windows.UI.Notifications.ToastNotification]::new($x);"
          r"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe').Show($n)")
    subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True)


if __name__ == '__main__':
    main()
