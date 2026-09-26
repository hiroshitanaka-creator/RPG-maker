class_name FirstRegionScreen
extends Control
## 最初の地方の表示だけを担当する。状態の変更は通常の操作として親へ通知する。
signal action_requested(action: Dictionary)
var game: GameSession
var screen_mode := "world"
var actor := ""
var target_action: Dictionary = {}
var message := ""
var speaker := ""
var speaking_actor := ""
var notice := ""
var place_name := ""
var walk_frame := 0
var show_field_buttons := true
var battle_background := "plains"
var replay: Dictionary = {}
var replay_members: Array = []
var replay_enemies: Array = []
var focus_label := ""
var flash_alpha := 0.0
var map_view: FirstRegionView
var place_label: Label
var _first_button: Button
var recovery_available := false

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	if screen_mode=="battle" or not replay.is_empty():_battle()
	else:
		map_view=FirstRegionView.new()
		map_view.saved=game.export_state()
		map_view.walk_frame=walk_frame
		map_view.speaking_actor=speaking_actor
		map_view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		add_child(map_view)
		match screen_mode:
			"world":_world()
			"dialogue":_dialogue()
			"commands":_commands()
			"items":_items()
			"shop":_shop()
			"defeat":_defeat()
	if flash_alpha>0.0:
		var flash := ColorRect.new()
		flash.color=Color(1,1,0.94,flash_alpha)
		flash.mouse_filter=Control.MOUSE_FILTER_IGNORE
		flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		add_child(flash)
		create_tween().tween_property(flash,"modulate:a",0.0,0.18)
	if screen_mode=="battle":
		if not focus_label.is_empty():
			for button in find_children("*","Button",true,false):
				if button.text==focus_label and not button.disabled:button.grab_focus.call_deferred();return
			focus_command.call_deferred()
	elif is_instance_valid(_first_button) and screen_mode in ["commands","items","shop"]:_first_button.grab_focus.call_deferred()

func focus_command() -> void:
	if is_instance_valid(_first_button):_first_button.grab_focus()

func _label(text_value: String, font_size: int = 13) -> Label:
	var label := Label.new()
	label.text=text_value
	label.add_theme_font_size_override("font_size",font_size)
	label.add_theme_color_override("font_color",Color("f5f3e8"))
	label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	return label

func _window(rect: Rect2) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.position=rect.position
	panel.size=rect.size
	var box := StyleBoxTexture.new()
	box.texture=load("res://assets/ui/window_bright.png")
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:
		box.set_texture_margin(side,8.0)
		box.set_content_margin(side,8.0)
	box.modulate_color=Color(1,1,1,0.93)
	panel.add_theme_stylebox_override("panel",box)
	add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",3)
	panel.add_child(column)
	return column

func _button(parent: Node, title: String, action: Dictionary, enabled: bool = true) -> Button:
	var button := Button.new()
	button.text=title
	button.disabled=not enabled
	button.add_theme_font_size_override("font_size",12)
	for state in ["normal","hover","pressed","focus","disabled"]:
		var box := StyleBoxFlat.new()
		box.bg_color=Color(1,1,1,0.10) if state in ["hover","pressed"] else Color(0,0,0,0)
		box.border_color=Color("f5f3e8")
		box.set_border_width_all(1 if state=="focus" else 0)
		box.content_margin_top=1;box.content_margin_bottom=1;box.content_margin_left=4;box.content_margin_right=4
		button.add_theme_stylebox_override(state,box)
	button.pressed.connect(func()->void:action_requested.emit(action))
	parent.add_child(button)
	if _first_button==null and enabled:_first_button=button
	return button

func _world() -> void:
	# 入力契約を改訂するまでは、現在の一般プレイヤー向け操作を保持する。
	if show_field_buttons:
		var save := _button(self,"セーブ",{"kind":"save"});save.position=Vector2(8,262);save.size=Vector2(66,20)
		var menu := _button(self,"メニュー",{"kind":"ui_menu"});menu.position=Vector2(436,262);menu.size=Vector2(68,20)
	if not place_name.is_empty():
		place_label=_label(place_name,16)
		place_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
		place_label.add_theme_color_override("font_shadow_color",Color("111827"))
		place_label.add_theme_constant_override("shadow_offset_x",1)
		place_label.add_theme_constant_override("shadow_offset_y",1)
		place_label.position=Vector2(90,12);place_label.size=Vector2(332,24);add_child(place_label)
	if not notice.is_empty():_window(Rect2(72,228,368,34)).add_child(_label(notice,12))

func _dialogue() -> void:
	var name_box := _window(Rect2(16,165,180,28));name_box.add_child(_label(speaker if not speaker.is_empty() else "カイナ",12))
	var dialogue := _window(Rect2(8,191,496,88));dialogue.add_child(_label(message,14))
	var next := _button(self,"▼",{"kind":"confirm"});next.position=Vector2(474,251);next.size=Vector2(24,20)

func _commands() -> void:
	var column := _window(Rect2(12,12,220,264))
	column.add_child(_label("メニュー",15))
	_button(column,"どうぐ",{"kind":"ui_items"})
	_button(column,"じょうたい・そうび・へんせい",{"kind":"party"})
	_button(column,"手帳",{"kind":"journal"})
	_button(column,"セーブ",{"kind":"save"})
	_button(column,"手動セーブから再開",{"kind":"ui_load"})
	_button(column,"現在の冒険に戻る",{"kind":"ui_resume"})
	_button(column,"タイトルへ",{"kind":"ui_title"})
	if not notice.is_empty():column.add_child(_label(notice,11))
	var status := _window(Rect2(248,12,252,160))
	for member in game.export_state()["party"]:
		status.add_child(_label("%s  HP %d/%d  MP %d/%d" % [member["name"],member["hp"],member["max_hp"],member["mp"],member["max_mp"]],12))

func _items() -> void:
	var state := game.export_state()
	var column := _window(Rect2(30,20,452,248))
	column.add_child(_label("どうぐ",15))
	_button(column,"世界地図を見る",{"kind":"ui_atlas"},int(state["inventory"].get("world_map",0))>0)
	column.add_child(_label("回復薬 ×%d　使う人を選んでください" % int(state["inventory"].get("potion",0)),12))
	for member in state["party"]:
		_button(column,"%s  HP %d/%d" % [member["name"],member["hp"],member["max_hp"]],{"kind":"ui_potion","actor":member["id"]},member["hp"]>0 and member["hp"]<member["max_hp"] and state["inventory"]["potion"]>0)
	if state["inventory"].get("gate_pass",0)>0:column.add_child(_label("関所の通行証",12))
	_button(column,"戻る",{"kind":"ui_back"})

func _shop() -> void:
	var column := _window(Rect2(40,156,432,122))
	column.add_child(_label(speaker,14))
	column.add_child(_label("所持金 %d" % game.export_state()["first_region"]["coins"],12))
	if speaker=="道具屋":_button(column,"回復薬を買う　5",{"kind":"buy_potion"})
	else:_button(column,"補強剣を買う　15",{"kind":"buy_weapon"})
	_button(column,"やめる",{"kind":"back"})
	if not notice.is_empty():column.add_child(_label(notice,11))

func _defeat() -> void:
	var column := _window(Rect2(54,58,404,178))
	column.add_child(_label("全員が戦闘不能になった。",16))
	column.add_child(_label("戦闘前の場所・編成・所持品から再開できます。",12))
	_button(column,"戦闘前へ戻る",{"kind":"retry_battle"},recovery_available)
	_button(column,"手動セーブから再開",{"kind":"ui_load"})
	_button(column,"タイトルへ",{"kind":"ui_title"})

func _battle() -> void:
	var arena := RpgBattleView.new()
	arena.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	arena.background=battle_background
	arena.members=game.export_state()["party"] if replay.is_empty() else replay_members
	arena.enemy_ids=game.current_enemy_ids() if replay.is_empty() else replay_enemies
	arena.definitions=game.enemy_definitions
	arena.selected_actor=actor
	var encounter := game.current_battle()
	if encounter!=null:
		for unit in encounter.actors:
			if unit.team==Combatant.Team.ENEMY:arena.enemy_hp[unit.id]=unit.hp
	if not replay.is_empty():
		arena.effect_target=str(replay.get("target",""));arena.effect_code=str(replay.get("code",""))
		for unit in replay.get("snapshot",{}).get("actors",[]):
			if str(unit["id"]).begins_with("enemy_"):arena.enemy_hp[unit["id"]]=int(unit["hp"])
		for member in arena.members:
			arena.frames[member["id"]]=2 if replay.get("target")==member["id"] and replay.get("code") in ["damage","fallen"] else 1 if replay.get("actor")==member["id"] else 0
	add_child(arena)
	if not replay.is_empty():
		_window(Rect2(8,194,496,84)).add_child(_label(str(replay.get("message","")),14))
		var skip := _button(self,"表示をスキップ  Enter",{"kind":"skip_presentation"});skip.position=Vector2(340,249)
		return
	if encounter==null:return
	var intent_window := _window(Rect2(292,6,212,34+maxi(0,encounter.enemy_intents().size()-1)*17))
	for intent in encounter.enemy_intents():
		var enemy := encounter.actor_by_id(intent["actor"])
		intent_window.add_child(_label("%s HP%d/%d  %s→%s" % [enemy.display_name,enemy.hp,enemy.max_hp,intent["action"],intent["target_name"]],11))
	var commands := _window(Rect2(8,189,188,92))
	var scroll := ScrollContainer.new();scroll.custom_minimum_size=Vector2(168,46);scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;commands.add_child(scroll)
	var grid := GridContainer.new();grid.columns=2;grid.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(grid)
	if not target_action.is_empty():
		var kind := BattleAction.Kind.ATTACK
		match target_action["kind"]:
			"ability":kind=BattleAction.Kind.ABILITY
			"potion":kind=BattleAction.Kind.ITEM
			"observe":kind=BattleAction.Kind.OBSERVE
		for target in encounter.targets_for(actor,kind,target_action.get("ability","")):
			var chosen := target_action.duplicate();chosen["target"]=target.id;_button(grid,target.display_name,chosen)
		_button(grid,"戻る",{"kind":"ui_cancel_target"})
	elif not actor.is_empty():
		_button(grid,"攻撃",{"kind":"ui_target","action":"attack"})
		_button(grid,"防御",{"kind":"guard","actor":actor})
		_button(grid,"回復薬",{"kind":"ui_target","action":"potion"},encounter.potions>0)
		_button(grid,"観察",{"kind":"ui_target","action":"observe"})
		for ability in encounter.actor_by_id(actor).equipped:
			if game.abilities[ability]["kind"]!="passive":_button(grid,game.abilities[ability]["name"],{"kind":"ui_target","action":"ability","ability":ability})
	var row := HBoxContainer.new();commands.add_child(row)
	_button(row,"ターン実行",{"kind":"resolve_round"},encounter.can_resolve())
	_button(row,"選び直す",{"kind":"clear_actions"})
	var status := _window(Rect2(202,189,302,92))
	for unit in encounter.actors:
		if unit.team!=Combatant.Team.PARTY:continue
		var button := _button(status,"%s  HP%d/%d  MP%d/%d%s" % [unit.display_name,unit.hp,unit.max_hp,unit.mp,unit.max_mp," ✓" if encounter.queued.has(unit.id) else ""],{"kind":"ui_actor","actor":unit.id},unit.is_alive())
		button.add_theme_font_size_override("font_size",11)
	var details := _button(self,"機構・予測",{"kind":"mechanics"});details.position=Vector2(8,7);details.size=Vector2(80,22)
