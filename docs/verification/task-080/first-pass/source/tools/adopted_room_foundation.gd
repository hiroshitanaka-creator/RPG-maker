extends "res://scripts/ui/game_root.gd"
## 開発専用。既存入力・歩行・描画を使い、通常進行や保存へ接続しない。
const DEFINITION := "res://world/adopted_room_foundation.json"
var rooms: Array = []
var selected := 0
var view: FirstRegionView
var caption: Label
var original_region: Dictionary
var original_visuals: Dictionary

func _ready() -> void:
	Engine.max_fps = 60
	OS.add_logger(_diagnostics)
	rooms = WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string(DEFINITION)))["rooms"]
	FirstRegion.data()
	FirstRegionPresentation.data()
	original_region = FirstRegion._data.duplicate(true)
	original_visuals = FirstRegionPresentation._data.duplicate(true)
	_install_rooms()
	game = GameSession.new()
	_rpg_audio = RpgAudio.new()
	add_child(_rpg_audio)
	var initial := 0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			initial = -1
			for i in range(rooms.size()):
				if rooms[i]["id"] == arg.trim_prefix("--room="):initial = i
	if initial < 0:
		printerr("ADOPTED_ROOM: unknown --room; inn|item_shop|weapon_shop|shrine|armor_shop")
		get_tree().quit(2)
		return
	select_room(initial)

func _install_rooms() -> void:
	for room in rooms:
		var threshold: Array = []
		for y in range(12):threshold.append("######.#######" if y in [10,11] else "##############")
		FirstRegion._data["sites"].append({"id":room["node"],"rooms":[
			{"title":room["label"],"layout":room["layout"],"events":[]},
			{"title":"入口確認領域","layout":threshold,"events":[]}]})
		FirstRegion.data()["encounters"][room["node"]] = {"chance":0.0,"enemies":[]}
		FirstRegion.data()["doors"].append({"from":point(room,0,room["exit"]),"to":point(room,1,room["exit"]),"facing":0})
		FirstRegion.data()["doors"].append({"from":point(room,1,room["return_trigger"]),"to":point(room,0,room["return_trigger"]),"facing":3})
		for index in [0,1]:
			FirstRegionPresentation._data["maps"]["%s:%d" % [room["node"],index]] = {
				"width":14,"height":12,"origin":[0,0],"layers":[],"tiles":{},
				"surround":"assets/tiles/bright_interior_wall.png",
				"backdrop":{"path":room["path"],"offset":[0,0]},
				"overlays":{"path":room["path"],"pieces":room["overlays"]}}

static func point(room: Dictionary, index: int, cell: Array) -> Dictionary:
	return {"layer":"interior","node":room["node"],"room":index,"cell":cell.duplicate()}

func select_room(index: int) -> void:
	if index < 0 or index >= rooms.size():return
	_world_mover.stop()
	selected = index
	game.new_first_region()
	FirstRegion.place(game._state["overworld"],point(rooms[index],0,rooms[index]["spawn"]))
	mode = Mode.WORLD
	_refresh()

func _input(event: InputEvent) -> void:
	if not event is InputEventKey:return
	if event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			get_tree().quit()
			return
		if event.keycode >= KEY_1 and event.keycode <= KEY_5:
			select_room(event.keycode-KEY_1)
			return
	if event.keycode in [KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_W,KEY_A,KEY_S,KEY_D]:super._input(event)

func submit_player_action(action: Dictionary) -> bool:
	# 開発起動では移動だけ。保存・販売・会話・進行操作は公開しない。
	if action.get("kind") != "world_move":return false
	return super.submit_player_action(action)

func _refresh() -> void:
	if game == null or game.export_state().is_empty():return
	if is_instance_valid(view):
		remove_child(view)
		view.queue_free()
	view = FirstRegionView.new()
	view.saved = game.export_state()
	view.walk_frame = _walk_frame
	add_child(view)
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if not is_instance_valid(caption):
		caption = Label.new()
		caption.add_theme_font_override("font",RpgFonts.get_font())
		caption.add_theme_font_size_override("font_size",10)
		caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(caption)
	move_child(caption,-1)
	caption.text = "開発用・歩行基盤 %d/5 %s%s\n1–5:室選択  矢印/WASD:歩行  Esc:終了" % [selected+1,rooms[selected]["label"]," / 入口確認" if game.overworld_state()["room"]==1 else ""]

func _process_region_display(delta: float) -> void:
	super._process_region_display(delta)
	if not is_instance_valid(view):return
	view.movement_offset = Vector2.ZERO
	if _world_mover.active() and _world_mover.route.size() == 2:
		view.movement_offset = Vector2(_world_mover.route[1]-_world_mover.route[0])*clampf(_world_mover.elapsed_seconds/0.15,0.0,1.0)
		view.walk_frame = 1 if _walk_frame%2==0 else 3
	view.queue_redraw()

func _exit_tree() -> void:
	# このsceneの一時登録を戻す。利用者の保存・記録には書き込まない。
	if not original_region.is_empty():FirstRegion._data = original_region
	if not original_visuals.is_empty():FirstRegionPresentation._data = original_visuals
	if is_instance_valid(_rpg_audio):_rpg_audio.shutdown()
	OS.remove_logger(_diagnostics)
