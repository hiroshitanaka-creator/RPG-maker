extends "res://tools/check_story_campaign.gd"


func _run() -> void:
	var game: Variant = GameSession.new()
	if not game.has_method("begin_expedition"):
		printerr("CONTENT_FAIL: 25区画の本編接続が未実装です。")
		quit(1)
		return
	await super._run()
