extends SceneTree
## 本番の敵サイズと描画方式を使い、原寸と75%表示を実描画で比較する。
const OUTPUT := "res://docs/verification/battle-compact/enemy-scaling/"
const BACKDROP := Color("162835")
const ENEMIES := ["slime","bat","shell_guard","mending_beast","river_beast","gate_beast"]
var records: Array=[]
var failures: Array[String]=[]

class Board extends RpgBattleView:
	func _draw() -> void:
		draw_rect(Rect2(0,0,420,192),Color("162835"))
		var source := enemy_region(enemy_ids[0])
		draw_texture_rect_region(_enemy_texture(enemy_ids[0]),Rect2(Vector2(8,8),source.size),source)
		draw_texture_rect_region(_enemy_texture(enemy_ids[0]),Rect2(Vector2(220,8),actor_rect("enemy_01").size),source)

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("ENEMY_SCALING_INVALID: 実描画が必要");quit(2);return
	call_deferred("run")

func nearest_indices(value: float) -> Array[int]:
	var lower := floori(value)
	return [lower-1,lower] if lower>0 and absf(value-lower)<0.000001 else [lower]

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	var viewport := SubViewport.new();viewport.size=Vector2i(840,384)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	var game := GameSession.new();game.new_game(4)
	for identifier in ENEMIES:
		var board := Board.new();board.enemy_ids=[identifier];board.definitions=game.enemy_definitions
		board.scale=Vector2(2,2);viewport.add_child(board)
		await process_frame;await process_frame;await RenderingServer.frame_post_draw
		RenderingServer.force_draw(false);RenderingServer.force_sync()
		var frame := viewport.get_texture().get_image()
		var source := board._enemy_texture(identifier).get_image().get_region(board.enemy_region(identifier))
		var dimensions := board.actor_rect("enemy_01").size
		var colors: Dictionary={BACKDROP.to_rgba32():true}
		var raw_errors := 0
		for y in range(source.get_height()):
			for x in range(source.get_width()):
				var pixel := source.get_pixel(x,y)
				if pixel.a==0:pixel=BACKDROP
				colors[pixel.to_rgba32()]=true
				for sy in range(2):
					for sx in range(2):
						if frame.get_pixel((x+8)*2+sx,(y+8)*2+sy)!=pixel:raw_errors+=1
		var added_colors := 0
		var nearest_errors := 0
		for y in range(floori(dimensions.y*2)):
			for x in range(floori(dimensions.x*2)):
				var actual := frame.get_pixel(440+x,16+y)
				if not colors.has(actual.to_rgba32()):added_colors+=1
				var matched := false
				for sx in nearest_indices((x+0.5)/1.5):
					for sy in nearest_indices((y+0.5)/1.5):
						var pixel := source.get_pixel(sx,sy)
						if pixel.a==0:pixel=BACKDROP
						if pixel==actual:matched=true
				if not matched:nearest_errors+=1
		if raw_errors or added_colors or nearest_errors or dimensions!=Vector2(source.get_size())*0.75:failures.append(identifier)
		if frame.save_png(OUTPUT+identifier+".png")!=OK:failures.append("画像保存: "+identifier)
		records.append({"id":identifier,"source_size":[source.get_width(),source.get_height()],"display_size":[dimensions.x,dimensions.y],"raw_mismatches":raw_errors,"interpolated_color_pixels":added_colors,"nearest_mismatches":nearest_errors})
		board.queue_free();await process_frame
	viewport.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"measurements.json",{"status":"PASS" if failures.is_empty() else "FAIL","failures":failures,"records":records,"filter":"nearest","display_scale":0.75,"window_scale":2,"note":"色のにじみと画素選択を実測。非整数倍のため線幅の不均一は残る。","build":BuildIdentity.current()})
	print("ENEMY_SCALING_PASS: cases=6 interpolation=0 nearest_mismatch=0" if failures.is_empty() else "ENEMY_SCALING_FAIL: "+str(failures))
	quit(0 if failures.is_empty() else 1)
