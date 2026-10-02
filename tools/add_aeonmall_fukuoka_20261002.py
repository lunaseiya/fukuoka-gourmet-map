# -*- coding: utf-8 -*-
"""イオンモール福岡(2026-10-02訪問)の子連れ情報を反映。親=aeonmallfukuoka / 子=ルクルパーク・ちきゅうのにわ・KIDS PARK(新)・ゼッテリア(新)
   コンプライアンス: ⚠(公式に撮影禁止の告知なし・イオンモール共通方針は無許可の商業撮影ご遠慮)→ 人が映らない写真だけ掲載"""
import io, json, os, shutil, subprocess, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
SRC = r'C:\Users\totor\Dropbox\ショート動画用\イオンモール福岡　ルクル'
LIST = r'C:\Users\totor\.claude\jobs\412933b6\tmp\aeonfk\list.txt'
FF = r'C:\Users\totor\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
PH, TH = os.path.join(R, 'map', 'photos'), os.path.join(R, 'map', 'thumbs')
L = {int(a): b for a, b in (l.strip().split('|', 1) for l in io.open(LIST, encoding='utf-8') if '|' in l)}
shutil.copy(P, P + '.bak_aeonfukuoka')
s = json.load(io.open(P, encoding='utf-8')); by = {x['id']: x for x in s}


def img(n, ss=1.5):
    p = os.path.join(SRC, L[n])
    if p.lower().endswith('.mov'):
        t = os.path.join(PH, '_t.jpg'); subprocess.run([FF, '-v', 'quiet', '-y', '-ss', str(ss), '-i', p, '-frames:v', '1', '-q:v', '2', t])
        im = Image.open(t).convert('RGB'); os.remove(t); return im
    return ImageOps.exif_transpose(Image.open(p)).convert('RGB')


def photos(sid, items, thumb_n):
    out = []
    for k, (n, name) in enumerate(items, 1):
        im = img(n); im.thumbnail((1080, 1920)); nm = '%s_%02d_%s.jpg' % (sid, k, name)
        im.save(os.path.join(PH, nm), quality=85); out.append(nm)
    ImageOps.fit(img(thumb_n), (240, 300), Image.LANCZOS).save(os.path.join(TH, sid + '.jpg'), quality=88)
    return out


V = '2026-10-02'
m = by['aeonmallfukuoka']
m.update(visited=V, wish=False, thumb='aeonmallfukuoka.jpg', ages=['baby', 'toddler', 'kids'], ages_src='manual',
    kids={'stroller': True, 'diaper': True, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': None},
    photos=photos('aeonmallfukuoka', [(3, 'キャラクターカートとベビーカー'), (43, 'キッズカート'), (44, '赤ちゃんルーム'),
        (45, '授乳室ブース'), (47, '調乳用のお湯'), (81, 'キッズメニュー案内')], 2),
    verdict='専門店約197店。トイザらス・ベビーザらス出店。⭐通路が広く、キャラクターカートのままレストラン街やフードコートの店に入れる店が多い'
            '(子供椅子より「カートのまま」が主流)。フードコートはテーブル埋め込み型のベビーチェアあり(子供椅子は少なめ・要再確認)。'
            '⭐赤ちゃんルーム: 個別授乳室(女性専用・さく乳可)、調乳用のお湯。キッズメニューの案内あり。'
            '屋内に0〜2歳の「KIDS PARK」(無料)、屋内遊び場「ちきゅうのにわ」、屋外に「ルクルパーク」(無料)。'
            '10:00〜21:00。TEL 092-938-4700。(2026-10-02実訪問)')
lp = by['lucleparkrukurupaakuionmooru']
lp.update(visited=V, wish=False, thumb='lucleparkrukurupaakuionmooru.jpg',
    kids={'stroller': True, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
    ages=['toddler', 'kids'], ages_src='manual',
    photos=photos('lucleparkrukurupaakuionmooru', [(39, '案内図とルール'), (40, 'すべり台'), (84, 'カラフルな遊具')], 40),
    verdict='イオンモール福岡の屋外あそび場で利用無料。⭐3〜6歳のエリアと6〜12歳のエリアに分かれている。人工芝・ネットの遊具・すべり台。'
            '10:00〜20:00。ボール遊び・ペット・飲食しながらの遊びは不可。雨天・遊具が濡れている時は使用不可。(2026-10-02実訪問)')
ck = by['chikyuunoniwafukuoka']
ck.update(visited=V, wish=False, thumb='chikyuunoniwafukuoka.jpg', ages=['baby', 'toddler', 'kids'], ages_src='manual',
    photos=photos('chikyuunoniwafukuoka', [(66, '入口'), (67, '料金表'), (68, '平日は飲食持ち込みOK')], 66),
    verdict='0〜12歳の屋内遊び場(キッズガーデン)。10:00〜20:00(最終受付19:30)。⭐料金(こども・会員価格/一般): 平日 最初の30分500/700円・'
            '1時間800/1,000円・3時間1,400/1,600円・1dayパス1,700/1,900円・ナイトパック(16時〜)800/1,000円。休日 1時間1,100/1,300円・1day1,800/2,000円。'
            'おとな(16歳〜)平日500円・休日600円。⭐0歳はトットット会員なら無料(証明書提示)。会員はこども1人200円引き(アプリ登録)。'
            '⭐平日限定で飲食持ち込みOK。保護者(16歳以上)1名の付き添い必須。春休み等は平日も休日料金。(2026-10-02店頭掲示)')
KP = 'kidspark-aeonmallfukuoka'
if KP not in by:
    s.append({'id': KP, 'name': 'KIDS PARK(イオンモール福岡)', 'area': None, 'city': '糟屋郡粕屋町', 'pref': '福岡県', 'genre': '室内遊び場',
        'lat': m['lat'], 'lng': m['lng'], 'visited': V, 'with': 'family', 'in': 'aeonmallfukuoka', 'category': 'play', 'wish': False,
        'kids': {'stroller': None, 'diaper': None, 'tatami': None, 'kidsChair': None, 'serveMin': None, 'noise': 'ok'},
        'verdict': '⭐0〜2歳専用の無料キッズスペース(マット敷き・小さなすべり台)。利用は9組まで。靴を脱いで遊ぶ。飲食・遊具の持ち込み不可。保護者の付き添いが必要。(2026-10-02実訪問)',
        'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': KP + '.jpg',
        'photos': photos(KP, [(73, 'KIDS PARKの看板'), (71, '小さなすべり台'), (75, 'ルール(0〜2歳・9組まで)')], 73),
        'ages': ['baby'], 'ages_src': 'manual'})
ZT = 'zetteria-aeonmallfukuoka'
if ZT not in by:
    s.append({'id': ZT, 'name': 'ゼッテリア イオンモール福岡店', 'area': None, 'city': '糟屋郡粕屋町', 'pref': '福岡県', 'genre': 'ハンバーガー',
        'lat': m['lat'], 'lng': m['lng'], 'visited': V, 'with': 'family', 'in': 'aeonmallfukuoka', 'category': 'gourmet', 'wish': False,
        'kids': {'stroller': True, 'diaper': None, 'tatami': None, 'kidsChair': True, 'serveMin': None, 'noise': 'ok'},
        'verdict': 'ハンバーガー店(旧ロッテリア系)。⭐木製のハイチェア(ベルト付き)あり。注文はタッチパネル。モール内なのでおむつ替えはモールの赤ちゃんルームで。(2026-10-02実訪問)',
        'video': {'youtube': None, 'tiktok': None, 'instagram': None}, 'thumb': ZT + '.jpg',
        'photos': photos(ZT, [(50, '店構え'), (52, '木製ハイチェア'), (97, 'メニュー')], 50),
        'ages': ['baby', 'toddler', 'kids'], 'ages_src': 'manual'})
ids = [x['id'] for x in s]; assert len(ids) == len(set(ids))
io.open(P, 'w', encoding='utf-8').write(json.dumps(s, ensure_ascii=False, indent=1))
print('ok')
