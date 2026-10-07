# 040 装備保存移行の接続計画

## 1. 対象・決定・未実装の境界

読取り対象はmain `0d8393070a6ff968ea95474654a975d4b349d397` と登録 `de4b2c1b8574a255f03bb2b08317a82567bd4dc4`。両者の差は040依頼書のみ。本書は実装計画・検査仕様で、新機能の実装、移行fixture検査、実ユーザー保存の変換は未実施である。

[034](equipment-foundation-plan.md)・[035の036採用追記](equipment-content-options.md#2026-10-07-の採用追記036)・036/038実装・039レビューに接続する。Q1A（鉄の短剣）、Q2A、Q3Aを再決定しない。既存6武器、新8品の仮値、数量、装飾効果、二刀流、戦士マスターによる両手持ちを維持する。034の「候補」「未決」と035の旧見出しは採用追記より前の記録である。

実装時の技術名・担当パス案は本書で決める。既存キー検索で `equipment_migration/equipment_grants/equipment_save` はscripts/data/toolsに存在しなかった。作品名ではない。今回はdecision-logを含む既存文書を変えず、判断と戻し方を本書と040報告だけに置く。

未確定を埋めない事項：両手持ちの実戦係数、正式数値調整、将来の価格・販売・報酬数量は本書の決定対象外。新能力のcatalog登録と戦闘接続はまだない。OSごとのrename・電源断耐久性はUNKNOWNで、後述の検証前に保証しない。旧保存に記録がない型・購入回数・人物・履歴は復元できたと呼ばない。

## 2. 実コードの接続点

行番号は登録SHA。関数名を基準に再検索する。

| パス・入口 | 読み取った事実 | 再利用／必要変更 |
| --- | --- | --- |
| `scripts/game/game_session.gd:116 export_state` / `:381 import_state` | exportはdeep copy。importは全数値の正規化→旧検証→代入、会話・戦闘関連の一時状態を消す | exportは候補採取に利用可能。typed配列と整数値floatを潰すimportを移行コミットに使わない。型付き候補専用の検証済み適用を追加 |
| 同 `:403 _valid_state` | 形式1/2、旧world/actor検証、能力catalog、HP/MP計算、Loadout、進行を照合。party人物を検証するがreserve人物本文は検証しない | 非装備条件は共有。新形式分岐は旧キー必須条件だけ分離し、新全状態検証にはreserveも同じ人物検証を適用 |
| 同 `:1779 save_game(path, record_id="") -> bool` | 戦闘外、userパス、旧_valid_stateが前提。先にflush_recording、state＋metrics＋trialID＋型情報をencodeしtmp→flush→rename。読戻しなし | エンコーダ部を副作用なしで抽出。既存save_gameを原本保管や移行I/Oに直接使用しない。flush失敗が保存前の履歴を変え得るため |
| 同 `:1825 load_game(path) -> bool` | JSON→SavedDocument.decode→型情報分離→位置補正→metrics/ID検査→数値正規化→旧検証→型復元→再検証。最後にarchive close/flush/import/resume | 同じ解読規則を純粋decoderへ抽出。preview・読戻し・復旧判定で通常load_gameを呼ばない。通常ロードで装備移行・追加付与をしない |
| `saved_document.gd encode/decode` | 262144bytes以上、最大33554432bytesまでgzip包みを選択。5キー、decoded/payload hash、gzip長・構造を検証 | 圧縮は保存形式版と独立。backupはこのAPIを通さずPackedByteArrayコピー。新保存はencodeを再利用しdecodeで検査 |
| `saved_value_types.gd describe/restore/same_types` | Arrayのbuiltin型とfloatパスを保存。深い配列から復元。型付き辞書・Object等は未対応 | 削除・移動した装備パスに旧メタデータを再利用しない。型復元済み候補からdescribeし直す。same_typesだけでは値一致にならない |
| `integrated_progression.gd valid_world/valid_actor/upgrade` | armory必須・重複不可、weapons必須・1〜2・二刀流条件。upgradeはpartyのみを対象とし形式1→2、JP比率切捨て、既得マスター最低JP、忘却を生成 | 旧検証は保存。upgradeの人物処理を純粋関数へ抽出しparty/reserveに適用する案。元のparty結果を固定版との比較で証明 |
| `game_session.gd:1918 upgrade_rules` | partyだけ修練初期化、上限再計算、状態代入、rules_upgraded履歴。旧読込みとは独立 | この副作用入口を候補作成で呼ばない。形式更新と装備付与の差分を別の台帳に残す |
| 同 `new_first_region/interact_first_region/finish_first_region_recruit` | party1＋reserve3。加入でdeep copyしてreserveから除去。pc_04不足時はnew_gameから生成する | 保存内の両配列を保持。新規則の加入は同一instance移動。遅延生成に旧全員稽古剣生成器を使わない |
| `scripts/world/first_region.gd:243 valid` | reserveのArray型を検査、世界位置・進行を検査。reserve人物の完全性を保証しない | 旧Valid成功だけで移行可能とはしない。全人物のID一意性と旧人物条件を追加の移行入口で確認 |
| `game_session.gd finish_first_region_audience/job_unlocked/choose_job` | 解放はprogress_flags.job_change_unlocked。first_region外の旧本編はこのフラグなしで基本職に転職可能 | 支給判定は `first_regionあり ? job_change_unlocked : true`。値があるならbool必須。通常解放操作と支給を同一候補で確定 |
| `scripts/combat/battle_catalog.gd _init/_load_document` | catalog.json＋integrated_rules.jsonのabilitiesを結合。equipment_rules.jsonを能力catalogとして読まない | `two_handed`定義を明示登録・検証する後続件が先。装備APIの文字列受理は能力catalogの保証ではない |
| `game_session.gd finish_battle:1127付近` / `job_mastery.gd` | JP達成で既存技を付与後、ready成立でmastered_jobsへ追加。countsとlegacy_mastersを別管理 | 新規則時の戦士マスター確定後に独立報酬を付与。JP閾値だけのapply_rewardの一般技リストへ追加しない |
| `play_session_metrics.gd snapshot/restore` | restoreでint化・Array.assign。events.details内のfloat等も正規化される | 検証用restoreの後に型付きスナップショットの全fieldを戻し、snapshotの型と値を再照合（現load_gameの方式）。previewは実metricsに触れない |
| `playthrough_archive.gd resume/flush` | ID不明・履歴欠落時は新IDを生成しhistory_unavailable、未正常終了はunclean_restartを追記 | 保存の_trial_idと別ファイル履歴は別資源。移行準備でresumeしない。旧履歴をコピー保管し、成功後の通常再開イベントを移行差分と混同しない |
| `scripts/ui/game_root.gd submit_player_action/_load_save/_persist_checkpoint/_load_checkpoint/_retry_battle` | 通常保存、戦闘前保存、失敗試行を残す復帰、旧規則更新を別に扱う | 手動スロットだけでなくcheckpointとロード先選択も新規則対応。メモリ型を潰す復帰importも接続対象 |

確認済み034〜039の再受入やmainマージは今回の工程に含まない。

## 3. 既存装備APIを使う境界

`EquipmentRules`（scripts/game/equipment_rules.gd）の公開APIを変更して都合を合わせない。

| 既存API | 接続契約 |
| --- | --- |
| `definition_errors() -> Array` / `catalog() -> Dictionary` | errors空、14品・20職・catalog_revision=1を確認。欠落定義のcatalog空を成功扱いしない |
| `can_equip(job_id, equipped_abilities, item_id, slot, index=0) -> bool` | 合法化と不足補填の分類判定。slotはweapon/armor/accessory、indexは0起点。職解放や習得の全検証の代わりにしない |
| `validate_equipment_state(state) -> Array` | party＋first_region.reserveの全所有を検査。エラーはtarget/reason_code。旧armory/weaponsの混在拒否 |
| `plan_equipment_change(state, actor_id, request) -> Dictionary` | equip/change_job/set_abilitiesの3種のみ。成功candidate/moves/stats_before/stats_after、失敗candidateなし。移行生成APIではない |
| `equipment_bonuses(state, actor_id) -> Dictionary` | 成功bonusesはhp/mp/attack/defenseのint。主武器のみattack、他装備合算。失敗invalid_state/unknown_actor/numeric_overflowを上位へ伝える |
| `two_handed_active(state, actor_id) -> bool` | 発動条件だけを導出。係数、能力習得、実戦効果は提供しない |

新規則保存の版は形式2＋`equipment_rules_version:int=1`。旧形式1/2に版を勝手に加えない。版なしで新キーあり、未知版、旧新混在、移行記録欠落の新移行保存を拒否する。新worldにはarmoryを置かず、人物integratedにはweaponsを置かない。旧キーの元配列は移行監査の中に値・型・順序ごと退避する。

**旧本編への投影**：現APIはfirst_region.reserve必須だが、旧本編保存へfirst_regionを足すと_game_sessionのモード判定が変わる。新 `EquipmentStateView.project(state) -> Dictionary` はdeep copyした装備検査用のビューだけに `first_region:{reserve:[]}` を補う。実保存にないfirst_regionやmidgame_slots（欠落時の既存既定false）を保存へ追加しない。全状態検証で元の型・欠落可否を先に判定し、存在する不正値を投影で隠さない。計画結果を戻す場合は装備・対象人物の許可パスだけを原状態コピーへ反映し、モード・他のキーを保持する。将来APIをoptional reserveへ改める必要はない。

**移行の合法化**：plan_equipment_change(change_job)を同職で呼ぶと合法な従前装備も最強へ替えるため、移行の「合法従前維持」に使わない。また旧不適合装備を持つ途中候補はvalidateを通らない。移行専用純粋builderが旧枠を退避・合法品を保持し、空欄だけ選ぶ。公開can_equip/catalogを使って固定された比較順（補正降順、同率item_id→instance_id）を実装し、完成候補になってからvalidateを呼ぶ。通常操作の3APIは完成後だけに使う。

## 4. 提案する責任別APIと順序（以下は未実装）

提案ファイルはscripts/game/配下。新APIの成功は `{ok:true,reason_code:"ok",...}`、失敗は `{ok:false,reason_code:String,errors:Array}`、失敗時candidate/documentなし。errorsはパス付きで、未知値を無言で直さない。

| 責任・提案API | 入力→成功結果 | 失敗と副作用 |
| --- | --- | --- |
| `equipment_save_codec.gd decode_source(bytes:PackedByteArray, context:Dictionary)` | raw bytes、jobs/abilities/旧検証・位置検査依存→`document`（型復元済み、補助field含む）、`source_sha256`、`source_format`、`observations` | invalid_json/envelope/types/metrics/record_id/legacy_state/unsupported_version。ファイル・state・archive不変 |
| 同 `encode_candidate(document:Dictionary) -> Dictionary` | describe再生成、SavedDocument.encode→bytes、document_sha256（出力bytesのhash）、型付き比較元 | unsupported_value、serialization_mismatch。圧縮後のdecode比較まで純粋。型付き辞書などをuntypeして通さない |
| `equipment_save_migration.gd plan(document:Dictionary, source_sha256:String, context:Dictionary)` | 検証済み旧doc、固定policy/catalog/完全な能力定義→candidate_document、audit、migration_id | invalid_source/reserve/policy/catalog、unknown_ability、numeric_overflow、unexpected_difference、already_migrated。I/Oなし、入力deep不変 |
| `equipment_save_validation.gd validate_new(document:Dictionary, context:Dictionary) -> Array` | 進行・全人物・能力・上限・型・移行台帳・配布台帳＋EquipmentRules投影→空errors | 新版のみ。旧validatorへ仮weaponsを注入しない。装備投影だけ成功でも全体成功にしない |
| 同 `compare_transition(source, candidate, audit) -> Array` | 第6節の許可パスと固定演算結果のみの差分→空errors | 未列挙の値/型/順序差は全て拒否。自己生成auditをそのまま許可表として信頼しない |
| `equipment_save_transaction.gd inspect(source_path:String) -> Dictionary` | 読取許可済みuserパス→bytes/hash/検証結果・既存取引状態 | path_invalid/read_failed。通常loadを呼ばず書込ゼロ |
| 同 `prepare(source_path:String, expected_sha:String, candidate_document:Dictionary, session_token:String) -> Dictionary` | 第7節の原本backup・履歴保管・新tmp読戻し済み→transaction_token、ready | source_changed/backup_failed/history_failed/write_failed/readback_failed/conflict。メモリは不変。検証済みbackup・作業中ファイルは復旧用に残る |
| 同 `commit(transaction_token:String, session_token:String) -> Dictionary` | source/hash/候補/セッション世代再照合→別スロットrename、receipt | stale_state/source_changed/rename_failed/target_conflict。成功点後の適用失敗はcommitted_not_applied（保存成功を取り消したと偽らない） |
| 同 `recover(transaction_dir:String) -> Dictionary` | 元・backup・tmp・出力を再検証→`prepared/committed/recovery_required`と再開可能操作 | receiptの主張だけで成功にしない。型/値/hash不一致は全自動操作停止、原本を保存 |
| GameSession `preview_equipment_migration(path:String)` / `confirm_equipment_migration(token:String)` | UI説明用差分／明示確定。上の純粋API→I/O→検証済みメモリ適用 | 戦闘・会話・未処理報酬・別保存中をbusy。UI二重押下は同tokenを再照合。通常ロードとは別入口 |

contextは実catalogと検証器の依存を渡す技術引数であり、数量をユーザー指定するAPIではない。policyは `equipment-q1a-q2a-q3a-v1` だけ。文書に指定のない関数名を既存実装として報告しない。

順序：inspect → decode_source → 原状態／metrics／archive世代トークン採取 → plan → validate_new＋compare_transition → preview → 明示確定 → 世代・元hash再確認 → prepare → commit → 新版全検証済みstate/metricsへ一括適用 → 通常の再開・履歴処理。準備中は時計の進行も固定し、準備前に採取した時点を比較点とする。失敗で回復や職変更、履歴イベント追加を起こさない。

未保存の進行があるときは過去のスロットを変換しない。既存保存のbyte保持に加え、明示操作の中で現セッションを別の「移行前チェックポイント」へ旧形式の純粋エンコーダで保存・読戻しする。この成功後のbytesを移行元とする。元スロットも旧チェックポイントも残す。通常save_gameによるarchive flushや型正規化を副作用なしと見なさない。記録中なら先に利用者が通常保存を完了した後、取引を開始する。通常保存の失敗は移行の成功と数えない。

### 4.1 decoderと候補検証の実装手順

1. bytesを保持したままUTF-8 JSONをparseし、Dictionary確認後SavedDocument.decode。元bytesと再UTF-8化が一致しない不正符号列はinvalid_encoding。型metadata・metrics・trialIDの存在有無も記録する。
2. 補助fieldを除いたコピーだけを既存_normalize_numbersで検証用にする。位置検査はコピーだけ。旧の世界・人物条件を検証する。S1で `_valid_state` の人物部分を `validate_legacy_actor(actor, format_version, world_integrated, flags)` 相当へ抽出し、旧party判定をbyte同等の結果で保ちつつ、移行側だけreserveも呼ぶ。reserveをpartyへ置換してleader/進行条件を壊す試験方法は使わない。
3. metricsは別PlaySessionMetricsで検証し、値が存在する場合は旧loadと同じ正規化されたsnapshotを型復元用docへ戻す。metadataがある場合に限りSavedValueTypes.restoreを呼び、全状態・metrics・trialIDを再検証する。metadataが指す欠落キーは拒否。存在しなかった_play_session/_trial_idを永続docへ勝手に追加しない（実セッションで必要な既定metricsは別に生成）。
4. 旧型復元済みdocを入力にplanを呼ぶ。形式更新・装備生成・監査以外の参照はdeep copyで保持する。候補の新型metadataをdescribeし、errorsが空であることを確認する。
5. 新全状態検証は旧world/人物条件から装備所有部分だけを版で分離した同じ共通validatorを使用する。reserveの上限計算には全stateの装備投影を明示引数で渡し、現在GameSession._stateの旧装備を参照しない。新能力catalog検証・修練条件・Loadout・進行・EquipmentRules・audit再計算がすべて成功して初めて完全なcandidateとする。
6. encode後の読戻しでは位置補正・再支給・旧upgradeを禁止した同decoderの新版分岐を使い、Compare.differences相当の値/型/キー/配列順比較とSavedValueTypes.same_typesの双方を要求する。新metadata自体もdescribeし直した期待と一致させる。比較の型なしfallbackで不一致を消さない。

S1のcontextの検証関数は実際の旧条件と新装備条件を呼ぶ。常にtrueのfixture validatorを本番受入証拠にしない。S1で生成した候補の完全な保存可能性はS2の実catalog/codec/new validatorが通るまで未検証と区別する。

## 5. 数量・識別・一回性

### 5.1 付与順序（採用案の固定転記）

1. 旧形式2：武器IDごとにparty＋reserve旧枠出現数N。N>0ならN個、N=0かつarmory解放済みなら袋へ1個。未解放0。同名2枠を1個へ潰さない。
2. 形式1：記録人物P人へ稽古剣各1、袋へ術杖1・稽古弓1、P+2個を「形式1支給」として生成。形式更新の生成weaponsからQ1Aを再実行しない。未記録reserveの推定生成なし。
3. 全人物の不適合品を袋へ退避。合法な従前枠は維持。全人物をID昇順で処理（保存配列順は変えない）し、空の主武器・防具だけ袋の最強合法品を割当てる。既存副武器が合法なら保持。不適合副武器を退避した空きへの無償補填は0。
4. なお主武器が空の人間に分類別入門武器1、防具が空の人間に最大許可rank入門防具1。魔物職は0。理由はmigration_support。通常転職では実行しない。
5. 転職可能なら共通7＋装飾3を袋へ一度だけ付与。未解放ならpending。これは不足補填後に別会計で行うので補填を節約する材料に先取りしない。装飾は自動装着しない。

共通7品は `practice_blade/cloth_fist_wrap/iron_dagger/practice_bow/practice_staff/cotton_travel_clothes/layered_leather_vest` 各1。装飾は `vitality_braid/thought_clasp/guard_stitched_bracelet` 各1。重防具を共通セットへ足さない。人間別入門防具はrank1/2/3をそれぞれcotton_travel_clothes/layered_leather_vest/iron_plate_armorへ対応する。

新規開始の本人用8個はpc_01=稽古剣＋重、pc_02=拳＋軽、pc_03/04=術杖＋軽。party2、reserve6で、共通支給後18。移行ではこの「新規8個」を追加しない。

### 5.2 提案永続キー

`equipment_migration` は `{version:1,migration_id,source_sha256,source_format,policy_id,catalog_revision:1,source_build,legacy_format_audit,equipment_audit}`。source_buildは読めた識別情報だけ（不明は空文字＋不明理由）。historyや状態から捏造しない。auditには元armoryと人物別weapons、元人物の配列位置、旧枠→個体ID対応、補填理由と数量、習得追加を含める。形式更新のJP・忘却差分はlegacy_format_audit、新装備・新能力はequipment_auditへ分離する。

`equipment_grants` は `{version:1,policy_id,common_set:"pending"|"granted",actor_initial:Dictionary,actor_support:Dictionary}`。値は人物ID→当該処理のentry配列（各entryはreason/item_id/instance_id）。emptyと未実行を区別し、魔物職0補填も「処理済み」の記録を残す。共通pending→grantedの変更と10個体追加は同一保存候補。人物初期8個と移行支援を混同しない。未知版・flag/台帳矛盾を新規扱いで再支給しない。

移行元識別は**元ファイルbytesのSHA-256**。同じJSON内容でも空白や圧縮の違いは別原本であると表示し、過去売買を推定して統合しない。migration_idは `SHA256(JSON.stringify(["equipment-migration-v1",source_sha256,policy_id,catalog_revision]))`（配列・UTF-8・固定オプション）。IDは `eqm_<migration_id>_<連番6桁以上>`。連番順は旧人物ID昇順・武器枠順→未装備解放品ID順→形式1支給→人物ID順補填→固定共通品順。分岐ごとに該当しない区分は0件。人物リスト自体は並替えない。生成ID衝突は拒否し、ランダム再生成でごまかさない。

共通遅延支給にも同じmigration_id名前空間と予約済み付与区分を使う。新規開始は一度生成・保存した別のorigin_id、遅延人物生成はorigin_id＋人物ID＋区分を使用。再加入は新規生成ではなく個体移動。同じ元保存の再実行は同migration_idの取引ディレクトリを再利用し、既存確定出力を再検証して返す。新保存をplanへ渡す場合はalready_migrated、生成0・入力不変。同じ旧元から作った出力を別ゲームの所持品に合算する入口は作らない。

## 6. 型・進行の保持と許可差分

比較基準を3つ保持する：A=原bytes、B=旧decoderで復元したdoc、C=新候補。Aの完全保存をB/CのJSON再出力で代用しない。型補助情報のない旧JSONは整数相当floatを既存互換規則でint化する。元々Array[int]だったか等はUNKNOWNであり補造しない。型補助情報ありならBの型・値・配列順を厳密に維持する。

| 領域 | B→Cの許可差分 |
| --- | --- |
| format_version、integrated | 形式1のみ2へ。旧upgradeのworld初期値、人物exp/level/侵蝕端数/忘却/再習得/修練初期値。旧armoryは監査へ移動。その他knowledge/outcomes/claimed/job_notesは不変 |
| party/reserve | 人数・ID・所属・配列順・name・job_id・last_human_job・monster_form・erosion・irreversible・unlocked_jobsは不変。並べ替えて保存しない。reserveもJP/上限/能力/修練を全検査 |
| jp | 形式1のみ `floor(old_jp * modern_cost / legacy_cost)` と既得マスターの最低cost補正。現upgradeと一致する算術を使用し、各職before/afterを列挙。形式2は不変 |
| mastered_jobs、修練 | マスター配列の型・値・順序は不変。未記録修練のみcounts={}、legacy_masters=元mastered_jobsコピー。既存counts/legacyは不変。実行回数を埋めない |
| learned_abilities | 戦士既得マスターにtwo_handedを末尾へ1回追加。既存要素と型・順序は保持。非マスター/JPだけ充足は追加0。equipped_abilitiesは完全不変、自動装着0 |
| integrated.weapons / actor.equipment | 旧枠を監査へ移し、新個体枠を生成。装備の喪失0、不適合の袋返却を全列挙。equipment_stock・上記台帳・版キーを新設 |
| max_hp/max_mp、hp/mp | 共通stats計算を新装備補正対応にして再計算。上限差を監査。現在値はmin(旧現在値,新上限)、増加・蘇生不可。移行時装飾空なら装飾由来の増減0 |
| world/overworld/return_point/expedition/story_task/story_battle/gate_team/leader_id/content_revision/field_battles/inventory/progress_flags/first_regionのreserve以外 | 全キー・型・値・順序不変。移行で進行フラグを立てない。住人・通行・船・帰還・所持金・加入進行も同じ |
| _play_session | 全fields・events・answers・detailsを型/値/順序まで保持。移行監査はequipment_migrationに置き、既存履歴の消去・付け替えなし |
| _trial_id | 存在・非存在と値を保持。32桁hex以外は拒否。移行が新規試行を偽装しない |
| _saved_value_types / gzip | 旧型情報はbackupに残し、新doc全体から再生成。移動したweaponsのtyped配列も監査内で記述。圧縮方式・bytes差は新出力だけ許可、decoded内容の型/値一致必須 |

非装備の未知キーは勝手に削除しない。サポート一覧にないキーはunknown_fieldで移行を停止してパスを提示し、通常旧ロードと元ファイルを維持する。後続で明示対応するまで成功としない。既知の履歴detailsは任意の保存可能値を再帰保持するため、キー追加を捨てるホワイトリストにはしない。

旧位置が現地形で不正な場合、通常loadの自動位置補正を無言で移行差分へ混ぜない。decoderの検査用コピーで既存 `_relocate_saved_position` の補正可否と差分だけ示し、`position_relocation_required` を返す。既存通常操作で位置補正した別チェックポイントを明示保存後、その原bytesから移行し直す。移行元自身は変更しない。

形式1＋reserveの派生入力は、FirstRegion.validのArray検査だけで受理しない。全reserveを旧形式1の人物条件（integratedなし等）で検証し、記録人物だけを同じ純粋upgrade_actorへ通す。混在形式・重複ID・不正reserveは拒否。形式2でworld修練版とreserveの修練有無が矛盾する入力も拒否し、不足人物や修練を黙って補完しない。

## 7. 原バイト保管・原子的出力・復旧

提案保存先は `user://equipment-migrations/<migration_id>/`。sourceはこのディレクトリ外、backupは`source.bin`、新スロットは`converted.json`、準備中は`converted.tmp`。source.binにはFileAccess.get_file_as_bytesで読んだPackedByteArrayをstore_bufferする。decode→encodeしない。source.bin自身もtmp→flush/close→読戻しbyte比較→renameで作る。原sourceと既存backup/確定出力は上書きしない。

ファイル名は入力の人物名・元ファイル名を埋め込まず、検証済みhex IDから生成。userルート内に解決されるパスだけ受理し、`..`・同一ファイル・異なるvolumeへのrenameを拒否。ディレクトリの排他的作成で所有権を得る単一writerとし、存在する場合は新規書込でなくrecoverへ。通常の再保存はconverted.jsonを原本証拠として残すため、別の通常作業スロットへ出す。

取引receipt（提案version=1）はsource hash/サイズ、候補hash/サイズ、policy/catalog、phase、source/target相対パス、trialID、履歴sidecarの有無/hashを含む。phaseの文字列だけで復旧判定しない。各更新はreceipt.tmp→読戻し→rename。UI選択先を先に切り替えない。新出力renameが成功点で、メモリ適用はその後。1ファイルのrenameと複数ファイル/メモリの原子性を混同しない。

| 中断・失敗点 | 保存された可能性のある物 | 再起動後の判定・処理／期待副作用 |
| --- | --- | --- |
| preview取消・source hash変化 | 何もない／取引前チェックポイントだけ | 生成0、元とメモリ・metrics不変。source_changedは新previewが必要 |
| ディレクトリ作成／backup open失敗（権限・容量） | 空dir | backup_failed。新保存なし、旧ロード可能。未完dirは再検証後に再開 |
| backup書込中／flush／close後・読戻し前 | source.tmpが途中または全部 | 元bytesとサイズ/hash/byte比較。欠損はbackupとして使わず再コピー。原本を消さない |
| backup読戻し不一致／backup rename前 | 不完全tmpまたは検証済みtmp | 不一致は停止。検証済みなら原source再確認後にsource.binへrename。既存source.binが異なるならconflictで上書きしない |
| backup確定後／履歴保管前後 | source.bin、場合によりhistory.bin | backupを再利用して二度目の付与なし。必要履歴の保管失敗は新出力前に停止 |
| 新tmp open／store／flush失敗（ENOSPC・権限） | backup＋不完全converted.tmp | write_failed。出力未確定。原bytesから同一候補を再生成し、自分の未完tmpだけ置換可能。他の保存に触れない |
| 新tmp close後／読戻し不正（型・gzip・値・順序） | backup＋tmp | 別decoderでvalidate_newと完全比較。失敗はreadback_failed、メモリ不変。hash一致だけで型の一致を代用しない |
| tmp読戻し成功／rename直前 | backup＋検証済みtmp＋ready receipt | source/hash・session世代を再確認。再起動は自動メモリ反映せず、同取引の再開を通常UIで提示 |
| rename失敗 | tmpまたは出力のどちらか（API戻り値だけに依存しない） | recoverで両方の存在・hashを調べる。出力が期待と一致すればcommitted、それ以外は停止。新規候補を再付与しない |
| rename成功後／receipt更新前 | 正しいconverted.json、古いreceipt | 出力をdecode、全検証・candidate hash・migration_id・backup照合しcommittedへ復元。入力から新規生成しない |
| receipt成功後／メモリ反映前 | 確定出力＋backup | committed_not_applied。旧メモリを維持し、再開UIから確定出力を読む。元sourceに戻す上書きはしない |
| メモリ反映後／選択先保存失敗 | 新メモリ・確定出力、旧選択先 | 成功点を取り消さず、次回取引走査で候補を表示。新ID/数量を生成しない。現在状態と保存先を画面に明示 |
| 同時実行／二重クリック | 1取引dir | 単一所有者以外はbusy。同tokenなら既存結果を返す。再起動で未完dirを新取引と誤認しない |
| backup/出力/receiptの外部改変 | 不一致ファイル | recovery_required、全原本を保持。自動修復・選択先変更・削除をしない。別の旧保存を選べる |

`flush()`は既存Godot APIの使用計画で、電源断時のdirectory fsyncまで実証したという意味ではない。S3で実機相当の別プロセス強制終了、容量不足、アクセス拒否、rename競合を試す。電源断で新出力を失う場合にも原sourceを消さない。OS/FSの保証が不足なら、新出力の消失を検出してbackupから同じ取引として再試行する。原本も同一媒体ごと壊れた場合の回復保証は本計画外で、byte保管の試験と混同しない。

**履歴sidecar**：_trial_idがある場合は、記録ディレクトリと対応する`<id>.json`を実際のarchive設定から解決し、存在すればhistory.binへraw保管する。既存ファイルが破損していればそのbytesも保管し、履歴未確認と明示する。非存在はreceiptにmissingとして記録し、作り話のhistory_complete=trueを出さない。プレビューはarchiveを開き直さない。成功後に通常resumeが新IDを発行する必要がある場合は旧_trial_idを監査・確定出力へ残し、再開後のID/unclean_restart/history_unavailableは別の運用履歴として示す。ID欠落・不正を移行中に隠して新IDへ置換しない。

## 8. 能力・通常接続・公開条件

新能力定義は別 `data/equipment_abilities.json` 案でtwo_handedを登録し、BattleCatalogの検証を通した同じabilities辞書をGameSession、UI、保存検証へ渡す。passiveとして二刀流と同じ必須fieldを持たせ、攻撃コマンドにはしない。報酬対応 `{warrior:[two_handed]}` を装備能力用データに置き、既存 `data/jobs/01_warrior.json` の4技・legacy2技・120JP・physical20回・成長値は不変。

移行器の最初の単体段階では明示的contextへfixture能力定義を渡せるが、それを現在のGameSession._valid_stateの成功や通常保存可能と呼ばない。候補は未接続型としてだけ返す。実GameSessionの新形式受理はcatalog登録、全状態新版検証、stats導出が同時にそろった後。two_handedを「未知でも今回だけ許可」というバリデータ例外は作らない。

新規則の戦士マスター確定時だけ学習し、移行時の既得者も1回。既存習得順・装着順を保持、JPだけ120、成功19、未マスター、他職だけマスターは追加0。legacy_masters保持・counts未記録は0のまま。通常旧load/import/upgrade_rulesは装備習得を発生させない。新形式で習得済みなら重複追加しない。排他は保存検証とset_abilitiesの両方で保証する。

公開前に次をすべて接続し、最終通常操作fixtureを通す。途中段階では通常UIやnew_first_regionを新規則へ切り替えない。

- GameSession save/load/import/export、型保持のcheckpoint複製とretry、battle開始前自動保存、復帰先の別スロット、元保存の選択。新旧版を渡す共通adapterを使用し、キーの存在だけで推測しない。
- _compute_stats/_refresh_caps/effective_stats/preview_job、Combatant生成、主武器差替え、両手持ちと二刀流、装飾HP/MP/防御、上限縮小時だけ現在値切詰め。EquipmentRulesのstats_before/afterは補正値であり最終能力値ではない。
- choose_job/change_job、能力装着・解除、_reconcile_slots、finish_battle強制転職、形態解除、加入・遅延生成。_reconcile_slotsの旧配列切捨てを新規則で使わない。原子的候補を通して袋へ返す。
- new_first_regionの本人8個、finish_first_region_audienceの共通10個、既解放移行の即時支給、未解放移行の遅延支給。支給だけを通常ロードの副作用にしない。
- UIの_integrated_party_controls、戦闘結果のarmory差分表示、_render_party/_job_preview_text、_render_rule_upgrade、通常submit_player_action。装飾の実効果と個数・袋・現在装備・拒否理由を表示し、通常ボタンと自動操作APIは同じ経路を使う。
- 旧buy_first_region_weapon、IntegratedCampaignの貸与報酬とclaimedの読書き。新形式へ単にarmoryを戻すと混在になる。旧貸与の一回解放と新有限入手を混同せず、未採用の販売数量を決めない。未接続のまま公開することも不可。後続発注で該当入手経路の採用済み契約を確認して接続する。

両手持ちの係数・入手経路など他の後続依存が残れば公開は未達と記録する。保存移行の計画や純粋API完成を装備全体完成と言い換えない。名前・配分・Q3A効果の再質問は不要。

## 9. 実装依頼へ分ける最小順序

下表は次の発注単位案であり、今回の実装許可ではない。新検査・fixtureはtools配下案、test/には書かない。各段階の完成SHAを提出時に完全SHAで固定し、後続はそのcheckoutで当時の全assertを再実行する。新CI接続の許可取得までローカル明示実行とし、未接続と報告する。

| 順序 | 担当パス案／前提 | 入口→出口・完了条件 | コマンド案・予算・失敗注入 |
| --- | --- | --- | --- |
| S1 未接続純粋変換 | 新equipment_save_migration.gd、equipment_save_validation.gd、equipment_state_view.gd、tools/check_equipment_save_migration.gd、tools/fixtures/equipment-save/。前提036/038と本計画。旧人物検証とupgrade人物処理の純粋抽出に限りgame_session.gd/integrated_progression.gdを追加 | 型復元済み旧doc＋明示context→候補＋二系統監査。M01〜M08、M10/M11の純粋部分を固定期待で成功。GameSessionの通常操作/UI/save_gameへ新規則を接続しない | `timeout 120 godot --headless --path . --script res://tools/check_equipment_save_migration.gd`。不正reserve、混在、未知能力、重複ID、数量改変、入力mutationを注入。候補を現行保存器へ渡さない |
| S2 codec・catalog・新版全検証 | 新equipment_save_codec.gd、data/equipment_abilities.json、battle_catalog.gd、game_session.gd、integrated_progression.gd、tools/check_equipment_save_codec.gd。S1成功 | raw→型復元doc、候補→bytes→読戻し。旧非装備検証の共通化、全人物版別検証、context付きstatsを同件で接続。新save/loadは内部APIとして試験、通常開始/移行UI未公開 | `timeout 120 godot --headless --path . --script res://tools/check_equipment_save_codec.gd`。M09〜M12、catalog欠落/不正定義、gzip/型情報破損、未知版。旧R全8も実行 |
| S3 保存I/O・復旧 | 新equipment_save_transaction.gd、tools/check_equipment_save_transaction.py、tools/equipment_save_transaction_probe.gd。S2成功 | 専用fixtureディレクトリだけでprepare→commit→recover、M13〜M16。原本hash/bytes不変、全failpoint再起動、成功点前後を区別 | `timeout 180 python tools/check_equipment_save_transaction.py --godot /path/to/godot --fixture-root /tmp/equipment-save-qa`。子プロセス各30秒、failpointごとkill、read/write/flush/rename拒否注入。権限は非rootで実証、容量は専用小容量FSまたは注入＋実書込失敗の両記録 |
| S4 通常runtime準備 | game_session.gd、combatant.gd/battle_state.gd/encounter_effects.gd、game_root.gdの読取りadapter、能力報酬データ、tools/check_equipment_runtime.gd。S2/S3、採用済み戦闘係数・入手契約の接続が前提 | 新生成・全切替・支給・加入・能力報酬・戦闘/装飾効果・checkpointを同じ版へ。通常新規開始の切替はまだしない。M17＋034 E01〜E12の接続条件を満たす | `timeout 240 godot --headless --path . --script res://tools/check_equipment_runtime.gd`。二刀流2n打、両手持ちn打、非対象技不変、HP0維持、解放再判定、遅延人物重複、強制転職。予算不足は分割し各上限を延ばさない |
| S5 通常明示移行と公開 | game_session.gd、game_root.gd、tools/check_equipment_save_ui.gd、tools/check_equipment_save_restart.py。S1〜S4・全既存検査対応・必要な承認済みCI接続が前提 | preview/取消/確定/失敗通知/再開、save_path/checkpoint分離、通常ロードの暗黙移行0。新規開始も完成した支給・効果と一括公開。M18全成功、既存R/全CI/保護一致 | `timeout 180 godot --headless --path . --script res://tools/check_equipment_save_ui.gd` と `timeout 180 python tools/check_equipment_save_restart.py --godot /path/to/godot`（子各30秒）。stale preview、未保存進行、戦闘中、容量不足、rename後再起動、通常UI取消を注入 |

S2でcatalogと新版validator/statsを同件にするのは、未知two_handed入り候補・armory欠落・装飾上限を現バリデータが拒否するため。S3はS2の完全な候補検証なしには安全な読戻しを成功と判定できない。S4/S5の分離は通常公開を遅らせるためで、未完成項目を省いたゲームを完成扱いするためではない。

## 10. 機械受入fixture（計画のみ・未実行）

全fixtureは専用QA userディレクトリ・固定seed・手書き期待値で作り、実ユーザー保存には触れない。各ケースに入力bytes/hash、typed Variant fixture、期待diff、数量・所有表、出力hash、終了codeと全assert数を記録する。全ケース終了0・失敗0・警告/エラー0、期待ケースID集合と件数一致を必須にする。範囲外フィールドを1個変える負例でも必ず失敗することを試す。

| ID | 具体入力・固定期待 |
| --- | --- |
| M01 | 旧形式2 party1/reserve3、初期4職、全員稽古剣、armory3。Q1A=剣4/杖1/弓1の6、補填=拳1/杖1/重1/軽3の6、未解放12。party/reserve順は元どおり。解放済みは共通10を加えて22 |
| M02 | warrior1名がtwin_gripを装着し同じpractice_blade2枠、他人物も同ID。Nを全枠合計とし異なるIDを割当てる。旧枠の順序・二刀流装着不変、副武器補填0。未装備iron_blade解放ありならちょうど1、未解放なら0 |
| M03 | 同職の合法な低攻撃武器と袋の高攻撃武器。移行は低い従前を保持、通常change_jobは高い物へ。合法負値staffを空欄にしない。袋選択同点と他人/reserveの所有除外を手書き表で比較 |
| M04 | 人間→不適合旧武器と魔物職人物を含む。旧個体全数保持、魔物職の武器防具0、袋へ返却。不適合副武器の空き補填0、主武器/防具だけ不足時各1 |
| M05 | 形式1 party3/4、reserveなし：基礎支給P+2=5/6。party4初期職は合法化支援6、共通前12/後22。戦士legacy JPをhalf/threshold/超過で固定し既存upgradeとJP/忘却一致、equipment付与と監査を分離 |
| M06 | 形式1の有効reserveあり派生入力。旧全人物検証を通したP人だけ支給・JP更新。reserve integrated混在、ID重複、未知job、不正HPはinvalid_reserveでcandidateなし。存在しないpc_04を生成しない |
| M07 | partyとreserve双方にwarrior既得master、非master JP120、counts19、他職masterを配置。既得2人だけtwo_handed追加1。JP/counts/legacy/装着順不変。再移行already_migratedで追加0、旧通常ロードでは全員追加0 |
| M08 | pending保存→通常転職解放→granted→再読込み/再解放/加入/再転職。増加は最初の10だけ、各品1。本人初期8・移行支援・遅延生成は別reason、既存reserve加入は生成0 |
| M09 | plainとgzip、型情報あり/なし、Array[int]/Array[String]/Array[float]/Array[Dictionary]/空typed配列、float1.0/1.5/1÷3、ネスト履歴10000件。型ありは全型/値/順序一致、なしは旧正規化結果と一致。元bytesは空白含め完全一致 |
| M10 | 世界・進行・住人・船/帰還・知識/解法/claimed・忘却/relearn/focus_binding・修練・inventory・coins・reserveの型/値を各1箇所改変。許可差分外は失敗。未知root/人物キーはパス付き拒否、削除成功にならない |
| M11 | 未知equipment版、版欠落＋新キー、旧新混在、孤児個体、重複所有、bag float/null、policy/台帳不整合、catalog欠落、numeric_overflow。失敗candidateなし、元state/request/doc完全不変 |
| M12 | gzip5field各破損、型path不在/重複/builtin不正、非有限値、typed辞書、trialID不正、metrics時刻和不正。decoder拒否、I/Oなし。位置不正はrelocation_requiredで差分提示、無断位置変更0 |
| M13 | 第7節の各境界で前/後kill、別プロセスrecover。backupは元とbytes/サイズ/hash一致、確定前は旧メモリ、確定後は同じ出力を再使用、付与増加0 |
| M14 | 各open/write/flush/readback/renameの失敗注入、容量不足と権限拒否。既存target/source.bin衝突、別volume、パス逸脱。同じ元の二重起動はwriter1、上書き0 |
| M15 | 同じrawを別名で再実行→同migration_id/同数量。新保存再実行→already_migrated。同じ内容・異なるraw→別sourceとして明示し、既存新保存へ加算しない。source差替え後のconfirmはsource_changed |
| M16 | trialIDあり/なし、履歴正常/欠落/破損/未正常終了。既存sidecar bytes不変、ある履歴はbackup一致。preview/取消/失敗で新ID・observer event追加0。成功後通常再開の運用履歴を別観測 |
| M17 | Q3A同名別個体1/2/3と異名混在、人間3枠目拒否/魔物3枠、HP0で装着、解除上限切詰め。+HP10/+MP2/+DEF1の仮値を使用、回復・蘇生0、保存/復帰一致。強制職変更・二刀流解除の返却総数不変 |
| M18 | 通常submit_player_actionでpreview→取消/確定、手動保存・新規開始・戦闘前保存・敗北再試行・再起動。未保存進行の別チェックポイントを保持し、古いスロットへ戻らない。旧通常ロードは自動付与0、確定前source/メモリ不変、確定後新スロットのみ選択 |

大きい整数は038の表現域検証を継承する。JSON.parseのfloat化で既に失った十進精度を復元できると主張しない。native intを候補に持つ場合はencode→decodeで差があればserialization_mismatchとして停止し、丸めた成功値を保存しない。新ゲームの上限や勝手なclampを追加しない。

## 11. 既存assert・世代対応・必要な承認

Rの最新実行を固定版成功だけで置き換えない。保護対象26件とR-01〜08をそのまま実行する。下表は読んだ実assertに対する対応案であり、変更許可ではない。

| 実検査・assert | 分類と将来の衝突 | 最新側・追加検査の対応 |
| --- | --- | --- |
| test/unit/test_save_roundtrip.gdの全フィールドdeep一致、破損loadで現在state不変（R-06） | 最新継続。新装備でも緩める理由なし | M09/M10/M13と新形式save/loadにも同じ一致条件 |
| test_job_data.gdの20職、12/8、技catalog参照（R-01） | 最新継続。戦士abilitiesへ報酬を混ぜないため期待変更不要 | catalog別登録のtwo_handed参照・passive検査を追加 |
| test_job_actions.gdのJPのみ不可、盗10/蘇5/獣20、行動進捗往復、旧load不変、explicit upgrade counts=0/legacy保持・二重実行false（R-02） | 最新継続。旧upgrade入口は装備付与と別のまま保持 | M05/M07/M08で戦士新報酬だけ追加、既存assertを削らない |
| test_ability_slots.gdの未習得/上限/重複拒否、装着解除で効果消失（R-03）、test_monster_form.gd（R-04）、test_battle_loop.gd（R-05） | 最新継続。新passiveが汎用「最初の技」fixtureへ紛れないことを実測 | 新装備の排他/職制限/能力条件/多段をM17＋runtime検査へ |
| tools/smoke_first_region.gdのA01〜A14（R-07）、R-08全unit | 最新継続。保護範囲変更なし | 装備公開後も通常到達・保存復帰を同予算で全実行。現物の失敗が出たら具体assertを追加分類し承認前に変更しない |
| check_integrated_storage.gd compare_game、gzip/非圧縮一致、包み5箇所破損時不変、10000events | 最新継続 | 移行自体のraw backup、metrics保全はM09/M12/M16を追加 |
| check_saved_value_types.gdのfloat/typed配列/旧型なし、不正path/builtin/shape/metric_type拒否 | 最新継続 | M09/M12で新equipment/監査の移動パス・新metadataを追加 |
| check_integrated_progression.gd:104〜107 旧import不変→明示形式2→二重更新拒否、95〜99型/値/履歴一致 | 最新継続。通常旧upgradeを装備移行に置き換えない | M05/M07で二つの監査と別入口を証明 |
| check_integrated_ui.gd:33 warriorが旧武器pickerからpractice_bowを装備、旧weapons配列を直接assert | 旧規則では最新継続。新通常開始を切り替える場合だけ「旧完成版固定／新職制限へ置換」が必要 | 旧fixtureは旧モードで全assert保持、新通常UIはwarrior弓拒否・hunter弓許可の正負例。旧assertを単に合法武器へ差替えない |
| check_integrated_combat.gd:86以降のCombatant.weapons2本・負値差替え、多段/反応検査 | 最新継続（戦闘入力としての複数武器）。装備所有検証とは別層 | 新IDからCombatantへのadapterをM17で追加検査、既存二刀流検査を維持 |
| check_save_contract.gd:17 各359状態、:23旧_valid_state、:28キー/型/値/順序、:35metrics、:38〜42領域coverage | 旧保存の最新継続。718状態は減らさない | 新形式は別fixture集合。旧import型保持を改善しても固定旧入力の全assertを継続 |
| check_save_complete.gd:69 Compare.unlisted(before).is_empty、:127〜131全領域coverage / save_state_comparison.gd ROOT_FIELDS/ACTOR_FIELDS | 新キー・equipment・first_regionを未列挙として拒否。旧保存用検査の成功は新版全領域の成功でない | 最小案は版別schemaで新root3キー＋equipment＋reserve再帰＋監査/配布項目を列挙し、旧列挙も維持。変更前の全assertを固定SHAで残し、最新ではM10の未列挙拒否と新coverageを追加。検査変更は別承認 |
| 006/009/012/016等の固定完成版と最新回帰（region2-village-connections.yml） | 旧完成版固定＋通行/住人/保存等の最新継続。現在17job | fixtureが新生成を使う箇所は型/数量の追加観測、固定側のSHAやassertを再定義しない |
| 036完成dbceae8f68e18939a40ace71f3a24a1a1953e653、038完成45a58b7faf09809d916954353a3a1fe0c3d2d035の装備検査 | 旧完成版の範囲監査は固定。5394条件/400切替＋038追加93、202異常定義は最新継続 | 新接続はS1〜S5の別検査で、未接続という当時条件だけを公開時に置換。元assertを消さない |

ci.ymlはpush/PRの3job（preplay35分、godot-import25分、assets）、region2-village-connections.ymlは17job（各15分）。既存import600秒、統合各240秒、型60秒、位置120秒、復帰180秒、R各300秒を維持する。legacy-campaign.ymlはworkflow_dispatchのみで、旧保存契約300秒、全変数通し各600秒等を持つ。push20job成功を手動旧本編workflow成功と呼ばない。

新検査CI接続の最小案は、S1/S2純粋検査、S3復旧、S4/S5通常接続を独立jobへ追加し、各15分以内・個別上限は第9節のまま、全ケース実行・警告拒否・artifact保存・if:alwaysの保護照合を要求すること。既存20jobを削除・skip・continue-on-error・予算延長しない。各実装完成SHAの固定checkout実行も残し、latest動作は最新本番で別実行する。workflow変更は今回も次件も自動的には許可されない。

今回変更しないが将来承認が必要な操作は、(1)上記既存保存領域検査の版別拡張および衝突が実測された既存UI検査の世代分離、(2)新検査のworkflow接続、(3)万一R/test/.scope-lock等の保護変更が必要になった場合の具体差分。現時点でR契約の弱化・凍結hash更新を前提にしない。承認前でも未接続の純粋変換と専用fixtureの準備は依存順に発注できる。

## 12. 技術判断と戻し方

- 2026-10-07：原bytes hashを移行元とし、別スロットrenameを成功点にする。理由は原本再保存の変質とメモリ先行適用を避けるため。未公開段階なら新モジュールと呼出しをGitで戻せる。既に生成した保存を削除する方法では戻さない。
- 同日：装備投影にだけ空reserveを補い、保存にはfirst_regionを捏造しない。理由はAPIの実引数と旧本編モード判定の両立。adapterを差し替えても保存の進行構造は変わらない。
- 同日：新能力catalog/新版全検証/statsをS2で同時成立させる。理由は未登録能力入り候補を旧validatorへ通す矛盾の排除。公開フラグ解除前なら純粋候補段階へ戻せる。
- 同日：位置補正、型なし旧JSON正規化、形式1のJP更新、装備数量/新習得、archive運用イベントを別の差分として扱う。理由は何を保持し何を変えたか検証可能にするため。旧原本は全ての比較の起点として残る。
