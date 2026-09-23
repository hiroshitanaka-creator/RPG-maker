extends RefCounted
## 検査自身の中断再開。ゲーム保存と集計を2世代で保持し、異なる版への再利用を拒否する。
const COUNTERS=["moved","activities","battles","rounds","saves","save_bytes","max_save_ms","max_load_ms"]
var prefix: String
var build: Dictionary
var checks: Dictionary
var initial_hash: String
func _init(session: String,label: String,source: Dictionary,code: Dictionary,initial: Dictionary)->void:
	prefix="user://qa_long_audit_"+session+"_"+label
	build=source;checks=code
	initial_hash=JSON.stringify(initial).sha256_text()
func load_latest(game: GameSession,driver: RefCounted)->Dictionary:
	var candidates: Array=[]
	var existed:=false
	for slot in range(2):
		var path:=prefix+"_%d.receipt.json" % slot
		if not FileAccess.file_exists(path):continue
		existed=true
		var parser:=JSON.new()
		if parser.parse(FileAccess.get_file_as_string(path))!=OK:continue
		var raw: Variant=parser.data
		if not raw is Dictionary:continue
		var value: Dictionary=LongCampaign._integers(raw)
		if value.get("build")!=build or value.get("checks")!=checks or value.get("initial_hash")!=initial_hash:continue
		if value.get("version")!=1 or not value.get("sequence") is int or not value.get("counters") is Dictionary:continue
		if value["sequence"]<1 or value["sequence"]>5000 or not value.get("checkpoints") is int or value["checkpoints"]<0 or value["checkpoints"]>value["sequence"]:continue
		if not value.get("world_detour") is bool or not value.get("resumptions") is int or value["resumptions"]<0:continue
		if not (value.get("elapsed_seconds") is int or value.get("elapsed_seconds") is float) or value["elapsed_seconds"]<0:continue
		if value.get("save")!=prefix+"_%d.save.json" % slot or not FileAccess.file_exists(value["save"]):continue
		if FileAccess.get_sha256(value["save"])!=value.get("save_sha256"):continue
		candidates.append(value)
	if candidates.is_empty():return {"error":"保存・集計・コードの一致する再開記録がありません。"} if existed else {}
	candidates.sort_custom(func(a:Dictionary,b:Dictionary)->bool:return a["sequence"]>b["sequence"])
	var chosen: Dictionary=candidates[0]
	if not game.load_game(chosen["save"]):return {"error":"再開用のゲーム保存を読めません。"}
	if game.play_metrics.source!="automated":return {"error":"自動検査の実行記録ではありません。"}
	var state:=game.export_state()
	var missions:=0;var activities:=0;var battles:=0
	for mission in LongCampaign.data()["missions"]:
		if state["progress_flags"].get(LongCampaign.cleared_flag(mission["id"]),false):missions+=1
		for activity in mission["activities"]:
			if state["progress_flags"].get(LongCampaign.activity_flag(activity["id"],"done"),false):activities+=1
	for event in game.play_metrics.events:
		if event["kind"]=="battle_finished" and event["details"].get("victory",false):battles+=1
	if chosen.get("missions")!=missions or chosen["counters"].get("activities")!=activities or chosen["counters"].get("battles")!=battles:return {"error":"集計と保存内の実行履歴が一致しません。"}
	for key in COUNTERS:
		if not chosen["counters"].get(key) is int or chosen["counters"][key]<0:return {"error":"検査集計の型が不正です。"}
		driver.set(key,chosen["counters"][key])
	return chosen
func store(game: GameSession,driver: RefCounted,progress: Dictionary)->bool:
	var slot: int=progress["sequence"]%2
	var save_path:=prefix+"_%d.save.json" % slot
	if not game.save_game(save_path):return false
	var value:=progress.duplicate(true)
	value["version"]=1;value["build"]=build;value["checks"]=checks;value["initial_hash"]=initial_hash
	value["save"]=save_path;value["save_sha256"]=FileAccess.get_sha256(save_path)
	value["counters"]={}
	for key in COUNTERS:value["counters"][key]=driver.get(key)
	return PlaySessionMetrics.write_json(prefix+"_%d.receipt.json" % slot,value)
