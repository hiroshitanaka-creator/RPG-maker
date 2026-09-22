extends SceneTree
var failures: Array[String]=[]
var routes:=0
func check(ok: bool,message: String)->void:
	if not ok:failures.append(message)
func _initialize()->void:
	var source:=IntegratedCampaign.data()
	var rules: Array=IntegratedProgression.rules()["enemy_rules"].map(func(r:Dictionary)->String:return r["id"])
	var found: Dictionary={}
	var expected: Array=[]
	for mission in LongCampaign.data()["missions"]:expected.append(mission["id"])
	var graph: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://world/map_graph.json"))
	for node in graph["nodes"]:expected.append("world/"+str(node["id"]))
	check(expected.size()==129 and source["assignments"].size()==129,"80話と49拠点の配分、欠落・追加0")
	for id in expected:
		var entry:=IntegratedCampaign.assignment(id)
		check(not entry.is_empty() and entry.get("rule") in rules,"機構を実定義へ接続: "+id)
		if entry.is_empty():continue
		found[entry["rule"]]=true
		check(not IntegratedProgression.weapon(entry["reward"]).is_empty(),"貸与される武器が存在")
		for route in entry["routes"]:
			var cell:=Vector2i(route["cell"][0],route["cell"][1])
			check(not LongCampaign.is_walkable(route["room"],cell,{}),"機構を利用する前は閉じている")
			check(LongCampaign.is_walkable(route["room"],cell,{entry["flag"]:true}),"解法に応じて実際の通行セルを開く")
			check(LongCampaign.is_walkable(route["room"],cell+Vector2i.LEFT) and LongCampaign.is_walkable(route["room"],cell+Vector2i.RIGHT),"近道の両端が元の通路へ接続")
			routes+=1
	check(found.size()==6,"全6機構の配分")
	var game:=GameSession.new();game.new_game(4)
	var before:=game.export_state()
	check(before["integrated"]["job_notes"].is_empty(),"開始時は未取得の手掛かり")
	game.read_job_lore()
	check(game.export_state()["integrated"]["job_notes"].size()==8,"町で読むと噂4・図鑑4を取得")
	var invalid:=game.export_state();invalid["integrated"]["outcomes"]["unknown"]={"rule":"conductor","methods":[]}
	check(not game.import_state(invalid),"存在しない拠点の解法を拒否")
	invalid=game.export_state();invalid["integrated"]["claimed"].append(expected[0])
	check(not game.import_state(invalid),"解法なしの報酬取得を拒否")
	invalid=game.export_state();invalid["progress_flags"]["integration_route_"+str(expected[0])]=true
	check(not game.import_state(invalid),"解法なしの開通フラグを拒否")
	for malformed in [null,[],"flags",7]:
		invalid=game.export_state();invalid["progress_flags"]=malformed
		check(not game.import_state(invalid),"フラグの型不正を例外なしで拒否")
	invalid=game.export_state();invalid["integrated"]["outcomes"][1]={}
	check(not game.import_state(invalid),"解法IDの型不正を例外なしで拒否")
	PlaySessionMetrics.write_json("res://docs/verification/integrated-campaign-current.json",{"status":"PASS" if failures.is_empty() else "FAIL","assignments":expected.size(),"rules":found.size(),"route_checks":routes,"failures":failures,"scope":"配分・通行セル・入力境界。通常全編の操作証拠はlong-full検査。"})
	for message in failures:printerr("INTEGRATED_CAMPAIGN_FAIL: "+message)
	print("INTEGRATED_CAMPAIGN_RESULT: assignments=%d routes=%d failures=%d" % [expected.size(),routes,failures.size()])
	quit(0 if failures.is_empty() else 1)
