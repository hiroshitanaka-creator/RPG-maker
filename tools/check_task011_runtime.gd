extends SceneTree
## 011は直接読み込む確認用状態。本番セーブは使わず、指定した検査用ファイルだけで保存を往復する。
const DIRS := [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]
var failures: Array[String] = []
var checks := 0
var base: Dictionary
var stage := false
var cells := 0
var moves := 0
var stair_trips := 0
var saves := 0
var relocations := 0
var encounter_returns := 0
var walk_enemies: Dictionary = {}

func valid_walk_event(event: Dictionary) -> bool:
	if event.get("kind") == "moved":return true
	if event.get("kind") != "battle" or not event.get("id") is String or str(event["id"]).is_empty():return false
	if not event.get("enemies") is Array or event["enemies"].is_empty() or not event.get("seed") is int:return false
	for enemy in event["enemies"]:
		if not enemy is String or not walk_enemies.has(enemy):return false
	return true

func check_stair(before: Dictionary, after: Dictionary, link: Dictionary) -> void:
	check(after["overworld"]["layer"]==before["overworld"]["layer"] and after["overworld"]["node"]==before["overworld"]["node"] and after["overworld"]["room"]==link["to_room"] and after["overworld"]["cell"]==link["to_cell"] and after["overworld"]["facing"]==link["facing"],"階段の着地と向き")
	var unchanged := before.duplicate(true)
	for key in ["room","cell","facing","entry_lock"]:unchanged["overworld"][key]=after["overworld"][key]
	check(unchanged==after,"階段直前直後は位置以外の進行・所持品・地図状態を変えない")

func resume_confirmation_encounter(game: GameSession) -> GameSession:
	# 戦闘の攻略・報酬は対象外。通知後の全保存値を新インスタンスへ保持し、確認用探索を続ける。
	# 撮影は本番UIが実際に戦闘を開始した後だけ、runtimeはstart APIの受理後だけここへ来る。
	check(game.current_battle()!=null,"確認用遭遇は本番戦闘APIで開始済み")
	var saved := game.export_state()
	var resumed := GameSession.new()
	check(resumed.import_state(saved) and resumed.export_state()==saved and resumed.current_battle()==null,"確認用戦闘から通知後の全状態を維持して探索へ戻る")
	encounter_returns += 1
	return resumed

func check(ok: bool, why: String) -> bool:
	checks += 1
	if not ok:failures.append(why)
	return ok

func placed(index: int, cell: Array) -> Dictionary:
	var saved := base.duplicate(true)
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"region2_ruins","room":index,"cell":cell})
	return saved

func route(saved: Dictionary, goal: Vector2i) -> Array[Vector2i]:
	var from := WorldExpedition.point(saved["overworld"]["cell"])
	var seen := {from:from};var queue: Array[Vector2i] = [from];var cursor := 0
	var triggers: Array = []
	for link in Region2Ruins.data()["stairs"]:
		if link["from_room"] == saved["overworld"]["room"]:triggers.append(WorldExpedition.point(link["from_cell"]))
	while cursor < queue.size() and not seen.has(goal):
		var here := queue[cursor];cursor += 1
		for dir in DIRS:
			var next: Vector2i = here+dir
			if seen.has(next) or (next in triggers and next != goal) or not FirstRegion.walkable(saved,next):continue
			seen[next] = here;queue.append(next)
	var path: Array[Vector2i] = []
	if not seen.has(goal):return path
	var cell := goal
	while cell != from:path.push_front(cell);cell=seen[cell]
	return path

func _initialize() -> void:
	stage = "--stage" in OS.get_cmdline_user_args()
	var game := GameSession.new()
	check(game.new_first_region(),"本番新ゲームから確認用状態を作る")
	base = game.export_state()
	walk_enemies=game.enemy_definitions
	var document := Region2Ruins.data()
	check(document["site"]["rooms"].size() == 4,"4階の定義")
	for index in range(4):
		var saved := placed(index,Region2Ruins.landing(index))
		check(FirstRegion.valid(saved),"階段前の確認用状態受理")
		var map := FirstRegionPresentation.map_for(saved["overworld"])
		var layout: Array = FirstRegion.room(saved["overworld"])["layout"]
		check(layout == map["layout"],"描画用・部屋用の全マス定義一致")
		var reach := 0
		for y in range(-1,map["height"]+1):
			for x in range(-1,map["width"]+1):
				var expected: bool = y>=0 and y<layout.size() and x>=0 and x<map["width"] and str(layout[y]).substr(x,1)=="."
				cells += 1
				check(FirstRegion.walkable(saved,Vector2i(x,y)) == expected,"全マス・外周通行一致 %d/%d/%d" % [index,x,y])
				if not expected:continue
				if [x,y] != saved["overworld"]["cell"]:check(not route(saved,Vector2i(x,y)).is_empty(),"階段前から床に到達 %d/%d/%d" % [index,x,y])
				reach += 1
				for dir in DIRS:
					var probe := placed(index,[x,y]);var before := probe.duplicate(true)
					var next: Vector2i = Vector2i(x,y)+dir
					var passable: bool=next.y>=0 and next.y<layout.size() and next.x>=0 and next.x<map["width"] and str(layout[next.y]).substr(next.x,1)=="."
					var event := FirstRegion.move(probe,next);moves += 1
					check(valid_walk_event(event) if passable else event.is_empty() and probe==before,"本番の全隣接移動と拒否")
					if stage and passable:check(event.get("kind")=="moved","完成時に遭遇・物語を発火しない")
		check(reach>0,"歩ける床がある")
		if stage:check(FirstRegion.room(saved["overworld"])["events"].is_empty(),"完成時イベント・宝箱未設置")
		save_roundtrip(index,saved)
	# 10往復、計60遷移。固定座標・向き・状態維持・通常APIを使う。
	var travel := GameSession.new();check(travel.import_state(placed(0,Region2Ruins.landing(0))),"階段検査起点")
	for repeat in range(10):
		for link_index in [0,2,4,5,3,1]:
			var link: Dictionary = document["stairs"][link_index]
			var before := travel.export_state()
			check(before["overworld"]["room"]==link["from_room"],"階段の出発階")
			var path := route(before,WorldExpedition.point(link["from_cell"]))
			if not check(not path.is_empty(),"階段への経路"):continue
			for step in path:
				travel.first_region_face(step-WorldExpedition.point(travel.export_state()["overworld"]["cell"]))
				var step_before := travel.export_state()
				var event := travel.move_first_region(step)
				var step_after := travel.export_state()
				if step == path[-1]:
					check(event.get("kind")=="moved","階段接触の通常移動通知")
					check_stair(step_before,step_after,link)
				else:
					check(valid_walk_event(event),"道中の有効な通常移動・戦闘通知")
					check(step_after["overworld"]["layer"]==step_before["overworld"]["layer"] and step_after["overworld"]["node"]==step_before["overworld"]["node"] and step_after["overworld"]["room"]==link["from_room"] and step_after["overworld"]["cell"]==[step.x,step.y],"道中では指定位置へ歩き誤接続しない")
					if event.get("kind")=="battle" and valid_walk_event(event):
						check(travel.start_first_region_battle(event)!=null,"道中の本番戦闘通知を受理")
						travel=resume_confirmation_encounter(travel)
				if stage:check(event.get("kind")=="moved","完成時に階段までの全経路で無遭遇")
			var after := travel.export_state()
			if stage:
				var unchanged := before.duplicate(true);unchanged["overworld"]=after["overworld"].duplicate(true)
				check(unchanged==after,"完成時の全経路の位置以外の状態保持")
			check(travel.move_first_region(WorldExpedition.point(after["overworld"]["cell"])).is_empty() and travel.export_state()==after,"静止時に再遷移しない")
			stair_trips += 1
	if stage:
		check(not document["world_connection"]["enabled"] and not document["encounters_enabled"] and not document["boss_enabled"],"完成時の入口・遭遇・ボス無効")
		var entry := placed(0,Region2Ruins.landing(0))
		for cell in document["world_connection"]["cells"]:check(not FirstRegion.walkable(entry,WorldExpedition.point(cell)),"完成時の入口マス不通")
		check(not FirstRegion.data().has("region2_ruins_entrance"),"完成時の世界接続なし")
	var output := "res://docs/verification/task-011/latest/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
	var report := {"status":"PASS" if failures.is_empty() else "FAIL","execution_sha":OS.get_environment("TASK011_EXECUTION_SHA"),"confirmation_state":true,"stage":stage,"checks":checks,"cells":cells,"neighbor_moves":moves,"stair_trips":stair_trips,"saves":saves,"relocations":relocations,"encounter_returns":encounter_returns,"failures":failures}
	var file := FileAccess.open(output+"runtime.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	for failure in failures:print("TASK011_FAIL: "+failure)
	print("TASK011_RUNTIME_%s: cells=%d moves=%d stairs=%d saves=%d relocation=%d" % [report["status"],cells,moves,stair_trips,saves,relocations])
	quit(0 if failures.is_empty() else 1)

func save_roundtrip(index: int, saved: Dictionary) -> void:
	var prefix := OS.get_environment("RPG_QA_SAVE_PREFIX")
	if not check(prefix.begins_with("task011-"),"通常保存と分離した専用接頭辞"):return
	var path := "user://"+prefix+"-floor%d.json" % index
	var game := GameSession.new();check(game.import_state(saved),"保存用確認状態")
	for face in range(4):
		game.first_region_face(DIRS[face]);var expected := game.export_state()
		check(game.save_game(path),"本番保存")
		var resumed := GameSession.new();check(resumed.load_game(path) and not resumed.position_relocated and resumed.export_state()==expected,"別インスタンスの保存再開・全状態一致")
		saves += 1
	# 壁・範囲外・その階の障害物の古い保存は既存補正へ通す。
	var obstacle_cells := [[33,11],[35,21],[20,12],[27,14]] # 崩落穴・階段内開口・水面・柱の足元
	for old_cell in [[0,0],[-1,-1],[100,100],obstacle_cells[index]]:
		check(not FirstRegion.walkable(saved,WorldExpedition.point(old_cell)),"古い保存の負例は実際に不通")
		var decoded := SavedDocument.decode(JSON.parse_string(FileAccess.get_file_as_string(path)))
		decoded["overworld"]["cell"] = old_cell
		var file := FileAccess.open(path,FileAccess.WRITE);file.store_string(SavedDocument.encode(decoded));file.close()
		var resumed := GameSession.new();check(resumed.load_game(path) and resumed.position_relocated,"古い不通位置の本番補正")
		var expected := game.export_state();expected["overworld"]["cell"] = Region2Ruins.landing(index);expected["overworld"]["entry_lock"] = ""
		check(resumed.export_state()==expected,"階段前に補正し他の保存値を維持")
		check(game.save_game(path),"次の負例前に専用保存だけを戻す")
		relocations += 1
