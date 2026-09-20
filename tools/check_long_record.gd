extends SceneTree

func _initialize()->void:
	var metrics:=PlaySessionMetrics.new()
	metrics.source="human"
	metrics.completed=true
	metrics.active_ms=3600*60000
	metrics.elapsed_ms=metrics.active_ms
	var context: Dictionary={"history_complete":true,"mixed_builds":false,"content_revision":1,"circuits_completed":["waterway","cave","school","records","gate"],"duration_target_id":DurationTarget.definition()["id"],"long_campaign_required":true,"long_campaign_complete":false}
	var failures: Array[String]=[]
	if metrics.report(context)["target_duration_observed"]:failures.append("長編未完了の60時間を達成扱いにした")
	context["long_campaign_complete"]=true
	var report:=metrics.report(context)
	if not report["target_duration_observed"]:failures.append("有効な時間帯と完走状態を照合できない")
	if report["acceptance_status"]!="UNREVIEWED" or report["human_identity_verified"]:failures.append("合成入力を正式な人間受入へ変換した")
	var game:=GameSession.new()
	game.new_game(4)
	if game.recording_context()["long_campaign_complete"]:failures.append("新規開始を長編完走として記録した")
	for failure in failures:printerr("LONG_RECORD_FAIL: "+failure)
	if failures.is_empty():print("LONG_RECORD_PASS: 長編の未完走を除外。合成境界入力、人間の実測ではない")
	quit(0 if failures.is_empty() else 1)
