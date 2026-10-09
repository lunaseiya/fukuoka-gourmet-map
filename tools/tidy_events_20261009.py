# -*- coding: utf-8 -*-
"""三連休(10/10〜10/12)イベントの name / area を手で整える(スキル: 登録後に目視で整える)"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(R, 'data', 'spots.json')
FIX = {
    'ev-593495': ('キッズマネースクール おかいもの大作戦', '北九州市立商工貿易会館'),
    'ev-605957': ('鉄道フェスタ2026', '南福岡車両区'),
    'ev-1524fc50-ad4f-4dd1-9bb6-f-aeonmallfu': ('名探偵プリキュア! ショー(観覧無料)', 'イオンモール福津'),
    'ev-69fbf52e-eed3-4461-ac68-e-aeonmallch': ('親子でハロウィン ビューティーフェスタ', 'イオンモール筑紫野'),
    'ev-1c6b358c-b678-44c3-8803-c-aeonmallom': ('出張カンドゥー おかしクリエイター仕事体験', 'イオンモール大牟田'),
    'ev-e9ee5407-4f5c-4667-b225-1-aeonmallfu': ('悪の秘密結社と遊ぼう&ふれあい撮影会', 'イオンモール福津'),
    'ev-597469': ('新幹線ふれあいデー(博多総合車両所)', '博多総合車両所'),
    'ev-d78a7855-655e-4908-9e1e-f-aeonmallom': ('ふわふわ絵の具でアート(テクスチャーアート)', 'イオンモール大牟田'),
    'ev-274547': ('第21回 竹の里フェスタ in 那珂川', 'ミリカローデン那珂川'),
    'ev-13x': ('ドゲンジャーズとふれあい撮影会', 'イオン小郡ショッピングセンター'),
    'ev-604788-aeonmallka': ('本格ろくろ体験', 'イオンモール香椎浜'),
    'ev-597533': ('3Dプリンター出力体験', 'デジタルクラフトスタジオひびきの'),
    'ev-event8712-acrossmall': ('スクイーズベア ワークショップ', 'アクロスモール春日'),
    'ev-605603': ('科学の不思議を知ろう!', '直方市中央公民館'),
    'ev-605036': ('スイートポテトを作ろう(料理教室)', '福津市複合文化センター'),
    'ev-598621': ('大野城オータムフェスタ2026', '南福岡自動車学校'),
}
shutil.copy(P, P + '.bak_tidy_events')
spots = json.loads(io.open(P, encoding='utf-8-sig').read())
n = 0
for s in spots:
    if s['id'] in FIX:
        s['name'], s['area'] = FIX[s['id']]; n += 1
assert n == len(FIX), n
io.open(P, 'w', encoding='utf-8').write(json.dumps(spots, ensure_ascii=False, indent=1))
print('整えた', n)
