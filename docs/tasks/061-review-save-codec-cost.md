# 061 保存codec計測の独立レビュー

- 状態：報告済み（部分確認。CI直接取得不可、F1/S3未受入）
- 作成日：2026-10-10 JST
- 担当：Codex独立レビュー、受入はルッカ
- 環境：保存済みRPG-makerクラウドCodex環境、GPT-6 Astra／Medium。使用量影響不明。
- 基点・対象：060提出4ec85645d883897a5c1c18e2b53f60a7818710d5
- ブランチ：codex/task-061-review-save-codec-cost
- 前提：060実行終了、51CIは43成功8失敗。計測報告の独立確認であり、S3受入や失敗解消ではない。060に依存する逐次発注。

## 目的
060の計測・再集計・証拠同等性・結論を独立確認し、次に必要な最小調査/修正範囲を示す。本番性能修正・新規則の採用はしない。

## 変更予定ファイル（全件）
1. docs/tasks/061-review-save-codec-cost.md の状態行のみ
2. docs/tasks/reports/061-review-save-codec-cost.md 新規
追跡ファイルの変更はこの2文書だけ。一時領域に検証用のコピー/出力を作ってよいが、原証拠・本番・既存検査・CI・保護対象・decision-log・tasks READMEを変更しない。

## 読むもの
AGENTS.md、docs/tasks/README.md、060依頼全文、060報告全文、060専用5コードと全証拠の対応、059報告の世代境界。重大な物語内容を報告へ含めない。

## 独立確認
1. 登録e37ddbafから対象4ec85645までの全差分が060許可集合内か、本番・既存検査・原証拠・保護26・予算・6安全境界が不変か。依頼本文は状態行以外不変か。
2. 計測開始c126bc84870225b38842054f20e1784b023384d6、最終専用コード5d941bfe23715be0c2300b0263fcbea7ae7059fe、回帰checkout2c6fef966576bb38fcaa0863b3982b1777c4fdff、提出4ec85645を混同しない。実Git blobからcode-inventoryのhash・採取関数・exec-json分岐の同一性を独立再計算する。比較器はcode-inventory自体をすべて検証しているとは限らないため自己申告を鵜呑みにしない。
3. 全12試行の原archive/member bytes/hash、入力/型付きgdv/出力/元configを照合。batch projectionの重複排除が正当か原bytesから確認する。inventory.cli_finalization_checkの生成物を独立再現し、手動補完が不要か確認する。取得不能部分は未確認として明記する。拒否された経路の迂回は禁止。
4. on/off3組、交互の順序、試行wall/並行累積/inclusive/exclusive、完結spanだけの偏り、計測器負荷を確認。codec6成功・取引3成功3失敗、取引同等性INCOMPLETE/exit1を保持しているか。欠落ケースやinspect差異を正規化で隠していないか。Windows専用計測未実施をLinux結果で代替しない。
5. 専用比較器の8負例とscope6負例、codec154/975、取引172/2178/97kill、16伝播、R-01〜R-08、保護26の証拠と判定を照合。全体未達を局所成功で代替しない。再現は元予算内、成功するまでの選別再実行は禁止。
6. 候補A（2回目gzip/parse）の全取引呼出0、候補B（metadata再生成+複製）の0.724〜0.756秒並行累積が原spanから再計算できるか。これをwall短縮量やF1主因と断定しない。validate等の追加計測を含め、次の最小案は実測寄与に基づく。
7. 最終CIの全51終了43成功8失敗を直接確認。native run38006271798の固定055/057両OS取引の時間未達、最新Windows本体時間未達、最新4jobのscope059失敗を区別。親はUbuntu latest/primitives artifact11651858421とWindows latest/transaction11652390544のraw archiveと全member hashを照合し、scope059の完成後担当外拒否を確認済み。他2jobまで推定で同原因としない。
8. scope059は固定code41a34ea33fe184274e6722c88cdbca2a7ffd3708と後続060 headの差分を拒否している。既存059検査の修復再故障とは区別し、完成固定と後続最新を安全に分離する別件案を示す。検査を弱める変更は実行しない。

## 出口
判定は受入/差し戻し/部分確認のいずれかと根拠。指摘に再現手順・証拠・重大度・対象ファイル・最小修正案・承認要否を付ける。F1、F4実ENOSPC/nested別volume、inspect原因、Windows060未測、旧351原因不明、通常UI未接続を未解決のまま明示。変更しない場合も本番最適化へ進む根拠の有無を示す。
専用報告と状態行をcommit/push、最終SHA全CI終了（成功/失敗含む）・remote一致・clean/未pushを報告。PR作成・main反映・他タスク委譲・環境設定変更は禁止。
