# -*- coding: utf-8 -*-
"""太宰府市・春日市・大野城市の子連れ向け飲食店32件を青ピン(wish=True / visited=None)で一括登録(2026-10-06)
   候補リスト: data/候補_太宰府春日大野城_20261006.md(ユーザー承認済み。参考枠のねことうさぎのカフェ/Cafe Makuma は対象外)
   内訳: 太宰府12 / 春日10 / 大野城10
   座標: geocoding.jp(住所で取得・11秒間隔)。国土地理院の逆ジオコーダで市区コードが住所の市と一致することを確認済み
   kids: 候補リストに出典がある設備だけ True。根拠が無い項目は null(推測で埋めない)
   要確認だった3件は登録前に再調査:
     - 清香園 大野城店: 2024/5/15 移転。公式(1129.cc)で新住所 大野城市御笠川1-17-10・11:30〜22:00 を確認
       (ホットペッパーは旧住所 山田2-13-38 のまま。食べログ40009662は「移転」表示なので tabelog は付けない)
     - マメロッシュTakata: 食べログ「掲載保留」・ホットペッパー404。ただし予約サイト hamoni は稼働中、
       2026/4のジモティー口コミあり → 登録するが verdict に営業状況要確認と明記。tabelog は付けない
     - うどん大文字: 食べログに「子供可(乳児可)・ベビーカー入店可」を確認 → stroller=True。
       座敷はジモティー口コミ(あり)とRetty(なし)が食い違うので tatami=null、キッズ椅子も口コミのみなので null"""
import io, json, math, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
TL = 'https://tabelog.com/fukuoka/A4003/A400301/%s/'
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}


def K(stroller=None, diaper=None, tatami=None, kidsChair=None):
    return {'stroller': stroller, 'diaper': diaper, 'tatami': tatami, 'kidsChair': kidsChair, 'serveMin': None, 'noise': None}


# (id, 店名, area, city, genre, 住所(福岡県以降), lat, lng, tabelog id, kids, verdict)
SPOTS = [
 # ---- 太宰府市 ----
 ('cafe-coccolo-dazaifu', 'CAFE COCCOLO', '宰府', '太宰府市', '古民家カフェ(イタリアン・フレンチ)', '太宰府市宰府3-3-2', None, None, '40045967',
  K(True, True, True, True),
  '⭐トイレにおむつ替えシート・ベビーカー入店可・2Fに座敷、子供椅子(バンボ/座敷用/テーブル用)・絵本や玩具・お子様メニューあり。'
  '天満宮参道近くの古民家カフェ。火〜木11:00〜17:00/金〜日11:00〜15:00・17:00〜22:00、月曜休。⚠駐車場なし(近隣有料P)。'),
 ('sushiei-dazaifu', '寿し栄', '宰府', '太宰府市', '寿司', '太宰府市宰府3-3-6', None, None, '40001334',
  K(True, None, True, None),
  '⭐座敷個室・2Fに座敷広間、お子様メニュー・子供用食器あり、ベビーカー入店可。'
  '11:00〜14:00・17:00〜21:00、水曜休。駐車場3台+近隣コインP。'),
 ('washoku-bistro-toutou-dazaifu', '和食ビストロ 橙橙', '大佐野', '太宰府市', '創作和食', '太宰府市大佐野2-10-20', None, None, '40001606',
  K(True, None, True, True),
  '⭐子供用イス・キッズメニューあり、ベビーカー可、座敷・個室あり。駐車場25台。'
  '11:30〜15:00・17:30〜22:00、火曜休。'),
 ('mamerossyu-takata-dazaifu', 'マメロッシュTakata', '吉松', '太宰府市', 'イタリアン・カフェ', '太宰府市吉松2-8-17', None, None, None,
  K(True, None, True, None),
  '⭐小上がり席に柵があり、授乳できるベビールームあり。子供可(乳児〜小学生)・お子様メニュー・ベビーカー入店可(食べログ)。'
  'プレートランチ1,000円台。火〜木11:30〜17:00・18:00〜21:00/金土は時間短め、日月休(要確認)。駐車場6台(食べログ)。'
  '⚠食べログは「掲載保留」表示のため営業状況は要確認(予約サイトhamoniは稼働中・2026年4月の口コミあり)。'),
 ('noanoa-dazaifu', 'のあのあ', '坂本', '太宰府市', 'おうちカフェ', '太宰府市坂本1-5-17', None, None, '40041957',
  K(None, None, True, None),
  '⭐全面畳にちゃぶ台、おもちゃあり。キッズプレートあり。'
  '⚠10席のみの小さな店。火〜土11:00〜15:00、日月休。駐車場3台。'),
 ('umenohana-dazaifu-bessou-jinenan', '梅の花 太宰府別荘 自然庵', '宰府', '太宰府市', '豆腐・湯葉懐石', '太宰府市宰府4-4-41', None, None, None,
  K(None, None, True, None),
  '⭐子供メニューあり、座敷・個室あり(いこーよ)。'
  '⚠コース4,500円〜。2026年6〜8月は夏季休止だったので営業日は公式で要確認。11:00〜21:00・年末年始休。駐車場なし(近隣有料P)。'),
 ('yasutake-dazaifu', 'やす武', '宰府', '太宰府市', '梅ヶ枝餅・手打ちそば', '太宰府市宰府2-7-16', None, None, '40000059',
  K(True, None, True, None),
  '⭐子供可(乳児可)・ベビーカー入店可・座敷あり。参道の梅ヶ枝餅とそばの店。8:30〜18:00、不定休。⚠駐車場なし。'),
 ('sukesanudon-dazaifu', '資さんうどん 太宰府店', '向佐野', '太宰府市', 'うどん', '太宰府市向佐野4-12-17', None, None, '40027231',
  K(True, None, True, None),
  '⭐子供可(乳児可)・ベビーカー入店可・座敷あり。24時間営業。駐車場あり。'),
 ('makinoudon-onojo-dazaifu', '牧のうどん 大野城店', '向佐野', '太宰府市', 'うどん', '太宰府市向佐野364-1', None, None, '40004993',
  K(None, None, True, None),
  '⭐子供可・座敷あり。店名は大野城店だが所在は太宰府市。10:00〜23:00、不定休。駐車場あり。'),
 ('sakadonoya-dazaifu', '酒殿屋', '宰府', '太宰府市', 'そば・和食', '太宰府市宰府3-2-40', None, None, '40019269',
  K(None, None, True, None),
  '⭐子供可・座敷36席。太宰府天満宮の境内にあるそば・和食処。9:00〜17:00、不定休。⚠専用駐車場なし。'),
 ('oishichaya-dazaifu', 'お石茶屋', '宰府', '太宰府市', '甘味・うどん', '太宰府市宰府4-7-43', None, None, '40003617',
  K(None, None, True, None),
  '⭐子供可・座敷あり。天満宮裏手の茶屋で梅ヶ枝餅・甘味・うどん。11:00〜16:30、火曜休。⚠専用駐車場なし。'),
 ('meshiya-inokichi-dazaifu', '飯屋 いの吉', '宰府', '太宰府市', '居酒屋(海鮮・肉)', '太宰府市宰府2-1-16', None, None, '40047286',
  K(None, None, True, None),
  '⭐子供可・座敷・掘りごたつあり。⚠夜のみ営業(17:00〜22:00)、水曜+第2・4木曜休。店前に駐車場あり。'),
 # ---- 春日市 ----
 ('3rdcafe-kasuga', '3rd.Cafe(サードカフェ)', '白水ヶ丘', '春日市', 'カフェ', '春日市白水ヶ丘4-7', None, None, None,
  K(True, True, True, None),
  '⭐授乳室・おむつ交換台・座敷席あり(公式)、ベビーカー可・キッズメニューあり(いこーよ)、キッズスペース・キッズプレートあり(2022年時点605円)。'
  'アミティときわ1F。11:00〜22:00(金土〜24:00/水〜18:00)。駐車場9台無料。'),
 ('hassenkaku-kasuga', '八仙閣 春日店', '惣利', '春日市', '中華', '春日市惣利1-65', None, None, '40031692',
  K(None, None, True, True),
  '⭐子供可(乳児可)・おもちゃ付きお子様メニュー・簡易ベッド・子供椅子あり、座敷・掘りごたつ・個室あり。駐車場50台。'
  '11:00〜15:00・17:00〜21:00(土日祝は〜15:30/16:30〜)、不定休。'),
 ('hanakoume-kasuga', '花小梅 春日店', '星見ヶ丘', '春日市', '釜めし・和食', '春日市星見ヶ丘5-7', None, None, '40037805',
  K(True, None, True, None),
  '⭐子供可(乳児可)・お子様メニュー・ベビーカー入店可、座敷・掘りごたつあり。駐車場25台。'
  '平日11:00〜15:30・17:00〜22:00/土日祝11:00〜22:00、不定休。'),
 ('yakiniku-kaya-kasuga', '焼肉 伽耶', '星見ヶ丘', '春日市', '焼肉', '春日市星見ヶ丘3-22', None, None, '40019779',
  K(None, None, True, True),
  '⭐お子様用椅子あり、45人入れる座敷・個室あり。11:30〜15:00・17:00〜22:00、火曜休。駐車場あり。'),
 ('tairyouichiba-narumino-kasuga', '大漁市場 なるみ乃 本店', '白水ヶ丘', '春日市', '海鮮・和食', '春日市白水ヶ丘4-117', None, None, None,
  K(None, None, True, True),
  '⭐お子様連れ歓迎、子供用椅子・取皿・カトラリーあり、座敷・個室4室・掘りごたつあり(ホットペッパー)。'
  '11:30〜14:30・夜16:00/17:00〜21:30頃、火曜休。店裏に駐車場あり。'),
 ('juttokuya-kasuga-shimoshiromizu', '十徳や 春日下白水店', '下白水北', '春日市', '海鮮居酒屋', '春日市下白水北3-85', None, None, None,
  K(None, None, True, None),
  '⭐お子様連れ歓迎、座敷個室・掘りごたつ個室あり(ホットペッパー)。駐車場40台。11:30〜14:30・17:00〜22:00、無休。'),
 ('makinoudon-shiromizu-kasuga', '牧のうどん 白水店', '天神山', '春日市', 'うどん', '春日市天神山1-75', None, None, '40002129',
  K(None, None, True, None),
  '⭐子供可(乳児可)・座敷あり。10:00〜23:00、第3水曜頃休。駐車場あり。'),
 ('sukesanudon-kasuga-shiromizu', '資さんうどん 春日白水店', '上白水', '春日市', 'うどん', '春日市上白水1309-78', None, None, '40035071',
  K(None, None, True, None),
  '⭐子供可・座敷あり。9:00〜翌1:00。駐車場あり。'),
 ('fukufukutei-kasuga', 'そば処 ふくふく亭 春日店', '下白水南', '春日市', 'そば・定食', '春日市下白水南1-147', None, None, '40020558',
  K(None, None, True, None),
  '⭐子供可・座敷・掘りごたつあり。ふくの湯 春日店の館内食事処。9:30〜翌2:00、不定休。駐車場あり。'),
 ('juuwarisoba-sano-kasuga', '十割蕎麦 さ乃', '紅葉ヶ丘西', '春日市', 'そば', '春日市紅葉ヶ丘西2-52', None, None, '40044363',
  K(None, None, None, None),
  '⭐お子様連れ可。広間10席あり(座敷かは未確認)。11:00〜15:00、火曜休。⚠駐車場なし(近隣コインP)。'),
 # ---- 大野城市 ----
 ('seikaen-onojo', '清香園 大野城店', '御笠川', '大野城市', '焼肉', '大野城市御笠川1-17-10', None, None, None,
  K(None, None, None, None),
  '⭐キッズスペース付きの個室が4室(DVDも見られる)、おもちゃ付きお子様セットあり。全席個室・お子様連れ歓迎。'
  '2024年5月に移転(サイクルベースあさひ大野城店の隣)。11:30〜22:00(ランチOS14:30)、無休。駐車場あり。'),
 ('menshosabou-fuku-onojo', '麺処茶房 福', '東大利', '大野城市', 'ラーメン・カフェ', '大野城市東大利3-4-14', None, None, '40065944',
  K(True, True, True, None),
  '⭐キッズスペース・おむつ台あり、子供可(乳児可)・ベビーカー入店可、座敷・掘りごたつあり。駐車場4台。'
  '⚠営業日が変則: 月木金11:30〜15:00(木金は17:00〜21:00も)/土日祝11:30〜21:00、火水+第1・3木曜休。'),
 ('dondontei-onojo', 'どんどん亭 大野城店', '白木原', '大野城市', 'お好み焼き', '大野城市白木原5-37', None, None, '40031798',
  K(None, None, True, None),
  '⭐子供可(乳児可)・お子様メニュー・座敷あり。駐車場あり。平日11:30〜15:30・17:00〜24:00/土日祝11:30〜24:00、元日休。'),
 ('blackcatcafe-shimoori', 'BLACK CAT CAFE', '下大利', '大野城市', 'カフェ', '大野城市下大利1-10-9', None, None, '40062278',
  K(True, None, None, None),
  '⭐子供可(乳児可)・ベビーカー入店可・キッズメニューあり、バリアフリー。西鉄下大利駅構内。10:00〜21:00頃、不定休。⚠駐車場なし。'),
 ('okawaribuffet-nicominho-onojo', 'おかわりビュッフェ ニコミーニョ', '若草', '大野城市', 'ビュッフェ', '大野城市若草3-13-13', None, None, '40049464',
  K(True, None, None, None),
  '⭐子供可(乳児可)・お子様メニュー・ベビーカー入店可。11:30〜15:00(土日祝は夜も)、水曜休。'
  '⚠14席のみ。駐車場3台(ランチ・要電話)。'),
 ('hozumisaryou-onojo', '穂積茶寮', '牛頸', '大野城市', '古民家カフェ・郷土料理', '大野城市牛頸3-17-18', None, None, '40023428',
  K(None, None, True, None),
  '⭐子供可・座敷32席の古民家。駐車場あり。⚠平日10:00〜15:00のみ(土日祝休)。'),
 ('taiwanryouri-fukuhanten-onojo', '台湾料理 福飯店', '山田', '大野城市', '台湾料理', '大野城市山田2-18-45', None, None, '40031065',
  K(True, None, True, None),
  '⭐子供可(乳児可)・ベビーカー入店可・座敷あり。山田吉村コーポ1F。11:00〜15:00・17:00〜23:00、火曜休。駐車場3台。'),
 ('soufuren-kamioori-onojo', '想夫恋 上大利店', '上大利', '大野城市', '焼きそば', '大野城市上大利4-12-23', None, None, '40044278',
  K(True, None, None, None),
  '⭐子供可(乳児可)・ベビーカー入店可。11:00〜22:30(金土〜23:30)。共用駐車場30台。'),
 ('gusto-dazaifu-ic-onojo', 'ガスト 太宰府インター店', '瓦田', '大野城市', 'ファミレス', '大野城市瓦田4-15-34', None, None, '40020056',
  K(None, None, None, None),
  '⭐子供可・家族向けのファミレス。店名は太宰府インター店だが所在は大野城市。7:00〜翌2:00。駐車場あり。'),
 ('udon-daimonji-onojo', 'うどん大文字 大野城店', '山田', '大野城市', 'うどん', '大野城市山田4-2-1', None, None, '40033963',
  K(True, None, None, None),
  '⭐子供可(乳児〜小学生)・ベビーカー入店可(食べログ)。キッズ椅子・キッズ食器・座敷ありとの口コミ(2026年4月)もあるが、'
  'Rettyは座敷なし表記で設備は要確認。平打ち麺の店。駐車場11台+近隣2台。11:00〜15:00・18:00〜21:00(土日祝は通し営業との情報も)、火曜休(要確認)。'),
]

# geocoding.jp の結果(住所で取得。lat/lng の None をここで埋める)
#   全件、国土地理院逆ジオコーダで市区コード一致(太宰府40221/春日40218/大野城40219)を確認
#   ⚠geocoding.jp が needs_to_verify=yes を返したもの(番地精度が怪しい・町丁目レベルでは一致):
#     牧のうどん大野城店(向佐野364-1 は旧地番表記) / 資さん春日白水店 / 麺処茶房 福 / どんどん亭 / ニコミーニョ / 台湾料理 福飯店
#   東大利・山田4 は「3-4-14」形式で lat=0/エラーが返ったので「3丁目4-14」形式で再取得
GEO = {
 'cafe-coccolo-dazaifu': (33.520678, 130.532606),
 'sushiei-dazaifu': (33.520872, 130.532756),
 'washoku-bistro-toutou-dazaifu': (33.501535, 130.496715),
 'mamerossyu-takata-dazaifu': (33.513811, 130.49277),
 'noanoa-dazaifu': (33.514811, 130.505074),
 'umenohana-dazaifu-bessou-jinenan': (33.518626, 130.536185),
 'yasutake-dazaifu': (33.519358, 130.532775),
 'sukesanudon-dazaifu': (33.51053, 130.493829),
 'makinoudon-onojo-dazaifu': (33.509108, 130.496178),          # needs_to_verify=yes
 'sakadonoya-dazaifu': (33.519609, 130.533541),
 'oishichaya-dazaifu': (33.522941, 130.535971),
 'meshiya-inokichi-dazaifu': (33.516978, 130.531219),
 '3rdcafe-kasuga': (33.516961, 130.445287),
 'hassenkaku-kasuga': (33.512903, 130.46912),
 'hanakoume-kasuga': (33.505566, 130.452209),
 'yakiniku-kaya-kasuga': (33.503938, 130.45616),
 'tairyouichiba-narumino-kasuga': (33.517037, 130.442726),
 'juttokuya-kasuga-shimoshiromizu': (33.526892, 130.443894),
 'makinoudon-shiromizu-kasuga': (33.517338, 130.447987),
 'sukesanudon-kasuga-shiromizu': (33.519388, 130.440173),      # needs_to_verify=yes
 'fukufukutei-kasuga': (33.525621, 130.443911),
 'juuwarisoba-sano-kasuga': (33.521501, 130.456247),
 'seikaen-onojo': (33.545264, 130.481178),
 'menshosabou-fuku-onojo': (33.527932, 130.487516),            # needs_to_verify=yes
 'dondontei-onojo': (33.531181, 130.486953),                   # needs_to_verify=yes
 'blackcatcafe-shimoori': (33.522205, 130.489401),
 'okawaribuffet-nicominho-onojo': (33.505685, 130.469444),     # needs_to_verify=yes
 'hozumisaryou-onojo': (33.499009, 130.471606),
 'taiwanryouri-fukuhanten-onojo': (33.545626, 130.474809),     # needs_to_verify=yes
 'soufuren-kamioori-onojo': (33.512968, 130.483083),
 'gusto-dazaifu-ic-onojo': (33.532045, 130.485634),
 'udon-daimonji-onojo': (33.543153, 130.472264),
}
assert len(SPOTS) == 32 and set(GEO) == {x[0] for x in SPOTS}

if __name__ == '__main__':
    shutil.copy(P, P + '.bak_dazaifu_kasuga_onojo')
    s = json.load(io.open(P, encoding='utf-8'))
    ids = {x['id'] for x in s}

    def nn(t):
        t = re.sub(r'[（(].*?[)）]', '', t or '')
        return re.sub(r'[\s　・.]', '', t).lower()
    names = {nn(x.get('name')): x['id'] for x in s}
    added = []
    for (sid, name, area, city, genre, addr, la, ln, tl, kids, verdict) in SPOTS:
        la, ln = GEO[sid]
        if sid in ids:
            print('skip (id exists):', sid); continue
        if nn(name) in names:
            print('skip (same name):', name, '->', names[nn(name)]); continue
        near = [x for x in s if x.get('lat') and x.get('lng') and
                math.hypot((x['lat'] - la) * 111, (x['lng'] - ln) * 111 * math.cos(math.radians(la))) < 0.03]
        if near:
            print('  note: 30m以内に既存', name, '->', [(x['id'], x['name']) for x in near])
        s.append({'id': sid, 'name': name, 'area': area, 'city': city, 'pref': '福岡県', 'genre': genre,
                  'address': '福岡県' + addr, 'lat': la, 'lng': ln, 'visited': None, 'with': 'family',
                  'kids': kids, 'verdict': verdict, 'video': dict(VIDEO0), 'thumb': None,
                  'wish': True, 'category': 'gourmet', 'tabelog': (TL % tl) if tl else None})
        added.append(sid)
    allids = [x['id'] for x in s]; assert len(allids) == len(set(allids))
    assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
    io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
    print('added', len(added))
    print(' '.join(added))
