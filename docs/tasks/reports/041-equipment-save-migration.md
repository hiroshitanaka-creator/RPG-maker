# 041 装備保存の純粋変換の報告

## 作業前の計画

基点mainは `821448b384d37edc041152beb5d6b6f560ad771d`、依頼登録は `a6a61a7eb0fe071ba5c8e662e5506c3582c0df9e`。登録を直接fetchし指定ブランチを作成した。開始時の未コミット変更なし、登録以外の未pushコミットなし。別タスクの取り込み、追加委譲、main書込み・マージはしない。checkoutの `.agents/skills` は存在せず、`/workspace/.agents` は空。AGENTS.mdと関連設計・依頼・報告・旧保存実コードを確認する。

API案：`EquipmentSaveMigration.plan(document, source_sha256, context)`、`grant_common(document, source, source_sha256, context)`、`EquipmentSaveValidation.validate_new(document, source, source_sha256, context)`、`compare_transition(source, candidate, source_sha256, context)`、`EquipmentStateView.project(state)`。入力は型復元済みの旧doc。contextには実GameSession（旧状態・旧人物検証と実jobsを読むだけ）と明示能力定義を渡す。成功は参照を分離した候補と二系統監査、失敗は理由とパスでcandidateなし。新能力fixtureを現GameSessionへ登録しない。

既存変更は `_valid_state` の人物本文を `validate_legacy_actor` へ、`IntegratedProgression.upgrade` の人物処理を `upgrade_actor` へ純粋抽出するだけ。元のparty入口・結果・副作用を固定版との同一入力照合で確認する。

手書き期待はtools/fixtures/equipment-save/へ置く。M01〜M08、M10/M11の純粋部分について、全人物の順序、数量・所有、JP/忘却、能力追加、型・値・入力不変、候補参照分離、ID決定性、異常理由を検査する。元SHAの別checkoutと実装SHAの別checkoutで実行し、既存証拠は上書きしない。

S1の保証は純粋変換・装備層・許可差分・台帳の照合まで。codec、新版stats/全保存検証、通常ゲーム接続、実ファイルI/O、実ユーザー保存は対象外。新検査CI接続も未許可で変更しない。既存R8・保護26・素材・装備5394＋93／400切替・異常202と最終同一SHAの全CIを別途確認する。

## 実装とAPI

実行コードは `8d3c1848d09b588fa41bcf6345d3aab6e12a5347` に固定した。以下の証拠はこのSHAの別checkoutで取得し、後続の報告・証拠コミットでは実装・fixture・検査器を変更しない。

| API | 入力と結果 |
| --- | --- |
| `EquipmentSaveMigration.plan(document, source_sha256, context)` | 型復元済みの旧形式1/2、64桁小文字hexの元保存SHA256、明示context。成功は `ok/reason_code/candidate_document/migration_id/legacy_format_audit/equipment_audit/errors/guaranteed_layer`。失敗は `ok=false/reason_code/errors` のみで候補なし |
| `EquipmentSaveMigration.grant_common(document, source, source_sha256, context)` | 移行時の信頼する旧sourceとpending候補。解放の事実は `context.job_change_unlocked=true`、地方モードでは候補の同名bool進行フラグもtrueを要求。許可差分はそのフラグと共通10個・監査・型記述だけ。成功候補はコピー。正規grantedへの再実行は `already_granted` で候補なし |
| `EquipmentSaveValidation.validate_legacy(document, context)` | party/reserve全人物を実旧人物検証へ渡し、旧全体入口も確認。旧・新混在、未知root/人物/人物integratedキー、不正reserve、重複人物ID、非有限数、JP換算overflow等をパス付きで拒否 |
| `EquipmentSaveValidation.equipment_layer(document, context)` | 新装備層の型、全個体の所有、合法装着、能力定義、装備補正overflowを既存EquipmentRulesと明示contextで検査。生成数量と台帳の正規性は次の差分照合が担当 |
| `EquipmentSaveValidation.compare_transition(source, candidate, source_sha256, context)` | 信頼する旧sourceから許可結果を再計算してキー・型・値・配列順を厳密比較。候補側の監査を許可表にしない。新sourceによる再帰や台帳改ざんを拒否 |
| `EquipmentSaveValidation.validate_new(document, source, source_sha256, context)` | 上の装備層と正規移行・正規共通支給の差分照合を実行。一般の進行済み新保存を受理する全体検証器ではない |
| `EquipmentStateView.project(state)` | コピーだけに、存在しない `first_region.reserve=[]` と `midgame_slots=false` を補う。元に存在する不正値は拒否。保存候補へモードや容量既定を永続追加しない |

必須contextは、データ読込みが成功した実 `GameSession` を `legacy_session` に、旧定義すべてと明示的新能力の完全定義を含むDictionaryを `abilities` に置く。旧能力定義の上書き・欠落は拒否する。fixtureの `two_handed` はpassive/selfとして明示し、能力の戦闘倍率や効果を新設していない。現GameSessionへ登録もしていない。`source_build` は任意Stringで、未指定はunknownを監査に記録する。移行済みdocの `plan` 再実行には信頼する旧入力を `context.source_document` に渡す。正規候補を検証して `already_migrated` を返し、所有・数量・監査を改変した候補は拒否する。

SHA256とsourceの由来は呼出し側の責務である。S1は実バイトを読むcodec、SHAとファイルの一致確認、署名・真正性確認を実装していない。型復元済み旧docの入力契約を使い、既存metadataがある場合の `_saved_value_types` はコピー側で再記述する。旧保存をdecode/normalizeしたことにはしない。

## 採用規則と監査

人物の格納配列は並べ替えず、割当処理だけ人物ID順にする。個体IDは元保存SHA・固定policy・catalog revisionから得るmigration IDと連番で決定し、同じ入力の再実行は全候補まで一致する。

形式2は旧各武器枠を別個体にし、旧armoryの未装備解放品だけ各1個を追加する。未解放品は0。形式1は記録されたP人だけの剣P個＋杖1＋弓1でP+2。旧形式更新後の初期armoryから形式2数量を重ねて数えない。全人物の合法従前を先に確保し、不適合品をすべて袋へ戻してから不足を処理する。袋では攻撃/防御降順、item ID、instance ID順。主武器・防具だけ不足時に移行支援を生成し、副武器補填・魔物職武器防具補填・移行による本人初期8個は0。

共通10個は支援計数の後に採用済み順で各1個。地方モード未解放はpending、解放済みまたはfirst_regionのない旧本編はgranted。`actor_initial` は空、`actor_support` は全記録人物の処理結果（生成0も空配列で記録）。生成理由は `legacy_slot/legacy_unheld/format1_supply/migration_support/common_set` を分け、旧armoryと人物別旧枠・割当個体、不適合返却、習得追加を equipment_audit に残す。

形式1だけ既存JPのfloor換算・忘却/relearnを純粋抽出へ渡し、partyとreserveの全記録人物に一度適用する。legacy_format_auditに元/先JPと作成integratedを残す。形式2の未記録修練は既存 `JobMastery.initial` と同じ counts空・取得済みlegacy_mastersで初期化し、JP換算・忘却はしない。記録済みcounts・JP・習得/装着順は維持する。戦士の既得masterだけ `two_handed` を末尾へ1回追加し、装着・回数補完・未master追加はしない。

## 旧入口の最小抽出と前後等価性

`game_session.gd` は旧 `_valid_state` 内の人物本文を `validate_legacy_actor` へ抽出し、重複IDチェックを旧全体入口に残した。旧人物検証の条件・計算は保持する。`integrated_progression.gd` は旧 `upgrade` の人物本文を、人物をdeep-copyして返す `upgrade_actor` へ抽出した。旧入口はpartyだけを処理する従前のまま、新S1側だけreserveを別途処理する。

同じ固定fixture・比較検査器を抽出前 `a6a61a7eb0fe071ba5c8e662e5506c3582c0df9e` と実装SHAへ置き、旧全体検証142入力、更新10入力を実際に実行した。成否、純粋更新結果、既存import/upgrade_rules、二重更新、stateの型・値、metrics/history、旧save/load往復まで出力がbyte単位で一致した。旧入口による新能力追加は全員0。旧I/O往復のfixtureファイルは隔離XDG内の専用user://だけで、実ユーザー保存には触れていない。旧save/loadコードは変更していない。

前後出力の展開SHA256はともに `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。`legacy-before.json.gz` / `legacy-after.json.gz` と両実行ログを今回の証拠へ保存した。

## 固定期待と040 M対応

`tools/fixtures/equipment-save/base.json` は抽出前の実旧入口から得た型復元済みの固定入力。派生入力と明示能力定義は `fixtures.gd`、数量・所有連番・袋順・支援順・JP・忘却・能力追加・migration IDの手書き期待は `expectations.json` にある。migration IDの期待は独立したPython hashlibで固定した。実装出力を期待として保存していない。固定ケースの元保存hashは `a` 64文字の明示fixture値であり、実行コードSHAや実ファイルhashと混同しない。期待JSONのSHA256は `fc1ac6a46ceaf6381473aa1a4943333f33ba5d9777ddbaf60b3963e0bca29fd3`。

| 040項目 | S1で実行した固定期待・反証 |
| --- | --- |
| M01 | 旧形式2 party1/reserve3：旧数量6＋支援6＝pending12、共通後22。品別数量、4人の武器/防具所有、袋順、支援順を固定照合。旧本編のモード・容量キー欠落も保持 |
| M02 | 同名旧武器枠を別IDへ。全旧剣枠5、未装備解放iron_blade1、未解放0、副武器補填0、旧枠順保持 |
| M03 | 合法な弱い従前武器・負値staffを維持。既存EquipmentRulesの同職change_jobでは最強化。reserve既所有を袋選択から除外し、不足だけ補填 |
| M04 | 不適合旧主/副武器、魔物職の返却順・個数を固定。魔物職支援0、空副枠補填0。合法副武器を維持し主だけ袋から補う同点個体の安定順も確認 |
| M05 | 形式1 party3/4のP+2＝5/6、旧数量二重計数0。party4は共通前12/後22、party3は支援4と共通10で19。旧JP12/24/36→60/120/180、忘却/relearnを固定。形式2未記録修練はcounts空・JP換算0 |
| M06 | 形式1reserveのJP更新、記録人物だけの支給、存在しない人物の生成0。reserve混在/ID重複/未知job/不正HP/修練不整合の拒否と候補なし |
| M07 | party/reserveの戦士既得master2人だけ1回習得追加。非master JP120/counts19・他職masterは追加0、装着0。再移行候補なし、能力context欠落・未知能力拒否。現GameSessionによる新候補受理はfalse |
| M08 | 純粋pending→grantedの10個だけ、一回性、再実行3回拒否、入力/進行不変。既存reserveを配列移動した加入fixtureと既存EquipmentRulesの再転職は生成0。進行済み加入docの再支給も拒否。通常解放/ロード/加入ハンドラへの接続はS2で未実装 |
| M10 | 非装備進捗の型・値・順保持、既存型付き配列、HP0、型付きhistory、有限小数、任意記録IDを検査。非装備保存のscalar leaf311箇所を各単独改変して全拒否。未知root/party/reserveキーを削除せず拒否 |
| M11 | 未知版、新キーに版欠落、旧新混在、孤児、重複所有、bag float/null、policy/監査/支援台帳、余分な個体、未知習得、7種stock不正型、新source context、既存不正mode/容量/解放フラグ、JP overflow等を拒否。成否理由とパス、失敗候補なし、元doc/state/metrics/history/jobs/能力context不変 |

新検査は61ケース・2,828条件、failed=0。成功例では決定性と候補/監査の参照分離も確認する。M09/M12/M13のcodec・I/O・通常接続をこの成功に含めない。

## 実行コマンドと証拠

Godotは公式 `4.7.2.stable.official.ed1daf0bf`。公式ZIPのSHA256は `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、展開したLinux実行ファイルは `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`。環境標準の別版は検査に使用していない。PATHの先頭へこの版を置き、XDG_CACHE_HOME/XDG_DATA_HOME/XDG_CONFIG_HOMEを `/tmp/task041/xdg/` 配下へ隔離した。

実装SHAの別checkout `/tmp/task041/after`、抽出前の別checkout `/tmp/task041/before` を使用した。既存検査が書く証拠は別checkoutだけに生成し、今回ディレクトリへ別名コピーした。既存証拠原本は変更していない。

| コマンド | 結果・今回証拠 |
| --- | --- |
| `timeout 600 godot --headless --path /tmp/task041/after --editor --import --quit` | exit0、error/warning0。`import.log` |
| `RPG_EQUIPMENT_SAVE_EXECUTION_SHA=8d3c1848d09b588fa41bcf6345d3aab6e12a5347 RPG_EQUIPMENT_SAVE_OUTPUT=/tmp/task041/evidence/migration.json timeout 120 godot --headless --path . --script res://tools/check_equipment_save_migration.gd` | exit0、61ケース/2,828条件。`migration.json` / `migration.log` |
| `RPG_LEGACY_EQ_OUTPUT=<前後の別出力先> timeout 120 godot --headless --path . --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 両SHAでexit0、検証142/更新10、byte一致。`legacy-before/after.json.gz` とログ |
| `python tools/run_locked_checks.py` | R-01〜R-08全PASS、すべてexit0・実テストあり・parser_failed/timed_outなし。既存各300秒上限。`requirements.json` / `locked.log` / `requirements-logs/*.log.gz` |
| `python tools/check_frozen_files.py` | 前後とも26/26一致。`frozen-before.log` / `frozen-after.log` |
| `python tools/validate_assets.py --strict` | exit0、画像1,154/音15/字体2/パレット3、問題0。`assets.log` |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit0、既存5,394＋93条件、400切替、失敗0。`equipment-core.json` / `equipment.log` |
| `python tools/check_equipment_invalid_definitions.py --source-sha 8d3c1848d09b588fa41bcf6345d3aab6e12a5347 --godot /tmp/task041/bin/godot --output /tmp/task041/evidence/invalid` | exit0、202/202ケース、1,576条件、失敗0。`invalid/results.json` と全202実行ログ |
| `git diff --check` / 担当外差分照合 | whitespace問題0。protected/data/assets/.github/addons/既存検査/既存証拠変更なし、依頼書本文不変、decision-log既存部分不変 |

初回R検査をimport終了前に起動してしまい、R-01〜R-04がUID警告でFAILとなった。成功扱いせず、`locked-premature.json/log` と全8初回ログを保持した。import完了後に検査コード・警告判定・300秒上限を変更せず全8を再実行し、すべてPASSを取得した。

証拠は `docs/verification/equipment-save-migration/`。`execution.json` は実行完全SHA・前後SHA・Godot hash・実装/固定入力/検査器hash、`summary.json` は件数・結果・初回失敗・担当外不変確認、`sha256.json` は全証拠のhash（gzipは展開時hashも併記）を持つ。

## 段階限定・継続条件と残る検証

未接続状態・今回の担当範囲・固定期待とS1の受入は上記完成コードSHAへ固定する。入力不変、型/値/順保持、数量/所有、一回性、旧入口等価性、既存R8と保護は継続条件である。後続で接続する際はS1の固定版検査を残し、新版のcodec/stats/通常保存/戦闘/UI検査を別途追加する。新S1検査はこの専用環境で実行したもので、既存CIへ接続していない。

未実装・未検証は、新版完全codec、保存バイトとhashの照合、新版全保存/stats受理、通常save/loadと復旧I/O、通常解放/加入/転職・戦闘・UIへの接続、実ユーザー保存移行である。正規移行直後/正規共通支給だけを照合する `validate_new` を、進行後の全体validatorとして使わない。実装失敗・範囲内の残件・追加の判断要求はない。

## 変更パス

- 新実装：`scripts/game/equipment_save_migration.gd`、`equipment_save_validation.gd`、`equipment_state_view.gd` と対応uid。
- 許可された最小抽出：`scripts/game/game_session.gd`、`scripts/game/integrated_progression.gd`。
- 新検査・固定入力：`tools/check_equipment_save_migration.gd` とuid、`tools/fixtures/equipment-save/` のbase/expectations JSON、fixtures/legacy_equivalence GDScriptと対応uid。
- 自身の状態/報告：`docs/tasks/041-equipment-save-migration.md` 状態行のみ、`docs/tasks/reports/041-equipment-save-migration.md`、`docs/decision-log.md` 今回判断の追記のみ。
- 新証拠：`docs/verification/equipment-save-migration/`。通常入口接続、データ、素材、原画、契約、保護、既存検査、.github、既存証拠の変更なし。

## CIと最終引渡し

報告・証拠を指定ブランチへcommit/pushした後、その最終SHAの全20CIの終了と成功を確認して最終応答で完全SHA・run・全job結果を返す。自身の最終SHAと自身のCI終了結果を同じcommit本文へ埋め込むことはできないため、ここには固定コードSHAのCI途中記録（`ci-code.json`、確認時19/20成功、残り1実行中）を保存し、文書だけを追加した最終SHAの再確認結果を最終応答へ添付する。mainへ書込み・マージしない。追加委譲、削除、強制pushはしていない。

固定コードSHAのCI途中記録：run `37594412575` は素材・通常検査2/3成功で凍結受入ジョブ実行中、run `37594412593` は17/17終了・成功。途中記録を全CI成功とは扱わない。最終提出では同一最終SHAの3＋17全ジョブ終了と成功を必ず確認する。
