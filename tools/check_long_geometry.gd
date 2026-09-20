extends SceneTree

var errors: Array[String]=[]

func check(condition: bool,message: String)->void:
	if not condition:errors.append(message)

func _initialize()->void:
	var original_enabled:=LongCampaign.enabled()
	LongCampaign._source["enabled"]=true
	var began:=Time.get_ticks_msec()
	var cold:=GameSession.new()
	check(cold.errors.is_empty(),"初回の定義検査にエラーがない")
	var cold_ms:=Time.get_ticks_msec()-began
	began=Time.get_ticks_msec()
	for iteration in range(20):
		var next:=GameSession.new()
		check(next.errors.is_empty(),"同じ定義での初期化を繰り返しても結果が一致する")
	var repeated_ms:=Time.get_ticks_msec()-began
	# 暫定の検査予算。20回で5秒なら、初期化1回の平均を250ms以下に保てる。
	check(repeated_ms<=5000,"同一定義での20回の初期化が5秒以内である")
	var count:=0
	for room in LongCampaign.data()["rooms"]:
		var id: String=room["id"]
		check(LongCampaign._reachable(id,room["spawn"],[29,14]),id+": 通路の先へ到達できる")
		check(LongCampaign._reachable(id,[29,14],room["spawn"]),id+": 同じ道を戻れる")
		check(not LongCampaign._reachable(id,room["spawn"],[0,0]),id+": 壁へ到達したことにしない")
		check(not LongCampaign._reachable(id,[7,1],[29,14]),id+": 壁を開始地点として通行を認めない")
		count+=1
	var area: Dictionary=LongCampaign.data()["rooms"][0]
	check(not LongCampaign._reachable(area["id"],area["spawn"],[29.5,14]),"半端な座標を別のマスへ丸めて到達扱いにしない")
	var original: Array=area["layout"].duplicate()
	for y in range(1,17):area["layout"][y]=original[y].substr(0,10)+"#"+original[y].substr(11)
	check(not LongCampaign._reachable(area["id"],area["spawn"],[29,14]),"地形を閉じたら以前の到達結果を使わない")
	area["layout"]=original
	check(LongCampaign._reachable(area["id"],area["spawn"],[29,14]),"地形を戻すと到達結果も更新する")
	LongCampaign._source["enabled"]=original_enabled
	PlaySessionMetrics.write_json("res://docs/verification/long-geometry-current.json",{
		"status":"PASS" if errors.is_empty() else "FAIL","rooms":count,"cold_init_ms":cold_ms,
		"repeated_inits":20,"repeated_init_ms":repeated_ms,"provisional_max_ms":5000,"failures":errors,
		"scope":"定義検査の初期化時間と、未開通の地形の到達判定。80話の完成や人間の所要時間ではない。","build":BuildIdentity.current()})
	print("LONG_GEOMETRY_TIMING: cold_ms=%d repeated_20_ms=%d" % [cold_ms,repeated_ms])
	for message in errors.slice(0,10):printerr("LONG_GEOMETRY_FAIL: "+message)
	if errors.is_empty():print("LONG_GEOMETRY_PASS: rooms=%d 地形の変更も検査に反映" % count)
	quit(0 if errors.is_empty() else 1)
