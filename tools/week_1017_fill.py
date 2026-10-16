# -*- coding: utf-8 -*-
"""2026-10-17〜18「週末どうする？ 福岡の子連れおでかけ12選」の手入力ぶん。
   ユーザー確定(2026-10-16): 11件 + イオンモール福津のティラノサウルス = 12件。
   memo(detail)は各イベントの詳細ページ(いこーよ/公式)を読んで書いた。
   ⚠イオンモール社は 2026-10 に <slug>.aeonmall.jp へ移転。候補JSONのURLは新ドメインに書き換え済み。
   並びは「窓の中の初日 → 終了日」順(10/17のみ → 10/17-18 → 10/18のみ)。"""
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'data')

ROWS = [
 # (url, 表示名, 会場, 市区, time, price/free, place, note, parking, detail4)
 ('https://iko-yo.net/events/605390', 'Kidsジョブチャレンジ(ホテルのお仕事体験)', 'クロスライフ博多柳橋', '福岡市中央区',
  '10時〜15時(各1時間)', None, None, '小学生向け・事前予約制', None,
  ['ホテルのフロント係を体験(10時〜)', 'ハーブを蒸留してアロマ作り(14時〜・持ち帰り)',
   '天神店ではシェフ体験(12時〜)', '小学生向け・事前予約制。料金は公式で確認']),
 ('https://iko-yo.net/events/604862', '本物かぼちゃでハロウィンオーナメント作り', 'ビエラ小倉 3F', '北九州市小倉北区',
  '10時〜17時', 'free', '新幹線小倉駅直結', '予約不要・先着50名', None,
  ['本物のかぼちゃに飾り付けして持ち帰る', '新幹線小倉駅直結のビエラ小倉3F(屋内)',
   '予約不要・先着50名。無くなり次第終了', '無料。小倉お城まつり(〜10/18)と合わせて']),
 ('https://www.boatrace-fukuoka.com/modules/news/?page=index_event&storyid=2703', '海辺のカーニバル2026', 'ボートレース福岡', '福岡市中央区',
  '10時〜17時', 'free', None, 'ゴムボート試乗は受付終了', None,
  ['3才〜小学生のキッズドライビングスクール(整理券)', 'ミニショベル・高所作業車に乗れる',
   '宝石採掘は採った石を持ち帰れる', 'ふわふわ・段ボール迷路・宝探しも無料']),
 ('https://www.jrhakatacity.com/kids/detail/?cd=000167', '天体観測 in つばめの杜ひろば', 'JR博多シティ 屋上つばめの杜ひろば', '福岡市博多区',
  '18:30〜19:30', '1,000円(当日現金)', None, '各日10名・15分前受付・荒天中止', None,
  ['博多駅の屋上から望遠鏡で星を見る', '各日10名。予約なし、15分前から受付',
   '1,000円は当日現金のみ', '雨天決行・荒天中止。屋上なので上着を']),
 ('https://konohamall.com/news/event/7364', '環境わくわくひろば(ゴミ収集車の積み込み体験)', '木の葉モール橋本', '福岡市西区',
  '10:30〜14:00', 'free', None, '整理券は10:00と12:30に1Fもみじコート', None,
  ['ゴミ収集車にゴミを積み込む体験(10:30〜30分おき)', 'ペットボトルキャップでキーホルダー作り',
   '整理券は1Fもみじコートで10時と12時半', '無料。収集車の体験は雨天中止']),
 ('https://tenpo.aeon-kyushu.info/detail/ogori/event-news/1944244/', 'ハロウィン迷路', 'イオン小郡ショッピングセンター', '小郡市',
  '11時〜16時', '1人200円', None, '仮装かiAEONお気に入り登録で100円引き', None,
  ['ハロウィン仕様の迷路に挑戦する', 'ゴールのカボチャのオブジェと記念写真',
   '1人200円。仮装していくと100円引き', '2日間とも11時〜16時']),
 ('https://fukutsu.aeonmall.jp/event/7ac9de6e-b85d-4a2d-bc59-dd31a27af55e', 'ティラノサウルスにエサをあげよう！', 'イオンモール福津', '福津市',
  '10時〜18時', 'free', '1Fサウスコート', 'アンケート回答が条件・1人1回', None,
  ['動くティラノサウルスの口にお肉を投げ入れる', 'エサやりゲームに1人1回挑戦できる',
   'アンケートに答えるのが参加条件(ソフトバンク主催)', '無料。子供だけでは不可、保護者と一緒に']),
 ('https://iko-yo.net/events/599972', 'にしてつ電車まつり(第31回)', '西鉄 筑紫車両基地', '筑紫野市',
  '10時〜16時(最終入場15:30)', 'free', None, '駐車場なし・筑紫駅から無料送迎バス', None,
  ['電車の洗浄機を車内から体験(10:40/13:20/14:40)', '工場の中でクイズラリー',
   'キャラクター登場は11:40と12:40', '駐車場なし。筑紫駅から無料バスで']),
 ('https://fukutsu.aeonmall.jp/event/e1935fb7-b66d-4a1b-8f40-f9ae1c88eaec', 'それいけ！アンパンマン ショー(観覧無料)', 'イオンモール福津', '福津市',
  '①11:00 ②15:00', 'free', '1Fノースコート', '整理券は9〜10時に配布(各回70組)', None,
  ['ステージでアンパンマンのショーを観る', '整理券は9〜10時にB-3の1Fノースコート入口前',
   '各回70組(1家族5名まで)。周辺から立ち見も可', '撮影は不可。観覧無料']),
 ('https://iko-yo.net/events/598339', '秋のハイハイレース・カタカタレース', '筑紫野市山口コミュニティセンター', '筑紫野市',
  '10:00〜11:30', '800円(両方は+500円)', None, '要予約・締切10/17', None,
  ['赤ちゃんのハイハイレースに出場', '歩き始めの子は手押し車のカタカタレース',
   '終了後に無料の足形アート', '800円。前日10/17までに要予約']),
 ('https://iko-yo.net/events/605308', 'ハロウィンおえかきマグカップ作り', 'TNC住宅展示場 きてミテ！小倉', '北九州市小倉南区',
  '10時〜17時', 'free', None, '要予約・定員40名・未就学〜8歳', None,
  ['マグカップにハロウィンの絵を描いて持ち帰る', '対象は未就学児〜8歳。定員40名',
   'アンケート回答とモデルハウス1棟見学が条件', '無料だが要予約']),
 ('https://www.crossroadfukuoka.jp/event/12237', 'ちっご祭2026(花火あり)', '県営筑後広域公園', '筑後市',
  '11時〜19時', 'free', None, '雨天中止・小雨決行', 'あり',
  ['謎解きラリーとスタンプラリー', 'ステージとキッチンカーで1日遊べる',
   '締めは花火。船小屋駅から徒歩10分', '無料・駐車場あり。雨天中止(小雨決行)']),
]

cand = json.load(io.open(os.path.join(D, '_週末イベント候補.json'), encoding='utf-8'))
by = {e['url']: e for e in cand['events']}
missing = [r[0] for r in ROWS if r[0] not in by]
assert not missing, missing

ext_p = os.path.join(D, '_イベント補足.json')
ext = json.load(io.open(ext_p, encoding='utf-8'))
disp_p = os.path.join(D, '_イベント表示名.json')
disp = json.load(io.open(disp_p, encoding='utf-8'))
for url, name, venue, city, tm, price, place, note, park, detail in ROWS:
    e = {'city': city, 'time': tm, 'detail': detail, 'memo': detail,
         '_memo': '2026-10-16 週末どうする？12選。詳細ページを読んで記入'}
    if price == 'free':
        e['free'] = True
    elif price:
        e['price'] = price
    if place:
        e['place'] = place
    if note:
        e['note'] = note
    if park:
        e['parking'] = park
    # ちっご祭の県公式画像は吹奏楽部と観客が写った現地写真(ポスターではない)。
    # 他人が写る写真は出典があっても出さない → テキストカードにする
    if 'crossroadfukuoka.jp/event/12237' in url:
        e['no_poster'] = True
    ext[url] = e
    disp[url] = {'name': name, 'venue': venue}
io.open(ext_p, 'w', encoding='utf-8').write(json.dumps(ext, ensure_ascii=False, indent=1))
io.open(disp_p, 'w', encoding='utf-8').write(json.dumps(disp, ensure_ascii=False, indent=1))
cand['selected'] = [r[0] for r in ROWS]
# マップ登録(event_to_map.py)用: 会場がマップに無いものは住所を候補側に書く(ジオコーディングは --apply 時)。
# 住所の根拠: いこーよ/公式の詳細ページ(クロスライフ・ビエラ・筑紫車両基地・きてミテ・筑後広域公園)、
#   筑紫野市公式(山口コミュニティセンター 大字古賀196-1)、イオン九州 店舗検索(小郡 大保字弓場110)
ADDR = {
 'https://iko-yo.net/events/605390': '福岡県福岡市中央区春吉1-6-5',
 'https://iko-yo.net/events/604862': '福岡県北九州市小倉北区浅野1-1-1',
 'https://tenpo.aeon-kyushu.info/detail/ogori/event-news/1944244/': '福岡県小郡市大保字弓場110',
 'https://iko-yo.net/events/599972': '福岡県筑紫野市下見673-3',
 'https://iko-yo.net/events/598339': '福岡県筑紫野市大字古賀196-1',
 'https://iko-yo.net/events/605308': '福岡県北九州市小倉南区津田1-4-7',
 'https://www.crossroadfukuoka.jp/event/12237': '福岡県筑後市津島831-1',
}
for url, name, venue, city, *_ in ROWS:
    e = by[url]
    e['title'] = name            # 生タイトル(煽り・絵文字入り)はマップ/一覧にも出るので表示名に揃える
    e['venue'] = venue
    e['city'] = city
    if url in ADDR:
        e['addr'] = ADDR[url]
io.open(os.path.join(D, '_週末イベント候補.json'), 'w', encoding='utf-8').write(
    json.dumps(cand, ensure_ascii=False, indent=1))
print('補足 %d件 / 表示名 %d件 / selected %d件' % (len(ext), len(disp), len(cand['selected'])))
for r in ROWS:
    print(' ', by[r[0]]['span'], r[1])
