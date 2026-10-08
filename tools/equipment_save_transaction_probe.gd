extends SceneTree
const Worker = preload("res://tools/fixtures/equipment-save-transaction/probe_worker.gd")

func _initialize() -> void:
	var request: Variant=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	if request is Array:
		# 起動後に実GameSessionを完全構築。読取り専用依存だけ再利用し、T/cacheは各要求で新規。
		var dependency := GameSession.new()
		for options in request:Worker.new().run_config(options,dependency)
	else:Worker.new().run_config(request)
	quit(0)
