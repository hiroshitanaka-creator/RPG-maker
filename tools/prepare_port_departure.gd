extends "res://tools/capture_forest_tower.gd"
## 採用済みの通常到達検査から、次の区切りの開始に使う通常保存を作る。
func _castle_route() -> void:
	OUTPUT="res://docs/verification/sprint5-port-town/departure/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	await super._castle_route()
	if not castle_failures.is_empty():return
	var save_path := "user://port_departure_%d.json" % OS.get_process_id()
	if not castle_check(_session().save_game(save_path),"港町手前の通常保存"):return
	var raw := FileAccess.get_file_as_bytes(save_path)
	var copy := FileAccess.open("res://.tools/port-departure.json",FileAccess.WRITE);copy.store_buffer(raw);copy.close()
	var hash := HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(raw)
	PlaySessionMetrics.write_json(OUTPUT+"save-origin.json",{"sha256":hash.finish().hex_encode(),"location":_state()["overworld"],"party":_state()["party"].map(func(a:Dictionary)->String:return a["id"]),"method":"新規開始から通常操作で村・洞窟・城・森の塔を通過し、山道でGameSession.save_gameを実行。保存内容の編集なし。"})
