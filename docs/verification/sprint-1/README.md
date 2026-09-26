# スプリント1：人物原画の取り込み

2026年9月27日。原本は保管済みの36枚を変更せず使った。会話・事件用の静止ポーズ34体と、若い4人の動作ポーズ84コマを登録した。仲間 pc_01〜pc_04 の置換・職業変更・戦闘処理への接続は行っていない。

人物は32×48 px、自然色16色以内、二値透過。若い4人は立ち姿と動作を人物ごとの共通16色へそろえた。個々のポーズは武器・光を含む全形を収めるため、見かけの体格が異なる。連続再生する歩行・戦闘アニメーションとしては登録していない。

名前・性格・配置・ライバルかゲストかは未決。以下の役は採用済みの物語の大筋に対応する範囲だけを記録した。神の明暗対は原画の並び順が異なるため、原本スロットを個別に対応させた。

| 人物id | 原画・位置 | 役または候補 |
| --- | --- | --- |
| h_hooded_spirit | IMG_0940.PNG 左から2 | 役・配置とも未決 |
| h_masked_scout | IMG_0941.PNG 左から2 | 役・配置とも未決 |
| h_violet_mage | IMG_0941.PNG 左から3 | 役・配置とも未決 |
| h_bandit | IMG_0941.PNG 左から4 | 役・配置とも未決 |
| h_ochre_mage | IMG_0941.PNG 左から5 | 役・配置とも未決 |
| h_trident_merman | IMG_0947.PNG 左から5 | 役・配置とも未決 |
| h_ghost_sailor | IMG_0948.PNG 左から4 | 役・配置とも未決 |
| h_ghost_captain | IMG_0949.PNG 左から3 | 役・配置とも未決 |
| h_sea_king | IMG_0951.PNG 左から2 | 役・配置とも未決 |
| h_fairy_knight | IMG_0953.PNG 左から4 | 役・配置とも未決 |
| h_serpent_haired | IMG_0954.PNG 左から4 | 役・配置とも未決 |
| h_sun_guard | IMG_0956.PNG 左から1 | 太陽の神・明るい姿 |
| h_moon_robed | IMG_0956.PNG 左から2 | 月の神・明るい姿 |
| h_sea_god | IMG_0956.PNG 左から3 | 海の神・明るい姿 |
| h_red_guard | IMG_0956.PNG 左から4 | 戦いの神・明るい姿 |
| h_harvest | IMG_0956.PNG 左から5 | 実りの神・明るい姿 |
| h_reaper | IMG_0957.PNG 左から1 | 死者の国の役候補 |
| h_smith | IMG_0957.PNG 左から2 | 武器屋・特別な武器を作る人の候補 |
| h_white_spirit | IMG_0957.PNG 左から3 | 各地の守り手の候補 |
| h_tree_spirit | IMG_0957.PNG 左から4 | 各地の守り手の候補 |
| h_masked_spirit | IMG_0957.PNG 左から5 | 案内役の候補 |
| h_dark_sun | IMG_0958.PNG 左から1 | 太陽の神・黒く染まった姿 |
| h_dark_moon | IMG_0958.PNG 左から2 | 月の神・黒く染まった姿 |
| h_war_god | IMG_0958.PNG 左から3 | 戦いの神・黒く染まった姿 |
| h_wood_god | IMG_0958.PNG 左から4 | 実りの神・黒く染まった姿 |
| h_depth_god | IMG_0958.PNG 左から5 | 海の神・黒く染まった姿 |
| h_bishop | IMG_0959.PNG 左から2 | 役・配置とも未決 |
| h_pale_spirit | IMG_0959.PNG 左から3 | 役・配置とも未決 |
| h_stone_sage | IMG_0959.PNG 左から4 | 役・配置とも未決 |
| h_jester | IMG_0959.PNG 左から5 | 役・配置とも未決 |
| owner_young_01 | IMG_0961.PNG 左から1 | 別の冒険者の一行。ライバルかゲストか、名前・性格・登場場面は未決 |
| owner_young_02 | IMG_0961.PNG 左から2 | 別の冒険者の一行。ライバルかゲストか、名前・性格・登場場面は未決 |
| owner_young_03 | IMG_0961.PNG 左から3 | 別の冒険者の一行。ライバルかゲストか、名前・性格・登場場面は未決 |
| owner_young_04 | IMG_0961.PNG 左から4 | 別の冒険者の一行。ライバルかゲストか、名前・性格・登場場面は未決 |

## 神の姿の対応

| 柱 | 明るい姿 | 黒く染まった姿 |
| --- | --- | --- |
| 太陽 | h_sun_guard | h_dark_sun |
| 月 | h_moon_robed | h_dark_moon |
| 海 | h_sea_god | h_depth_god |
| 戦い | h_red_guard | h_war_god |
| 実り | h_harvest | h_wood_god |

## 確認画像と記録

- `characters-01.png`〜`characters-03.png`：原画、実寸、3倍表示。
- `young-01-poses.png`〜`young-04-poses.png`：若い4人のポーズ一覧。
- `target-character-compare.png`：目標の村と人物の色・縮尺の比較。参考画像はゲーム素材へ転用していない。
- `assets/source_records/owner-characters.json`：全118コマの切り出し座標、原本SHA-256、共通16色、出力SHA-256。

## 未提供・未接続

若い4人のうち4人目の詠唱・被弾・勝利の原画は未提供。今回の原画には含まれないため生成していない。全員の4方向歩行も今回の原画からは作れないため、歩行シートを偽造していない。物語への配置と画面への接続は後続の依頼で行う。

狛犬の対の候補は、既に登録済みの `gold_guard_lion` と `silver_guard_lion` の原画・画像を参照する。今回の用途のために敵の配置や画像を変えていない。

検査は `python tools/check_sprint1_characters.py`。完成時の固定タグを読み、後続スプリントの作業ツリーには依存しない。
