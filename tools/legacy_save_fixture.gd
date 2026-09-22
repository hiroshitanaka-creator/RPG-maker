extends RefCounted
## 旧仕様の数値を変えずに保存形式1の互換契約を検査するための入力。
## 新規ゲームの検査には使わない。形式2はcheck_integrated_*とlong-fullが検査する。
static func begin(game: GameSession,size: int=4)->bool:
	if not game.new_game(size):return false
	return as_legacy(game)
static func as_legacy(game: GameSession)->bool:
	var state:=game.export_state()
	state["format_version"]=1;state.erase("integrated")
	for actor in state["party"]:actor.erase("integrated")
	return game.import_state(state)

