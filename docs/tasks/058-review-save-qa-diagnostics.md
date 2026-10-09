# 058 保存検査ログ修正・時間計測の独立レビュー
- 状態：未着手
- 担当：Codex GPT-6 Astra／Medium
- 依頼日：2026-10-09 JST
- 前提：なし（未達を含む057提出の独立レビュー。全保存機能の受入成功を前提にしない）。
- 対象：057提出 fdd6ce03c3e46cfac430930e001a383f3a7c9aec、修正コード 3cf4b6c293f6796220b43cf566f8eb792c3932ec
- ブランチ：codex/task-058-review-save-qa-diagnostics

## 目的
057のF5ログ保持修正とWindows/Linux計測を独立確認し、F1時間未達・F4未実測とは分けて評価する。資料作成・実装・実行・受入を混同しない。ゲーム内容を報告に含めない。

## 読むもの
AGENTS.md、docs/tasks/README.md、057依頼と報告全文、056報告、原053/055の依頼・報告・証拠、専用platform runner/helper/workflowと今回証拠。必要ならcheckout .agents/skills内の関連SKILL.md。本レビューは親の受入管理に属する独立成果物レビューであり、実装担当への担当変更ではない。

## 変更可能な場所
本依頼書の状態行と docs/tasks/reports/058-review-save-qa-diagnostics.md の新規作成だけ。専用隔離checkout・一時QAで反例と検証を行い、指定branchへ2文書をcommit/pushする。
本番・検査・workflow・過去証拠・契約・保護26・test/.scope-lock・通常入口・原画を変更しない。新PR/main/PR33への反映、force、削除、追加委譲、新環境起動、mount/VHD/ACL/OS設定変更は禁止。

## 独立確認
1. 基点849d02bd2ea4dd44298eef225fe9a12927858d1bから057提出までの全差分を許可パスに照合。3cf4b6c完成後のコード不変、本番/保護/原053/旧055固定SHA・inventory・expectations・contract・scope prefix不変を確認。R01〜08と保護26前後を実確認する。
2. 実子30秒timeoutの前後再現、stdout/stderr部分出力、PID/argv/開始終了/exit/timeout種別/deadline/kill/waitを照合。正常・異常exit・親例外・起動失敗・境界kill・worker例外・受付停止・queue/dequeue済み子未起動・active子回収を検証。縮尺0.2秒fixtureを実174/180秒超過試験と呼ばない。未取得・未回収を成功/exit0で補わない。
3. Suite.run/run_restart_batch、RestartBatch、run_ci.py外側の各例外経路を読み、終了直前raceや並行例外で再び原ログが消えないか独立反例で確認。OSに強制終了された親のfinally保証など、保証不能な範囲を区別する。子/worker回収・ログ確定も元予算内で行われるか確かめる。
4. queue→worker→一意batch/PID→各root/futureを対応づける。共有batchやroot投影の時間二重計上、inclusive/exclusive/wallと累積の混同、未完の集計除外を調べる。
5. 診断wrapperが本体へ同じ引数を渡し、plan本文の計測追加以外一致、入力/履歴/出力hash・数量・memoryのoff/on一致、cache復活/検証省略なしを確認。decode/migration/prepare/encode、plan/verify、native、起動/依存/snapshotの境界と回数を検証する。
6. WindowsとLinuxの実OS/CPU/FS/SHA/profile/worker/batchを区別。6seed×off/on各1回のsampleを統計的性能保証や全取引成功としない。原053/055固定とlatest057、21d6a66/f6d5697/80cff71/fdd6ce0の実コード・helper・原証拠を分離。同一hashでも異なるCPU/負荷をOSだけの差と断定しない。Windows実環境がなければCI原物照合とローカル独立実行を区別する。
7. 既存055 latest scopeは055固定SHA対象であり057差分の保証ではない。新057 scopeの後続文書正例・担当外負例・固定差分負例を実exitとbytesで確認。fixed055は旧checkoutのrunnerで、057修正の成功に数えない。
8. 23archive/58325 memberと報告された今回原証拠、元21archive/258948 member、不変inventory541のhash・サイズ・索引集合・Git blobを照合。取得できないZIP API digestと復元raw hashを混同しない。全展開・一部抽出・報告読取りを区別し、アクセス拒否を迂回しない。
9. 原172ケース/2178条件/97kill、native primitive/配布物、16伝播とscope正負、S1/S2・装備・旧比較142/10全文を保持。実際の再実行/原ログ照合/未確認を区別。全体180秒・内174秒・子30秒・import600秒・job15分と既存予算不変。skip、continue-on-error、警告無視、期待弱化、ケース削減、時間延長は禁止。
10. 最終057は6workflow・47job全終了、42成功5失敗（native両OS fixed/latestの4transaction、旧053 latest1）。生ログで時間未達と診断成功を照合。中間f6の45/2を最終と混同しない。F4実ENOSPC/nested別volumeはNOT_RUNのまま。
11. 指摘があれば再現・影響・重大度・最小修正パスを示す。F5解消の可否と計測の妥当性、F1/F4残件、次の最小調査案を分ける。既存codec等の変更・新たな最適化は実行せず提案だけ。

## 提出
判定と未達を先頭に、日本語で根拠・実argv/秒/exit・成功/失敗/未実施、CI/run/SHA、反例、証拠取得限界、次の最小案を報告。058は2文書だけ保存し、自分の状態を報告済みにする。最終SHAの全workflow/job終了を確認し、clean/未pushを返す。全CIが緑でない間は保存機能全体の完了やmain統合可能とはしない。レビュー文書追加のscope拒否と既存の実装失敗を分ける。
