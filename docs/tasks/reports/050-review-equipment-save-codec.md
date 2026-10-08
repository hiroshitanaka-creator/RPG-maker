# 050 保存codec・新版全状態検証の独立レビュー

## 判定

**差し戻し。P2を5件（F1〜F5）。** 049提出の実CI成功、原112ケースの成功と、独自反例で判明した未達を区別する。本番・原検査・workflowを修正して通していない。S3以降の未実装をS2の欠陥として数えていない。

## 対象・開始状態・環境

- 049提出：`a09809d56658686ea7bc200ee4014112e64cff3c`。完成コード：`99e9d03d4e095b4627b510efd4806f82276617c9`。
- 049範囲監査基点：`5f5aab4fbe48e77f7e217b71672a043be2839d34`。
- 050登録／開始：`138e45ec3e234c75300a12cd15536e957f92a42d`。branch：`codex/task-050-review-equipment-save-codec`。
- MSIの既存 `2026-10-04/task/repo`（main `4f5568e`）と `task-3/repo`（main `5f1c2ba`）は未commit差分0、各追跡refに対するahead0。前者004 branchはbehind2。OneDrive側game開発はcommitのないmaster。既存checkoutにfetch・checkout・書込みをしていない。追跡refの観測と最新remoteとの照合は同一視しない。
- 新規の `D:/codex/Documents-Codex/2026-10-08/task/review050` に指定branchをcloneし、remote登録SHAと一致、開始未commit／未push0。別clone `qa050` を登録SHAへdetachして検査を実行した。
- Godot Windows実体：`4.7.2.stable.official.ed1daf0bf`。QA専用配置 `qa-bin/godot.exe` のSHA256は `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`。Linux CI実体hashとは別である。
- APPDATA／LOCALAPPDATA／USERPROFILE／HOME／XDG各変数を子プロセスだけ `task/qa-profile/` 配下へ指定。実Godotの `OS.get_user_data_dir()` は `task/qa-profile/APPDATA/Godot/app_userdata/RPG-maker` と確認。ユーザー保存の読取り・変換、既存アプリ停止、グローバル設定変更なし。
- 初回sandboxのgh認証は失敗したが、MSIホスト接続ではGitHub認証・取得が成功した。初回importは元エンジンのself-contained設定保存先への書込みがsandboxで拒否され、ERRORを記録した。これを成功に数えず、実体もQA専用配置へコピーして再importし、exit0・警告／エラー0を確認した。console wrapper単体のコピーによる起動失敗も成功に数えない。

AGENTS、050／049、040計画、041／042、043〜046の依頼・報告、049変更・固定期待・原証拠、素材規約・職業魔物化企画と台帳の関連箇所を確認。checkoutに `.agents/skills` はない。catalogの [verification-before-completion](skill://plugins~Plugin_60aea7460bd4819199fd97a9553a5e12/verification-before-completion/SKILL.md) を使用。追加委譲・モデル設定変更・親の監督や依頼書作成の代行なし。

## 指摘と最小修正範囲

### F1 / P2：最新CIが後続レビュー文書だけで失敗する

対象：`tools/fixtures/equipment-save-codec/run_ci.py:150–156`、`.github/workflows/equipment-codec.yml` のlatest呼出し。

`BASE→source_sha` の049担当範囲をprofileに関係なく監査し、050依頼書追加を拒否する。049提出→050登録の全tree差は依頼書1件だけ。登録CI [run 37707589198 / job 113085549365](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37707589198/job/113085549365) の実原ログは `CODEC_CI_FAIL: 担当外差分:A docs/tasks/050-review-equipment-save-codec.md`、exit1。固定049 jobは成功。

原artifactも取得した。登録latestはversion・保護前・import・原codec・保護後の5コマンドすべてexit0、112ケース／723条件も成功。しかしscope監査で止まり、伝播13件は未実行、最終sha256.jsonも生成されない。execution.statusはFAILで、失敗時uploadと保護照合は実行されている。

期待：049当時の担当範囲は固定049で全条件維持し、latestは後続の承認文書が増えても継続動作を検査する。実際：文書だけで最新回帰と失敗伝播の完走を阻害する。

再現：登録SHAで原wrapperへ `--profile latest --source-sha 138e45ec3e234c75300a12cd15536e957f92a42d --godot <Linux公式4.7.2> --output <新規絶対パス>`。Linux hash固定のためWindowsで原main全体を通したとは報告しない。MSIでは全tree差と原CI artifact／原ログを照合した。

最小案：scope判定を当時の完成SHAに固定した監査へ分離し、latestの原動作／件数／警告／証拠検査は残す。050だけallowlistへ追加する場当たり対応や固定条件の削除はしない。修正対象は049の新wrapperと必要な新専用fixture／workflow対応表に限定できる。今回は変更しない。

### F2 / P2：prepare_candidateが壊れた型metadataを消して成功にする

対象：`scripts/game/equipment_document_validation.gd:247–272`、特に268–270。

正規region移行候補に型付きmetricsを加え、`F.typed` でmetadataを作る。そのmetadataをnull、version99、存在しないfloat path、重複path、TYPE_OBJECT配列、未知キー、float path欠落の7通りに壊した。付録の `metadata` で再現。

期待：型metadata不正をパス付きで拒否し、documentなし。実際：直接encodeは全7件 `invalid_types`、prepareは全7件 `ok=true/documentあり/errors=[]/caps_changes=[]`。元入力は不変だが、返すコピーから破損情報を消して再記述する。後段encodeの厳密拒否をprepare経由で迂回できる。独自検査23条件のうち7拒否期待が失敗、exit1。

最小案：変更前候補について既存metadataの構造とnative値のdescribeとの整合を検証し、不正なら返す。合法な上限変更後の再生成は維持する。S1は型復元済み入力の契約であり、S1原検査／変換を変える必要はない。S2 validatorと049専用負例に限定する。

### F3 / P2：不正catalog contextでスクリプトエラー後に成功を返す

対象：`scripts/game/equipment_document_validation.gd:10–16`、特に14。

実GameSessionから正常abilitiesを採取後、その専用fixture sessionの `catalog=null` とし、正常documentをencodeへ渡す。`context` で再現。既存ユーザーsessionは操作しない。

期待：`invalid_context` または `invalid_catalog`、パス付きerrors、成功document／bytesなし、SCRIPT ERRORなし。実際：`Nonexistent function 'equipment_context_abilities' in base 'Nil'` が4回出るが、最後は `ok=true/documentあり/errors=[]`。型付きArray戻り値のエラーを拒否根拠として保証できず、呼出し側が空errorsとして進む。missing-session／missing-abilities／catalog-errorsの対照3件は拒否した。

最小案：catalog参照が有効なBattleCatalogか、初期化・定義エラーがないかを呼出し前に検査し、必ず明示エラーを返す。S2 context_errorsと専用負例に限定し、旧通常入口・旧catalog定義を変更しない。

### F4 / P2：decodeの形状検査前の位置検査が不正入力で実行時エラーを出す

対象：`scripts/game/equipment_save_codec.gd:107–117`、特に108。到達先は既存 `first_region.gd:87/207`。

固定 `F.region()` のoverworldを `room=1, cell=[1,1]` とし、(a) `party=null`、(b) `overworld.residents=null` をJSON化してdecodeする。付録 `relocation` で再現。

期待：先に不正形状を拒否し、SCRIPT ERRORなし。実際：(a) joinedでNilを反復、(b) event_cellでNil.getを呼ぶエラーが発生。その後 `invalid_state/invalid_shape` とdocumentなしを返す。プロセスはexit0・ローカルassert失敗0でも、SCRIPT ERRORがあるため**検証失敗**と判定した。安全な失敗契約を満たさない。合法な位置補正対象を示す原M10ケースの成功と混同しない。

最小案：codec入口で位置検査が参照する構造を事前確認する。通常ロードの位置処理、保護された位置検査、FirstRegionの既存挙動を変更せず、新codec側の順序／形状guardと専用負例で修正する。

### F5 / P2：証拠validatorが条件数の同時偽装と空の成功documentを受理する

対象：`tools/fixtures/equipment-save-codec/run_ci.py:57–58,69`。

実再実行の正常出力を別コピーし、(a) codec.jsonのchecksを723→1、logのPASS行も723条件→1条件、(b) `M09-new-typed/document.gdv` を0byteへ変更。原 `--validate-only` は正常対照・両反例ともexit0／`CODEC_EVIDENCE_PASS`。元13伝播のmissing-documentはファイル不在だけを検査し、pass-countはlogだけを変えるため、この反例を検出しない。

期待：固定112／723の原条件と、成功document実物の完全性を検証し、破損記録を拒否する。実際：checksは正整数かつlogと相互一致だけ、documentは存在のみ。空documentでも成功となり、後で作るmanifestはその壊れたbyteを追認し得る。

現在の原検査が省略された、または取得したCI artifactが改ざんされていたという指摘ではない。今回取得原本は112／723、document14件も保存原本に一致した。将来のproducer回帰／欠損記録に対する検証契約の不足を指摘する。

最小案：完成固定期待の条件数と照合し、成功documentの観測hash／サイズと実物を照合する。原Godot側で出力した完全なdocument・encode/decode比較を保証した上で、その証拠の欠損をwrapperが拒否する。両同時改変と空／改変documentの負例を新fixtureへ追加する。旧043〜046 wrapperや旧原検査を変更しない。

## S2で確認した挙動と将来境界

- 原112ケースは全ID／順／成否／errors／caps_changesが完成原本と一致。raw UTF-8、重複JSONキー、5field包み、未知版／キー、typed配列／空／float／大整数、10000履歴、trialID／metrics、party／reserve、所有／袋、修練／能力／上限、監査／支給を原固定期待で再実行した。
- 独自progressは所持品・所持金・reserveのJP／成功回数を進め、reserve HP0をpartyへ加入移動してencode→decode。全値／型／配列順、人数／所有、HP0、原state／metrics／history不変が成功。移行直後比較は同じ進行後docを拒否し、一般検証と責任が分離されている。
- 正規共通支給12→22個もS1 pure関数→S2 prepare→encodeで成功。audit.generatedと現在instancesの全一致はこの支給・加入・進行を誤拒否しなかった。任意の `future_example` 個体を袋へ足すとinvalid_audit。未採用の将来売買／報酬をS2受入に捏造せず、ここは後続入手経路・台帳契約の明示接続が必要な引継ぎとする。無条件に完全一致検査を外す提案はしない。
- two_handedは実catalogの内部合成辞書で受理、通常abilities／報酬へ未接続。原ケースでマスター条件・未習得拒否・旧通常入口拒否を維持。独自catalog35入力は不正34拒否、合法なString description対照1受理、警告なし。倍率や新ゲーム規則を追加決定していない。
- M10上限上下・HP0・回復／蘇生0、明示documentによるreserve stats、S1移行差分の原条件は成功。F2はこの通常成功と別の不正metadata経路である。

## 実行結果・原証拠照合

コマンドはQA cloneをcwdとし、Godotは上記Windows版。PythonはMSI既存runtime。全生出力はtask/evidence050に保存した。提出可能パス制限に従い、永続レビュー成果は本報告の再現コード・結果・hashと050状態行だけ。

| 実行 | 個別上限 | 結果 |
| --- | --- | --- |
| `godot --headless --editor --import --quit`（隔離再実行） | 600秒 | exit0、5.297秒、警告／エラー0 |
| `godot --headless --path . --script res://tools/check_equipment_save_codec.gd` | 120秒 | exit0、13.344秒、112ケース／723条件、失敗0 |
| 原wrapper `validate`／`self_test` を未変更でロードして実出力へ適用 | 各子30秒 | 13件＝正常control exit0＋異常12件実exit1。初回子にUTF8設定が継承されずcp932エラー、別新規出力でPYTHONUTF8=1を子へ継承後に全件成功 |
| `godot --headless --path . --script res://tools/check_equipment_rules.gd` | 240秒 | exit0、0.829秒、5394＋93条件／400切替 |
| `godot --headless --path . --script res://tools/check_equipment_save_migration.gd` | 120秒 | exit0、26.500秒、61ケース／2828条件 |
| `RPG_LEGACY_EQ_OUTPUT=<専用出力> godot --headless --path . --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 120秒 | exit0、2.265秒、142検証／10更新。旧before原本と全byte一致 |
| `python tools/run_locked_checks.py` | 各verify300秒 | exit0、R全8 PASS、tests_ran=true／parser_failed=false／timeoutなし |
| `python tools/check_frozen_files.py` | 30秒 | 前後exit0、26／26一致 |
| `python tools/validate_assets.py --strict` | 120秒 | exit0、画像1154／音15／palette3／font2、問題0 |
| 独自GDScript metadata／context／relocation | 各120秒 | F2／F3／F4再現。実行時エラーを成功条件に加算しない |
| 独自GDScript progress／shape／catalog | 各120秒 | 9／17／36条件、各exit0、警告／エラー0 |
| 独自wrapper破損証拠3件 | 各30秒 | 対照exit0、拒否期待2件もexit0（F5） |

独自検査初稿では辞書の挿入順までnative bytesで同一視していたためprogress比較が失敗した。辞書キー順は契約外なので、値型・キー集合・配列順を再帰比較する独立sameへ訂正した。また空progress_flags／空residents、String descriptionは合法対照へ訂正。変更は独自probeのみ。原実装・原検査の修正ではなく、初稿失敗を製品不具合に数えていない。

完成archive1960 file member、初回archive1848 file memberは `archive-members-sha256.json` の集合と全hashが一致。Windows再実行と完成Linux原本はinput112件中105件、document14件すべて、encoded6件中5件がbyte一致。残るgzip符号化は圧縮payload長が両方30924、差分はoffset9のOS識別byteだけ。展開内容SHA256は両方 `2e0f2193e591772e2c485816b0783a71c6d430e1f95ca127a7bd4c4b6f92ae01`。gzipから派生した包み負例等の7入力hash差もこのOS byteと包みhashによるもので、別OSのencoded byte完全一致とは主張しない。原raw入力保持・同一環境のencode/decode全内容比較は成功している。

旧142／10の出力SHA256：`bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。今回codec.json：`8b08c4d5d8380a5add6f827d7b091773b42834e653f1b1cc2572930913fc40f7`。

## Git範囲・CI

049基点→提出の全53パスは新codec／validator／専用fixture・workflow・証拠・許可3既存コード・data追加・049文書・decision-log末尾のみ。削除なし。decision-log旧本文prefix一致。完成コード99e9d03→提出a09809dのscripts／tools／dataは差分0。提出→050登録は050依頼書だけ。今回提出はその状態行と本報告のみ。

test／.scope-lock／assets（原画含む）／addons、既存4workflow、旧装備・異常定義・S1原検査とfixture、旧CI wrapper、SavedDocument／SavedValueTypes、S1 migration／validation／viewは基点から全blob不変。旧本番3ファイルの変更は非装備共通検証／明示stats／内部catalogの接続に限られ、通常save/load／通常報酬／戦闘処理を新形式へ接続していない。既存予算・保護26／旧142・10の原期待全文を維持。

049最終提出同一SHAのpush36＋PR36をGitHub jobs APIで独立照合し、**72／72 completed/success**。同じSHAで後から050 branchを作成した別push runは、この72件の集計に混ぜない。

| workflow | 049 push run／件数 | 049 PR run／件数 |
| --- | --- | --- |
| CI | [37705305923](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705305923)／3 | [37705309334](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705309334)／3 |
| 006固定／最新 | [37705305919](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705305919)／17 | [37705309414](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705309414)／17 |
| Equipment and Save | [37705305911](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705305911)／14 | [37705309349](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705309349)／14 |
| Equipment Codec | [37705306058](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705306058)／2 | [37705309393](https://github.com/hiroshitanaka-creator/RPG-maker/actions/runs/37705309393)／2 |

049 push codecのfixed049／latestと050登録codecのfixed049／latest、計4artifactを取得。各source SHA、原5コマンド・予算・exit・log hash、112／723全結果が保存原本と一致。成功3artifactは各139 manifest hashと伝播13件の全実exit一致。登録latestは原5コマンド正常だがscopeでFAIL、伝播0・最終manifestなし。固定と最新、原検査成功とwrapper失敗を別々に記録した。

新workflowはcontents:read、各job15分、import600秒／codec120秒、fail-fast:false、失敗時保護・artifact保存を確認。050文書追加後もF1を直して通さない。今回の最終commit SHA・push後全CIの終了結果は、自己参照による再commitを避け最終応答に記載する。全CI成功やS2受入済みとは記さない。

## 未達・未検証

S2未達はF1〜F5。修正とその独立再検証が必要。S3保存I/O取引・復旧、S4通常runtime／報酬／戦闘接続、S5UI／公開、未採用入手経路と実戦係数、実ユーザー保存／電源断、手動旧本編workflowは範囲外・未実行。Windows上でLinux hash固定wrapperのmain全体を実行したとは扱わない。Linux固定／latestの実物確認はGitHub CI artifact、ローカルは同版Windowsの原GDScriptと未変更証拠validator／伝播13件。旧異常定義202ケースのローカル再実行はしておらず、同一049 SHAのCI成功を確認した。

## 再現付録

以下は隔離QA cloneだけへ保存する。`independent050.gd` をrepo rootへ置き、各modeを `godot --headless --path . --script res://independent050.gd -- MODE` で120秒以内に実行。APPDATAなどは専用ディレクトリへ向け、先に同じGodotでimportする。戻りexitだけで合格させず、logに `SCRIPT ERROR|ERROR:|WARNING:|Parse Error` があれば失敗とする。期待値は今回手書きで、元入力は原固定fixtureからの明示派生である。

```gdscript
extends SceneTree
const F=preload("res://tools/fixtures/equipment-save-codec/fixtures.gd")
const M=preload("res://scripts/game/equipment_save_migration.gd")
const V=preload("res://scripts/game/equipment_document_validation.gd")
const C=preload("res://scripts/game/equipment_save_codec.gd")
var s=GameSession.new()
var ctx:Dictionary
var checks=0
var failures=[]
func ck(ok:bool,label:String):
	checks+=1
	if not ok:failures.append(label)
func same(a:Variant,b:Variant)->bool:
	if typeof(a)!=typeof(b):return false
	if a is Dictionary:
		if a.size()!=b.size() or a.is_typed()!=b.is_typed():return false
		for key in a:
			if not b.has(key) or not same(a[key],b[key]):return false
		return true
	if a is Array:
		if a.size()!=b.size() or a.get_typed_builtin()!=b.get_typed_builtin():return false
		for i in range(a.size()):
			if not same(a[i],b[i]):return false
		return true
	return a==b
func emit(label:String,r:Dictionary):
	print("OBS ",label," ",JSON.stringify({"ok":r.get("ok"),"reason":r.get("reason_code"),"errors":r.get("errors"),"document":r.has("document"),"caps":r.get("caps_changes",[])}))
func base(region=true):
	var p=M.new().plan(F.region() if region else F.base(),"a".repeat(64),ctx)
	return V.prepare_candidate(p.candidate_document,ctx).document
func metadata():
	var d=base();d["_play_session"]=F.metrics();d=F.typed(d)
	ck(C.encode_candidate(d,ctx).ok,"valid metadata control")
	for kind in ["null","version","missing","duplicate","builtin","unknown","mismatch"]:
		var b=d.duplicate(true)
		match kind:
			"null":b._saved_value_types=null
			"version":b._saved_value_types.version=99
			"missing":b._saved_value_types.floats.append(["missing"])
			"duplicate":b._saved_value_types.floats.append(b._saved_value_types.floats[0].duplicate())
			"builtin":b._saved_value_types.arrays[0].builtin=TYPE_OBJECT
			"unknown":b._saved_value_types["extra"]=1
			"mismatch":b._saved_value_types.floats=[]
		var before=var_to_bytes(b)
		var enc=C.encode_candidate(b,ctx);emit("encode-"+kind,enc)
		var prep=V.prepare_candidate(b,ctx);emit("prepare-"+kind,prep)
		ck(not enc.ok,"encode rejects "+kind)
		ck(not prep.ok and not prep.has("document"),"prepare rejects "+kind)
		ck(var_to_bytes(b)==before,"metadata input unchanged "+kind)
func progress():
	var d=base()
	var before=var_to_bytes(d)
	var p=d.duplicate(true)
	p.inventory.potion+=1;p.first_region.coins+=1
	p.first_region.reserve[0].jp["warrior"]=3
	p.first_region.reserve[0].integrated.mastery.counts["warrior"]=1
	p.first_region.reserve[0].hp=0
	p.party.append(p.first_region.reserve.pop_front())
	p=F.typed(p)
	var r=C.encode_candidate(p,ctx);emit("progress-and-recruit",r)
	ck(r.ok,"legal progress and reserve recruit")
	ck(not V.compare_migration(F.region(),p,"a".repeat(64),ctx).is_empty(),"migration diff separately rejects progress")
	ck(var_to_bytes(d)==before,"original unchanged")
	if r.ok:
		var q=C.decode_source(r.bytes,ctx)
		ck(q.ok and same(q.document,r.document),"all values types order roundtrip")
		ck(q.document.party[1].hp==0,"reserve death no revive")
	var g=d.duplicate(true);g.progress_flags["job_change_unlocked"]=true
	var gc=ctx.duplicate();gc["job_change_unlocked"]=true
	var grant=M.new().grant_common(g,F.region(),"a".repeat(64),gc)
	ck(grant.ok,"pure common grant")
	if grant.ok:
		var prepared=V.prepare_candidate(grant.candidate_document,ctx)
		emit("common-grant",prepared)
		ck(prepared.ok and prepared.document.equipment_stock.instances.size()==22,"common grant 12 to22")
		var raw=C.encode_candidate(prepared.document,ctx)
		ck(raw.ok,"common grant encodes")
	var future=d.duplicate(true)
	future.equipment_stock.instances["future_example"]="practice_blade"
	future.equipment_stock.bag.append("future_example")
	emit("future-acquisition-outside-S2",C.encode_candidate(future,ctx))
func shape():
	for key in ["party","progress_flags","inventory","residents"]:
		for value in [null,1,[],{}]:
			var d=F.region()
			if key=="residents":d.overworld["residents"]=value
			else:d[key]=value
			var raw=JSON.stringify(d).to_utf8_buffer()
			print("BEGIN shape ",key," ",JSON.stringify(value))
			var r=C.decode_source(raw,ctx);emit(key,r)
			var valid_control=value is Dictionary and value.is_empty() and key in ["progress_flags","residents"]
			ck(r.get("ok",false) if valid_control else (not r.get("ok",false) and not r.has("document") and not r.get("errors",[]).is_empty()),"shape outcome "+key+str(value))
			print("END shape ",key)
func catalog():
	var data=JSON.parse_string(FileAccess.get_file_as_string("res://data/equipment_abilities.json"))
	for key in ["id","kind","target","cost","power","hits","description"]:
		for value in [null,[],{},true,"wrong"]:
			var c=BattleCatalog.new();var bad=data.duplicate(true);bad.abilities[0][key]=value
			print("BEGIN catalog ",key," ",JSON.stringify(value))
			c._load_equipment_document(bad)
			ck(c.equipment_errors.is_empty() if key=="description" and value is String else (not c.equipment_errors.is_empty() and c.equipment_context_abilities().is_empty()),"catalog outcome "+key+str(value))
			print("END catalog ",key)
func relocation():
	for key in ["party","residents"]:
		var d=F.region();d.overworld.room=1;d.overworld.cell=[1,1]
		if key=="party":d.party=null
		else:d.overworld["residents"]=null
		print("BEGIN relocation ",key)
		var r=C.decode_source(JSON.stringify(d).to_utf8_buffer(),ctx);emit("relocation-"+key,r)
		ck(not r.get("ok",false) and not r.has("document"),"relocation malformed refuses "+key)
		print("END relocation ",key)
func context():
	var d=base()
	for mode in ["missing-session","missing-abilities","null-catalog","catalog-errors"]:
		var ns=GameSession.new();ns.new_game()
		var c={"legacy_session":ns,"abilities":ns.catalog.equipment_context_abilities()}
		match mode:
			"missing-session":c.erase("legacy_session")
			"missing-abilities":c.erase("abilities")
			"null-catalog":ns.catalog=null
			"catalog-errors":ns.catalog.equipment_errors.append("fixture invalid")
		print("BEGIN context ",mode)
		var r=C.encode_candidate(d,c);emit(mode,r)
		ck(not r.get("ok",false) and not r.has("document"),"context rejects "+mode)
		print("END context ",mode)
func _initialize():
	print("QA_USER_DIR ",OS.get_user_data_dir())
	s.new_game();ctx={"legacy_session":s,"abilities":s.catalog.equipment_context_abilities()}
	var before=var_to_bytes(s.export_state());var metrics=var_to_bytes(s.play_metrics.snapshot())
	var mode=OS.get_cmdline_user_args()[0]
	call(mode)
	ck(before==var_to_bytes(s.export_state()) and metrics==var_to_bytes(s.play_metrics.snapshot()),"live state metrics history unchanged")
	print("REVIEW050 ",JSON.stringify({"mode":mode,"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
```


### F5再現（未変更wrapperを別Pythonで実行）

```python
import os, sys, json, shutil, subprocess
from pathlib import Path
os.environ["PYTHONUTF8"]="1"
repo=Path.cwd()
# CODEC_ORIGINALは原検査が生成したcodec.json/codec.logと各ケース実物を持つ新規出力。
original=Path(os.environ["CODEC_ORIGINAL"])
destination=Path(os.environ["REVIEW050_PROBES"])
for name in ["control","checks-one","document-empty"]:
    p=destination/name
    shutil.copytree(original,p)  # 既存先があれば停止。原証拠は不変。
    if name=="checks-one":
        d=json.loads((p/"codec.json").read_bytes());d["checks"]=1
        (p/"codec.json").write_text(json.dumps(d,ensure_ascii=False),encoding="utf8")
        log=(p/"codec.log").read_text(encoding="utf8").replace("723条件","1条件")
        (p/"codec.log").write_text(log,encoding="utf8")
    if name=="document-empty":(p/"M09-new-typed/document.gdv").write_bytes(b"")
    child=subprocess.run([sys.executable,str(repo/"tools/fixtures/equipment-save-codec/run_ci.py"),
        "--validate-only","--checkout",str(repo),"--output",str(p)],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    (p/"validation.log").write_bytes(child.stdout)
    print(name,child.returncode,child.stdout.decode("utf8"))
```

### 今回原ログ・再現コードのSHA256

| ファイル | SHA256 |
| --- | --- |
| independent050.gd | `5c72d5f30cc6a9e405d40d7a6cc4ec4d070be82b550ae5dbe4131d7a5ef51139` |
| codec.log | `870dcd5e5a5cea72b4e13f6d21bbaf5160df048c12d140f3230cbefeacee75ef` |
| locked.log | `ef664316fb8253345d8e459b8b9ee0ba745ebc3766ca3004c93e3fd914966076` |
| legacy-latest.json | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| propagation.json | `e35bf88517a059040fa6130e3e877606896ffc7b0f508ad3d47132c9506268c6` |
| audit.json | `aea6fc09e76ce56ac042fffda807d5fa14433fee21f2987111ea46ae55835338` |
| ci-artifact-check.json | `47f14ad57d3a6c003cc9666cb6117883f80181872080549babff78244eae2ebc` |
| wrapper-final.log | `46aab7fa638ac5b649e67ed9c902cd1123cf65ad23817ac4a51420bd9e3474c4` |
| final-metadata.log | `c2d7ca3f0e06c6641ba7fd056af5f15516aec23d2b7f2792ff3e059286ba2f0b` |
| final-progress.log | `b6f169f457631518a17751853fbe8267efa59e357bb6ec2fb66389ab0d68ad8c` |
| final-shape.log | `db632ea633b5239d1c49d3ac2852b6c2230b5a3a2fb3889e8e6fd28bd2f4e9ee` |
| final-catalog.log | `7a4bcc1045486a9d6d17ffe050e5a0f095a6f8d9cc7ba729120bf872173f0099` |
| final-context.log | `4180cb5ad7a06c5cb8229d169c66c6338803525804967e379774a87d38e83bf9` |
| final-relocation.log | `258d2e66a42bb1d9d8a13290118eddffa5d3ac88303d0ab9afe8b624abc36e65` |
