# 018 016固定監査の独立定数照合

作業中。F3の再現と最小修正・ローカル正負例は成功。提出commitの全CIはpush後に確認し追記する。

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
- 同じCLIへ修正済みcheckerだけをコピー：終了1、`016 CLIの固定SHAが独立定数と不一致`。故障入力を成功扱いしない。
- 正常な最新コピー `1e32aaf43abf32381a4404d9904a97700c3681b5`：既存6件＋新規14負例、20/20 PASS、終了0、19.211秒（180秒以内）。正常な状態行更新・新依頼登録・別範囲本番変更は、完成監査の非干渉正例として引き続き成功。
- 固定012当時checkoutから既存17件：17/17 PASS、終了0、1.884秒。現行012独立照合：PASS、0.263秒、反証14/14 PASS、3.680秒。元F1同時付替え拒否を保持。
- `python tools/check_frozen_files.py`：26/26一致、終了0。全コマンド・結果は`local-results.json`、20件内訳は`scope-cases-local.json`。

## CI・提出差分

提出commitのCI確認待ち。workflowは1バイトも変更していない。既存上限、全matrix、R-01〜R-08、失敗判定は維持。元F2の13正負例と固定/最新動作・全描画は提出CIで確認する。

## 残る制約

- 指定モデル/effortの実効設定を照合するAPIはないため、独立確認済みとは称さない。クラウド内のみ、追加委譲なし。今回は追加スキルを適用していない。
- Astra再レビューは親の別発注。main未統合、007以降は未着手。007サービス・将来機能・人間試遊・約60時間実測を今回の成功に含めない。
- 018自身の固定監査は新設しない。今回の開始点から提出点への許可範囲は親が実差分で確認する。
