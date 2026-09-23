extends SceneTree
var failures: Array[String]=[]
var cases:=0
func check(value: bool,message: String) -> void:
	if not value:failures.append(message)
func make_battle(rule: String="", enemy_hp: int=2000) -> BattleState:
	var catalog:=BattleCatalog.new()
	var party: Array[Combatant]=[]
	for i in range(4):
		var actor:=Combatant.new("pc_%02d" % (i+1),"検査用の仲間",Combatant.Team.PARTY,{"hp":1000,"mp":100,"attack":50,"defense":8,"magic":20,"resistance":8,"speed":100-i})
		actor.learned.assign(catalog.abilities.keys())
		actor.equipped.assign(catalog.abilities.keys())
		party.append(actor)
	var foe:=Combatant.new("enemy_01","検査用の相手",Combatant.Team.ENEMY,{"hp":enemy_hp,"mp":0,"attack":0,"defense":60,"magic":0,"resistance":20,"speed":1})
	var enemies: Array[Combatant]=[foe]
	var b:=BattleState.new(party,enemies,catalog,41)
	for entry in catalog.integration["enemy_rules"]:
		if entry["id"]==rule:b.effects.configure(entry,{})
	return b
func skill(b: BattleState, actor: String,id: String,target: String="enemy_01") -> void:
	check(b.queue_action(BattleAction.skill(actor,target,id)).is_empty(),"有効な新技を予約: "+id)
func run_round(b: BattleState) -> Array[Dictionary]:
	for actor in b.pending():check(b.queue_action(BattleAction.guard(actor.id)).is_empty(),"残る仲間が防御を予約")
	return b.resolve_round()
func damage_by(events: Array, actor: String) -> int:
	var result:=0
	for event in events:
		if event["code"]=="damage" and event["actor"]==actor:result+=int(event["amount"])
	return result
func _initialize() -> void:
	var b:=make_battle("conductor")
	skill(b,"pc_01","conduct","pc_04");skill(b,"pc_02","amplify","pc_04");skill(b,"pc_03","cover","pc_04");skill(b,"pc_04","four_strike")
	var before:=b.snapshot()
	var rng_before:=b._rng.state
	var preview:=b.preview_action(BattleAction.skill("pc_04","enemy_01","four_strike"))
	check(b.snapshot()==before and b._rng.state==rng_before,"予測で状態・乱数を進めない")
	check(preview["predicted_damage"]==-1,"未確認の敵規則の解答を予測で公開しない")
	var events:=run_round(b)
	check(damage_by(events,"pc_04")==336,"現行基礎式で導電＋増幅＋四連撃は336")
	check(b.actor_by_id("pc_04").mp==94 and b.actor_by_id("pc_01").mp==96 and b.actor_by_id("pc_02").mp==94,"打数分のMPを消費しない")
	check(not b.effects.state("pc_04").has("conduct") and not b.effects.state("pc_04").has("amplifier"),"攻撃1行動で両付与を消費")
	check(b.effects.knowledge["conductor"]["confirmed"],"作用した規則を確認済みにする")
	cases+=1
	b=make_battle()
	b.actor_by_id("pc_04").focus_binding="four_strike"
	skill(b,"pc_04","focus_vow","pc_04");run_round(b)
	skill(b,"pc_01","amplify","pc_04");skill(b,"pc_04","four_strike")
	events=run_round(b)
	check(damage_by(events,"pc_04")==280,"専心100%と通常増幅50%は加算2.5倍")
	check(not b.effects.state("pc_04").get("focused",false),"専心は攻撃後に残らない")
	cases+=1
	b=make_battle()
	skill(b,"pc_01","overdrive","pc_04");skill(b,"pc_04","four_strike");run_round(b)
	check(not b.queue_action(BattleAction.strike("pc_04","enemy_01")).is_empty(),"過負荷の次の攻撃を拒否")
	check(b.queue_action(BattleAction.observe("pc_04","enemy_01")).is_empty(),"過負荷でも観察を選べる")
	run_round(b)
	check(b.queue_action(BattleAction.strike("pc_04","enemy_01")).is_empty(),"次の本人行動機会を過ぎると攻撃可能")
	cases+=1
	b=make_battle()
	skill(b,"pc_01","amplify","pc_04");skill(b,"pc_02","overdrive","pc_04");run_round(b)
	check(b.actor_by_id("pc_01").mp==94 and b.actor_by_id("pc_02").mp==100,"実行時に重複増幅を拒否して無消費")
	run_round(b)
	check(not b.effects.state("pc_04").has("amplifier"),"未使用付与は2ラウンド目の終了で失効")
	cases+=1
	b=make_battle("charger")
	b.actor_by_id("enemy_01").mp=20
	skill(b,"pc_01","seal");skill(b,"pc_02","seal");events=run_round(b)
	check(b.effects.state("enemy_01").get("seal_used",false) and b.actor_by_id("enemy_01").mp==20,"充填前の加算で中断し敵MPを消費しない")
	for actor in b.pending():b.queue_action(BattleAction.strike(actor.id,"enemy_01"))
	events=run_round(b)
	check(damage_by(events,"pc_01")==100,"崩した相手の防御は0")
	check(not b.queue_action(BattleAction.skill("pc_01","enemy_01","seal")).is_empty(),"同じ敵を再び完全に崩さない")
	cases+=1
	b=make_battle()
	skill(b,"pc_01","reflect_field","pc_01");run_round(b)
	b.actor_by_id("pc_02").weapons=[{"attack":0,"tags":["projectile"]}]
	b.queue_action(BattleAction.strike("pc_02","enemy_01"));events=run_round(b)
	check(damage_by(events,"pc_02")==20,"有効な反射場は射撃だけ半減")
	var device:=b.actor_by_id("reflection_anchor")
	check(device!=null and device.is_device and b.living(Combatant.Team.ENEMY).size()==1,"維持装置を敵種や行動者へ数えない")
	for actor in b.pending():b.queue_action(BattleAction.strike(actor.id,"reflection_anchor"))
	run_round(b)
	check(b.effects.field.is_empty(),"維持装置を壊して場を解除")
	cases+=1
	b=make_battle()
	b.actor_by_id("pc_01").weapons=[{"attack":0,"tags":["melee"]},{"attack":-10,"tags":["melee"]}]
	skill(b,"pc_01","four_strike");events=run_round(b)
	check(damage_by(events,"pc_01")==168,"二刀流は異なる武器値で4打ずつ。112＋56")
	check(b.actor_by_id("pc_01").mp==94,"8打でも消費は一度")
	cases+=1
	b=make_battle("residue",10)
	for actor in b.living(Combatant.Team.PARTY):actor.hp=5
	b.queue_action(BattleAction.strike("pc_01","enemy_01"));events=run_round(b)
	check(b.phase==BattleState.Phase.DEFEAT,"最後の敵の残留効果を解決し、同時全滅は全滅")
	check(events.filter(func(e: Dictionary)->bool:return e["code"]=="damage" and e["actor"]=="enemy_01").size()==4,"残留効果は各対象へ一度")
	cases+=1
	b=make_battle("residue",10)
	skill(b,"pc_01","disarm");b.queue_action(BattleAction.strike("pc_02","enemy_01"));run_round(b)
	check(b.phase==BattleState.Phase.VICTORY and b.actor_by_id("pc_04").hp==1000,"残留解除で死亡後の被害を防ぐ")
	cases+=1
	b=make_battle()
	skill(b,"pc_01","recycle","pc_04");skill(b,"pc_04","four_strike");run_round(b)
	check(b.actor_by_id("pc_04").mp==96,"還元は1行動に最大2、打数で増えない")
	cases+=1
	b=make_battle("attrition")
	b.actor_by_id("pc_01").mp=17
	run_round(b);run_round(b)
	check(b.effects.phase_index==1 and b.actor_by_id("pc_01").mp==17,"戦闘の局面切替でMPを回復しない")
	cases+=1
	boundaries()
	var report: Dictionary={"status":"PASS" if failures.is_empty() else "FAIL","cases":cases,"failures":failures,"scope":"実BattleStateでの固定数値・状態遷移。ゲーム全編や人間の面白さの検証とは別。"}
	PlaySessionMetrics.write_json("res://docs/verification/integrated-combat-current.json",report)
	for failure in failures:printerr("INTEGRATED_COMBAT_FAIL: "+failure)
	if failures.is_empty():print("INTEGRATED_COMBAT_PASS: cases=%d" % cases)
	quit(0 if failures.is_empty() else 1)

func boundaries() -> void:
	var b:=make_battle()
	b.actor_by_id("enemy_01").attack=100
	b._enemy_plan_round=1;b._enemy_plan=[BattleAction.strike("enemy_01","pc_04")]
	skill(b,"pc_04","deflect_physical","pc_04");run_round(b)
	check(b.actor_by_id("pc_04").hp==961,"物理偏向は192ダメージを切上げ39に軽減")
	check(not b.effects.state("pc_04").has("deflect"),"偏向は次のラウンドに持ち越さない")
	cases+=1
	b=make_battle();b.actor_by_id("enemy_01").attack=100
	b._enemy_plan_round=1;b._enemy_plan=[BattleAction.strike("enemy_01","pc_04")]
	skill(b,"pc_04","deflect_magic","pc_04");run_round(b)
	check(b.actor_by_id("pc_04").hp==712,"区分が違う偏向は物理192を288へ増加")
	cases+=1
	b=make_battle();var foe:=b.actor_by_id("enemy_01");foe.attack=100;foe.mp=100
	foe.learned.append("four_strike");foe.equipped.append("four_strike")
	b._enemy_plan_round=1;b._enemy_plan=[BattleAction.skill("enemy_01","pc_04","four_strike")]
	skill(b,"pc_01","cover","pc_04");run_round(b)
	check(b.actor_by_id("pc_04").hp==1000 and b.actor_by_id("pc_01").hp==728,"護衛は4打全てを引き受け、各135を68へ軽減")
	cases+=1
	b=make_battle("mixed");foe=b.actor_by_id("enemy_01");foe.mp=100
	skill(b,"pc_01","cover","pc_04");run_round(b)
	check(b._events.filter(func(e:Dictionary)->bool:return e["code"]=="damage" and e["actor"]=="enemy_01").size()==4 and b.effects.state("pc_04")["cover"]["used"]==0,"全体魔法は4人全員が対象で護衛を消費しない")
	cases+=1
	b=make_battle();b.actor_by_id("pc_01").weapons=[{"attack":0,"tags":["melee"],"on_hit":{"kind":"seal"}}]
	skill(b,"pc_01","four_strike");run_round(b)
	check(b.effects.state("enemy_01").get("seal_count")==1,"武器追加封緘は4打でも対象ごとに1回")
	cases+=1
	b=make_battle();foe=b.actor_by_id("enemy_01");foe.mp=100
	foe.learned.append("four_strike");foe.equipped.append("four_strike")
	b._enemy_plan_round=1;b._enemy_plan=[BattleAction.skill("enemy_01","pc_01","four_strike")]
	skill(b,"pc_01","riposte","pc_01")
	var events:=run_round(b)
	check(events.filter(func(e:Dictionary)->bool:return e["code"]=="damage" and e["actor"]=="pc_01").size()==1,"4打への反撃は1回")
	cases+=1
	b=make_battle("attrition");foe=b.actor_by_id("enemy_01");foe.mp=100
	check(b.enemy_intents()[0]["ability"]=="charge_blow","本番の予告で前半は物理行動")
	run_round(b);run_round(b)
	check(b.enemy_intents()[0]["ability"]=="arc_burst","本番の予告で後半は魔法行動へ変わる")
	b=make_battle("reflector");b.actor_by_id("enemy_01").mp=100
	check(b.enemy_intents()[0]["ability"]=="reflect_field","本番の敵行動選択が反射場を準備する")
	run_round(b)
	check(b.effects.field.get("owner")=="enemy_01","敵自身が実際に維持装置を生成する")
	cases+=1
	b=make_battle();b.actor_by_id("pc_01").mp=3
	var before:=b.snapshot()
	check(not b.queue_action(BattleAction.skill("pc_01","enemy_01","four_strike")).is_empty() and before==b.snapshot(),"MP不足の予約は全状態を変えない")
	b.actor_by_id("pc_01").mp=100;b.actor_by_id("pc_01").equipped.erase("four_strike")
	check(not b.queue_action(BattleAction.skill("pc_01","enemy_01","four_strike")).is_empty(),"未装着の新技を拒否")
	cases+=1
	b=make_battle();b.actor_by_id("enemy_01").physical_taken=1.25
	skill(b,"pc_01","four_strike");events=run_round(b)
	check(damage_by(events,"pc_01")==140,"形態の物理弱点1.25倍は4打それぞれに適用")
	b=make_battle();b.actor_by_id("enemy_01").magic_taken=1.25
	skill(b,"pc_01","arc_burst");events=run_round(b)
	check(damage_by(events,"pc_01")==68,"形態の魔法弱点1.25倍は54から切上げ68")
	cases+=1
