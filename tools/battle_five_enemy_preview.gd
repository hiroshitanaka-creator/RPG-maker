extends GameSession
## 5体の配置だけを確認する撮影用入力。通常ゲームの敵4体上限は変更しない。
var preview: BattleState
var preview_ids: Array[String]=["bat","ember_wisp","slime","shell_guard","slime"]

func prepare(count: int = 4) -> void:
	new_game(count)
	var base := start_battle(preview_ids.slice(0,4),20260927)
	var party: Array[Combatant]=[]
	var foes: Array[Combatant]=[]
	for unit in base.actors:
		if unit.team==Combatant.Team.PARTY:party.append(unit.copy())
		else:foes.append(unit.copy())
	var definition: Dictionary=enemy_definitions[preview_ids[4]]
	var fifth := Combatant.new("enemy_05",definition["name"],Combatant.Team.ENEMY,definition["stats"])
	fifth.learned.assign(definition["abilities"]);fifth.equipped.assign(definition["abilities"])
	fifth.weaknesses.assign(definition["weaknesses"]);fifth.tactics=definition["tactics"].duplicate(true)
	foes.append(fifth)
	preview=BattleState.new(party,foes,catalog,20260927)
	preview.potions=base.potions

func current_battle() -> BattleState:
	return preview if preview!=null else super.current_battle()

func current_enemy_ids() -> Array[String]:
	return preview_ids.duplicate() if preview!=null else super.current_enemy_ids()
