# 028 遺跡ボスの表示を約1.5倍にする — 作業・検証報告

## 基点と検証計画

- 指定基点：`a5f3f65dcb63e8fa86a8c68e702ebf931115cd85`。027制作完了：`3ca51fcd756d885d6e0fd309f47efee3b841050c`。開始時の未コミット変更0。既存ローカルworkブランチは保持し、対象ブランチを指定SHAから作成した。
- 最新main：`e9ecb5a5be6bc1e3ad01c55e2dfec040e442cdb2`。共通基点からmainだけの変更は移行済み親文書2件のみ。028では親文書に触れず、011・027の保存済み成果を保持する。mainへ直接commit／push／統合しない。
- 変更対象：`scripts/ui/rpg_battle_view.gd` の巨像ID限定倍率、`tools/capture_task011_ruins.gd` の画素参照座標（独立した指定倍率）。原画・派生PNG・素材台帳・能力値・本番遭遇を変更しない。
- 倍率：元の実画素bbox122×152に対し0.75→1.125。表示bbox91.5×114→137.25×171、縦横各1.5倍。足元(170,196)を保持する。
- 前後比較：基点の別checkoutと最新で同じ確認用状態・Godot4.7.2・X11/Vulkan・1024×576を使用。巨像の表示bbox／最近傍の全画素／画面内／味方・下部UI分離を検査。他の敵6体の2画面は全画素一致、本番敵全36種の領域・配置も基点と一致することを新規検査で照合。原画を含む全assetsは基点Git blobと全バイト照合。
- 既存011撮影の倍率0.75固定だけを依頼者指定の巨像1.125／他敵0.75へ変更し、全画素一致・境界候補・色差1・assertion・全25枚・時間上限は保持する。011完成固定SHAとCI登録SHA、011以前の検査、workflow、保護ファイルは不変。

## 表示・素材・画素の結果

Godot4.7.2（`4.7.2.stable.official.ed1daf0bf`）、X11／Vulkan／llvmpipe、同じ確認用パーティと背景、1024×576の実画面。ZIP SHA-256はCI固定の `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` と一致した。

| 項目（内部512×288の座標） | 修正前 | 修正後 |
| --- | --- | --- |
| 素材の実画素region `[x,y,w,h]` | `[35,6,122,152]` | 同一 |
| 表示rect `[x,y,w,h]` | `[124.25,82,91.5,114]` | `[101.375,25,137.25,171]` |
| 素材に対する倍率 | 0.75 | 1.125 |
| 現状からの幅・高さの倍率 | 1 | **各1.5** |
| 足元中心 | `(170,196)` | 同一 |
| 画面上端からの余白 | 82px | 25px |
| 下部UI開始223pxまでの余白 | 27px | 27px |

- 修正前のbattle-3は011提示画像と全バイト一致。拡大後の敵・透明部の最近傍照合は93,708／93,708画素一致。前後各93検査、実測撮影12.236秒／12.213秒、元の180秒上限内。
- 前後画像の変化は巨像領域だけで53,856画素、実変化bboxは1024×576上の`[203,50,477,392]`。それ以外の背景・味方・表示文字は全画素一致。味方4人の待機／30px前進位置との交差なし。
- 他の敵42体（本番36種＋遺跡の他6種）の素材region・表示rect・足元を基点と照合し全一致。他6体のbattle-1／battle-2はPNG全バイト一致。
- 原画・台帳・派生素材を含むassets全1,611ファイルを基点のGit blobと全バイト照合し一致。巨像原画のSHA-256は `560358d71d33cfafda538d7abf2dd2d1879b3163d9a4484dbbeaaedfd48f215a`、既存派生PNGは `ef665f5c2a1630a85185da306388eedcb2c4e974c621c81eeab74882a06695a0` のまま。色追加0。
- 基点は完全SHAに固定した別checkout。本番コードは当時のものを使い、028の共通撮影検査器とUIDだけを持ち込み、前後同じ入力・撮影手順で比較した。

## 画像

- `docs/verification/task-028/before/battle-3.png`：修正前。
- `docs/verification/task-028/after/battle-3.png`：修正後。
- `docs/verification/task-028/before-after.png`：左が前、右が後。各画面を原寸で並べた比較。
- `before/`・`after/`のbattle-1／battle-2：他敵不変の証拠。
- `checks.json`・前後`checks.json`・`image-manifest.json`：SHA、寸法、画素・レイアウトの照合結果。

Library保存は現行スキルの正式prepared-upload helperを使ったが、`hosted apps tools/list request failed: network`で準備前に終了1。確認済みLibrary IDは0件。直接アップロードへ切り替えず、全画像をこのブランチへ保持する。詳細は`library-save.json`。親の接続環境での再保存は未達。

## 検証

最終実装・検査器SHA：`9a691bdfb5bec12cd421c92cdcb9d07ef3e8f7c6`。本番描画は045423aの初回全検証と同一。最終変更は撮影検査のUV計算を、実測倍率ではなく巨像1.125／他敵0.75の独立した指定値へ固定したもの。検査の自己一致を避け、他敵の従来の0.75期待を保持する。

| 実行コマンド | 結果・記録 |
| --- | --- |
| `godot --headless --editor --import --quit` | 終了0、エラー・警告0。`import.log`、追加検査器の`import-after.log`、基点別checkoutの`before-import.log` |
| `python tools/validate_assets.py --strict` | 終了0、素材1154・音15・字体2・パレット3、問題なし。`assets.log` |
| `python tools/run_locked_checks.py` | 終了0、R-01〜R-08全PASS、全tests_ran=true／parser_failed=false。`locked.log`・`locked.json`。本番・保護対象は最終実装と同一 |
| `python tools/check_frozen_files.py`（前後） | 終了0、保護26／26一致。最終は`frozen-after.log` |
| `python -B tools/check_task028.py --godot /tmp/task028/bin/godot` | 最終実装9a691bdで終了0。前後各93検査、画素・画面内・他敵・全素材・許可範囲・011撮影のassertion不変を照合。`checks.json` |
| `python tools/check_task011.py --completed d258908fbb0397e64d08780694786ef1855c4979 --godot /tmp/task028/bin/godot` | 初回045423aで終了0、固定／最新／027の全PASS。`initial-full-045423a/summary.json`・`run.log` |
| `python tools/check_task011_ci_boundary.py --godot /tmp/task028/bin/godot` | 初回045423aで終了0、正1・負3 PASS。CI固定点8ae87d6不変。`initial-full-045423a/ci-boundary.json`・`.log` |
| `xvfb-run -a godot --path . --rendering-method mobile --rendering-driver vulkan --audio-driver Dummy --script res://tools/capture_task011_ruins.gd` | 独立期待値へ変更後の9a691bdで終了0、全25枚・315キー歩・元の全画素／状態条件PASS。実行SHAのJSON一致とbattle-3の新規028撮影との全バイト一致を照合。`final-existing-capture.json`・`.log` |
| `git diff --check`／基点からの範囲照合 | 不正空白なし。原画・他素材・能力値・world・保護ファイル・011以前の検査・workflow・親文書に差分なし |

初回の固定import38.038秒、素材30.753秒、runtime6.571秒、capture120.416秒。最新素材3.324秒、runtime6.743秒、capture120.221秒。027正1・負7、毎歩通知の25枚・309復帰・歩行4枚すべて本番コマ1、stage拒否1が全PASS。通知あり撮影176.454秒／180秒。既存の600／180／120秒・各jobの上限を変更していない。初回検証のSHAを最終検証のSHAとして扱わず、最終CIで最終提出点の全既存検査を再実行する。

準備時の日本語パスのGit引用、隔離先へのUID持込み不足を直して新規検査を再実行した。最後の既存撮影は実行SHA環境変数の取り違えを中断し、`git rev-parse HEAD`を入力に正式再実行。中断した結果は採用していない。

## CIと引渡し

- 初回全検証045423aのpush CI：[CI 37295772283](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37295772283)、[固定／最新 37295772170](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37295772170)。提出準備時点のジョブ実物を`ci-at-report.json`へ保存する。進行中を成功と表記しない。
- 提出コミット自身のCIはpushで起動する。本書に未実行の成功は記載しない。全20ジョブの終了・結果を直接照会してから、最終SHA・runリンク・残件を親への最終通知で返す。
- workflowを変えず、通常の3＋17ジョブを保持する。新規028検査はローカルで独立実行し、既存CIの固定版／最新／027全検査と区別する。
- 主な変更：`scripts/ui/rpg_battle_view.gd`（ID限定倍率を描画と配置で共通化）、`tools/capture_task011_ruins.gd`（当該UVの倍率のみ）、新規`tools/check_task028.py`・`tools/check_task028_capture.gd`・UID、依頼書の状態・本報告・`docs/decision-log.md`、`docs/verification/task-028/`。
- 成果は指定ブランチへcommit／pushして返す。mainへのcommit／push／マージなし。旧親文書を変更せず、011・027完成固定SHAも保持する。

## 未達・採否

- Library保存：ネットワーク接続失敗、保存確認済みID0件。画像は全てブランチで保全。
- 見た目の採否：親が依頼者へ前後画像を提示して確認する。子から採用済みにしない。
- 作業範囲の表示調整・機械検証に未実装項目なし。本番の遭遇・ボス戦・物語の接続は変更していない。新たに決定を求める事項なし。
