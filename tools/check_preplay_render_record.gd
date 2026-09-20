extends SceneTree

# 実描画の記録をheadlessで再集計する。headlessの実行時間を表示遅延に使わない。
func _initialize() -> void:
	var errors: Array[String]=[]
	var record: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/preplay-ui-native.json"))
	if record.get("kind")!="native_preplay_ui" or record.get("native_timing")!="MEASURED" or record.get("display_server")=="headless":errors.append("実描画の記録ではない")
	var recorded_build: Dictionary=record.get("build",{})
	var current_build:=BuildIdentity.current()
	# JSONの数値はfloatとして復元されるため、辞書の型付き一致ではなく各フィールドを照合する。
	for key in ["id","engine","version","files"]:
		if recorded_build.get(key)!=current_build[key]:errors.append("現在の実行版と記録の版が異なる: "+key)
	if record.get("runner_sha256")!=FileAccess.get_sha256("res://tools/check_preplay_ui.gd"):errors.append("測定コードの版が異なる")
	if record.get("status")!="PASS" or record.get("failures")!=[]:errors.append("実描画の検査が未達")
	var latencies: Dictionary=record.get("latency",{})
	if latencies.size()!=4:errors.append("4種類の入力の記録がない")
	for kind in ["move","select","cancel","equip"]:
		var entry: Dictionary=latencies.get(kind,{})
		var values: Array=entry.get("sorted_samples_ms",[])
		if values.size()!=100 or entry.get("samples")!=100 or entry.get("initial_five_ms",[]).size()!=5:
			errors.append("100回と初回5回が揃わない: "+kind)
			continue
		values.sort()
		if values[0]<0 or values[94]>100.0 or values.back()>200.0:errors.append("表示遅延の閾値未達: "+kind)
		if values[94]!=entry.get("p95_ms") or values.back()!=entry.get("max_ms") or entry.get("includes_render_readback")!=true:errors.append("生値と集計が一致しない: "+kind)
	for message in errors:printerr("RENDER_RECORD_FAIL: "+message)
	if errors.is_empty():print("RENDER_RECORD_PASS: 実描画4入力×100回の生値・版・閾値を再集計")
	quit(0 if errors.is_empty() else 1)
