extends "res://tools/check_save_complete.gd"

# UI経路検査で採取した全入力を、保存契約の検査として別インスタンスで再実行する。
# 移動時間の検査は元のcheck_save_completeと全編CIで引き続き実行する。
func _run() -> void:
	if not _comparison_self_test():return
	var reports: Array = []
	for size in [3,4]:
		covered.clear()
		receipts.clear()
		var path := "res://docs/verification/save-contract-cases-%d.bin" % size
		if not _check(FileAccess.file_exists(path),"保存検査入力が存在する"):return
		var input := FileAccess.open_compressed(path,FileAccess.READ,FileAccess.COMPRESSION_ZSTD)
		if not _check(input != null,"保存検査入力を読める"):return
		var fixture: Variant = input.get_var(false)
		input.close()
		if not _check(fixture is Dictionary and fixture.get("party_size") == size and fixture.get("cases",[]).size() == 359,"各編成の359状態を省略しない"):return
		var names: Dictionary = {}
		for entry in fixture["cases"]:
			if not _check(not names.has(entry["case"]),"検査状態の重複を拒否する"):return
			names[entry["case"]] = true
			var game := GameSession.new()
			if not _check(game._valid_state(entry["state"]),"実経路で採取した入力が有効"):return
			# JSON読込用のimport_stateは配列を正規化するため、型付きの保存前fixtureは
			# 原型のまま設定する。保存後や期待値を型変換して差分を消してはいけない。
			game._state = entry["state"].duplicate(true)
			var input_differences := Compare.differences(entry["state"],game.export_state(),"$",[])
			if not _check(input_differences.is_empty(),"入力のキー・型・値・順序を復元段階で失わない: "+str(entry["case"])+" / "+" / ".join(input_differences)):return
			if entry["recording"]:
				if not _check(game.enable_recording("user://qa_contract_"+run_token+"_"+str(size)+"_"+str(names.size())),"独立した検査用履歴を生成する"):return
			for field in entry["metrics"]:
				if field == "version":continue
				var value: Variant = entry["metrics"][field]
				game.play_metrics.set(field,value.duplicate(true) if value is Dictionary or value is Array else value)
			if not _check(Compare.differences(entry["metrics"],game.play_metrics.snapshot(),"$",[]).is_empty(),"計測入力も型と値を保持する"):return
			if not _roundtrip(game,entry["case"]):return
		for field in Compare.ROOT_FIELDS:
			if not _check(covered.has("$."+field),"全保存領域を比較した: "+field):return
		for field in Compare.ACTOR_FIELDS:
			if not _check(covered.has("$.party[]."+field),"全人物項目を比較した: "+field):return
		for field in ["$.return_point.location","$.story_battle.cleared","$.story_task.id","$.gate_team[]","$.expedition.solved[]","$.party[].unlocked_jobs[]","$._play_session.answers[].note","$._trial_id","$.party[].integrated.mastery.counts"]:
			if not _check(covered.has(field),"条件付き保存項目を比較した: "+field):return
		reports.append({"party_size":size,"states":receipts.size(),"differences":0,"fixture_sha256":FileAccess.get_sha256(path),"covered_paths":covered.duplicate(true)})
		print("SAVE_COMPLETE_PASS: party=%d states=%d differences=0" % [size,receipts.size()])
	if not _check(PlaySessionMetrics.write_json("res://docs/verification/save-contract-current.json",{"status":"PASS","source":"captured_state_replay_actual_save_load","build":BuildIdentity.current(),"runner_sha256":FileAccess.get_sha256("res://tools/check_save_contract.gd"),"reports":reports,"human_playtest":"NOT_RUN"}),"実行結果を記録する"):return
	quit(0)
