# 040 装備保存移行の接続設計報告

## 作業前の計画・境界

- 対象main：`0d8393070a6ff968ea95474654a975d4b349d397`。登録SHA：`de4b2c1b8574a255f03bb2b08317a82567bd4dc4`。指定ブランチ：`codex/task-040-equipment-save-plan`。
- 開始時の未コミット変更なし。指定リモートブランチのSHAは登録SHAと一致し、そこから作成したローカルブランチに未pushコミットなし。mainとの登録差分は040依頼書のみ。
- 読む関数：GameSessionのsave/load/import/export/_valid_state/_normalize_numbers/upgrade_rules、生成/加入/解放/能力/戦闘報酬、SavedDocument、SavedValueTypes、IntegratedProgression、EquipmentRules、BattleCatalog、JobMastery、FirstRegion.valid、metrics/archive、GameRootの通常保存/復帰/旧更新UI。
- 決定済み：034〜039確認済み・PR27統合済み・mainのCI20成功は親からの引継ぎ。Q1A（鉄の短剣）/Q2A/Q3A、旧枠数量、7＋3配布、戦士既得報酬、原保存と進行保持を変更しない。
- UNKNOWN：OS別電源断耐久性、未記録旧型/未記録人物や入手数、新能力の未実装catalog/実戦接続、後続の正式調整・販売接続。仮成功で埋めない。
- 担当3文書：新 `docs/design/equipment-save-integration-plan.md`、040依頼書の状態行、本報告だけ。コード/data/原画/既存文書/保護/契約/workflowは変更しない。追加委譲・mainマージなし。

AGENTS.mdと伝言板の決まりを確認。checkout内 `.agents/skills` と `/workspace/.agents/skills` は存在せず、適用するローカルskillなし。034設計、035採用追記、036/038/039報告と実API、素材規約・台帳の構成、職業/魔物化企画と優先されるexperience-spec-v2、装備原本を参照した。

## 成果と根拠

[技術計画](../../design/equipment-save-integration-plan.md)に、実装者が使う責任別API、引数/戻り値/失敗コード、呼出し順、保存先、許可差分、型復元順、数量policy、移行IDと一回性、失敗点ごとの復旧表、18群の機械fixture、5件の発注順を記載した。計画のみで新機能実装は未着手。

実コードで確かめた重要な点：

1. GameSession.save_gameは旧_valid_state前提で、archive flush後tmp→rename。読戻しはない。load_gameは位置補正・metrics/recordID・正規化・型復元・archive再開まで行うため、純粋preview/移行読戻しへそのまま流用できない。
2. IntegratedProgression.valid_world/valid_actorは旧armory/weapons必須、EquipmentRulesは混在拒否。版別の共通検証が必要。装備APIは保存全体や能力catalogを保証しない。
3. EquipmentRulesにはfirst_region.reserveが必須。旧本編へfirst_regionを永続追加するとモードが変わるため、検査/計画用の投影だけに空reserveを補う。
4. 旧upgradeとGameSession.upgrade_rulesはpartyだけを処理する。FirstRegion.validはreserveのArray型だけで人物本文を保証しない。全人物の旧検証と変換を抽出する必要がある。
5. 移行にchange_job計画をそのまま使うと合法従前装備まで最強へ変更する。専用builderで従前維持・空主武器/防具だけ割当てを行い、完成時に既存装備APIで検証する。
6. BattleCatalogはequipmentの能力を未登録。two_handedのcatalogと全状態検証/statsを同時に用意し、一般技JP閾値で覚える経路とは分ける。
7. PlaythroughArchive.resumeは履歴欠落時に新IDを発行する。移行前に呼ばず、原保存の_trial_idとsidecarの原bytesを保管し、成功後の通常再開イベントを別に扱う。

旧初期4人はQ1A6＋支援6、共通支給後22。形式1は記録人物P＋2を専用支給として別監査し、旧形式2と二重計上しない。新規本人8・共通10・魔物職0補填・副武器補填0・採用Q3Aの仮値と手動装着を維持する。

## 後続の順序と承認境界

S1：未接続純粋変換と全人物検証 → S2：codec・能力catalog・新版全検証 → S3：別保存I/Oと中断復旧 → S4：支給/全切替/能力報酬/実戦/復帰 → S5：通常明示UIと公開。各件の担当パス・前提・入口/出口・コマンド・上限・失敗注入は計画9節。

原本bytesは再encodeせず保管し、型/値/配列順を別に比較する。位置補正は別チェックポイント、形式1JP換算・新数量/新習得は別監査。判断と理由・戻し方は計画12節へ記録し、範囲外のdecision-logは変更しなかった。

将来承認が必要なのは既存保存領域検査の版別拡張・旧UI期待の世代分離、新検査のworkflow接続、実際に必要になった場合の保護変更の具体差分。今回どれも実行しない。R-06完全一致、R-01職数、R-02修練条件等は最新でも継続する。現在のpush20jobと手動旧本編workflowは区別した。採用済み名称・数量・効果に追加判断は不要。

## 実行コマンド・検証

標準PATHのGodotは4.6.3で、版確認時にfontconfigのcache警告が出た。これを受入実行に使わず、CI指定4.7.2-stableを/tmp/task040/binへ取得。ZIP SHA-256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` を照合して成功。XDG_CACHE_HOME/DATA_HOME/CONFIG_HOMEは/tmp/task040/xdg配下へ隔離した。

通常検査は登録SHAの独立clone `/tmp/task040-check` で実行。検査生成物は指定3文書以外へ登録しない。本番・data・既存検査は提出版と同一で、文書差分は実行後に範囲照合する。

| コマンド | 実測結果 |
| --- | --- |
| `git fetch origin codex/task-040-equipment-save-plan` と `git fetch origin de4b2c1b8574a255f03bb2b08317a82567bd4dc4` | 成功。fetch設定がmainだけのため直接switchは未登録refとして失敗、その後登録SHAから指定名でbranch作成して一致確認 |
| `git ls-remote origin refs/heads/codex/task-040-equipment-save-plan` | 開始時de4b2c1…一致 |
| `git diff 0d8393070a6ff968ea95474654a975d4b349d397 HEAD --stat`（作業前） | 040依頼書だけ |
| `timeout 600 godot --headless --editor --import --quit` | 指定版でexit0。SCRIPT ERROR/ERROR:/WARNING:/Parse Error該当0 |
| `python tools/check_frozen_files.py`（検査前・文書作成後） | exit0、保護26/26一致 |
| `python tools/run_locked_checks.py` | exit0、R-01〜08の8件全PASS、全tests_ran=true/parser_failed=false、timeoutなし |
| `python tools/validate_assets.py --strict` | exit0、素材1154・音15・パレット3・字体2、問題なし |
| `git diff --check` | exit0 |
| checkout/local skill、API/キー/検査/workflowのrg・本文読取り | 上記根拠と計画の実assert対応表を作成。計画中の新API名を現行APIと区別 |

R内訳：R-01=2tests/765assertions、R-02=5/946、R-03=2/73、R-04=1/293、R-05=2/79、R-06=2/87、R-08=17/2302、各failed=0/pending=0/invalid=false。R-07はA01〜A14全PASSとFIRST_REGION_PASSを既存判定器で確認した。Rログ・import・素材ログは/tmp/task040と独立cloneの.toolsにあり、担当外証拠ファイルは追加しない。

GitHub CLIのauth status/APIは無効token/Forbidden、認証なしHTTPも接続不可だった。接続済みGitHub connectorのread-only fetchで登録SHAのActions runs取得に成功したため、提出後も同手段で確認する。git fetch/pushは別経路として結果を確認する。失敗したCLI確認をCI成功と扱わない。

## 提出CI・自己点検・未検証

本報告を含む最終コミットのSHAと、その同じhead_sha・pushイベントの全CI（3＋17job）の終了結果は最終返答に記す。自己参照で報告SHAを更新し続けないため、本報告作成時にはまだ存在しない提出CIの成功を先取りしない。親が確認したmainの20件を提出版CIの代わりにしない。

指定3文書だけ、040依頼書は状態行だけを変更する。採用規則の再質問/変更なし、実装なし、実保存変換なし、main更新なし、追加委譲なし。計画の各実装件には前提・完了条件・検査入口があり、原bytes/型/数量/副作用/再起動をfixtureで比較する設計になっている。

未検証：M01〜M18は検査仕様で未実装・未実行。新移行API、実ユーザー保存、電源断耐久性、新装備通常接続/実戦/新CI接続は未実施。今回は文書計画の受入だけであり、装備保存移行の実装完了や新規則公開とは報告しない。
