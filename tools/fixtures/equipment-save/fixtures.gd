extends RefCounted
## 固定旧入力の派生。期待値はexpectations.jsonに手書きし、本番から作らない。

static func base() -> Dictionary:
	return GameSession._normalize_numbers(JSON.parse_string(FileAccess.get_file_as_string("res://tools/fixtures/equipment-save/base.json")))

static func region() -> Dictionary:
	var document := base()
	document["first_region"] = {"version": 1, "reserve": document.party.slice(1).duplicate(true), "coins": 20}
	document["party"] = [document.party[0]]
	document["inventory"]["world_map"] = 1
	document["overworld"] = {"active": true, "layer": "interior", "node": "start_village", "room": 0, "cell": [6, 7], "facing": 0, "transport": "walk", "cleared": [], "opened": [], "entry_lock": ""}
	# 固定版から採取した初期位置。現実のゲーム生成器で期待は作らない。
	document["overworld"]["cell"] = [6, 7]
	return document

static func legacy(region_mode: bool = false, count: int = 4) -> Dictionary:
	var document := region() if region_mode else base()
	document["format_version"] = 1
	document.erase("integrated")
	if not region_mode:document.party.resize(count)
	for person in document.party + document.get("first_region", {}).get("reserve", []):person.erase("integrated")
	return document

static func caps(actor: Dictionary, session: GameSession) -> void:
	var stats := session._compute_stats(actor, true)
	actor["max_hp"] = stats.hp
	actor["max_mp"] = stats.mp
	actor["hp"] = mini(actor.hp, actor.max_hp)
	actor["mp"] = mini(actor.mp, actor.max_mp)

static func context(session: GameSession) -> Dictionary:
	var abilities := session.abilities.duplicate(true)
	abilities["two_handed"] = {"id": "two_handed", "name": "両手持ち", "kind": "passive", "target": "self", "cost": 0, "power": 0, "hits": 1, "priority": 0, "element": "none", "description": "S1検証用の能力定義。戦闘係数を含まない。"}
	return {"legacy_session": session, "abilities": abilities}
