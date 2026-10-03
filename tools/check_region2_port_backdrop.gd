extends SceneTree
## 第2港の外観（一枚絵の背景＋見えない通行地図＋上の層）の検査。
## 既存の check_region2_port.gd は変更せず、外観の表現が変わったことで確かめられなくなった項目（部品タイル8棟）に
## 相当する確認を、新しい表現に対して行う。人工状態による検査であり、通常操作の撮影ではない。
const LIMIT_MS := 120000
const COLUMNS := 45
const ROWS := 30
var started := Time.get_ticks_msec()
var checks := 0
var failures: Array[String] = []

func check(ok: bool, message: String) -> bool:
	checks += 1
	if not ok:failures.append(message)
	return ok

func exterior_state(cell: Array) -> Dictionary:
	var game := GameSession.new()
	game.new_first_region()
	var saved := game.export_state()
	FirstRegion.place(saved["overworld"],{"layer":"interior","node":"brine_port","room":0,"cell":cell})
	saved["overworld"]["transport"]="walk"
	return saved

func reach(saved: Dictionary, start: Vector2i) -> Dictionary:
	var seen := {start:true}
	var queue: Array[Vector2i]=[start]
	var index := 0
	while index<queue.size():
		var p := queue[index];index+=1
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var q: Vector2i = p+d
			if not seen.has(q) and FirstRegion.walkable(saved,q):seen[q]=true;queue.append(q)
	return seen

func image_of(path: String) -> Image:
	return Image.load_from_file(ProjectSettings.globalize_path("res://"+path))

func _initialize() -> void:
	var data := Region2Port.data()
	var map: Dictionary=data["maps"]["brine_port:0"]
	var room: Dictionary=data["site"]["rooms"][0]
	var record: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://assets/source_records/region2-port-town-backdrop.json")))
	# --- 1. 絵と地図の大きさ
	check(map["width"]==COLUMNS and map["height"]==ROWS,"外観は45×30マス")
	check(map["layout"]==room["layout"],"地図の通行地図と部屋の通行地図が同一")
	check(room["layout"].size()==ROWS and room["layout"].all(func(row:String)->bool:return row.length()==COLUMNS),"通行地図の行数・桁数")
	check(room["layout"]==record["layout"],"通行地図が生成記録と一致")
	check(map["tiles"].is_empty() and map["layers"].is_empty(),"部品タイルを並べず一枚絵だけ")
	var backdrop := image_of(map["backdrop"]["path"])
	check(backdrop!=null and backdrop.get_size()==Vector2i(COLUMNS*32,ROWS*32),"背景は1440×960px（45×30マス×32px）")
	if backdrop!=null:
		var colors := {}
		var opaque := true
		for y in range(0,backdrop.get_height(),1):
			for x in range(0,backdrop.get_width(),1):
				var c := backdrop.get_pixel(x,y)
				colors[c.to_html(false)]=true
				if c.a<1.0:opaque=false
		check(colors.size()<=64,"背景は64色以内: %d" % colors.size())
		check(opaque,"背景は不透明")
	# --- 2. 上の層は背景と同じ画素を切り出したもの
	var atlas := image_of(map["overlays"]["path"])
	var pieces: Array=map["overlays"]["pieces"]
	check(atlas!=null and pieces.size()>0,"上の層の部品がある: %d" % pieces.size())
	if atlas!=null and backdrop!=null:
		var bad_alpha := 0
		var mismatch := 0
		var pixels := 0
		for piece in pieces:
			check(piece[6] is int and piece[6]>=1 and piece[6]<=ROWS+1,"部品の足元の行が範囲内: "+str(piece[7]))
			for y in range(piece[3]):
				for x in range(piece[2]):
					var a := atlas.get_pixel(piece[0]+x,piece[1]+y)
					if a.a==0.0:continue
					if a.a!=1.0:bad_alpha+=1;continue
					pixels+=1
					if a.to_html(false)!=backdrop.get_pixel(piece[4]+x,piece[5]+y).to_html(false):mismatch+=1
		check(bad_alpha==0,"上の層のアルファは0か255だけ")
		check(mismatch==0 and pixels>0,"上の層の画素が背景と全て同じ（%d画素）" % pixels)
	# --- 3. 通行地図と実際の通り抜け判定が全マスで一致する
	var saved := exterior_state(record["spawn"])
	var npc_cells := {}
	for event in room["events"]:npc_cells[Vector2i(event["cell"][0],event["cell"][1])]=true
	var disagreements := 0
	var walkable_count := 0
	for y in range(ROWS):
		for x in range(COLUMNS):
			var expected: bool = room["layout"][y][x]=="." and not npc_cells.has(Vector2i(x,y))
			if expected:walkable_count+=1
			if FirstRegion.walkable(saved,Vector2i(x,y))!=expected:disagreements+=1
	check(disagreements==0,"通行地図と実際の判定が全%dマスで一致（歩ける%dマス）" % [COLUMNS*ROWS,walkable_count])
	check(not FirstRegion.walkable(saved,Vector2i(-1,0)) and not FirstRegion.walkable(saved,Vector2i(COLUMNS,ROWS-1)),"地図の外へ出られない")
	var border_open := false
	for x in range(COLUMNS):
		if room["layout"][0][x]=="." or room["layout"][ROWS-1][x]==".":border_open=true
	for y in range(ROWS):
		if room["layout"][y][0]=="." or room["layout"][y][COLUMNS-1]==".":border_open=true
	check(not border_open,"外周の1周は通れない")
	# --- 4. 8棟・扉・アーチ・桟橋・住人（部品タイルの検査に代わる確認）
	var start := Vector2i(record["spawn"][0],record["spawn"][1])
	var seen := reach(saved,start)
	check(seen.has(start) and seen.has(Vector2i(record["exit"][0],record["exit"][1])),"入口からアーチの出口へ歩ける")
	check(seen.has(Vector2i(record["dock"][0],record["dock"][1])),"入口から船のそばの桟橋へ歩ける")
	var names: Array=["inn","item","weapon","armor","shrine","harbor","home_a","home_b"]
	check(record["doors"].size()==8,"8棟の扉が記録されている")
	for name in names:
		var door: Array=record["doors"][name]
		var cell := Vector2i(door[0],door[1])
		check(seen.has(cell) and seen.has(cell+Vector2i.DOWN),"入口から扉と扉の前へ歩ける: "+name)
		check(not FirstRegion.walkable(saved,cell+Vector2i.UP),"扉の奥（建物の壁）へ入れない: "+name)
		var wall := 0
		for dy in range(-3,1):
			for dx in range(-3,4):
				var q := cell+Vector2i(dx,dy)
				if q.x>=0 and q.y>=0 and q.x<COLUMNS and q.y<ROWS and not FirstRegion.walkable(saved,q):wall+=1
		check(wall>=8,"扉のまわりに建物の壁がある: "+name)
	for link in data["definition"]["second_port_doors"]:
		if link["from"]["room"]==0:check(record["doors"].values().has(link["from"]["cell"]),"扉の接続が8棟の扉と一致")
	var guarded := 0
	for spec in room["events"]:
		var cell := Vector2i(spec["cell"][0],spec["cell"][1])
		check(room["layout"][cell.y][cell.x]==".","住人の立つマスは地図上で歩ける: "+spec["id"])
		var around := 0
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			if seen.has(cell+d):around+=1
		check(around>0,"住人に話しかけられる隣のマスへ歩ける: "+spec["id"])
		for step in spec.get("patrol",[]):check(room["layout"][step[1]][step[0]]=="." and (seen.has(Vector2i(step[0],step[1])) or npc_cells.has(Vector2i(step[0],step[1]))),"巡回の道がすべて歩ける: "+spec["id"])
		guarded+=1
	check(guarded==4,"外観の住人は4人")
	finish()

func finish() -> void:
	check(Time.get_ticks_msec()-started<LIMIT_MS,"120秒以内")
	PlaySessionMetrics.write_json("res://docs/verification/region2-port-backdrop/checks.json",{"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"elapsed_ms":Time.get_ticks_msec()-started,"limit_ms":LIMIT_MS,"method":"人工状態による一枚絵の外観の検査。通常操作の撮影ではない。"})
	for failure in failures:printerr("REGION2_BACKDROP_FAIL: "+failure)
	print("REGION2_BACKDROP_PASS: checks=%d" % checks if failures.is_empty() else "REGION2_BACKDROP_FAIL")
	quit(0 if failures.is_empty() else 1)
