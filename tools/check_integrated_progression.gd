extends SceneTree
var failures: Array[String]=[]
var cases:=0
func check(ok: bool,message: String) -> void:
	if not ok:failures.append(message)
func actor(game: GameSession) -> Dictionary:
	return game.export_state()["party"][0]
func fight(game: GameSession, skill: String="") -> void:
	var b:=game.start_battle(["slime"],71)
	check(b!=null,"本番戦闘を開始")
	if b==null:return
	for a in b.pending():
		var action:=BattleAction.skill(a.id,"enemy_01",skill) if a.id=="pc_01" and not skill.is_empty() else BattleAction.guard(a.id)
		check(b.queue_action(action).is_empty(),"初回行動を通常APIで予約")
	b.resolve_round()
	for turn in range(30):
		if b.phase!=BattleState.Phase.INPUT:break
		for a in b.pending():check(b.queue_action(BattleAction.strike(a.id,b.living(Combatant.Team.ENEMY)[0].id)).is_empty(),"通常攻撃で戦闘を解決")
		b.resolve_round()
	check(b.phase==BattleState.Phase.VICTORY and game.finish_battle(),"勝利と実報酬を反映")
func _initialize() -> void:
	var game:=GameSession.new()
	check(game.new_game(4),"新規開始")
	check(game.export_state()["format_version"]==2,"通常開始の保存形式2")
	for i in range(4):fight(game)
	check(actor(game)["integrated"]["exp"]==80 and actor(game)["integrated"]["level"]==2 and actor(game)["jp"]["warrior"]==4,"EXPとJPを別々に加算")
	cases+=1
	game.new_game(4)
	var fixture:=game.export_state()
	fixture["party"][0]["integrated"]["exp"]=60
	fixture["party"][0]["hp"]=0
	check(game.import_state(fixture),"戦闘不能の有効な途中状態")
	fight(game)
	check(actor(game)["integrated"]["level"]==2 and actor(game)["hp"]==0,"基礎成長は蘇生しない")
	cases+=1
	game.new_game(4);game.change_job("pc_01","beast")
	fixture=game.export_state()
	fixture["party"][0]["erosion"]=29;fixture["party"][0]["integrated"]["erosion_fraction"]=8
	fixture["party"][0]["learned_abilities"]=["rending_claw"];fixture["party"][0]["equipped_abilities"]=["rending_claw"]
	check(game.import_state(fixture),"29.8の状態")
	fight(game,"rending_claw")
	check(actor(game)["erosion"]==30 and actor(game)["integrated"]["erosion_fraction"]==1,"戦闘0.2と技1行動0.1で30.1。4打を4使用にしない")
	cases+=1
	game.new_game(4)
	fixture=game.export_state()
	fixture["party"][0]["erosion"]=59;fixture["party"][0]["integrated"]["erosion_fraction"]=9
	fixture["party"][0]["learned_abilities"]=["rending_claw"];fixture["party"][0]["equipped_abilities"]=["rending_claw"]
	check(game.import_state(fixture),"59.9の人間職")
	fight(game,"rending_claw")
	check(actor(game)["erosion"]==60 and actor(game)["jp"]["warrior"]==0 and actor(game)["integrated"]["jp_remainders"]["warrior"]==1,"終了時60でJP半分の端数を保持")
	fight(game)
	check(actor(game)["jp"]["warrior"]==1 and actor(game)["integrated"]["jp_remainders"]["warrior"]==0,"2勝の半分JPを失わない")
	cases+=1
	game.new_game(4)
	fixture=game.export_state()
	fixture["party"][0]["erosion"]=89;fixture["party"][0]["integrated"]["erosion_fraction"]=9
	fixture["party"][0]["learned_abilities"]=["rending_claw"];fixture["party"][0]["equipped_abilities"]=["rending_claw"]
	check(game.import_state(fixture),"89.9の人間職")
	fight(game,"rending_claw")
	check(actor(game)["erosion"]==90 and actor(game)["irreversible"] and actor(game)["job_id"]=="beast","90到達で人間職を閉じる")
	check(not game.choose_job("pc_01","mage") and not game.release_monster_form("pc_01","purification_shrine"),"不可逆性を転職や祠で消さない")
	cases+=1
	game.new_game(4);game.change_job("pc_01","beast")
	fixture=game.export_state();fixture["party"][0]["jp"]["beast"]=119
	check(game.import_state(fixture),"マスター直前の状態")
	fight(game)
	check(actor(game)["monster_form"]=="beast","JP到達で必ず魔物化")
	var traits: Array=actor(game)["mastered_jobs"].duplicate()
	check(game.release_monster_form("pc_01","purification_shrine"),"祠で解除")
	check("form_beast" not in actor(game)["learned_abilities"] and "rending_claw" not in actor(game)["learned_abilities"],"専用技を消去")
	check(game.change_job("pc_01","beast"),"マスター済み職へ再転職")
	check("form_beast" not in actor(game)["learned_abilities"],"再転職だけで形態技を復活させない")
	fight(game)
	check("rending_claw" not in actor(game)["learned_abilities"] and actor(game)["integrated"]["relearn"]["rending_claw"]==1,"次の1勝だけで消去した技を復活させない")
	check(actor(game)["mastered_jobs"]==traits,"再習得でマスター特性を重ねない")
	var saved:=game.export_state()
	var metrics:=game.play_metrics.snapshot()
	var path:="user://qa_integrated_progression_%d.json" % OS.get_process_id()
	check(game.save_game(path),"新しい全進捗を保存")
	var loaded:=GameSession.new()
	check(loaded.load_game(path),"別インスタンスで読む")
	check(preload("res://tools/save_state_comparison.gd").differences(saved,loaded.export_state(),"$",[]).is_empty(),"新しい全値の型・キー・値・順序が一致")
	check(preload("res://tools/save_state_comparison.gd").differences(metrics,loaded.play_metrics.snapshot(),"$",[]).is_empty(),"小数を含む実使用履歴も一致")
	cases+=1
	game.new_game(4)
	var legacy:=game.export_state();legacy["format_version"]=1;legacy.erase("integrated")
	for a in legacy["party"]:a.erase("integrated")
	check(game.import_state(legacy) and game.export_state()==legacy,"旧形式を勝手に更新しない")
	check(game.upgrade_rules() and game.export_state()["format_version"]==2,"明示的な操作で新ルールへ移行")
	var upgraded:=game.export_state()
	check(not game.upgrade_rules() and game.export_state()==upgraded,"移行の二重実行を拒否")
	cases+=1
	for size in [3,4]:
		game.new_game(size);game.change_job("pc_01","beast")
		for victory in range(120):
			check(game.rest(),"町で正規の休息")
			fight(game)
			if victory==6:check("fang" not in actor(game)["learned_abilities"],"7JPでは未習得")
			if victory==7:check("fang" in actor(game)["learned_abilities"],"8JPの実勝利で第1技を習得")
			if victory==118:check(actor(game)["monster_form"]=="","119JPでは未マスター")
		check(actor(game)["monster_form"]=="beast" and actor(game)["jp"]["beast"]==120,"新規開始から120勝で魔物化。JP注入なし")
		check(game.release_monster_form("pc_01","purification_shrine") and game.change_job("pc_01","beast"),"通常の祠と再転職")
		for victory in range(60):
			game.rest();fight(game)
			if victory==58:check("rending_claw" not in actor(game)["learned_abilities"],"再習得59JPでは未取得")
		check("rending_claw" in actor(game)["learned_abilities"] and "form_beast" not in actor(game)["learned_abilities"],"再習得60JPで爪だけ取得、形態技120JPはまだ未取得")
		cases+=1
	var report:={"status":"PASS" if failures.is_empty() else "FAIL","cases":cases,"failures":failures,"scope":"実GameSessionの新規開始・報酬・境界・祠・保存・旧形式移行。境界の直前状態は明示的な検査入力。"}
	PlaySessionMetrics.write_json("res://docs/verification/integrated-progression-current.json",report)
	for failure in failures:printerr("INTEGRATED_PROGRESSION_FAIL: "+failure)
	if failures.is_empty():print("INTEGRATED_PROGRESSION_PASS: cases=%d" % cases)
	quit(0 if failures.is_empty() else 1)
