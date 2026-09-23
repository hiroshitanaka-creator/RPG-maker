extends SceneTree
const Compare=preload("res://tools/save_state_comparison.gd")
var failures: Array[String]=[]
var checks:=0
func check(ok: bool,message: String)->void:
	checks+=1
	if not ok:failures.append(message)
func compare_game(before: GameSession,after: GameSession,label: String)->void:
	check(Compare.differences(before.export_state(),after.export_state(),"$state",[]).is_empty(),label+": 状態のキー・型・値・配列順序")
	check(Compare.differences(before.play_metrics.snapshot(),after.play_metrics.snapshot(),"$metrics",[]).is_empty(),label+": 履歴のキー・型・値・配列順序")
func _initialize()->void:
	var game:=GameSession.new();game.new_game(4);game.play_metrics.set_source("automated")
	var decimals: Array[float]=[1.0,1.0/3.0,0.000000012345]
	for i in range(10000):game.play_metrics.record_event("packed_fixture",{"ordinal":i,"decimals":decimals})
	var path:="user://qa_integrated_packed_%d.json" % OS.get_process_id()
	check(game.save_game(path),"大きい保存を作成")
	var packet: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path))
	check(packet.get("_storage_format")==SavedDocument.FORMAT,"大きい保存には可逆圧縮を適用")
	var restored:=GameSession.new();check(restored.load_game(path),"圧縮保存を別インスタンスへ読込")
	compare_game(game,restored,"圧縮往復")
	var plain:=game.export_state();plain["_play_session"]=game.play_metrics.snapshot();plain["_saved_value_types"]=SavedValueTypes.describe(plain)
	var old_path:=path+".plain"
	check(PlaySessionMetrics.write_json(old_path,plain),"従来の非圧縮JSONを用意")
	var legacy:=GameSession.new();check(legacy.load_game(old_path),"従来の大きいJSONも読める")
	compare_game(game,legacy,"非圧縮互換")
	for field in ["payload","payload_sha256","sha256","decoded_bytes","_storage_format"]:
		var broken:=packet.duplicate(true)
		if field=="decoded_bytes":broken[field]=SavedDocument.MAX_DECODED+1
		else:broken[field]=str(broken[field])+"x"
		var before:=restored.export_state()
		check(PlaySessionMetrics.write_json(path+".bad",broken),"破損した保存を用意")
		check(not restored.load_game(path+".bad") and restored.export_state()==before,"破損で現在の状態を変更しない: "+field)
	var actual: Array=[]
	if "--existing-completed-files" in OS.get_cmdline_user_args():
		for size in [3,4]:
			for order in ["forward","reverse"]:
				var prefix:="user://qa_long_audit_integrated_20260923_0050_%d_%s" % [size,order]
				var source:=""
				var latest:=-1
				for slot in range(2):
					var receipt: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(prefix+"_%d.receipt.json" % slot))
					if int(receipt["sequence"])>latest and FileAccess.get_sha256(receipt["save"])==receipt["save_sha256"]:
						source=receipt["save"];latest=int(receipt["sequence"])
				var old:=GameSession.new()
				if not FileAccess.file_exists(source) or not old.load_game(source):check(false,"実際の全編保存が存在する");continue
				check(old.story_complete(),"全編を通過して保存した実データ")
				var target:=path+".%d_%s" % [size,order]
				check(old.save_game(target),"実保存を新しい形式で再保存")
				var loaded:=GameSession.new();check(loaded.load_game(target),"実保存の圧縮後を読込")
				compare_game(old,loaded,"実保存の互換")
				var packed_bytes:=FileAccess.get_file_as_bytes(target).size()
				check(packed_bytes<1048576,"実際の全編保存が1MiB未満")
				actual.append({"party":size,"order":order,"original_bytes":FileAccess.get_file_as_bytes(source).size(),"packed_bytes":packed_bytes})
	PlaySessionMetrics.write_json("res://docs/verification/integrated-storage-current.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"synthetic_events":10000,"actual_completed_saves":actual,"failures":failures,"build":BuildIdentity.current(),"scope":"保存形式の互換と全変数の往復。旧版の実保存を読み替えたことを最終版の全編通過には数えない。"})
	for message in failures:printerr("INTEGRATED_STORAGE_FAIL: "+message)
	print("INTEGRATED_STORAGE_RESULT: checks=%d actual_saves=%d failures=%d" % [checks,actual.size(),failures.size()])
	quit(0 if failures.is_empty() else 1)
