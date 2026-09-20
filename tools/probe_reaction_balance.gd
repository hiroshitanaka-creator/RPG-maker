extends "res://tools/check_battle_acceptance.gd"

var game:=GameSession.new()
var initial_states: Dictionary={}
var results: Array=[]
var probe_hp:=0
var probe_resistance:=-1
var probe_guard_every:=0
var probe_heal_below:=0
var last_fast:=0.0
var last_p50:=0.0
var last_p90:=0

func _run() -> void:
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	for size in [3,4]:initial_states[size]=_initial_state(game,size,profile)
	var selected: Array=[]
	for enemy in ["gate_beast","elder_slime","night_bat","ancient_shell","core_wisp","flood_beast"]:
		var candidates: Array=[]
		for power in [0,5,10,15,20,25,30,40,50,60,75,100,125,150,175,200,250,300,400,600]:
			for speed in [0,3,6]:
				var rate:=_sample(enemy,power,speed,100,3,64)
				candidates.append({"enemy":enemy,"power":power,"speed":speed,"three_rate":rate})
		candidates.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return absf(a["three_rate"]-0.5)<absf(b["three_rate"]-0.5))
		var paired: Array=[]
		for candidate in candidates.slice(0,4):
			for shield in [100,85,70,55,40,25,10]:
				var rate:=_sample(enemy,candidate["power"],candidate["speed"],shield,4,128)
				var item: Dictionary=candidate.duplicate()
				item["shield"]=shield
				item["four_rate"]=rate
				item["distance"]=absf(item["three_rate"]-0.5)+absf(rate-0.5)
				paired.append(item)
		paired.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return a["distance"]<b["distance"])
		selected.append(paired[0])
		print("REACTION_SELECTED: ",paired[0])
		results.append({"enemy":enemy,"three_candidates":candidates,"paired_candidates":paired})
		PlaySessionMetrics.write_json("res://docs/verification/reaction-candidates.json",{"kind":"candidate_search_not_acceptance","results":results,"selected":selected,"errors":errors,"profile_sha256":FileAccess.get_sha256(PROFILE),"runner_sha256":FileAccess.get_sha256("res://tools/probe_reaction_balance.gd")})
	quit(0 if errors.is_empty() else 1)

func _sample(enemy: String,power: int,speed: int,shield: int,size: int,samples: int)->float:
	var won:=0
	var fast:=0
	var consumed: Array[int]=[]
	for seed_value in range(samples):
		game.new_game(size)
		if not game.import_state(initial_states[size]):errors.append("初期化失敗");break
		var battle:=game.start_battle([enemy],seed_value)
		var foe:=battle.living(Combatant.Team.ENEMY)[0]
		if probe_hp>0:foe.max_hp=probe_hp;foe.hp=probe_hp
		if probe_resistance>=0:foe.resistance=probe_resistance
		foe.tactics=foe.tactics.duplicate(true)
		foe.tactics["reaction_power"]=power
		foe.tactics["reaction_speed"]=speed
		foe.tactics["chorus_guard"]=shield
		foe.tactics["focus_variation"]=100
		if probe_guard_every>0:foe.tactics["guard_every"]=probe_guard_every
		if probe_heal_below>0:foe.tactics["heal_below"]=probe_heal_below
		var turns:=0
		for turn in range(30):
			if battle.phase!=BattleState.Phase.INPUT:break
			for actor in battle.pending():
				var error:=battle.queue_action(_action(battle,actor))
				if not error.is_empty():errors.append(error)
			battle.resolve_round()
			turns+=1
		won+=1 if battle.phase==BattleState.Phase.VICTORY else 0
		if battle.phase==BattleState.Phase.VICTORY:consumed.append(3-battle.potions)
		fast+=1 if battle.phase in [BattleState.Phase.VICTORY,BattleState.Phase.DEFEAT] and turns<=10 else 0
	last_fast=float(fast)/samples
	consumed.sort()
	last_p50=(float(consumed[(consumed.size()-1)/2])+float(consumed[consumed.size()/2]))/2.0 if not consumed.is_empty() else 99.0
	last_p90=consumed[ceili(consumed.size()*0.9)-1] if not consumed.is_empty() else 99
	return float(won)/samples
