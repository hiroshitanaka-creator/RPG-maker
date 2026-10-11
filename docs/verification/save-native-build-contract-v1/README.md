# 066 実行済み証拠と原67の継続対応

状態：証拠提出。保存全体・F1/S3・通常UIの受入成功ではない。

- 正式コードC：`130cf60cf53450715c700b1441e9d3d12e249391`。コードtree：`e1f056a3f047ef6864fed657954b4e7ec7a0a2bb`。
- 承認文書D：`baf43630a2ad55d6c01bd77ddffe8f6b4a46ce4d`。文書tree：`fb8ec0d712aec7242811faeb91c03c8dfd6f2bc5`。
- Cの4コードとDの3文書は、親が公式GitHubで全量読戻しし、原bytes一致を確認したとの報告。クラウドによるGitHub再取得ではない。
- code-fixed-sha.txtは上記の実在C完全SHAの1行。ローカル検証commitは固定値に使わない。
- 依頼書はヘッダの状態行1件のみを更新。状態行を除く本文SHA256は `9cbdb54a558f04d45bcbea85fd05150416a2181ea0b61fe4054469f69cdb9f60` のまま。
- Drive索引・決定ログ・コード・workflow・原67・assertion-map.jsonはDから変更しない。

## 実行済み結果の範囲

| 検証 | 実行済み結果 | 範囲 |
|---|---:|---|
| C準備の原67 | 67/67 PASS | Cと同一コードtreeの合成正負 |
| C準備の世代正負 | 62/62 PASS | 原期待値と既存全件を維持 |
| 役割別fetch | 21/21 PASS | 通信なしの模擬検証。実fetch成功ではない |
| C準備の既存保護 | 36/36 PASS | 旧assertion・予算・失敗伝播 |
| C境界 | 23/23 PASS | C/E未設定の3実コマンドはexit 1を期待どおり保持 |
| checker単独の正確なreview tree | 120/120 PASS | 原67＋実文書53。他3準備コードなし |
| 限定修正時の回帰 | 延べ313件PASS | 他3準備コード入り。独立review treeの結果と区別 |

C準備の合計は209件。これは正式CIの成功ではない。Windows実build、両OS/両phaseの最終CI、提出後のcompleted_contractは、この証拠提出時点では未実施である。未来の結果・提出自身のcommit SHAは記録しない。

## 原失敗の保持

旧Linux primitivesのbuild・本体・7+7成功と、その後のUID3件追加拒否を区別する。旧transactionのENOSPC、追加独立採取での取引本体・validator失敗、16伝播NOT_RUN、初回collector停止、原文書の正例5失敗を取消さない。旧065の51job中43成功8失敗は当時の依頼書由来であり、今回の直接CI照会ではない。
local-results.jsonは、C準備の全結果原JSON、過去のlocal/linux結果とstdout/stderrの全原bytesをbase64で保持する。元JSONの空白・改行を含め再生成していない。原ログ・全補助資料・原失敗は下記Library原本およびDのDrive索引から参照する。

## 原67の分類対応表

原ファイルは13,249 bytes、SHA256 `fba1d492e1fbef4ea1296b82626707e7f3b216d9092e88c678c8f7000f83e8f7` のまま。67件すべて「最新でも継続」。固定側はf71の原検査器・原67を保持し、最新側でも原67を実行する。追加の世代検査で置き換えない。以下のPASSはC準備時の記録である。

| # | 原検査名 | 分類 | C準備時 |
|---:|---|---|---|
| 1 | `positive-linux-transaction-changed` | 最新でも継続 | PASS |
| 2 | `positive-linux-transaction-identical` | 最新でも継続 | PASS |
| 3 | `positive-linux-primitives-changed` | 最新でも継続 | PASS |
| 4 | `positive-linux-primitives-identical` | 最新でも継続 | PASS |
| 5 | `positive-windows-transaction-changed` | 最新でも継続 | PASS |
| 6 | `positive-windows-transaction-identical` | 最新でも継続 | PASS |
| 7 | `positive-windows-primitives-changed` | 最新でも継続 | PASS |
| 8 | `positive-windows-primitives-identical` | 最新でも継続 | PASS |
| 9 | `binary-not-run-control` | 最新でも継続 | PASS |
| 10 | `failed-archive-control` | 最新でも継続 | PASS |
| 11 | `dirty` | 最新でも継続 | PASS |
| 12 | `shipped-forged` | 最新でも継続 | PASS |
| 13 | `source` | 最新でも継続 | PASS |
| 14 | `cpp` | 最新でも継続 | PASS |
| 15 | `build-py` | 最新でも継続 | PASS |
| 16 | `sconstruct` | 最新でも継続 | PASS |
| 17 | `pin` | 最新でも継続 | PASS |
| 18 | `profile` | 最新でも継続 | PASS |
| 19 | `gdscript` | 最新でも継続 | PASS |
| 20 | `gdextension` | 最新でも継続 | PASS |
| 21 | `other-os` | 最新でも継続 | PASS |
| 22 | `addon-extra` | 最新でも継続 | PASS |
| 23 | `added` | 最新でも継続 | PASS |
| 24 | `deleted` | 最新でも継続 | PASS |
| 25 | `renamed` | 最新でも継続 | PASS |
| 26 | `symlink` | 最新でも継続 | PASS |
| 27 | `mode` | 最新でも継続 | PASS |
| 28 | `manifest-extra` | 最新でも継続 | PASS |
| 29 | `manifest-missing` | 最新でも継続 | PASS |
| 30 | `manifest-duplicate` | 最新でも継続 | PASS |
| 31 | `manifest-os` | 最新でも継続 | PASS |
| 32 | `manifest-hash` | 最新でも継続 | PASS |
| 33 | `rehash-all` | 最新でも継続 | PASS |
| 34 | `after-build-replace` | 最新でも継続 | PASS |
| 35 | `test-replace` | 最新でも継続 | PASS |
| 36 | `diagnostic-replace` | 最新でも継続 | PASS |
| 37 | `snapshot-missing` | 最新でも継続 | PASS |
| 38 | `snapshot-order` | 最新でも継続 | PASS |
| 39 | `snapshot-sha` | 最新でも継続 | PASS |
| 40 | `snapshot-os` | 最新でも継続 | PASS |
| 41 | `snapshot-job` | 最新でも継続 | PASS |
| 42 | `schema-downgrade` | 最新でも継続 | PASS |
| 43 | `snapshot-bytes` | 最新でも継続 | PASS |
| 44 | `snapshot-receipt` | 最新でも継続 | PASS |
| 45 | `snapshot-recapture` | 最新でも継続 | PASS |
| 46 | `build-nonzero` | 最新でも継続 | PASS |
| 47 | `build-timeout` | 最新でも継続 | PASS |
| 48 | `build-not-run` | 最新でも継続 | PASS |
| 49 | `build-log-missing` | 最新でも継続 | PASS |
| 50 | `build-unconfirmed` | 最新でも継続 | PASS |
| 51 | `build-argv` | 最新でも継続 | PASS |
| 52 | `build-budget` | 最新でも継続 | PASS |
| 53 | `fixed055` | 最新でも継続 | PASS |
| 54 | `fixed057` | 最新でも継続 | PASS |
| 55 | `scope-outside` | 最新でも継続 | PASS |
| 56 | `scope-old-code` | 最新でも継続 | PASS |
| 57 | `scope-old-evidence` | 最新でも継続 | PASS |
| 58 | `scope-task-body` | 最新でも継続 | PASS |
| 59 | `map-missing` | 最新でも継続 | PASS |
| 60 | `map-duplicate` | 最新でも継続 | PASS |
| 61 | `map-replaced` | 最新でも継続 | PASS |
| 62 | `old112` | 最新でも継続 | PASS |
| 63 | `old14` | 最新でも継続 | PASS |
| 64 | `workflow-budgets` | 最新でも継続 | PASS |
| 65 | `dependency-dirty` | 最新でも継続 | PASS |
| 66 | `ignored-dependency-input` | 最新でも継続 | PASS |
| 67 | `ignored-native-input` | 最新でも継続 | PASS |

assertion-map.jsonは元の構造・原bytes・map_valueとの完全一致を維持する。この対応表をmapへ追加しない。

## 原本の取得先

| 内容 | Library ID | filename / version | bytes / SHA256 |
|---|---|---|---|
| C preparation | `libfile_9dfedcff69a0819181476c5cc5bde006` | `066-stage-C-four-code-originals-and-validation.zip` / 0 | 4892069 / `c3d1753ff4c58a4533ab10176fb608a1ea2bac3c13ca2db630e5ad4e8c65e20f` |
| exact checker-only review tree | `libfile_0412b91938cc8191934aac8e7125e746` | `066-exact-review-tree-validation-originals.zip` / 0 | 6176408 / `c01a655570a443f288b82749287e99cb959c2ff0c460e686765e4618db3826b7` |
| limited fix and regression | `libfile_33d910b381648191b89d96be7bd19309` | `066-limited-A-checker-fix-review-originals.zip` / 0 | 12042282 / `acaa63f3805e3c097858ddd295b441fb0b0dd3116209443467bbfc4846516626` |
| original five real-document failures | `libfile_a0e23007bab08191936028e5cc351cd7` | `066-real-approved-documents-validation-originals.zip` / 0 | 1149904 / `50823baea2df3f1a4bc90a4b88931d4fccc57d9bd81a3d8928d92e6a17925f47` |

大きいLinux原本・分割順序・各Drive ID・再取得照合は、承認原本のdrive-evidence-index.jsonに固定されている。新しい共有設定や別保存先への迂回は行わない。

## 提出後の資料の扱い

提出後の契約検証とFのCI原資料は、親のlucca-workspace/projects/rpg-maker/reports/066-next-stage/へ別保存し、この提出へ遡って書き込まない。Fはworkflow envへ実在C/E完全SHAの2行だけを追加し、最新HEAD=F、固定完成版=Eを検査する。リポジトリ変数は使わない。
固定055/057の時間切れを修正・免除しない。全CI終了前に受入成功としない。
