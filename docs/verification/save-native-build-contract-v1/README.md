# 066 v2 実行済み証拠と原67の継続対応

状態：証拠提出。保存全体・F1/S3・通常UIの受入成功ではない。

- 正式コードC′：`30ea6a5bc50f99ded868f9618655c6289ddb5727`。tree：`a999c3f9a9f32c7ff1d23fe13f80765659bba838`。
- 承認文書D′：`9a99e6501a7b252f77cd6acf515a9f7564abe5f1`。tree：`1e951cb07b7c573735ff64be9bb5541739586d25`。
- 親が公式GitHub aiでC′4ファイル・D′3文書を全量読戻しし原bytes一致を報告。クラウドのGitHub再取得とは区別する。
- code-fixed-sha.txtは正式C′の完全SHA1行。ローカル実行commitを固定値へ代入しない。
- 状態行を除く依頼本文SHA256は `9cbdb54a558f04d45bcbea85fd05150416a2181ea0b61fe4054469f69cdb9f60`。コード・workflow・原67・assertion-map・承認Drive索引・決定ログはD′から不変。

## C′準備で実行済みの結果

| 検証 | 結果 | 範囲 |
|---|---:|---|
| 原67 | 67/67 PASS | 正10・負57。原ファイル・期待値不変 |
| 世代検査 | 62/62 PASS | 正15・負47 |
| 副産物保全 | 40/40 PASS | 正8・負32。実file生成子processによるfixture |
| 移動失敗・独立archive | 6/6 PASS | 原bytes保持・別filesystem拒否・独立再展開 |
| 保護条件 | 92/92 PASS | 旧assertion・承認値・予算・v1原物の保持 |
| 役割別fetch | 21/21 PASS | 通信しない模擬正負。実fetchではない |

合計288チェック。実Windows/Linux native compile・正式CIの成功を意味しない。C′段階ではC′/E′環境値未設定の3コマンドはexit 1（完全SHA必須）を保持した。提出後の正式検証結果・提出自身のcommit SHAをこの提出へ書かない。

## 副産物の保全と保存先

確認済みWindows debug/releaseの `libequipment_save_io.windows.template_*.x86_64.a` の2固定名だけを、ビルド前の不存在・実buildの終了/停止確認後に移動する。ignore globを許可集合へ転用せず、addon実file完全一致判定と許可3生成物の検査を維持する。
原bytesは `$RUNNER_TEMP/native-evidence/build-byproducts-v2/files/`、移動前一覧・file名/bytes/SHA256/mode・移動receiptは同 `build-byproducts-v2/`、段階receiptは `$RUNNER_TEMP/native-build-v1/byproduct-receipts-v2/` に保存する。
実サイズはCIで各fileと合計を原bytesから計測する。今回は実native副産物サイズ未計測。同一filesystem renameが失敗した場合も削除へフォールバックせず元/既移動先の全原bytesを保持する。

## 原失敗と過去の証拠

local-results.jsonには、C′の全結果原JSONと報告原本、v1証拠JSON/READMEの全原bytes、原文書5失敗をbase64で保持する。空白・改行を含め元のbytesを再生成していない。
初期v2試験用コードの構文/配置不備とrun3の不適切な負例集計は受入成功に使わない。修正後のrun4は全拒否理由まで照合した。native build資料を持たないfixtureのcollector総合replay失敗も保持し、副産物単独再検証の成功と分離する。
旧UID追加拒否・ENOSPC・取引本体失敗・16伝播NOT_RUN・初回collector停止・旧065の失敗を取消さない。大きい過去原資料は承認済みdrive-evidence-index.jsonを参照する。同索引を書き換えない。

## 原67の分類対応表

原67は13,249 bytes、SHA256 `fba1d492e1fbef4ea1296b82626707e7f3b216d9092e88c678c8f7000f83e8f7`。全件「最新でも継続」。固定側のf71原検査器と原67を保持し、最新側も原67を実行する。以下のPASSはC′準備時の記録である。

| # | 原検査名 | 分類 | C′準備時 |
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

assertion-map.jsonは原bytesとmap_valueの完全一致を維持し、この表を既存mapへ追加しない。

## C′原本の取得先

Library ID：`libfile_7bb4152bdce881918956e83fd3b586e9`。filename：`066-v2-Cprime-four-originals-and-validation.zip`。version：0。
原ZIP：14675642 bytes、SHA256 `4dcc2d83cc054c12f91bd1595eb1a0174dc0a3bc3ad671f4954572f5bccfb24a`。
指定Drive ID：`1zkoYZRxGH13eLmA_KDmCFCYH78JfmWAo`。親が全量読戻し一致を確認したとの報告。
原資料ZIPは親が指定Driveへ保存する。共有設定変更や別認証経路への迂回は行わない。

## 提出後の資料

正式E′保存・読戻し後に実commitのE4を検証し、その成功後にF′のworkflow envへ実C′/E′完全SHAの2行だけを追加する。リポジトリ変数は使わない。
以後の検証・CI原資料は親の `lucca-workspace/projects/rpg-maker/reports/066-next-stage/` に保存し、この提出へ遡及追加しない。UID/元scriptは別作業067であり、この提出へ追加しない。
固定055/057の原失敗・締切を変更せず、全CI終了前に受入成功とはしない。
