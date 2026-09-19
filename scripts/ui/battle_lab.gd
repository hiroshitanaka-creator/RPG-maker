extends Control

const INK := Color("eef2f7")
const MUTED := Color("a7b5c8")
const ACCENT := Color("e0bc78")
const PANEL := Color("172335")
const BORDER := Color("405169")

var catalog: BattleCatalog
var battle: BattleState
var job_ids: Array[String] = ["warrior", "martial_artist", "priest", "mage"]
var equipped: Array = [["power_strike", "firm_guard"], ["double_strike", "breath"], ["heal", "revive"], ["fire", "ice"]]
var playback_delay_seconds: float = 0.16
var playing: bool = false

var tabs: TabContainer
var setup_hint: Label
var stat_labels: Array[Label] = []
var job_controls: Array[OptionButton] = []
var ability_controls: Array = []
var encounter_control: OptionButton
var start_button: Button
var turn_button: Button
var reset_button: Button
var edit_button: Button
var skip_button: Button
var round_label: Label
var potion_label: Label
var prompt_label: Label
var action_buttons: Array[Button] = []
var actor_buttons: Dictionary = {}
var enemy_labels: Dictionary = {}
var target_row: HBoxContainer
var party_row: HBoxContainer
var enemy_row: HBoxContainer
var log_view: RichTextLabel

var _selected_actor: String = ""
var _selected_kind: BattleAction.Kind = BattleAction.Kind.ATTACK
var _selected_ability: String = ""
var _skip_playback: bool = false
var _history: Array[String] = []


func _ready() -> void:
	_apply_theme()
	catalog = BattleCatalog.new()
	if not catalog.errors.is_empty():
		var error_label := _label("戦闘データのエラー\n" + "\n".join(catalog.errors), 12)
		add_child(error_label)
		return
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 6)
	add_child(margin)
	var column := _column()
	margin.add_child(column)
	var heading := _row()
	column.add_child(heading)
	var title := _label("RPG-maker", 17)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(title)
	heading.add_child(_label("戦闘検証 / 仮数値", 10, ACCENT))
	tabs = TabContainer.new()
	tabs.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(tabs)
	_build_setup()
	_build_battle()
	tabs.set_tab_disabled(1, true)
	_refresh_setup()


func _apply_theme() -> void:
	var ui_theme := Theme.new()
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Yu Gothic UI", "Meiryo", "Noto Sans CJK JP", "sans-serif"])
	ui_theme.default_font = font
	ui_theme.default_font_size = 11
	ui_theme.set_color("font_color", "Label", INK)
	ui_theme.set_color("default_color", "RichTextLabel", INK)
	for control_type in ["Button", "OptionButton"]:
		for state in ["normal", "hover", "pressed", "focus", "disabled"]:
			var style := StyleBoxFlat.new()
			style.bg_color = Color("223149") if state in ["hover", "pressed"] else PANEL
			style.border_color = ACCENT if state in ["focus", "pressed"] else BORDER
			style.set_border_width_all(1)
			style.set_corner_radius_all(3)
			style.content_margin_left = 5
			style.content_margin_right = 5
			style.content_margin_top = 2
			style.content_margin_bottom = 2
			ui_theme.set_stylebox(state, control_type, style)
		ui_theme.set_color("font_color", control_type, INK)
		ui_theme.set_color("font_disabled_color", control_type, Color("7f8c9d"))
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color("101a29")
	panel.content_margin_left = 5
	panel.content_margin_right = 5
	panel.content_margin_top = 4
	panel.content_margin_bottom = 4
	ui_theme.set_stylebox("panel", "TabContainer", panel)
	theme = ui_theme


func _build_setup() -> void:
	var column := _column()
	column.name = "編成"
	tabs.add_child(column)
	column.add_child(_label("4人 / 人間職5種 / 習得済み10技を2枠へ装着", 10, MUTED))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 3)
	column.add_child(grid)
	for heading in ["仲間・能力値", "現在の職業", "装着 1", "装着 2"]:
		grid.add_child(_label(heading, 10, ACCENT))
	var available_jobs := catalog.playable_jobs()
	var available_abilities := catalog.training_abilities()
	for i in range(4):
		var stats_label := _label("", 10)
		stats_label.custom_minimum_size = Vector2(99, 27)
		grid.add_child(stats_label)
		stat_labels.append(stats_label)
		var jobs := OptionButton.new()
		jobs.name = "Job%d" % i
		jobs.custom_minimum_size = Vector2(78, 27)
		for job_id in available_jobs:
			jobs.add_item(catalog.jobs[job_id]["name"])
			jobs.set_item_metadata(jobs.item_count - 1, job_id)
		jobs.item_selected.connect(_job_changed.bind(i))
		grid.add_child(jobs)
		job_controls.append(jobs)
		var controls: Array[OptionButton] = []
		for slot in range(2):
			var skills := OptionButton.new()
			skills.name = "Ability%d_%d" % [i, slot]
			skills.custom_minimum_size = Vector2(120, 27)
			skills.add_item("なし")
			skills.set_item_metadata(0, "")
			for ability_id in available_abilities:
				var ability: Dictionary = catalog.abilities[ability_id]
				skills.add_item("%s %dMP" % [ability["name"], int(ability["cost"])])
				skills.set_item_metadata(skills.item_count - 1, ability_id)
				skills.set_item_tooltip(skills.item_count - 1, ability["description"])
			skills.item_selected.connect(_ability_changed.bind(i, slot))
			grid.add_child(skills)
			controls.append(skills)
		ability_controls.append(controls)
	var footer := _row()
	footer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	footer.alignment = BoxContainer.ALIGNMENT_END
	column.add_child(footer)
	encounter_control = OptionButton.new()
	encounter_control.name = "Encounter"
	encounter_control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for encounter_id in catalog.encounters:
		encounter_control.add_item(catalog.encounters[encounter_id]["name"])
		encounter_control.set_item_metadata(encounter_control.item_count - 1, encounter_id)
	footer.add_child(encounter_control)
	start_button = _button("この編成で戦う", "StartBattle", start_battle)
	start_button.custom_minimum_size = Vector2(155, 26)
	footer.add_child(start_button)
	setup_hint = _label("魔物職・上級職と成長は未実装。編成の比較用です。", 10, MUTED)
	column.add_child(setup_hint)


func _build_battle() -> void:
	var column := _column()
	column.name = "戦闘"
	tabs.add_child(column)
	var toolbar := _row()
	column.add_child(toolbar)
	round_label = _label("第1ターン", 11, ACCENT)
	round_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	toolbar.add_child(round_label)
	potion_label = _label("薬 3", 10)
	toolbar.add_child(potion_label)
	edit_button = _button("選び直す", "EditActions", _clear_actions)
	toolbar.add_child(edit_button)
	reset_button = _button("編成へ", "BackToSetup", _back_to_setup)
	toolbar.add_child(reset_button)
	turn_button = _button("ターン実行", "ResolveRound", execute_round)
	toolbar.add_child(turn_button)
	party_row = _row()
	column.add_child(party_row)
	enemy_row = _row()
	column.add_child(enemy_row)
	prompt_label = _label("", 11, ACCENT)
	column.add_child(prompt_label)
	var commands := _row()
	column.add_child(commands)
	for i in range(5):
		var button := _button("", "Command%d" % i, _command_pressed.bind(i))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.custom_minimum_size.y = 24
		commands.add_child(button)
		action_buttons.append(button)
	target_row = _row()
	target_row.custom_minimum_size.y = 23
	column.add_child(target_row)
	var log_row := _row()
	log_row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(log_row)
	log_view = RichTextLabel.new()
	log_view.name = "BattleLog"
	log_view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	log_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log_view.custom_minimum_size.y = 35
	log_view.scroll_following = true
	log_view.bbcode_enabled = false
	log_view.add_theme_font_size_override("normal_font_size", 10)
	log_row.add_child(log_view)
	skip_button = _button("結果\nまで", "SkipPlayback", func() -> void: _skip_playback = true)
	log_row.add_child(skip_button)


func _job_changed(index: int, member: int) -> void:
	job_ids[member] = job_controls[member].get_item_metadata(index)
	_refresh_setup()
	setup_hint.text = "職業を変更しました。習得済みの装着技は持ち越します。"


func _ability_changed(index: int, member: int, slot: int) -> void:
	var control: OptionButton = ability_controls[member][slot]
	var identifier: String = control.get_item_metadata(index)
	var next_slots: Array = equipped[member].duplicate()
	next_slots[slot] = identifier
	var selected: Array[String] = []
	for value in next_slots:
		if not str(value).is_empty():
			selected.append(value)
	var error := Loadout.validate(catalog.training_abilities(), selected, 2)
	if error.is_empty():
		equipped[member] = next_slots
		setup_hint.text = catalog.abilities[identifier]["description"] if not identifier.is_empty() else "装着を外しました。"
	else:
		setup_hint.text = error
	_refresh_setup()


func _refresh_setup() -> void:
	for i in range(4):
		var stats: Dictionary = catalog.jobs[job_ids[i]]["stats"]
		stat_labels[i].text = "仲間%d  攻%d / 魔%d\nHP%d / MP%d" % [i + 1, int(stats["attack"]), int(stats["magic"]), int(stats["hp"]), int(stats["mp"])]
		_select_metadata(job_controls[i], job_ids[i])
		for slot in range(2):
			_select_metadata(ability_controls[i][slot], equipped[i][slot])


func start_battle() -> void:
	if playing:
		return
	var selected_loadouts: Array = []
	for slots in equipped:
		var selected: Array[String] = []
		for identifier in slots:
			if not str(identifier).is_empty():
				selected.append(identifier)
		selected_loadouts.append(selected)
	var encounter_id: String = encounter_control.get_item_metadata(encounter_control.selected)
	battle = BattleState.new(catalog.make_party(job_ids, selected_loadouts), catalog.make_enemies(encounter_id), catalog)
	if battle.phase == BattleState.Phase.INVALID:
		setup_hint.text = battle.last_error
		return
	_history.clear()
	log_view.text = "仲間の行動を選択。選択済みの仲間を押すと変更できます。"
	_clear_children(party_row)
	_clear_children(enemy_row)
	actor_buttons.clear()
	enemy_labels.clear()
	for actor in battle.actors:
		if actor.team == Combatant.Team.PARTY:
			var button := _button("", "Actor_" + actor.id, _select_actor.bind(actor.id))
			button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			button.add_theme_font_size_override("font_size", 10)
			party_row.add_child(button)
			actor_buttons[actor.id] = button
		else:
			var label := _label("", 10, MUTED)
			label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			enemy_row.add_child(label)
			enemy_labels[actor.id] = label
	_selected_actor = battle.pending()[0].id
	tabs.set_tab_disabled(1, false)
	tabs.current_tab = 1
	_clear_children(target_row)
	_render_battle(battle.snapshot())


func _select_actor(identifier: String) -> void:
	if playing or battle.phase != BattleState.Phase.INPUT or not battle.actor_by_id(identifier).is_alive():
		return
	_selected_actor = identifier
	_clear_children(target_row)
	_render_battle(battle.snapshot())


func _command_pressed(index: int) -> void:
	if playing or _selected_actor.is_empty():
		return
	var actor := battle.actor_by_id(_selected_actor)
	_selected_ability = ""
	match index:
		0:
			_selected_kind = BattleAction.Kind.ATTACK
		1:
			_selected_kind = BattleAction.Kind.GUARD
		2, 3:
			_selected_kind = BattleAction.Kind.ABILITY
			_selected_ability = actor.equipped[index - 2]
		4:
			_selected_kind = BattleAction.Kind.ITEM
	var targets := battle.targets_for(actor.id, _selected_kind, _selected_ability)
	_clear_children(target_row)
	if _selected_kind == BattleAction.Kind.GUARD or (not _selected_ability.is_empty() and catalog.abilities[_selected_ability]["target"] == "self"):
		_confirm_target(actor.id)
		return
	prompt_label.text = "%sの対象を選択" % actor.display_name
	for target in targets:
		var button := _button(target.display_name, "Target_" + target.id, _confirm_target.bind(target.id))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		target_row.add_child(button)
	target_row.add_child(_button("戻る", "CancelTarget", func() -> void: _select_actor(actor.id)))


func _confirm_target(identifier: String) -> void:
	var action := BattleAction.new(_selected_kind, _selected_actor, identifier, _selected_ability)
	var error := battle.queue_action(action)
	if not error.is_empty():
		prompt_label.text = error
		return
	_clear_children(target_row)
	var remaining := battle.pending()
	_selected_actor = remaining[0].id if not remaining.is_empty() else ""
	_render_battle(battle.snapshot())


func _clear_actions() -> void:
	if playing:
		return
	battle.clear_queue()
	_selected_actor = battle.pending()[0].id if not battle.pending().is_empty() else ""
	_clear_children(target_row)
	_render_battle(battle.snapshot())


func _back_to_setup() -> void:
	if not playing:
		tabs.current_tab = 0


func execute_round() -> void:
	if playing or battle == null or not battle.can_resolve():
		return
	playing = true
	_skip_playback = false
	tabs.set_tab_disabled(0, true)
	_clear_children(target_row)
	var events := battle.resolve_round()
	for event in events:
		_history.append(event["message"])
		if _history.size() > 150:
			_history.pop_front()
		log_view.text = "\n".join(_history)
		_render_battle(event["snapshot"])
		if playback_delay_seconds > 0.0 and not _skip_playback:
			await get_tree().create_timer(playback_delay_seconds).timeout
	playing = false
	tabs.set_tab_disabled(0, false)
	var remaining := battle.pending()
	_selected_actor = remaining[0].id if battle.phase == BattleState.Phase.INPUT and not remaining.is_empty() else ""
	_render_battle(battle.snapshot())


func _render_battle(state: Dictionary) -> void:
	round_label.text = "第%dターン" % int(state["round"])
	potion_label.text = "薬 %d" % int(state["potions"])
	for member in state["actors"]:
		var identifier: String = member["id"]
		if actor_buttons.has(identifier):
			var button: Button = actor_buttons[identifier]
			button.text = "%s%s  HP%d/%d\nMP%d/%d%s" % [member["name"], " ✓" if battle.queued.has(identifier) else "", int(member["hp"]), int(member["max_hp"]), int(member["mp"]), int(member["max_mp"]), " 戦闘不能" if int(member["hp"]) == 0 else ""]
			button.disabled = playing or battle.phase != BattleState.Phase.INPUT or int(member["hp"]) == 0
			button.modulate = ACCENT if identifier == _selected_actor and not playing else Color.WHITE
		else:
			enemy_labels[identifier].text = "%s\nHP %d/%d%s" % [member["name"], int(member["hp"]), int(member["max_hp"]), " 撃破" if int(member["hp"]) == 0 else ""]
	turn_button.disabled = playing or not battle.can_resolve()
	edit_button.disabled = playing or battle.phase != BattleState.Phase.INPUT or battle.queued.is_empty()
	reset_button.disabled = playing
	skip_button.disabled = not playing
	for button in action_buttons:
		button.disabled = true
	if playing:
		prompt_label.text = "行動を解決中"
		return
	if battle.phase in [BattleState.Phase.VICTORY, BattleState.Phase.DEFEAT]:
		prompt_label.text = "勝利！ 編成へ戻って再戦できます。" if battle.phase == BattleState.Phase.VICTORY else "全滅。編成へ戻って再挑戦できます。"
		return
	if _selected_actor.is_empty():
		prompt_label.text = "全員選択済み。ターン実行で確定。"
		return
	var actor := battle.actor_by_id(_selected_actor)
	prompt_label.text = "%s（%s）の行動" % [actor.display_name, catalog.jobs[actor.job_id]["name"]]
	action_buttons[0].text = "攻撃"
	action_buttons[1].text = "防御"
	action_buttons[4].text = "回復薬"
	action_buttons[0].disabled = false
	action_buttons[1].disabled = false
	action_buttons[4].disabled = battle.targets_for(actor.id, BattleAction.Kind.ITEM).is_empty()
	for slot in range(2):
		var button: Button = action_buttons[slot + 2]
		if slot >= actor.equipped.size():
			button.text = "未装着"
			button.tooltip_text = "編成画面で技を装着できます。"
			continue
		var ability_id := actor.equipped[slot]
		var definition: Dictionary = catalog.abilities[ability_id]
		button.text = "%s %dMP" % [definition["name"], int(definition["cost"]) ]
		button.tooltip_text = definition["description"]
		button.disabled = battle.targets_for(actor.id, BattleAction.Kind.ABILITY, ability_id).is_empty()


static func _select_metadata(control: OptionButton, value: String) -> void:
	for i in range(control.item_count):
		if control.get_item_metadata(i) == value:
			control.select(i)
			return


static func _clear_children(node: Node) -> void:
	for child in node.get_children():
		node.remove_child(child)
		child.queue_free()


static func _label(value: String, font_size: int = 11, color: Color = INK) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	return label


static func _button(value: String, identifier: String, action: Callable) -> Button:
	var button := Button.new()
	button.text = value
	button.name = identifier
	button.pressed.connect(action)
	return button


static func _row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	return row


static func _column() -> VBoxContainer:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 3)
	return column
