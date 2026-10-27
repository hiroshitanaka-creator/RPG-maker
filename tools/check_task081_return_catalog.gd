extends SceneTree
## 既存の閉じたAPIと、訪問済みの新港を扱う本番文脈APIの互換検証。
const OUT := "res://docs/verification/task-081-ci-fix/"
var checks: Array = []

func check(ok: bool, label: String) -> bool:
	checks.append({"ok":ok,"label":label})
	if not ok:printerr("TASK081_CATALOG_FAIL: "+label)
	return ok

func _initialize() -> void:
	var fixture: Dictionary=WorldExpedition._integers(JSON.parse_string(FileAccess.get_file_as_string("res://docs/verification/task-009/continuing-contract.json")))
	var legacy: Array=fixture["destinations"]
	check(FirstRegionTravel.destinations()==legacy,"無引数の既存5件・順序・全フィールドを維持")
	var api := FirstRegionTravel.new()
	if not check(api.has_method("destinations_for"),"本番文脈を受け取る拡張APIを公開"):finish();return
	var old_game := GameSession.new();old_game.new_first_region()
	var no_travel := old_game.export_state();no_travel["first_region"].erase("travel")
	var no_travel_before := no_travel.duplicate(true)
	check(api.call("destinations_for",no_travel)==legacy,"travel項目のない旧保存も既存5件のまま照会")
	check(no_travel==no_travel_before and not no_travel["first_region"].has("travel"),"旧保存の照会でtravelや訪問履歴を補完しない")
	var game := GameSession.new()
	var source := "res://docs/verification/task-081-implementation/arrival-save.json"
	var path := "user://task081-catalog.json"
	var file := FileAccess.open(path,FileAccess.WRITE);file.store_buffer(FileAccess.get_file_as_bytes(source));file.close()
	if not check(game.load_game(path),"実在する新港の通常到達保存を読込"):finish();return
	var visited := game.export_state()
	var before := visited.duplicate(true)
	var old_state := visited.duplicate(true)
	old_state["first_region"]["travel"]["visited"].erase("region3_port")
	check(api.call("destinations_for",old_state)==legacy,"新港未訪問の旧保存は既存候補のまま")
	var expanded: Array=api.call("destinations_for",visited)
	var full_expected := legacy.duplicate(true)
	full_expected.append({"id":"region3_port","name":"第3地方の港町（仮）","entrance":"region3_port_entrance","ship_cell":[180,45]})
	check(expanded.size()==6 and expanded.slice(0,5)==legacy,"訪問後も既存5件の全データと順序を保持")
	check(expanded.size()==6 and expanded[5]=={"id":"region3_port","name":"第3地方の港町（仮）","entrance":"region3_port_entrance","ship_cell":[180,45]},"訪問済み新港の正しい入口・船先を追加")
	check(visited==before,"候補の照会で保存状態を変更しない")
	check(FirstRegionTravel.destinations()==legacy,"新港訪問後も無引数APIを完全互換に保つ")
	check(api.call("destinations_for",old_state)==legacy and api.call("destinations_for",visited)==expanded,"訪問済み→未訪問→訪問済みを連続照会しても履歴が混ざらない")
	var unvisited_before := old_state.duplicate(true)
	check(not FirstRegionTravel.return_to(old_state,"pc_01","region3_port") and old_state==unvisited_before,"未訪問の新港へ帰還できず状態も不変")
	var actor_id := ""
	for member in visited["party"]:
		if member["hp"]>0 and member["mp"]>=2:actor_id=str(member["id"]);break
	if not check(not actor_id.is_empty(),"通常保存に帰還できる生存者がいる"):finish();return
	var actor: Dictionary=visited["party"].filter(func(member:Dictionary)->bool:return member["id"]==actor_id)[0]
	var previous_mp: int=actor["mp"]
	check(FirstRegionTravel.return_to(visited,actor_id,"region3_port"),"同じ文脈APIで訪問済み新港へ帰還")
	check(visited["overworld"]["layer"]=="world" and visited["overworld"]["cell"]==[179,44] and visited["overworld"]["facing"]==1,"新港入口前・外向きの既存着地規則")
	check(actor["mp"]==previous_mp-2 and visited["first_region"]["travel"]["ship_cell"]==[180,45],"選択生存者だけMP2・船は新港")
	check(FirstRegionTravel.destinations()==legacy,"帰還後も既存APIの結果を変更しない")
	var unknown := before.duplicate(true);unknown["first_region"]["travel"]["visited"].append("unknown_port")
	check(api.call("destinations_for",unknown)==expanded,"未知の訪問値から新しい行先を作らない")
	check(not FirstRegionTravel.return_to(unknown,actor_id,"unknown_port"),"未知の行先への帰還を拒否")
	var away := before.duplicate(true)
	FirstRegion.place(away["overworld"],{"layer":"world","node":"","room":0,"cell":[32,54]})
	check(api.call("destinations_for",away)==expanded,"現在地が離れた地方でもvisitedに基づく同じ新港候補")
	var returning := GameSession.new()
	if check(returning.import_state(away),"離れた地方の有効な保存を受理"):
		check(returning.cast_first_region_return(actor_id,"region3_port") and returning.overworld_state()["cell"]==[179,44],"離れた地方から新港へ通常の帰還実行")
	for negative in ["unvisited","unlearned","mp","dead","battle","unknown_actor","unknown_target"]:
		var candidate := away.duplicate(true)
		if negative=="unvisited":candidate["first_region"]["travel"]["visited"].erase("region3_port")
		if negative=="unlearned":candidate["first_region"]["travel"]["return_learned"]=false
		for member in candidate["party"]:
			if member["id"]==actor_id:
				if negative=="mp":member["mp"]=1
				if negative=="dead":member["hp"]=0
		var rejected := GameSession.new()
		if not check(rejected.import_state(candidate),"帰還拒否の前提状態を受理: "+negative):continue
		if negative=="battle":check(rejected.start_first_region_battle({"kind":"battle","id":"first_region_encounter","enemies":["slime"],"seed":815})!=null,"帰還拒否の本番戦闘を開始")
		var unchanged := rejected.export_state()
		var accepted := rejected.cast_first_region_return("missing" if negative=="unknown_actor" else actor_id,"missing" if negative=="unknown_target" else "region3_port")
		check(not accepted and rejected.export_state()==unchanged,"新港帰還の拒否で全状態保持: "+negative)
	var isolated: Array=api.call("destinations_for",before)
	isolated[0]["name"]="返却値だけの変更"
	isolated[5]["ship_cell"][0]=-1
	isolated.append({"id":"返却配列だけの追加"})
	check(FirstRegionTravel.destinations()==legacy,"返却候補の変更で既存キャッシュを変更しない")
	check(api.call("destinations_for",before)==full_expected,"返却候補の変更で新港キャッシュを変更しない")
	check(before==game.export_state(),"照会と別セッションの帰還で元保存を変更しない")
	finish()

func finish() -> void:
	var failed := checks.filter(func(item:Dictionary)->bool:return not item["ok"]).size()
	PlaySessionMetrics.write_json(OUT+"catalog-checks.json",{"checks":checks,"failed":failed})
	print("TASK081_CATALOG_RESULT: checks=%d failed=%d"%[checks.size(),failed])
	quit(0 if failed==0 else 1)
