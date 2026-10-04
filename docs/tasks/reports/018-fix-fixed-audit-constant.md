# 018 016固定監査の独立定数照合

**F3を既存checkerへの独立定数照合で解消した。既存6件を保持し追加14負例は全て期待どおり拒否。修正提出SHAの全20CI成功。018は報告済み、main未統合で親へ返す。**

## 対象と修正

- 開始SHA：`0ea253e47b7d210581efebd788b42a39fe2271a2`。開始時の未コミット変更・登録branchに対する未push commitは0件。古いworkブランチから登録branchを取得し、完全SHA一致を確認した。mainの取込みなし。
- 独立期待値：016完成SHA `6706397e2674ffa382852e0f33ce23edf5c76634`、tree `02105ab24ef39a2acf7405274e040d8cefaa399b`。018依頼書から転記し、Git実treeと既存完成記録commit `9f1a18892273ac06d9776d2ddf8dbcc1c6423453` の記録を照合した。
- `tools/check_task016_scope.py:18–20` に独立定数、`:53–82` にCLI/実commit tree/実checkout/manifest/workflowとの照合を追加。bootstrapもCLI/実checkoutの独立定数照合を迂回しない。scopeのSTART・PERMITTED・audit本体は不変。
- 同ファイル`:125–188` に017F3同時付替え、manifest単独誤SHA/tree/開始点、workflow単独誤SHA/checkout/欠損、記録フィールド/JSON/ファイル欠損、CLI不正/不存在SHA、実checkout付替え/欠損の14負例を追加。状態子commitが元範囲監査だけには通る前提も実測し、意図した拒否理由を照合する。
- 固定006/009/012/016のSHA・当時コード・既存範囲/当時検査は維持。012の信頼記録 `9e647b3d6d0f91b061f7de974dbb5411937a2bb9` は無変更。新規018固定manifest・CI checkout・workflow・監査層は0。

## 前後実測

`docs/verification/task-018/before.json` / `after.json` に同じ状態子commitと同時付替え入力を保存。元repoへ故障注入せず、no-hardlinksの一時cloneのみを使った。

- 状態だけ変更した016子：`38021055d12c1656dc13d3256807357d6fd54eab`。manifest SHA/tree＋workflow env/checkout＋CLI＋実checkoutをこの子へ揃えた最新コピー：`b28a9fbd72f9a10429f3f1e850fa4b951d304abc`。
- 修正前のCLI：終了0、6/6 PASS、7.307秒。
- 同じCLIへ修正済みcheckerだけをコピー：終了1、`016 CLIの固定SHAが独立定数と不一致`。故障入力を成功扱いしない。`--bootstrap`追加でも同じ拒否、終了1・0.050秒（`bootstrap-rejection.json`）。
- 正常な最新コピー `1e32aaf43abf32381a4404d9904a97700c3681b5`：既存6件＋新規14負例、20/20 PASS、終了0、19.211秒（180秒以内）。正常な状態行更新・新依頼登録・別範囲本番変更は、完成監査の非干渉正例として引き続き成功。
- 固定012当時checkoutから既存17件：17/17 PASS、終了0、1.884秒。現行012独立照合：PASS、0.263秒、反証14/14 PASS、3.680秒。元F1同時付替え拒否を保持。
- `python tools/check_frozen_files.py`：26/26一致、終了0。全コマンド・結果は`local-results.json`、20件内訳は`scope-cases-local.json`。

## CI・提出差分

修正提出SHA：`80908c34f619d3cbf55920dbcbb28720bf442aec`。接続済みGitHubのread-only APIで、全run/job/stepと全20jobの実ログを直接取得。全ログの最新checkoutはこのSHAと一致し、固定実行のSHAと区別した。通常gh APIは403だったため接続済みAPIを使用。証拠は `docs/verification/task-018/ci-results.json`。

- [通常CI 37204986620](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986620)：3/3 completed/success。R-01〜R-08全てexit=0/tests_ran=True/parser_failed=False、保護26/26、素材原画・台帳・既存回帰成功。
- [専用CI 37204986649](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649)：17/17 completed/success。修正016範囲20/20、固定012当時17/17、012独立照合14/14、NPC等既存13正負例全成功。
- 固定006 runtime7592/20保存/restart9,26,37,51,43。最新提出runtime7662/20保存/restart10,27,38,52,44。固定/最新各7描画モード49枚全成功（固定journey137・最新journey132、details34、restart17×5）。固定009範囲監査と135箇所・未分類0も成功。
- 元F1同時付替えは独立012記録と不一致として拒否。元F2正常カウンター裏NPCは7661項目・20保存・隣接[7,4]実到達・足元拒否/全状態保持・保存後退出が成功、20.810秒。NPC付きjourney描画132項目・28枚・119.802秒で成功。
- 占有無視はexit1/7663、状態破壊はexit1/7661、客側[8,6]閉塞はexit1/7658、出口[8,11]閉塞はexit1/7543。全てparser_errors=falseで該当assertionの失敗を確認。外観床39×2・7656回帰、誤接続/不正保存受理拒否も保持。
- workflowは1バイトも変更していない。専用各15分、import600秒、各検査/描画180秒、内部180000ms/600移動/3000入力/300ターン、既存ci.ymlの35分/25分・Rverify300秒を保持。項目削除・新規skip・失敗無視・時間延長・PERMITTED拡張なし。bootstrapの既存初回用モードは保持するが独立定数照合を迂回しない。
- 全CIとは今回pushで起動した2workflow・20jobを指す。workflow_dispatch専用の旧本編手動検査は今回起動していない。Godot動作/描画・Rは上記提出CIの直接ログで確認しており、全てをローカルで再実行したという意味ではない。

| job | 結果 | 秒（ログ先頭〜末尾） |
| --- | --- | ---: |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986620/job/111444194289) | success | 208 |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986620/job/111444194389) | success | 267 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986620/job/111444194397) | success | 95 |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194670) | success | 479 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194813) | success | 163 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194823) | success | 116 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194836) | success | 119 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194838) | success | 215 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194843) | success | 153 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194846) | success | 257 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194854) | success | 121 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194860) | success | 218 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194867) | success | 165 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194869) | success | 154 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194893) | success | 122 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194898) | success | 138 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194904) | success | 115 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194905) | success | 129 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194909) | success | 210 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37204986649/job/111444194958) | success | 139 |

## 変更ファイルと親の差分確認

開始完全SHA `0ea253e47b7d210581efebd788b42a39fe2271a2` → 修正提出完全SHA `80908c34f619d3cbf55920dbcbb28720bf442aec` は以下8ファイルだけ。以後の報告確定commitはコード変更0で、018状態行/本報告、CI証拠/追加bootstrap証拠だけを加える。最終提出完全SHAは最終応答に記載する（報告commit自身のSHAを自身の内容へ埋め込むことはできない）。親は以下コマンドで開始→最終提出の全差分を確認できる。

```sh
git diff --name-status 0ea253e47b7d210581efebd788b42a39fe2271a2 <最終応答の提出完全SHA>
git diff 0ea253e47b7d210581efebd788b42a39fe2271a2 <最終応答の提出完全SHA> -- tools/check_task016_scope.py
```

変更一覧（最終報告確定後は10ファイル）：

- `tools/check_task016_scope.py`（唯一のコード変更）
- `docs/decision-log.md`
- `docs/tasks/018-fix-fixed-audit-constant.md`（状態行だけ）
- `docs/tasks/reports/018-fix-fixed-audit-constant.md`
- `docs/verification/task-018/before.json`
- `docs/verification/task-018/after.json`
- `docs/verification/task-018/local-results.json`
- `docs/verification/task-018/scope-cases-local.json`
- `docs/verification/task-018/bootstrap-rejection.json`（報告確定時追加）
- `docs/verification/task-018/ci-results.json`（報告確定時追加）

`git diff --check`成功。開始→修正提出の `assets/scripts/world/data/test/.scope-lock/addons/project.godot/.github/AGENTS.md` と既存012検査器・016独立012照合/反証は差分0。原画・本番・保護・workflow不変。016当時のSTART/PERMITTED/auditは不変で、完成差分の対象を6706397から動かしていない。016状態行は既存の報告済みを維持した。新018固定manifest/checkout/workflow/監査層は0。

報告確定commitも通常pushし、最終HEADの全20CI終了を最終応答で報告する。親のAstra再レビューまでmainへ統合しない。開始時mainと修正提出push後のmainは `5be5aeecf1a3c73a5242d18f75975eb02fa55cda`、同じ。今回の未push修正commitはpushで解消した。


## 残る制約

- 指定モデル/effortの実効設定を照合するAPIはないため、独立確認済みとは称さない。クラウド内のみ、追加委譲なし。今回は追加スキルを適用していない。
- 実装上の未達・ブロッカーは0。Astra再レビューは親の別発注。main未統合、007以降は未着手。007サービス・将来機能・人間試遊・約60時間実測を今回の成功に含めない。
- 018自身の固定監査は新設しない。今回の開始点から提出点への許可範囲は親が実差分で確認する。
