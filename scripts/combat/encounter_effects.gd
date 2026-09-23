class_name EncounterEffects
extends RefCounted
## 一つの戦闘内の効果と公開知識。BattleStateへの参照は循環させない。
var _battle: WeakRef
var states: Dictionary = {}
var rules: Dictionary = {}
var knowledge: Dictionary = {}
var field: Dictionary = {}
var reactions: Array[Dictionary] = []
var methods: Array[String] = []
var action_serial := 0
var current: Dictionary = {}
var phase_index := 0
var _deaths: Dictionary = {}
var _countered: Dictionary = {}

func _init(battle: RefCounted) -> void:
	_battle = weakref(battle)

func state(id: String) -> Dictionary:
	if not states.has(id):states[id] = {"opportunities":0}
	return states[id]

func record_method(value: String) -> void:
	if value not in methods:methods.append(value)

func attack(action: BattleAction) -> bool:
	var b = _battle.get_ref()
	return action.kind==BattleAction.Kind.ATTACK or (action.kind==BattleAction.Kind.ABILITY and b.catalog.abilities.get(action.ability_id,{}).get("kind") in ["physical","magic"])

func configure(definition: Dictionary, known: Dictionary) -> void:
	var b = _battle.get_ref()
	rules = definition.duplicate(true)
	knowledge = known.duplicate(true)
	if rules.is_empty():return
	for actor in b.living(Combatant.Team.ENEMY):
		if rules.has("armor_defense"):state(actor.id)["armor"] = int(rules["armor_defense"])
		if rules.has("death_burst"):state(actor.id)["death_armed"] = true
		for key in ["charge","magic","field"]:
			if not rules.get(key,false):continue
			var skill: String = {"charge":"charge_blow","magic":"arc_burst","field":"reflect_field"}[key]
			if skill not in actor.learned:actor.learned.append(skill)
			if skill not in actor.equipped:actor.equipped.append(skill)
		if rules.get("charge",false) or rules.has("phase_round"):
			for skill in ["charge_blow","arc_burst"]:
				if skill not in actor.learned:actor.learned.append(skill)
				if skill not in actor.equipped:actor.equipped.append(skill)
		if rules.get("field",false):
			if "bolt_shot" not in actor.learned:actor.learned.append("bolt_shot")
			if "bolt_shot" not in actor.equipped:actor.equipped.append("bolt_shot")
	if rules.get("device","")=="armor":_make_device("armor_regulator",int(rules.get("device_hp",45)),"装甲調整器")

func _make_device(id: String, hp: int, label: String) -> void:
	var b = _battle.get_ref()
	var existing = b.actor_by_id(id)
	if existing != null:
		existing.hp=hp;existing.max_hp=hp
		_deaths.erase(id)
		return
	var device := Combatant.new(id,label,Combatant.Team.ENEMY,{"hp":hp,"mp":0,"attack":0,"defense":0,"magic":0,"resistance":0,"speed":0})
	device.is_device = true
	b.actors.append(device)

func cost(actor: Combatant, ability: Dictionary) -> int:
	return IntegratedProgression.ability_cost(ability,actor.affinities,actor.form_mp_add)

func validate(action: BattleAction) -> String:
	var b = _battle.get_ref()
	var actor = b.actor_by_id(action.actor_id)
	var target = b.actor_by_id(action.target_id)
	if actor==null or target==null:return "対象が存在しません。"
	var own: Dictionary = states.get(actor.id,{})
	var other: Dictionary = states.get(target.id,{})
	if attack(action) and own.get("recovery",false):return "過負荷のため次の本人行動機会は攻撃できません。防御・道具・観察を選べます。"
	if action.kind!=BattleAction.Kind.ABILITY:return ""
	var ability: Dictionary = b.catalog.abilities[action.ability_id]
	var kind: String = ability["kind"]
	if kind=="passive":return "装着による効果です。行動として使用しません。"
	if kind=="focus":
		if actor.focus_binding.is_empty() or actor.focus_binding not in actor.equipped:return "専心へ装着中の攻撃技を結び付けてください。"
		if own.get("focused",false):return "すでに準備しています。"
		if own.get("amplifier",{}).get("overload",false):return "過負荷増幅と専心は併用できません。"
	if kind in ["amplify","overdrive"]:
		if other.has("amplifier"):return "同系統の増幅は重複しません。"
		if kind=="overdrive" and other.get("focused",false):return "専心と過負荷増幅は併用できません。"
	if kind=="conduct" and other.has("conduct"):return "導電付与は重複しません。"
	if kind=="recycle" and other.has("recycle"):return "還流付与は重複しません。"
	if kind=="cover" and actor.id==target.id:return "護衛する別の仲間を選んでください。"
	if kind=="cover" and other.get("cover",{}).get("used",1)==0:return "その仲間には未使用の護衛が付いています。"
	if kind=="seal" and (target.is_device or other.get("seal_used",false)):return "この対象には封緘の完全な崩しを使えません。"
	if kind=="field" and not field.is_empty():return "準備中または有効な場が既にあります。"
	if kind=="disarm" and not other.get("death_armed",false):return "解除する残留反応がありません。"
	if kind=="restore_mp" and target.mp>=target.max_mp:return "対象のMPは満タンです。"
	return ""

func observe(target: Combatant) -> void:
	var b = _battle.get_ref()
	if rules.is_empty():
		b._log("observe","この相手に特殊な機構は見当たらない。",current.get("actor",""),target.id)
		return
	var id: String = rules["id"]
	var entry: Dictionary = knowledge.get(id,{"facts":[],"confirmed":false})
	entry["facts"] = [0,1]
	knowledge[id] = entry
	record_method("observe")
	b._log("observe"," / ".join(rules["facts"]),current.get("actor",""),target.id)

func confirm_rule(method: String) -> void:
	record_method(method)
	if rules.is_empty():return
	var id: String = rules["id"]
	var entry: Dictionary = knowledge.get(id,{"facts":[],"confirmed":false})
	entry["confirmed"] = true
	knowledge[id] = entry

func enemy_action(actor: Combatant) -> BattleAction:
	var b = _battle.get_ref()
	if rules.is_empty():return null
	var opponents = b.living(Combatant.Team.PARTY)
	if opponents.is_empty():return null
	var skill := ""
	if rules.has("phase_round"):skill="charge_blow" if phase_index==0 else "arc_burst"
	elif rules.get("field",false) and b.round_number%4==1 and field.is_empty():skill="reflect_field"
	elif rules.get("field",false):skill="bolt_shot"
	elif rules.get("charge",false) and b.round_number%2==1:skill="charge_blow"
	elif rules.get("magic",false) or (rules.get("charge",false) and b.round_number%2==0):skill="arc_burst"
	if not skill.is_empty() and skill in actor.equipped and actor.mp>=cost(actor,b.catalog.abilities[skill]):
		return BattleAction.skill(actor.id,actor.id if skill=="reflect_field" else opponents[0].id,skill)
	return null

func begin_action(actor: Combatant, action: BattleAction) -> bool:
	var b = _battle.get_ref()
	var own := state(actor.id)
	own["opportunities"]+=1
	current={"id":action_serial+1,"actor":actor.id,"bonus":0,"paid":0,"attack":attack(action),"overload":false}
	action_serial+=1
	if not actor.is_alive():
		own.erase("focused");own.erase("recovery")
		return false
	if own.get("focused",false):
		if action.kind==BattleAction.Kind.ABILITY and action.ability_id==actor.focus_binding:current["bonus"]=100
		own.erase("focused")
	if own.get("cancel",false):
		own.erase("cancel");own.erase("recovery")
		b._log("interrupted","封緘によって予定行動が中断された。",actor.id,actor.id)
		return false
	var ability: Dictionary = b.catalog.abilities.get(action.ability_id,{})
	if "charge" in ability.get("tags",[]) and own.get("seal_count",0)>0 and not own.get("seal_used",false):
		add_seal(actor)
		if own.get("cancel",false):
			own.erase("cancel");own.erase("recovery")
			b._log("interrupted","充填の開始で封緘が完成し、行動が止まった。",actor.id,actor.id)
			return false
	return true

func finish_action(actor: Combatant, action: BattleAction) -> void:
	var b = _battle.get_ref()
	var own := state(actor.id)
	if current.get("attack",false) and current.get("executed",false):
		if own.has("recycle") and int(current.get("paid",0))>0:
			var restored := mini(2,int(current["paid"]))
			actor.mp=mini(actor.max_mp,actor.mp+restored)
			own.erase("recycle")
			b._log("mp_refund","支払ったMPの一部が戻った。",actor.id,actor.id,restored)
		own.erase("conduct")
		own.erase("amplifier")
	var next_recovery: bool = current.get("overload",false) and current.get("executed",false)
	own.erase("recovery")
	if next_recovery:own["recovery"]=true
	flush_reactions()

func add_seal(target: Combatant) -> void:
	var b = _battle.get_ref()
	var own := state(target.id)
	if own.get("seal_used",false):return
	own["seal_count"]=int(own.get("seal_count",0))+1
	own["seal_last"]=b.round_number
	b._log("seal","封緘が進んだ。",current.get("actor",""),target.id,own["seal_count"])
	if own["seal_count"]>=3:
		own["seal_used"]=true
		own["seal_until"]=b.round_number+2
		own["cancel"]=true
		own["seal_count"]=0
		confirm_rule("seal_break")
		b._log("seal_break","封緘が完成した。予定行動1回を中断し、このラウンドと後続2ラウンドは防御0。",current.get("actor",""),target.id)

func apply(actor: Combatant, target: Combatant, ability: Dictionary) -> bool:
	var b = _battle.get_ref()
	var own := state(actor.id)
	var other := state(target.id)
	match ability["kind"]:
		"focus":own["focused"]=true
		"conduct":other["conduct"]={"until":b.round_number+1}
		"amplify","overdrive":other["amplifier"]={"until":b.round_number+1,"bonus":100 if ability["kind"]=="overdrive" else 50,"overload":ability["kind"]=="overdrive"}
		"deflect_physical":own["deflect"]="physical"
		"deflect_magic":own["deflect"]="magic"
		"cover":other["cover"]={"guardian":actor.id,"used":0}
		"seal":add_seal(target)
		"field":
			field={"owner":actor.id,"start":b.round_number+1,"end":b.round_number+2,"device":"reflection_anchor"}
			_make_device("reflection_anchor",120,"反射場の維持装置")
		"riposte":own["riposte"]={"until":b.round_number+1}
		"recycle":other["recycle"]={"until":b.round_number+1}
		"disarm":other["death_armed"]=false;confirm_rule("disarm")
		"restore_mp":
			var amount := mini(int(ability["power"]),target.max_mp-target.mp)
			target.mp+=amount
			b._log("mp_recover","息を整えてMPを回復した。",actor.id,target.id,amount)
		_:return false
	record_method(ability["kind"])
	b._log("effect",ability["description"],actor.id,target.id)
	return true

func redirect(target: Combatant, physical: bool, area: bool) -> Combatant:
	var b = _battle.get_ref()
	if not physical or area:return target
	var cover: Dictionary = state(target.id).get("cover",{})
	if cover.is_empty():return target
	var guardian = b.actor_by_id(cover["guardian"])
	if guardian==null or not guardian.is_alive():return target
	if cover["used"] not in [0,current["id"]]:return target
	cover["used"]=current["id"]
	current["covered"]=guardian.id
	record_method("cover")
	return guardian

func damage(actor: Combatant, target: Combatant, ability: Dictionary, weapon: Dictionary={}) -> int:
	var b = _battle.get_ref()
	var own: Dictionary=states.get(actor.id,{})
	var other: Dictionary=states.get(target.id,{})
	var physical: bool=ability.get("kind","physical")=="physical"
	var element: String=ability.get("element","none")
	if physical and own.has("conduct"):element="electric"
	var defense: int=int(other.get("armor",target.defense))
	if element=="electric" and rules.has("electric_defense") and target.team==Combatant.Team.ENEMY and not target.is_device:
		defense=int(rules["electric_defense"])
		confirm_rule("conducted_hit")
	if b.round_number<=int(other.get("seal_until",-1)):defense=0
	defense=maxi(0,defense-int(ability.get("ignore_defense",0)))
	var attack_value: int=actor.attack+int(weapon.get("attack",0))-actor.primary_weapon_attack
	var raw: int=BattleMath.physical(attack_value,defense,int(ability.get("power",100))) if physical else BattleMath.magical(actor.magic,target.resistance,int(ability["power"]),element in target.weaknesses)
	var bonus: int=int(current.get("bonus",0))+int(own.get("amplifier",{}).get("bonus",0))
	current["overload"]=bool(own.get("amplifier",{}).get("overload",false))
	raw=ceili(raw*(1.0+bonus/100.0))
	var rate: float=target.guard_rate
	if other.has("deflect"):
		rate*=0.2 if other["deflect"]==("physical" if physical else "magic") else 1.5
		if target.team==Combatant.Team.PARTY and other["deflect"]==("physical" if physical else "magic"):confirm_rule("deflect_"+other["deflect"])
	if current.get("covered","")==target.id:rate*=0.5
	rate*=target.physical_taken if physical else target.magic_taken
	if not field.is_empty() and b.round_number>=field["start"] and b.round_number<=field["end"] and physical and ("projectile" in weapon.get("tags",[]) or "projectile" in ability.get("tags",[])):
		rate*=0.5
	return maxi(1,ceili(raw*rate))

func after_hit(actor: Combatant, target: Combatant, amount: int, reactive: bool=true) -> void:
	var b = _battle.get_ref()
	var own := state(target.id)
	if reactive and amount>0 and target.is_alive() and not target.is_device and current.get("on_hit",{}).get("kind")=="seal":
		var applied: Array=current.get("on_hit_targets",[])
		if target.id not in applied:
			applied.append(target.id);current["on_hit_targets"]=applied
			add_seal(target)
	if reactive and amount>0 and target.is_alive() and own.has("riposte") and actor.team!=target.team:
		var key := "%s:%d" % [target.id,current.get("id",0)]
		if not _countered.has(key):
			_countered[key]=true
			reactions.append({"kind":"counter","actor":target.id,"target":actor.id})
	if target.is_alive() or _deaths.has(target.id):return
	_deaths[target.id]=true
	if target.id=="armor_regulator":
		for id in states:states[id].erase("armor")
		confirm_rule("device")
	if not field.is_empty() and target.id==field["device"]:
		field.clear();confirm_rule("field_break")
	if own.get("death_armed",false):
		reactions.append({"kind":"residue","actor":target.id,"team":target.team,"amount":int(rules.get("death_burst",25))})

func flush_reactions() -> void:
	var b = _battle.get_ref()
	while not reactions.is_empty():
		var reaction: Dictionary=reactions.pop_front()
		var actor = b.actor_by_id(reaction["actor"])
		if reaction["kind"]=="counter":
			var target = b.actor_by_id(reaction["target"])
			if actor.is_alive() and target!=null and target.is_alive():
				b._hit(actor,target,BattleMath.physical(actor.attack,target.defense,100,target.guard_rate),"反撃",false)
				record_method("riposte")
		else:
			for target in b.living(Combatant.Team.PARTY if reaction["team"]==Combatant.Team.ENEMY else Combatant.Team.ENEMY):
				var rate: float=target.guard_rate*target.magic_taken
				if state(target.id).has("deflect"):rate*=0.2 if state(target.id)["deflect"]=="magic" else 1.5
				b._hit(actor,target,maxi(1,ceili(int(reaction["amount"])*rate)),"残留反応",false)

func end_round() -> void:
	var b = _battle.get_ref()
	for id in states:
		var own: Dictionary=states[id]
		for key in ["conduct","amplifier","recycle","riposte"]:
			if own.has(key) and int(own[key]["until"])<=b.round_number:own.erase(key)
		own.erase("deflect")
		if own.has("cover"):
			var guardian=b.actor_by_id(own["cover"]["guardian"])
			if own["cover"]["used"]!=0 or guardian==null or not guardian.is_alive():own.erase("cover")
		if own.get("seal_count",0)>0 and b.round_number>=int(own.get("seal_last",0))+2:own["seal_count"]=0
	if not field.is_empty() and b.round_number>=field["end"]:
		var device = b.actor_by_id(field["device"])
		if device!=null:device.hp=0
		field.clear()
	if rules.has("phase_round") and phase_index==0 and b.round_number+1>=int(rules["phase_round"]):
		phase_index=1
		b._log("phase_change","機構の局面が変化した。HP・MPと残る付与は持ち越す。","","")
		for actor in b.living(Combatant.Team.ENEMY):state(actor.id)["phase_magic"]=true

func description() -> Array[String]:
	var b = _battle.get_ref()
	var result: Array[String]=[]
	if not rules.is_empty():
		var seen: Dictionary=knowledge.get(rules["id"],{})
		result.append(str(rules["name"])+("・確認済み" if seen.get("confirmed",false) else "・規則未確認"))
		for index in seen.get("facts",[]):result.append(rules["facts"][int(index)])
		if seen.get("facts",[]).size()>0:result.append("見立て: "+str(rules.get("hypothesis","")))
		if rules.has("death_burst"):
			var armed: bool=b.living(Combatant.Team.ENEMY).any(func(foe:Combatant)->bool:return states.get(foe.id,{}).get("death_armed",false))
			result.append("残留反応: 全員へ基礎%dの魔法被害。最後の敵の後にも発動。防御・解除が可能。" % rules["death_burst"] if armed else "生存している相手の残留反応は解除済み。")
	if not field.is_empty():result.append("反射場: 第%d〜%dラウンド" % [field["start"],field["end"]])
	for device in b.actors:
		if device.is_device and device.is_alive():result.append("%s HP%d/%d。攻撃対象に選べる。" % [device.display_name,device.hp,device.max_hp])
	for id in states:
		var own: Dictionary=states[id]
		var actor=b.actor_by_id(id)
		var name: String=actor.display_name if actor!=null else "戦闘対象"
		if own.get("focused",false):result.append(name+": 次の本人行動機会に専心")
		if own.get("recovery",false):result.append(name+": 次の本人行動機会は攻撃不可")
		if own.get("seal_count",0)>0:result.append(name+": 封緘%d/3" % own["seal_count"])
		for key in ["conduct","amplifier","recycle","riposte"]:
			if own.has(key):result.append("%s: %s / 第%dラウンド終了まで" % [name,{"conduct":"次の物理攻撃に導電","amplifier":"次の攻撃に増幅","recycle":"次の有料攻撃に還流","riposte":"相手の1行動へ反撃1回"}[key],own[key]["until"]])
		if own.has("cover") and own["cover"]["used"]==0:result.append(name+": 次の単体物理攻撃に護衛あり")
	return result

func snapshot() -> Dictionary:
	return {"states":states.duplicate(true),"rules":rules.duplicate(true),"knowledge":knowledge.duplicate(true),"field":field.duplicate(true),"methods":methods.duplicate(),"phase":phase_index}
