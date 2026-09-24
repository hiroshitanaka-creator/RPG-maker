extends Control

enum Mode { MENU, FIELD, DIALOGUE, BATTLE, PARTY, COMPLETE, DEFEAT, ASSETS_MISSING, EROSION_CONFIRMATION, JOURNAL, VISITS, GATE, EXPLORATION, REVIEW, CHALLENGE, JOB_LORE, JOURNEYS, WORLD, WORLD_CHOICE, WORLD_ATLAS, JOURNEY_DEVICE, MECHANICS, RULE_UPGRADE }

var game: GameSession
var mode: Mode = Mode.MENU
var _diagnostics := RuntimeDiagnostics.new()
var _body: VBoxContainer
var _messages: Array[String] = []
var _message_index: int = 0
var _advance_after_dialogue: bool = false
var _notice: String = ""
var _battle_log: Array[String] = []
var _actor: String = ""
var _target_action: Dictionary = {}
var _party_index: int = 0
var _facing: int = 0
var _walk_frame: int = 0
var _textures: Dictionary = {}
var _last_move_ms: int = -1000
var _purify_actor: String = ""
var _risk_action: Dictionary = {}
var _risk_return_mode: Mode = Mode.FIELD
var _risk_preview: Array[Dictionary] = []
var _confirmed_erosion_actors: Array[String] = []
var _risk_bypass: bool = false
var _dialogue_return: Mode = Mode.FIELD
var _dialogue_past: bool = false
var _dialogue_summary: Array = []
var _party_return: Mode = Mode.FIELD
var _gate_team: Array = []
var _journal_return: Mode = Mode.FIELD
var _journal_index: int = 0
var _trail: Array[Dictionary] = []
var _trail_location: String = ""
var _replay: Array[Dictionary] = []
var _replay_index: int = 0
var _replay_timer: float = 0.0
var _replay_party: Array = []
var _replay_enemies: Array = []
var _review_return: Mode = Mode.MENU
var save_path: String = "user://save_v1.json"
var checkpoint_path: String = "user://battle_checkpoint_v1.json"
var _checkpoint: Dictionary = {}
var _checkpoint_error: String = ""
var _world_mover := WorldMovement.new()
var _world_atlas_texture: ImageTexture
var _world_motion_ms := -1000
var _long_support_actor: String = ""
var _mechanics_return: Mode = Mode.FIELD
var _tactic_actor: String = ""
var _tactic_ability: String = "__observe"
var _tactic_target: String = ""


func _ready() -> void:
	Engine.max_fps = 60
	# 自動検査は通常の冒険の保存領域から分離する。ゲームの挙動は共通。
	var qa_prefix := OS.get_environment("RPG_QA_SAVE_PREFIX")
	if not qa_prefix.is_empty() and qa_prefix.is_valid_filename():
		save_path = "user://qa_" + qa_prefix + "_save.json"
		checkpoint_path = "user://qa_" + qa_prefix + "_checkpoint.json"
	OS.add_logger(_diagnostics)
	game = GameSession.new()
	game.enable_recording("user://playthroughs" if qa_prefix.is_empty() else "user://qa_playthroughs/"+qa_prefix)
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "sans-serif"])
	var ui_theme := Theme.new()
	ui_theme.default_font = font
	ui_theme.default_font_size = 11
	ui_theme.set_color("font_color", "Label", Color("eef0f4"))
	ui_theme.set_color("default_color", "RichTextLabel", Color("eef0f4"))
	for state in ["normal", "hover", "pressed", "focus", "disabled"]:
		var box := StyleBoxFlat.new()
		box.bg_color = Color("26364c") if state in ["hover", "pressed"] else Color("152236")
		box.border_color = Color("d9bb76") if state in ["focus", "pressed"] else Color("4a5c73")
		box.set_border_width_all(1)
		box.set_corner_radius_all(2)
		box.content_margin_left = 5
		box.content_margin_right = 5
		box.content_margin_top = 3
		box.content_margin_bottom = 3
		ui_theme.set_stylebox(state, "Button", box)
		ui_theme.set_stylebox(state, "OptionButton", box)
	theme = ui_theme
	_refresh()


func _process(delta: float) -> void:
	if mode == Mode.WORLD and _world_mover.active():
		var previous := _world_mover.route.find(_world_mover.cell)
		var moved := _world_mover.advance(delta)
		for offset in range(1,moved+1):
			var next: Vector2i = _world_mover.route[previous+offset]
			var before_cell := WorldExpedition.point(game.overworld_state()["cell"])
			if not game.move_overworld(next):
				_world_mover.stop()
				break
			var direction := next-before_cell
			_facing = 1 if direction.x < 0 else 2 if direction.x > 0 else 3 if direction.y < 0 else 0
			_world_motion_ms = Time.get_ticks_msec()
			_walk_frame = (_walk_frame+1)%4
		if moved > 0:
			_refresh()
	if game != null and not game.export_state().is_empty():
		game.play_metrics.update_clock(str(Mode.keys()[mode]).to_lower(),int(_step().get("chapter",6)),get_window().has_focus())
		game.play_metrics.completed = game.story_complete()
		game.flush_recording(true)
	if not _replay.is_empty():
		_replay_timer -= delta
		if _replay_timer <= 0:
			_replay_index += 1
			_replay_timer = 0.35
			if _replay_index >= _replay.size():
				_replay.clear()
			_refresh()
	if mode == Mode.FIELD and _walk_frame != 0 and Time.get_ticks_msec()-_last_move_ms > 180:
		_walk_frame = 0
		_refresh()
	if mode == Mode.WORLD and not _world_mover.active() and _walk_frame != 0 and Time.get_ticks_msec()-_world_motion_ms > 180:
		_walk_frame = 0
		_refresh()


func _exit_tree() -> void:
	if game != null:
		game.flush_recording()
	if game != null and game.party_defeated() and recovery_available():
		_persist_checkpoint()
	if game != null and not game.export_state().is_empty() and game.play_metrics.source != "unclassified":
		game.save_playtest_report("user://playtest-"+game.play_metrics.source+"-latest.json")
	if game != null:
		game.close_recording()
	OS.remove_logger(_diagnostics)


func _input(event: InputEvent) -> void:
	if (event is InputEventKey or event is InputEventMouseButton) and event.pressed and game != null:
		game.play_metrics.touch()
	if not _replay.is_empty() and event is InputEventKey and event.pressed and event.keycode in [KEY_ENTER,KEY_SPACE,KEY_E]:
		submit_player_action({"kind":"skip_presentation"})
		get_viewport().set_input_as_handled()
		return
	if not event is InputEventKey or not event.pressed:
		return
	if mode == Mode.WORLD:
		var movement := Vector2i.ZERO
		match event.keycode:
			KEY_LEFT, KEY_A: movement = Vector2i.LEFT
			KEY_RIGHT, KEY_D: movement = Vector2i.RIGHT
			KEY_UP, KEY_W: movement = Vector2i.UP
			KEY_DOWN, KEY_S: movement = Vector2i.DOWN
			KEY_ENTER, KEY_SPACE, KEY_E:
				submit_player_action({"kind":"world_interact"})
				get_viewport().set_input_as_handled()
				return
		if movement != Vector2i.ZERO:
			submit_player_action({"kind":"world_move","dx":movement.x,"dy":movement.y})
			get_viewport().set_input_as_handled()
		return
	if mode == Mode.DIALOGUE and event.keycode in [KEY_ENTER, KEY_SPACE, KEY_E]:
		submit_player_action({"kind":"confirm"})
		get_viewport().set_input_as_handled()
	elif mode == Mode.FIELD:
		var delta := Vector2i.ZERO
		match event.keycode:
			KEY_LEFT, KEY_A: delta = Vector2i.LEFT
			KEY_RIGHT, KEY_D: delta = Vector2i.RIGHT
			KEY_UP, KEY_W: delta = Vector2i.UP
			KEY_DOWN, KEY_S: delta = Vector2i.DOWN
			KEY_ENTER, KEY_SPACE, KEY_E:
				submit_player_action({"kind":"interact"})
				get_viewport().set_input_as_handled()
				return
		if delta != Vector2i.ZERO:
			submit_player_action({"kind":"move", "dx":delta.x, "dy":delta.y})
			get_viewport().set_input_as_handled()


func start_new_game(party_size: int = 4) -> void:
	_world_mover.stop()
	var previous_source: String = game.play_metrics.source
	if not game.new_game(party_size):
		_notice = "ゲームを開始できません。" + "\n".join(game.errors)
		_refresh()
		return
	_risk_action.clear()
	_checkpoint.clear()
	_checkpoint_error = ""
	_trail.clear()
	_replay.clear()
	_trail_location = ""
	if "--human-playtest" in OS.get_cmdline_user_args():
		game.play_metrics.set_source("human")
	elif "--automated-playtest" in OS.get_cmdline_user_args():
		game.play_metrics.set_source("automated")
	elif previous_source in ["human","automated"]:
		game.play_metrics.set_source(previous_source)
	_risk_preview.clear()
	_confirmed_erosion_actors.clear()
	_risk_bypass = false
	_gate_team = []
	_journal_index = 0
	_party_return = Mode.FIELD
	_journal_return = Mode.FIELD
	if not ChapterOne.missing_art().is_empty():
		mode = Mode.ASSETS_MISSING
		_notice = "必要な素材が揃うと探索を開始できます。"
		print("ASSET_INPUT_REQUIRED: " + ", ".join(ChapterOne.missing_art()))
	else:
		mode = Mode.FIELD
		_notice = "矢印 / WASDで移動。黄色の印でEnterまたは『調べる』。"
	_refresh()


func _step() -> Dictionary:
	return game.current_story_step()


func automation_snapshot() -> Dictionary:
	var saved := game.export_state()
	var diagnostics := _diagnostics.messages()
	var names := {Mode.MENU:"menu", Mode.FIELD:"field", Mode.DIALOGUE:"dialogue", Mode.BATTLE:"battle", Mode.PARTY:"party", Mode.COMPLETE:"complete", Mode.DEFEAT:"defeat", Mode.ASSETS_MISSING:"assets_missing"}
	names[Mode.EROSION_CONFIRMATION] = "erosion_confirmation"
	names[Mode.JOURNAL] = "journal"
	names[Mode.VISITS] = "visits"
	names[Mode.GATE] = "gate"
	names[Mode.EXPLORATION] = "exploration"
	names[Mode.REVIEW] = "review"
	names[Mode.CHALLENGE] = "challenge"
	names[Mode.JOB_LORE] = "job_lore"
	names[Mode.JOURNEYS] = "journeys"
	names[Mode.JOURNEY_DEVICE] = "journey_device"
	names[Mode.MECHANICS]="mechanics"
	names[Mode.RULE_UPGRADE]="rule_upgrade"
	names[Mode.WORLD] = "world"
	names[Mode.WORLD_CHOICE] = "world_choice"
	names[Mode.WORLD_ATLAS] = "world_atlas"
	var result := {"mode": "error" if not diagnostics.is_empty() else names[mode],
		"chapter1_cleared": diagnostics.is_empty() and saved.get("progress_flags", {}).get("chapter1_cleared", false)}
	result["story_complete"] = diagnostics.is_empty() and game.story_complete()
	result["quest_step"] = game.world_state().get("quest_step",0)
	result["chapter"] = int(_step().get("chapter",6 if game.story_complete() else 1))
	result["battle_wave"] = game.story_wave_index()
	result["section"] = game.world_state().get("section","")
	if game.world_exploration_active():
		result["overworld"] = game.overworld_state()
	if not diagnostics.is_empty():
		result["errors"] = diagnostics
		return result
	if mode == Mode.FIELD:
		var world := game.world_state()
		result["player_cell"] = world["player_cell"]
		result["objective_cell"] = [5,4] if game.is_returning_to_town() else _step().get("cell", world["player_cell"])
		result["walkable_cells"] = game.world_walkable_cells()
		result["exploration_sites"] = game.exploration_sites()
	elif mode == Mode.BATTLE:
		var encounter := game.current_battle()
		var pending := encounter.pending()
		var targets := encounter.living(Combatant.Team.ENEMY)
		result["battle_input"] = {"ready": encounter.can_resolve(), "actor": "" if pending.is_empty() else pending[0].id, "enemy": "" if targets.is_empty() else targets[0].id}
	elif mode == Mode.DIALOGUE:
		result["line"] = _message_index
	elif mode == Mode.EROSION_CONFIRMATION:
		result["risk"] = _risk_preview.duplicate(true)
	return result


func submit_player_action(action: Dictionary) -> bool:
	var kind: String = str(action.get("kind", ""))
	if kind == "open_world" and mode in [Mode.MENU,Mode.FIELD]:
		if not game.open_world_exploration():
			return false
		_world_mover.stop()
		mode = Mode.WORLD
		_notice = "全図で行き先を確認できます。入口の上で『調べる』。"
		_refresh()
		return true
	game.play_metrics.touch()
	if not _replay.is_empty():
		_replay.clear()
		if kind == "skip_presentation":
			_refresh()
			return true
	if kind=="mechanics" and mode in [Mode.FIELD,Mode.PARTY,Mode.BATTLE]:
		_mechanics_return=mode;mode=Mode.MECHANICS;_refresh();return true
	if mode==Mode.MECHANICS:
		if kind=="back":mode=_mechanics_return;_refresh();return true
		if kind=="reserve_tactic" and game.current_battle()!=null:
			var command: Dictionary={"kind":"observe" if _tactic_ability=="__observe" else "ability","actor":_tactic_actor,"ability":_tactic_ability,"target":_tactic_target}
			var accepted:=_battle_action(command)
			if accepted:mode=Mode.BATTLE
			_refresh();return accepted
	if kind=="preview_rule_upgrade" and mode==Mode.PARTY:
		mode=Mode.RULE_UPGRADE;_refresh();return true
	if mode==Mode.RULE_UPGRADE:
		if kind=="back":mode=Mode.PARTY;_refresh();return true
		if kind=="confirm_rule_upgrade":
			var changed:=game.upgrade_rules()
			mode=Mode.PARTY;_notice="新しいルールへ引き継ぎました。" if changed else "更新できませんでした。"
			_refresh();return changed
	if kind == "review" and mode in [Mode.MENU,Mode.FIELD,Mode.COMPLETE]:
		_review_return = mode
		mode = Mode.REVIEW
		_refresh()
		return true
	if kind == "retry_battle" and mode == Mode.DEFEAT:
		return _retry_battle()
	if kind == "load_checkpoint" and mode in [Mode.MENU,Mode.DEFEAT]:
		return _load_checkpoint()
	if mode == Mode.EROSION_CONFIRMATION:
		return _respond_to_erosion(kind)
	if not _risk_bypass and _request_erosion_confirmation(action):
		return true
	var accepted := false
	match mode:
		Mode.JOURNEY_DEVICE:
			if kind == "back":
				mode = Mode.FIELD
				accepted = true
			elif kind == "party":
				_party_return = Mode.JOURNEY_DEVICE
				mode = Mode.PARTY
				accepted = true
			elif kind == "long_device_answer":
				var activity := game.long_activity()
				if game.complete_long_activity(int(action.get("option",-1)),_long_support_actor):
					_show_dialogue([activity["resolution"],"MPを使って近道を残した。" if not _long_support_actor.is_empty() else "MPを温存して手順を終えた。"],false)
				else:
					_notice = "二つの観察と装着・MPを確認してください。進行と報酬は変わっていません。"
				accepted = true
		Mode.WORLD, Mode.WORLD_CHOICE, Mode.WORLD_ATLAS:
			accepted = _world_action(action)
		Mode.FIELD:
			if kind == "move":
				if Time.get_ticks_msec()-_last_move_ms < 150:
					return false
				var dx := int(action.get("dx", 0))
				var dy := int(action.get("dy", 0))
				if absi(dx) + absi(dy) != 1:
					return false
				var world := game.world_state()
				var next := Vector2i(int(world["player_cell"][0])+dx, int(world["player_cell"][1])+dy)
				accepted = game.set_world(world["location"], [next.x,next.y], world["quest_step"],world.get("section",""))
				if accepted:
					var trail_key: String = world["location"]+":"+str(world.get("section",""))
					if _trail_location != trail_key:
						_trail.clear()
					_trail_location = trail_key
					_trail.push_front({"cell":world["player_cell"].duplicate(),"facing":_facing})
					if _trail.size() > 3:
						_trail.pop_back()
					game.play_metrics.mark("moved_cells")
					_last_move_ms = Time.get_ticks_msec()
					_facing = 1 if dx < 0 else (2 if dx > 0 else (3 if dy < 0 else 0))
					_walk_frame = (_walk_frame+1) % 4
					_notice = ""
			elif kind == "interact":
				accepted = _interact()
			elif kind == "party":
				_party_return = Mode.FIELD
				mode = Mode.PARTY
				accepted = true
			elif kind == "journal":
				_journal_return = Mode.FIELD
				mode = Mode.JOURNAL
				accepted = true
			elif kind == "save":
				accepted = game.save_game(save_path)
				_notice = "保存しました。" if accepted else "今は保存できません。"
			elif kind == "rest" and game.world_state()["location"] in ChapterOne.TOWNS:
				accepted = game.rest()
				_notice = "宿でHPとMPを回復しました。"
			elif kind == "return_to_town":
				accepted = game.return_to_town()
				_notice = "町へ帰還しました。休息・転職・祠での解除後、探索位置へ戻れます。" if accepted else "今は帰還できません。"
			elif kind == "resume_exploration":
				accepted = game.resume_exploration()
				_notice = "帰還前の探索位置へ戻りました。" if accepted else "戻る探索位置がありません。"
			elif kind == "field_battle":
				var encounter := _start_encounter(false)
				if encounter != null:
					if not _risk_bypass:
						_confirmed_erosion_actors.clear()
					mode = Mode.BATTLE
					_battle_log = ["周辺の魔物と戦う。勝利で現在の職業にJPが入る。"]
					_add_erosion_lines()
					_actor = encounter.pending()[0].id
					_target_action.clear()
					_notice = ""
					accepted = true
		Mode.DIALOGUE:
			if kind == "summary" and not _dialogue_summary.is_empty():
				_messages.assign(_dialogue_summary)
				_dialogue_summary = []
				_message_index = 0
				accepted = true
			elif kind == "confirm":
				_message_index += 1
				accepted = true
				if _message_index >= _messages.size():
					if _advance_after_dialogue:
						_advance_step()
					mode = _dialogue_return
		Mode.BATTLE:
			accepted = _battle_action(action)
		Mode.PARTY:
			if kind == "back":
				_purify_actor = ""
				mode = _party_return
				accepted = true
			elif kind == "choose_job":
				accepted = game.choose_job(str(action.get("actor","")),str(action.get("job","")))
				_notice = "転職しました。装着済みの技は持ち越します。" if accepted else "その職はまだ選べません。町の噂と魔物図鑑で手掛かりを探せます。"
				_refresh()
			elif kind == "job_lore":
				game.read_job_lore()
				mode = Mode.JOB_LORE
				accepted = true
			elif kind == "set_leader":
				accepted = game.set_party_leader(str(action.get("actor","")))
				if accepted:
					_trail.clear()
			elif kind == "request_purify":
				accepted = _request_purify(str(action.get("actor", "")))
			elif kind == "cancel_purify" and not _purify_actor.is_empty():
				_purify_actor = ""
				accepted = true
			elif kind == "confirm_purify" and not _purify_actor.is_empty():
				accepted = game.world_state()["location"] == "town" and game.release_monster_form(_purify_actor, "purification_shrine")
				_notice = "魔物の技を手放し、姿を戻しました。" if accepted else "解除条件を満たしていません。"
				_purify_actor = ""
		Mode.COMPLETE:
			if kind == "save":
				accepted = game.save_game(save_path)
				_notice = "保存しました。" if accepted else "保存できませんでした。"
			elif kind == "continue_story":
				accepted = game.continue_story()
				if accepted:
					mode = Mode.FIELD
					_notice = "町の記録室で、番人の来歴を確かめよう。"
					_show_dialogue(["通路の入口で振り返る。番人の首の札に、水番の符号が見えた。町の勤務記録で確かめよう。"],false)
			elif kind == "journal":
				_journal_return = Mode.COMPLETE
				mode = Mode.JOURNAL
				accepted = true
		Mode.JOURNAL:
			if kind == "back":
				mode = _journal_return
				accepted = true
			elif kind == "replay":
				for record in game.replayable_records():
					if record["id"] == action.get("event"):
						_show_dialogue(record["text"],false,Mode.JOURNAL,true)
						accepted = true
		Mode.JOB_LORE:
			if kind == "back":
				mode = Mode.PARTY
				accepted = true
		Mode.VISITS:
			if kind == "visit_task":
				accepted = game.start_revisit_task(str(action.get("task", "")))
				if accepted:
					mode = Mode.FIELD
			elif kind == "back":
				mode = Mode.FIELD
				accepted = true
		Mode.GATE:
			if kind == "gate_team":
				_gate_team = action.get("team",[]).duplicate()
				accepted = true
			elif kind == "operate_gate":
				_gate_team = action.get("team",_gate_team).duplicate()
				var reasons := game.gate_requirements(_gate_team)
				if reasons.is_empty():
					_show_dialogue(game.story_lines(),true)
					accepted = true
				else:
					_notice = "担当・装着・生存・MPを確認してください。"
					_refresh()
			elif kind == "party":
				_party_return = Mode.GATE
				mode = Mode.PARTY
				accepted = true
			elif kind == "back":
				mode = Mode.FIELD
				accepted = true
		Mode.EXPLORATION:
			if kind == "back":
				mode = Mode.FIELD
				accepted = true
			elif kind == "party":
				_party_return = Mode.EXPLORATION
				mode = Mode.PARTY
				accepted = true
			elif kind == "use_site":
				accepted = game.use_exploration_site(str(action.get("actor","")),str(action.get("ability","")))
				if accepted:
					game.play_metrics.mark("exploration_rewards" if game.exploration_at_player()["kind"] == "cache" else "devices_opened")
					_notice = "補給を受け取りました。" if game.exploration_at_player()["kind"] == "cache" else "近道と補給箱が開きました。開通状態はセーブに残ります。"
		Mode.REVIEW:
			if kind == "back":
				mode = _review_return
				accepted = true
			elif kind == "set_playtest_source":
				accepted = game.play_metrics.set_source(str(action.get("source","")))
			elif kind == "submit_review":
				accepted = game.play_metrics.add_review(int(action.get("exploration",0)),int(action.get("reward",0)),int(action.get("difficulty",0)),str(action.get("note","")))
				_notice = "回答を記録しました。セーブまたはJSON保存で残せます。" if accepted else "人間の試遊を選び、3項目の評価を選択してください。"
			elif kind == "export_playtest":
				accepted = game.save_playtest_report()
				_notice = "試遊記録を保存しました: "+ProjectSettings.globalize_path("user://playtest-report.json") if accepted else "試遊記録を保存できませんでした。"
		Mode.CHALLENGE:
			if kind == "back":
				mode = Mode.FIELD
				accepted = true
			elif kind == "challenge_answer":
				var entry := _step()
				if game.answer_challenge(int(action.get("option",-1))):
					_notice = ""
					var reward:=int(entry["reward_potions"])
					if entry.has("choice_effects"):reward+=int(entry["choice_effects"][int(action["option"])].get("potion_bonus",0))
					_show_dialogue([entry["resolution"],"備蓄から回復薬%d個を受け取った。" % reward],false)
				else:
					_notice = "記録に書かれた条件と照らして、もう一度選べます。"
				accepted = true
		Mode.JOURNEYS:
			if kind=="back":
				mode=Mode.FIELD
				accepted=true
			elif kind=="begin_journey":
				accepted=game.begin_expedition(str(action.get("id","")))
				if accepted:mode=Mode.FIELD
	if accepted:
		_refresh()
	return accepted


func _request_erosion_confirmation(action: Dictionary) -> bool:
	var kind: String = action.get("kind", "")
	var check_start := mode == Mode.FIELD and kind == "field_battle" and not game.field_battle_enemies().is_empty()
	if mode == Mode.WORLD and kind == "world_interact":
		var state := game.overworld_state()
		var event := WorldExpedition.event_at(state)
		check_start = event.get("kind") == "battle" and not WorldExpedition.done(state,event["id"]) and WorldExpedition.ready(state,event)
	if mode == Mode.FIELD and kind == "interact":
		var world := game.world_state()
		var step := _step()
		check_start = not game.is_returning_to_town() and step.get("kind") == "battle" and not game.story_battle_cleared() and world["location"] == step.get("location") and world["player_cell"] == step.get("cell")
	var check_round := mode == Mode.BATTLE and kind == "resolve_round" and game.current_battle().can_resolve()
	if not check_start and not check_round:
		return false
	var risk: Array[Dictionary] = []
	for entry in game.erosion_preview(check_round):
		if entry["crosses_irreversible"] and (check_start or not entry["actor"] in _confirmed_erosion_actors):
			risk.append(entry)
	if check_start:risk.append_array(game.mastery_forecast(kind=="field_battle"))
	if risk.is_empty():
		return false
	_risk_action = action.duplicate(true)
	_risk_preview = risk
	_risk_return_mode = mode
	mode = Mode.EROSION_CONFIRMATION
	_refresh()
	return true


func _respond_to_erosion(kind: String) -> bool:
	if kind not in ["cancel_erosion", "confirm_erosion"]:
		return false
	var pending := _risk_action.duplicate(true)
	mode = _risk_return_mode
	if kind == "confirm_erosion":
		if mode in [Mode.FIELD,Mode.WORLD]:
			_confirmed_erosion_actors.clear()
		for entry in _risk_preview:
			if not entry["actor"] in _confirmed_erosion_actors:
				_confirmed_erosion_actors.append(entry["actor"])
	_risk_action.clear()
	_risk_preview.clear()
	if kind == "cancel_erosion":
		_refresh()
		return true
	_risk_bypass = true
	var accepted := submit_player_action(pending)
	_risk_bypass = false
	return accepted


func _interact() -> bool:
	var step := _step()
	var world := game.world_state()
	if not game.integrated_observation().is_empty():
		_show_dialogue(game.read_integrated_observation(),false)
		return true
	var activity := game.long_activity_at_player()
	if not activity.is_empty():
		if activity["observation"] >= 0:
			_show_dialogue(game.read_long_observation(),false)
		elif activity["complete"]:
			_show_dialogue(["この作業は完了しています。黄色の目的地で判断を伝えられます。"],false)
		else:
			_long_support_actor = ""
			mode = Mode.JOURNEY_DEVICE
		return true
	if step.has("required_activity") and not game.export_state()["progress_flags"].get(LongCampaign.activity_flag(step["required_activity"],"done"),false):
		_notice = "先に緑の観察記録を二つ調べ、青い操作台で作業を終えてください。"
		_refresh()
		return false
	if not game.exploration_at_player().is_empty():
		mode = Mode.EXPLORATION
		_notice = ""
		return true
	if game.is_returning_to_town():
		_show_dialogue(["町で休息と編成を整えられる。『探索へ戻る』で帰還前の位置へ戻ろう。"], false)
		return true
	if step.is_empty() or world["location"] != step["location"] or world["player_cell"] != step["cell"]:
		_notice = "黄色の印へ移動して調べてください。"
		_refresh()
		return false
	match step["kind"]:
		"expedition":
			if not game.long_missions().is_empty():
				mode=Mode.JOURNEYS
				return true
			return game.begin_expedition(step["expedition_id"])
		"section_travel", "circuit_complete":
			return game.advance_story_step()
		"challenge":
			mode = Mode.CHALLENGE
		"dialogue":
			var lines := game.story_lines(step)
			if lines.is_empty():
				_notice = "先に手帳の手掛かりと記録を確かめてください。"
				return false
			if step.get("rest", false):
				game.rest()
			_show_dialogue(lines, true, Mode.FIELD, bool(step.get("past",false)) or StoryCampaign.event(step.get("event", "")).get("past", false))
		"travel":
			return game.advance_story_step()
		"battle":
			if game.story_battle_cleared():
				_show_dialogue(step.get("text",["この場所の魔物は退けた。先へ進もう。"]),true)
				return true
			var encounter := _start_encounter(true)
			if encounter == null:
				return false
			if not _risk_bypass:
				_confirmed_erosion_actors.clear()
			mode = Mode.BATTLE
			_battle_log = ["相手の特徴と残りHPを見て、行動を選ぼう。"]
			_add_erosion_lines()
			_actor = encounter.pending()[0].id
			_target_action.clear()
		"complete":
			if not game.advance_story_step():
				return false
			mode = Mode.COMPLETE
		"story_complete":
			if not game.advance_story_step():
				_notice = "回収していない手掛かりが残っています。"
				return false
			mode = Mode.COMPLETE
		"choice":
			if game.advance_story_step():
				return true
			mode = Mode.VISITS
		"gate":
			if _gate_team.is_empty():
				for actor in game.export_state()["party"]:
					if _gate_team.size() < 3 and actor["hp"] > 0:
						_gate_team.append(actor["id"])
			mode = Mode.GATE
	return true


func _advance_step() -> void:
	if not game.advance_story_step(_gate_team):
		_notice = "進行条件がそろっていません。手帳と装着を確認してください。"


func _show_dialogue(lines: Array, advance: bool, return_mode: Mode = Mode.FIELD, past: bool = false) -> void:
	_messages.assign(lines)
	_message_index = 0
	_advance_after_dialogue = advance
	_dialogue_return = return_mode
	_dialogue_past = past
	_dialogue_summary = StoryCampaign.event(_step().get("event", "")).get("summary", []).duplicate() if advance else []
	if advance and _dialogue_summary.is_empty():
		var short_lines: Array[String] = []
		for line in lines:
			var sentences := str(line).split("。",false)
			short_lines.append(str(line) if str(line).length() <= 120 or sentences.size() <= 2 else sentences[0]+"。"+sentences[-1]+"。")
		_dialogue_summary = ["\n".join(short_lines)]
	mode = Mode.DIALOGUE


func _battle_action(action: Dictionary) -> bool:
	var encounter := game.current_battle()
	var kind: String = str(action.get("kind", ""))
	if kind == "resolve_round":
		if not encounter.can_resolve():
			return false
		var story_battle := not game.is_field_battle()
		var world_battle := game.is_world_battle()
		_replay_party = game.export_state()["party"].duplicate(true)
		_replay_enemies = game.current_enemy_ids().duplicate()
		var events := encounter.resolve_round()
		game.play_metrics.mark("battle_rounds")
		_replay.clear()
		_replay_index = 0
		_replay_timer = 0.35
		for event in events:
			_battle_log.append(event["message"])
			if event["code"] in ["damage","heal","guard","revive","steal","fallen"]:
				_replay.append(event.duplicate(true))
		_target_action.clear()
		if encounter.phase == BattleState.Phase.VICTORY:
			game.play_metrics.mark("battles_won")
			var before := game.export_state()
			game.finish_battle()
			var lines: Array = ["勝利！"]
			var after := game.export_state()
			if after.has("integrated"):
				if after["integrated"]["claimed"].size()>before["integrated"]["claimed"].size():lines.append("場を止めて補給箱へ手が届いた。回復薬を2個受け取った。")
				for id in after["integrated"]["armory"]:
					if id not in before["integrated"]["armory"]:lines.append("機構の扱いを確認し、『%s』の貸与が解放された。編成で持ち替えられる。" % IntegratedProgression.weapon(id)["name"])
				for flag in after["progress_flags"]:
					if str(flag).begins_with("integration_route_") and not before["progress_flags"].get(flag,false):lines.append("機構の扱いを通路に応用した。この区画の東側の近道が開いた。")
			for i in range(after["party"].size()):
				var actor: Dictionary = after["party"][i]
				var job_id: String = before["party"][i]["job_id"]
				var gain := int(actor["jp"].get(job_id, 0))-int(before["party"][i]["jp"].get(job_id, 0))
				lines.append("%s: %sのJP +%d" % [actor["name"],game.jobs[job_id]["name"],gain])
				if actor.has("integrated"):
					var old_growth: Dictionary=before["party"][i]["integrated"]
					lines.append("EXP +%d / Lv%d→%d" % [actor["integrated"]["exp"]-old_growth["exp"],old_growth["level"],actor["integrated"]["level"]])
				if actor["mastered_jobs"].size() > before["party"][i]["mastered_jobs"].size():
					lines.append("%sが%sをマスター。" % [actor["name"], game.jobs[job_id]["name"]])
				for id in actor["unlocked_jobs"]:
					if id not in before["party"][i]["unlocked_jobs"]:lines.append("%sは%sへ転職できるようになった。" % [actor["name"],game.jobs[id]["name"]])
				for ability_id in actor["learned_abilities"]:
					if not ability_id in before["party"][i]["learned_abilities"]:
						lines.append("%sが『%s』を習得。編成で装着すると使える。" % [actor["name"], game.abilities[ability_id]["name"]])
				if actor["monster_form"] != before["party"][i]["monster_form"]:
					lines.append("%sが魔物化した。能力と使用可能な技、装着枠が変化した。" % actor["name"])
				var old_erosion := IntegratedProgression.erosion_tenths(before["party"][i])/10.0
				var new_erosion := IntegratedProgression.erosion_tenths(actor)/10.0
				if old_erosion != new_erosion:
					lines.append("%sの侵蝕 %.1f→%.1f（%s）" % [actor["name"], old_erosion, new_erosion, GameSession.erosion_stage(int(new_erosion))])
				if actor["job_id"] != job_id:
					lines.append("侵蝕90に達し、%sは%sへ移った。人間職へ戻ることと祠での解除はできない。" % [actor["name"], game.jobs[actor["job_id"]]["name"]])
			if story_battle:
				if game.story_battle_cleared():
					lines.append_array(_step().get("text", []))
				else:
					lines.append("%d/%d戦を終えた。帰還・編成・保存を済ませてから、同じ地点で次の敵へ進める。" % [game.story_wave_index(),game.story_wave_count()])
			_show_dialogue(lines, story_battle and game.story_battle_cleared(), Mode.WORLD if world_battle else Mode.FIELD)
		elif encounter.phase == BattleState.Phase.DEFEAT:
			game.play_metrics.mark("battles_lost")
			game.finish_battle()
			# 再起動後も敗北・消費時間を失わず、進行だけ戦闘前から再開できる。
			_persist_checkpoint()
			mode = Mode.DEFEAT
		else:
			_actor = encounter.pending()[0].id
		return true
	if kind == "clear_actions":
		encounter.clear_queue()
		_actor = encounter.pending()[0].id
		_target_action.clear()
		return true
	var actor_id: String = str(action.get("actor", ""))
	var target_id: String = str(action.get("target", ""))
	var command: BattleAction
	match kind:
		"attack": command = BattleAction.strike(actor_id, target_id)
		"guard": command = BattleAction.guard(actor_id)
		"ability": command = BattleAction.skill(actor_id, target_id, str(action.get("ability", "")))
		"potion": command = BattleAction.potion(actor_id, target_id)
		"observe": command = BattleAction.observe(actor_id,target_id)
		_: return false
	var error := encounter.queue_action(command)
	if not error.is_empty():
		_notice = error
		return false
	var pending := encounter.pending()
	_actor = "" if pending.is_empty() else pending[0].id
	_target_action.clear()
	return true


func _refresh() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_"+side, 6)
	add_child(margin)
	_body = VBoxContainer.new()
	_body.add_theme_constant_override("separation", 3)
	margin.add_child(_body)
	var header := HBoxContainer.new()
	_body.add_child(header)
	var title := _label("RPG-maker", 15)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var saved := game.export_state()
	if not saved.is_empty():
		var values: Array[String] = []
		for actor in saved["party"]:
			values.append(str(game.current_erosion(actor["id"])))
		header.add_child(_label("侵蝕 " + " / ".join(values), 10))
	match mode:
		Mode.JOURNEY_DEVICE: _render_long_device()
		Mode.MECHANICS: _render_mechanics()
		Mode.RULE_UPGRADE: _render_rule_upgrade()
		Mode.WORLD: _render_world()
		Mode.WORLD_CHOICE: _render_world_choice()
		Mode.WORLD_ATLAS: _render_world_atlas()
		Mode.MENU: _render_menu()
		Mode.ASSETS_MISSING: _render_missing()
		Mode.FIELD: _render_field()
		Mode.DIALOGUE: _render_dialogue()
		Mode.BATTLE: _render_battle()
		Mode.PARTY: _render_party()
		Mode.JOURNAL: _render_journal()
		Mode.VISITS: _render_visits()
		Mode.GATE: _render_gate()
		Mode.EXPLORATION: _render_exploration()
		Mode.REVIEW: _render_review()
		Mode.CHALLENGE: _render_challenge()
		Mode.JOURNEYS: _render_journeys()
		Mode.JOB_LORE: _render_job_lore()
		Mode.EROSION_CONFIRMATION: _render_erosion_confirmation()
		Mode.COMPLETE: _render_complete()
		Mode.DEFEAT:
			_body.add_child(_label("全員が戦闘不能になった。", 16))
			var retry := _action_button(_body,"戦闘前へ戻る",{"kind":"retry_battle"})
			retry.disabled = not recovery_available()
			var help := _label("戦闘前のHP・MP・薬・装着・侵蝕へ戻ります。\n戻った後は編成や町への帰還を選べます。\n試遊の全滅回数と経過時間は残ります。",11)
			help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			_body.add_child(help)
			_button(_body, "手動セーブから再開", _load_save)
			_button(_body, "タイトルへ", _to_menu)
	if not _notice.is_empty() and mode != Mode.BATTLE:
		var notice := _label(_notice,10)
		notice.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_body.add_child(notice)
	if not _checkpoint_error.is_empty() and mode != Mode.BATTLE:
		var warning := _label(_checkpoint_error,10)
		warning.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_body.add_child(warning)
	if not _replay.is_empty():
		_render_presentation()


func _render_menu() -> void:
	_body.add_child(_label("職を選び、技を組み、自分の姿を決める。", 13))
	_body.add_child(_label("第1章  閉じた道", 16))
	if not game.export_state().is_empty():
		var row := HBoxContainer.new()
		_body.add_child(row)
		_button(row, "現在の冒険に戻る", _resume_current)
		var world_button := _action_button(row,"世界地図へ",{"kind":"open_world"})
		world_button.disabled = game.world_state().get("location","") not in ChapterOne.TOWNS
	_button(_body, "新しくはじめる（4人）", start_new_game.bind(4))
	_button(_body, "新しくはじめる（3人）", start_new_game.bind(3))
	_button(_body, "手動セーブから再開", _load_save)
	var checkpoint := _action_button(_body,"自動保存した戦闘前から再開",{"kind":"load_checkpoint"})
	checkpoint.disabled = not FileAccess.file_exists(checkpoint_path)
	checkpoint.tooltip_text = "直近の戦闘開始時の位置と編成へ戻ります。手動セーブとは別の記録です。"
	_action_button(_body,"試遊の記録と評価",{"kind":"review"})
	_button(_body, "終了", func() -> void: get_tree().quit())
	if not game.errors.is_empty():
		_body.add_child(_label("\n".join(game.errors), 10))
	var missing := ChapterOne.missing_art()
	if not missing.is_empty():
		_body.add_child(_label("開始に必要な素材が未取込: %d件" % missing.size(), 10))


func _resume_current() -> void:
	mode = Mode.COMPLETE if game.chapter_one_pause() or game.story_complete() else Mode.FIELD
	if game.world_exploration_active():
		mode = Mode.WORLD
	if game.party_defeated():
		mode = Mode.DEFEAT
	if not ChapterOne.missing_art().is_empty():
		mode = Mode.ASSETS_MISSING
	_notice = ""
	_refresh()


func _render_missing() -> void:
	_body.add_child(_label("画像素材の取り込みを待っています。", 14))
	var list := RichTextLabel.new()
	list.text = "\n".join(ChapterOne.missing_art())
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(list)
	_button(_body, "タイトルへ", _to_menu)


func _render_field() -> void:
	var world := game.world_state()
	var objective: String = "休息・編成後、探索へ戻る" if game.is_returning_to_town() else _step().get("objective", "町を歩く")
	if not game.is_returning_to_town() and game.story_wave_count() > 1:
		objective += "（%d/%d戦終了）" % [game.story_wave_index(),game.story_wave_count()]
	var place: String = ChapterOne.TITLES[world["location"]]
	if not str(world.get("section","")).is_empty():
		place += "・"+CampaignContent.section(world["section"])["title"]
	var heading := _label("第%d章 %s / %s" % [int(_step().get("chapter",1)),place,objective], 11)
	heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(heading)
	var map := WorldView.new()
	map.location = world["location"]
	map.section_id = world.get("section","")
	map.player_cell = Vector2i(int(world["player_cell"][0]), int(world["player_cell"][1]))
	var goal: Array = [5,4] if game.is_returning_to_town() else _step().get("cell", world["player_cell"])
	map.objective = Vector2i(int(goal[0]), int(goal[1]))
	map.facing = _facing
	map.walk_frame = _walk_frame
	map.progress_flags = game.export_state()["progress_flags"]
	map.sites = game.exploration_sites()
	map.members = game.walking_party()
	if _trail_location == world["location"]+":"+str(world.get("section","")):
		map.trail = _trail.duplicate(true)
	map.custom_minimum_size = Vector2(480, 160)
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map.cell_clicked.connect(_map_clicked)
	_body.add_child(map)
	if not map.sites.is_empty():
		_body.add_child(_label("緑: 観察 / 青: 操作台。二つの記録を読んで調べる。" if not game.long_activity().is_empty() else "青い枠: 設備 / 緑の箱: 補給 / 灰色: 利用済み。上に立って調べる。",9))
	var row := HBoxContainer.new()
	_body.add_child(row)
	_action_button(row, "調べる", {"kind":"interact"})
	_action_button(row, "編成", {"kind":"party"})
	_action_button(row, "手帳", {"kind":"journal"})
	_action_button(row,"記録",{"kind":"review"})
	_action_button(row, "セーブ", {"kind":"save"})
	if world["location"] in ChapterOne.TOWNS:
		_action_button(row, "宿で休む", {"kind":"rest"})
		if game.is_returning_to_town():
			_action_button(row, "探索へ戻る", {"kind":"resume_exploration"})
	else:
		_action_button(row, "町へ帰還", {"kind":"return_to_town"})
	if not game.field_battle_enemies().is_empty():
		_action_button(row, "周辺で戦う", {"kind":"field_battle"})
	_button(row, "メニュー", _to_menu)


func _map_clicked(cell: Vector2i) -> void:
	var current: Array = game.world_state()["player_cell"]
	if cell == Vector2i(int(current[0]), int(current[1])):
		submit_player_action({"kind":"interact"})
	else:
		submit_player_action({"kind":"move", "dx":cell.x-int(current[0]), "dy":cell.y-int(current[1])})


func _world_action(action: Dictionary) -> bool:
	var kind: String = action.get("kind","")
	var state := game.overworld_state()
	if not game.world_exploration_active():
		return false
	if kind == "back" and mode in [Mode.WORLD_CHOICE,Mode.WORLD_ATLAS]:
		mode = Mode.WORLD
		return true
	if kind == "world_choose" and mode == Mode.WORLD_CHOICE:
		var result := game.choose_world_option(int(action.get("option",-1)))
		if result.is_empty():
			return false
		_show_dialogue(result["text"],false,Mode.WORLD)
		return true
	if kind == "world_target" and mode in [Mode.WORLD,Mode.WORLD_ATLAS] and state["layer"] == "world":
		var target: Vector2i
		if action.has("node"):
			if not WorldExpedition.unlocked(str(action["node"]),state["flags"]):
				_notice = "まだ入れません。先に道や乗り物を整えてください。"
				return false
			target = WorldTerrain.cell_of(str(action["node"]))
		else:
			target = Vector2i(int(action.get("x",-1)),int(action.get("y",-1)))
		var route := WorldTerrain.path(WorldExpedition.point(state["cell"]),target,state["transport"])
		if route.is_empty():
			_notice = "現在の移動手段では届きません。船は青い点の船着場で切り替えられます。"
			_refresh()
			return false
		_world_mover.begin(route,state["transport"])
		mode = Mode.WORLD
		_notice = "現在地です。『調べる』で入れます。" if route.size() == 1 else "移動中。別の方向キーか『調べる』で進路を変えられます。"
		return true
	if mode != Mode.WORLD:
		return false
	match kind:
		"world_move":
			if Time.get_ticks_msec()-_last_move_ms < 150:
				return false
			if _world_mover.active():
				if _world_mover.route.size() <= 2:
					return false
				_world_mover.stop()
			var delta := Vector2i(int(action.get("dx",0)),int(action.get("dy",0)))
			if absi(delta.x)+absi(delta.y) != 1:
				return false
			var current := WorldExpedition.point(state["cell"])
			var target := current+delta
			if not WorldExpedition.walkable(state,target):
				return false
			if state["layer"] == "world":
				var route: Array[Vector2i] = [current,target]
				_world_mover.begin(route,state["transport"])
			elif not game.move_overworld(target):
				return false
			_last_move_ms = Time.get_ticks_msec()
			_world_motion_ms = _last_move_ms
			_facing = 1 if delta.x < 0 else 2 if delta.x > 0 else 3 if delta.y < 0 else 0
			_walk_frame = (_walk_frame+1)%4
			_notice = ""
			return true
		"world_transport":
			_world_mover.stop()
			var changed := game.change_world_transport(str(action.get("transport","")))
			_notice = "移動手段を切り替えました。" if changed else "解放済みの移動手段を、入口や船着場で選んでください。"
			return changed
		"world_interact":
			_world_mover.stop()
			var result := game.interact_overworld()
			match result.get("kind",""):
				"moved":
					_notice = ""
					return true
				"dialogue", "blocked":
					_show_dialogue(result["text"],false,Mode.WORLD)
					return true
				"choice":
					mode = Mode.WORLD_CHOICE
					return true
				"battle":
					var before := game.export_state()
					var encounter := game.start_world_battle()
					if encounter == null:
						return false
					_checkpoint = before
					_persist_checkpoint()
					if not _risk_bypass:
						_confirmed_erosion_actors.clear()
					mode = Mode.BATTLE
					_battle_log = ["この区画の魔物が現れた。勝利後は同じ場所から探索を続けられる。"]
					_add_erosion_lines()
					_actor = encounter.pending()[0].id
					_target_action.clear()
					return true
		"party":
			_world_mover.stop()
			_party_return = Mode.WORLD
			mode = Mode.PARTY
			return true
		"save":
			_world_mover.stop()
			var saved := game.save_game(save_path)
			_notice = "世界地図と拠点の進行を保存しました。" if saved else "保存できませんでした。"
			return saved
		"world_atlas":
			if state["layer"] != "world":
				return false
			_world_mover.stop()
			mode = Mode.WORLD_ATLAS
			return true
		"close_world":
			_world_mover.stop()
			if not game.close_world_exploration():
				return false
			mode = Mode.FIELD
			_notice = "町の冒険へ戻りました。広域での記録は残っています。"
			return true
	return false


func _render_world() -> void:
	var state := game.overworld_state()
	var place: String = "世界地図" if state["layer"] == "world" else WorldExpedition.current_room(state)["title"]
	var modes := {"walk":"徒歩","ship":"船","flight":"飛行"}
	_body.add_child(_label("%s / %s / 訪問%d・依頼%d" % [place,modes[state["transport"]] if state["layer"] == "world" else "徒歩",state["visited"].size(),state["choices"].size()],11))
	var map := ExpeditionView.new()
	map.state = state
	map.members = game.walking_party()
	map.facing = _facing
	map.walk_frame = _walk_frame
	map.custom_minimum_size = Vector2(480,136)
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map.cell_clicked.connect(func(cell: Vector2i) -> void:
		var current := WorldExpedition.point(game.overworld_state()["cell"])
		if cell == current:
			submit_player_action({"kind":"world_interact"})
		elif game.overworld_state()["layer"] == "world":
			submit_player_action({"kind":"world_target","x":cell.x,"y":cell.y})
		else:
			submit_player_action({"kind":"world_move","dx":cell.x-current.x,"dy":cell.y-current.y})
	)
	_body.add_child(map)
	var help := _label("矢印/WASDで移動。入口で調べる。青点は船着場。" if state["layer"] == "world" else "記録と魔物の印を調べて奥へ。左下の出口から戻れます。",9)
	_body.add_child(help)
	var row := HBoxContainer.new()
	_body.add_child(row)
	_action_button(row,"調べる",{"kind":"world_interact"})
	_action_button(row,"編成",{"kind":"party"})
	_action_button(row,"保存",{"kind":"save"})
	if state["layer"] == "world":
		_action_button(row,"全図",{"kind":"world_atlas"})
		for transport in ["walk","ship","flight"]:
			var button := _action_button(row,modes[transport],{"kind":"world_transport","transport":transport})
			button.disabled = not WorldExpedition.transport_allowed(state,transport)
	if WorldExpedition.at_origin(state):
		_action_button(row,"本編へ",{"kind":"close_world"})
	_button(row,"メニュー",_to_menu)


func _render_world_choice() -> void:
	var state := game.overworld_state()
	var event := WorldExpedition.event_at(state)
	_body.add_child(_label(WorldExpedition.node(state["node"])["name"],15))
	var question := _label(event.get("question","選択を確かめる"),13)
	question.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(question)
	for i in range(event.get("options",[]).size()):
		_action_button(_body,event["options"][i],{"kind":"world_choose","option":i})
	_action_button(_body,"周囲を調べ直す",{"kind":"back"})


func _render_world_atlas() -> void:
	var state := game.overworld_state()
	_body.add_child(_label("世界全図 / 行き先を選ぶと現在の移動手段で進みます",11))
	var row := HBoxContainer.new()
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(row)
	var overview := VBoxContainer.new()
	row.add_child(overview)
	if _world_atlas_texture == null:
		var picture := Image.create(128,128,false,Image.FORMAT_RGB8)
		var colors := {"~":Color("244f72"),"g":Color("6b8743"),"f":Color("35502c"),"m":Color("77776e"),"r":Color("ad9971"),"b":Color("c8b087"),"n":Color("f2dd94")}
		for y in range(128):
			for x in range(128):
				picture.set_pixel(x,y,colors.get(WorldTerrain.tile(Vector2i(x*2,y*2)),Color.BLACK))
		for entry in WorldTerrain.data()["nodes"]:
			var cell := WorldTerrain.cell_of(entry["id"])
			picture.set_pixel(cell.x/2,cell.y/2,Color("71b7e8") if entry["dock"] else Color("f2dd94"))
		_world_atlas_texture = ImageTexture.create_from_image(picture)
	var image := TextureRect.new()
	var marked := _world_atlas_texture.get_image()
	var current := WorldExpedition.point(state["cell"])/2
	for dy in range(-1,2):
		for dx in range(-1,2):
			marked.set_pixel(clampi(current.x+dx,0,127),clampi(current.y+dy,0,127),Color("ef7457"))
	image.texture = ImageTexture.create_from_image(marked)
	image.custom_minimum_size = Vector2(128,128)
	overview.add_child(image)
	overview.add_child(_label("青: 海 / 緑: 森\n灰: 山 / 黄: 拠点\n赤: 現在地\n船は青点の船着場で切替",10))
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	row.add_child(scroll)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)
	for entry in WorldExpedition.data()["nodes"]:
		var allowed := WorldExpedition.unlocked(entry["id"],state["flags"])
		var label: String = entry["name"] + (" / 依頼済" if state["choices"].has(entry["id"]) else "")
		if not allowed:
			label += " / 未解放"
		var button := _action_button(list,label,{"kind":"world_target","node":entry["id"]})
		button.disabled = not allowed
		if not allowed:
			button.tooltip_text = "船修理場で船を整えると向かえます。" if entry["required_transport"] == "ship" else "風見の観測所で飛行の準備をすると向かえます。" if entry["required_transport"] == "flight" else "分け水門で保守道を整えると入れます。"
	_action_button(_body,"地図を閉じる",{"kind":"back"})


func _render_exploration() -> void:
	var site := game.exploration_at_player()
	_body.add_child(_label(site["name"],16))
	var description := _label(site["text"],12)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(description)
	if site["complete"]:
		_body.add_child(_label("受取済みです。" if site["kind"] == "cache" else "開通済みです。通路と補給箱を利用できます。",12))
	elif site["kind"] == "device":
		var names: Array[String] = []
		for identifier in site["abilities"]:
			names.append(game.abilities[identifier]["name"])
		_body.add_child(_label("必要な技: "+" または ".join(names),12))
		_body.add_child(_label("生存・技の装着・必要MPを満たす仲間を選んでください。",11))
	else:
		var required := ExplorationSites.by_id(site["requires"])
		_body.add_child(_label("解錠条件: "+required["name"]+"の開通",12))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body.add_child(scroll)
	var choices := VBoxContainer.new()
	choices.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(choices)
	for option in game.exploration_options():
		var label: String = option["label"]
		if not option["allowed"]:
			label += "・条件不足"
		var button := _action_button(choices,label,{"kind":"use_site","actor":option["actor"],"ability":option["ability"]})
		button.disabled = not option["allowed"]
	var row := HBoxContainer.new()
	_body.add_child(row)
	_action_button(row,"編成・装着を見直す",{"kind":"party"})
	_action_button(row,"探索へ戻る",{"kind":"back"})


func _render_journeys() -> void:
	_body.add_child(_label("引き受けることを選ぶ",16))
	var scroll:=ScrollContainer.new()
	scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	_body.add_child(scroll)
	var choices:=VBoxContainer.new()
	choices.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	scroll.add_child(choices)
	for mission in game.long_missions():
		var button:=_action_button(choices,mission["title"],{"kind":"begin_journey","id":mission["id"]})
		button.tooltip_text=ChapterOne.TITLES[mission["region"]]
	_action_button(_body,"今は戻る",{"kind":"back"})


func _render_dialogue() -> void:
	if _dialogue_past:
		_body.add_child(_label("現在の記録室" if _messages[_message_index].begins_with("【現在】") else "過去の記録", 13))
	else:
		var row := HBoxContainer.new()
		_body.add_child(row)
		for i in range(game.export_state()["party"].size()):
			var face := _picture("res://assets/characters/pc_%02d/portrait.png" % (i+1), Vector2(64,64))
			row.add_child(face)
	var message := RichTextLabel.new()
	message.text = _messages[_message_index]
	message.add_theme_font_size_override("normal_font_size",14)
	message.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(message)
	_action_button(_body, "次へ  Enter", {"kind":"confirm"})
	if not _dialogue_summary.is_empty():
		_action_button(_body, "要約へ", {"kind":"summary"})


func _render_battle() -> void:
	var encounter := game.current_battle()
	_body.add_theme_constant_override("separation",2)
	var tools := HBoxContainer.new()
	_body.add_child(tools)
	var caption := _label("第%dターン / 回復薬 %d" % [encounter.round_number, encounter.potions], 11)
	if not _actor.is_empty():caption.text+=" / "+encounter.actor_by_id(_actor).display_name+"の行動"
	caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tools.add_child(caption)
	_action_button(tools,"機構・予測",{"kind":"mechanics"})
	_action_button(tools, "選び直す", {"kind":"clear_actions"})
	var resolve := _action_button(tools, "ターン実行", {"kind":"resolve_round"})
	resolve.disabled = not encounter.can_resolve()
	var forecast := _label(_erosion_forecast_text(), 9)
	forecast.tooltip_text = "戦闘終了時の侵蝕見込み。予約した技がすべて発動した場合の値。"
	forecast.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(forecast)
	var stage := HBoxContainer.new()
	_body.add_child(stage)
	var foes := HBoxContainer.new()
	foes.custom_minimum_size.x = 252
	stage.add_child(foes)
	var definitions: Array = game.current_enemy_ids()
	var intents: Dictionary = {}
	var predictions:=VBoxContainer.new()
	predictions.add_theme_constant_override("separation",0)
	for intent in encounter.enemy_intents():
		intents[intent["actor"]] = intent
	var index := 0
	for actor in encounter.actors:
		if actor.team != Combatant.Team.ENEMY or actor.is_device:
			continue
		var card := VBoxContainer.new()
		card.add_theme_constant_override("separation",2)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var definition: Dictionary = game.enemy_definitions[definitions[index]]
		var icon_size := 32 if definitions.size() >= 3 else 64
		card.add_child(_picture("res://assets/monsters/%s/idle.png" % definition.get("sprite_id",definitions[index]), Vector2(icon_size,icon_size)))
		card.add_child(_label("%s\n敵%d HP%d/%d" % [actor.display_name,index+1,actor.hp,actor.max_hp],10))
		if intents.has(actor.id):
			var intent: Dictionary = intents[actor.id]
			var target_name: String = intent["target_name"]
			if str(intent["target"]).begins_with("enemy_"):
				target_name = "敵"+str(int(str(intent["target"]).trim_prefix("enemy_")))
			var description := _label("敵%d %s→%s" % [index+1,intent["action"],target_name],9)
			description.tooltip_text = "次の行動予定: %s→%s" % [intent["action"],intent["target_name"]]
			if game.export_state()["format_version"]==1 and encounter.effects.rules.is_empty() and (int(intent.get("reaction_power",0))>0 or int(intent.get("chorus_guard",100))<100):
				var shield:=int(intent["guard_percent"])
				var expected:=encounter.forecast_damage(intent["target"],false,-1,false,actor.id)
				var guarded:=encounter.forecast_damage(intent["target"],true,-1,false,actor.id)
				var kind: String=game.abilities.get(intent["ability"],{}).get("kind","physical")
				if kind in ["physical","magic"]:
					description.text+=" / 被%d 防%d / 技%d 敵被%d%%" % [expected,guarded,encounter.reaction_count(),shield]
					if expected>=encounter.actor_by_id(intent["target"]).hp:description.add_theme_color_override("font_color",Color("eea38b"))
				else:description.text+=" / 反応:技%d 敵被%d%%" % [encounter.reaction_count(),shield]
				description.tooltip_text+="\n被は対象が受ける被害の予測、防は通常の防御を選んだ場合です。敵被は敵が受ける割合で、20%なら80%軽減です。攻撃技の予約人数で反応が強まり、3人以上で共鳴防御。通常攻撃・回復・蘇生・防御は数えません。選び直すと予告も戻ります。"
			description.size_flags_horizontal=Control.SIZE_EXPAND_FILL
			description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			predictions.add_child(description)
		foes.add_child(card)
		index += 1
	var allies := GridContainer.new()
	allies.columns = 2
	allies.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stage.add_child(allies)
	for actor in encounter.actors:
		if actor.team != Combatant.Team.PARTY:
			continue
		var card := HBoxContainer.new()
		allies.add_child(card)
		var member: Dictionary = {}
		for candidate in game.export_state()["party"]:
			if candidate["id"] == actor.id:
				member = candidate
		card.add_child(_actor_picture(member,"battle",0,Vector2(32,32)))
		var button := _button(card, "%s HP%d\n%sMP%d/%d" % [actor.display_name,actor.hp,"✓ " if encounter.queued.has(actor.id) else "",actor.mp,actor.max_mp], _select_actor.bind(actor.id))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.disabled = not actor.is_alive()
	_body.add_child(predictions)
	if not _actor.is_empty():
		var commands := GridContainer.new()
		commands.columns = 4
		_body.add_child(commands)
		_button(commands, "攻撃", _choose_target.bind("attack", ""))
		_button(commands,"観察",_choose_target.bind("observe",""))
		_action_button(commands, "防御", {"kind":"guard", "actor":_actor})
		var actor := encounter.actor_by_id(_actor)
		for identifier in actor.equipped:
			var definition: Dictionary = game.abilities[identifier]
			if definition["kind"]=="passive":continue
			var button := _button(commands, "%s %dMP" % [definition["name"], encounter.effects.cost(actor,definition)], _choose_target.bind("ability", identifier))
			button.tooltip_text = game.describe_ability(identifier,actor.id)
			button.disabled = encounter.targets_for(_actor, BattleAction.Kind.ABILITY, identifier).is_empty()
		var potion := _button(commands, "回復薬", _choose_target.bind("potion", ""))
		potion.tooltip_text = "HPを%d回復します。MP回復・蘇生の効果はありません。" % game.catalog.potion_healing
		potion.disabled = encounter.targets_for(_actor, BattleAction.Kind.ITEM).is_empty()
	if not _target_action.is_empty():
		var row := HBoxContainer.new()
		_body.add_child(row)
		var action_kind := BattleAction.Kind.ABILITY if _target_action["kind"] == "ability" else (BattleAction.Kind.ITEM if _target_action["kind"] == "potion" else (BattleAction.Kind.OBSERVE if _target_action["kind"]=="observe" else BattleAction.Kind.ATTACK))
		for target in encounter.targets_for(_actor, action_kind, _target_action.get("ability", "")):
			var action := _target_action.duplicate()
			action["target"] = target.id
			_action_button(row, target.display_name, action)
	var log := RichTextLabel.new()
	log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log.custom_minimum_size.y = 24
	log.scroll_following = true
	log.add_theme_font_size_override("normal_font_size", 10)
	log.text = "\n".join(_battle_log.slice(maxi(0,_battle_log.size()-60)))
	for message in [_notice,_checkpoint_error]:
		if not message.is_empty():
			log.text += "\n"+message
	_body.add_child(log)
	# OSのフォント差があっても、戦闘の操作部品とログを同じ画面内に収める。
	for control in _body.find_children("*","Button",true,false):
		control.add_theme_font_size_override("font_size",10)
		for state in ["normal","hover","pressed","focus","disabled"]:
			var box: StyleBox = control.get_theme_stylebox(state).duplicate()
			box.content_margin_top = 1
			box.content_margin_bottom = 1
			control.add_theme_stylebox_override(state,box)


func _select_actor(identifier: String) -> void:
	_actor = identifier
	_target_action.clear()
	_refresh()


func _choose_target(kind: String, ability_id: String) -> void:
	_target_action = {"kind":kind, "actor":_actor, "ability":ability_id}
	if kind == "ability" and game.abilities[ability_id]["target"] == "self":
		_target_action["target"] = _actor
		submit_player_action(_target_action.duplicate())
	else:
		_refresh()


func _render_party() -> void:
	if not _purify_actor.is_empty():
		_render_purify_confirmation()
		return
	var outer := _body
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	outer.add_child(scroll)
	_body = VBoxContainer.new()
	_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_body)
	var party: Array = game.export_state()["party"]
	_party_index = clampi(_party_index, 0, party.size()-1)
	var actor: Dictionary = party[_party_index]
	var selector := OptionButton.new()
	for entry in party:
		selector.add_item(entry["name"])
	selector.select(_party_index)
	selector.item_selected.connect(func(index: int) -> void: _party_index = index; _refresh())
	_body.add_child(selector)
	_action_button(_body,"この仲間を先頭にする",{"kind":"set_leader","actor":actor["id"]})
	var job_row := HBoxContainer.new()
	_body.add_child(job_row)
	var jobs := OptionButton.new()
	jobs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for identifier in game.jobs:
		jobs.add_item(game.jobs[identifier]["name"]+("（未解放）" if not game.job_unlocked(actor["id"],identifier) else ""))
		jobs.set_item_metadata(jobs.item_count-1, identifier)
		if identifier == actor["job_id"]:
			jobs.select(jobs.item_count-1)
	job_row.add_child(jobs)
	var change := _button(job_row, "この職に転職", func() -> void:
		var identifier: String = jobs.get_item_metadata(jobs.selected)
		submit_player_action({"kind":"choose_job","actor":actor["id"],"job":identifier}))
	var comparison := _label(_job_preview_text(actor, actor["job_id"]), 10)
	comparison.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(comparison)
	jobs.item_selected.connect(func(index: int) -> void:
		var identifier: String = jobs.get_item_metadata(index)
		comparison.text = _job_preview_text(actor, identifier)
		change.disabled = not game.preview_job(actor["id"], identifier)["allowed"] or not game.job_unlocked(actor["id"],identifier))
	_action_button(_body,"町の噂・魔物図鑑",{"kind":"job_lore"})
	_body.add_child(_label("魔物職はマスターで魔物化。侵蝕90以降は人間職へ戻れません。", 10))
	_body.add_child(_label("侵蝕 %.1f（%s） / 30:兆候・60:人間JP半減・90:復帰不可" % [game.current_erosion(actor["id"]), GameSession.erosion_stage(actor["erosion"])], 10))
	_body.add_child(_label("JP %d/%d  %s / 装着 %d/%d" % [int(actor["jp"].get(actor["job_id"],0)), IntegratedProgression.cost(game.jobs[actor["job_id"]],actor.has("integrated")), "マスター" if actor["job_id"] in actor["mastered_jobs"] else "修練中", actor["equipped_abilities"].size(), game.slot_limit(actor["id"])], 11))
	if actor.has("integrated"):_integrated_party_controls(actor)
	else:_action_button(_body,"新しい育成・侵蝕ルールへの引継ぎ",{"kind":"preview_rule_upgrade"})
	_action_button(_body,"機構の覚え書き",{"kind":"mechanics"})
	var trait_total := _label(game.mastery_bonus_text(actor["id"]), 10)
	trait_total.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(trait_total)
	for trait_entry in game.mastery_traits(actor["id"]):
		var trait_label := _label(trait_entry["name"]+": "+trait_entry["description"]+"（常時・枠不要）",10)
		trait_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_body.add_child(trait_label)
	var slots := GridContainer.new()
	slots.columns = 2
	_body.add_child(slots)
	for identifier in actor["equipped_abilities"]:
		var remove := _button(slots, game.abilities[identifier]["name"] + "を外す", _unequip.bind(actor["id"], identifier))
		remove.tooltip_text = game.describe_ability(identifier,actor["id"])
	var skills := OptionButton.new()
	for identifier in game.available_abilities(actor["id"]):
		if not identifier in actor["equipped_abilities"]:
			skills.add_item(game.abilities[identifier]["name"])
			skills.set_item_metadata(skills.item_count-1, identifier)
	var skill_row := HBoxContainer.new()
	_body.add_child(skill_row)
	skills.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	skill_row.add_child(skills)
	var equip := _button(skill_row, "装着", func() -> void:
		if skills.selected >= 0:
			_notice = "装着しました。" if game.equip_ability(actor["id"], skills.get_item_metadata(skills.selected)) else "装着枠または習得状態を確認してください。"
			_refresh())
	equip.disabled = skills.item_count == 0
	var skill_details := _label("習得した技をここで装着できます。" if skills.item_count == 0 else game.describe_ability(skills.get_item_metadata(skills.selected),actor["id"]), 10)
	skill_details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(skill_details)
	skills.item_selected.connect(func(index: int) -> void:
		skill_details.text = game.describe_ability(skills.get_item_metadata(index),actor["id"]))
	var current := game.effective_stats(actor["id"])
	_body.add_child(_label("HP%d/%d MP%d/%d\n攻撃%d 防御%d 魔力%d 魔防%d 速さ%d" % [actor["hp"],actor["max_hp"],actor["mp"],actor["max_mp"],current["attack"],current["defense"],current["magic"],current["resistance"],current["speed"]], 11))
	if not str(actor["monster_form"]).is_empty() or int(actor["erosion"]) > 0:
		if not str(actor["monster_form"]).is_empty():
			_body.add_child(_label("魔物化: " + game.jobs[actor["monster_form"]]["name"], 11))
		var release := _action_button(_body, "町の祠で清める（魔物専用技を全消去）", {"kind":"request_purify", "actor":actor["id"]})
		release.disabled = game.world_state()["location"] != "town" or actor["irreversible"]
	_body = outer
	_action_button(_body, "探索へ戻る", {"kind":"back"})


func _job_preview_text(actor: Dictionary, job_id: String) -> String:
	var preview := game.preview_job(actor["id"], job_id)
	var current := game.effective_stats(actor["id"])
	var next: Dictionary = preview["stats"]
	var text := "転職後の比較: HP%d→%d MP%d→%d\n攻撃%d→%d 防御%d→%d 魔力%d→%d 魔防%d→%d 速さ%d→%d" % [current["hp"],next["hp"],current["mp"],next["mp"],current["attack"],next["attack"],current["defense"],next["defense"],current["magic"],next["magic"],current["resistance"],next["resistance"],current["speed"],next["speed"]]
	var definitions: Array = IntegratedProgression.skill_list(game.jobs[job_id],actor.has("integrated"))
	text += "\nマスター特性: "+game.mastery_trait(job_id)["description"]+"（転職後も常時）"
	for index in range(definitions.size()):
		var ability_id: String = definitions[index]
		var required := IntegratedProgression.threshold(game.jobs[job_id],ability_id) if actor.has("integrated") else (ceili(float(preview["mastery_cost"])/2.0) if index==0 else int(preview["mastery_cost"]))
		var remaining := maxi(0,required-int(actor.get("integrated",{}).get("relearn",{}).get(ability_id,0))) if ability_id in actor.get("integrated",{}).get("forgotten",[]) else maxi(0,required-int(preview["jp"]))
		var progress := "次の勝利で再習得" if remaining == 0 else "あと%dJPで習得" % remaining
		text += "\n%s: %s" % [game.abilities[ability_id]["name"], "習得済み" if ability_id in actor["learned_abilities"] else progress]
	if not str(preview["monster_form"]).is_empty():
		text += "\n転職後も魔物化: " + game.jobs[preview["monster_form"]]["name"]
	if not preview["allowed"]:
		text += "\n今はこの職業へ転職できません。"
	return text


func _unequip(actor_id: String, identifier: String) -> void:
	_notice = "装着を外しました。" if game.unequip_ability(actor_id, identifier) else "外せませんでした。"
	_refresh()


func _request_purify(actor_id: String) -> bool:
	if game.world_state()["location"] != "town":
		return false
	for actor in game.export_state()["party"]:
		if actor["id"] == actor_id and (not str(actor["monster_form"]).is_empty() or int(actor["erosion"]) > 0) and not actor["irreversible"]:
			_purify_actor = actor_id
			return true
	return false


func _render_purify_confirmation() -> void:
	_body.add_child(_label("魔物専用の技を手放し、侵蝕を下げますか？", 14))
	var description := _label("習得済みの魔物専用アビリティをすべて消去し、侵蝕度を30下げます。\n人間職でも習得できる技と、マスター済みの成長は残ります。", 12)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(description)
	_action_button(_body, "やめる", {"kind":"cancel_purify"})
	_action_button(_body, "専用技を消去して清める", {"kind":"confirm_purify"})


func _erosion_forecast_text() -> String:
	var parts: Array[String] = []
	for entry in game.erosion_preview(true):
		if entry["after"] != entry["before"]:
			parts.append("%s %.1f→%.1f %s" % [entry["name"], entry["before"], entry["after"], GameSession.erosion_stage(int(entry["after"]))])
	return "侵蝕予測: " + ("変化なし" if parts.is_empty() else " / ".join(parts))


func _render_erosion_confirmation() -> void:
	_body.add_child(_label("戦闘後の変化を確認", 15))
	var text := "侵蝕90以上では、人間職への転職と祠での解除ができなくなります。\n"
	for entry in _risk_preview:
		if entry.get("kind")=="mastery":
			text+="\n%s: 勝利のJP%dで%sをマスターし、魔物化します。追加枠＋1。" % [entry["name"],entry["jp"],entry["job"]]
			var weak: Dictionary=game.catalog.integration["forms"].get(entry["job_id"],{})
			text+="有料技MP＋%d、物理被害%.2f倍、魔法被害%.2f倍。" % [weak.get("mp_add",0),weak.get("physical_rate",1),weak.get("magic_rate",1)]
			text+="避ける場合は取消して職業を変えられます。\n"
			continue
		text += "\n%s: %.1f→最大%.1f" % [entry["name"], entry["before"], entry["after"]]
		if not str(entry["forced_job"]).is_empty():
			text += " / 終了後は" + game.jobs[entry["forced_job"]]["name"]
	text += "\n\n予約した技は実際に発動した回数だけ加算します。未マスターの職が、この確認だけでマスターになることはありません。"
	var description := RichTextLabel.new()
	description.text = text
	description.add_theme_font_size_override("normal_font_size",12)
	description.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(description)
	_action_button(_body, "やめる・選び直す", {"kind":"cancel_erosion"})
	_action_button(_body, "条件を確認して進む", {"kind":"confirm_erosion"})


func _render_complete() -> void:
	if game.story_complete():
		_body.add_child(_label("開ける役目  おわり", 17))
		_body.add_child(_label("水門が開き、番人は町へ戻った。\n二打の合図は、これからも受け継がれていく。", 14))
		var state := game.export_state()
		var team: Array = state.get("gate_team",[])
		var duties: Array[String] = []
		var witnesses: Array[String] = ["番人"]
		for actor in state["party"]:
			if actor["id"] in team:
				var station: String = ["上流","中央","下流"][team.find(actor["id"])]
				duties.append(station + ": " + actor["name"])
			else:
				witnesses.append(actor["name"])
		_body.add_child(_label("引継ぎ帳  " + " / ".join(duties) + "\n見届け: " + "、".join(witnesses),11))
	else:
		_body.add_child(_label("第1章  閉じた道  クリア", 17))
		_body.add_child(_label("番人はもう一度、板を二度打った。\nその音の意味は、まだ分からない。", 14))
		_action_button(_body, "物語を続ける", {"kind":"continue_story"})
	_action_button(_body, "手帳を読み返す", {"kind":"journal"})
	_action_button(_body, "冒険の記録を保存", {"kind":"save"})
	_button(_body, "タイトルへ", _to_menu)


func _render_journal() -> void:
	var entries := game.journal_entries()
	_body.add_child(_label("旅の手帳  %d / %d件" % [entries.size(),game.journal_capacity()],15))
	if entries.is_empty():
		_body.add_child(_label("見聞きした手掛かりが、ここへ記録されます。",12))
	else:
		_journal_index = clampi(_journal_index,0,entries.size()-1)
		var selector := OptionButton.new()
		for entry in entries:
			selector.add_item("%s %s（%s）" % [entry["id"],entry["title"],"回収済み" if entry["stage"] == 2 else "調査中"])
		selector.select(_journal_index)
		selector.item_selected.connect(func(index: int) -> void: _journal_index=index; _refresh())
		_body.add_child(selector)
		var entry: Dictionary = entries[_journal_index]
		var text := "見たこと\n%s\n\nその時の見立て\n%s" % [entry["observation"],entry["first"]]
		if entry.has("resolved"):
			text += "\n\n分かったこと\n" + entry["resolved"]
		if entry.has("loadout"):
			text += "\n\n" + entry["loadout"]
		var body := RichTextLabel.new()
		body.text = text
		body.size_flags_vertical = Control.SIZE_EXPAND_FILL
		body.add_theme_font_size_override("normal_font_size",12)
		_body.add_child(body)
	var row := HBoxContainer.new()
	_body.add_child(row)
	var titles := {"identity":"来歴の記録", "choice":"閉めた日の記録", "board":"打ち板の記録"}
	for record in game.replayable_records():
		_action_button(row,titles[record["id"]],{"kind":"replay","event":record["id"]})
	_action_button(_body,"戻る",{"kind":"back"})


func _render_visits() -> void:
	_body.add_child(_label("先に確かめる場所を選ぶ",15))
	_body.add_child(_label("町の教習と、水門の番人への応答。\nどちらを先に進めても、もう一方は後から確かめられます。",12))
	var flags: Dictionary = game.export_state()["progress_flags"]
	var lesson := _action_button(_body,"町で教習を再開する",{"kind":"visit_task","task":"teaching"})
	lesson.disabled = StoryCampaign.stage(flags,"R08") == 2
	var reply := _action_button(_body,"水門で番人に応答する",{"kind":"visit_task","task":"reply"})
	reply.disabled = StoryCampaign.stage(flags,"R05") == 2
	_action_button(_body,"町の探索へ戻る",{"kind":"back"})


func _render_gate() -> void:
	_body.add_child(_label("三つの操作台の担当",15))
	_body.add_child(_label("三人に堅守と響きの波を装着し、一人%dMPを使います。" % game.gate_mp_cost(),11))
	var row := HBoxContainer.new()
	_body.add_child(row)
	for actor in game.export_state()["party"]:
		var check := CheckBox.new()
		check.text = actor["name"]
		check.button_pressed = actor["id"] in _gate_team
		check.toggled.connect(func(selected: bool) -> void:
			if selected and not actor["id"] in _gate_team:
				_gate_team.append(actor["id"])
			elif not selected:
				_gate_team.erase(actor["id"])
			_refresh())
		row.add_child(check)
	var reasons := game.gate_requirements(_gate_team)
	var detail := RichTextLabel.new()
	detail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.text = "準備がそろっています。" if reasons.is_empty() else "\n".join(reasons)
	_body.add_child(detail)
	_action_button(_body,"編成・装着を変える",{"kind":"party"})
	var operate := _action_button(_body,"三人で水門を動かす",{"kind":"operate_gate"})
	operate.disabled = not reasons.is_empty()
	_action_button(_body,"探索へ戻る",{"kind":"back"})


func _load_save() -> void:
	_world_mover.stop()
	if not game.load_game(save_path):
		_notice = "読み込めるセーブがありません。"
		_refresh()
		return
	_checkpoint.clear()
	_checkpoint_error = ""
	_gate_team = []
	_trail.clear()
	_replay.clear()
	game.play_metrics.mark("loads")
	_party_return = Mode.FIELD
	mode = Mode.COMPLETE if game.chapter_one_pause() or game.story_complete() else Mode.FIELD
	if game.world_exploration_active():
		mode = Mode.WORLD
	if game.party_defeated():
		mode = Mode.DEFEAT
	if not ChapterOne.missing_art().is_empty():
		mode = Mode.ASSETS_MISSING
	_notice = "冒険の記録を読み込みました。"
	_refresh()


func _start_encounter(story_battle: bool) -> BattleState:
	var before := game.export_state()
	var encounter := game.start_story_battle() if story_battle else game.start_field_battle()
	if encounter != null:
		_notice = ""
		_checkpoint = before
		_persist_checkpoint()
	return encounter


func _add_erosion_lines() -> void:
	var encounter:=game.current_battle()
	if encounter!=null and encounter.has_reactive_enemy():
		_battle_log.append("攻撃技の予約人数で反応が強まる相手だ。3人以上の攻撃技では共鳴防御も構える。通常攻撃・回復・蘇生・防御は反応を増やさない。")
	for actor in game.export_state()["party"]:
		var line := CharacterVisuals.battle_line(actor)
		if not line.is_empty():
			_battle_log.append(line)


func recovery_available() -> bool:
	return not _checkpoint.is_empty()


func _persist_checkpoint() -> bool:
	if _checkpoint.is_empty():
		return false
	# 別セッションに進行だけを複製し、戦闘中の本体や手動保存を変更しない。
	var saved := GameSession.new()
	if _checkpoint.get("format_version",1)==2:
		_checkpoint["integrated"]["knowledge"]=game.integration_knowledge()
	if not saved.import_state(_checkpoint):
		_checkpoint_error = "戦闘前の記録が不正です。手動セーブを確認してください。"
		return false
	saved.play_metrics = game.play_metrics
	game.flush_recording()
	var written := saved.save_game(checkpoint_path,game.playthrough_id())
	_checkpoint_error = "" if written else "自動保存できませんでした。起動中は戦闘前へ戻れますが、終了前に手動保存してください。"
	return written


func _retry_battle() -> bool:
	if not recovery_available() or not game.import_state(_checkpoint):
		return false
	# 読み直すのは進行だけ。失敗した試行の計測と回答は巻き戻さない。
	game.play_metrics.mark("battle_retries")
	game.play_metrics.record_event("battle_retry",{"world":game.world_state()})
	_persist_checkpoint()
	_reset_after_recovery()
	return true


func _load_checkpoint() -> bool:
	# 起動中の同じ敗北からなら、現在までの計測を優先する。
	if game.party_defeated() and recovery_available():
		return _retry_battle()
	var candidate := GameSession.new()
	if not candidate.load_game(checkpoint_path) or candidate.party_defeated():
		_notice = "読み込める自動保存がありません。現在の冒険はそのままです。"
		_refresh()
		return false
	if not game.load_game(checkpoint_path):
		return false
	_checkpoint_error = ""
	_checkpoint = game.export_state()
	game.play_metrics.mark("checkpoint_loads")
	game.play_metrics.record_event("checkpoint_load",{"world":game.world_state()})
	_reset_after_recovery()
	return true


func _reset_after_recovery() -> void:
	_world_mover.stop()
	_gate_team = []
	_trail.clear()
	_replay.clear()
	_target_action.clear()
	_confirmed_erosion_actors.clear()
	_risk_action.clear()
	_risk_preview.clear()
	_risk_bypass = false
	_party_return = Mode.FIELD
	mode = Mode.WORLD if game.world_exploration_active() else Mode.FIELD
	_notice = "戦闘前へ戻りました。編成や帰還で立て直してから挑戦できます。"
	_refresh()


func _to_menu() -> void:
	_world_mover.stop()
	_replay.clear()
	mode = Mode.MENU
	_notice = ""
	_refresh()


func _picture(path: String, dimensions: Vector2) -> TextureRect:
	var picture := TextureRect.new()
	picture.custom_minimum_size = dimensions
	picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if not _textures.has(path) and ResourceLoader.exists(path):
		_textures[path] = load(path)
	if _textures.has(path):
		picture.texture = _textures[path]
	return picture


func _actor_picture(actor: Dictionary, kind: String, frame: int, dimensions: Vector2) -> Control:
	var visual := CharacterVisuals.appearance(actor,kind,frame)
	if not visual["available"]:
		var missing := _label("外見\n未取込",8)
		missing.custom_minimum_size = dimensions
		return missing
	var picture := _picture(visual["path"],dimensions)
	var region := AtlasTexture.new()
	region.atlas = picture.texture
	region.region = visual["region"]
	picture.texture = region
	return picture


func presentation_snapshot() -> Dictionary:
	if _replay.is_empty():
		return {"active":false}
	var event: Dictionary = _replay[_replay_index]
	var frames: Dictionary = {}
	for actor in _replay_party:
		frames[actor["id"]] = 2 if event["target"] == actor["id"] and event["code"] in ["damage","fallen"] else (1 if event["actor"] == actor["id"] and event["code"] in ["damage","heal","revive","steal"] else 0)
	return {"active":true,"index":_replay_index,"frames":frames,"event":event.duplicate(true)}


func _render_presentation() -> void:
	var shade := PanelContainer.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	var box := StyleBoxFlat.new()
	box.bg_color = Color("0a101a")
	for side in ["left","right","top","bottom"]:
		box.set("content_margin_"+side,8)
	shade.add_theme_stylebox_override("panel",box)
	var column := VBoxContainer.new()
	shade.add_child(column)
	var event: Dictionary = _replay[_replay_index]
	var banner := _label(event["message"],13)
	banner.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(banner)
	var arena := HBoxContainer.new()
	arena.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(arena)
	var enemies := VBoxContainer.new()
	enemies.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	arena.add_child(enemies)
	for identifier in _replay_enemies:
		var definition: Dictionary = game.enemy_definitions[identifier]
		enemies.add_child(_picture("res://assets/monsters/%s/idle.png" % definition.get("sprite_id",identifier),Vector2(64,64)))
	var party := VBoxContainer.new()
	arena.add_child(party)
	var display := presentation_snapshot()
	for actor in _replay_party:
		var row := HBoxContainer.new()
		party.add_child(row)
		row.add_child(_actor_picture(actor,"battle",display["frames"][actor["id"]],Vector2(48,48)))
		for state in event["snapshot"]["actors"]:
			if state["id"] == actor["id"]:
				row.add_child(_label("%s  HP %d/%d\nMP %d/%d" % [actor["name"],state["hp"],state["max_hp"],state["mp"],state["max_mp"]],10))
	_action_button(column,"表示をスキップ  Enter",{"kind":"skip_presentation"})


func _render_review() -> void:
	var metrics: Dictionary = game.playtest_document()
	_body.add_child(_label("試遊の記録と評価",16))
	_body.add_child(_label("経過 %.1f分 / 操作中 %.1f分 / 無操作 %.1f分 / 休止 %.1f分" % [metrics["elapsed_ms"]/60000.0,metrics["active_ms"]/60000.0,metrics["idle_ms"]/60000.0,metrics["pause_ms"]/60000.0],10))
	_body.add_child(_label("記録区分: "+{"unclassified":"未指定","human":"人間の試遊・自己申告","automated":"自動操作"}[metrics["source"]],10))
	if not game.recording_issue().is_empty():
		var issue := _label(game.recording_issue(),10)
		issue.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_body.add_child(issue)
	_action_button(_body,"人間の試遊として記録する",{"kind":"set_playtest_source","source":"human"})
	var row := HBoxContainer.new()
	_body.add_child(row)
	var ratings: Array[OptionButton] = []
	for title in ["探索の分かりやすさ","報酬の満足度","難易度"]:
		var choice := OptionButton.new()
		choice.add_item(title)
		for value in range(1,6):
			choice.add_item(str(value))
		row.add_child(choice)
		ratings.append(choice)
	_body.add_child(_label("探索・報酬: 1=低い、5=高い / 難易度: 1=易しい、5=難しい",9))
	var note := TextEdit.new()
	note.placeholder_text = "迷った場所、報酬が足りない場面、難しすぎた敵など"
	note.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(note)
	var buttons := HBoxContainer.new()
	_body.add_child(buttons)
	_button(buttons,"回答を記録",func() -> void: submit_player_action({"kind":"submit_review","exploration":ratings[0].selected,"reward":ratings[1].selected,"difficulty":ratings[2].selected,"note":note.text}))
	_action_button(buttons,"JSONへ保存",{"kind":"export_playtest"})
	_action_button(buttons,"戻る",{"kind":"back"})


func _render_challenge() -> void:
	var task := _step()
	var question := _label(task["question"],14)
	question.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(question)
	var record := RichTextLabel.new()
	record.size_flags_vertical = Control.SIZE_EXPAND_FILL
	record.text = task["record"]
	record.add_theme_font_size_override("normal_font_size",11)
	_body.add_child(record)
	for index in range(task["options"].size()):
		_action_button(_body,task["options"][index],{"kind":"challenge_answer","option":index})
	_action_button(_body,"探索へ戻る",{"kind":"back"})


func _render_long_device() -> void:
	var activity := game.long_activity()
	var flags: Dictionary = game.export_state()["progress_flags"]
	_body.add_child(_label(activity["name"],13))
	var record := RichTextLabel.new()
	record.size_flags_vertical = Control.SIZE_EXPAND_FILL
	record.add_theme_font_size_override("normal_font_size",10)
	var lines: Array[String] = []
	var ready := true
	for i in range(2):
		var read: bool = flags.get(LongCampaign.activity_flag(activity["id"],"seen_"+str(i)),false)
		ready = ready and read
		lines.append("観察%d: %s" % [i+1,activity["observations"][i]["text"] if read else "現地でまだ確認していない"])
	lines.append(activity["support_description"])
	record.text = "\n".join(lines)
	_body.add_child(record)
	var support := OptionButton.new()
	support.add_item("MPを温存して手順だけで進める")
	support.set_item_metadata(0,"")
	for actor in game.export_state()["party"]:
		var skill: String = activity["support_ability"]
		if actor["hp"] > 0 and skill in actor["equipped_abilities"] and actor["mp"] >= int(game.abilities[skill]["cost"]):
			support.add_item("%sの堅守で支える（%dMP・近道）" % [actor["name"],game.abilities[skill]["cost"]])
			support.set_item_metadata(support.item_count-1,actor["id"])
			if actor["id"] == _long_support_actor:support.select(support.item_count-1)
	_long_support_actor = support.get_item_metadata(support.selected)
	support.item_selected.connect(func(index: int) -> void: _long_support_actor = support.get_item_metadata(index))
	_body.add_child(support)
	var question := _label(activity["question"],11)
	question.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.add_child(question)
	for i in range(activity["options"].size()):
		var button := _action_button(_body,activity["options"][i],{"kind":"long_device_answer","option":i})
		button.disabled = not ready
	var row := HBoxContainer.new()
	_body.add_child(row)
	_action_button(row,"装着を確認",{"kind":"party"})
	_action_button(row,"探索へ戻る",{"kind":"back"})


func _render_job_lore() -> void:
	var in_town: bool = game.world_state()["location"] in ChapterOne.TOWNS
	_body.add_child(_label("町の噂と魔物図鑑" if in_town else "魔物図鑑の覚え書き",16))
	var text := RichTextLabel.new()
	text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	text.add_theme_font_size_override("normal_font_size",12)
	var lines: Array[String] = []
	for identifier in game.job_progression["advanced"]:
		var record: Dictionary = game.job_progression["advanced"][identifier]
		lines.append(str(game.jobs[identifier]["name"]))
		var known: Array=game.export_state().get("integrated",{}).get("job_notes",[])
		var legacy: bool=game.export_state()["format_version"]==1
		if (legacy and in_town) or identifier+"/rumor" in known:
			lines.append("町の噂: "+str(record["rumor"]))
		else:lines.append("町の噂: 未確認。町で聞ける。")
		if legacy or identifier+"/bestiary" in known:lines.append("図鑑: "+str(record["bestiary"]))
		else:lines.append("図鑑: 未確認。図鑑を開いて調べる。")
		lines.append("")
	text.text = "\n".join(lines)
	_body.add_child(text)
	_action_button(_body,"編成へ戻る",{"kind":"back"})


static func _label(value: String, font_size: int) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_size_override("font_size", font_size)
	return label


func _action_button(parent: Node, text: String, action: Dictionary) -> Button:
	return _button(parent, text, func() -> void: submit_player_action(action))


static func _button(parent: Node, text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.pressed.connect(callback)
	parent.add_child(button)
	return button


func _integrated_party_controls(actor: Dictionary) -> void:
	var own: Dictionary=actor["integrated"]
	_body.add_child(_label("Lv%d / EXP%d / 専門技と基礎成長は別" % [own["level"],own["exp"]],11))
	for slot in range(2 if "twin_grip" in actor["equipped_abilities"] else 1):
		var row:=HBoxContainer.new();_body.add_child(row)
		row.add_child(_label("武器%d" % (slot+1),11))
		var picker:=OptionButton.new();picker.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(picker)
		for id in game.export_state()["integrated"]["armory"]:
			var item:=IntegratedProgression.weapon(id)
			picker.add_item("%s / 攻撃%+d / %s" % [item["name"],item["attack"],"射撃" if "projectile" in item["tags"] else "近接"])
			picker.set_item_metadata(picker.item_count-1,id)
			if slot<own["weapons"].size() and own["weapons"][slot]==id:picker.select(picker.item_count-1)
		picker.item_selected.connect(func(index: int)->void:
			_notice="武器を持ち替えました。" if game.equip_weapon(actor["id"],picker.get_item_metadata(index),slot) else "装着条件を確認してください。"
			_refresh())
	if "focus_vow" in actor["equipped_abilities"]:
		var bind:=OptionButton.new();bind.add_item("専心: 結び付けなし");bind.set_item_metadata(0,"")
		for id in actor["equipped_abilities"]:
			if game.abilities[id]["kind"] not in ["physical","magic"]:continue
			bind.add_item("専心 → "+str(game.abilities[id]["name"]));bind.set_item_metadata(bind.item_count-1,id)
			if own["focus_binding"]==id:bind.select(bind.item_count-1)
		bind.item_selected.connect(func(index: int)->void:game.bind_focus(actor["id"],bind.get_item_metadata(index));_refresh())
		_body.add_child(bind)
	for id in own["forgotten"]:
		_body.add_child(_label("再習得: %s / 累積%dJP" % [game.abilities[id]["name"],own["relearn"].get(id,0)],10))
	var form:=IntegratedProgression.form_rule(actor)
	if not form.is_empty():
		var line:=_label("形態: 有料技MP＋%d / 物理被害%.2f倍 / 魔法被害%.2f倍" % [form.get("mp_add",0),form.get("physical_rate",1),form.get("magic_rate",1)],10)
		line.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;_body.add_child(line)

func _render_mechanics() -> void:
	_body.add_child(_label("機構・行動の確認",14))
	var b:=game.current_battle()
	if b==null:
		var text:=RichTextLabel.new();text.size_flags_vertical=Control.SIZE_EXPAND_FILL;text.add_theme_font_size_override("normal_font_size",12)
		var lines: Array[String]=[]
		for rule in game.catalog.integration["enemy_rules"]:
			var known: Dictionary=game.integration_knowledge().get(rule["id"],{})
			if known.is_empty():continue
			lines.append(str(rule["name"])+(" / 確認済み" if known.get("confirmed",false) else " / 見立て"))
			for index in known.get("facts",[]):lines.append(rule["facts"][int(index)])
			lines.append(str(rule["hypothesis"]))
		text.text="観察した機構はまだありません。現地の緑の印や、戦闘中の観察で記録できます。" if lines.is_empty() else "\n".join(lines)
		_body.add_child(text)
	else:
		var select_actor:=OptionButton.new()
		for actor in b.living(Combatant.Team.PARTY):
			select_actor.add_item(actor.display_name);select_actor.set_item_metadata(select_actor.item_count-1,actor.id)
			if actor.id==_tactic_actor:select_actor.select(select_actor.item_count-1)
		_tactic_actor=select_actor.get_item_metadata(select_actor.selected)
		select_actor.item_selected.connect(func(index:int)->void:_tactic_actor=select_actor.get_item_metadata(index);_tactic_ability="__observe";_tactic_target="";_refresh())
		_body.add_child(select_actor)
		var actor:=b.actor_by_id(_tactic_actor)
		var skills:=OptionButton.new();skills.add_item("観察 / MP0");skills.set_item_metadata(0,"__observe")
		for id in actor.equipped:
			if game.abilities[id]["kind"]=="passive":continue
			skills.add_item("%s / %dMP" % [game.abilities[id]["name"],b.effects.cost(actor,game.abilities[id])]);skills.set_item_metadata(skills.item_count-1,id)
			if id==_tactic_ability:skills.select(skills.item_count-1)
		_tactic_ability=skills.get_item_metadata(skills.selected)
		skills.item_selected.connect(func(index:int)->void:_tactic_ability=skills.get_item_metadata(index);_tactic_target="";_refresh())
		_body.add_child(skills)
		var targets:=OptionButton.new()
		var mode_name: String="enemy" if _tactic_ability=="__observe" else game.abilities[_tactic_ability]["target"]
		for target in b.actors:
			var offered: bool=(target.team!=actor.team and target.is_alive()) if mode_name in ["enemy","enemies"] else (target.team==actor.team and (not target.is_alive() if mode_name=="fallen_ally" else target.is_alive()))
			if mode_name=="self":offered=target.id==actor.id
			if not offered:continue
			targets.add_item(target.display_name);targets.set_item_metadata(targets.item_count-1,target.id)
			if target.id==_tactic_target:targets.select(targets.item_count-1)
		_body.add_child(targets)
		_tactic_target=targets.get_item_metadata(targets.selected) if targets.item_count>0 else ""
		targets.item_selected.connect(func(index:int)->void:_tactic_target=targets.get_item_metadata(index);_refresh())
		var action:=BattleAction.observe(_tactic_actor,_tactic_target) if _tactic_ability=="__observe" else BattleAction.skill(_tactic_actor,_tactic_target,_tactic_ability)
		var preview:=b.preview_action(action)
		var text:=RichTextLabel.new();text.size_flags_vertical=Control.SIZE_EXPAND_FILL;text.add_theme_font_size_override("normal_font_size",10)
		text.text="\n".join(b.effects.description())+"\n"
		if _tactic_ability!="__observe":text.text+=str(game.abilities[_tactic_ability]["description"])+"\n"
		if preview["allowed"]:
			text.text+="消費MP%d / %s\n%s" % [preview["cost"],"予測ダメージ%d" % preview["predicted_damage"] if preview["predicted_damage"]>=0 else "ダメージ未確定",preview["condition"]]
		else:text.text+=str(preview["reason"])
		_body.add_child(text)
		var reserve:=_action_button(_body,"この行動を予約",{"kind":"reserve_tactic"});reserve.disabled=not preview["allowed"]
	_action_button(_body,"戻る",{"kind":"back"})

func _render_rule_upgrade() -> void:
	_body.add_child(_label("新しいルールへ引き継ぐ",14))
	var text:=RichTextLabel.new();text.size_flags_vertical=Control.SIZE_EXPAND_FILL;text.add_theme_font_size_override("normal_font_size",12)
	text.text="現在地、所持技、解決済みの出来事、魔物化と不可逆の履歴を保持します。JPは新しいマスター量への割合で換算し、取得済みマスターを維持します。\nEXPはLv1から開始し、侵蝕は戦闘0.2・専用技1行動0.1になります。祠で消した技には再習得の量が必要になります。\n終えた事件は巻き戻しません。新しい導入から遊ぶ場合は新規開始を使えます。更新は確認した場合だけ行います。"
	_body.add_child(text)
	_action_button(_body,"引き継ぐ",{"kind":"confirm_rule_upgrade"});_action_button(_body,"今は戻る",{"kind":"back"})
