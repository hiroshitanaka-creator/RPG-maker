extends SceneTree
## 本番と同じ描画経路で96px原寸と72px縮小を撮り、補間色と間引きを測定する。
const OUTPUT := "res://docs/verification/battle-layout-target/scaling/"
const JOBS := ["warrior","martial_artist","priest","mage"]
const BACKDROP := Color("162835")
const DISPLAY_SCALE := 2
var records: Array = []
var failures: Array[String] = []

class ScaleBoard extends RpgBattleView:
	var actor: Dictionary
	var pose := 0
	func _draw() -> void:
		draw_rect(Rect2(0,0,224,112),Color("162835"))
		var visual := CharacterVisuals.appearance(actor,"battle",pose)
		draw_texture_rect_region(_texture(visual["path"]),Rect2(8,8,96,96),visual["region"])
		draw_texture_rect_region(_texture(visual["path"]),Rect2(128,32,72,72),visual["region"])

func _initialize() -> void:
	if DisplayServer.get_name()=="headless":printerr("SCALING_INVALID: 実描画が必要");quit(2);return
	call_deferred("run")

func nearest_indices(coordinate: float) -> Array[int]:
	var lower := floori(coordinate)
	# テクセル境界では左右が等距離。GPUの丸め方向によるどちらの最近傍も認める。
	if lower>0 and absf(coordinate-lower)<0.000001:return [lower-1,lower]
	return [lower]

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	# 実ゲームの標準1024×576と同じ2倍のcanvas_items描画を、固定サイズで測定する。
	var viewport := SubViewport.new()
	viewport.size=Vector2i(224,112)*DISPLAY_SCALE
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var game := GameSession.new();game.new_game(4)
	for job in JOBS:
		for saved in game.export_state()["party"]:
			if not game.choose_job(saved["id"],job):failures.append("転職: "+saved["id"]+"/"+job)
		for saved in game.export_state()["party"]:
			for pose in range(3):
				var board := ScaleBoard.new();board.actor=saved;board.pose=pose;board.size=Vector2(224,112)
				board.scale=Vector2(DISPLAY_SCALE,DISPLAY_SCALE)
				viewport.add_child(board)
				await process_frame;await process_frame
				await RenderingServer.frame_post_draw
				RenderingServer.force_draw(false);RenderingServer.force_sync()
				var image := viewport.get_texture().get_image()
				var visual := CharacterVisuals.appearance(saved,"battle",pose)
				if visual["path"]!="res://assets/characters/%s/jobs/%s/battle.png" % [saved["id"],job]:failures.append("衣装参照: "+job+"/"+saved["id"])
				var source := (load(visual["path"]) as Texture2D).get_image().get_region(visual["region"])
				var colors: Dictionary={BACKDROP.to_rgba32():true}
				var raw_errors := 0
				for y in range(96):
					for x in range(96):
						var pixel := source.get_pixel(x,y)
						if pixel.a==0:pixel=BACKDROP
						colors[pixel.to_rgba32()]=true
						for sy in range(DISPLAY_SCALE):
							for sx in range(DISPLAY_SCALE):
								if image.get_pixel((x+8)*DISPLAY_SCALE+sx,(y+8)*DISPLAY_SCALE+sy)!=pixel:raw_errors+=1
				var added_colors := 0
				var nearest_errors := 0
				for y in range(72*DISPLAY_SCALE):
					for x in range(72*DISPLAY_SCALE):
						var actual := image.get_pixel(x+128*DISPLAY_SCALE,y+32*DISPLAY_SCALE)
						if not colors.has(actual.to_rgba32()):added_colors+=1
						var matched := false
						for sx in nearest_indices((x+0.5)*96/(72.0*DISPLAY_SCALE)):
							for sy in nearest_indices((y+0.5)*96/(72.0*DISPLAY_SCALE)):
								var pixel := source.get_pixel(sx,sy)
								if pixel.a==0:pixel=BACKDROP
								if pixel==actual:matched=true
						if not matched:nearest_errors+=1
				var name := "%s-%s-%d" % [job,saved["id"],pose]
				if raw_errors!=0 or added_colors!=0 or nearest_errors!=0:failures.append(name)
				if image.save_png(OUTPUT+name+".png")!=OK:failures.append("画像保存: "+name)
				records.append({"job":job,"actor":saved["id"],"pose":pose,"source_size":96,"display_size":72,"raw_pixel_mismatches":raw_errors,"interpolated_color_pixels":added_colors,"nearest_sample_mismatches":nearest_errors})
				board.queue_free();await process_frame
	viewport.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"measurements.json",{"records":records,"failures":failures,"status":"PASS" if failures.is_empty() else "FAIL","window_scale":DISPLAY_SCALE,"source_columns":96,"display_columns":72,"physical_display_columns":144,"source_pixel_width_counts":{"1px":48,"2px":48},"source_pixel_height_counts":{"1px":48,"2px":48},"coverage_counts_basis":"倍率からの計算値。色の補間と最近傍の一致は実描画から測定。","filter":"nearest","build":BuildIdentity.current()})
	for error in failures:printerr("SCALING_FAIL: "+error)
	print("SCALING_PASS: frames=48 interpolation=0 nearest_mismatch=0" if failures.is_empty() else "SCALING_FAIL: cases=%d" % failures.size())
	quit(0 if failures.is_empty() else 1)
