extends SceneTree

var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:failures.append(message)

func _initialize() -> void:
	var target := DurationTarget.definition()
	check(target.get("target_minutes") == 3600,"正式目標は60時間")
	check(target.get("goal_status") == "USER_APPROVED" and target.get("tolerance_status") == "PROVISIONAL","正式目標と暫定許容幅を区別")
	check(not DurationTarget.includes(330*60000),"旧5〜6時間の記録を60時間達成にしない")
	var metrics := PlaySessionMetrics.new()
	metrics.source = "human"
	metrics.completed = true
	# 時間帯だけを検査するため、完走済みという合成前提を与える。実ゲームの未完走は別の検査で拒否する。
	var context := {"history_complete":true,"mixed_builds":false,"content_revision":1,"circuits_completed":["waterway","cave","school","records","gate"],"duration_target_id":target.get("id",""),"long_campaign_required":true,"long_campaign_complete":true}
	for minutes in [3239,3240,3600,3960,3961]:
		metrics.active_ms = minutes*60000
		metrics.elapsed_ms = metrics.active_ms
		var report := metrics.report(context)
		check(report["target_duration_observed"] == (minutes >= 3240 and minutes <= 3960),"時間境界を判定: "+str(minutes))
		check(report["acceptance_status"] == "UNREVIEWED" and not report["human_identity_verified"],"合成した時間を実プレイ受入にしない")
	metrics.active_ms = 3600*60000
	metrics.elapsed_ms = metrics.active_ms
	var old := context.duplicate(true)
	old.erase("duration_target_id")
	check(not metrics.report(old)["target_duration_observed"],"目標版が不明な記録は候補にしない")
	metrics.source = "automated"
	check(not metrics.report(context)["target_duration_observed"],"自動操作を人間の60時間実測にしない")
	var result := {"kind":"synthetic_duration_boundary_test","target":target,"failures":failures,"real_60h_play":"NOT_RUN"}
	check(PlaySessionMetrics.write_json("res://docs/verification/duration-target-60h.json",result),"合成境界検査の結果を保存")
	for message in failures:printerr("DURATION_TARGET_FAIL: "+message)
	if failures.is_empty():print("DURATION_TARGET_PASS: 60時間目標、54〜66時間の暫定幅、旧記録・自動操作の除外")
	quit(0 if failures.is_empty() else 1)
