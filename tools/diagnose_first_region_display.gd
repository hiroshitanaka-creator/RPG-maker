extends "res://tools/smoke_first_region.gd"
## 凍結された入力・判定は変えず、失敗時の読み取り情報だけを追加する。
func _finish() -> void:
	var party: Array=[]
	for actor in _state().get("party",[]):party.append({"id":actor["id"],"hp":actor["hp"],"mp":actor["mp"]})
	print("FIRST_REGION_DIAGNOSTIC: "+JSON.stringify({"blocker":_blocker,"moves":_moves,"turns":_turns,"snapshot":_snapshot(),"party":party,"boss_starts":_boss_starts,"boss_won":_boss_won,"pose":_pose()}))
	super._finish()
