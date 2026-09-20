extends SceneTree
var errors: Array[String] = []
func check(ok: bool, message: String) -> void:
	if not ok:errors.append(message)
func _initialize() -> void:
	var game := GameSession.new()
	game.new_game(4)
	game.play_metrics.set_source("automated")
	# 60時間・毎分20回の操作履歴を合成する容量検査。人間のプレイ時間ではない。
	for minute in range(3600):
		game.play_metrics._accept_delta(60000,str(1+mini(5,minute/600)),"active_ms")
		for action in range(20):game.play_metrics.record_event("synthetic_input",{"actor":"pc_01","action":action,"ordinal":minute})
	var before := game.play_metrics.snapshot()
	var path := "user://qa_long_capacity_%d.json" % OS.get_process_id()
	var began := Time.get_ticks_msec()
	check(game.save_game(path),"60時間相当の合成履歴を保存")
	var save_ms := Time.get_ticks_msec()-began
	var loaded := GameSession.new()
	began = Time.get_ticks_msec()
	check(loaded.load_game(path),"別インスタンスへ合成履歴を読み戻す")
	var load_ms := Time.get_ticks_msec()-began
	check(preload("res://tools/save_state_comparison.gd").differences(before,loaded.play_metrics.snapshot(),"$",[]).is_empty(),"履歴72000件のキー・型・値・順序を保持")
	check(loaded.play_metrics.source=="automated" and not loaded.playtest_document()["target_duration_observed"],"合成60時間を人間の受入候補へ入れない")
	var file := FileAccess.open(path,FileAccess.READ)
	var bytes := file.get_length()
	file.close()
	# 頻繁な装着操作も含む上限寄りの合成負荷。暫定16MiB、保存/復元各5秒。
	check(bytes<=16777216 and save_ms<=5000 and load_ms<=5000,"合成高頻度履歴の暫定容量・時間予算")
	PlaySessionMetrics.write_json("res://docs/verification/long-record-capacity.json",{"status":"PASS" if errors.is_empty() else "FAIL","events":72000,"synthetic_active_hours":60,"save_bytes":bytes,"save_ms":save_ms,"load_ms":load_ms,"limits_provisional":{"bytes":16777216,"save_ms":5000,"load_ms":5000},"failures":errors,"build":BuildIdentity.current(),"human_duration":"NOT_RUN"})
	for error in errors:printerr("LONG_CAPACITY_FAIL: "+error)
	if errors.is_empty():print("LONG_CAPACITY_PASS: events=72000 bytes=%d save_ms=%d load_ms=%d" % [bytes,save_ms,load_ms])
	quit(0 if errors.is_empty() else 1)
