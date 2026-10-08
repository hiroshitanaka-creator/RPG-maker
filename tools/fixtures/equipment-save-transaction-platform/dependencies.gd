extends SceneTree
const T=preload("res://scripts/game/equipment_save_transaction.gd")
const F=preload("res://tools/fixtures/equipment-save-codec/fixtures.gd")
func _initialize() -> void:
	var root: String=OS.get_cmdline_user_args()[0]
	var kind: String=OS.get_cmdline_user_args()[1]
	var session := GameSession.new()
	var context := {"legacy_session":session,"abilities":session.catalog.equipment_context_abilities()}
	var document := F.region()
	var advanced: String=session.job_progression.advanced.keys()[0]
	if kind=="job_progression":document.party[0].unlocked_jobs=[advanced]
	var raw := JSON.stringify(document,"",true,true).to_utf8_buffer()
	var source := root.path_join("source.json")
	var file := FileAccess.open(source,FileAccess.WRITE);file.store_buffer(raw);file.close()
	var t := T.new(root,context,"g1")
	var before := t.plan(raw)
	var prepared := t.prepare(source,T.hash_raw(raw),before.document,"g1") if before.ok else before
	match kind:
		"job_progression":session.job_progression.advanced.erase(advanced)
		"jobs":session.jobs.erase(document.party[0].job_id)
		"abilities":context.abilities.erase("two_handed")
		"source_build":context["source_build"]="changed-source-build"
		"session":
			var other := GameSession.new();other.job_progression.advanced.erase(advanced)
			if kind=="session":other.jobs.erase(document.party[0].job_id)
			context.legacy_session=other
	var same := t.plan(raw)
	var fresh := T.new(root,context,"g1").plan(raw)
	var committed := t.commit(before.token,"g1") if prepared.ok else prepared
	var result := {"before":before.ok,"prepared":prepared.ok,"same_ok":same.ok,"fresh_ok":fresh.ok,"same_reason":same.get("reason_code","ok"),"fresh_reason":fresh.get("reason_code","ok"),"candidate_equal":same.get("sha256","")==fresh.get("sha256",""),"commit":committed,"kind":kind}
	var out := FileAccess.open(root.path_join("dependency-result.json"),FileAccess.WRITE);out.store_string(JSON.stringify(result,"",true,true));out.close()
	print("DEPENDENCY_RESULT: ",JSON.stringify(result));quit(0)
