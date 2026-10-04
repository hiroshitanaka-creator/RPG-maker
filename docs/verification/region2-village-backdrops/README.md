# 原画・派生・実表示の比較（採用未確認）

2026-10-04 UTC。村外観と4室の独立した背景土台。機械検査の成功と初回見た目の採用は別に扱う。本番の移動先・保存先・施設機能・NPC・会話・品目・職業解放場面は未接続。

| 対象 | 6面の比較 | 原画・変換だけの比較 | 実表示の手前／奥 |
| --- | --- | --- | --- |
| 外観 | [exterior/review-comparison.png](exterior/review-comparison.png) | [source-comparison.png](exterior/source-comparison.png) | [手前](exterior/native-detail.png) / [奥](exterior/native-behind.png) |
| 宿の室内 | [inn/review-comparison.png](inn/review-comparison.png) | [source-comparison.png](inn/source-comparison.png) | [手前](inn/native-detail.png) / [奥](inn/native-behind.png) |
| 道具屋の室内 | [item/review-comparison.png](item/review-comparison.png) | [source-comparison.png](item/source-comparison.png) | [手前](item/native-detail.png) / [奥](item/native-behind.png) |
| 武器屋の室内 | [weapon/review-comparison.png](weapon/review-comparison.png) | [source-comparison.png](weapon/source-comparison.png) | [手前](weapon/native-detail.png) / [奥](weapon/native-behind.png) |
| 祠の室内 | [shrine/review-comparison.png](shrine/review-comparison.png) | [source-comparison.png](shrine/source-comparison.png) | [手前](shrine/native-detail.png) / [奥](shrine/native-behind.png) |

各6面：原画と派生、通行判定と扉、実表示の人物尺度、既存の目標、上層の奥、上層の元画素。画像は比較用に最近傍で紙面へ配置したもので、ゲーム本体の出力解像度は512×288。

- `data-checks.json`：原本5点全バイト・SHA、規定色、全画素、連結性、入口、2回再生成の243検査PASS。
- `runtime-checks.json`：本番の通行・移動APIによる2,170検査PASS。
- `native-checks.json`：Godot 4.7.2-stableのWindows/OpenGLネイティブ描画、2,230検査PASS。25枚を保存。
- `native-pixel-checks.json`：独立画素合成と実表示25枚の差は全て0。手前の遮蔽0、奥は人物が部分的に隠れ、可視画素もある。
- 原本と既存パレットはバイト不変。追加色0。目標画像・原画・実表示のSHAは記録内に保持。

通常の進捗報告には具体的な場面画像を表示せず、区切り末の確認用リンクとして渡す。見た目の採用、色調・尺度・歩きやすさの人間評価は未実施で、PLAYTEST_QUEUEに記載。

## 004 の最新比較

開始main・今回004・原画・既存目標・実描画を6面で識別した5比較。原画と目標は参照のみ。初の採否は未確認。

| 対象 | 004比較 |
| --- | --- |
| 外観 | [exterior/color-review-004.png](exterior/color-review-004.png) |
| 宿 | [inn/color-review-004.png](inn/color-review-004.png) |
| 道具屋 | [item/color-review-004.png](item/color-review-004.png) |
| 武器屋 | [weapon/color-review-004.png](weapon/color-review-004.png) |
| 祠 | [shrine/color-review-004.png](shrine/color-review-004.png) |

最新実行：原画照合244項目、独立2回再生成全バイト一致、通行2170項目、Windows/OpenGL2230項目・実描画25枚の独立合成差0。原画5点・先頭80色1940バイト・村以外の1538素材・全通行／上層形状は不変。原画の実画素4色を末尾追加。停止11負例と追加4負例は拒否。

- `palette-validation-004.json`：停止11負例を含むパレット14負例。
- `color-integrity-004.json`：追加4色の実出所・旧80色近似誤差・使用画素数・原画との色差、全形状・村外実体1バイト負例。
- `comparison-index-004.json`：5比較と原画・目標・最新実描画のSHA。

上段の追加色0・243検査等は初期土台の実測履歴。CIとmain反映・指揮役の確認状態は [004報告](../../tasks/reports/004-resume-village-colors.md) を参照。
