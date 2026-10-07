# 042 装備保存の純粋変換・独立レビュー報告

## 判定と対象

**PASS（S1の範囲）**。再現したP0/P1/P2の指摘なし。041の報告を実コード・固定期待・保存証拠と照合し、専用検査を独立再実行した。通常保存全体・実ユーザー保存への接続成功は意味しない。追加委譲、本番修正、main書込み・マージなし。

- レビュー対象：`9e1c48eeb0fb626c7a86cb56414ac61fbc85d7e6`
- 実行コード：`8d3c1848d09b588fa41bcf6345d3aab6e12a5347`
- 全tree比較基点／旧処理比較前：`821448b384d37edc041152beb5d6b6f560ad771d`
- 042登録／開始HEAD：`ffae22493cece8c4c785775e605be3a1cdbd0070`
- ブランチ：`codex/task-042-review-equipment-save-migration`
- 開始時：未コミットなし、remoteの同名branchは登録SHA、未pushなし。初期環境のwork branchは基点だったため、指定branchをfetchして登録SHAから作業した。

checkoutのAGENTS.md、041/042、034数量・035の036採用追記・036・040の設計とS1/M表、041報告、新3モジュール、旧2ファイル、検査器/fixture/証拠を確認した。素材規約・職業魔物化企画・素材台帳も参照した。AGENTSは基点から変更なし。checkout `.agents/skills` は存在せず、`/workspace/.agents` にSKILL.mdなし。catalogの `superpowers:requesting-code-review` SKILL.mdを参照したが、追加委譲・修正に関する手順は依頼042の禁止を優先して行っていない。040の未実行計画を実行証拠として数えない。

## 差分と担当範囲

`git diff --name-status 821448b... 9e1c48e...` をパス限定せず全treeで確認：258追加・3変更・削除0。既存変更は旧2ファイルとdecision-logの末尾7行のみ。新規追加は新3モジュール＋uid、新検査＋uid、equipment-save fixture群、041依頼/報告、新しい検証証拠群で、許可範囲内。

`data/ assets/ .github/ test/ .scope-lock/ addons/` は全blob不変。既存検査・既存証拠・原画を含む他の既存ファイルは不変。実行コードSHA→レビュー対象SHAのscripts/tools/data/assets/test/.scope-lock/.githubは差分0。execution.jsonの16コード/fixture/検査器hashもすべて実物一致。証拠sha256.jsonの241件を全件再hashし不一致0。decision-logは過去部分を保持した追記だけ。

`game_session.gd` は人物本文の抽出と同じ場所からの呼出し、ID重複検証は元入口に残す。`integrated_progression.gd` はコピーした人物へ旧更新本文を適用する抽出のみ。通常入口のparty範囲、save/load、履歴・metrics副作用、新能力の通常登録に追加変更なし。別checkoutの実行結果も以下のとおり一致した。

## 環境・実行結果

Linux、Godot `4.7.2.stable.official.ed1daf0bf`。標準4.6.3は版確認のみで検証に使わなかった。公式ZIP SHA256 `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4`、実行ファイル `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` を照合。

別checkoutは `/tmp/task042/before`（基点）と `/tmp/task042/after`（実行コードSHA）。PATHは `/tmp/task042/bin` を先頭、XDG_CACHE_HOME/DATA_HOME/CONFIG_HOMEは `/tmp/task042/xdg/{cache,data,config}`。ログと専用出力は `/tmp/task042/evidence/`。既存検査の出力は別checkoutにだけ生成した。永続成果物の制限に従い、独自検査の全文・主要出力・hashは本報告に収め、既存証拠原本を上書きしていない。

| 実行コマンド（afterをcwd、特記以外） | 結果 |
| --- | --- |
| `timeout 600 godot --headless --path <before/after> --editor --import --quit` | 前後ともexit0、エラー/警告なし |
| `RPG_EQUIPMENT_SAVE_EXECUTION_SHA=8d3c1848d09b588fa41bcf6345d3aab6e12a5347 RPG_EQUIPMENT_SAVE_OUTPUT=/tmp/task042/evidence/migration.json timeout 120 godot --headless --path . --script res://tools/check_equipment_save_migration.gd` | exit0、61ケース・2,828条件・失敗0 |
| `RPG_LEGACY_EQ_OUTPUT=<before/after別json> timeout 120 godot --headless --path <before/after> --script res://tools/fixtures/equipment-save/legacy_equivalence.gd` | 前後exit0、旧検証142入力・更新10入力、cmp一致 |
| `timeout 240 godot --headless --path . --script res://tools/check_equipment_rules.gd` | exit0、5,394条件・400切替＋93条件、失敗0 |
| `python tools/check_equipment_invalid_definitions.py --source-sha 8d3c1848d09b588fa41bcf6345d3aab6e12a5347 --godot /tmp/task042/bin/godot --output /tmp/task042/evidence/invalid` | exit0、202/202ケース、1,576条件、失敗0 |
| `python tools/run_locked_checks.py` | exit0、R-01〜R-08全PASS、各tests_ran=true・parser_failed=false、timeoutなし |
| `python tools/check_frozen_files.py` | 実行前後とも26/26一致。提出checkoutでも26/26 |
| `python tools/validate_assets.py --strict` | exit0、画像1,154・音15・字体2・パレット3、問題0 |
| `timeout 120 godot --headless --path . --script res://independent042.gd` | 独自の手書き期待59条件、失敗0 |
| `timeout 120 godot --headless --path . --script res://review042.gd` | 独自型境界91例・273条件、失敗0。受理17・拒否74、全失敗候補なし・理由パスあり |
| `git diff --check` / 全tree・全証拠hash照合 | 問題なし |

既存検査のassert、時間上限、警告検出、workflowを変更していない。最終成功ログにSCRIPT ERROR/ERROR:/WARNING:/Parse Errorなし。

旧前後出力のSHA256はともに `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea`。041の保存出力とも一致。旧入口による新能力付与なし、純粋更新・import/upgrade二重実行・型値・metrics/history・隔離user://での旧save/load往復を比較した。

初回のbefore実行はfixtureコピー先の階層を誤りFile not foundでexit1。パスだけ訂正し同じスクリプトで再実行した。独自検査の初稿は新キーへのdot代入がStringNameを作る点とNaN比較を誤り7条件失敗した。テスト側をStringキーとvar_to_bytesの比較へ直し、最終59条件を再実行した。本番変更なし。初回ログを成功結果として扱っていない。

## 独自固定期待とM対応

既存期待JSONを結果から作り直さず、下表の期待と付録のassertを別に記述した。独自検査のsameは実装のdifferencesを使わず、var_to_bytes＋SavedValueTypes.same_typesで全体を比較する。

| 対応 | 確認した期待と結果 |
| --- | --- |
| M01/M05 | 形式1/2のparty1＋reserve3の12個、支給後22個。形式1はP+2=6、形式2にはformat1_supplyなし。新規本人8＋共通10=18を移行へ足していない |
| M02/M03 | 既存検査の同名旧枠別個体、未装備解放1、未解放0、弱い合法従前/負値杖の維持、reserve既所有の除外を再実行。通常同職change_jobの最強化を移行に流用していない |
| M04 独自 | regionの記録人物を戦士1人だけにし、二刀流・旧主弓/副剣、reserve空、armory剣/杖/弓。手書き期待は旧3＋支援剣1/重防具1=5、主000004・副000002を保持、袋2。共通後15/袋12、二重支給拒否。既存の多人数例では隠れる「袋に合法主武器がない」組合せも成功 |
| M06/M07 | reserve順を反転しArray[Dictionary]を保持、形式1/2双方で人数・ID・所属順維持。戦士既得masterのreserveだけtwo_handed追加1・装着0、未記録counts={}、legacy_masters保持、非master付与0。既存party/reserve既得2名例も再実行 |
| M08 | 同じpending候補の解放フラグだけtrueにして共通10付与、再実行already_granted。coinsを1だけ進めた候補は拒否。通常解放・加入・再転職の接続成功とは呼ばない |
| M10 | Array[String]/Array[Dictionary]/Array[float]、0.0/1.0/1.25、配列順、元入力deep不変、候補のネスト変更と外部二系統auditの変更が互いへ伝播しない。metadata再記述のerrors空と全文一致。既存311leaf改変検査も全実行 |
| M11 | 未知reserveキー→unknown_field、非Stringキー/型付き辞書→unsupported_value、NaN→numeric_overflow、未知習得→invalid_source、いずれも指定パス・候補なし・入力不変。所有重複・IDのitem差替え・source hash改変・支援台帳改変・未知能力・旧新混在・未知版を別々に拒否。正規候補の再入力はalready_migrated |
| 決定性 | fixture元hashはb×64。Python hashlibで独立計算したmigration IDは `fc3ab2256cc64efc331a79ae354b846c61b26ffc55f6ec96fd9554b25cdd5f4f`、実物一致。同入力の候補全体が一致 |

91型境界は13パス×[null,false,1,1.5,"bad",[],{}]。旧actor.integrated、world、overworld、integrated、first_region、job_id、last_human_job、player_cell等を含み、既存validator呼出し前後にスクリプト例外なし。17受理の内訳は、_play_sessionの7値、_saved_value_typesの7値、正しいcontent_revision=1・解放false・coins=1。残り74は拒否。最初の14はS1の全保存検証を意味しない（次節）。

## API保証と未実装の境界・引継ぎ

S1で保証するのは型復元済み旧docからの純粋装備移行、party/reserve旧人物条件、装備所有・合法化・数量、旧docから再計算する差分監査と、正規候補に限定した共通支給である。contextは実GameSession＋完全な旧能力定義＋明示two_handed定義が必要。未知能力を全受理する代替validatorではない。新候補は現GameSession._valid_stateに拒否されることも実行した。

- `validate_new` / `compare_transition` は移行直後または正規共通支給直後だけの照合器。任意に進行した新版保存の全体validatorではない。
- `grant_common` は通常解放の経路へ未接続。信頼する旧sourceと解放context、候補のboolフラグ以外の進行不変が前提。加入・職変更・所持品使用後にそのまま呼べるAPIと報告しない。
- 不正 `_play_session` の構造をS1は検証しない。型復元済み入力に残った `_saved_value_types` は存在すれば再記述するため、旧metadataの正否をこの入口だけでは証明しない。旧metadataの解読、履歴schema、保存bytes/hash一致はS2側の責務。上記の受理は通常保存成功の証拠に使わない。
- `_metadata` のdescribeとvaluesの対応型集合を照合し、非有限値・非Stringキー・型付き辞書の入口拒否、正常型付き配列の再記述errors空を独自確認した。未知キーの明示拒否はroot/actor/actor.integrated/masteryの列挙であり、履歴detailsなどの任意Dictionary全体へ未知キー禁止を拡大していない。
- S2以降：完全codec・新能力catalog登録・新版全状態/stats・通常save/load、S3の実ファイルI/O/原本保管/復旧、S4の支給/加入/戦闘/装飾実効果、S5の通常runtime/UI/公開は未実装・未検証。実ユーザー保存、実バイトの変換、手動旧本編workflowは実行していない。
- 新S1検査と独自検査は専用実行であり、既存CIには未接続。CI全成功からこれらの実行を推定していない。

これらは041の明記したS1境界と一致する。P3の修正要求もなし。後続の受入では当該固定SHAの全assertを保持し、S2〜S5の正負例を別途追加する必要がある。今回の範囲で追加判断を求める事項はない。

## CI・提出

041最終対象SHAについてGitHub APIで再照合した。run `37595909084`（CI）と `37595908965`（地方接続）のhead SHAは対象と一致し、全20jobがcompleted/success。

| 全ジョブ名 | 041最終対象の結果 |
| --- | --- |
| 素材検査 | success |
| 試遊前の通常戦闘・案内・画面・復帰検査 | success |
| Godot・凍結受入テスト | success |
| lifecycle-audit | success |
| acceptance-and-regression (fixed) | success |
| acceptance-and-regression (latest) | success |
| normal-input-and-rendering (fixed, journey) | success |
| normal-input-and-rendering (fixed, details) | success |
| normal-input-and-rendering (fixed, restart-0) | success |
| normal-input-and-rendering (fixed, restart-1) | success |
| normal-input-and-rendering (fixed, restart-2) | success |
| normal-input-and-rendering (fixed, restart-3) | success |
| normal-input-and-rendering (fixed, restart-4) | success |
| normal-input-and-rendering (latest, journey) | success |
| normal-input-and-rendering (latest, details) | success |
| normal-input-and-rendering (latest, restart-0) | success |
| normal-input-and-rendering (latest, restart-1) | success |
| normal-input-and-rendering (latest, restart-2) | success |
| normal-input-and-rendering (latest, restart-3) | success |
| normal-input-and-rendering (latest, restart-4) | success |

042の変更は依頼書の状態行と本報告だけ。commit/push後の最終SHA・同一SHAの全ジョブ終了結果・未コミット/未push状況は最終応答に記載する。本文自身のcommit SHAを本文へ埋め込んでSHAを変え続けることはしない。ローカルghの認証確認は失敗したため、CI照会には接続済みGitHubの読取APIを使用した。

## 再現用付録（独自検査の実行版）

別checkoutのルートへ以下をそれぞれ保存して表の120秒コマンドで実行する。期待は実装から生成していない。

### independent042.gd

SHA256 `f101d8ff267026cbd0f714e2a9b29e3b311066e45711008c6a82313a7bb8a60d`

```gdscript
extends SceneTree
const F=preload("res://tools/fixtures/equipment-save/fixtures.gd")
const M=preload("res://scripts/game/equipment_save_migration.gd")
const V=preload("res://scripts/game/equipment_save_validation.gd")
const H="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
var checks=0
var failures=[]
var s=GameSession.new()
var ctx=F.context(s)
func ck(ok:bool,label:String):
	checks+=1
	if not ok:failures.append(label)
func same(a,b):return var_to_bytes(a)==var_to_bytes(b) and SavedValueTypes.same_types(a,b)
func reject(doc:Dictionary,label:String,code:String,path:String):
	var before=doc.duplicate(true)
	var r=M.new().plan(doc,H,ctx)
	print("REJECT ",label," ",r)
	ck(r.get("ok")==false and r.get("reason_code")==code and not r.has("candidate_document"),label+" rejection")
	ck(r.get("errors",[]).any(func(e):return e.target==path),label+" path")
	ck(same(doc,before),label+" unchanged")
func counts(doc):
	var c={}
	for item in doc.equipment_stock.instances.values():c[item]=c.get(item,0)+1
	return c
func _initialize():
	var d=F.region()
	d.first_region.reserve=[]
	d.party[0].id="z_actor"
	d.leader_id="z_actor"
	d.party[0].learned_abilities=["twin_grip"]
	d.party[0].equipped_abilities=["twin_grip"]
	d.party[0].integrated.weapons=["practice_bow","practice_blade"]
	var before=d.duplicate(true)
	var r=M.new().plan(d,H,ctx)
	ck(r.ok,"single actor offhand source accepted")
	if r.ok:
		var c=r.candidate_document
		ck(counts(c)=={"practice_bow":1,"practice_blade":2,"practice_staff":1,"iron_plate_armor":1},"manual count5: old3 support2")
		ck(c.party[0].equipment.weapons.size()==2,"offhand retained count")
		ck(c.party[0].equipment.weapons[0].ends_with("000004") and c.party[0].equipment.weapons[1].ends_with("000002"),"main support4 offhand2")
		ck(c.equipment_stock.bag.size()==2 and c.equipment_grants.common_set=="pending","pending bag2")
		ck(c.equipment_migration.migration_id=="fc3ab2256cc64efc331a79ae354b846c61b26ffc55f6ec96fd9554b25cdd5f4f","independent Python digest")
		ck(same(d,before),"source immutable")
		ck(same(c,M.new().plan(d,H,ctx).candidate_document),"deterministic full candidate")
		var granted_input=c.duplicate(true)
		granted_input.progress_flags["job_change_unlocked"]=true
		var gc=ctx.duplicate();gc["job_change_unlocked"]=true
		var g=M.new().grant_common(granted_input,d,H,gc)
		ck(g.ok and g.candidate_document.equipment_stock.instances.size()==15,"pending5 to15")
		ck(g.candidate_document.equipment_stock.bag.size()==12,"common10 all bag")
		var again=M.new().grant_common(g.candidate_document,d,H,gc)
		ck(not again.ok and again.reason_code=="already_granted" and not again.has("candidate_document"),"grant second rejected")
		var unrelated=granted_input.duplicate(true);unrelated.first_region.coins+=1
		var limited=M.new().grant_common(unrelated,d,H,gc)
		ck(not limited.ok and not limited.has("candidate_document"),"grant not general progressed save")
		for kind in ["owner","id","audit","count","unknown","mixed","version"]:
			var bad=c.duplicate(true)
			match kind:
				"owner":bad.equipment_stock.bag.append(bad.party[0].equipment.weapons[0])
				"id":bad.equipment_stock.instances[bad.party[0].equipment.weapons[0]]="practice_staff"
				"audit":bad.equipment_migration.source_sha256="c".repeat(64)
				"count":bad.equipment_grants.actor_support.z_actor=[]
				"unknown":bad.party[0].learned_abilities.append("undefined_ability")
				"mixed":bad.party[0].integrated.weapons=["practice_blade"]
				"version":bad.equipment_rules_version=99
			var bc=ctx.duplicate();bc["source_document"]=d
			var br=M.new().plan(bad,H,bc)
			ck(not br.ok and not br.has("candidate_document") and not br.errors.is_empty(),"mutant "+kind)
		var rc=ctx.duplicate();rc["source_document"]=d
		ck(M.new().plan(c,H,rc).reason_code=="already_migrated","repeat migration")
		var frozen=c.duplicate(true)
		r.equipment_audit.actor_slots[0].instances.append("tamper")
		r.legacy_format_audit.actors.append({"tamper":true})
		ck(same(c,frozen),"both external audits independent")
		c.party[0].jp["warrior"]=17;c.equipment_migration.equipment_audit.actor_slots[0].weapons[0]="tamper"
		ck(same(d,before),"candidate nested mutation source independent")
	for version in [1,2]:
		var doc=F.legacy(true) if version==1 else F.region()
		var reserve:Array[Dictionary]=[];reserve.assign(doc.first_region.reserve);reserve.reverse()
		doc.first_region.reserve=reserve
		var learned:Array[String]=[];doc.party[0].learned_abilities=learned
		var details:Array[float]=[0.0,1.0,1.25]
		doc["_play_session"]={"details":details}
		doc["_saved_value_types"]=SavedValueTypes.describe(doc)
		var original=doc.duplicate(true)
		var rr=M.new().plan(doc,H,ctx)
		print("TYPED ",version," ",rr.get("errors"))
		ck(rr.ok,"typed version "+str(version))
		if rr.ok:
			ck(same(original,doc),"typed source unchanged")
			ck(rr.candidate_document.equipment_stock.instances.size()==12,"manual old4 pending12")
			ck(rr.candidate_document.first_region.reserve.is_typed() and rr.candidate_document.first_region.reserve[0].id=="pc_04","reserve type and order")
			ck(same(rr.candidate_document._play_session,doc._play_session),"fraction integral float preserved")
			ck(rr.candidate_document._saved_value_types.errors==[],"metadata describe no errors")
			var temp=rr.candidate_document.duplicate(true);temp.erase("_saved_value_types")
			ck(same(rr.candidate_document._saved_value_types,SavedValueTypes.describe(temp)),"metadata rewritten")
			ck(not s._valid_state(rr.candidate_document),"S1 not old normal acceptance")
			ck(rr.equipment_audit.generated.filter(func(e):return e.reason=="format1_supply").size()==(6 if version==1 else 0),"P+2 separated")
	var master=F.region()
	master.integrated.erase("mastery_rules_version")
	for actor in master.party+master.first_region.reserve:actor.integrated.erase("mastery")
	master.first_region.reserve[2].jp["warrior"]=120
	master.first_region.reserve[2].mastered_jobs=["warrior"]
	F.caps(master.first_region.reserve[2],s)
	var mr=M.new().plan(master,H,ctx)
	print("MASTER ",mr.get("errors"))
	ck(mr.ok,"unrecorded mastery source")
	if mr.ok:
		var a=mr.candidate_document.first_region.reserve[2]
		ck(a.learned_abilities==["two_handed"] and a.equipped_abilities==[],"master once no equip")
		ck(a.integrated.mastery=={"counts":{},"legacy_masters":["warrior"]},"no fabricated counts")
		ck(mr.candidate_document.party[0].learned_abilities==[],"nonmaster not rewarded")
	var bad=F.region();bad.first_region.reserve[2]["extra"]=1
	reject(bad,"unknown reserve","unknown_field","$.first_region.reserve[2].extra")
	bad=F.region();bad["_play_session"]={1:"bad key"}
	reject(bad,"nonstring key","unsupported_value","$._play_session")
	bad=F.region();bad["_play_session"]={"bad":NAN}
	reject(bad,"nonfinite","numeric_overflow","$._play_session.bad")
	bad=F.region();var typed:Dictionary[String,int]={"a":1};bad["_play_session"]=typed
	reject(bad,"typed dictionary","unsupported_value","$._play_session")
	bad=F.region();bad.party[0].learned_abilities=["missing"]
	reject(bad,"unknown ability","invalid_source","$.party[0]")
	print("INDEPENDENT042 ",JSON.stringify({"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
```

### review042.gd

SHA256 `239ea9a0e8e05f72199c1aa4fb9325e4bdf9a23478bfbb38c732986d2b0507d6`

```gdscript
extends SceneTree
const F=preload("res://tools/fixtures/equipment-save/fixtures.gd")
const M=preload("res://scripts/game/equipment_save_migration.gd")
var session=GameSession.new()
var ctx:Dictionary
var checks=0
var failures=[]
func _initialize():
	ctx=F.context(session)
	var base=F.region()
	for path in [["party",0,"integrated"],["world"],["overworld"],["integrated"],["first_region"],["_play_session"],["_saved_value_types"],["content_revision"],["party",0,"job_id"],["party",0,"last_human_job"],["progress_flags","job_change_unlocked"],["world","player_cell"],["first_region","coins"]]:
		for val in [null,false,1,1.5,"bad",[],{}]:
			var doc=base.duplicate(true)
			var ref=doc
			for i in range(path.size()-1):ref=ref[path[i]]
			ref[path[-1]]=val
			var before=var_to_bytes(doc)
			var expected_ok=path[0] in ["_play_session","_saved_value_types"] or (path==["content_revision"] and typeof(val)==TYPE_INT and val==1) or (path==["progress_flags","job_change_unlocked"] and typeof(val)==TYPE_BOOL) or (path==["first_region","coins"] and typeof(val)==TYPE_INT and val==1)
			print("BEGIN ",path,"=",JSON.stringify(val))
			var result=M.new().plan(doc,"a".repeat(64),ctx)
			print("END ",result.get("ok")," ",result.get("reason_code")," ",result.get("errors"))
			checks+=3
			if result.get("ok")!=expected_ok:failures.append(str(path)+" outcome "+str(val))
			if var_to_bytes(doc)!=before:failures.append(str(path)+" mutation")
			if not expected_ok and (result.has("candidate_document") or result.get("errors",[]).is_empty() or not result.errors.all(func(e):return e.target is String and not e.target.is_empty())):failures.append(str(path)+" failure contract")
	print("TYPE042 ",JSON.stringify({"cases":91,"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
```

### 今回出力のSHA256

| 出力 | SHA256 |
| --- | --- |
| migration.json | `635b4f4ce3535b77d25d54e2660308cc30ff8ef00dd4c8191683c4505f7dbbaf` |
| migration.log | `951e3c7ade93e94abb342f95f7edb95c3225202fae6a864340c2cf25984b17d7` |
| legacy-before.json | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy-after.json | `bb7bc92c918d9ab046bfee348bd033a0404cf0138a3c2248ac13f705a7dfe3ea` |
| legacy-before-retry.log | `a6dedfee36c2b1ca1a1b461a1c059e5fde67e9a31c4006ec3f6c7e22e2cc85d1` |
| legacy-after.log | `a6dedfee36c2b1ca1a1b461a1c059e5fde67e9a31c4006ec3f6c7e22e2cc85d1` |
| equipment.log | `0445447eda5da6d950e3f5f579b574ea75ad91d0e12d675f9189f372d6aa80bf` |
| invalid/results.json | `37b46e7ce5086adf2cd3b307b85c29395e41a8ac4be216af1d85e93d972770b2` |
| locked.log | `1d7888f05efc5f8dd0119fdf0f586c71139801a56c81bd398132001f3386409a` |
| independent-final.log | `cb0b4fb2149f21c215d17baa67e94f231ef8680406eb2eb1eee55b8174f25bb1` |
| probe-final.log | `c7b63b2e0b4fb0d6169f82a88bcc0462d25cf415bc7434060cdeab8e8ed75d1c` |
| import-before.log | `e960ccd70e2a2122dcb99636b28d9ee1ee449e90cf60a8289d5aaef96c68e722` |
| import-after.log | `e9005f00dc6747dfcc24229fef37d8f6d14cabace7eff9006f9dc7b12c0ef103` |
