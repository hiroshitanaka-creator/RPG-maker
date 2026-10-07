# 041 装備保存の純粋変換の報告

## 作業前の計画

基点mainは `821448b384d37edc041152beb5d6b6f560ad771d`、依頼登録は `a6a61a7eb0fe071ba5c8e662e5506c3582c0df9e`。登録を直接fetchし指定ブランチを作成した。開始時の未コミット変更なし、登録以外の未pushコミットなし。別タスクの取り込み、追加委譲、main書込み・マージはしない。checkoutの `.agents/skills` は存在せず、`/workspace/.agents` は空。AGENTS.mdと関連設計・依頼・報告・旧保存実コードを確認する。

API案：`EquipmentSaveMigration.plan(document, source_sha256, context)`、`grant_common(document, source, source_sha256, context)`、`EquipmentSaveValidation.validate_new(document, source, source_sha256, context)`、`compare_transition(source, candidate, source_sha256, context)`、`EquipmentStateView.project(state)`。入力は型復元済みの旧doc。contextには実GameSession（旧状態・旧人物検証と実jobsを読むだけ）と明示能力定義を渡す。成功は参照を分離した候補と二系統監査、失敗は理由とパスでcandidateなし。新能力fixtureを現GameSessionへ登録しない。

既存変更は `_valid_state` の人物本文を `validate_legacy_actor` へ、`IntegratedProgression.upgrade` の人物処理を `upgrade_actor` へ純粋抽出するだけ。元のparty入口・結果・副作用を固定版との同一入力照合で確認する。

手書き期待はtools/fixtures/equipment-save/へ置く。M01〜M08、M10/M11の純粋部分について、全人物の順序、数量・所有、JP/忘却、能力追加、型・値・入力不変、候補参照分離、ID決定性、異常理由を検査する。元SHAの別checkoutと実装SHAの別checkoutで実行し、既存証拠は上書きしない。

S1の保証は純粋変換・装備層・許可差分・台帳の照合まで。codec、新版stats/全保存検証、通常ゲーム接続、実ファイルI/O、実ユーザー保存は対象外。新検査CI接続も未許可で変更しない。既存R8・保護26・素材・装備5394＋93／400切替・異常202と最終同一SHAの全CIを別途確認する。
