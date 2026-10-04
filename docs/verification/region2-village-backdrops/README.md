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
