# -*- coding: utf-8 -*-
"""魁龍 博多本店: 既存の青ピン dotonkotsuraamenkairyuuhakat を赤ピン化(1st STEP・2026-09-30)。撮影日 2026-09-29
   ⚠最初「kairyu-hakata」で新規登録しかけたが、'魁龍' で検索したら既存があった(海流/カイリューでしか探していなかった)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_kairyu')
spots = json.load(io.open(P, encoding='utf-8'))
ID = 'dotonkotsuraamenkairyuuhakat'
s = next(x for x in spots if x['id'] == ID)
s.update({
 'name': '魁龍 博多本店',
 'address': '福岡県福岡市博多区東那珂2-4-31',
 'visited': '2026-09-29',
 'wish': False,
 'kids': {'stroller': None, 'diaper': None, 'tatami': True, 'kidsChair': None, 'serveMin': None, 'noise': None},
 'verdict': '⚠子連れ向けの作りではない。小上がりの座敷はあるので入れないことはない、くらい(2026-09-29実体験)。 '
            'やわ麺「ずんだれ」しか出さない店(バリカタ・ハリガネ・粉落としは無し)。豚頭と背脂だけを24時間炊いて30年以上継ぎ足す「呼び戻し」のど豚骨。'
            '人気No.1は全部のせラーメン1,280円、替玉180円。11:00〜23:00(日祝21:00まで)年中無休・スープ切れ終了あり。駐車場12台。'
            '店内は有名人のサインとホークスのユニフォームだらけ。『オモウマい店』(2024年4月)出演店。',
 'thumb': ID + '.jpg',
 'web': 'https://kairyuramen.com/',
 'photos': [ID + '_01_外観.jpg', ID + '_02_小上がり座敷.jpg', ID + '_03_サインの壁とテーブル席.jpg', ID + '_04_ずんだれの掲示.jpg'],
})
ids = [x['id'] for x in spots]; assert len(ids) == len(set(ids))
assert not [x for x in spots if x.get('wish') and any((x.get('video') or {}).values())]
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('updated', ID)
