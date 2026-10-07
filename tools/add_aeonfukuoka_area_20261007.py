# -*- coding: utf-8 -*-
"""イオンモール福岡(粕屋町酒殿192-1)周辺の館外の子連れ向け飲食店19件を青ピン(wish=True / visited=None)で一括登録(2026-10-07)
   候補リスト: data/候補_イオンモール福岡周辺_20261007.md(ユーザー事前承認済み。館内テナントは aeonmallfukuoka の子なので対象外)
   内訳: 志免町南里12 / 粕屋町(長者原・仲原・大隈)7
   kids: 出典(食べログ「お子様連れ」「空間・設備」欄/ホットペッパー)に明記された設備だけ True。根拠が無い項目は null
   ages: 食べログに「乳児可、未就学児可、小学生可」と明記された店だけ baby/toddler/kids(ages_src=auto)
   重複で見送り: 串カツ田中 福岡志免店(kushikatsutanaka-shime)/ くら寿司 志免店 / はま寿司 福岡志免店 / 焼肉きんぐ 福岡志免店 ほか"""
import io, json, math, os, re, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
TL = 'https://tabelog.com/fukuoka/A4003/A400303/%s/'
VIDEO0 = {'youtube': None, 'tiktok': None, 'instagram': None}
ALL = ['baby', 'toddler', 'kids']


def K(stroller=None, diaper=None, tatami=None, kidsChair=None):
    return {'stroller': stroller, 'diaper': diaper, 'tatami': tatami, 'kidsChair': kidsChair, 'serveMin': None, 'noise': None}


# (id, 店名, area, city, genre, 住所(福岡県以降), tabelog id, kids, ages, verdict)
SPOTS = [
 # ---- 志免町 南里(モールの南西〜西 0.4〜1.5km) ----
 ('yuzuan-shime', 'ゆず庵 福岡志免店', '南里', '糟屋郡志免町', 'しゃぶしゃぶ・寿司食べ放題', '糟屋郡志免町大字南里字ヒサゲ19-1', '40053144',
  K(True, None, None, None), ALL,
  '⭐子供可(乳児〜小学生)・お子様メニューあり・ベビーカー入店可(食べログ)。しゃぶしゃぶ・寿司の食べ放題で136席。'
  'イオンモール福岡から約400m。11:00〜24:00(LO22:00)。駐車場あり。'),
 ('marugenramen-shime', '丸源ラーメン 福岡志免店', '南里', '糟屋郡志免町', 'ラーメン', '糟屋郡志免町大字南里字ヒサゲ20-1', '40053145',
  K(True, None, None, None), ALL,
  '⭐子供可(乳児〜小学生)・お子様メニューあり・ベビーカー入店可(食べログ)。101席。'
  'イオンモール福岡から約400m。10:30〜翌1:00。駐車場あり。'),
 ('sukesanudon-nanri-shime', '資さんうどん 南里店', '南里', '糟屋郡志免町', 'うどん', '糟屋郡志免町大字南里24-5', '40027491',
  K(None, None, True, None), None,
  '⭐子供可・座敷あり(食べログ)。イオンモール福岡から約400m。9:00〜翌1:00。駐車場あり。'),
 ('nerikomiudon-gon-shime', '練り込みうどん「権」', '南里', '糟屋郡志免町', 'うどん', '糟屋郡志免町大字南里34-4', '40003413',
  K(None, None, True, None), None,
  '⭐子供可・座敷あり・席が広い(食べログ)。イオンモール福岡から約500m。'
  '11:30〜15:30・18:00〜20:00(日曜は11:30〜16:00のみ)、木曜休。駐車場あり。'),
 ('hassenkaku-shime', '八仙閣 志免店', '南里', '糟屋郡志免町', '中華', '糟屋郡志免町南里36-1', '40006480',
  K(True, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・キッズメニューあり・ベビーカー入店可、掘りごたつ・個室(4〜30人)あり、バリアフリー(食べログ)。100席。'
  'イオンモール福岡から約500m。平日11:00〜15:00・17:00〜21:00/土日祝11:00〜15:30・16:30〜21:00、不定休。駐車場あり。'),
 ('seikaen-shime', '清香園 志免店', '南里', '糟屋郡志免町', '焼肉', '糟屋郡志免町南里63-2', '40046442',
  K(None, None, True, None), None,
  '⭐全室個室で、キッズスペース付きの席あり(電話予約で確保)。お子様連れ歓迎・座敷個室あり(ホットペッパー)。お子様セットあり(個人ブログ)。'
  'イオンモール福岡から約600m。11:30〜15:00・17:00〜22:00、無休。駐車場あり。'),
 ('joyfull-shime', 'ジョイフル 志免店', '南里', '糟屋郡志免町', 'ファミレス', '糟屋郡志免町大字南里7番2', '40016305',
  K(True, None, None, None), ALL,
  '⭐子供可(乳児〜小学生)・お子様メニューあり・ベビーカー入店可(食べログ)。キッズメニューあり(公式)。'
  'イオンモール福岡から約500m。24時間営業。駐車場あり。'),
 ('cocohare-shime', 'かくれ酒場ココハレ', '南里', '糟屋郡志免町', '居酒屋', '糟屋郡志免町南里1-6-1', '40059038',
  K(True, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・ベビーカー入店可。掘りごたつ式の座卓席20席があり、子連れはこの席を予約する人が多い(食べログ)。'
  '⚠夜のみ17:00〜24:00、月曜休。駐車場9台。'),
 ('marutomiramen-shime', 'まる富ラーメン', '南里', '糟屋郡志免町', 'ラーメン', '糟屋郡志免町南里3-4-38', '40052379',
  K(None, None, True, None), None,
  '⭐子供可・小上がり12席あり(食べログ)。火〜土11:00〜14:00・18:00〜23:00/日祝11:00〜21:00、月曜休。駐車場8台。'),
 ('torifuji-shime', '溶岩焼と焼鳥の店 鶏富士', '南里', '糟屋郡志免町', '鳥料理・焼き鳥', '糟屋郡志免町南里6-20-20', '40052227',
  K(True, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・お子様メニューあり・ベビーカー入店可、座敷30席(半個室)・掘りごたつ25席(食べログ)。'
  '昼12:00〜16:00(月曜除く)・夜18:00〜24:00、火曜休。駐車場4台。'),
 ('chingu-shime', '韓国家庭料理 焼肉 ちんぐ', '南里', '糟屋郡志免町', '韓国料理・焼肉', '糟屋郡志免町南里6-20-20 三陽ビル1F', '40030372',
  K(None, None, None, None), None,
  '⭐子供可(食べログ)。ランチ11:30〜14:00・夜17:30〜23:00、火曜休。駐車場4〜5台。'),
 ('torikawahonpo-shime', '博多焼鳥 とりかわ本舗 志免店', '南里', '糟屋郡志免町', '焼き鳥', '糟屋郡志免町南里7-7-20', '40060363',
  K(True, None, None, None), None,
  '⭐子供可・ベビーカー入店可(食べログ)。⚠夜のみ18:00〜24:00、不定休。駐車場10台。'),
 # ---- 粕屋町 長者原・仲原・大隈(モールの北〜西 2〜3km) ----
 ('staminayakiniku-teppanou-kuukouhigashi', 'スタミナ焼肉鉄板王 空港東店', '仲原', '糟屋郡粕屋町', '焼肉', '糟屋郡粕屋町仲原2351-1', '40018362',
  K(None, None, None, None), None,
  '⭐子供可(食べログ)。11:30〜24:00、火曜休(祝日なら翌日)。駐車場あり。'),
 ('shokudou-sachi-chojabaru', '幸', '長者原東', '糟屋郡粕屋町', '食堂', '糟屋郡粕屋町長者原東2-12-2', '40047583',
  K(True, None, True, None), None,
  '⭐子供可・ベビーカー入店可・座敷12席(食べログ)。22席の小さな食堂。11:30〜14:00・17:30〜23:00(定休日は要確認)。駐車場あり。'),
 ('newhanachina-kasuya', '粕屋町中華料理 ニューハナチャイナ', '長者原東', '糟屋郡粕屋町', '中華', '糟屋郡粕屋町長者原東2-13-1', '40045838',
  K(None, None, None, None), None,
  '⭐子供可(食べログ)。38席。11:30〜14:30・17:30〜21:30(土曜は〜24:00)、月火休。駐車場あり。'),
 ('nikuniku-udon-kasuya', '肉肉うどん 粕屋店', '仲原', '糟屋郡粕屋町', 'うどん', '糟屋郡粕屋町大字仲原2638-1', '40035319',
  K(True, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・ベビーカー入店可・座敷あり(食べログ)。11:00〜22:00、不定休。駐車場7台。'),
 ('akakara-fukuokahigashi', '赤から 福岡東店', '仲原', '糟屋郡粕屋町', '赤から鍋・焼肉', '糟屋郡粕屋町仲原2574-1', '40017996',
  K(None, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・掘りごたつ席・バリアフリー(食べログ)。130席。'
  '平日17:00〜23:00/土日祝11:30〜15:00・17:00〜23:00、無休。共用駐車場100台以上。'),
 ('tometeba-nakabaru', '九州名物とめ手羽 仲原店', '仲原', '糟屋郡粕屋町', '手羽先・もつ鍋', '糟屋郡粕屋町大字仲原2525', '40052810',
  K(True, None, True, None), ALL,
  '⭐子供可(乳児〜小学生)・お子様メニューあり・ベビーカー入店可、掘りごたつ・個室あり(食べログ)。'
  '⚠夜のみ16:00〜23:00、不定休。駐車場4台。'),
 ('sanshounoki-kasuya', '山椒の木', '大隈', '糟屋郡粕屋町', 'うなぎ・そば・海鮮', '糟屋郡粕屋町大字大隈38-4', '40020728',
  K(True, None, None, None), ALL,
  '⭐子供可(乳児〜小学生)・ベビーカー入店可、多目的トイレ完備・個室(20〜30人)・バリアフリー(食べログ)。'
  '月水木金11:00〜15:00/土日祝11:00〜21:00、火曜+第1・3月曜休(7・8月は変則)。駐車場 店前4台+裏30台。'),
]

# geocoding.jp の結果(住所で取得・11秒間隔)。食べログ地図ピンと突き合わせて差10m前後を確認済み
#   例外: ジョイフル志免店・鉄板王は geocoding.jp がエラー/lat=0 → 食べログ地図ピンを採用(ジョイフルはNAVITIMEとも一致)
#         赤から福岡東店は geocoding.jp と食べログで141mずれ → 共用駐車場の複合敷地なので食べログ側を採用
GEO = {
 'yuzuan-shime': (33.593813, 130.476984),
 'marugenramen-shime': (33.59403, 130.476954),
 'sukesanudon-nanri-shime': (33.595544, 130.476244),
 'nerikomiudon-gon-shime': (33.596726, 130.47512),
 'hassenkaku-shime': (33.596931, 130.475084),
 'seikaen-shime': (33.597125, 130.474441),
 'joyfull-shime': (33.592605, 130.477704),                       # 食べログ地図(geocoding.jp不可)
 'cocohare-shime': (33.591856, 130.475927),
 'marutomiramen-shime': (33.596707, 130.469351),
 'torifuji-shime': (33.601225, 130.465475),
 'chingu-shime': (33.601248, 130.465466),                         # 鶏富士と同じ建物(食べログ地図)
 'torikawahonpo-shime': (33.600983, 130.464962),
 'staminayakiniku-teppanou-kuukouhigashi': (33.610944, 130.461428),  # 食べログ地図(geocoding.jp不可)
 'shokudou-sachi-chojabaru': (33.617744, 130.478253),
 'newhanachina-kasuya': (33.618102, 130.478401),
 'nikuniku-udon-kasuya': (33.608785, 130.448113),
 'akakara-fukuokahigashi': (33.609354, 130.450782),               # 食べログ地図(geocoding.jpと141m差)
 'tometeba-nakabaru': (33.610621, 130.454943),
 'sanshounoki-kasuya': (33.621771, 130.49644),
}
assert len(SPOTS) == 19 and set(GEO) == {x[0] for x in SPOTS}

if __name__ == '__main__':
    shutil.copy(P, P + '.bak_aeonfukuoka_area')
    s = json.load(io.open(P, encoding='utf-8'))
    ids = {x['id'] for x in s}

    def nn(t):
        t = re.sub(r'[（(].*?[)）]', '', t or '')
        return re.sub(r'[\s　・.「」]', '', t).lower()
    names = {nn(x.get('name')): x['id'] for x in s}
    added = []
    for (sid, name, area, city, genre, addr, tl, kids, ages, verdict) in SPOTS:
        la, ln = GEO[sid]
        if sid in ids:
            print('skip (id exists):', sid); continue
        if nn(name) in names:
            print('skip (same name):', name, '->', names[nn(name)]); continue
        near = [x for x in s if x.get('lat') and x.get('lng') and x['id'] not in added and
                math.hypot((x['lat'] - la) * 111, (x['lng'] - ln) * 111 * math.cos(math.radians(la))) < 0.15]
        if near:
            print('  note: 150m以内に既存', name, '->', [(x['id'], x['name']) for x in near])
        o = {'id': sid, 'name': name, 'area': area, 'city': city, 'pref': '福岡県', 'genre': genre,
             'address': '福岡県' + addr, 'lat': la, 'lng': ln, 'visited': None, 'with': 'family',
             'kids': kids, 'verdict': verdict, 'video': dict(VIDEO0), 'thumb': None,
             'wish': True, 'category': 'gourmet', 'tabelog': TL % tl}
        if ages:
            o['ages'] = list(ages); o['ages_src'] = 'auto'
        s.append(o)
        added.append(sid)
    allids = [x['id'] for x in s]; assert len(allids) == len(set(allids))
    assert not [x['id'] for x in s if x.get('wish') and any((x.get('video') or {}).values())]
    io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
    print('added', len(added))
    print(' '.join(added))
