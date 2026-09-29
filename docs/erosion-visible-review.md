# 侵蝕の見分けやすさ：発光模様・輪郭光・段階印

依頼者はスイナの再配色と、90以上を既存の魔物姿で比較する案1を採用した。今回の基準は `405fd257fb60cc550cd40c2d693b124317b57ffa`。開始時の未コミット変更・未pushコミットは0件。

## 今回の変更

- 模様の暗い芯を、白に近い色へ変更した。カイナは明るい水色の縁と近白色の芯を使う。
- 兆候（30〜59）は片腕と頬へ広げた。変異（60〜89）はその模様を保って、両腕・首・頬へ広げた。
- 変異では、人物のシルエットの内側に沿って戦闘素材2画素・歩行素材1画素の光を付けた。元の透過形状、表示サイズ、足元は変更していない。
- 戦闘ステータスの名前欄の横に、兆候は三角、変異はひし形、不可逆は交差形の小さな印を追加した。平常は印なし。マウスを重ねると段階と値を確認できる。
- 90の見本は採用済みのカイナのスライム姿を使用した。侵蝕の値・条件・不可逆・職業変更の仕組みは変更していない。

リオネは明るい赤茶、ハルドは白に近い淡い金、スイナは明るい紫という方針を仕様書へ記録し、段階印の色にも使用した。今回の模様の位置合わせと画像はカイナの戦士のみ。他の3人・11職の模様は未制作。

## 原寸の比較画像

ゲームの内部解像度は512×288、標準ウィンドウは整数2倍の1024×576。今回の上段は標準ウィンドウの撮影画像を、拡大・縮小せずそのまま配置した。比較画像は横4枚で4096px幅になる。単独画像も保存したため、画像ビューアの自動縮小の影響を避けて原寸で確認できる。

- [戦闘4段階の比較](verification/erosion-visible/battle-stages.png)
- [歩行4段階の比較](verification/erosion-visible/walk-stages.png)

| 段階 | 戦闘の単独画像 | 歩行の単独画像 |
| --- | --- | --- |
| 平常・侵蝕0 | [戦闘](verification/erosion-visible/runtime/battle-0.png) | [歩行](verification/erosion-visible/runtime/walk-0.png) |
| 兆候・侵蝕30 | [戦闘](verification/erosion-visible/runtime/battle-30.png) | [歩行](verification/erosion-visible/runtime/walk-30.png) |
| 変異・侵蝕60 | [戦闘](verification/erosion-visible/runtime/battle-60.png) | [歩行](verification/erosion-visible/runtime/walk-60.png) |
| 不可逆・侵蝕90、スライムの例 | [戦闘](verification/erosion-visible/runtime/battle-90.png) | [歩行](verification/erosion-visible/runtime/walk-90.png) |

上段8画面が元の撮影画像と全画素一致することを `comparison-checks.json` に記録した。下段だけ人物部分を拡大している。本番の描画・移動・保存形式を使用するが、侵蝕値とマスター済み状態は素材確認用の明示入力であり、本編到達の実測ではない。

## ファイルと検査

- 模様の重ね絵・合成画像8枚、素材台帳と制作記録、`tools/build_erosion_pattern_preview.py`。
- 段階印：`scripts/ui/erosion_stage_mark.gd`、`scripts/ui/first_region_screen.gd`。
- 今回追加した撮影・検査：`tools/capture_erosion_visible.gd`、`tools/check_erosion_visible.py`、`tools/build_erosion_visible_review.py`。
- 仕様・計画：`docs/experience-spec-v2.md`、`docs/roadmap-v2.md`、本書。

| 実行コマンド | 結果 |
| --- | --- |
| `python tools/build_erosion_pattern_preview.py` | 明るい模様、変異の輪郭光、合成画像を作成 |
| `godot --headless --editor --import --quit` | 成功、エラー・警告なし |
| `godot --path . --rendering-method gl_compatibility --script res://tools/capture_erosion_visible.gd` | 289項目成功、4段階の戦闘・歩行8枚を撮影 |
| `python tools/build_erosion_visible_review.py` | 上段8画面の全画素一致を確認 |
| `python tools/check_erosion_visible.py` | 近白色・範囲拡大・輪郭光・元衣装不変・対象外681件不変を確認 |
| `python tools/validate_assets.py --strict` | 素材673件・音14件・字体2件、問題なし |
| `python tools/check_frozen_files.py` | 保護対象26件、一致26件 |
| `python3 D:/Codex/.codex/scope-lock/scripts/verify_cli.py --quiet .` | R-01〜R-08すべて成功 |

既存の検査、保護ファイル、パレット、project.godotは変更していない。既存衣装とスイナの採用済み再配色を含む対象外の登録ファイル681件をバイト単位で照合した。模様の拡大・明るさ・輪郭光の構成を機械で確認し、原寸で見分けられるかの採否は依頼者の画像確認に残す。

初回の撮影処理では内部解像度512×288をウィンドウ寸法と取り違え、実寸検査が失敗した。固定設定を確認し、標準ウィンドウ1024×576の撮影画像を上段へ無加工で置く形へ修正した。ゲーム設定の変更や、撮影画像を縮めて寸法を合わせる処理は行っていない。

今回は比較画像を報告して止まる。他の人物・職業の模様、スプリント5の残りには進んでいない。
