# -*- coding: utf-8 -*-
"""2026-10-22 東平尾公園 大谷広場(touheiokouenootanihiroba)を訪問済み(赤ピン)に。エモ回の着手時点で登録(動画完成を待たない)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_touheio_20261022')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
by = {s['id']: s for s in spots}
s = by['touheiokouenootanihiroba']
assert s.get('wish') is True and not s.get('visited'), s.get('visited')
photos = sorted(f for f in os.listdir(os.path.join(R, 'map', 'photos')) if f.startswith('touheiokouenootanihiroba_'))
assert len(photos) == 11, photos
assert os.path.exists(os.path.join(R, 'map', 'thumbs', 'touheiokouenootanihiroba.jpg'))
s.update({
    'area': '東平尾公園', 'city': '福岡市博多区', 'pref': '福岡県',
    'address': '福岡県福岡市博多区東平尾公園2丁目1-6',
    'genre': '公園',
    'visited': '2026-10-22', 'wish': False,
    'kids': {'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': None},
    'verdict': ('⭐**2026年4月22日グランドオープン**(2025年4月1日に一部先行オープン→山側の整備が完了)。博多の森(東平尾公園)の山の傾斜をまるごと使った遊び場。'
                '⭐坂の下は**インクルーシブな「みんなの遊び広場」**: 4連ブランコ(バケット型・ネット型)・プレイパネル・回転遊具・ドーム型遊具・ネット遊具・ジャンプトランポリン(6〜12歳・16人)・車いすのまま寄れる砂場。日よけの下に見守りベンチ。'
                '⭐**市内唯一の草スキー場**: そり貸出無料(持込み禁止・小学生まで・小さい子は18歳以上の保護者が同乗可・二人乗り禁止)。'
                '⭐坂を登りながら連続遊具 → **市内最大規模の複合遊具「冒険のとりで」**(すべり台・ロープ・ネット・クライミング)→ 森の広場(木陰で寝転べるネットデッキ)→ 山頂広場・展望デッキ(空港と博多の街が見える)。'
                '⚠**傾斜がきつい**。ベビーカーで回れるのは坂の下の遊び広場・芝生広場・草スキー場まで。上の遊具は抱っこ・歩きで。'
                '⭐トイレ棟が充実: こどもトイレ付き・バリアフリートイレ(ベビーチェア・オストメイト・介助用ベッド)・**ベビーケアルーム(おむつ交換台・授乳室)**・赤ちゃんの駅。キャッシュレス自販機(アイスも)。'
                '⭐タリーズコーヒー併設(平日9〜20時・土日祝8〜20時・ドライブスルーあり)。**入口が分かりにくいのでタリーズを目印に**(目の前が大谷第1駐車場)。'
                '⭐大谷広場の利用時間: 4〜9月 10:00〜18:30 / 10〜3月 10:00〜16:30(雨天クローズ)。入園無料。'
                '駐車場は有料: 入庫後20分無料・60分100円・通常日最大500円(特別日は3時間以上2,500円)・**タリーズ利用で1時間無料**。'
                'じゃぶじゃぶ池は夏休み期間のみ(2026年度は終了)。芝生広場はテント持参で1日。2026年10月22日撮影。'),
    'thumb': 'touheiokouenootanihiroba.jpg',
    'photos': photos,
    'web': 'https://otanihiroba-higashihirao.com/guide',
    'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'manual',
})
s.setdefault('added', '2026-10-22')
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('更新:', s['id'], s['name'], s['visited'], len(photos), '枚')
