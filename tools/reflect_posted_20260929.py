# -*- coding: utf-8 -*-
"""2026-09-29 未反映9本の投稿をマップへ紐付ける
   (check_upload_sync.py の「最近の未反映9本」。9/20〜9/29 の投稿が posted 未設定で NEW が0件になっていた)
   posted は yt-dlp の %(timestamp)s を JST に変換した日付(upload_date(UTC)は使わない)
"""
import io, json, os, shutil, sys
from PIL import Image, ImageOps
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
shutil.copy(P, P + '.bak_reflect_20260929')
spots = json.load(io.open(P, encoding='utf-8'))
by = {s['id']: s for s in spots}
assert len(by) == len(spots), 'id重複'

YT = 'https://youtube.com/shorts/%s'
UPD = [  # (id, videoId, posted(JST))
 ('merittakidstakeo',             'hZwFrXDec44', '2026-09-29'),
 ('kushikatsutanaka-shime',       'ee1KetCT_xc', '2026-09-28'),
 ('sanpururiki',                  '9E45KCOUAxA', '2026-09-27'),
 ('tokinomahouresutoranmajikkuk', 'PKsVHczbCbg', '2026-09-24'),
 ('shirouzuooikekouen',           'mkzZHwY5nso', '2026-09-23'),
 ('ic-kokusai-teien',             'DJf9TRWorsw', '2026-09-20'),  # 中央公園2本目=国際交流庭園の回
 ('shouwaromankura',              'lb2ubyMN0ds', '2026-09-20'),
]
for sid, vid, posted in UPD:
    s = by[sid]
    s.setdefault('video', {'youtube': None, 'tiktok': None, 'instagram': None})
    assert not s['video'].get('youtube'), sid + ' に既にYouTubeがある'
    s['video']['youtube'] = YT % vid
    s['posted'] = posted
    s['wish'] = False
    assert s.get('visited'), sid + ' に visited が無い'
    print('更新:', sid, s['name'], posted)

# ── 上川端商店街(新規)。素材は 0.アップロード済/中洲商店街　かろのうろん(撮影日 2026-09-20) ──
NEW_ID = 'kamikawabata-shotengai'
assert NEW_ID not in by
SRC = r'C:\Users\totor\Dropbox\ショート動画用\0.アップロード済\中洲商店街　かろのうろん\インスタサムネ_川端商店街.jpg'
im = ImageOps.exif_transpose(Image.open(SRC)).convert('RGB')
im = ImageOps.fit(im, (240, 300), Image.LANCZOS, centering=(0.5, 0.45))
im.save(os.path.join(R, 'map', 'thumbs', NEW_ID + '.jpg'), quality=88)
spots.append({
 'id': NEW_ID,
 'name': '上川端商店街',
 'area': None,
 'city': '福岡市博多区',
 'pref': '福岡県',
 'genre': '商店街',
 'lat': 33.594142, 'lng': 130.408647,   # geocoding.jp「福岡市博多区上川端町」
 'visited': '2026-09-20',
 'with': 'family',
 'kids': None,
 'verdict': '博多でいちばん歴史のある約400mのアーケード(約130店)。キャナルシティ博多⇄博多リバレインの間で、中洲川端駅すぐ。 '
            '⭐天井の「博多弁番付」、山笠の飾り山、博多提灯の絵付け体験、ラーメン屋3軒並び、抹茶ソフトの新店など歩くだけで楽しめる。 '
            '締めは商店街近くの明治15年創業「かろのうろん」。',
 'video': {'youtube': YT % 'mkk0V6Jif00', 'tiktok': None, 'instagram': None},
 'thumb': NEW_ID + '.jpg',
 'wish': False,
 'category': 'play',
 'posted': '2026-09-22',
})
print('新規:', NEW_ID)

# 整合チェック
ids = [s['id'] for s in spots]
assert len(ids) == len(set(ids))
bad = [s['id'] for s in spots if s.get('wish') and any((s.get('video') or {}).values())]
assert not bad, '青ピンに動画: %s' % bad
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))

# 照合除外(おむつ替え問題はテーマ回)
X = os.path.join(R, 'data', '照合除外.txt')
t = io.open(X, encoding='utf-8').read()
if 'gsfcjQ6orAI' not in t:
    io.open(X, 'a', encoding='utf-8').write('gsfcjQ6orAI  # おむつ替え問題(テーマ回・特定店舗ではない) 2026-09-28\n')
print('完了 spots=%d' % len(spots))
