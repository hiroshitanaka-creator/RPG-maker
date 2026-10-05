# 019 018最小修正の独立レビュー

## 結論

**PASS。017 F3は解消、元F1/F2の退行なし。今回の監査修正を理由とする差し戻しはなく、親は007へ進めてよい。** 007自体の実装・受入成功を意味しない。追加の監査層・コード修正・main統合・他タスク発注・追加委譲は行っていない。

## 対象と独立性

- レビュー対象018提出：`2cc56359ed90dce37247e320720082bf63a49e89`。
- 019登録・作業開始：`ebc8f6f1746534fdb316005efeaa4e3f02f12b80`、branch `codex/task-019-review-fixed-constant`。登録差分は019依頼書24行の追加のみ。開始時未コミット変更0、登録点からの未push commit 0。
- 017報告は `28c3ecb806b7b24e3bad17ce8fc4c111eddae8f5`、018開始は `0ea253e47b7d210581efebd788b42a39fe2271a2`。対象履歴上の017報告、018依頼・報告、開始→最終提出の全差分を読んだ。mainだけで代用していない。
- 固定006：`5f1c2ba231191b25b9b32a814b616a9f8d0a54ce`、009：`ce07fdada0466138260ab678c10fd78e61c0c63d`、012：`c327e7c439c9c8c8f1fd640e6cda6df7550fb26a`、016：`6706397e2674ffa382852e0f33ce23edf5c76634`。
- 016独立tree：`02105ab24ef39a2acf7405274e040d8cefaa399b`。完成記録commit `9f1a18892273ac06d9776d2ddf8dbcc1c6423453` の記録と実Git treeを照合。012の独立信頼記録 `9e647b3d6d0f91b061f7de974dbb5411937a2bb9` も維持。
- 故障注入・実行結果生成は `/workspace/review019/` の使い捨てcloneのみ。元repoの実装には触れていない。019成果物は本報告と019依頼書の状態行だけ。
- 追加スキルは適用していない。checkoutに `.agents/skills` は存在しなかった。モデル/effortの実効設定を照合するAPIはなく、指定設定の独立確認済みとは称さない。

## F3の元反証を独立再実行

016完成commitから依頼書状態行だけ違う子 `e5d049a036fa654fa5f77de89c72b291ec9d11f3` を作成。その子のSHA/treeへmanifest、workflowのenvと別checkout参照を揃えた最新コピー `c64805575a7649b23f8bf8046a3339fc41f1e38f` を作り、CLI・実checkoutも子へ付け替えた。検査器バイト列が対象018と同一であることをassertして実行した。

- `audit(repo, moved)` 単体はPASS。状態だけの子が元の許可範囲を逸脱しないという017反証の前提を再確認。
- `timeout 180 python tools/check_task016_scope.py --completed-sha <子SHA> --fixed-path <子checkout> --latest-sha <同時付替えSHA>` と同じ180秒上限のsubprocess実行：**終了1、0.041秒、016 CLIの固定SHAが独立定数と不一致**。
- 同じCLIに `--bootstrap` を追加：終了1、0.041秒、同じ独立定数不一致。
- 正常018に同CLIを正しい固定016で実行：**終了0、20/20 PASS、9.250秒**。旧6件（正常完成範囲・状態行・新依頼・両方・後続別範囲・完成内本番改変拒否）を保持し、新14負例も全成功。単独誤SHA/tree、誤開始点、workflowのSHA/checkout/欠損、manifest欠損・不正JSON、CLI不正・不存在、実checkoutの付替え・欠損を検出した。

`tools/check_task016_scope.py:18–20` の期待SHA/treeは独立定数。`:53–66` はCLI・実commit tree・実checkout HEAD/tree/dirtyを照合し、`:69–82` はlatest manifest・workflowを定数へ照合する。期待値をlatestから生成しない。`:95` の照合はbootstrap分岐より前。START/PERMITTED/audit本体と旧6件は開始時から不変。016当時の範囲監査は固定6706397のままで、018用固定manifest・checkout・workflow・新監査層は0。

## 元F1の退行なし

012状態行だけの子 `8d6ad5adb0781d1872258ce2ff4dcaeda3c86934` とmanifest/workflow/実checkoutの同時付替え最新 `b7dd2dbcecd1224c6ac77ae64a2afd003bb86545` を別コピーで作成した。

- 子checkoutの無変更の当時012検査器：**終了0、17/17、1.857秒**。元F1の自己一致の前提を再現。
- 018の無変更 `check_task016_fixed_anchor.py --fixed012-path <子checkout> --latest-sha <同時付替えSHA>`：**終了1、0.049秒、012 manifestが独立信頼基点の記録と不一致**。
- 正常012独立照合：終了0、0.280秒。`test_task016_fixed_anchor.py`：終了0、14/14、3.857秒。
- 固定012当時の `test_task012_pinned_audit.py --current-path <018> --fixed009-path <固定009> --completed012-sha <固定012> --latest-sha <018>`：終了0、17/17、1.868秒。
- 状態行・新依頼書・後続別範囲の正例は上記17件/20件で成功し、固定監査が正常後続編集を誤拒否しないことを実測。

## 元F2と最新本番回帰

Godot配布ZIPのSHA256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`。指定4.7.2-stableを使用し、環境既定4.6.3では検証していない。初回editor importはconfig保存先権限のERRORがあったため成功根拠にせず、XDG_CONFIG_HOME/XDG_CACHE_HOME/XDG_DATA_HOMEを一時領域へ設定して同じ600秒上限で再実行。終了0、SCRIPT ERROR/ERROR/WARNING/Parse Errorなし。

cleanな対象018のコピーで `python tools/check_region2_village_regression.py --commit 2cc56359ed90dce37247e320720082bf63a49e89 --godot <4.7.2>` を実行：**終了0、runtime 7662、20保存、restart 10/27/38/52/44、全体21.216秒**。固定版の成功で最新本番を代用していない。

元013同様、`world/region2_village.json` のroom 2のeventsだけをNPC [8,4]へ変更し、追加NPCで客側/出口を閉塞する負例をそれぞれ別実行した。fixture・本番コード・検査器は不変。各実行前に結果JSONを削除し、各プロセス上限180秒、finallyで元バイトへ復元。dirty故障注入時はGDを直接実行し、cleanを要求するPythonラッパーの成功とはしていない。

| 独立実行ケース | 終了 | checks | 秒 | 観測 |
| --- | ---: | ---: | ---: | --- |
| カウンター裏NPC [8,4] | 0 | 7661 | 16.978 | PASS、20保存 |
| 追加NPCで客側 [8,6] 閉塞 | 1 | 7658 | 17.172 | 必須目標閉塞assertion失敗 |
| 追加NPCで出口 [8,11] 閉塞 | 1 | 7543 | 16.889 | 扉リンク・実退出・保存後退出assertion失敗 |

全ケースでSCRIPT ERROR/ERROR/WARNING/Parse Errorなし。timeoutや構文エラーを負例成功と数えていない。

`check_region2_village_regression.gd:194–219` は家具裏の占有時に隣接への本番歩行・足元への移動拒否・全状態保持を実行し、必須の客側・出入口は占有を拒否する。単なるskipではない。対象CIの占有無視・拒否時状態破壊も実assertion失敗を確認（下記）。固定006は当時の全到達条件を維持。

## 018提出SHAの全CIを直接確認

実装者の報告に記載された80908c3のCIを最終提出の根拠に流用していない。接続済みGitHub read-only APIから、**対象2cc5635に対応する全4runの全40job/step状態を取得し全success**。そのうち018提出branchの下記2run・20jobは全実ログを取得し、最新checkout SHAを対象完全SHAと照合した。通常gh APIは403だったため接続済みAPIを使用。

- [018通常CI 37205609032](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609032)：3/3 completed/success。R-01〜R-08は全てexit=0、tests_ran=True、parser_failed=False。
- [018専用CI 37205609075](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075)：17/17 completed/success。固定012の17件、012独立照合14件、016範囲20件、NPC等13正負例を実ログで確認。
- 同じ対象SHAで019branch作成時にも [通常CI 37206356008](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37206356008) 3/3、[専用CI 37206356044](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37206356044) 17/17 success。こちらは全job/step状態の確認であり、実ログ確認の20jobと重複計上しない。
- 固定006 runtime7592・20保存・restart9/26/37/51/43。最新018 runtime7662・20保存・restart10/27/38/52/44。固定/最新それぞれ7描画modeで49枚、journey固定137/最新132、details34、restart17×5。
- NPC正例7661、20保存、隣接[7,4]実到達、占有拒否・状態保持、21.656秒。NPC付き描画132項目・28枚、123.816秒、180秒以内。
- 負例は占有無視exit1/7663、状態破壊exit1/7661、客側閉塞exit1/7658、出口閉塞exit1/7543。parser_errors=false、該当assertionの実失敗。外観39×2/7656回帰・誤接続/不正保存受理拒否も保持。
- matrixの反対世代stepのみ既存の条件付きskip。対応世代jobは実行済み。旧本編のworkflow_dispatch専用検査は起動対象外。

| job（直接取得した実ログ） | 結果 | 秒（ログ先頭〜末尾） |
| --- | --- | ---: |
| [試遊前の通常戦闘・案内・画面・復帰検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609032/job/111446052803) | success | 264 |
| [Godot・凍結受入テスト](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609032/job/111446052842) | success | 231 |
| [素材検査](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609032/job/111446052905) | success | 87 |
| [lifecycle-audit](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052717) | success | 531 |
| [normal-input-and-rendering (latest, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052804) | success | 154 |
| [normal-input-and-rendering (fixed, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052816) | success | 143 |
| [normal-input-and-rendering (fixed, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052820) | success | 163 |
| [normal-input-and-rendering (latest, restart-1)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052831) | success | 174 |
| [normal-input-and-rendering (latest, restart-4)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052848) | success | 158 |
| [normal-input-and-rendering (fixed, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052858) | success | 141 |
| [acceptance-and-regression (latest)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052865) | success | 124 |
| [acceptance-and-regression (fixed)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052876) | success | 104 |
| [normal-input-and-rendering (latest, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052890) | success | 160 |
| [normal-input-and-rendering (fixed, restart-3)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052946) | success | 178 |
| [normal-input-and-rendering (fixed, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446052972) | success | 209 |
| [normal-input-and-rendering (latest, details)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446053008) | success | 224 |
| [normal-input-and-rendering (fixed, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446053032) | success | 259 |
| [normal-input-and-rendering (fixed, restart-0)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446053052) | success | 159 |
| [normal-input-and-rendering (latest, journey)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446053070) | success | 209 |
| [normal-input-and-rendering (latest, restart-2)](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37205609075/job/111446053100) | success | 165 |


## 変更範囲・保護・上限

018開始 `0ea253e47b7d210581efebd788b42a39fe2271a2` → 提出 `2cc56359ed90dce37247e320720082bf63a49e89` の変更は次の10ファイルのみ。

- `tools/check_task016_scope.py`（唯一のコード変更）
- `docs/decision-log.md`
- `docs/tasks/018-fix-fixed-audit-constant.md`（状態行）
- `docs/tasks/reports/018-fix-fixed-audit-constant.md`
- `docs/verification/task-018/` の `before.json`、`after.json`、`bootstrap-rejection.json`、`ci-results.json`、`local-results.json`、`scope-cases-local.json`

`git diff --name-only <018開始> <018提出> -- assets scripts world data test .scope-lock addons project.godot .github AGENTS.md` は出力0。原画・本番・保護・workflowは不変。固定006/009/012の検査・manifestと012独立照合、旧assertion対応表も変更0。`python tools/check_frozen_files.py` は26/26、`python tools/check_task009_assertion_map.py` は135箇所・未分類0・fixture=fixed006、どちらも終了0。

専用job15分、import600秒、各検査/描画180秒、内部180000ms/600移動/3000入力/300ターン、通常CI35分/25分・R verify300秒を維持。項目削除・許可範囲拡張・新skip・continue-on-error・時間延長なし。

019の変更は `docs/tasks/019-review-fixed-constant.md` の状態行と本報告だけ。`git diff --check` で確認し、通常commit/pushする。mainの観測SHAは `5be5aeecf1a3c73a5242d18f75975eb02fa55cda`。統合・他依頼書の状態更新は行わない。

## 未確認・引継ぎ

- 今回の範囲に未解消の指摘・実装修正要求なし。007の施設サービス・6人配置・統合正負例・将来機能は未実装/未検証。配置確定後の描画点との衝突は007側で確認する。
- 人間試遊・約60時間の実測・ゲーム全体の完成は判定していない。
- ローカルでは描画全modeとR全件を重複再実行せず、対象SHAのCI実ログで確認した。ローカル実測とCI実測を区別して記載。
- 全コードを悪意をもって書き換えた場合まで保証する外部信頼基盤は対象外。今回のF3は参照・記録のみの同時付替えを無変更の検査器で拒否する条件に限定した。
- 019報告commit自身のSHAとpush後CIは最終応答で伝える。報告本文に自身のSHAを埋めるための再帰的commitは行わない。
