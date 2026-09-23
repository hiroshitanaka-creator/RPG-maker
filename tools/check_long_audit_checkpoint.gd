extends SceneTree
const Audit=preload("res://tools/long_audit_checkpoint.gd")
const Driver=preload("res://tools/long_play_driver.gd")
var failures: Array[String]=[]
var checked:=0
func check(ok: bool,message: String)->void:
	checked+=1
	if not ok:failures.append(message)
func _initialize()->void:
	var game:=GameSession.new();game.new_game(3);game.play_metrics.set_source("automated")
	var driver=Driver.new()
	var build:=BuildIdentity.current()
	var hashes:={"checker":FileAccess.get_sha256("res://tools/check_long_audit_checkpoint.gd")}
	var audit=Audit.new("boundary_%d" % OS.get_process_id(),"3_forward",build,hashes,game.export_state())
	var progress:={"sequence":1,"missions":0,"checkpoints":0,"world_detour":false,"elapsed_seconds":0.0,"resumptions":0}
	check(audit.store(game,driver,progress),"検査保存と集計を記録")
	check(not audit.load_latest(GameSession.new(),Driver.new()).has("error"),"同一の保存・版・集計を再開")
	var wrong=Audit.new("boundary_%d" % OS.get_process_id(),"3_forward",{"id":"different"},hashes,game.export_state())
	check(wrong.load_latest(GameSession.new(),Driver.new()).has("error"),"異なるコードの記録を拒否")
	progress["sequence"]=2
	check(audit.store(game,driver,progress),"次世代をもう一方へ記録")
	var file:=FileAccess.open(audit.prefix+"_0.receipt.json",FileAccess.WRITE);file.store_string("{");file.close()
	var fallback: Dictionary=audit.load_latest(GameSession.new(),Driver.new())
	check(fallback.get("sequence")==1,"新しい集計が中断しても前世代を保持")
	driver.battles=1
	check(audit.store(game,driver,progress),"集計不整合を検出する入力を記録")
	check(audit.load_latest(GameSession.new(),Driver.new()).has("error"),"実勝利履歴より多い戦闘集計を拒否")
	PlaySessionMetrics.write_json("res://docs/verification/long-audit-checkpoint.json",{"status":"PASS" if failures.is_empty() else "FAIL","failures":failures,"checks":checked})
	for message in failures:printerr("LONG_AUDIT_FAIL: "+message)
	print("LONG_AUDIT_RESULT: failures=%d" % failures.size())
	quit(0 if failures.is_empty() else 1)
