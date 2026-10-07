# -*- coding: utf-8 -*-
"""アーバンモール新宮中央(新規・親・赤ピン)と館内の子スポットを一括登録(2026-10-07)。
   ユーザー決定(2026-10-07):
     - 親 urbanmallshinguchuo = 訪問済み・時期不明 → wish=False / visited=None
     - 牛角 新宮店 / 神戸クック・ワールドビュッフェ = 訪問済み・時期不明 → 赤ピン(wish=False / visited=None)。
       どちらも既存スポット(gyukakushingu / worldbuffetshingu)なので**更新**し、in=親 を付ける
     - それ以外のテナント = 青ピン(wish=True)。既存の八仙閣(hassenkakushingu)は in=親 を付けて更新
   ユーザーの実体験(2026-10-07 伝聞):
     - 牛角: 個室あり / 子供向けの焼肉メニューがあり子供は安めに食べられる / 冷房がやや効きすぎていることがある
     - ワールドビュッフェ: とても広い店内 / アイスなどデザートも食べ放題
   根拠(すべて 2026-10-07 取得):
     - 所在地・開業: 出店ウォッチ https://shutten-watch.com/kyushu/7938 (第一交通産業、2019/10/12〜順次開業、16テナント予定)
     - 駐車場: ダイイチパーク News Release 2019/11/1 https://daiichipark.0152.jp/img/pdf/20191101.pdf
       (227台ゲート式・入庫90分無料・8-20時60分200円・店舗利用で追加サービス)。
       ゲオ公式店舗ページは「駐車場158台」→ 台数は食い違うので(要確認)
     - 店舗の駐車サービス: 食べログ ワールドビュッフェ/ヴィチーノ「最大4時間無料」(ヴィチーノはバー式駐車場に限り・駐車券提示)
     - ワールドビュッフェ料金: 公式 https://www.kobecook-wb.jp/shop/detail.php?shinguchuo
       (大人 平日ランチ1,540/土日祝ランチ2,090/平日ディナー1,760/土日祝ディナー2,310、
        小学生 平日990・土日祝1,100、キッズ(3歳〜未就学)平日550・土日祝660、3歳未満無料。税込)
       品数・スイーツ: ぐるなび店舗公式 https://fbzm802.gorp.jp/ (100種類以上・ソフトクリーム・スイーツ約30種食べ放題・278席・個室1室)
       子連れ: 食べログ 40053064(ベビーカー入店可・お子様の同伴大歓迎・平日時間無制限/土日祝90分制)
     - 牛角: 公式 お子様向け https://www.gyukaku.ne.jp/menu/menu-kids.php (キッズプレート528円・キッズカレープレート528円 等)
       公式 お気軽コース https://www.gyukaku.ne.jp/menu/50item-course.php (食べ放題 小学生未満無料・小学生半額、3,058円〜)
       食べログ 40053257(子供可(乳児・未就学児・小学生)・お子様メニュー・個室(20〜30人)・掘りごたつ・ソファー席・TEL 092-963-2911・
       平日17:00〜23:00/土日祝16:00〜23:00)
     - 八仙閣: 食べログ 40052981(子供可・お子様メニュー・ベビーカー入店可・座敷あり)
     - ヴィチーノ: 食べログ 40054152(4-10-3 アーバンモール新宮中央・オムツ交換台1台・キッズプレート(小学生まで)・ベビーカー入店可・
       11:00〜22:00・TEL 092-405-3056)
     - ゲオ: 公式 https://geo-online.co.jp/store/40532/ (9:00〜24:00・年中無休・ゲーム/トレカ販売・TEL 092-941-7522)
   登録しないもの: 長崎亭(国道3号線沿いへ移転済み)/ セカンドストリート新宮中央店(公式店舗検索に出ず営業確認できず)/
     ローソン・FIT365・医療モール(子連れの用途が薄い)
   座標: geocoding.jp「福岡県糟屋郡新宮町緑ケ浜4丁目10-5」→ 33.71288,130.447318(既存3店と同値・新宮中央駅の西約230mで妥当)。
     子は親と共有(館内)。"""
import io, json, math, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_urbanmall_shinguchuo')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}
names = {x['name'] for x in s}
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
added, updated, skipped = [], [], []

PID = 'urbanmallshinguchuo'
LAT, LNG = 33.71288, 130.447318
ADDR = '福岡県糟屋郡新宮町緑ケ浜4-10-5'
AREA = '緑ケ浜(アーバンモール新宮中央)'

# ---------- 近傍の既存スポット(300m)を表示して重複を目視 ----------
for x in s:
    if x.get('lat') is None or x.get('lng') is None:
        continue
    d = math.hypot((x['lat'] - LAT) * 111, (x['lng'] - LNG) * 111 * math.cos(math.radians(LAT)))
    if d < 0.3:
        print('near %.0fm' % (d * 1000), x['id'], x['name'])

# ---------- 親 ----------
if PID in by:
    skipped.append((PID, 'id重複'))
elif 'アーバンモール新宮中央' in names:
    skipped.append((PID, '同名重複'))
else:
    p = {'id': PID, 'name': 'アーバンモール新宮中央', 'area': AREA, 'city': '糟屋郡新宮町', 'pref': '福岡県',
         'genre': 'ショッピングモール', 'lat': LAT, 'lng': LNG, 'address': ADDR,
         'visited': None, 'with': 'family',
         'kids': {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
         'verdict': '以前訪問(時期不明)。JR新宮中央駅西口から徒歩数分、第一交通産業がミツカン工場跡地に開発し2019年開業した平屋の商業ゾーン。'
                    '⭐飲食は神戸クック・ワールドビュッフェ(食べ放題)・牛角・八仙閣・ヴィチーノ(石窯ピザ)と家族向けがそろう。'
                    'ほかにゲオ・ローソン・FIT365・医療モール。'
                    '駐車場はゲート式(入庫90分無料、以降8〜20時は60分200円。ワールドビュッフェ・ヴィチーノは利用で最大4時間無料)。'
                    '⚠台数は227台(2019年の運営会社発表)と158台の表記があり要確認。モール共用のおむつ替え・授乳室は確認できず'
                    '(ヴィチーノ店内にオムツ交換台1台)。',
         'video': dict(VIDEO0), 'thumb': None, 'wish': False, 'category': 'gourmet'}
    s.append(p); by[PID] = p; names.add(p['name']); added.append(PID)


def upd(sid, **kw):
    x = by.get(sid)
    if not x:
        skipped.append((sid, '既存が見つからない')); return
    for k, v in kw.items():
        if k == 'kids':
            if x.get('kids') is None:
                x['kids'] = {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None,
                             'serveMin': None, 'noise': None}
            x['kids'].update(v)
        else:
            x[k] = v
    x['in'] = PID
    updated.append(sid)


# ---------- 既存の更新(赤ピン化 2件 + 八仙閣) ----------
upd('gyukakushingu', wish=False, visited=None,
    kids={'kidsMenu': True},
    ages=['baby', 'toddler', 'kids'], ages_src='auto',
    tabelog='https://tabelog.com/fukuoka/A4001/A400201/40053257/',
    verdict='以前訪問(時期不明)。⭐個室あり(実体験)。食べログでは個室(20〜30人)・掘りごたつ・ソファー席。'
            '⭐子供向けの焼肉メニューがあり子供は安めに食べられる(実体験)。公式ではキッズプレート・キッズカレープレート各528円など、'
            '食べ放題は小学生未満無料・小学生半額(大人3,058円〜・税込)。食べログでは乳児・未就学児・小学生とも可。'
            '⚠冷房がやや効きすぎていることがあるので、子供に羽織るものがあると安心(実体験)。'
            '平日17:00〜23:00/土日祝16:00〜23:00(LO22:30)。TEL 092-963-2911。新宮中央駅西口から徒歩数分。')
upd('worldbuffetshingu', wish=False, visited=None,
    kids={'stroller': True},
    ages=['baby', 'toddler', 'kids'], ages_src='auto',
    tabelog='https://tabelog.com/fukuoka/A4001/A400201/40053064/',
    web='https://www.kobecook-wb.jp/shop/detail.php?shinguchuo',
    verdict='以前訪問(時期不明)。⭐とても広い店内(実体験・278席、個室あり)。⭐和洋中の世界の料理100種類以上に、'
            'ソフトクリームなどスイーツ約30種類まで食べ放題(アイスなどデザートも込み・実体験)。'
            '⭐子供料金: 小学生 平日990円/土日祝1,100円、3歳〜未就学 平日550円/土日祝660円、3歳未満無料'
            '(大人 平日ランチ1,540円〜・税込/公式)。ベビーカー入店可・お子様の同伴大歓迎(食べログ)。'
            '平日は時間無制限、土日祝は時間制(食べログ)。ランチ11:00〜16:00。駐車場は最大4時間無料。TEL 092-410-8207。')
upd('hassenkakushingu',
    kids={'stroller': True, 'tatami': True, 'kidsMenu': True},
    tabelog='https://tabelog.com/fukuoka/A4001/A400201/40052981/',
    verdict='福岡の老舗中華「八仙閣」の新宮店。アーバンモール新宮中央内。⭐キッズメニューあり・ベビーカー入店可・座敷あり'
            '(食べログ)。平日ランチ11:00〜15:00 / ディナー17:00〜21:00、土日祝はランチ11:00〜15:30 / ディナー16:30〜21:00。'
            'TEL 092-692-1186。⚠未訪問。')


# ---------- 新規の子(青ピン) ----------
def child(sid, name, genre, category, verdict, kids=None, ages=None, web=None, tabelog=None, addr=ADDR):
    if sid in by:
        skipped.append((sid, 'id重複')); return
    if name in names:
        skipped.append((sid, '同名重複: ' + name)); return
    x = {'id': sid, 'name': name, 'area': AREA, 'city': '糟屋郡新宮町', 'pref': '福岡県', 'genre': genre,
         'lat': LAT, 'lng': LNG, 'address': addr, 'visited': None, 'with': 'family', 'kids': kids, 'verdict': verdict,
         'video': dict(VIDEO0), 'thumb': None, 'wish': True, 'category': category, 'in': PID}
    if ages:
        x['ages'] = ages; x['ages_src'] = 'auto'
    if web:
        x['web'] = web
    if tabelog:
        x['tabelog'] = tabelog
    s.append(x); by[sid] = x; names.add(name); added.append(sid)


child('umshingu-vicino', 'ヴィチーノ レストラン・カフェ', 'イタリアン・ピザ', 'gourmet',
      'アーバンモール新宮中央の石窯ナポリピッツァの店(旧ピッツェリア ダ ヴィチーノ)。⭐オムツ交換台1台・ベビーカー入店可・'
      'キッズプレートあり(小学生まで)(食べログ)。ランチはピザにサラダ・ドルチェ・ドリンク付き。持ち帰り可。'
      '11:00〜22:00・不定休。TEL 092-405-3056。モールのバー式駐車場は最大4時間無料(駐車券を提示)。⚠未訪問。',
      kids={'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None, 'kidsMenu': True},
      ages=['baby', 'toddler', 'kids'],
      web='https://www.sereno.co.jp/restaurant',
      tabelog='https://tabelog.com/fukuoka/A4001/A400201/40054152/', addr='福岡県糟屋郡新宮町緑ケ浜4-10-3')
child('umshingu-geo', 'ゲオ アーバンモール新宮中央店', 'ゲーム・レンタル', 'play',
      'アーバンモール新宮中央のゲオ。ゲーム・トレカの新品/中古販売、DVD・コミックのレンタル。遊戯王の公認イベントも開催(公式)。'
      '9:00〜24:00・年中無休。TEL 092-941-7522。',
      web='https://geo-online.co.jp/store/40532/', addr='福岡県糟屋郡新宮町緑ケ浜4-10-1')

# ================= 整合チェック =================
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids)), 'id重複'
assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())], 'wish=Trueに動画'
assert all(re.fullmatch(r'[A-Za-z0-9-]+', i) for i in added)
dn = {}
for x in s:
    dn[x['name']] = dn.get(x['name'], 0) + 1
assert all(dn[by[i]['name']] == 1 for i in added + updated), '同名重複'
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('total', len(s), 'added', added, 'updated', updated)
print('skipped', skipped)
print('children of', PID, [x['id'] for x in s if x.get('in') == PID])
