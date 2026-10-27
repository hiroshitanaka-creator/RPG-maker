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
	check(expanded.size()==6 and expanded.slice(0,5)==legacy,"訪問後も既存5件の全データと順序を保持")
	check(expanded.size()==6 and expanded[5]=={"id":"region3_port","name":"第3地方の港町（仮）","entrance":"region3_port_entrance","ship_cell":[180,45]},"訪問済み新港の正しい入口・船先を追加")
	check(visited==before,"候補の照会で保存状態を変更しない")
	check(FirstRegionTravel.destinations()==legacy,"新港訪問後も無引数APIを完全互換に保つ")
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
	finish()

func finish() -> void:
	var failed := checks.filter(func(item:Dictionary)->bool:return not item["ok"]).size()
	PlaySessionMetrics.write_json(OUT+"catalog-checks.json",{"checks":checks,"failed":failed})
	print("TASK081_CATALOG_RESULT: checks=%d failed=%d"%[checks.size(),failed])
	quit(0 if failed==0 else 1)
