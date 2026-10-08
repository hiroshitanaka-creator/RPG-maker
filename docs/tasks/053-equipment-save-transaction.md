# 053 保存I/Oと中断復旧を実装する
- 状態：未着手
- 担当：Codex GPT-6.1 Sol／High
- 依頼日：2026-10-09 JST
- 基点：main 87f4e66ed64f2ae9a92538acb9716c6a01f5cb27（PR32統合後37CI成功）
- 作業ブランチ：codex/task-053-equipment-save-transaction
- 承認：2026-10-09 05:43 JST、ユーザーはS3の専用テストデータだけの実装・検証へ進む案Aを選択。通常UI/実ユーザー保存への接続は対象外。

## 目的と前提
040計画のS3・M13〜M16を実装する。S1/S2と049〜052は確認済みでmain統合済み。AGENTS、040計画第4/7/9/10節、051/052報告を読む。元保存を上書きせず別出力を確定し、途中失敗・プロセス終了後にも同じ取引として復旧できることを機械検証する。
専用QA領域以外のI/O、ユーザー保存・履歴の読み書き、通常load/save/UIへの接続、S4/S5、ゲーム規則・数値・名称の追加はしない。

## 担当範囲
- 新 scripts/game/equipment_save_transaction.gd と必要uid
- 新 tools/check_equipment_save_transaction.py、tools/equipment_save_transaction_probe.gd、tools/fixtures/equipment-save-transaction/
- 新 docs/verification/equipment-save-transaction/、docs/tasks/053-equipment-save-transaction.md の状態行と docs/tasks/reports/053-equipment-save-transaction.md、decision-log今回分
- 専用CIは新 .github/workflows/equipment-transaction.yml に追加する。新wrapperは tools/fixtures/equipment-save-transaction/ 内。既存workflow/wrapper/保護検査・S1/S2公開契約の変更は別途切り分ける
通常GameSession/UI/戦闘/記録処理への接続、実ユーザー保存・履歴へのアクセスは含めない。全I/O試験は専用QA rootと隔離XDG内。

## 必須の機能
1. inspectは読取りのみ。source bytes/サイズ/SHA、decoder結果、既存取引を返し、通常load/recording/archiveを起動しない。
2. prepareはsource expected hashとセッション世代を照合し、排他的取引dir・原bytes backup・該当履歴raw backup・新tmp書込みと読戻し検証を行う。原sourceは上書きしない。
3. commitは元hash/世代/候補/衝突を再照合。別converted.jsonへのrenameが成功点。成功後にreceipt更新が失敗しても「未確定」と偽らない。メモリ適用はS3で実施しない。
4. recoverはreceiptのphaseを信用せず、原本/backup/tmp/確定出力のbytes・hash・型・値・migration_idから判定する。同じ取引を再利用し二重付与を起こさない。
5. パスはQA root内に解決されるものだけ。..、別volume、同一ファイル、既存出力、外部改変、二重writerを拒否。実体解決後にrootを外れるリンクも検証する。既存ファイルやユーザー領域の削除なし。
6. trialIDあり/なし、sidecar正常/欠落/破損を区別する。存在する履歴は破損時もraw保存、欠落を履歴完備としない。新ID・運用イベントは生成しない。

## 機械検証と証拠
- 040第7節の各境界に対し、前後killと別プロセスrecoverを行う。期待phase、ファイル存在、全bytes/hash、原source不変、候補数量、二重付与0を固定期待で比較する。
- open/store/flush/readback/rename失敗、ENOSPC、非root権限拒否、target衝突、同時writer、source差替え、receipt・backup・output改変を含める。
- 容量不足は注入と実際の書込み失敗を分けて記録する。OS設定やユーザーの権限変更で試験環境を作らない。使える専用環境がなければ未検証として明示。
- 同じrawを別名にしても同migration_id/同数量、新版の再入力はalready_migrated、内容同じでもraw違いは別sourceとして区別。
- コマンド予算は全体180秒、子プロセス各30秒、import600秒、CI各15分。超過を隠さず、既存予算を延長しない。
- 完成時の変更範囲条件は完全SHA固定checkoutで保持。最新側では継続する全動作条件を実行し、後続レビュー文書の追加で誤拒否しない設計を検証する。
- 原証拠、全ケースID・期待・実際・終了code・kill地点・ファイル一覧・hash・ログを保存。提出時は最終SHAの全CI、R全8、保護26、既存装備/S1/S2回帰を確認。

## 明示する限界
プロセス強制終了の検証を、停電・媒体故障・全OS/FSでの耐久性保証と呼ばない。通常ロード/メモリ適用/UI公開/戦闘接続はS4/S5の残件。新しいゲーム規則・倍率・価格・入手数量は決定しない。

## 2026-10-08 確定S2 APIとの接続照合（準備のみ）
照合対象：RPG-maker a0b7adbf8124f850e611bbbed423f0dd98a0f5c6 の実ソース。040計画の提案名と実在APIを区別する。

- equipment_save_codec.gd の decode_source(bytes: PackedByteArray, context: Dictionary) は成功時document/source_bytes/source_sha256/source_format/observations/errorsを返す。source_formatはequipment-v1またはlegacy-N。I/Oは行わない。位置修正はposition_relocation_requiredとして差分提示し拒否するので、S3で勝手に位置補正して通さない。
- encode_candidate(document: Dictionary, context: Dictionary) はcontextも必須。出力bytesのhashがdocument_sha256であり、元rawのsource_sha256と取り違えない。再decodeによる全値・型・順序一致を内部で確認する。S3のファイル書込み後にも別途読戻した実bytesでこの整合を確認する。
- equipment_document_validation.gd の prepare_candidate(candidate, context) はmetadataの整合を先に検証し、上限再計算と現在値の切詰めを行いdocument/caps_changesを返す。失敗したmetadataを削って再試行しない。入力を直接変更しない。
- 同 validate(document, context) は新版一般状態検証。compare_migration(source, candidate, source_sha256, context) はS1の再計画と候補準備による移行差分照合。進行後保存の一般検証へ元source一致条件を混ぜない。
- contextは有効なGameSession/BattleCatalogと実能力定義に一致するabilitiesを必要とする。S3でも固定でtrueを返す代替検証器を受入証拠にしない。正常contextとnull/型不正の拒否を専用QAで確認する。
- 040第7節の「新tmp読戻し」はhash一致だけで済ませず、実ファイルbytes→新版decode→候補の全値/型/順序とmigration_idを照合する。元原本のbytes/サイズ/hash不変も別に検証する。
- 049完成固定112/723/13と051修正版154/975/18＋scope2をそのまま維持する。新S3検査の追加件数は別に固定し、既存検査の期待を上書きしない。

この追記は既存実装の読取り照合であり、S3実装・発注・I/O試験の実施を表さない。


## 実装・検証・提出の条件
- 上記接続照合は実在APIの資料であり、新しいS3実装では明示contextと許可済みQA rootを受け取り、依存関係を正しく渡す。040提案の旧関数名を実在すると仮定しない。
- inspect/prepare/commit/recoverのAPIと失敗契約を明文化し、各入口の正例・負例・不変条件をfixtureへ固定する。receiptだけを信じず、実bytes、型、値、migration_idと検証済み元保存から判定する。
- 同一取引の安全な再試行と別取引の衝突を分け、二重writerや所有権未確認のファイルを上書きしない。既存原本・backup・確定出力を保持する。新規専用QAで自分が生成した未完tmpの扱いだけを契約に沿って実装する。
- OSやユーザーの権限・ディスク設定を変更して失敗試験を作らない。環境内で既に使える非root実行や専用QAの失敗条件を使い、実測できない項目は明示して相談する。疑似注入だけを実ENOSPC/実権限拒否と書かない。
- 新workflowは固定完成SHAの全条件と最新の継続動作を分離。未完のSHAを完成固定にしない。固定対象・全コマンド・実exit・Godot公式版/hash・ケースID/件数/固定期待を記録し、後続文書追加のlatest正例と範囲逸脱の固定負例を検証する。失敗/警告/欠落/証拠改変が成功へ化けないことも専用検査に含める。
- Godot 4.7.2。既存S1/S2/装備/旧比較/R01〜R08/保護26/全CIを保持。既存workflow・検査・fixture、test/、.scope-lock/、原画/assets、通常本番入口、過去証拠は変更しない。担当外変更が必要なら理由と最小差分を返し、その部分だけ保留する。
- 開始前後の未commit/未pushを確認。関係ない変更を含めない。コードを完全SHAで固定して原証拠を別保存し、報告後のコード不変を照合する。全変更ファイル、実測、未実行を報告する。
- 指定branchへcommit/pushし、draft PRで提出。自身の状態だけ報告済みにする。最終SHAの全CI終了まで確認し、完全SHAとrunリンクを最終応答に記す。main直接書込み・merge・強制push・削除・追加委譲なし。親が独立レビューと受入管理を行う。
