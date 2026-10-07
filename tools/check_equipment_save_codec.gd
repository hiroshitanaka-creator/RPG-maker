extends SceneTree
const Codec = preload("res://scripts/game/equipment_save_codec.gd")
const Validation = preload("res://scripts/game/equipment_document_validation.gd")
const S1 = preload("res://scripts/game/equipment_save_validation.gd")
const Migration = preload("res://scripts/game/equipment_save_migration.gd")
const Rules = preload("res://scripts/game/equipment_rules.gd")
const Fixture = preload("res://tools/fixtures/equipment-save-codec/fixtures.gd")
const HASH = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
var session: GameSession
var context: Dictionary
var expected: Dictionary
var cases: Array=[]
var failures: Array=[]
var observations: Array=[]
var checks := 0

func check(condition: bool, label: String) -> void:
	checks+=1
	if not condition:failures.append(label)

func same(before: Variant, after: Variant) -> bool:
	return S1.differences(before,after).is_empty() and SavedValueTypes.same_types(before,after)

func run_case(id: String, value: Variant, operation: String="decode", custom: Dictionary={}) -> Dictionary:
	check(expected.cases.has(id) and id not in cases,id+" 固定ID・一意")
	cases.append(id)
	var ctx: Dictionary=context if custom.is_empty() else custom
	var before: Variant=value.duplicate(true) if value is Dictionary else value.duplicate()
	var state := session.export_state()
	var metrics := session.play_metrics.snapshot()
	var abilities: Dictionary=ctx.get("abilities",{}).duplicate(true)
	var result: Dictionary
	if operation=="decode":result=Codec.decode_source(value,ctx)
	elif operation=="encode":result=Codec.encode_candidate(value,ctx)
	elif operation=="prepare":result=Validation.prepare_candidate(value,ctx)
	else:
		var errors := Validation.validate(value,ctx)
		result={"ok":errors.is_empty(),"reason_code":"ok" if errors.is_empty() else errors[0].reason_code,"errors":errors}
	check(result.reason_code==expected.cases.get(id) and result.ok==(expected.cases.get(id)=="ok"),id+" 固定成否 実="+str(result.reason_code))
	check(var_to_bytes(value)==var_to_bytes(before),id+" 入力のnative表現不変")
	check(same(session.export_state(),state) and same(session.play_metrics.snapshot(),metrics) and same(abilities,ctx.get("abilities",{})),id+" state・計測・履歴・catalog不変")
	if not result.ok:
		check(not result.has("document") and not result.has("candidate_document") and not result.has("bytes"),id+" 失敗成功値なし")
		check(not result.errors.is_empty() and result.errors.all(func(error):return error.get("target") is String and not error.target.is_empty()),id+" パス付き拒否")
	var directory := OS.get_environment("EQUIPMENT_CODEC_EVIDENCE")
	if not directory.is_empty():
		var destination := directory.path_join(id)
		DirAccess.make_dir_recursive_absolute(destination)
		var source_file := FileAccess.open(destination.path_join("input.bin"),FileAccess.WRITE)
		if source_file==null:failures.append(id+" 入力証拠保存失敗")
		else:source_file.store_buffer(value if value is PackedByteArray else var_to_bytes(value));source_file.close()
		if result.ok and result.has("document"):
			var doc_file := FileAccess.open(destination.path_join("document.gdv"),FileAccess.WRITE)
			if doc_file==null:failures.append(id+" document証拠保存失敗")
			else:doc_file.store_buffer(var_to_bytes(result.document));doc_file.close()
		if result.ok and result.has("bytes"):
			var save_file := FileAccess.open(destination.path_join("encoded.bin"),FileAccess.WRITE)
			if save_file==null:failures.append(id+" raw出力証拠保存失敗")
			else:save_file.store_buffer(result.bytes);save_file.close()
	observations.append({"case":id,"operation":operation,"expected":expected.cases.get(id),"actual":result.reason_code,"errors":result.errors,"input_sha256":Codec.hash_bytes(value) if value is PackedByteArray else Codec.hash_bytes(var_to_bytes(value)),"input_bytes":value.size() if value is PackedByteArray else var_to_bytes(value).size(),"caps_changes":result.get("caps_changes",[]),"output_sha256":result.get("document_sha256",result.get("source_sha256",""))})
	return result

func json_bytes(document: Dictionary) -> PackedByteArray:
	return JSON.stringify(document,"",true,true).to_utf8_buffer()

func build(region: bool=false, format1: bool=false) -> Dictionary:
	var source := Fixture.region() if region else Fixture.base()
	if format1:
		source.format_version=1;source.erase("integrated")
		for actor in source.party+source.get("first_region",{}).get("reserve",[]):actor.erase("integrated")
	var plan := Migration.new().plan(source,HASH,context)
	check(plan.ok,"S1実APIの正規候補")
	if not plan.ok:return {}
	var prepared := Validation.prepare_candidate(plan.candidate_document,context)
	check(prepared.ok,"S2実APIの正規候補"+str(prepared.get("errors")))
	return prepared.get("document",{})

func codec_cases() -> void:
	var raw := FileAccess.get_file_as_bytes("res://tools/fixtures/equipment-save-codec/legacy.json")
	var result := run_case("M09-legacy-plain",raw)
	check(result.get("source_sha256")==expected.legacy_sha256,"固定raw SHA256")
	check(result.get("source_bytes")==raw,"raw bytes空白保持")
	if result.ok:check(same(result.document,Fixture.base()),"旧型なし正規化固定値")
	var old := Fixture.base()
	old["_play_session"]=Fixture.metrics()
	old["_trial_id"]="0123456789abcdef0123456789abcdef"
	old=Fixture.typed(old)
	result=run_case("M09-legacy-typed",json_bytes(old))
	if result.ok:check(same(old,result.document),"旧型あり全値・型・順序保持")
	old.erase("_saved_value_types")
	result=run_case("M09-legacy-untyped-metrics",json_bytes(old))
	if result.ok:
		check(result.document._play_session.events[0].details.integer_float is int and not result.document._play_session.events.is_typed(),"型なしの旧数値規則")
	var candidate := build()
	result=run_case("M09-new-no-aux",json_bytes(Fixture.typed(candidate)))
	if result.ok:check(not result.document.has("first_region") and not result.document.has("_play_session") and not result.document.has("_trial_id"),"非存在field追加0")
	candidate["_play_session"]=Fixture.metrics()
	candidate["_trial_id"]="0123456789abcdef0123456789abcdef"
	result=run_case("M09-new-typed",candidate,"encode")
	if result.ok:
		var reread := Codec.decode_source(result.bytes,context)
		check(reread.ok and same(Fixture.typed(candidate),reread.document),"同新版decoderで全値・型比較")
		check(reread.document._play_session.events[0].details.ints==[3,1,2] and reread.document._play_session.events[0].details.strings==["b","a"],"手書き配列順固定")
		check(reread.document._play_session.events[0].details.empty.get_typed_builtin()==TYPE_STRING and reread.document._play_session.events[0].details.integer_float is float,"空typed/float1.0固定")
	run_case("M09-new-existing-metadata",Fixture.typed(candidate),"encode")
	var many := candidate.duplicate(true)
	for index in range(9999):many._play_session.events.append({"kind":"history","chapter":"1","elapsed_ms":0,"details":{"index":index,"text":"固定履歴型保存の繰返し証拠"}})
	result=run_case("M09-new-gzip-10000",many,"encode")
	if result.ok:
		var envelope: Dictionary=JSON.parse_string(result.bytes.get_string_from_utf8())
		check(envelope.get("_storage_format")=="gzip-json-v1","実gzip包み")
		var read := Codec.decode_source(result.bytes,context)
		check(read.ok and read.document._play_session.events.size()==10000 and read.document._play_session.events[9999].details.index==9998,"10000履歴固定数と末尾")
		for key in ["_storage_format","decoded_bytes","sha256","payload_sha256","payload"]:
			var broken := envelope.duplicate(true)
			broken[key]=0 if key!="decoded_bytes" else -1
			run_case("M12-envelope-"+key,json_bytes(broken))
		var extra := envelope.duplicate(true);extra["extra"]=true
		run_case("M12-envelope-extra",json_bytes(extra))
	var untyped := candidate.duplicate(true)
	result=run_case("M09-new-untyped",json_bytes(untyped))
	if result.ok:check(result.document._play_session.events[0].details.integer_float is int,"新版型なし互換の観測")
	var roundtrip := candidate.duplicate(true)
	roundtrip._play_session.events[0].details["large"]=9007199254740993
	run_case("M12-precision-loss",roundtrip,"encode")
	for id in ["nan","inf"]:
		var broken := candidate.duplicate(true)
		broken._play_session.events[0].details["nonfinite"]=NAN if id=="nan" else INF
		run_case("M12-"+id,broken,"encode")
	var dictionary: Dictionary[String,int]={"value":1}
	var broken := candidate.duplicate(true);broken._play_session.events[0].details["typed_dictionary"]=dictionary
	run_case("M12-typed-dictionary",broken,"encode")
	broken=candidate.duplicate(true);broken._play_session.events[0].details["vector"]=Vector2.ZERO
	run_case("M12-builtin-value",broken,"encode")
	for id in ["missing","duplicate","builtin","extra","version"]:
		broken=Fixture.typed(candidate)
		match id:
			"missing":broken._saved_value_types.floats.append(["missing"])
			"duplicate":broken._saved_value_types.floats.append(broken._saved_value_types.floats[0].duplicate())
			"builtin":broken._saved_value_types.arrays[0].builtin=TYPE_OBJECT
			"extra":broken._saved_value_types["unknown"]=1
			"version":broken._saved_value_types.version=2
		run_case("M12-types-"+id,json_bytes(broken))
		run_case("M12-encode-types-"+id,broken,"encode")
	run_case("M12-invalid-utf8",PackedByteArray([123,34,255,34,58,49,125]))
	run_case("M12-invalid-json","{broken".to_utf8_buffer())
	run_case("M12-duplicate-json-key",'{"format_version":1,"format_version":2}'.to_utf8_buffer())
	var bad_inner := PackedByteArray([123,34,255,34,58,49,125])
	var payload := Marshalls.raw_to_base64(bad_inner.compress(FileAccess.COMPRESSION_GZIP))
	var bad_envelope := {"_storage_format":"gzip-json-v1","decoded_bytes":bad_inner.size(),"sha256":"0".repeat(64),"payload_sha256":payload.sha256_text(),"payload":payload}
	run_case("M12-gzip-invalid-utf8",json_bytes(bad_envelope))
	run_case("M12-json-array","[]".to_utf8_buffer())
	broken=Fixture.base();broken.format_version=99
	run_case("M12-unknown-legacy-version",json_bytes(broken))
	broken=Fixture.region();broken.overworld.cell=[0,0]
	result=run_case("M10-position-relocation",json_bytes(broken))
	check(result.has("position_before") and result.has("position_after") and not result.get("differences",[]).is_empty(),"位置補正の差分を提示")

func state_cases() -> void:
	var valid := build(true)
	run_case("M10-region-valid",valid,"validate")
	var prepared := run_case("M10-prepare-region",valid,"prepare")
	if prepared.ok:check(prepared.caps_changes.is_empty(),"再準備で上限変更0")
	var new_doc := build(false,true)
	run_case("M10-format1-migrated",new_doc,"encode")
	var progressed := valid.duplicate(true)
	progressed.inventory.potion=12;progressed.first_region.coins=37
	progressed.party[0].integrated.exp=8
	progressed.party[0].integrated.mastery.counts["warrior"]=1
	progressed.party[0].jp["warrior"]=3
	progressed.party[0].hp=0
	run_case("M10-progressed-new",progressed,"encode")
	check(not Validation.compare_migration(Fixture.region(),progressed,HASH,context).is_empty(),"進行後は移行直後との差分を拒否")
	check(Validation.compare_migration(Fixture.region(),valid,HASH,context).is_empty(),"S2正規移行差分API")
	check(S1.validate_new(valid,Fixture.region(),HASH,context).is_empty(),"S1固定契約維持（初期上限差なし）")
	check(not session.import_state(valid) and not session._valid_state(valid),"通常入口は新保存を拒否")
	for index in range(4):
		var actor: Dictionary=valid.party[0] if index==0 else valid.first_region.reserve[index-1]
		var stats := session.equipment_stats(actor,valid)
		check(stats.hp==expected.initial_stats[index].hp and stats.mp==expected.initial_stats[index].mp and stats.attack==expected.initial_stats[index].attack and stats.defense==expected.initial_stats[index].defense,"全人物stats固定表:%d" % index)
	for id in ["root","actor","reserve","integrated","world","metrics"]:
		var broken := valid.duplicate(true)
		match id:
			"root":broken["unknown"]=1
			"actor":broken.party[0]["unknown"]=1
			"reserve":broken.first_region.reserve[0]["unknown"]=1
			"integrated":broken.integrated["unknown"]=1
			"world":broken.world["unknown"]=1
			"metrics":broken["_play_session"]=Fixture.metrics();broken._play_session["unknown"]=1
		run_case("M10-unknown-"+id,broken,"validate")
	for id in ["hp","mp","mastery","jp","ability","duplicate"]:
		var broken := valid.duplicate(true)
		match id:
			"hp":broken.first_region.reserve[0].hp=999
			"mp":broken.first_region.reserve[0].max_mp=999
			"mastery":broken.first_region.reserve[0].integrated.mastery.counts["unknown"]=1
			"jp":broken.first_region.reserve[0].jp["unknown"]=1
			"ability":broken.first_region.reserve[0].learned_abilities.append("unknown")
			"duplicate":broken.first_region.reserve[0].id=broken.party[0].id
		run_case("M10-reserve-"+id,broken,"validate")
	for id in ["version","missing-version","mixed-world","mixed-actor","orphan","duplicate-owner","float-bag","null-bag","policy","audit","grants","grant-pending","grant-missing","support"]:
		var broken := valid.duplicate(true)
		match id:
			"version":broken.equipment_rules_version=2
			"missing-version":broken.erase("equipment_rules_version")
			"mixed-world":broken.integrated["armory"]=["practice_blade"]
			"mixed-actor":broken.party[0].integrated["weapons"]=["practice_blade"]
			"orphan":broken.equipment_stock.instances["orphan"]="practice_blade"
			"duplicate-owner":broken.equipment_stock.bag.append(broken.party[0].equipment.weapons[0])
			"float-bag":broken.equipment_stock.bag.append(1.0)
			"null-bag":broken.equipment_stock.bag.append(null)
			"policy":broken.equipment_migration.policy_id="unknown"
			"audit":broken.equipment_migration.equipment_audit.generated[0].item_id="iron_blade"
			"grants":broken.equipment_grants.policy_id="unknown"
			"grant-pending":broken.progress_flags["job_change_unlocked"]=true
			"grant-missing":broken.erase("equipment_grants")
			"support":broken.equipment_grants.actor_support.pc_01=[]
		run_case("M11-"+id,broken,"validate")
	for id in ["elapsed","chapter","counter","event","trial-empty","trial-length","trial-type"]:
		var broken := valid.duplicate(true)
		broken["_play_session"]=Fixture.metrics()
		match id:
			"elapsed":broken._play_session.elapsed_ms=1
			"chapter":broken._play_session.chapters["1"]={"active_ms":1,"elapsed_ms":1}
			"counter":broken._play_session.counters["n"]=-1
			"event":broken._play_session.events[0].elapsed_ms=1
			"trial-empty":broken["_trial_id"]=""
			"trial-length":broken["_trial_id"]="0123"
			"trial-type":broken["_trial_id"]=1
		run_case("M12-"+id,json_bytes(broken))
	var badctx := context.duplicate(true);badctx.abilities.erase("two_handed")
	run_case("M11-catalog-missing",valid,"encode",badctx)
	badctx=context.duplicate(true);badctx.abilities.two_handed.target="enemy"
	run_case("M11-catalog-invalid",valid,"encode",badctx)
	badctx=context.duplicate(true);badctx.abilities.two_handed.power=5
	run_case("M11-catalog-overwrite",valid,"encode",badctx)
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/equipment_abilities.json"))
	for id in ["missing","duplicate","passive","numeric"]:
		var catalog := BattleCatalog.new()
		var broken := data.duplicate(true)
		match id:
			"missing":broken.abilities=[]
			"duplicate":broken.abilities.append(broken.abilities[0].duplicate(true))
			"passive":broken.abilities[0].kind="physical"
			"numeric":broken.abilities[0].power=-1
		catalog._load_equipment_document(broken)
		check(not catalog.equipment_errors.is_empty() and catalog.equipment_context_abilities().is_empty(),"実catalog不正拒否:"+id)
	var unlocked := build()
	var hp_item := ""
	var mp_item := ""
	for instance in unlocked.equipment_stock.bag:
		if unlocked.equipment_stock.instances[instance]=="vitality_braid":hp_item=instance
		if unlocked.equipment_stock.instances[instance]=="thought_clasp":mp_item=instance
	unlocked.party[0].equipment.accessories=[hp_item,mp_item,""]
	unlocked.equipment_stock.bag.erase(hp_item);unlocked.equipment_stock.bag.erase(mp_item)
	unlocked.party[0].hp=0
	prepared=run_case("M10-caps-raise",unlocked,"prepare")
	if prepared.ok:
		check(prepared.document.party[0].max_hp==150 and prepared.document.party[0].max_mp==26 and prepared.document.party[0].hp==0 and prepared.document.party[0].mp==24,"+HP10/+MP2、回復・蘇生0")
		check(prepared.caps_changes.size()==1,"上限差分1人だけ")
		var lower: Dictionary=prepared.document
		lower.party[0].hp=149;lower.party[0].mp=26
		lower.equipment_stock.bag.append_array([hp_item,mp_item]);lower.party[0].equipment.accessories=["","",""]
		prepared=run_case("M10-caps-lower",lower,"prepare")
		if prepared.ok:check(prepared.document.party[0].hp==140 and prepared.document.party[0].mp==24,"上限低下時minだけ")
	# 現GameSession._stateの装備・人物値を変えても明示documentから同じstats。
	var actor: Dictionary=valid.first_region.reserve[0]
	var before_stats := session.equipment_stats(actor,valid)
	session._state.party[0].integrated.weapons=["iron_blade"]
	check(same(before_stats,session.equipment_stats(actor,valid)),"明示context reserve statsとlive state独立")

func extra_cases() -> void:
	var valid := build(true)
	for id in ["party-shape","inventory-shape","expedition-shape","actor-field-missing","reserve-field-missing","unknown-stock","unknown-travel","unknown-resident","negative-coins","invalid-world","invalid-progress","invalid-expedition","invalid-forgotten","invalid-relearn","invalid-focus","invalid-level","invalid-knowledge","invalid-outcome"]:
		var broken := valid.duplicate(true)
		match id:
			"party-shape":broken.party=[]
			"inventory-shape":broken.inventory=[]
			"expedition-shape":broken.expedition=[]
			"actor-field-missing":broken.party[0].erase("hp")
			"reserve-field-missing":broken.first_region.reserve[0].erase("hp")
			"unknown-stock":broken.equipment_stock["unknown"]=1
			"unknown-travel":broken.first_region["travel"]={"unknown":1}
			"unknown-resident":broken.overworld["residents"]={"fixture":{"cell":[6,7],"facing":0,"unknown":1}}
			"negative-coins":broken.first_region.coins=-1
			"invalid-world":broken.world.quest_step=-1
			"invalid-progress":broken.progress_flags["unknown"]=1
			"invalid-expedition":broken.expedition={"id":"unknown","stage":0,"wave":0,"origin":{},"solved":[]}
			"invalid-forgotten":broken.first_region.reserve[0].integrated.forgotten=["unknown"]
			"invalid-relearn":broken.first_region.reserve[0].integrated.relearn={"unknown":1}
			"invalid-focus":broken.first_region.reserve[0].integrated.focus_binding="unknown"
			"invalid-level":broken.first_region.reserve[0].integrated.level=2
			"invalid-knowledge":broken.integrated.knowledge={"unknown":{"facts":[],"confirmed":false}}
			"invalid-outcome":broken.integrated.outcomes={"unknown":{"rule":"unknown","methods":[]}}
		run_case("M10-"+id,broken,"prepare" if id in ["actor-field-missing","reserve-field-missing"] else "validate")
	for id in ["legacy-jp","legacy-world","legacy-nested","slot-index","slot-instance","slot-extra","audit-extra","audit-missing","generated-extra","support-reason","common-duplicate","returned-index","learned-reason"]:
		var broken := build(false,true) if id.begins_with("legacy") else build()
		match id:
			"legacy-jp":broken.equipment_migration.legacy_format_audit.actors[0].jp_after["warrior"]=999
			"legacy-world":broken.equipment_migration.legacy_format_audit.world_created.armory=[]
			"legacy-nested":broken.equipment_migration.legacy_format_audit.actors[0].integrated_created["unknown"]=1
			"slot-index":broken.equipment_migration.equipment_audit.actor_slots[0].index=99
			"slot-instance":broken.equipment_migration.equipment_audit.actor_slots[0].instances[0]="unknown"
			"slot-extra":broken.equipment_migration.equipment_audit.actor_slots[0]["unknown"]=1
			"audit-extra":broken.equipment_migration.equipment_audit["unknown"]=1
			"audit-missing":broken.equipment_migration.equipment_audit.erase("source_armory")
			"generated-extra":broken.equipment_migration.equipment_audit.generated[0]["unknown"]=1
			"support-reason":broken.equipment_grants.actor_support.pc_01[0].reason="unknown"
			"common-duplicate":broken.equipment_migration.equipment_audit.generated.back().reason="migration_support"
			"returned-index":broken.equipment_migration.equipment_audit.returned[0].index=3
			"learned-reason":broken.equipment_migration.equipment_audit.learned_added.append({"actor_id":"pc_01","ability_id":"two_handed","reason":"unknown"})
		run_case("M11-"+id,broken,"validate")
	var overflow := valid.duplicate(true)
	overflow["_play_session"]=Fixture.metrics()
	overflow._play_session.active_ms=9223372036854775807;overflow._play_session.idle_ms=1
	run_case("M12-metrics-overflow",overflow,"validate")
	var master := Fixture.region()
	master.party[0].mastered_jobs=["warrior"];master.party[0].jp={"warrior":120};master.party[0].integrated.mastery.counts={"warrior":20}
	var stats := session._compute_stats(master.party[0],true)
	master.party[0].max_hp=stats.hp;master.party[0].max_mp=stats.mp
	master=Fixture.typed(master)
	var planned := Migration.new().plan(master,HASH,context)
	check(planned.ok,"実catalogで戦士既得移行")
	if planned.ok:
		var prepared := Validation.prepare_candidate(planned.candidate_document,context)
		check(prepared.ok,"戦士既得S2上限準備")
		if prepared.ok:
			run_case("M10-two-handed-master",prepared.document,"encode")
			check(prepared.document.party[0].learned_abilities==["two_handed"] and prepared.document.party[0].equipped_abilities==[],"能力追加1・通常装着0")
			check(S1.validate_new(planned.candidate_document,master,HASH,context).is_empty(),"戦士既得S1契約維持")
			check(Validation.compare_migration(master,prepared.document,HASH,context).is_empty(),"戦士既得S2差分")
	var changed := valid.duplicate(true)
	changed.inventory.potion+=1;changed.first_region.coins+=1;changed.first_region.reserve[0].jp["warrior"]=1
	check(Validation.validate(changed,context).is_empty() and not Validation.compare_migration(Fixture.region(),changed,HASH,context).is_empty(),"有効進行と元保存差分を区別")
	for id in ["world","progress","coins","reserve","inventory","mastery"]:
		changed=valid.duplicate(true)
		match id:
			"world":changed.world.player_cell=[3,4]
			"progress":changed.progress_flags["midgame_slots"]=true
			"coins":changed.first_region.coins=21
			"reserve":changed.first_region.reserve.reverse()
			"inventory":changed.inventory.potion=4
			"mastery":changed.first_region.reserve[0].integrated.mastery.counts["warrior"]=1
		check(not Validation.compare_migration(Fixture.region(),changed,HASH,context).is_empty(),"非装備許可差分外を拒否:"+id)
	var broken := valid.duplicate(true);broken.party[0].learned_abilities.append("two_handed")
	run_case("M10-two-handed-unearned",broken,"validate")

func _initialize() -> void:
	expected=GameSession._normalize_numbers(JSON.parse_string(FileAccess.get_file_as_string("res://tools/fixtures/equipment-save-codec/expectations.json")))
	session=GameSession.new()
	check(session.errors.is_empty() and session.new_game(),"旧session実物初期化")
	context={"legacy_session":session,"abilities":session.catalog.equipment_context_abilities()}
	check(not context.abilities.is_empty() and not session.abilities.has("two_handed"),"実catalog内部登録・通常旧能力辞書維持")
	codec_cases()
	state_cases()
	extra_cases()
	var actual := cases.duplicate();actual.sort()
	var ids: Array=expected.cases.keys();ids.sort()
	check(actual==ids,"固定全ケース集合・件数・省略0")
	var output := {"cases":cases,"case_count":cases.size(),"checks":checks,"failures":failures,"observations":observations}
	var directory := OS.get_environment("EQUIPMENT_CODEC_EVIDENCE")
	if not directory.is_empty():
		DirAccess.make_dir_recursive_absolute(directory)
		var file := FileAccess.open(directory.path_join("codec.json"),FileAccess.WRITE)
		if file==null:failures.append("証拠保存失敗")
		else:file.store_string(JSON.stringify(output,"  ",true,true));file.close()
	if failures.is_empty():print("EQUIPMENT_CODEC_PASS: %dケース / %d条件 / 失敗0" % [cases.size(),checks])
	else:
		for label in failures:print("EQUIPMENT_CODEC_FAIL: "+label)
	quit(0 if failures.is_empty() else 1)
