class_name FirstRegionScreen
extends Control
## 最初の地方の表示だけを担当する。状態の変更は通常の操作として親へ通知する。
signal action_requested(action: Dictionary)
var game: GameSession
var screen_mode := "world"
var actor := ""
var target_action: Dictionary = {}
var message := ""
var dialogue_prompt := "▼"
var speaker := ""
var speaking_actor := ""
var notice := ""
var place_name := ""
var walk_frame := 0
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
	label.add_theme_color_override("font_color",Color.WHITE if screen_mode=="battle" else Color("f5f3e8"))
	label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	return label

func _window(rect: Rect2, inset: int = 8) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.position=rect.position
	panel.size=rect.size
	var box := StyleBoxTexture.new()
	box.texture=load("res://assets/ui/window_bright.png")
	for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:
		box.set_texture_margin(side,8.0)
		box.set_content_margin(side,inset)
	box.modulate_color=Color(1,1,1,0.86 if screen_mode=="battle" else 0.93)
	if screen_mode=="battle":
		var blue := StyleBoxFlat.new()
		blue.bg_color=Color("101c50");blue.border_color=Color.WHITE
		blue.set_border_width_all(1);blue.set_corner_radius_all(3)
		for side in [SIDE_LEFT,SIDE_TOP,SIDE_RIGHT,SIDE_BOTTOM]:blue.set_content_margin(side,inset)
		panel.add_theme_stylebox_override("panel",blue)
	else:panel.add_theme_stylebox_override("panel",box)
	add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",3)
	panel.add_child(column)
	return column

func _button(parent: Node, title: String, action: Dictionary, enabled: bool = true) -> Button:
	var button := Button.new()
	button.text=title
	button.disabled=not enabled
	if screen_mode=="battle":
		button.alignment=HORIZONTAL_ALIGNMENT_LEFT
		for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_disabled_color"]:button.add_theme_color_override(state,Color.WHITE)
	button.add_theme_font_size_override("font_size",11 if screen_mode=="battle" else 12)
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
	var next := _button(self,dialogue_prompt,{"kind":"confirm"})
	next.position=Vector2(474,251) if dialogue_prompt=="▼" else Vector2(270,251)
	next.size=Vector2(24,20) if dialogue_prompt=="▼" else Vector2(228,20)

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
			else:arena.party_hp[unit.id]=unit.hp
	if not replay.is_empty():
		arena.effect_target=str(replay.get("target",""));arena.effect_code=str(replay.get("code",""))
		arena.acting_actor=str(replay.get("actor",""));arena.effect_amount=int(replay.get("amount",0))
		if replay.get("code")=="fallen":arena.acting_actor=""
		arena.selected_actor=""
		for unit in replay.get("snapshot",{}).get("actors",[]):
			if str(unit["id"]).begins_with("enemy_"):arena.enemy_hp[unit["id"]]=int(unit["hp"])
			else:arena.party_hp[unit["id"]]=int(unit["hp"])
		for member in arena.members:
			arena.frames[member["id"]]=2 if replay.get("target")==member["id"] and replay.get("code") in ["damage","fallen"] else 1 if replay.get("actor")==member["id"] else 0
	add_child(arena)
	var status := _window(Rect2(268,223,240,65),4)
	status.name="BattlePartyStatus"
	status.add_theme_constant_override("separation",0)
	var visible_members: Array=arena.members.duplicate(true)
	var observed: Array=replay.get("snapshot",{}).get("actors",[]) if not replay.is_empty() else encounter.snapshot()["actors"] if encounter!=null else []
	for member in visible_members:
		for unit in observed:
			if unit["id"]==member["id"]:member.merge(unit,true)
		var row := HBoxContainer.new();row.add_theme_constant_override("separation",3);status.add_child(row)
		var member_id: String=member["id"]
		var queued := encounter!=null and encounter.queued.has(member_id)
		var button := _button(row,str(member["name"])+( " 済" if queued else ""),{"kind":"ui_actor","actor":member_id},int(member["hp"])>0 and replay.is_empty())
		button.name="Status_"+member_id;button.custom_minimum_size.x=48;button.add_theme_font_size_override("font_size",10)
		if member_id==(arena.acting_actor if not replay.is_empty() else actor):
			for state in ["font_color","font_hover_color","font_pressed_color","font_focus_color","font_disabled_color"]:button.add_theme_color_override(state,Color("ffe36b"))
		var hp := _label("HP%d/%d" % [member["hp"],member["max_hp"]],10);hp.custom_minimum_size.x=58;row.add_child(hp)
		_battle_bar(row,member_id,"HP",int(member["hp"]),int(member["max_hp"]),Color("73b54a"))
		var mp := _label("MP%d/%d" % [member["mp"],member["max_mp"]],10);mp.custom_minimum_size.x=50;row.add_child(mp)
		_battle_bar(row,member_id,"MP",int(member["mp"]),int(member["max_mp"]),Color("5d98c4"))
	_first_button=null
	var intent_window := _window(Rect2(156,223,108,65),4)
	intent_window.name="BattleEnemyList"
	var enemy_scroll := ScrollContainer.new();enemy_scroll.custom_minimum_size=Vector2(100,57);intent_window.add_child(enemy_scroll)
	var enemy_lines := VBoxContainer.new();enemy_lines.size_flags_horizontal=Control.SIZE_EXPAND_FILL;enemy_scroll.add_child(enemy_lines)
	var intents: Array=encounter.enemy_intents() if encounter!=null else []
	var groups: Dictionary={}
	var details: Dictionary={}
	for i in range(arena.enemy_ids.size()):
		var enemy_id := "enemy_%02d" % (i+1)
		var definition: Dictionary=arena.definitions[arena.enemy_ids[i]]
		var enemy_state := {"name":definition["name"],"hp":arena.enemy_hp.get(enemy_id,definition["stats"]["hp"]),"max_hp":definition["stats"]["hp"]}
		for unit in observed:
			if unit["id"]==enemy_id:enemy_state=unit
		var key := str(arena.enemy_ids[i])+":"+str(enemy_state["name"])
		if not groups.has(key):groups[key]={"name":enemy_state["name"],"count":0}
		if int(enemy_state["hp"])>0:groups[key]["count"]+=1
		var line := "%s HP%d/%d" % [enemy_state["name"],enemy_state["hp"],enemy_state["max_hp"]]
		for intent in intents:
			if intent["actor"]==enemy_id:line+="\n%s→%s" % [intent["action"],intent["target_name"]]
		details[enemy_id]=line
	for group in groups.values():
		var summary := _label(str(group["name"])+( " %d" % group["count"] if group["count"]!=1 else ""),10)
		summary.name="EnemyGroup";enemy_lines.add_child(summary)
	if not replay.is_empty():
		if replay.get("code")=="ability":
			var banner := _window(Rect2(156,4,200,24),3);banner.name="BattleSkillName"
			var title := _label(str(replay.get("ability_name","")),12);title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;banner.add_child(title)
		# コマンド窓は作らず、従来のスキップ操作だけを空いた下端に残す。
		var skip := _button(self,"表示をスキップ  Enter",{"kind":"skip_presentation"});skip.add_theme_font_size_override("font_size",10)
		skip.position=Vector2(4,264);skip.size=Vector2(148,20)
		for state in ["normal","hover","pressed","focus"]:
			var skip_box := StyleBoxFlat.new();skip_box.bg_color=Color("101c50");skip_box.border_color=Color.WHITE
			skip_box.set_border_width_all(1);skip_box.set_corner_radius_all(3)
			skip.add_theme_stylebox_override(state,skip_box)
		skip.tooltip_text=str(replay.get("message",""))
		return
	if encounter==null:return
	var commands := _window(Rect2(4,223,148,65),4);commands.name="BattleCommands"
	commands.add_theme_constant_override("separation",0)
	# 対象名の長さやスクロールバーで下の操作欄を押し広げない固定領域。
	var content := Control.new();content.custom_minimum_size=Vector2(140,57);commands.add_child(content)
	var scroll := ScrollContainer.new();scroll.name="BattleActionScroll";scroll.position=Vector2.ZERO;scroll.size=Vector2(140,28)
	scroll.follow_focus=true
	if not target_action.is_empty():scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(scroll)
	var grid := GridContainer.new();grid.columns=2;grid.add_theme_constant_override("v_separation",0);grid.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(grid)
	if not target_action.is_empty():
		scroll.size.y=57
		grid.columns=1
		var detail := _label("",10);detail.name="BattleTargetDetails"
		# 詳細は対象選択中だけ。敵一覧の代わりに同じ下端の窓内へ表示する。
		enemy_lines.add_child(detail)
		var focus := func(identifier: String)->void:
			arena.focus_target(identifier)
			detail.text=str(details.get(identifier,""))
			for child in enemy_lines.get_children():child.visible=(child==detail) if details.has(identifier) else (child!=detail)
		var kind := BattleAction.Kind.ATTACK
		match target_action["kind"]:
			"ability":kind=BattleAction.Kind.ABILITY
			"potion":kind=BattleAction.Kind.ITEM
			"observe":kind=BattleAction.Kind.OBSERVE
		var targets := encounter.targets_for(actor,kind,target_action.get("ability",""))
		for target in targets:
			var chosen := target_action.duplicate();chosen["target"]=target.id
			var target_button := _button(grid,target.display_name,chosen)
			target_button.focus_entered.connect(focus.bind(target.id))
			target_button.mouse_entered.connect(focus.bind(target.id))
		if not targets.is_empty():focus.call(targets[0].id)
		_button(grid,"戻る",{"kind":"ui_cancel_target"})
		return
	elif not actor.is_empty():
		_button(grid,"攻撃",{"kind":"ui_target","action":"attack"})
		_button(grid,"防御",{"kind":"guard","actor":actor})
		_button(grid,"回復薬",{"kind":"ui_target","action":"potion"},encounter.potions>0)
		_button(grid,"観察",{"kind":"ui_target","action":"observe"})
		for ability in encounter.actor_by_id(actor).equipped:
			if game.abilities[ability]["kind"]!="passive":_button(grid,game.abilities[ability]["name"],{"kind":"ui_target","action":"ability","ability":ability})
	var row := GridContainer.new();row.name="BattleRoundActions";row.columns=2;row.add_theme_constant_override("v_separation",0)
	row.position=Vector2(0,29);row.size=Vector2(140,28);content.add_child(row)
	_button(row,"ターン実行",{"kind":"resolve_round"},encounter.can_resolve())
	_button(row,"選び直す",{"kind":"clear_actions"})
	_button(row,"技の効果を確認",{"kind":"mechanics"})
	for button in row.get_children():button.add_theme_font_size_override("font_size",10)

func _battle_bar(parent: Control, member_id: String, kind: String, value: int, maximum: int, color: Color) -> void:
	var bar := ProgressBar.new()
	bar.name=kind+"_"+member_id
	bar.custom_minimum_size=Vector2(20,7)
	bar.size_flags_vertical=Control.SIZE_SHRINK_CENTER
	bar.max_value=maxi(1,maximum);bar.value=value;bar.show_percentage=false
	bar.mouse_filter=Control.MOUSE_FILTER_IGNORE
	bar.tooltip_text="%s %d/%d" % [kind,value,maximum]
	var track := StyleBoxFlat.new();track.bg_color=Color("18212b");track.border_color=Color("b5aa95");track.set_border_width_all(1)
	var fill := StyleBoxFlat.new();fill.bg_color=color
	bar.add_theme_stylebox_override("background",track);bar.add_theme_stylebox_override("fill",fill)
	parent.add_child(bar)
