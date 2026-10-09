# 059 保存QAの起動前記録と限定子孫回収を修正する
- 状態：報告済み
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-10 JST
- 前提：なし（058の差し戻し修正。保存全体の成功を前提にしない）
- 基点：058提出579ca1f463aaf9e93275039a59cf9d1ffb86adb5
- ブランチ：codex/task-059-fix-save-qa-finalization
- 承認：2026-10-10 01:59 JST、依頼者が059の具体的なブランチ登録・クラウドSol/High発注を含むA「起動前の記録漏れと、今回のテストが起動した子孫処理だけの回収を修正する」を選択。使用量不明を提示済み。本番コード・OS設定・検査時間は変えない。
- 指揮・受入：ルッカ。実装修正・検証：上記Codex。

## 目的・読むもの
承認済みのF5-a起動前終端記録とF5-b専用QA子孫回収を修正しWindows/Linuxで再検証する。F1時間内未完走・F4実容量不足/別volume未測は別に保持し、保存全体の完成と呼ばない。
AGENTS.md、docs/tasks/README.md、057依頼/報告、058報告全文・再現コード、専用platform driver/helpers/workflow、原053/055/057の固定証拠を読む。必要ならcheckoutの.agents/skillsから関連SKILL.mdを読む。

## 担当の場所
- tools/check_equipment_save_transaction_platform.py
- tools/fixtures/equipment-save-transaction-platform/ の process_capture.py、run_ci.py、test_capture057.py、capture_fixture.py
- 同directoryへの今回専用process監督helper・scope059/診断helper・回帰fixtureの追加
- diagnostic_ci057.py と .github/workflows/equipment-transaction-platform.yml は必要な世代分離配線のみ
- 新 docs/verification/task059-save-qa-finalization/、本依頼書状態行、docs/tasks/reports/059-fix-save-qa-finalization.md、docs/decision-log.mdの今回追記
禁止：scripts/本番、native/addons、旧053検査/証拠、旧055/057完成SHA・inventory・expectations/recovery-phases/contract、scope057.py/055 scope許可prefix、他workflow、AGENTS、test/.scope-lock/保護26、原画/data、過去報告の変更。担当外が必要なら最小差分を親へ報告し該当部分だけ保留する。

## F5-a 起動前終端記録
1. 基点で058のrestarted-batch.jsonをdirectoryにするIsADirectoryError反例を再現し、欠落・recovery_complete誤判定の原証拠を保持。
2. request受付時から安定IDと予定record先を持ち、config/env/capture準備/log.open/record保存を含む失敗を終端に確定する。Suite.runのqueue前経路も含める。
3. 未起動はPID/実argv/子log/exitを捏造せずNoneと理由。予定argvと実argvを分け、共有batchと各要求を対応づける。
4. closeは例外文字列一致に依存しない。recovery_completeは全受付要求の終端記録・ID対応・起動済みprocess終了・worker/future終了が確認できた時だけtrue。欠落/壊れJSON/ID違い/保存失敗を上位へ非0・未確認として伝播する。
5. 記録不在をprocess不在の証明としない。保存先自体が書けなければ可能な上位に対象/理由を記録し、不完全とする。回収完了と取引成功を分離し、失敗要求を完了ケース数へ加えない。
6. 実反例に加えenv/capture準備失敗、log/record失敗、4root共有batch、記録欠落/壊れJSON/ID違い、close競合/再呼出し、Suite.run queue前失敗を検証。既存12検証を削除・弱化しない。

## F5-b 自分が起動した専用QA子孫だけを監督
1. 開始から所有根拠を持ち、親finallyを前提にしない。Linux専用process group/sessionやWindows専用Job Object等は候補。OS設定・権限変更・持続的アクセス作成は行わない。
2. global/name一致kill、他job/ユーザーprocess終了は禁止。所有不明なら終了せず未確認とする。
3. 直接子waitと子孫停止確認を分離。Windows所属確定前の孫起動race、Linux入れ子captureの外側監督逸脱を検証。未監督を成功扱いしない。
4. 元174/180/30秒の残量内で停止・確認・記録。期限後の追加待機や予算延長で成功にしない。残量0なら未回収/未確認の理由と保証範囲を明示する。OS全体停止等まで完全保存を保証しない。
5. 両OSで親→待機孫の058縮尺反例、親先行終了、孫のlog handle保持、通常終了での残子孫、所属/終了race、監督設定失敗、期限0、無関係な専用sentinel生存を確認。縮尺を実174/180秒検査と呼ばない。

## 世代別CI・保持する検査
- 057固定3cf4b6c293f6796220b43cf566f8eb792c3932ecは当時のコード/検査/期待で保持。scope057の正負と固定証拠を削除・skipしない。
- 057完成SHA→HEADのcode不変検査を059変更へ無理に適用せず、057固定checkoutと059最新継続回帰/新scopeを分離する配線・対応表を先に計画する。旧scope許可prefixを拡張しない。
- scope059は基点579ca1fから許可パス限定、新コードを完全SHA固定し、後続文書正例/担当外code負例/固定差分負例を実exitで検証。
- 原053固定e003b126de6695fa131e07a3db14c3011fb74f2e、055固定0a44409c99b06569b9e6088ffeb46c2238c821faは不変。原172/2178・97kill、16伝播、primitive/配布物、S1/S2・装備・旧比較142/10全文、R8・保護26前後を検証する。
- 既存job/コマンドの180/174/30/600秒・15分、worker/batch、全期待を保持。別job化も既存上限を超えない。skip/continue-on-error/警告無視/期待弱化/ケース削減/時間延長は禁止。未達を正確に残す。
- 正常sample計測と全取引受入は別。batch一意、inclusive/exclusive、wall/並行累積を分離して二重加算しない。既存codec最適化・cache復活・検証回数削減は対象外。
- F4実ENOSPC/nested別volumeはNOT_RUN。mount/VHD/ACL/OS設定/共有disk充填/新環境起動は行わない。

## 計画と提出
開始前後のdirty/未push、最小変更計画とCI世代対応、変更一覧、実argv/秒/exit、両OS修正前後・原証拠・完全SHA/hash/索引・保証限界・F1/F4/F5残件を日本語で報告する。旧証拠を上書きせず、実行/照合/未確認を区別。
指定branchへcommit/pushし、本依頼状態を報告済み、上記報告書を保存。新PR/PR33反映/main push/merge/force/削除/追加委譲は禁止。最終SHAの全workflow/job終了とclean/未pushを確認して返す。全CIが緑でなければ保存全体の受入完了とはしない。F5修正とF1/F4残件を分ける。
