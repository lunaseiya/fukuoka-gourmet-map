# -*- coding: utf-8 -*-
"""アソビュー掲載施設のうち「九州7県+山口の子連れ向け」を spots.json に一括登録する。

  python tools/asoview_import.py            # ドライラン(採用/除外の一覧を出すだけ)
  python tools/asoview_import.py --apply    # 書き込み

方針(2026-08-28ユーザー確定):
  第1段階=九州+山口の子連れ施設だけ。大人向け(メイドカフェ・バンジー・ダーツバー等)と
  県外は入れない。マップの性格(福岡こそだてグルメマップ)を保つため。
  座標・住所はアソビューの施設ページから取得済み(data/asoview_detail.json)なので
  ジオコーディング不要。wish=true(青ピン)で入れ、asoview のPRリンクを最初から付ける。
"""
import json, io, re, os, sys, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP  = os.path.join(ROOT, 'data', 'spots.json')
DET  = os.path.join(ROOT, 'data', 'asoview_detail.json')

PREF9 = ('福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','山口県')

# 大人向け・子連れ想定でないものは入れない
NG_WORD = [
 'めいどりーみん','メイドカフェ','コンセプトカフェ','コミックパブ','ネットカフェ','漫画喫茶',
 'バンジー','AXE THROWING','ダーツ','ビリヤード','射撃','ガンシューティング',
 'クラフトビール','ワイナリー','酒蔵','日本酒','焼酎','ビール工場見学の試飲',
 'カジノ','パチンコ','麻雀','脱出ゲーム 恐怖','ホラー','お化け屋敷',
 'ナイトプール','クラブ','キャバ','リラクゼーション','マッサージ','エステ','脱毛',
 'ゴルフ','ダイビングライセンス','スカイダイビング','パラグライダー','ジェットスキー',
 'レンタカー','レンタルバイク','タクシー','ハイヤー','空港送迎',
 'アソビュー株式会社',
 # 工房系は子供の一般的な嗜好と違うため除外(2026-08-28ユーザー確定)
 '陶芸','陶工房','陶家','窯元','窯工房','焼窯','ガラス工房','がらす工房','サンドブラスト',
 'キャンドル','candle','石けん','石鹸','アロマ','宝石工房','ジュエリー','シルバー工房',
 '色彩工房','巧工房','工房アリィ','木のおもちゃ','飛鳥工房','対馬ヤマネコ工房','つむぐ工房',
 'クライミング','ボルダリング','サップ','SUP',
 '陶片','平家窯','岳焼','purifywith','志田焼の里',
]
# 会期のある企画展。until を手で入れる必要があるので自動登録から外す
EXHIBIT_WORD = ['展！','展～','展〜','ゴッホ展','ムーミン展','美術館 特別展','企画展']
# 子連れで行く施設のジャンル語(名前 or genre のどちらかに含まれれば採用)
OK_WORD = [
 '動物園','水族館','サファリ',' zoo','アクアリウム','イルカ','ペンギン','牧場','ふれあい',
 '遊園地','テーマパーク','アスレチック','キッズ','こども','子供','親子','ファミリー',
 'プール','水遊び','公園','ランド','パーク','ワールド','遊び場','あそび',
 '博物館','美術館','科学館','記念館','資料館','ミュージアム','水土里','プラネタリウム',
 '体験','工房','手づくり','手作り','陶芸','ガラス','キャンドル','絵付け','工場見学',
 '温泉','スパ','岩盤浴','日帰り','足湯','湯',
 '展望','タワー','クルーズ','遊覧','川下り','屋形船','観光船','ロープウェイ','ケーブル',
 'いちご狩り','ぶどう狩り','みかん狩り','果物狩り','農園','収穫',
 'カート','ゴーカート','トランポリン','ボルダリング','クライミング','アイススケート',
 'キャンプ','グランピング','BBQ','バーベキュー','ハーモニーランド','城','武家屋敷',
]

def clean_name(t):
    return re.sub(r'\s+', ' ', str(t)).strip()

def norm(s):
    s = re.sub(r'[（(].*?[)）]', '', str(s))
    s = re.sub(r'[\s　・=\-−ー_,、。&＆/／「」『』!！★☆\'\"®™]', '', s)
    return s.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')).lower()

def slug(bid):
    return 'aso%s' % bid

def city_of(addr):
    m = re.search(r'(?:福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|山口県)'
                  r'(.+?(?:市|郡[^\s]{1,6}町|郡[^\s]{1,6}村|町|村))', addr or '')
    if not m: return None
    c = m.group(1)
    # 福岡市・北九州市・熊本市は区まで
    m2 = re.match(r'((?:福岡|北九州|熊本)市[^\s]{1,3}区)', c)
    return m2.group(1) if m2 else c

def area_of(addr, city):
    if not addr: return city or ''
    tail = addr
    for p in PREF9: tail = tail.replace(p, '')
    if city: tail = tail.replace(city, '', 1)
    tail = re.sub(r'^[\s　]*', '', tail)
    tail = re.sub(r'[\d０-９].*$', '', tail).strip('　 -−ー')
    return tail or (city or '')

def main():
    apply_it = '--apply' in sys.argv
    sp  = json.load(io.open(MAP, encoding='utf-8'))
    det = json.load(io.open(DET, encoding='utf-8'))
    have_id   = {s['id'] for s in sp}
    have_name = {norm(s['name']) for s in sp}
    have_aso  = {str(s.get('asoview','')).split('/')[-2] for s in sp if s.get('asoview')}

    take, skip = [], []
    for bid, v in det.items():
        name = clean_name(v.get('name') or '')
        addr = (v.get('addr2') or '').strip()   # addr2=正しい住所(旧addrは宣伝文を誤取得)
        if bid in have_aso:                      continue
        if not name or v.get('err'):             continue
        if not addr.startswith(PREF9):
            skip.append((name, '県外/住所不明: %s' % (addr[:14] or '—'))); continue
        if v.get('lat') is None or v.get('lng') is None:
            skip.append((name, '座標なし')); continue
        low = name.lower()
        hit_ng = [w for w in NG_WORD if w.lower() in low]
        if hit_ng:
            skip.append((name, '大人向け: ' + hit_ng[0])); continue
        if any(w in name for w in EXHIBIT_WORD):
            skip.append((name, '期間限定の企画展(untilを手入力するため別扱い)')); continue
        hay = (name + ' ' + str(v.get('genre') or '') + ' ' + addr).lower()
        if not any(w.lower() in hay for w in OK_WORD):
            skip.append((name, '子連れ向けと判定できず')); continue
        n = norm(name)
        if any(n == x or (len(n) >= 5 and (n in x or x in n)) for x in have_name):
            skip.append((name, 'マップに既存')); continue
        sid = slug(bid)
        if sid in have_id:
            skip.append((name, 'id重複')); continue
        take.append((bid, name, addr, v))
        have_name.add(n); have_id.add(sid)

    print('=== 採用候補 %d件 (%s) ===' % (len(take), '書き込み' if apply_it else 'ドライラン'))
    for bid, name, addr, v in take[:60]:
        print('  %-34s %-22s %s' % (name[:34], (city_of(addr) or '?')[:22], addr[:26]))
    if len(take) > 60: print('  ... 他 %d件' % (len(take)-60))
    print()
    from collections import Counter
    print('除外の内訳:', dict(Counter(r.split(':')[0] for _, r in skip)))

    if apply_it and take:
        shutil.copy(MAP, MAP + '.bak_asoimport')
        for bid, name, addr, v in take:
            city = city_of(addr)
            pref = next((p for p in PREF9 if addr.startswith(p)), None)
            sp.append({
                'id': slug(bid), 'name': name,
                'area': area_of(addr, city), 'city': city, 'pref': pref,
                'genre': v.get('genre') or 'レジャー',
                'lat': v['lat'], 'lng': v['lng'], 'address': addr,
                'visited': None, 'with': 'family', 'kids': None,
                'verdict': None,
                'video': {'youtube': None, 'tiktok': None, 'instagram': None},
                'thumb': None, 'wish': True, 'category': 'play',
                'asoview': 'https://www.asoview.com/base/%s/' % bid,
            })
        io.open(MAP, 'w', encoding='utf-8').write(json.dumps(sp, ensure_ascii=False, indent=1))
        print('追加 %d件 / 合計 %d件 (バックアップ .bak_asoimport)' % (len(take), len(sp)))

if __name__ == '__main__':
    main()
