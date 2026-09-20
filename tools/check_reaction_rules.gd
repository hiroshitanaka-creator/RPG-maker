extends "res://tools/check_battle_acceptance.gd"

var diagnostics:=RuntimeDiagnostics.new()

func check(value: bool, message: String)->void:
	if not value:errors.append(message)

func _run()->void:
	OS.add_logger(diagnostics)
	var profile: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(PROFILE))
	var game:=GameSession.new()
	var initial:=_initial_state(game,4,profile)
	var a:=_fixture(initial,731)
	var initial_state:=a.snapshot()
	var intent:=a.enemy_intents()
	var rng_state:=a._rng.state
	for index in range(20):
		check(a.enemy_intents()==intent and a._rng.state==rng_state and a.snapshot()==initial_state,"予告再表示で乱数と状態が変わらない")
	_queue_three(a)
	check(a.reaction_count()==3,"攻撃技を予約した人数を数える")
	check(a.reaction_multiplier(a.actor_by_id("enemy_01"))==4.0,"攻撃技の予約に応じた反応倍率")
	check(a.effective_speed(a.actor_by_id("enemy_01"))==19,"速さの予告が予約に対応する")
	var target_id: String=intent[0]["target"]
	var damage:=a.forecast_damage(target_id,false,-1,false)
	var defended:=a.forecast_damage(target_id,true,-1,false)
	check(defended<damage,"防御で反応攻撃の被害を軽減できる")
	a.clear_queue()
	check(a.reaction_count()==0 and a.reaction_multiplier(a.actor_by_id("enemy_01"))==1.0,"選び直しで反応が戻る")
	check(a.enemy_intents()[0]["target"]==target_id and a._rng.state==rng_state,"選び直しで敵の対象を再抽選しない")
	_queue_three(a)
	var b:=_fixture(initial,731)
	_queue_three(b)
	var expected:=a.forecast_damage(target_id,false,-1,false)
	var events:=a.resolve_round()
	check(events==b.resolve_round() and a.snapshot()==b.snapshot(),"予告参照回数によらず同じ入力とシードで一致する")
	var actual:=0
	for event in events:
		if event["code"]=="damage" and event["actor"]=="enemy_01":actual+=int(event["amount"])
	check(actual==expected,"反応込みのダメージ予告が実計算と一致する")
	var offensive_damage:=0
	for event in events:
		if event["code"]=="damage" and event["target"]=="enemy_01":offensive_damage+=int(event["amount"])
	var open:=_fixture(initial,731)
	open.actor_by_id("enemy_01").tactics["chorus_guard"]=100
	_queue_three(open)
	var unguarded_damage:=0
	for event in open.resolve_round():
		if event["code"]=="damage" and event["target"]=="enemy_01":unguarded_damage+=int(event["amount"])
	check(offensive_damage<unguarded_damage,"3人の攻撃技で共鳴防御が実際に働く")
	var supports:=_fixture(initial,731)
	supports.actor_by_id("pc_01").hp=20
	check(supports.queue_action(BattleAction.skill("pc_03","pc_01","heal")).is_empty(),"回復を通常操作で予約する")
	check(supports.reaction_count()==0,"回復は攻撃技に数えない")
	_check_production_replay(profile)
	await _check_ui(initial)
	errors.append_array(diagnostics.messages())
	OS.remove_logger(diagnostics)
	var native:=DisplayServer.get_name()!="headless"
	var destination: String="res://docs/verification/reaction-rules-native.json" if native else "res://docs/verification/reaction-rules.json"
	PlaySessionMetrics.write_json(destination,{"status":"PASS" if errors.is_empty() else "FAIL","errors":errors,"build":BuildIdentity.current(),"display_server":DisplayServer.get_name(),"native_render_checked":native,"scope":"反応の予告・取消・再現性・軽減・防御・回復の除外と戦闘画面。勝率の受入とは別。"})
	for message in errors:printerr("REACTION_RULE_FAIL: "+message)
	if errors.is_empty():print("REACTION_RULE_PASS: 予告・取消・実計算・防御・再現性・画面")
	quit(0 if errors.is_empty() else 1)

func _check_production_replay(profile: Dictionary)->void:
	for size in [3,4]:
		for setup in profile["encounters"]:
			for seed_value in [0,37,999]:
				var first:=GameSession.new()
				var second:=GameSession.new()
				var initial:=_initial_state(first,size,profile)
				second.new_game(size)
				check(second.import_state(initial),"本番編成を同一状態へ戻す")
				var a:=first.start_battle(setup["enemies"],seed_value)
				var b:=second.start_battle(setup["enemies"],seed_value)
				check(a.has_reactive_enemy(),"本番の指定戦闘に反応設定が接続されている")
				for turn in range(30):
					check(a.phase==b.phase,"本番戦闘の状態が再現される")
					if a.phase!=BattleState.Phase.INPUT:break
					var before:=a.snapshot()
					var preview:=a.enemy_intents()
					for repeat in range(4):check(a.enemy_intents()==preview and a.snapshot()==before,"本番の予告を再表示しても状態が変わらない")
					for encounter in [a,b]:
						for actor in encounter.pending():check(encounter.queue_action(_action(encounter,actor)).is_empty(),"本番の同一方針を予約する")
					check(a.resolve_round()==b.resolve_round() and a.snapshot()==b.snapshot(),"予告参照の有無によらず本番の行動順・結果が一致する")

func _fixture(initial: Dictionary, seed_value: int)->BattleState:
	var game:=GameSession.new()
	game.new_game(4)
	check(game.import_state(initial),"有効な固定編成")
	var battle:=game.start_battle(["gate_beast"],seed_value)
	var enemy:=battle.actor_by_id("enemy_01")
	enemy.max_hp=10000;enemy.hp=10000;enemy.attack=10
	enemy.tactics=enemy.tactics.duplicate(true)
	enemy.tactics.merge({"reaction_power":100,"reaction_speed":2,"chorus_guard":25},true)
	return battle

func _queue_three(battle: BattleState)->void:
	for action in [BattleAction.skill("pc_01","enemy_01","power_strike"),BattleAction.skill("pc_02","enemy_01","double_strike"),BattleAction.strike("pc_03","enemy_01"),BattleAction.skill("pc_04","enemy_01","fire")]:
		check(battle.queue_action(action).is_empty(),"通常のコマンドから技を予約できる")

func _check_ui(initial: Dictionary)->void:
	var main: Node=(load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	for roster in [["gate_beast"],["gate_beast","core_wisp","ancient_shell"]]:
		main.start_new_game(4)
		check(main.game.import_state(initial),"画面用の状態")
		var battle: BattleState=main.game.start_battle(roster,731)
		for enemy in battle.living(Combatant.Team.ENEMY):enemy.tactics.merge({"reaction_power":100,"reaction_speed":2,"chorus_guard":25},true)
		_queue_three(battle)
		main.mode=main.Mode.BATTLE
		main._actor="pc_01"
		main._refresh()
		await process_frame
		await process_frame
		if DisplayServer.get_name()!="headless":
			# 元の512px検査は1倍表示を明示して実行し、通常の2倍表示も別に検査する。
			root.size=Vector2i(512,288)
			await process_frame
			await process_frame
			RenderingServer.force_draw(false)
			RenderingServer.force_sync()
			var picture: Image=main.get_viewport().get_texture().get_image()
			check(not picture.is_empty() and picture.get_size()==Vector2i(512,288),"512×288の実描画が得られる: image="+str(picture.get_size())+" viewport="+str(main.get_viewport_rect().size))
			root.size=Vector2i(1024,576)
			await process_frame
			await process_frame
			RenderingServer.force_draw(false)
			RenderingServer.force_sync()
			picture=main.get_viewport().get_texture().get_image()
			check(not picture.is_empty() and picture.get_size()==Vector2i(1024,576),"通常の2倍表示を実描画する")
			check(main.get_viewport_rect().size==Vector2(512,288),"2倍表示でも内部解像度は512×288")
		var explanations:=0
		for node in main.find_children("*","Control",true,false):
			if not node.is_visible_in_tree():continue
			if node is Label and "技3" in node.text:explanations+=1
			if node is Label or node is BaseButton or node is RichTextLabel:
				check(main.get_viewport_rect().encloses(node.get_global_rect()),"反応予告を含む戦闘部品が画面内: "+node.get_class()+" "+str(node.get_global_rect()))
		check(explanations==roster.size(),"各敵の反応を画面に表示する")
	main.queue_free()
	await process_frame
