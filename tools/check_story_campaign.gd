extends "res://tools/smoke_chapter1.gd"

var _failed: bool = false
var _captured: Dictionary = {}


func _check(condition: bool, message: String) -> bool:
	if not condition:
		_failed = true
		_fail(message)
	return condition


func _fail(message: String) -> void:
	printerr("STORY_FAIL: " + message)
	quit(1)


func _run() -> void:
	var packed: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var main := packed.instantiate()
	root.add_child(main)
	await process_frame
	var party_size := 3 if "--three-member-party" in OS.get_cmdline_user_args() else 4
	main.start_new_game(party_size)
	main.game.play_metrics.set_source("automated")
	if not main.game.has_method("journal_entries") or not main.game.has_method("story_complete"):
		_fail("v1本編の回収台帳・手帳・結末への進行が未接続です。")
		return
	if not main.game.has_method("story_audit"):
		_fail("回収の依存関係を検査できません。")
		return
	var problems: Array = main.game.story_audit()
	if not problems.is_empty():
		_fail(" / ".join(problems))
		return
	if not _check(main.game.journal_entries().is_empty(), "初期手帳に未発見の答えを出さない"):
		return
	main.submit_player_action({"kind":"journal"})
	if not _check(not main.submit_player_action({"kind":"replay","event":"identity"}), "未読の過去記録を再生できない"):
		return
	main.submit_player_action({"kind":"back"})
	var original: Dictionary = main.game.export_state()
	var broken := original.duplicate(true)
	broken["progress_flags"]["clue_R01_resolved"] = true
	if not _check(not main.game.import_state(broken) and main.game.export_state() == original, "設置なしの回収をロードで持ち込まない"):
		return
	var prepared: Dictionary = {}
	var summarized: Dictionary = {}
	var checked_chapters: Dictionary = {}
	var gate_checked := false
	var gate_before: Dictionary = {}
	var visits: Array[String] = []
	var moved := 0
	var rounds := 0
	var old_serial := ""
	var stalled := 0
	for frame in range(MAX_STEPS):
		await process_frame
		var state: Dictionary = main.automation_snapshot()
		if _failed:
			return
		if not gate_before.is_empty() and StoryCampaign.stage(main.game.export_state()["progress_flags"],"R03") == 2:
			var after_gate: Dictionary = main.game.export_state()
			for index in range(after_gate["party"].size()):
				var member: Dictionary = after_gate["party"][index]
				var expected := int(gate_before["party"][index]["mp"]) - (7 if member["id"] in after_gate["gate_team"] else 0)
				if not _check(member["mp"] == expected, "水門を担当した三人だけが7MPを一度消費する"):
					return
			gate_before = {}
		if state.get("story_complete",false):
			if int(main.game.export_state().get("content_revision",0)) == 1:
				for circuit in CampaignContent.data()["circuits"]:
					if not _check(main.game.export_state()["progress_flags"].get("circuit_"+circuit["id"]+"_cleared",false),"追加5ダンジョンの点検をすべて完了する"):
						return
			var entries: Array = main.game.journal_entries()
			if not _check(entries.size() == 8, "手帳8件を維持する"):
				return
			for entry in entries:
				if not _check(entry["stage"] == 2, "全8件を回収して結末へ進む"):
					return
			var unchanged: Dictionary = main.game.export_state()
			var altered := unchanged.duplicate(true)
			altered["party"][0]["erosion"] = 30
			var witness := GameSession.new()
			if not _check(witness.import_state(altered), "反応差分の有効な状態を読める"):
				return
			for identifier in ["identity","lesson","teaching"]:
				var ordinary: Array = main.game.story_lines({"event":identifier})
				var changed: Array = witness.story_lines({"event":identifier})
				if not _check(ordinary[0] != changed[0] and ordinary.slice(1) == changed.slice(1), "NPC反応は要所3箇所の短い差分に限る"):
					return
			if not _check(main.game.export_state() == unchanged, "手帳と記録の参照で結果を変更しない"):
				return
			if not _check(visits.size() == 2, "第5章の両方の再訪を実行する"):
				return
			await _capture(main,"ending")
			main.submit_player_action({"kind":"journal"})
			await _capture(main,"journal_complete")
			if not _check(main.submit_player_action({"kind":"replay","event":"identity"}), "読了済みの過去記録を再閲覧できる"):
				return
			await _capture(main,"past_record_replay")
			for index in range(20):
				if main.automation_snapshot().get("mode") != "dialogue":
					break
				main.submit_player_action({"kind":"confirm"})
			if not _check(main.automation_snapshot().get("mode") == "journal" and main.game.export_state() == unchanged, "再閲覧は手帳へ戻り報酬やフラグを重複変更しない"):
				return
			print("STORY_PASS: party=%d moved=%d rounds=%d clues=8 visits=%s" % [party_size,moved,rounds,",".join(visits)])
			if not _check(main.game.save_playtest_report("user://qa_story_route_%d.json" % party_size),"自動操作の実測を人間の試遊とは別に保存する"):
				return
			print("AUTOMATED_ELAPSED_SECONDS: %.3f" % (main.game.play_metrics.elapsed_ms/1000.0))
			quit(0)
			return
		var serial := JSON.stringify(state)
		stalled = stalled+1 if serial == old_serial else 0
		old_serial = serial
		if stalled > 600:
			_fail("進行停止: " + serial)
			return
		var entry: Dictionary = main.game.current_story_step()
		var key := str(state.get("quest_step",0)) + ":" + str(entry.get("id","")) + ":wave" + str(state.get("battle_wave",0))
		match state.get("mode", ""):
			"challenge":
				main.submit_player_action({"kind":"challenge_answer","option":entry["answer"]})
			"complete":
				var legacy: Dictionary = main.game.export_state()
				for identifier in legacy["progress_flags"].keys():
					if str(identifier).begins_with("story_event_"):
						legacy["progress_flags"].erase(identifier)
				var restored := GameSession.new()
				if not _check(restored.import_state(legacy) and restored.chapter_one_pause() and restored.journal_entries().size() == 3, "従来の第1章クリア保存から三つの既知情報を保って再開する"):
					return
				main.game.import_state(restored.export_state())
				if not _check(main.submit_player_action({"kind":"continue_story"}), "第1章クリア後に本編を継続できる"):
					return
			"field":
				var chapter := int(state.get("chapter",1))
				if not checked_chapters.has(chapter):
					checked_chapters[chapter] = true
					var before: Dictionary = main.game.export_state()
					var path := "user://story_route_%d.json" % party_size
					var restored := GameSession.new()
					if not _check(main.game.save_game(path) and restored.load_game(path) and restored.export_state() == before, "章をまたいだセーブ往復が一致する"):
						return
					main.game.import_state(restored.export_state())
					main._resume_current()
					if before["progress_flags"].get("story_event_lesson",false):
						for actor in before["party"]:
							var capacity := 3 if str(actor["monster_form"]).is_empty() else 4
							if not _check(main.game.slot_limit(actor["id"]) == capacity, "中盤の教習で三枠、魔物化中なら四枠を保持する"):
								return
					print("STORY_PROGRESS: chapter=%d step=%s" % [chapter,key])
				if chapter >= 2 and not _captured.has("journal_first") and StoryCampaign.stage(main.game.export_state()["progress_flags"],"R01") == 2:
					main.submit_player_action({"kind":"journal"})
					var journal: Array = main.game.journal_entries()
					for item in journal:
						if item["id"] == "R02" and not _check(not item.has("resolved"), "次の疑問の答えを先に表示しない"):
							return
					await _capture(main,"journal_first")
					_captured["journal_first"] = true
					main.submit_player_action({"kind":"back"})
				if entry.get("kind") == "battle" and not prepared.has(key):
					prepared[key] = true
					if main.game.world_state()["location"] not in ChapterOne.TOWNS:
						if not _check(main.submit_player_action({"kind":"return_to_town"}), "戦闘前に町へ帰還できる"):
							return
						main.submit_player_action({"kind":"rest"})
						if not _check(main.submit_player_action({"kind":"resume_exploration"}), "戦闘地点への探索を再開する"):
							return
					_prepare_loadout(main)
				var here: Array = state["player_cell"]
				var goal: Array = state["objective_cell"]
				if here == goal:
					main.submit_player_action({"kind":"interact"})
				else:
					var route := _route(here,goal,state["walkable_cells"])
					if route.is_empty():
						_fail("歩いて到達できない目標: " + key)
						return
					if main.submit_player_action({"kind":"move","dx":route[0][0]-here[0],"dy":route[0][1]-here[1]}):
						moved += 1
			"dialogue":
				if entry.get("event") == "identity":
					await _capture(main,"past_record")
				if not summarized.has(key) and main.submit_player_action({"kind":"summary"}):
					summarized[key] = true
				else:
					main.submit_player_action({"kind":"confirm"})
			"battle":
				var input: Dictionary = state["battle_input"]
				if input["ready"]:
					main.submit_player_action({"kind":"resolve_round"})
					rounds += 1
				else:
					_choose_battle_action(main,input)
			"visits":
				await _capture(main,"visit_order")
				var first := "teaching" if "--teaching-first" in OS.get_cmdline_user_args() else "reply"
				var task := first if visits.is_empty() else ("reply" if first == "teaching" else "teaching")
				visits.append(task)
				if not _check(main.submit_player_action({"kind":"visit_task","task":task}), "再訪の順序を選べる"):
					return
			"gate":
				var team: Array = []
				for actor in main.game.export_state()["party"]:
					if team.size() < 3:
						team.append(actor["id"])
				if not gate_checked:
					gate_checked = true
					var before: Dictionary = main.game.export_state()
					if not _check(not main.submit_player_action({"kind":"operate_gate","team":[]}) and main.game.export_state() == before, "担当不足では回収もMP消費も起こらない"):
						return
					await _capture(main,"gate_requirements")
					main.submit_player_action({"kind":"party"})
					for identifier in team:
						for actor in main.game.export_state()["party"]:
							if actor["id"] == identifier:
								for skill in actor["equipped_abilities"]:
									main.game.unequip_ability(identifier,skill)
						main.game.equip_ability(identifier,"firm_guard")
						main.game.equip_ability(identifier,"sound_wave")
					main.submit_player_action({"kind":"back"})
					main.game.unequip_ability(team[0],"sound_wave")
					before = main.game.export_state()
					if not _check(not main.submit_player_action({"kind":"operate_gate","team":team}) and main.game.export_state() == before, "一人の必要技を外すと古い成功判定が残らない"):
						return
					main.game.equip_ability(team[0],"sound_wave")
				gate_before = main.game.export_state()
				if not _check(main.submit_player_action({"kind":"operate_gate","team":team}), "現在の三人の装着で水門操作へ進む"):
					return
			_:
				_fail("未知の状態: " + serial)
				return
	_fail("最大操作数までに本編の結末へ到達しませんでした。")


func _prepare_loadout(main: Node) -> void:
	var desired := {"warrior":["power_strike","firm_guard"],"martial_artist":["double_strike","breath"],"priest":["heal","revive"],"mage":["fire","ice"]}
	for actor in main.game.export_state()["party"]:
		for identifier in desired.get(actor["job_id"],[]):
			if identifier in main.game.available_abilities(actor["id"]) and not identifier in actor["equipped_abilities"]:
				main.game.equip_ability(actor["id"],identifier)


func _choose_battle_action(main: Node, input: Dictionary) -> void:
	var encounter: BattleState = main.game.current_battle()
	var actor := encounter.actor_by_id(str(input["actor"]))
	if actor == null:
		return
	# 公開された行動予定から、自分の回復より先に致死量を受ける時は防御する。
	# 固定の勝利判定は変えず、通常画面で選べる入力だけを使う。
	if _incoming_before_action(encounter,actor) >= actor.hp:
		main.submit_player_action({"kind":"guard","actor":actor.id})
		return
	for identifier in actor.equipped:
		var ability: Dictionary = main.game.abilities[identifier]
		if actor.mp < int(ability["cost"]):
			continue
		var targets := encounter.targets_for(actor.id,BattleAction.Kind.ABILITY,identifier)
		if ability["kind"] == "revive" and not targets.is_empty():
			main.submit_player_action({"kind":"ability","actor":actor.id,"target":targets[0].id,"ability":identifier})
			return
		if ability["kind"] == "heal":
			for target in targets:
				if target.hp * 2 < target.max_hp:
					main.submit_player_action({"kind":"ability","actor":actor.id,"target":target.id,"ability":identifier})
					return
	for identifier in actor.equipped:
		var ability: Dictionary = main.game.abilities[identifier]
		if ability["kind"] in ["physical","magic"] and actor.mp >= int(ability["cost"]):
			main.submit_player_action({"kind":"ability","actor":actor.id,"target":input["enemy"],"ability":identifier})
			return
	main.submit_player_action({"kind":"attack","actor":actor.id,"target":input["enemy"]})


func _incoming_before_action(encounter: BattleState, actor: Combatant) -> int:
	var damage := 0
	for intent in encounter.enemy_intents():
		if intent["target"] != actor.id:
			continue
		var enemy := encounter.actor_by_id(intent["actor"])
		var ability: Dictionary = encounter.catalog.abilities.get(intent["ability"],{})
		if int(ability.get("priority",0)) <= 0 and (enemy.speed < actor.speed or (enemy.speed == actor.speed and enemy.id > actor.id)):
			continue
		match ability.get("kind","physical"):
			"physical":
				damage += BattleMath.physical(enemy.attack,actor.defense,int(ability.get("power",100)),1.0) * int(ability.get("hits",1))
			"magic":
				damage += BattleMath.magical(enemy.magic,actor.resistance,int(ability["power"]),str(ability["element"]) in actor.weaknesses,1.0)
	return damage


func _capture(main: Node, name: String) -> void:
	if not "--capture" in OS.get_cmdline_user_args() or _captured.has(name):
		return
	await process_frame
	await process_frame
	await process_frame
	# 非表示のウィンドウでも描画完了シグナルを無期限に待たない。
	RenderingServer.force_draw(false)
	RenderingServer.force_sync()
	_check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/story_"+name+".png") == OK,"実描画を保存する")
	_captured[name] = true
