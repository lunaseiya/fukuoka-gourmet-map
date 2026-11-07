# -*- coding: utf-8 -*-
"""竣工ウォッチの巡回結果(data/openings.json)を、公開用の一覧(data/openings_list.json)へ自動で取り込む(2026-11-08 新設)。

  python tools/sync_openings_from_watch.py         # 取り込み(auto の行を作り直す)→ export_openings.py も回す
  python tools/sync_openings_from_watch.py --dry   # 件数だけ

方針(2026-11-08 ユーザー「全ての欄で拾えるものは拾って登録」):
  - 手で書いた行(auto でない)は触らない。名前が重なる自動行は作らない
  - 自動行は毎回作り直す(巡回の最新に合わせる)。id は名前のハッシュで固定
  - 子連れの一言(kids_note)は自動では書かない → 「すべて」欄に出る。子連れ欄に上げたい行は手で kids_note を足して auto を外す
  - 公園だけは「公園」なので子連れ欄に出す(遊べる場所であることは確か)
  - 開業済みは90日以内だけ。時期不明はニュースが45日以内のものだけ
"""
import json, os, re, sys, hashlib, datetime, unicodedata, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'data', 'openings.json')
LST = os.path.join(ROOT, 'data', 'openings_list.json')
TODAY = datetime.date.today()

JUNK = re.compile(r'画像|<|＜|まとめ|続々|新店|情報|オープン予定|一覧|番組|ランキング|選$|とは|って|ください|しよう|しちゃ|！|!|？|\?|※|http|^[0-9０-９/／\-]+$')
KIND = {'商業': '商業', '公園': '公園', '複合': '複合', 'ホテル': 'ホテル', 'その他': '施設'}


def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[(（]仮称[)）]', '', s)
    return re.sub(r'[\s・\-ー〜~()（）「」『』【】〈〉<>]', '', s).lower()


def clean_name(x):
    nm = (x.get('name') or '').strip()
    nm = re.sub(r'^[★☆\s]+', '', nm)
    nm = re.sub(r'\s*\d{1,2}/\d{1,2}.*$', '', nm)          # 「〜 10/30オープン」の日付以下を落とす
    nm = re.sub(r'(が|に|を|で)\d{1,2}月\d{1,2}日.*$', '', nm)
    nm = re.sub(r'(が|に)?(オープン|開業|開店|誕生|登場|移転|リニューアル).*$', '', nm)
    nm = nm.strip(' 　、。')
    if not (2 <= len(nm) <= 40) or JUNK.search(nm):
        return None
    # 見出しの文になっている名前は落とす(「〜が今年10月」「10周年」「〜で学んだ職人の…」)
    body = re.sub(r'^[(（]仮称[)）]', '', nm)
    if re.search(r'(が|を|へ|から|周年|拠点|超高層|新たな|最大店|初出店|初上陸|で学んだ|つなぐ|九州最大|[^\s]{2,}に[^\s]{2,})', body):
        return None
    # 販促・改装・メニュー名は「開業」ではない。福岡以外の支店(チェーンの記事に混ざる)も落とす
    if re.search(r'円|飲み放題|均一|改装|フロア|【|コラボ|乱舞|^焼き?カツ丼$|越谷|上新庄|大森|東京|大阪|名古屋|横浜|札幌|京都|神戸|埼玉|千葉', body):
        return None
    if re.fullmatch(r'[ぁ-ん]{2,6}', body):       # ひらがなだけの短い語(「うれしか」など)は店名か判断できない
        return None
    # 地名だけ・一般名詞だけは捨てる
    if re.fullmatch(r'(九州初上陸|九州初出店|福岡初|手土産の新定番|顔パス|顔認証改札|地域コミュニティ拠点|.{0,4}(市|区|町))', nm):
        return None
    return nm


def status_of(x):
    iso = x.get('when_iso'); when = x.get('when') or ''
    note = (x.get('note') or '') + when
    if iso:
        d = datetime.date.fromisoformat(iso)
        if d < TODAY:
            if (TODAY - d).days > 90:
                return None, None
            return 'open', iso
        exact = bool(re.search(r'\d{1,2}月\d{1,2}日|\d{4}年\d{1,2}月(?!頃)', when)) and '推定' not in note
        return ('dated' if exact else 'planned'), iso
    # 時期が書かれていないニュースは、ほとんどが「オープンしました」の記事。開業の記事だけを記事日で「最近できた」に入れる
    f = x.get('found') or ''
    t = (x.get('title') or '') + (x.get('note') or '')
    if f and (TODAY - datetime.date.fromisoformat(f)).days <= 45 and re.search(r'オープン|開業|開店|誕生|移転|上陸|出店|リニューアル|OPEN', t, re.I):
        return 'open', f
    if x.get('src') == 'manual' or (x.get('src') or '').startswith(('福岡市', '福岡県')):
        return 'tbd', (TODAY + datetime.timedelta(days=400)).isoformat()   # 公的な発表で時期だけ未定のもの
    return None, None


def main():
    dry = '--dry' in sys.argv
    raw = json.load(open(W, encoding='utf-8'))
    doc = json.load(open(LST, encoding='utf-8'))
    manual = [it for it in doc['items'] if not it.get('auto')]
    taken = {norm(it['name']) for it in manual}
    taken |= {norm(re.sub(r'[(（].*?[)）]', '', it['name'])) for it in manual}
    auto, seen = [], set()
    for x in raw:
        nm = clean_name(x)
        if not nm:
            continue
        k = norm(nm)
        if any(k in t or t in k for t in taken if len(t) >= 3 and len(k) >= 3):
            continue
        st, when = status_of(x)
        if not st:
            continue
        # 大店立地法の日付は届出からの推定。過ぎても「開業済み」とは言えないので、予定日超過(要確認)として出す
        if st == 'open' and '大店立地法' in (x.get('src') or ''):
            st = 'dated'
        # 自動の行どうしの表記ゆれ(「ゴディパン」と「ゴディパン 大丸福岡天神店」)は短いほうに寄せる
        dupe = next((a for a in auto if (k in norm(a['name']) or norm(a['name']) in k) and min(len(k), len(norm(a['name']))) >= 3), None)
        if dupe:
            if len(nm) < len(dupe['name']):
                pass
            continue
        seen.add(k)
        kind = KIND.get(x.get('kind'), '施設')
        if kind == '公園' and not re.search(r'公園|広場|緑地|ガーデン|GARDEN|プロムナード|川床|テラス', nm):
            kind = '商業'      # 巡回側が公園の記事に紛れたパン屋などを「公園」にしていることがある
        area = x.get('area') or ''
        city = (re.match(r'^(福岡市.{1,2}区|北九州市.{1,3}区|[^\s]{1,6}?郡[^\s]{1,4}?[町村]|[^\s]{1,5}?[市町村])', area) or [None])[0] or (area or '福岡県')
        src_t = x.get('src') or '出典'
        when_text = x.get('when') or ('時期未定' if st == 'tbd' else '')
        if st == 'open':
            when_text = f"{when_text}(開業)" if when_text else '開業済み'
        if '大店立地法' in src_t and st != 'open':
            when_text += '(届出からの推定。実際はもっと後が普通)'
        it = {'id': 'ow-' + hashlib.md5(nm.encode('utf-8')).hexdigest()[:10], 'auto': True, 'name': nm, 'kind': kind,
              'city': city, 'place': area if area != city else '', 'status': st, 'when': when, 'when_text': when_text,
              'note': (x.get('note') or x.get('title') or '')[:120] if (x.get('note') or x.get('title') or '') != nm else '',
              'kids_note': ('公園(遊べる場所)。詳細は行ってから追記します' if kind == '公園' else None),
              'sources': [{'t': src_t, 'u': x.get('src_url') or '', 'd': x.get('found') or TODAY.isoformat()}],
              'videos': [], 'spot': None, 'updated': TODAY.isoformat()}
        if st == 'open':
            it['opened'] = when
        auto.append(it)
    from collections import Counter
    print('自動で取り込む行', len(auto), Counter(a['status'] for a in auto), Counter(a['kind'] for a in auto))
    if dry:
        for a in auto[:40]:
            print(' ', a['status'], a['when'], a['kind'], a['name'], '|', a['city'])
        return
    doc['items'] = manual + auto
    json.dump(doc, open(LST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'export_openings.py')], check=True)


if __name__ == '__main__':
    main()
