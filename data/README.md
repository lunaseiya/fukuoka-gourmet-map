# spots.json について

福岡(および周辺)の飲食店・宿泊施設データベース。`spots.json` は店舗情報の配列で、地図ページ(`map/index.html`)がこのファイルを読み込んで表示する。

## ファイル形式

配列の中に、店舗1件につき1つのオブジェクトを入れる。

```json
[
  { "id": "...", "name": "...", ... },
  { "id": "...", "name": "...", ... }
]
```

## 項目一覧

| キー | 型 | 説明 | 入力例 |
|---|---|---|---|
| `id` | string | 半角英数とハイフンのみ。店名のローマ字表記などから作る。**他の店と重複させない** | `"sharyo-wajiro"` |
| `name` | string | 店名 | `"資さんうどん 和白店"` |
| `area` | string | エリア名(駅・地区レベル) | `"和白"` |
| `city` | string \| null | 市区名。福岡市は区単位(`"福岡市東区"`)、それ以外は市町単位(`"大野城市"`)。マップの「市区で絞る」に使用。不明なら `null` | `"福岡市東区"` |
| `pref` | string \| null | 都道府県名。市区セレクトの並び順(福岡県内→県外)と県外ラベルに使用。不明なら `null` | `"福岡県"` |
| `genre` | string | ジャンル | `"うどん"` |
| `lat` | number \| null | 緯度。不明なら `null` | `33.6538` |
| `lng` | number \| null | 経度。不明なら `null` | `130.4419` |
| `visited` | string \| null | 訪問日。`"YYYY-MM-DD"` 形式。不明なら `null` | `"2026-08-06"` |
| `with` | string | 同行者。`"solo"` / `"friends"` / `"family"` のいずれか | `"family"` |
| `kids` | object \| null | 子連れ情報。下記「kids オブジェクト」参照。`with` が `"solo"` か `"friends"` なら `null` でよい | — |
| `verdict` | string \| null | 一言まとめ。不明・未執筆なら `null` | `"カウンター中心。抱っこ紐推奨"` |
| `video` | object | 各SNSのURL。下記「video オブジェクト」参照 | — |
| `thumb` | string \| null | サムネ画像のファイル名(`map/thumbs/` 内、幅240pxに縮小したもの)。無ければ `null` | `"sansenkaku-beppu.jpg"` |
| `wish` | boolean(省略可) | `true` なら「行きたい」(未訪問)スポット。ピンが青になり、動画リンクは無くてよい | `true` |
| `web` | string(省略可) | 公式サイト等のURL。設定すると「🌐 詳細」ボタンの飛び先になる(未設定はGoogleマップ検索に飛ぶ) | `"https://oncri.com/"` |
| `posted` | string(省略可) | 動画を投稿した日 `"YYYY-MM-DD"`。投稿から1週間はマップ・リストに NEW 表示される | `"2026-08-10"` |
| `category` | string(省略可) | `"onsen"` なら「日帰り温泉」タブに表示(スーパー銭湯・ホテルの日帰り湯含む)。省略時はグルメ・おでかけタブ | `"onsen"` |
| `bathAge` | string \| null(省略可) | 温泉スポット用。何歳から入浴できるか・オムツ児可否など | `"オムツの取れていない子はベビーバス利用"` |
| `ages` | string[] \| 省略可 | 向いている年齢(2026-10-01追加)。`"baby"`=乳幼児(0〜2歳) / `"toddler"`=幼児(3〜6歳) / `"kids"`=小人(小学生)。**根拠があるものだけ**。マップのバッジと「年齢」絞り込み(選んだ区分を全部満たす所)・詳細ページの「向いている年齢」に出る | `["baby","toddler","kids"]` |
| `photos` | string[](省略可) | ギャラリー写真のファイル名(`map/photos/` 内、幅1080)。詳細カードに横スワイプで出る | `["tsubuku-park_01_園内.jpg"]` |
| `photoCredits` | object[](省略可) | **自分で撮っていない写真**(ウィキメディア・コモンズ等のCCライセンス写真)を `thumb`/`photos` に使ったときの出典。`{author, lic, url(ファイルページ), licurl}` の配列。カードに「📷 写真: 作者 / ライセンス」が出る(2026-10-12追加)。**他人のSNS投稿や自治体サイト(All rights reserved)の写真は載せない**。自分で撮った写真に差し替えたらこの項目ごと消す | `[{"author":"Peka","lic":"CC BY-SA 4.0","url":"https://commons.wikimedia.org/wiki/File:Kurume_Tsubuku_Park.jpg","licurl":"https://creativecommons.org/licenses/by-sa/4.0"}]` |
| `ages_src` | string(省略可) | `"manual"`=実際に行って付けた(自動付与で上書きしない) / `"auto"`=tools/assign_ages.py が説明文・ジャンルから付与 | `"manual"` |

### kids オブジェクト

`with` が `"family"` のときに埋める(それ以外は `kids` ごと `null` でよい)。

| キー | 型 | 説明 | 入力例 |
|---|---|---|---|
| `stroller` | boolean \| null | ベビーカーで入店できるか | `true` |
| `diaper` | boolean \| null | おむつ替え台があるか | `false` |
| `tatami` | boolean \| `"banquet"` \| null | 座敷・小上がりがあるか。宴会用で普段使えないなら `"banquet"` | `true` |
| `kidsChair` | boolean \| null | キッズチェアがあるか | `true` |
| `kidsMenu` | boolean \| null | キッズメニュー(お子様ランチ等)があるか | `true` |
| `sofa` | boolean \| `"board"` \| null | ソファ席があるか。板張りのソファ(クッションなし)は `"board"` | `true` |
| `horigotatsu` | boolean \| null | 掘りごたつの席があるか | `true` |
| `babyKeep` | boolean \| null | トイレに補助チェア(ベビーキープ)があるか | `true` |
| `kidsPlate` | boolean \| null | 子供用の食器(取り皿・スプーン)があるか | `true` |
| `kidsSpace` | boolean \| null | キッズスペース・おもちゃ・赤ちゃんを寝かせられる席があるか | `true` |
| `serveMin` | number \| null | 提供までの実測分数 | `12` |
| `noise` | string \| null | 騒音許容度。`"ok"` / `"careful"` / `"ng"` | `"ok"` |

**子連れの判定は「歓迎」と「可」の2段(2026-10-19ユーザー確定)**:
- **歓迎** = 店が子供のために用意しているものがある … `kidsChair`・`kidsMenu`・`diaper`(店の)・`kidsSpace`・`tatami:true`(普段使える座敷)。
  ほかに家族風呂・貸切風呂、家族で行った遊び場・宿(赤ピン・with:"family"・グルメ以外)
- **可** = 子供と座れる/入れるが店は大人向け … `sofa:true`・`horigotatsu`・`stroller`・`babyKeep`・`"facility"`(モール等の建物にある)。
  △(`kidsPlate`・`sofa:"board"`)は2つ以上で可、1つだけは入れない
- **喫煙可の店は無条件に「歓迎」にしない**(最大でも可)。トップレベルの `smoking`: `"ok"`=喫煙可 / `"separate"`=分煙 / `"no"`=禁煙(未入力は verdict の「喫煙可」「全席喫煙」等から拾う)。**分煙は判定に影響させない**(2026-10-19ユーザー確定)
- `tatami:"banquet"` = 座敷はあるが宴会用(普段は使えない)。数えない。⚠**掘りごたつを `tatami` で代用しない**(`horigotatsu` を使う)
- 新項目が未入力の店は verdict の文言からも拾う。実装は `map/index.html` の `kidsLevelOf()`。
  マップの子連れボタンは押すたびに 歓迎(初期) → 可まで → すべて

### video オブジェクト

3つのキーは常に用意し、URLが無いものは `null` にする。

| キー | 型 | 入力例 |
|---|---|---|
| `youtube` | string \| null | `"https://youtube.com/shorts/xxxx"` |
| `tiktok` | string \| null | `"https://www.tiktok.com/@xxx/video/xxxx"` |
| `instagram` | string \| null | `"https://www.instagram.com/reel/xxxx"` |

## ルール

- **未確認の項目はすべて `null`**。空文字 `""` や `0` を代わりに使わない(「未入力」と「値がゼロ」を区別するため)
- 日本語はエスケープしない(`テ...` のような形にしない)
- `id` が重複する店舗は追加しない

## 新しい店舗を追加する手順

1. `spots.json` を開き、配列の最後の `}` の後ろに `,` を足す
2. 上記スキーマに沿って新しいオブジェクトを追記する
3. `id` が既存のものと重複していないか確認する
4. 分かる項目だけ埋め、残りは `null` のままにする(推測で埋めない)
5. JSONとして正しいか(カンマ抜け・閉じ忘れがないか)を確認して保存する

Claude Code に「動画リストから spots.json に追記して」と頼む場合は、店名・エリア・動画URLの一覧を用意してから渡すとスムーズ。
