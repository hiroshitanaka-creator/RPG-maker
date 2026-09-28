extends "res://tools/capture_first_region.gd"
## 既存の通常入力経路を変更せず、家・関所・水際の撮影先だけを今回の記録へ分ける。
const OUTPUT := "res://docs/verification/sprint5-home-shoreline/runtime/"
var global_samples: Array=[]

func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	await super._run()

func _capture(name: String) -> void:
	await create_timer(3.0 if name=="01-village-start" else 0.3).timeout
	await process_frame;await process_frame;await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var destination := OUTPUT+name+".png"
	var im := _main.get_viewport().get_texture().get_image()
	if im.is_empty() or im.save_png(destination)!=OK:_capture_errors.append(destination)
	_capture_busy=false;capture_done.emit()

func _finish() -> void:
	if _capture_busy:await capture_done
	if not _route_finished:await super._finish();return
	var hash := HashingContext.new();hash.start(HashingContext.HASH_SHA256)
	hash.update(WorldShoreline.texture().get_image().get_data())
	if hash.finish().hex_encode()!=WorldShoreline.data()["render_rgba_sha256"]:_capture_errors.append("色と透明範囲の合成が生成側の全画素と一致しない")
	# 未解放の地方は描画だけを検査し、到達済みのプレイ記録とは区別する。
	for center in [Vector2i(64,64),Vector2i(192,64),Vector2i(64,192),Vector2i(192,192)]:
		var chosen := Vector2i(-1,-1);var distance := INF
		for y in range(center.y-64,mini(256,center.y+64)):
			for x in range(center.x-64,mini(256,center.x+64)):
				var mask: int=WorldShoreline.data()["mask_rows"][y][x]
				if mask==0 or mask==511 or not (mask&16) or WorldTerrain.tile(Vector2i(x,y))!="~":continue
				var cell := Vector2i(x,y)
				if cell.distance_squared_to(center)<distance:chosen=cell;distance=cell.distance_squared_to(center)
		if chosen.x<0:_capture_errors.append("広域の水際が見つからない");continue
		var preview := ExpeditionView.new()
		preview.state=WorldExpedition.initial("town",{})
		preview.state["cell"]=[chosen.x,chosen.y]
		preview.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		preview.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
		root.add_child(preview)
		await process_frame;await process_frame;await RenderingServer.frame_post_draw
		RenderingServer.force_draw(false);RenderingServer.force_sync()
		var index := global_samples.size()+1
		var path := OUTPUT+"global-coast-%d.png" % index
		var im := root.get_texture().get_image()
		var water_region := WorldShoreline.region(chosen)
		if water_region.size!=Vector2(32,32):_capture_errors.append("広域の水際参照が空: "+str(chosen))
		else:
			var expected := WorldShoreline.texture().get_image().get_pixelv(Vector2i(water_region.position)+Vector2i(16,16))
			var sample := (chosen-preview._camera)*64+Vector2i(33,33)
			if not im.get_pixelv(sample).is_equal_approx(expected):_capture_errors.append("広域の水面が画面に描かれていない: "+str(chosen))
		if im.is_empty() or im.save_png(path)!=OK:_capture_errors.append(path)
		global_samples.append({"cell":[chosen.x,chosen.y],"image":path,"scope":"広域描画の確認。通常プレイで到達した記録ではない。"})
		preview.queue_free();await process_frame
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",{"status":"PASS" if _capture_errors.is_empty() and global_samples.size()==4 else "FAIL","first_region_images":_captured.size(),"global_samples":global_samples,"errors":_capture_errors,"world_terrain_sha256":WorldShoreline.data()["terrain_sha256"],"build":BuildIdentity.current()})
	await super._finish()
