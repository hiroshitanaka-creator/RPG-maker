extends SceneTree
## 本番画像・単独描画・前景のアルファを照合し、頭と顔の遮蔽を画素単位で検出する。
const OUTPUT := "res://docs/verification/battle-layout-exact/"
const HEAD_ROWS := {"warrior":56,"martial_artist":48,"priest":56,"mage":60}
const HEAD_AREAS := {
	"warrior":[[Rect2i(0,0,96,48)],[Rect2i(0,0,96,48),Rect2i(36,48,32,4)],[Rect2i(0,0,96,48),Rect2i(32,48,28,6)]],
	"martial_artist":[[Rect2i(0,0,96,48)],[Rect2i(0,0,96,48)],[Rect2i(0,0,96,48)]],
	"priest":[[Rect2i(0,0,96,48)],[Rect2i(0,0,96,52)],[Rect2i(0,0,96,52)]],
	"mage":[[Rect2i(0,0,96,52)],[Rect2i(0,0,96,52),Rect2i(40,52,30,8)],[Rect2i(0,0,96,54)]]
}
const JOBS := ["warrior","martial_artist","priest","mage"]
var records: Array=[]
var failures: Array[String]=[]
var viewport: SubViewport
var checked_pixels := 0
var negative_control_pixels := 0

class IsolatedActor extends Control:
	var texture: Texture2D
	var destination: Rect2
	var region: Rect2
	var tint := Color.WHITE
	func _draw() -> void:
		draw_texture_rect_region(texture,destination,region,tint)

class PixelProbe extends Node2D:
	func _draw() -> void:
		draw_rect(Rect2(0,0,0.5,0.5),Color.MAGENTA)

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("HEAD_PIXELS_INVALID: 実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.size=Vector2i(1024,576)
	call_deferred("run")

func rendered() -> Image:
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	return root.get_texture().get_image()

func inspect_case(job: String, count: int, pose: int, code: String = "", actor_index: int = -1, target_index: int = -1, shake: int = 0, cursor_index: int = -1) -> void:
	var game := GameSession.new();game.new_game(count)
	for i in range(count):game.choose_job("pc_%02d" % (i+1),JOBS[i] if job=="mixed" else job)
	var battle := game.start_battle(["slime","shell_guard"],20260927)
	var panel := FirstRegionScreen.new();panel.game=game;panel.screen_mode="battle";panel.actor="pc_01"
	panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font();panel.battle_background="ruins"
	if not code.is_empty():
		var state := battle.snapshot()
		if code=="fallen":
			for unit in state["actors"]:
				if unit["id"]=="pc_%02d" % (target_index+1):unit["hp"]=0
		var event_actor := "pc_%02d" % (actor_index+1)
		if code=="damage":event_actor="enemy_01"
		if code=="fallen":event_actor="pc_%02d" % (target_index+1)
		panel.replay={"code":code,"actor":event_actor,"target":"pc_%02d" % (target_index+1),"amount":123,"ability_name":"火球","snapshot":state}
		panel.replay_members=game.export_state()["party"];panel.replay_enemies=game.current_enemy_ids()
	root.add_child(panel)
	var arena: RpgBattleView
	for child in panel.get_children():
		if child is RpgBattleView:arena=child
	arena.set_process(false);arena.set("_time",asin(shake/3.0)/70.0)
	if code.is_empty():
		for member in arena.members:arena.frames[member["id"]]=pose
	if cursor_index>=0:arena.focus_target("pc_%02d" % (cursor_index+1))
	arena.queue_redraw()
	var full := await rendered()
	var images: Array[Image]=[]
	var references: Array[Image]=[]
	var head_rects: Array[Rect2i]=[]
	var areas: Array=[]
	var boxes: Array[Rect2]=[]
	for node in panel.get_children():
		if node is PanelContainer:boxes.append(node.get_global_rect())
	for i in range(count):
		var member: Dictionary=arena.members[i]
		var id: String=member["id"]
		var fallen: bool=arena.party_hp.get(id,1)<=0
		var appearance := CharacterVisuals.appearance(member,"battle",2 if fallen else int(arena.frames.get(id,0)))
		var sprite := IsolatedActor.new()
		sprite.texture=load(appearance["path"]);sprite.region=appearance["region"]
		sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;sprite.scale=Vector2(2,2)
		sprite.destination=arena.actor_rect(id);sprite.destination.position+=arena._impact(id)
		if fallen:sprite.tint=Color(0.6,0.6,0.6,1)
		viewport.add_child(sprite);await rendered()
		images.append(viewport.get_texture().get_image())
		# 色は本番と同じウィンドウで測る。透過用SubViewportとの色変換差を混ぜない。
		panel.hide();sprite.reparent(root);sprite.scale=Vector2.ONE
		references.append(await rendered())
		panel.show()
		var rows: int=HEAD_ROWS[member["job_id"]]
		head_rects.append(Rect2i(Vector2i(sprite.destination.position*2),Vector2i(144,rows*3/2)))
		areas.append(HEAD_AREAS[member["job_id"]][2 if fallen else int(arena.frames.get(id,0))])
		sprite.queue_free();await process_frame
	var mismatches := 0
	var covered := 0
	var window_pixels := 0
	var pixels := 0
	var probe := Vector2i(-1,-1)
	for i in range(count):
		var area := head_rects[i]
		for y in range(area.position.y,area.end.y):
			for x in range(area.position.x,area.end.x):
				var source_point := Vector2i((Vector2(x,y)-Vector2(area.position)+Vector2(0.5,0.5))/1.5)
				var protected := false
				for head_area: Rect2i in areas[i]:
					if head_area.has_point(source_point):protected=true
				if not protected:continue
				var own := images[i].get_pixel(x,y)
				if own.a==0:continue
				pixels+=1;probe=Vector2i(x,y)
				if references[i].get_pixel(x,y)!=full.get_pixel(x,y):mismatches+=1
				for j in range(i+1,count):
					if images[j].get_pixel(x,y).a>0:
						covered+=1
				for box in boxes:
					if box.has_point(Vector2(x+0.5,y+0.5)/2):window_pixels+=1
	var label := "%s-%d-pose%d-%s-a%d-t%d-shake%d-cursor%d" % [job,count,pose,code,actor_index,target_index,shake,cursor_index]
	if pixels==0 or mismatches or covered or window_pixels:failures.append(label)
	checked_pixels+=pixels
	records.append({"case":label,"protected_pixels":pixels,"render_mismatches":mismatches,"foreground_pixels":covered,"window_pixels":window_pixels})
	if records.size()==1:
		# 1物理画素の侵入をわざと置き、比較が必ず検出することも確かめる。
		var intruder := PixelProbe.new()
		intruder.position=Vector2(probe)/2;panel.add_child(intruder)
		var changed := await rendered()
		if changed.get_pixelv(probe)!=full.get_pixelv(probe):negative_control_pixels=1
		else:failures.append("1画素の遮蔽を検出できない")
		intruder.queue_free()
	panel.queue_free();await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1024,576);viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	for job in ["mixed"]+JOBS:
		for pose in range(3):await inspect_case(job,4,pose)
		for actor_index in range(4):await inspect_case(job,4,1,"ability",actor_index,actor_index)
	for target_index in range(4):
		for code in ["damage","heal","revive","fallen"]:
			for shake in [-3,0,3] if code in ["damage","fallen"] else [0]:
				await inspect_case("mixed",4,0,code,(target_index+1)%4,target_index,shake)
	await inspect_case("mixed",3,0)
	for cursor_index in range(4):await inspect_case("mixed",4,0,"",-1,-1,0,cursor_index)
	viewport.queue_free();await process_frame
	var definitions: Dictionary={}
	for job in HEAD_AREAS:
		var poses: Array=[]
		for pose_areas in HEAD_AREAS[job]:
			var rectangles: Array=[]
			for area: Rect2i in pose_areas:rectangles.append([area.position.x,area.position.y,area.size.x,area.size.y])
			poses.append(rectangles)
		definitions[job]=poses
	PlaySessionMetrics.write_json(OUTPUT+"head-pixels.json",{"status":"PASS" if failures.is_empty() else "FAIL","head_regions":definitions,"source_frame_size":[96,96],"display_size":[72,72],"window_scale":2,"cases":records.size(),"protected_pixel_samples":checked_pixels,"negative_control_detected_pixels":negative_control_pixels,"records":records,"failures":failures,"build":BuildIdentity.current()})
	for failure in failures:printerr("HEAD_PIXELS_FAIL: "+failure)
	print("HEAD_PIXELS_PASS: cases=%d pixels=%d occlusion=0 negative_control=%d" % [records.size(),checked_pixels,negative_control_pixels] if failures.is_empty() else "HEAD_PIXELS_FAIL: cases=%d" % failures.size())
	quit(0 if failures.is_empty() else 1)
