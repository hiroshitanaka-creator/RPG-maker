extends Control

enum Mode { MENU, FIELD, DIALOGUE, BATTLE, PARTY, COMPLETE, DEFEAT, ASSETS_MISSING }

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


func _ready() -> void:
	Engine.max_fps = 60
	OS.add_logger(_diagnostics)
	game = GameSession.new()
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


func _process(_delta: float) -> void:
	if mode == Mode.FIELD and _walk_frame != 0 and Time.get_ticks_msec()-_last_move_ms > 180:
		_walk_frame = 0
		_refresh()


func _exit_tree() -> void:
	OS.remove_logger(_diagnostics)


func _input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
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
	if not game.new_game(party_size):
		_notice = "ゲームを開始できません。" + "\n".join(game.errors)
		_refresh()
		return
	if not ChapterOne.missing_art().is_empty():
		mode = Mode.ASSETS_MISSING
		_notice = "必要な素材が揃うと探索を開始できます。"
		print("ASSET_INPUT_REQUIRED: " + ", ".join(ChapterOne.missing_art()))
	else:
		mode = Mode.FIELD
		_notice = "矢印 / WASDで移動。黄色の印でEnterまたは『調べる』。"
	_refresh()


func _step() -> Dictionary:
	return ChapterOne.step(int(game.world_state().get("quest_step", 0)))


func automation_snapshot() -> Dictionary:
	var saved := game.export_state()
	var diagnostics := _diagnostics.messages()
	var names := {Mode.MENU:"menu", Mode.FIELD:"field", Mode.DIALOGUE:"dialogue", Mode.BATTLE:"battle", Mode.PARTY:"party", Mode.COMPLETE:"complete", Mode.DEFEAT:"defeat", Mode.ASSETS_MISSING:"assets_missing"}
	var result := {"mode": "error" if not diagnostics.is_empty() else names[mode],
		"chapter1_cleared": diagnostics.is_empty() and saved.get("progress_flags", {}).get("chapter1_cleared", false)}
	if not diagnostics.is_empty():
		result["errors"] = diagnostics
		return result
	if mode == Mode.FIELD:
		var world := game.world_state()
		result["player_cell"] = world["player_cell"]
		result["objective_cell"] = _step().get("cell", world["player_cell"])
		result["walkable_cells"] = ChapterOne.walkable_cells(world["location"])
	elif mode == Mode.BATTLE:
		var encounter := game.current_battle()
		var pending := encounter.pending()
		var targets := encounter.living(Combatant.Team.ENEMY)
		result["battle_input"] = {"ready": encounter.can_resolve(), "actor": "" if pending.is_empty() else pending[0].id, "enemy": "" if targets.is_empty() else targets[0].id}
	elif mode == Mode.DIALOGUE:
		result["line"] = _message_index
	return result


func submit_player_action(action: Dictionary) -> bool:
	var kind: String = str(action.get("kind", ""))
	var accepted := false
	match mode:
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
				accepted = game.set_world(world["location"], [next.x,next.y], world["quest_step"])
				if accepted:
					_last_move_ms = Time.get_ticks_msec()
					_facing = 1 if dx < 0 else (2 if dx > 0 else (3 if dy < 0 else 0))
					_walk_frame = (_walk_frame+1) % 4
					_notice = ""
			elif kind == "interact":
				accepted = _interact()
			elif kind == "party":
				mode = Mode.PARTY
				accepted = true
			elif kind == "save":
				accepted = game.save_game("user://save_v1.json")
				_notice = "保存しました。" if accepted else "今は保存できません。"
			elif kind == "rest" and game.world_state()["location"] == "town":
				accepted = game.rest()
				_notice = "宿でHPとMPを回復しました。"
		Mode.DIALOGUE:
			if kind == "confirm":
				_message_index += 1
				accepted = true
				if _message_index >= _messages.size():
					if _advance_after_dialogue:
						_advance_step()
					mode = Mode.FIELD
		Mode.BATTLE:
			accepted = _battle_action(action)
		Mode.PARTY:
			if kind == "back":
				mode = Mode.FIELD
				accepted = true
		Mode.COMPLETE:
			if kind == "save":
				accepted = game.save_game("user://save_v1.json")
				_notice = "保存しました。" if accepted else "保存できませんでした。"
	if accepted:
		_refresh()
	return accepted


func _interact() -> bool:
	var step := _step()
	var world := game.world_state()
	if step.is_empty() or world["location"] != step["location"] or world["player_cell"] != step["cell"]:
		_notice = "黄色の印へ移動して調べてください。"
		_refresh()
		return false
	match step["kind"]:
		"dialogue":
			if step.get("rest", false):
				game.rest()
			_show_dialogue(step["text"], true)
		"travel":
			return game.set_world(step["destination"], step["spawn"], int(world["quest_step"])+1)
		"battle":
			var encounter := game.start_battle(step["enemies"], 20260919 + int(world["quest_step"]))
			if encounter == null:
				return false
			mode = Mode.BATTLE
			_battle_log = ["相手の特徴と残りHPを見て、行動を選ぼう。"]
			_actor = encounter.pending()[0].id
			_target_action.clear()
		"complete":
			game.set_progress_flag("chapter1_cleared")
			game.set_world(world["location"], world["player_cell"], ChapterOne.STEPS.size())
			mode = Mode.COMPLETE
	return true


func _advance_step() -> void:
	var step := _step()
	if step.has("flag"):
		game.set_progress_flag(step["flag"])
	for identifier in step.get("flags", []):
		game.set_progress_flag(identifier)
	var world := game.world_state()
	game.set_world(world["location"], world["player_cell"], int(world["quest_step"])+1)


func _show_dialogue(lines: Array, advance: bool) -> void:
	_messages.assign(lines)
	_message_index = 0
	_advance_after_dialogue = advance
	mode = Mode.DIALOGUE


func _battle_action(action: Dictionary) -> bool:
	var encounter := game.current_battle()
	var kind: String = str(action.get("kind", ""))
	if kind == "resolve_round":
		if not encounter.can_resolve():
			return false
		var events := encounter.resolve_round()
		for event in events:
			_battle_log.append(event["message"])
		_target_action.clear()
		if encounter.phase == BattleState.Phase.VICTORY:
			var before := game.export_state()
			game.finish_battle()
			var lines: Array = ["勝利！"]
			var after := game.export_state()
			for i in range(after["party"].size()):
				var actor: Dictionary = after["party"][i]
				var job_id: String = actor["job_id"]
				var gain := int(actor["jp"].get(job_id, 0))-int(before["party"][i]["jp"].get(job_id, 0))
				lines.append("%s: %sのJP +%d" % [actor["name"], game.jobs[job_id]["name"], gain])
				if actor["mastered_jobs"].size() > before["party"][i]["mastered_jobs"].size():
					lines.append("%sが%sをマスター。" % [actor["name"], game.jobs[job_id]["name"]])
				if actor["monster_form"] != before["party"][i]["monster_form"]:
					lines.append("%sが魔物化した。能力と使用可能な技、装着枠が変化した。" % actor["name"])
			lines.append_array(_step().get("text", []))
			_show_dialogue(lines, true)
		elif encounter.phase == BattleState.Phase.DEFEAT:
			game.finish_battle()
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
			values.append(str(actor["erosion"]))
		header.add_child(_label("侵蝕 " + " / ".join(values), 10))
	match mode:
		Mode.MENU: _render_menu()
		Mode.ASSETS_MISSING: _render_missing()
		Mode.FIELD: _render_field()
		Mode.DIALOGUE: _render_dialogue()
		Mode.BATTLE: _render_battle()
		Mode.PARTY: _render_party()
		Mode.COMPLETE: _render_complete()
		Mode.DEFEAT:
			_body.add_child(_label("全員が戦闘不能になった。", 16))
			_button(_body, "セーブから再開", _load_save)
			_button(_body, "タイトルへ", _to_menu)
	if not _notice.is_empty():
		_body.add_child(_label(_notice, 10))


func _render_menu() -> void:
	_body.add_child(_label("職を選び、技を組み、自分の姿を決める。", 13))
	_body.add_child(_label("第1章  閉じた道", 16))
	if not game.export_state().is_empty():
		_button(_body, "現在の冒険に戻る", _resume_current)
	_button(_body, "新しくはじめる（4人）", start_new_game.bind(4))
	_button(_body, "新しくはじめる（3人）", start_new_game.bind(3))
	_button(_body, "セーブから再開", _load_save)
	_button(_body, "終了", func() -> void: get_tree().quit())
	if not game.errors.is_empty():
		_body.add_child(_label("\n".join(game.errors), 10))
	var missing := ChapterOne.missing_art()
	if not missing.is_empty():
		_body.add_child(_label("開始に必要な素材が未取込: %d件" % missing.size(), 10))


func _resume_current() -> void:
	mode = Mode.COMPLETE if game.export_state()["progress_flags"].get("chapter1_cleared", false) else Mode.FIELD
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
	_body.add_child(_label("%s  /  %s" % [ChapterOne.TITLES[world["location"]], _step().get("objective", "町を歩く")], 11))
	var map := WorldView.new()
	map.location = world["location"]
	map.player_cell = Vector2i(int(world["player_cell"][0]), int(world["player_cell"][1]))
	var goal: Array = _step().get("cell", world["player_cell"])
	map.objective = Vector2i(int(goal[0]), int(goal[1]))
	map.facing = _facing
	map.walk_frame = _walk_frame
	map.custom_minimum_size = Vector2(480, 160)
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map.cell_clicked.connect(_map_clicked)
	_body.add_child(map)
	var row := HBoxContainer.new()
	_body.add_child(row)
	_action_button(row, "調べる", {"kind":"interact"})
	_action_button(row, "編成", {"kind":"party"})
	_action_button(row, "セーブ", {"kind":"save"})
	if world["location"] == "town":
		_action_button(row, "宿で休む", {"kind":"rest"})
	_button(row, "メニュー", _to_menu)


func _map_clicked(cell: Vector2i) -> void:
	var current: Array = game.world_state()["player_cell"]
	if cell == Vector2i(int(current[0]), int(current[1])):
		submit_player_action({"kind":"interact"})
	else:
		submit_player_action({"kind":"move", "dx":cell.x-int(current[0]), "dy":cell.y-int(current[1])})


func _render_dialogue() -> void:
	var row := HBoxContainer.new()
	_body.add_child(row)
	for i in range(game.export_state()["party"].size()):
		var face := _picture("res://assets/characters/pc_%02d/portrait.png" % (i+1), Vector2(64,64))
		row.add_child(face)
	var message := _label(_messages[_message_index], 14)
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_body.add_child(message)
	_action_button(_body, "次へ  Enter", {"kind":"confirm"})


func _render_battle() -> void:
	var encounter := game.current_battle()
	var tools := HBoxContainer.new()
	_body.add_child(tools)
	var caption := _label("第%dターン / 回復薬 %d" % [encounter.round_number, encounter.potions], 11)
	caption.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tools.add_child(caption)
	_action_button(tools, "選び直す", {"kind":"clear_actions"})
	var resolve := _action_button(tools, "ターン実行", {"kind":"resolve_round"})
	resolve.disabled = not encounter.can_resolve()
	var stage := HBoxContainer.new()
	_body.add_child(stage)
	var foes := HBoxContainer.new()
	foes.custom_minimum_size.x = 215
	stage.add_child(foes)
	var definitions: Array = _step().get("enemies", [])
	var index := 0
	for actor in encounter.actors:
		if actor.team != Combatant.Team.ENEMY:
			continue
		var card := VBoxContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.add_child(_picture("res://assets/monsters/%s/idle.png" % definitions[index], Vector2(64,64)))
		card.add_child(_label("%s\nHP%d/%d" % [actor.display_name, actor.hp, actor.max_hp], 10))
		foes.add_child(card)
		index += 1
	var allies := GridContainer.new()
	allies.columns = 2
	allies.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stage.add_child(allies)
	for actor in encounter.actors:
		if actor.team != Combatant.Team.PARTY:
			continue
		var button := _button(allies, "%s%s HP%d\nMP%d/%d" % [actor.display_name, " ✓" if encounter.queued.has(actor.id) else "", actor.hp, actor.mp, actor.max_mp], _select_actor.bind(actor.id))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.disabled = not actor.is_alive()
	if not _actor.is_empty():
		_body.add_child(_label("%sの行動" % encounter.actor_by_id(_actor).display_name, 10))
		var commands := GridContainer.new()
		commands.columns = 4
		_body.add_child(commands)
		_button(commands, "攻撃", _choose_target.bind("attack", ""))
		_action_button(commands, "防御", {"kind":"guard", "actor":_actor})
		var actor := encounter.actor_by_id(_actor)
		for identifier in actor.equipped:
			var definition: Dictionary = game.abilities[identifier]
			var button := _button(commands, "%s %dMP" % [definition["name"], int(definition["cost"])], _choose_target.bind("ability", identifier))
			button.disabled = encounter.targets_for(_actor, BattleAction.Kind.ABILITY, identifier).is_empty()
		var potion := _button(commands, "回復薬", _choose_target.bind("potion", ""))
		potion.disabled = encounter.targets_for(_actor, BattleAction.Kind.ITEM).is_empty()
	if not _target_action.is_empty():
		var row := HBoxContainer.new()
		_body.add_child(row)
		var action_kind := BattleAction.Kind.ABILITY if _target_action["kind"] == "ability" else (BattleAction.Kind.ITEM if _target_action["kind"] == "potion" else BattleAction.Kind.ATTACK)
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
	_body.add_child(log)


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
	var job_row := HBoxContainer.new()
	_body.add_child(job_row)
	var jobs := OptionButton.new()
	jobs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for identifier in game.jobs:
		jobs.add_item(game.jobs[identifier]["name"])
		jobs.set_item_metadata(jobs.item_count-1, identifier)
		if identifier == actor["job_id"]:
			jobs.select(jobs.item_count-1)
	job_row.add_child(jobs)
	_button(job_row, "この職に転職", func() -> void:
		var identifier: String = jobs.get_item_metadata(jobs.selected)
		_notice = "転職しました。装着済みの技は持ち越します。" if game.change_job(actor["id"], identifier) else "今はその職業へ変更できません。"
		_refresh())
	_body.add_child(_label("魔物職はマスターで魔物化。侵蝕90以降は人間職へ戻れません。", 10))
	_body.add_child(_label("JP %d/%d  %s / 装着 %d/%d" % [int(actor["jp"].get(actor["job_id"],0)), int(game.jobs[actor["job_id"]]["mastery_cost"]), "マスター" if actor["job_id"] in actor["mastered_jobs"] else "修練中", actor["equipped_abilities"].size(), game.slot_limit(actor["id"])], 11))
	var slots := GridContainer.new()
	slots.columns = 2
	_body.add_child(slots)
	for identifier in actor["equipped_abilities"]:
		_button(slots, game.abilities[identifier]["name"] + "を外す", _unequip.bind(actor["id"], identifier))
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
	var current := game.effective_stats(actor["id"])
	_body.add_child(_label("HP%d/%d MP%d/%d\n攻撃%d 防御%d 魔力%d 魔防%d 速さ%d" % [actor["hp"],actor["max_hp"],actor["mp"],actor["max_mp"],current["attack"],current["defense"],current["magic"],current["resistance"],current["speed"]], 11))
	if not str(actor["monster_form"]).is_empty():
		_body.add_child(_label("魔物化: " + game.jobs[actor["monster_form"]]["name"], 11))
		var release := _button(_body, "町の祠で解除（魔物の技を全消去）", _purify.bind(actor["id"]))
		release.disabled = game.world_state()["location"] != "town" or actor["irreversible"]
	_body = outer
	_action_button(_body, "探索へ戻る", {"kind":"back"})


func _unequip(actor_id: String, identifier: String) -> void:
	_notice = "装着を外しました。" if game.unequip_ability(actor_id, identifier) else "外せませんでした。"
	_refresh()


func _purify(actor_id: String) -> void:
	_notice = "魔物の技を手放し、姿を戻しました。" if game.release_monster_form(actor_id, "purification_shrine") else "解除条件を満たしていません。"
	_refresh()


func _render_complete() -> void:
	_body.add_child(_label("第1章  閉じた道  クリア", 17))
	_body.add_child(_label("番人はもう一度、板を二度打った。\nその音の意味は、まだ分からない。", 14))
	_action_button(_body, "冒険の記録を保存", {"kind":"save"})
	_button(_body, "タイトルへ", _to_menu)


func _load_save() -> void:
	if not game.load_game("user://save_v1.json"):
		_notice = "読み込めるセーブがありません。"
		_refresh()
		return
	mode = Mode.COMPLETE if game.export_state()["progress_flags"].get("chapter1_cleared", false) else Mode.FIELD
	if not ChapterOne.missing_art().is_empty():
		mode = Mode.ASSETS_MISSING
	_notice = "冒険の記録を読み込みました。"
	_refresh()


func _to_menu() -> void:
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
