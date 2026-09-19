class_name Combatant
extends RefCounted

enum Team { PARTY, ENEMY }

var id: String
var display_name: String
var team: Team
var job_id: String = ""
var max_hp: int
var hp: int
var max_mp: int
var mp: int
var attack: int
var defense: int
var magic: int
var resistance: int
var speed: int
var guard_rate: float = 1.0
var loot_available: bool = true
var learned: Array[String] = []
var equipped: Array[String] = []
var weaknesses: Array[String] = []


func _init(actor_id: String, actor_name: String, actor_team: Team, stats: Dictionary) -> void:
	id = actor_id
	display_name = actor_name
	team = actor_team
	max_hp = int(stats["hp"])
	hp = max_hp
	max_mp = int(stats["mp"])
	mp = max_mp
	attack = int(stats["attack"])
	defense = int(stats["defense"])
	magic = int(stats["magic"])
	resistance = int(stats["resistance"])
	speed = int(stats["speed"])


func is_alive() -> bool:
	return hp > 0


func damage(amount: int) -> int:
	var actual := mini(hp, maxi(0, amount))
	hp -= actual
	return actual


func heal(amount: int) -> int:
	if not is_alive():
		return 0
	var actual := mini(max_hp - hp, maxi(0, amount))
	hp += actual
	return actual


func snapshot() -> Dictionary:
	return {"id": id, "name": display_name, "hp": hp, "max_hp": max_hp, "mp": mp, "max_mp": max_mp}
