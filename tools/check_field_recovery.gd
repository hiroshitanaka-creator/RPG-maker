extends "res://tools/check_battle_acceptance.gd"

const Compare=preload("res://tools/save_state_comparison.gd")

func check(value: bool,message: String)->void:
	if not value:errors.append(message)

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var cases:=0
	for size in [3,4]:
		for circuit in CampaignContent.data()["circuits"]:
			var solved: Array=[]
			var base:=StoryCampaign.step(circuit["trigger_step"])
			for stage in range(circuit["steps"].size()):
				var task: Dictionary=circuit["steps"][stage]
				if task["kind"]!="challenge":continue
				var game:=GameSession.new()
				var before:=_initial_state(game,size,profile)
				before["world"]={"location":task["location"],"player_cell":task["cell"],"section":task["section"],"quest_step":circuit["trigger_step"]}
				before["expedition"]={"id":circuit["id"],"stage":stage,"wave":0,"origin":{"location":base["location"],"player_cell":base["cell"],"quest_step":circuit["trigger_step"]},"solved":solved.duplicate()}
				before["party"][0]["hp"]=1;before["party"][0]["mp"]=0
				before["party"][1]["hp"]-=1;before["party"][1]["mp"]=1
				before["party"][2]["hp"]=0;before["party"][2]["mp"]=0
				check(game.import_state(before),"消耗・戦闘不能を含む有効状態")
				check(not game.answer_challenge((int(task["answer"])+1)%3) and game.export_state()==before,"誤答で回復・報酬を得ない")
				check(game.answer_challenge(int(task["answer"])),"正答の通常操作で報酬を受け取る")
				var after:=game.export_state()
				for index in range(size):
					var previous: Dictionary=before["party"][index]
					var actor: Dictionary=after["party"][index]
					for pair in [["hp","max_hp"],["mp","max_mp"]]:
						var expected: int=previous[pair[0]] if previous["hp"]==0 else mini(previous[pair[1]],previous[pair[0]]+ceili(previous[pair[1]]*0.5))
						check(actor[pair[0]]==expected,"生存者のみ50%回復し上限を越えない")
				check(after["inventory"]["potion"]==before["inventory"]["potion"]+1,"薬を1個だけ受け取る")
				check(not game.answer_challenge(int(task["answer"])) and game.export_state()==after,"再操作で報酬を重複しない")
				var path: String="user://qa_field_recovery_%d.json" % size
				check(game.save_game(path),"報酬後の進行を保存する")
				var loaded:=GameSession.new()
				check(loaded.load_game(path),"別インスタンスへ復帰する")
				check(Compare.differences(after,loaded.export_state(),"$",[]).is_empty(),"HP・MP・報酬・進行の型と値を保存復帰で保持する")
				check(not loaded.answer_challenge(int(task["answer"])),"ロードしても解決済み報酬を取得できない")
				solved.append(task["id"])
				cases+=1
	check(cases==50,"25区画と3人・4人を網羅する")
	PlaySessionMetrics.write_json("res://docs/verification/field-recovery.json",{"cases":cases,"errors":errors,"status":"PASS" if errors.is_empty() else "FAIL","build":BuildIdentity.current()})
	for error in errors:printerr("FIELD_RECOVERY_FAIL: "+error)
	if errors.is_empty():print("FIELD_RECOVERY_PASS: 50状態、誤答・上限・戦闘不能・二重取得・保存復帰")
	quit(0 if errors.is_empty() else 1)
