extends SceneTree

const CATALOG: String="res://data/long_campaign_v1.json"
const IMPLEMENTATION: String="res://scripts/world/long_campaign.gd"
var errors: Array[String]=[]

func check(value: bool,message: String)->void:
	if not value:errors.append(message)

func _initialize()->void:
	check(FileAccess.file_exists(CATALOG),"長編の本番データが存在する")
	check(FileAccess.file_exists(IMPLEMENTATION),"長編の進行処理が存在する")
	if not errors.is_empty():
		_finish()
		return
	var document: Variant=JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	check(document is Dictionary,"長編データが辞書である")
	if not document is Dictionary:
		_finish()
		return
	check(document.get("arcs",[]).size()==20,"既存の土地に20件の連続した物語を置く")
	check(document.get("missions",[]).size()==80,"80件の冒険を定義する")
	check(document.get("rooms",[]).size()==80,"再訪して使う80区画を定義する")
	check(document.get("enabled",false)==true,"長編が本番の新規開始で有効になっている")
	var definition: Variant=load(IMPLEMENTATION)
	check(definition!=null,"進行処理を読み込める")
	if definition!=null:
		var game:=GameSession.new()
		var findings: Array=definition.audit(game.abilities,game.enemy_definitions)
		for finding in findings:errors.append(str(finding))
	_finish()

func _finish()->void:
	for message in errors:printerr("LONG_CONTENT_FAIL: "+message)
	if errors.is_empty():print("LONG_CONTENT_PASS: 20連作・80冒険・80区画の定義と依存を検査")
	quit(0 if errors.is_empty() else 1)
