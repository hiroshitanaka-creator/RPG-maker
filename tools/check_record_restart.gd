extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	print("RESTART_MODE: "+str(args))
	var token: String = args[-1]
	if token.length() != 32 or not token.is_valid_hex_number(false):
		quit(2)
		return
	var game := GameSession.new()
	game.enable_recording("user://qa_crash_trials/"+token)
	var save_path := "user://qa_crash_"+token+".json"
	if "--writer" in args:
		game.new_game(4)
		game.play_metrics.set_source("automated")
		if not game.save_game(save_path):
			quit(3)
			return
		game.play_metrics.record_event("flushed_after_progress_save",{"synthetic":true})
		game.play_metrics.mark("flushed_after_progress_save")
		if not game.flush_recording():
			quit(4)
			return
		if not PlaySessionMetrics.write_json("res://.tools/restart-ready-"+token+".json",{"ready":true}):
			printerr("RESTART_FAIL: 合図を書き込めません")
			quit(6)
			return
		print("RESTART_WRITER_READY")
		# 親の検査プロセスがこの子だけを強制終了する。
		return
	if not game.load_game(save_path):
		quit(5)
		return
	var report := game.playtest_document()
	var ok: bool = report["counters"].get("flushed_after_progress_save") == 1 and not report["history_complete"] and not report["target_duration_observed"]
	print("RESTART_PASS: 保存済みの試行履歴を復元し、強制終了後の不明な末尾時間を未検証と表示" if ok else "RESTART_FAIL")
	game.close_recording()
	quit(0 if ok else 1)
