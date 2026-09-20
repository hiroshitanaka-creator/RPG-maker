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
	var optional:=context.duplicate(true)
	optional["long_campaign_required"]=false
	if metrics.report(optional)["target_duration_observed"]:failures.append("長編が無効なら未完了でも受入候補にしてしまう")
	optional.erase("long_campaign_required")
	if metrics.report(optional)["target_duration_observed"]:failures.append("長編の必須欄がない記録を受入候補にしてしまう")
	context["long_campaign_complete"]=true
	var report:=metrics.report(context)
	if not report["target_duration_observed"]:failures.append("有効な時間帯と完走状態を照合できない")
	if report["acceptance_status"]!="UNREVIEWED" or report["human_identity_verified"]:failures.append("合成入力を正式な人間受入へ変換した")
	var game:=GameSession.new()
	game.new_game(4)
	if game.recording_context()["long_campaign_complete"]:failures.append("新規開始を長編完走として記録した")
	if not game.recording_context()["long_campaign_required"]:failures.append("未完成の本番でも60時間に必要な長編を必須として記録する")
	var incomplete:=game.recording_context()
	for key in ["history_complete","mixed_builds","content_revision","circuits_completed","duration_target_id"]:incomplete[key]=context[key]
	if metrics.report(incomplete)["target_duration_observed"]:failures.append("未完成の実ゲームの文脈から60時間の受入候補を作った")
	var wrong_routes:=context.duplicate(true)
	wrong_routes["circuits_completed"]=["waterway","waterway","waterway","waterway","waterway"]
	if metrics.report(wrong_routes)["target_duration_observed"]:failures.append("5件という個数だけで異なる5地点の完走と判定した")
	var wrong_type:=context.duplicate(true)
	wrong_type["long_campaign_complete"]=1
	if metrics.report(wrong_type)["target_duration_observed"]:failures.append("長編完了の型が真偽値でなくても受入候補にした")
	for failure in failures:printerr("LONG_RECORD_FAIL: "+failure)
	if failures.is_empty():print("LONG_RECORD_PASS: 長編の未完走を除外。合成境界入力、人間の実測ではない")
	quit(0 if failures.is_empty() else 1)
