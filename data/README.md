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

### kids オブジェクト

`with` が `"family"` のときに埋める(それ以外は `kids` ごと `null` でよい)。

| キー | 型 | 説明 | 入力例 |
|---|---|---|---|
| `stroller` | boolean \| null | ベビーカーで入店できるか | `true` |
| `diaper` | boolean \| null | おむつ替え台があるか | `false` |
| `tatami` | boolean \| null | 座敷・小上がりがあるか | `true` |
| `kidsChair` | boolean \| null | キッズチェアがあるか | `true` |
| `serveMin` | number \| null | 提供までの実測分数 | `12` |
| `noise` | string \| null | 騒音許容度。`"ok"` / `"careful"` / `"ng"` | `"ok"` |

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
