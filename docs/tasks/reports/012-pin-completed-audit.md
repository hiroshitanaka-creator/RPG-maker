# 012 完成点固定修正の報告

状態：報告済み。実装・独立反証・push/PR/main全CI成功、通常main統合済み。009は差し戻し・親確認待ちを維持し、009/012の確認済み判定は親が行う。

## 変更一覧

- `.github/workflows/region2-village-connections.yml`：git log/作業中ならGITHUB_SHAという可変選択を、完成009 SHAと当時の検査器の別checkoutへ置換。012の別checkoutと180秒以内の再発検査を追加。既存17job・各コマンド・上限を保持。
- `tools/test_task012_pinned_audit.py`：不変SHA・tree・checkout・範囲、後続commit正例、異常SHA/不存在/改変/範囲違反の負例、旧方式の誤拒否を検証。012完成workflowを開始版へ逆変換して全文照合し、選択以外の既存項目/上限変更を拒否。
- `docs/tasks/009-test-lifecycle.md`：状態行だけ差し戻しへ変更。
- `docs/tasks/012-pin-completed-audit.md`：状態行だけ更新。
- `docs/decision-log.md`：不変完成点と2commit方式の理由・戻し方を記録。
- `docs/tasks/reports/012-pin-completed-audit.md`：本報告。
- `docs/verification/task-012/**`：開始計画、009完成CI、012固定記録、独立反証、ローカル実行、CI全job・実行SHA一致の新規証拠。

開始main `ce07fdada0466138260ab678c10fd78e61c0c63d`。開始作業 `8ed58c00f8d7d16e2df24f3273f18019d2406002`。a1022b6の010/011原本登録は保持し、007/008/010/011は未着手。指定開始時は未コミット0件、mainにないのは親登録と012登録の2件。実装push後も未push0件（remoteのfetch対象がmain限定のため作業refを明示更新して照合）。

## 固定点と最新対象

| 検査 | 対象 | 実行場所・検査器 |
| --- | --- | --- |
| 固定006全受入・範囲・描画 | `5f1c2ba231191b25b9b32a814b616a9f8d0a54ce` | fixed checkoutの当時コード/期待値/元検査器。7592項目・20保存・5別プロセス、通常描画7mode・49枚全実行 |
| 固定009範囲 | `ce07fdada0466138260ab678c10fd78e61c0c63d` | completed009 checkoutの当時check_task009_scope.py。独立tree `655312a33364d8e3fe97f09bd9bd3c415ed1ceae`と照合 |
| 固定012完成範囲 | `c327e7c439c9c8c8f1fd640e6cda6df7550fb26a` | completed012 checkoutの当時test_task012_pinned_audit.py。開始8ed58c0との完成差分だけ監査 |
| 最新継続回帰・描画・正負例 | 各push/PRの`GITHUB_SHA` | current checkoutの本番API。7662項目・20保存・5別プロセス、通常描画7mode・49枚、既存正例3/負例4全実行 |

機能完成 `c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`、tree `1a128f883bd555653bd9eea3082c09b875c1f7e5`。
固定記録 `9e647b3d6d0f91b061f7de974dbb5411937a2bb9`。完成commit作成後に独立manifestで完全SHA/treeを記録し、workflowの参照と照合する。状態変更や報告commitで固定点を再探索せず、後続差分全体を009/012の範囲として監査しない。固定記録後に新タスクを要求する再帰構造はない。

009完成候補はmain専用 [37195689879](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37195689879) 17/17、通常 [37195689874](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37195689874) 3/3の終了・成功とtree内容を照合（ce07-all-ci.json）。

## 独立コピーの反証

`pinned-audit/summary.json`、各ケースの.log/.jsonに入力SHA・選択SHA・元検査器の監査結果を保存。独立期待値は依頼書から転記し、実装値から生成しない。012のSHA/treeは機能完成commit後の独立固定記録を使用。ローカル17ケースPASS。push CIでも同じ17ケースを実行。

| 入力 | 期待と観測 |
| --- | --- |
| new-request | 新規099コピー依頼書追加。006/009/012不変、元009固定監査終了0 |
| 009-state-only | 状態行だけ更新。同じ固定3点、終了0 |
| state-and-new-request-same-commit | 状態行と新規依頼書を同一commit。同じ固定3点、終了0 |
| state-and-010-011-same-commit | currentの原本010/011と状態行。同じ固定3点、終了0（010/011は既存なので次の歴史入力でも追加を再現） |
| historical-state-and-010-011-added | 009完成treeを親に、状態行と010/011原本を実際に同時追加。修正workflow/固定記録を使用して同じ固定3点、終了0 |
| future-other-scope | 別範囲の本番ファイルへコピー限定コメント。同じ固定3点、終了0。新機能を実装したとは扱わない |
| 012-state-only | 012の親確認状態だけ更新。012自身も完成c327e7cを継続監査、終了0 |
| old-selector-parent-registration | 元git log方式はa1022b6を選択。変更していない元009検査器が010/011の2パスを拒否し終了1。修正でこの誤適用を解消 |
| wrong009-sha / wrong012-sha | 実在する異なる完全SHAへ誤選択。独立期待値不一致で拒否 |
| nonexistent-sha / nonexistent-object | 全0の完全SHA。選択不一致とgit実在検査の両方で拒否 |
| broken009-target | 009完成対象のコピーへ担当外ファイルを混入。元009検査器が該当パスを拒否し終了1 |
| broken012-target | 012完成対象のコピーへ本番変更を混入。012固定範囲監査FAIL、該当本番パスを列挙 |
| modified009-checkout | 別checkoutの当時検査器へコピー限定改変。実行前に不変違反を拒否 |

正常ケースの成功だけでなく、負例は元検査器の終了1/実assertion失敗を確認。timeout・parse errorは負例成功として数えない。

## 既存009負例と最新検証

`local/negative-cases/summary.json`：正例3・負例4全PASS、本番バイト不変。
NPC床の配置前後プローブ各39項目、後続依頼書+NPC占有の正例7656項目成功。占有無視は39項目の2assertion失敗、誤接続は最新7662項目で扉リンク等が失敗、不正room5の保存受理は最新7662項目で拒否/全状態保持5assertion失敗。いずれも終了1、parser_errors=false。既存異常006 SHAも拒否。後続007サービスは未実装・未検証のまま。

ローカルで実行したコマンド：

- 指定ZIP SHA256照合、Godot `4.7.2.stable.official.ed1daf0bf`。
- `timeout 600 Godot --headless --path <current/fixed006> --editor --import --quit`：双方終了0、SCRIPT ERROR/ERROR/WARNING/Parse Error 0。
- `timeout 180 python <completed012>/tools/test_task012_pinned_audit.py --current-path . --fixed009-path <completed009> --completed012-sha c327e7c... --latest-sha 9e647b3...`：17ケースPASS。
- `python tools/check_task009_lifecycle.py --fixed-sha 5f1c2ba... --fixed-path <fixed006> --godot <指定Godot>`：7592・20保存・5再起動9/26/37/51/43、範囲PASS。
- `python tools/check_region2_village_regression.py --commit HEAD --godot <指定Godot>`：9e647b3の最新7662・20保存・5再起動10/27/38/52/44、PASS。
- `python tools/test_task009_lifecycle.py --fixed-path <fixed006> --godot <指定Godot>`：上記正例3/負例4、PASS。
- `python tools/run_locked_checks.py`（指定GodotをPATHへ設定）：R-01〜R-08の8件全PASS、local/scope-lock-current.jsonとlocal/locked.logに保存。
- `python tools/check_task009_assertion_map.py`：135箇所、未分類0。
- `python tools/check_frozen_files.py`：保護26/26一致。
- `git diff --check`、完成012範囲、007/008/010/011の原本照合：成功。生成された009既存証拠は012へ今回実行分だけ保存して原本へ戻す。

ローカル描画は未実行。描画の成功根拠は下記GitHubの全mode実行証拠であり、過去の画像を今回描画と数えない。

## CIと上限

push対象/最新実行SHA `9e647b3d6d0f91b061f7de974dbb5411937a2bb9`。専用 [37196997061](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061) 17/17、通常 [37196997052](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997052) 3/3、計20/20終了・success。全job結果・日時・所要秒・上限・実際のJSON/PASSマーカーは `ci/push-all-jobs.json`。最大job273秒。009固定範囲ce07fda、012固定範囲c327e7c、最新9e647b3をログの実行値で区別。

最新runtime artifact11301298494はZIP SHA256 `08f3ddd1fb3554cfd16e8add59f99f4068b3dd6e7f7d9940f55ebb138b3e7162`を照合し、今回9e647b3に一致する7JSONだけci/push-runtime/へ保存。runtime7662、20保存、5再起動全成功。既存の同梱画像/過去証拠を今回結果と混ぜない。

専用17jobは各15分、import600秒、Godotプロセス/描画各180秒、描画内部180000ms/600移動/3000入力/300ターン。新規012反証も外側180秒以内。通常CIはpreplay35分、Godot25分、素材jobは元のtimeout未指定のまま。Rverify300秒。項目削除、黙ったskip、continue-on-error、時間延長、ALLOWED拡張0。matrixの既存ifによる固定/最新の分担は維持し、両側全ジョブを確認する。

PR対象HEAD `9e647b3d6d0f91b061f7de974dbb5411937a2bb9`、実行checkout/最新回帰 `3bca09749519d6124ad22922d678fc9ef6d6c557`。専用 [37197047782](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782) 17/17、通常 [37197047785](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047785) 3/3、計20/20終了・success。各run-IDのJSONへ全job・上限・実行値を保存。PR専用最大job275秒。固定006/009/012はpushと同一、最新側だけPRのmerge checkout SHAを使用した。

PR #17は通常mergeし、main SHA `15248ac3f93b30ed75760b7dbd50fb880d64af56`。main取得後のimportも終了0・警告/エラー0（main-import.log）、保護26/26一致、012反証17ケースPASS。pinned-audit/summary.jsonのlatest_shaはこのmain SHA。main専用 [37197767478](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478) 全17、通常 [37197767572](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767572) 全3、計20/20終了・success。実行checkout/最新回帰は同じmain SHA。全jobの日時・秒数・上限・JSON・R全8のPASSマーカーをci/run-37197767478.jsonとci/run-37197767572.jsonに収録。専用最大job276秒。固定006/009/012全監査、135分類、17追加反証、既存正例3/負例4、通常操作/描画全modeを省略せず成功。

main最新artifact11302125175のZIP SHA256 `5ebe38f929c30182b6916b305dbcc3876aeb7de44d86ed8d62e7b00872094ba3`と実行SHAを照合し、7JSONだけci/main-runtime/へ保存。最新7662・20保存・5再起動10/27/38/52/44成功。

本報告保存commitと、そのcommitのbranch/main全CI結果・最終main完全SHAは最終応答へ記録する。自分自身のcommit SHAを文書へ書くためだけの無限な追記commitは作らない。報告後も固定006/009/012の参照は上記3点のまま。

## 残る制約

人間試遊・約60時間の実測・未発注の後続機能は今回実施しない。未実施を成功扱いせず、007/008/010/011未着手と原本不変を維持。009/012の確認済み判定は親に残す。新規の判断依頼は0件。

## 全CIジョブ一覧（機能完成・統合時の60件）

| イベント/対象HEAD | job | 結果 | job秒 | job上限分 |
| --- | --- | --- | --- | --- |
| push 9e647b3 | [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997052/job/111420838817) | success | 273 | 35 |
| push 9e647b3 | [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997052/job/111420838913) | success | 95 | 元の未指定 |
| push 9e647b3 | [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997052/job/111420838981) | success | 220 | 25 |
| push 9e647b3 | [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838749) | success | 104 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838842) | success | 257 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838848) | success | 223 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838856) | success | 158 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838860) | success | 168 | 15 |
| push 9e647b3 | [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838865) | success | 128 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838871) | success | 203 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838873) | success | 128 | 15 |
| push 9e647b3 | [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838878) | success | 228 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838882) | success | 214 | 15 |
| push 9e647b3 | [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838888) | success | 183 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420838964) | success | 169 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420839052) | success | 218 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420839061) | success | 143 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420839091) | success | 157 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420839096) | success | 202 | 15 |
| push 9e647b3 | [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37196997061/job/111420839109) | success | 264 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047785/job/111420979740) | success | 267 | 35 |
| PR 9e647b3 / checkout 3bca0974 | [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047785/job/111420979828) | success | 105 | 元の未指定 |
| PR 9e647b3 / checkout 3bca0974 | [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047785/job/111420979836) | success | 243 | 25 |
| PR 9e647b3 / checkout 3bca0974 | [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979743) | success | 125 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979860) | success | 209 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979863) | success | 158 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979875) | success | 123 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979897) | success | 155 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979922) | success | 227 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979945) | success | 171 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979954) | success | 155 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979960) | success | 140 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979964) | success | 221 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979979) | success | 275 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420979985) | success | 157 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420980020) | success | 165 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420980034) | success | 171 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420980045) | success | 155 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420980060) | success | 190 | 15 |
| PR 9e647b3 / checkout 3bca0974 | [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197047782/job/111420980104) | success | 156 | 15 |
| main 15248ac3 | [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767572/job/111423073318) | success | 270 | 35 |
| main 15248ac3 | [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767572/job/111423073538) | success | 98 | 元の未指定 |
| main 15248ac3 | [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767572/job/111423073546) | success | 223 | 25 |
| main 15248ac3 | [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073155) | success | 188 | 15 |
| main 15248ac3 | [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073302) | success | 142 | 15 |
| main 15248ac3 | [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073336) | success | 113 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073375) | success | 166 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073478) | success | 159 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073482) | success | 134 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073513) | success | 165 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073518) | success | 160 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073520) | success | 276 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073542) | success | 213 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073545) | success | 126 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073568) | success | 193 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073581) | success | 171 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073588) | success | 212 | 15 |
| main 15248ac3 | [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073595) | success | 161 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073596) | success | 157 | 15 |
| main 15248ac3 | [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37197767478/job/111423073598) | success | 243 | 15 |
