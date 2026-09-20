extends "res://tools/check_preplay_combat.gd"

const Counterplay=preload("res://tools/counterplay_policy.gd")
var _planned_key: String=""
var _planned: Dictionary={}

# 予約・選び直しは本番の公開APIで行う。AC-01の固定方針は変更しない。
func _action(battle: BattleState, actor: Combatant)->BattleAction:
	var key: String="%d:%d" % [battle.get_instance_id(),battle.round_number]
	if key!=_planned_key:
		_planned_key=key
		for member in battle.pending():
			var error:=battle.queue_action(Counterplay.base_action(battle,member))
			if not error.is_empty():errors.append(error)
		for adjustment in Counterplay.adjustments(battle):
			var error:=battle.queue_action(adjustment)
			if not error.is_empty():errors.append(error)
		_planned=battle.queued.duplicate()
	return _planned[actor.id]

func _run()->void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	var records: Array=[]
	for circuit in CampaignContent.data()["circuits"]:
		for section in circuit["sections"]:
			var waves: Array=[]
			var reward: Dictionary={}
			for entry in circuit["steps"]:
				if entry["section"]!=section["id"]:continue
				if entry["kind"]=="battle":waves.append(entry["enemies"])
				if entry["kind"]=="challenge":reward=entry
			for size in [3,4]:
				var initial:=_initial_state(game,size,profile)
				var wins:=0
				var used: Array[int]=[]
				for seed_value in range(1000):
					game.new_game(size)
					if not game.import_state(initial):errors.append("初期状態の復元失敗");break
					var result:=_trial(game,waves,seed_value,true,false,reward)
					if result.is_empty():break
					if result["victory"]:wins+=1;used.append(result["potions_used"])
				used.sort()
				var median: float=(float(used[(used.size()-1)/2])+float(used[used.size()/2]))/2.0 if not used.is_empty() else 99.0
				var p90:=used[ceili(used.size()*0.9)-1] if not used.is_empty() else 99
				records.append({"section":section["id"],"party_size":size,"trials":1000,"wins":wins,"potion_median":median,"potion_p90":p90})
				if wins<900:errors.append("対処方針の無帰還連戦が90%未達: "+section["id"]+"/"+str(size))
				print("ROUTE_COUNTERPLAY_CASE: %s party=%d wins=%d median=%.1f p90=%d" % [section["id"],size,wins,median,p90])
	if records.size()!=50:errors.append("25区画と2編成の網羅が不足")
	errors.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	PlaySessionMetrics.write_json("res://docs/verification/route-counterplay.json",{"kind":"counterplay_route_diagnostic","threshold_status":"PROVISIONAL","minimum_win_rate":0.9,"reason":"予告に対処した固定方針で、追加育成・帰還を挟まず区画を9割以上完了できる初期案。人間の初見勝率とは扱わない。","results":records,"errors":errors,"build":BuildIdentity.current(),"human_playtest":"NOT_RUN"})
	for message in errors:printerr("ROUTE_COUNTERPLAY_FAIL: "+message)
	if errors.is_empty():print("ROUTE_COUNTERPLAY_PASS: 25区画×3人/4人×1000シード、途中帰還なしで全件90%以上")
	quit(0 if errors.is_empty() else 1)
