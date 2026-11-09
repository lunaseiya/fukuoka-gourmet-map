# -*- coding: utf-8 -*-
"""撮影に行く日の条件(天気・曜日・祝日)を出す(2026-11-09)。

  python tools/shoot_conditions.py            # 今日から7日分
  python tools/shoot_conditions.py --days 2   # 今日・明日だけ

- 天気は気象庁の予報JSON(福岡県=400000 / 福岡地方=400010)。キー不要
  3日目までは6時間ごとの降水確率、4日目以降は週間予報の降水確率と信頼度
- 祝日は holidays-jp(取れなければ土日だけで判定)
- 判定は「屋外OK / 屋内寄り / 屋内」と「平日 / 休日」。候補の選び方は shoot-plan スキルが正
"""
import argparse
import datetime as dt
import json
import sys
import urllib.request

JMA = 'https://www.jma.go.jp/bosai/forecast/data/forecast/400000.json'
HOL = 'https://holidays-jp.github.io/api/v1/date.json'
WD = '月火水木金土日'
WX = {'1': '晴', '2': '曇', '3': '雨', '4': '雪'}


def get(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7)
    a = ap.parse_args()
    today = dt.date.today()
    try:
        hol = get(HOL)
    except Exception:
        hol = {}
        print('※祝日を取れなかったので土日だけで判定')
    d = get(JMA)

    # 3日予報: 天気の文・6時間ごとの降水確率
    near_wx, near_pop = {}, {}
    ts = d[0]['timeSeries']
    area = next(x for x in ts[0]['areas'] if x['area']['code'] == '400010')
    for t, w in zip(ts[0]['timeDefines'], area['weathers']):
        near_wx[t[:10]] = w.replace('　', '')
    area = next(x for x in ts[1]['areas'] if x['area']['code'] == '400010')
    for t, p in zip(ts[1]['timeDefines'], area['pops']):
        h = int(t[11:13])
        if 6 <= h < 18 and p != '':     # 撮影する時間帯(6〜18時)だけ見る
            near_pop.setdefault(t[:10], []).append(int(p))
    # 週間予報
    wk = {}
    w = d[1]['timeSeries'][0]
    ar = w['areas'][0]
    for i, t in enumerate(w['timeDefines']):
        wk[t[:10]] = (ar['weatherCodes'][i], ar['pops'][i], (ar.get('reliabilities') or [''] * 9)[i])
    tmax = {}
    tw = d[1]['timeSeries'][1]['areas'][0]
    for t, v in zip(d[1]['timeSeries'][1]['timeDefines'], tw['tempsMax']):
        tmax[t[:10]] = v

    print(f'{"日付":<10} 曜 区分      天気                          日中の降水確率  判定')
    prev_rain = False
    for i in range(a.days):
        day = today + dt.timedelta(days=i)
        k = str(day)
        holiday = hol.get(k)
        off = day.weekday() >= 5 or bool(holiday)
        kubun = ('休日' + (f'({holiday})' if holiday else '')) if off else '平日'
        wx = near_wx.get(k)
        if wx is None and k in wk:
            code, _, rel = wk[k]
            wx = WX.get(code[:1], '?') + (f' 信頼度{rel}' if rel else '')
        pops = near_pop.get(k)
        if pops:
            pop = max(pops)
            pops_s = '/'.join(map(str, pops)) + '%'
        elif k in wk and wk[k][1] != '':
            pop = int(wk[k][1])
            pops_s = f'{pop}%(週間)'
        else:
            pop, pops_s = None, '-'
        rainy = (pop is not None and pop >= 50) or (wx or '').startswith('雨')
        if pops and len(pops) == 2 and pops[0] >= 50 and pops[1] <= 20:
            judge = '午前は屋内・午後は屋外OK'
        elif pops and len(pops) == 2 and pops[0] <= 20 and pops[1] >= 50:
            judge = '午前は屋外OK・午後は屋内'
        elif pop is None and not wx:
            judge = '予報なし'
        elif rainy and (pop or 0) >= 70:
            judge = '屋内'
        elif rainy or (pop or 0) >= 40 or '雨' in (wx or ''):
            judge = '屋内寄り(屋外は晴れ間に短時間)'
        else:
            judge = '屋外OK'
        note = []
        if prev_rain and judge == '屋外OK':
            note.append('前日が雨=遊具・芝が濡れている')
        if tmax.get(k):
            note.append(f'最高{tmax[k]}℃')
        note.append('工事現場は休み(無人で撮りやすい)' if off else '工事現場は稼働(昼休み12〜13時は止まる)')
        print(f'{k:<10} {WD[day.weekday()]} {kubun:<9} {(wx or "-")[:28]:<30} {pops_s:<14} {judge}  ' + ' / '.join(note))
        prev_rain = rainy
    print('\n出典: 気象庁 福岡地方の予報(3日目まで)・福岡県の週間予報')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
