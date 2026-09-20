extends SceneTree

var errors: Array[String]=[]
var cases:=0

func check(condition: bool,message: String)->void:
	if not condition:errors.append(message)

func _initialize()->void:
	var definition: Variant=load("res://scripts/world/long_campaign.gd")
	var clues: Array=LongCampaign.data().get("clues",[])
	var authored: Dictionary={}
	for mission in LongCampaign.data().get("missions",[]):authored[mission["arc"]]=0
	check(not clues.is_empty(),"制作済みの連作に設置と回収の台帳がある")
	check(definition.has_method("clue_stage"),"保存された進行から設置と回収の既読段階を導ける")
	if not errors.is_empty():_finish();return
	var ids: Dictionary={}
	var chained:=0
	for clue in clues:
		check(not ids.has(clue.get("id")),"回収IDが重複しない")
		ids[clue["id"]]=clue
		check(authored.has(clue.get("arc")),"制作済みの連作を参照する")
		if authored.has(clue.get("arc")):authored[clue["arc"]]+=1
	for clue in clues:
		var setup: Dictionary=clue.get("setup",{})
		var payoff: Dictionary=clue.get("payoff",{})
		var setup_at:=_location(setup)
		var payoff_at:=_location(payoff)
		check(setup_at>=0 and payoff_at>setup_at,clue["id"]+": 設置を提示してから回収する")
		for required in clue.get("requires",[]):
			check(ids.has(required),clue["id"]+": 依存IDが存在する")
			if not ids.has(required):continue
			check(ids[required]["arc"]==clue["arc"],clue["id"]+": 順不同の別連作へ依存しない")
			check(_location(ids[required]["payoff"])<payoff_at,clue["id"]+": 先行回収が必要な順で配置され循環しない")
			chained+=1
		if setup_at<0 or payoff_at<0:continue
		var unseen: Dictionary={"progress_flags":{},"expedition":{}}
		check(definition.clue_stage(clue["id"],unseen)==0,clue["id"]+": 新規状態で情報を先出ししない")
		var state:=_before(setup)
		check(definition.clue_stage(clue["id"],state)==0,clue["id"]+": 設置を読み終える前は未読")
		state["expedition"]["stage"]+=1
		check(definition.clue_stage(clue["id"],state)==1,clue["id"]+": 設置後に最初の意味だけを解放する")
		var journal: Array=definition.journal(state)
		for entry in journal:
			if entry["id"]==clue["id"]:check(not entry.has("resolved"),clue["id"]+": 未回収の解答を手帳に出さない")
		state=_before(payoff)
		check(definition.clue_stage(clue["id"],state)==1,clue["id"]+": 回収直前に答えを出さない")
		state["expedition"]["stage"]+=1
		check(definition.clue_stage(clue["id"],state)==2,clue["id"]+": 回収を読み終えると意味が更新される")
		journal=definition.journal(state)
		for entry in journal:
			if entry["id"]==clue["id"]:check(entry.get("resolved","").begins_with(clue["resolved"]),clue["id"]+": 解答が手帳へ反映される")
		check(JSON.parse_string(JSON.stringify(state))["progress_flags"]==state["progress_flags"],"台帳用の追加保存変数を必要としない")
		cases+=1
	for arc in authored:check(authored[arc]>=2,str(arc)+": 再解釈と次の問いをIDで記録する")
	check(chained>=2,"回収を前提とする連鎖が2本以上ある")
	_finish()

func _location(reference: Dictionary)->int:
	if not reference.has_all(["mission","step","text"]):return -1
	var mission:=LongCampaign.mission(reference["mission"])
	if mission.is_empty():return -1
	for at in range(mission["steps"].size()):
		var entry: Dictionary=mission["steps"][at]
		if entry["id"]==reference["step"]:
			check(reference["text"] in entry.get("text",[]),"台帳の本文が本番の提示地点に存在する")
			# 各連作は末尾1〜4の話を順に解放する。別連作の順は固定しない。
			return int(str(mission["id"]).get_slice("_",2))*100+at
	return -1

func _before(reference: Dictionary)->Dictionary:
	var state: Dictionary={"progress_flags":{"long_campaign_started":true},"expedition":{"id":reference["mission"],"stage":0}}
	var mission:=LongCampaign.mission(reference["mission"])
	for earlier in LongCampaign.data()["missions"]:
		if earlier["arc"]==mission["arc"] and earlier["id"]<mission["id"]:
			state["progress_flags"][LongCampaign.cleared_flag(earlier["id"])]=true
	for at in range(mission["steps"].size()):
		if mission["steps"][at]["id"]==reference["step"]:state["expedition"]["stage"]=at;break
	return state

func _finish()->void:
	PlaySessionMetrics.write_json("res://docs/verification/long-clues-current.json",{
		"status":"PASS" if errors.is_empty() else "FAIL","clues":cases,"failures":errors,
		"scope":"設置・回収の本文と順序、既読直前・直後の手帳公開範囲。意味が伝わるかの主観は未検証。",
		"build":BuildIdentity.current()})
	for error in errors:printerr("LONG_CLUES_FAIL: "+error)
	if errors.is_empty():print("LONG_CLUES_PASS: clues=%d 設置・回収の到達順と既読境界を検査" % cases)
	quit(0 if errors.is_empty() else 1)
