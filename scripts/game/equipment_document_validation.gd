extends RefCounted
## S2内部の全状態検証。進行後保存に元保存を要求しない。
const S1 = preload("res://scripts/game/equipment_save_validation.gd")
const View = preload("res://scripts/game/equipment_state_view.gd")
const Migration = preload("res://scripts/game/equipment_save_migration.gd")
const Rules = preload("res://scripts/game/equipment_rules.gd")
const METRICS = ["version","source","source_changed","active_ms","elapsed_ms","idle_ms","pause_ms","chapters","counters","answers","events","completed"]
const WORLD = ["location","player_cell","quest_step","section"]

static func context_errors(context: Dictionary) -> Array:
	if not context.get("legacy_session") is GameSession:return [S1.error("context.legacy_session","invalid_context")]
	if not context.get("abilities") is Dictionary:return [S1.error("context.abilities","invalid_catalog")]
	if not context.abilities.has("two_handed"):return [S1.error("context.abilities.two_handed","unknown_ability")]
	var real: Dictionary=context.legacy_session.catalog.equipment_context_abilities()
	if real.is_empty() or not S1.differences(real,context.abilities).is_empty():return [S1.error("context.abilities","invalid_catalog")]
	return S1.context_errors(context)

static func shape(value: Variant, keys: Array, path: String, errors: Array) -> bool:
	if not value is Dictionary:
		errors.append(S1.error(path,"invalid_shape"))
		return false
	S1.fields(value,keys,path,errors)
	return true

static func auxiliary(document: Dictionary) -> Array:
	var errors := S1.values(document)
	if not errors.is_empty():return errors
	if document.has("_trial_id") and (not document._trial_id is String or not PlaythroughArchive.valid_id(document._trial_id)):
		errors.append(S1.error("$._trial_id","invalid_record_id"))
	if document.has("_play_session"):
		var metrics: Variant = document._play_session
		if not shape(metrics,METRICS,"$._play_session",errors):return errors
		var time_total := 0
		for key in ["active_ms","idle_ms","pause_ms"]:
			var amount: Variant=metrics.get(key,0)
			if not (amount is int or amount is float) or not is_finite(float(amount)) or amount<0 or amount!=floor(float(amount)) or (amount is float and amount>=9223372036854775808.0):return [S1.error("$._play_session."+key,"invalid_metrics")]
			if time_total>9223372036854775807-int(amount):return [S1.error("$._play_session","numeric_overflow")]
			time_total+=int(amount)
		if metrics.get("chapters") is Dictionary:
			for key in ["active_ms","elapsed_ms"]:
				var total := 0
				for chapter in metrics.chapters.values():
					if chapter is Dictionary:
						var amount: Variant=chapter.get(key,0)
						if not (amount is int or amount is float) or not is_finite(float(amount)) or amount<0 or amount!=floor(float(amount)) or (amount is float and amount>=9223372036854775808.0):return [S1.error("$._play_session.chapters","invalid_metrics")]
						if total>9223372036854775807-int(amount):return [S1.error("$._play_session.chapters","numeric_overflow")]
						total+=int(amount)
		if not PlaySessionMetrics.new().restore(metrics):
			errors.append(S1.error("$._play_session","invalid_metrics"))
			return errors
		for key in metrics.get("chapters",{}):
			shape(metrics.chapters[key],["active_ms","elapsed_ms"],"$._play_session.chapters."+key,errors)
		for key in ["answers","events"]:
			for index in range(metrics.get(key,[]).size()):
				shape(metrics[key][index],["chapter","active_ms","exploration","reward","difficulty","note","self_reported"] if key=="answers" else ["kind","chapter","elapsed_ms","details"],"$._play_session.%s[%d]" % [key,index],errors)
		# restoreの検証を利用するが、履歴detailsの正規化結果で原値を置換しない。
	return errors

static func schema(document: Dictionary, equipment: bool) -> Array:
	var errors := auxiliary(document)
	S1.fields(document,S1.ROOT+S1.NEW_ROOT if equipment else S1.ROOT,"$",errors)
	var schemas := {"world":WORLD,"return_point":WORLD,"story_task":["id","step"],"story_battle":["step","cleared"],"expedition":["id","stage","wave","origin","solved"],"integrated":["knowledge","outcomes","claimed","job_notes","mastery_rules_version"]+([] if equipment else ["armory"]),"first_region":["version","reserve","coins","errands","travel"]}
	for key in schemas:
		if document.has(key):shape(document[key],schemas[key],"$."+key,errors)
	if equipment and document.has("equipment_stock"):shape(document.equipment_stock,["instances","bag"],"$.equipment_stock",errors)
	if not errors.is_empty():return errors
	if document.has("expedition") and document.expedition.has("origin"):shape(document.expedition.origin,WORLD,"$.expedition.origin",errors)
	if document.has("first_region") and document.first_region.has("travel"):shape(document.first_region.travel,["version","visited","return_learned","ship_owned","ship_cell"],"$.first_region.travel",errors)
	if document.has("overworld"):
		shape(document.overworld,["active","origin","layer","cell","world_cell","transport","node","room","flags","seen","cleared","choices","visited","facing","opened","entry_lock","residents"],"$.overworld",errors)
		if document.overworld is Dictionary and document.overworld.has("residents"):
			if document.overworld.residents is Dictionary:
				for key in document.overworld.residents:shape(document.overworld.residents[key],["cell","facing"],"$.overworld.residents."+str(key),errors)
			else:errors.append(S1.error("$.overworld.residents","invalid_shape"))
	if not errors.is_empty():return errors
	if not document.get("party") is Array or document.party.size()<(1 if document.has("first_region") else 3) or document.party.size()>4:return [S1.error("$.party","invalid_state")]
	if not document.get("inventory") is Dictionary:return [S1.error("$.inventory","invalid_state")]
	var view := View.project(document)
	if not view.ok:return view.errors
	for group in ["party","reserve"]:
		var people: Array = view.view.party if group=="party" else view.view.first_region.reserve
		for index in range(people.size()):
			var actor: Variant = people[index]
			var path := "$.party[%d]" % index if group=="party" else "$.first_region.reserve[%d]" % index
			if not shape(actor,S1.ACTOR+(["equipment"] if equipment else []),path,errors):continue
			if actor.has("integrated"):
				if shape(actor.integrated,S1.OWN.filter(func(key):return not equipment or key!="weapons"),path+".integrated",errors) and actor.integrated.has("mastery"):
					shape(actor.integrated.mastery,["counts","legacy_masters"],path+".integrated.mastery",errors)
	for key in ["knowledge","outcomes"]:
		var data: Variant = document.get("integrated",{}).get(key,{})
		if not data is Dictionary:errors.append(S1.error("$.integrated."+key,"invalid_shape"))
		else:
			for identifier in data:shape(data[identifier],["facts","confirmed"] if key=="knowledge" else ["rule","methods"],"$.integrated."+key+"."+str(identifier),errors)
	return errors

static func validate(document: Dictionary, context: Dictionary) -> Array:
	var errors := context_errors(context)
	if not errors.is_empty():return errors
	errors = schema(document,true)
	if not errors.is_empty():return errors
	if not document.get("format_version") is int or document.format_version!=2 or not document.get("equipment_rules_version") is int or document.equipment_rules_version!=1:
		return [S1.error("$.equipment_rules_version","unsupported_version")]
	errors = S1.equipment_layer(document,context)
	if not errors.is_empty():return errors
	var session: GameSession = context.legacy_session
	var explicit := {"document":document,"abilities":context.abilities}
	if not session.validate_state_common(document,explicit):return [S1.error("$","invalid_state")]
	var ids: Array = []
	for group in ["party","reserve"]:
		var people: Array = document.party if group=="party" else document.get("first_region",{}).get("reserve",[])
		for index in range(people.size()):
			var actor: Dictionary = people[index]
			var path := "$.party[%d]" % index if group=="party" else "$.first_region.reserve[%d]" % index
			if actor.id in ids or not session.validate_actor_common(actor,2,document.integrated,document.progress_flags,explicit):
				return [S1.error(path,"invalid_reserve" if group=="reserve" else "invalid_actor")]
			if "two_handed" in actor.learned_abilities and "warrior" not in actor.mastered_jobs:return [S1.error(path+".learned_abilities","invalid_actor")]
			ids.append(actor.id)
	return audit_errors(document,context)

static func audit_errors(document: Dictionary, context: Dictionary) -> Array:
	var errors: Array = []
	var m: Variant = document.get("equipment_migration")
	var g: Variant = document.get("equipment_grants")
	if not shape(m,["version","migration_id","source_sha256","source_format","policy_id","catalog_revision","source_build","source_build_reason","legacy_format_audit","equipment_audit"],"$.equipment_migration",errors) or not shape(g,["version","policy_id","common_set","actor_initial","actor_support"],"$.equipment_grants",errors):return errors
	if not errors.is_empty():return errors
	if not m.has_all(["version","migration_id","source_sha256","source_format","policy_id","catalog_revision","source_build","source_build_reason","legacy_format_audit","equipment_audit"]) or not g.has_all(["version","policy_id","common_set","actor_initial","actor_support"]):return [S1.error("$.equipment_migration","invalid_audit")]
	if not m.version is int or m.version!=1 or not m.source_format is int or m.source_format not in [1,2] or not m.catalog_revision is int or m.catalog_revision!=1 or m.policy_id!=Migration.POLICY or not m.source_sha256 is String or m.source_sha256.length()!=64 or not m.source_sha256.is_valid_hex_number(false) or m.source_sha256!=m.source_sha256.to_lower() or m.migration_id!=Migration.migration_id(m.source_sha256) or not m.source_build is String or m.source_build_reason!=("unknown" if m.source_build.is_empty() else "provided"):
		return [S1.error("$.equipment_migration","invalid_audit")]
	if not g.version is int or g.version!=1 or g.policy_id!=Migration.POLICY or g.common_set not in ["pending","granted"] or not g.actor_initial is Dictionary or not g.actor_initial.is_empty() or not g.actor_support is Dictionary:
		return [S1.error("$.equipment_grants","invalid_grants")]
	var unlocked: bool = not document.has("first_region") or document.progress_flags.get("job_change_unlocked",false)
	if (g.common_set=="granted")!=unlocked:return [S1.error("$.equipment_grants.common_set","invalid_grants")]
	var a: Variant=m.equipment_audit
	var legacy: Variant=m.legacy_format_audit
	if not shape(a,["source_armory","actor_slots","generated","returned","learned_added"],"$.equipment_migration.equipment_audit",errors) or not shape(legacy,["source_format","target_format","actors","world_created","mastery_initialized"],"$.equipment_migration.legacy_format_audit",errors):return errors
	if not a.has_all(["source_armory","actor_slots","generated","returned","learned_added"]) or not legacy.has_all(["source_format","target_format","actors","world_created","mastery_initialized"]):return [S1.error("$.equipment_migration","invalid_audit")]
	for key in ["source_armory","actor_slots","generated","returned","learned_added"]:
		if not a[key] is Array:return [S1.error("$.equipment_migration.equipment_audit."+key,"invalid_audit")]
	if legacy.source_format!=m.source_format or legacy.target_format!=2 or not legacy.actors is Array or not legacy.mastery_initialized is Array or not legacy.world_created is Dictionary:return [S1.error("$.equipment_migration.legacy_format_audit","invalid_audit")]
	# 元保存がない場合は台帳の完全性と内部会計を検証する。元との差分保証とは別。
	var generated: Dictionary={}
	var common: Array=[]
	var support: Dictionary={}
	var catalog := Rules.new().catalog()
	for index in range(a.generated.size()):
		var entry: Variant=a.generated[index]
		if not shape(entry,["instance_id","item_id","reason","actor_id"],"$.equipment_migration.equipment_audit.generated[%d]" % index,errors):return errors
		if not entry.has_all(["instance_id","item_id","reason","actor_id"]) or entry.instance_id!="eqm_%s_%06d" % [m.migration_id,index+1] or not entry.item_id is String or not catalog.has(entry.item_id) or not entry.actor_id is String or entry.reason not in ["legacy_slot","legacy_unheld","format1_supply","migration_support","common_set"]:
			return [S1.error("$.equipment_migration.equipment_audit.generated[%d]" % index,"invalid_audit")]
		if not document.equipment_stock.instances.has(entry.instance_id) or document.equipment_stock.instances[entry.instance_id]!=entry.item_id:return [S1.error("$.equipment_stock.instances."+entry.instance_id,"invalid_audit")]
		generated[entry.instance_id]=entry
		if entry.reason=="common_set":
			if not entry.actor_id.is_empty():return [S1.error("$.equipment_migration.equipment_audit.generated","invalid_audit")]
			common.append(entry.item_id)
		if entry.reason=="migration_support":
			if not support.has(entry.actor_id):support[entry.actor_id]=[]
			support[entry.actor_id].append({"reason":entry.reason,"item_id":entry.item_id,"instance_id":entry.instance_id})
	if common!=(Migration.COMMON if g.common_set=="granted" else []):return [S1.error("$.equipment_grants.common_set","invalid_grants")]
	var old_ids: Array=[]
	var old_items: Array=[]
	var slot_instances: Array=[]
	for entry in a.actor_slots:
		if not shape(entry,["actor_id","group","index","weapons","instances"],"$.equipment_migration.equipment_audit.actor_slots",errors):return errors
		if not entry.has_all(["actor_id","group","index","weapons","instances"]) or not entry.actor_id is String or entry.actor_id.is_empty() or entry.actor_id in old_ids or entry.group not in ["party","reserve"] or not entry.index is int or entry.index<0 or not entry.weapons is Array or not entry.instances is Array:return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
		old_ids.append(entry.actor_id)
		var supplied: Array=entry.weapons if m.source_format==2 else ["practice_blade"]
		if entry.instances.size()!=supplied.size() or (m.source_format==1 and not entry.weapons.is_empty()) or (m.source_format==2 and (supplied.is_empty() or supplied.size()>2)):return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
		for index in range(supplied.size()):
			var id: Variant=entry.instances[index]
			if not id is String or id in slot_instances or not generated.has(id) or generated[id].item_id!=supplied[index] or generated[id].actor_id!=entry.actor_id or generated[id].reason!=("legacy_slot" if m.source_format==2 else "format1_supply"):return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
			slot_instances.append(id)
			old_items.append(supplied[index])
		if not g.actor_support.has(entry.actor_id) or not S1.differences(g.actor_support[entry.actor_id],support.get(entry.actor_id,[])).is_empty():return [S1.error("$.equipment_grants.actor_support."+entry.actor_id,"invalid_grants")]
	var sorted_ids := old_ids.duplicate();sorted_ids.sort()
	if old_ids!=sorted_ids:return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
	var positions: Dictionary={"party":[],"reserve":[]}
	for slot in a.actor_slots:
		if slot.index in positions[slot.group]:return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
		positions[slot.group].append(slot.index)
	for group in positions:
		positions[group].sort()
		if positions[group]!=range(positions[group].size()):return [S1.error("$.equipment_migration.equipment_audit.actor_slots","invalid_audit")]
	for entry in a.generated:
		if entry.reason=="legacy_slot" or (entry.reason=="format1_supply" and not entry.actor_id.is_empty()):
			if entry.instance_id not in slot_instances:return [S1.error("$.equipment_migration.equipment_audit.generated","invalid_audit")]
		elif entry.reason in ["migration_support"]:
			if entry.actor_id not in old_ids or entry.item_id not in Migration.START_WEAPONS+Migration.ARMORS:return [S1.error("$.equipment_migration.equipment_audit.generated","invalid_audit")]
		elif entry.reason=="legacy_unheld" and (m.source_format!=2 or not entry.actor_id.is_empty()):return [S1.error("$.equipment_migration.equipment_audit.generated","invalid_audit")]
	if document.equipment_stock.instances.size()!=generated.size():return [S1.error("$.equipment_stock.instances","invalid_audit")]
	if old_ids.is_empty() or g.actor_support.size()!=old_ids.size():return [S1.error("$.equipment_grants.actor_support","invalid_grants")]
	var releases: Array=[]
	for item in a.source_armory:
		if not item is String or IntegratedProgression.weapon(item).is_empty() or item in releases:return [S1.error("$.equipment_migration.equipment_audit.source_armory","invalid_audit")]
		releases.append(item)
	if m.source_format==2:
		for item in old_items:
			if item not in releases:return [S1.error("$.equipment_migration.equipment_audit.source_armory","invalid_audit")]
		for item in old_items:releases.erase(item)
	else:
		if not releases.is_empty():return [S1.error("$.equipment_migration.equipment_audit.source_armory","invalid_audit")]
		releases=["practice_staff","practice_bow"]
	var actual_releases: Array=[]
	for entry in a.generated:
		if entry.reason in ["legacy_unheld","format1_supply"] and entry.actor_id.is_empty():actual_releases.append(entry.item_id)
	actual_releases.sort();releases.sort()
	if actual_releases!=releases:return [S1.error("$.equipment_migration.equipment_audit.generated","invalid_audit")]
	for key in ["returned","learned_added"]:
		var seen: Array=[]
		for entry in a[key]:
			if not shape(entry,["actor_id","ability_id","reason"] if key=="learned_added" else ["instance_id","item_id","actor_id","slot","index"],"$.equipment_migration.equipment_audit."+key,errors):return errors
			if key=="learned_added":
				if not entry.has_all(["actor_id","ability_id","reason"]) or entry.actor_id not in old_ids or entry.actor_id in seen or entry.ability_id!="two_handed" or entry.reason!="warrior_master":return [S1.error("$.equipment_migration.equipment_audit."+key,"invalid_audit")]
				seen.append(entry.actor_id)
			else:
				if not entry.has_all(["instance_id","item_id","actor_id","slot","index"]) or not entry.instance_id is String or not generated.has(entry.instance_id) or entry.instance_id in seen or generated[entry.instance_id].actor_id!=entry.actor_id or generated[entry.instance_id].item_id!=entry.item_id or entry.slot!="weapon" or not entry.index is int or entry.index<0 or entry.index>1:return [S1.error("$.equipment_migration.equipment_audit."+key,"invalid_audit")]
				seen.append(entry.instance_id)
	var legacy_ids: Array=[]
	for entry in legacy.actors:
		if not shape(entry,["actor_id","group","index","jp_before","jp_after","integrated_created"],"$.equipment_migration.legacy_format_audit.actors",errors):return errors
		if not entry.has_all(["actor_id","group","index","jp_before","jp_after","integrated_created"]) or entry.actor_id not in old_ids or not entry.jp_before is Dictionary or not entry.jp_after is Dictionary or not entry.integrated_created is Dictionary:return [S1.error("$.equipment_migration.legacy_format_audit.actors","invalid_audit")]

		if entry.actor_id in legacy_ids or not entry.index is int or entry.group not in ["party","reserve"]:return [S1.error("$.equipment_migration.legacy_format_audit.actors","invalid_audit")]
		legacy_ids.append(entry.actor_id)
		var slots: Array=a.actor_slots.filter(func(slot):return slot.actor_id==entry.actor_id)
		if slots.is_empty() or slots[0].index!=entry.index or slots[0].group!=entry.group:return [S1.error("$.equipment_migration.legacy_format_audit.actors","invalid_audit")]
		if not shape(entry.integrated_created,S1.OWN,"$.equipment_migration.legacy_format_audit.actors.integrated_created",errors):return errors
		var mastery: Variant=entry.integrated_created.get("mastery")
		if not mastery is Dictionary or not shape(mastery,["counts","legacy_masters"],"$.equipment_migration.legacy_format_audit.actors.mastery",errors) or not mastery.get("legacy_masters") is Array or mastery.get("counts")!={}:return [S1.error("$.equipment_migration.legacy_format_audit.actors","invalid_audit")]
		var jp: Dictionary={}
		for identifier in entry.jp_before:
			if not context.legacy_session.jobs.has(identifier) or not entry.jp_before[identifier] is int or entry.jp_before[identifier]<0:return [S1.error("$.equipment_migration.legacy_format_audit.actors.jp_before","invalid_audit")]
			var job: Dictionary=context.legacy_session.jobs[identifier]
			var converted := float(entry.jp_before[identifier])*float(IntegratedProgression.cost(job,true))/float(IntegratedProgression.cost(job,false))
			if not is_finite(converted) or converted>=9223372036854775808.0:return [S1.error("$.equipment_migration.legacy_format_audit.actors.jp_before","numeric_overflow")]
			jp[identifier]=floori(converted)
			if identifier in mastery.legacy_masters:jp[identifier]=maxi(jp[identifier],IntegratedProgression.cost(job,true))
		if not S1.differences(jp,entry.jp_after).is_empty():return [S1.error("$.equipment_migration.legacy_format_audit.actors.jp_after","invalid_audit")]
	var initialized_ids: Array=[]
	for entry in legacy.mastery_initialized:
		if not shape(entry,["actor_id","group","index","mastery"],"$.equipment_migration.legacy_format_audit.mastery_initialized",errors):return errors
		if not entry.has_all(["actor_id","group","index","mastery"]) or entry.actor_id not in old_ids or not entry.mastery is Dictionary:return [S1.error("$.equipment_migration.legacy_format_audit.mastery_initialized","invalid_audit")]
		if entry.actor_id in initialized_ids or entry.group not in ["party","reserve"] or not entry.index is int or not shape(entry.mastery,["counts","legacy_masters"],"$.equipment_migration.legacy_format_audit.mastery_initialized.mastery",errors) or entry.mastery.get("counts")!={} or not entry.mastery.get("legacy_masters") is Array:return [S1.error("$.equipment_migration.legacy_format_audit.mastery_initialized","invalid_audit")]
		initialized_ids.append(entry.actor_id)
	if (m.source_format==2 and (not legacy.actors.is_empty() or not legacy.world_created.is_empty())) or (m.source_format==1 and legacy.actors.size()!=old_ids.size()):return [S1.error("$.equipment_migration.legacy_format_audit","invalid_audit")]
	if m.source_format==1 and not S1.differences(legacy.world_created,IntegratedProgression.initial_world()).is_empty():return [S1.error("$.equipment_migration.legacy_format_audit.world_created","invalid_audit")]
	return errors

static func prepare_candidate(candidate: Dictionary, context: Dictionary) -> Dictionary:
	var errors := context_errors(context)
	if errors.is_empty():errors=schema(candidate,true)
	if errors.is_empty():errors=S1.equipment_layer(candidate,context)
	if not errors.is_empty():return {"ok":false,"reason_code":errors[0].reason_code,"errors":errors}
	var document := candidate.duplicate(true)
	var explicit := {"document":document,"abilities":context.abilities,"skip_caps":true}
	if not context.legacy_session.validate_state_common(document,explicit):return {"ok":false,"reason_code":"invalid_state","errors":[S1.error("$","invalid_state")]}
	for actor in document.get("first_region",{}).get("reserve",[]):
		if not context.legacy_session.validate_actor_common(actor,2,document.integrated,document.progress_flags,explicit):return {"ok":false,"reason_code":"invalid_reserve","errors":[S1.error("$.first_region.reserve","invalid_reserve")]}
	var changes: Array=[]
	for actor in document.party+document.get("first_region",{}).get("reserve",[]):
		var stats: Dictionary=context.legacy_session.equipment_stats(actor,document)
		if stats.is_empty():return {"ok":false,"reason_code":"numeric_overflow","errors":[S1.error("actor/"+actor.id,"numeric_overflow")]}
		var before := {"hp":actor.hp,"mp":actor.mp,"max_hp":actor.max_hp,"max_mp":actor.max_mp}
		actor.max_hp=stats.hp;actor.max_mp=stats.mp
		actor.hp=mini(actor.hp,actor.max_hp);actor.mp=mini(actor.mp,actor.max_mp)
		var after := {"hp":actor.hp,"mp":actor.mp,"max_hp":actor.max_hp,"max_mp":actor.max_mp}
		if not S1.differences(before,after).is_empty():changes.append({"actor_id":actor.id,"before":before,"after":after})
	if document.has("_saved_value_types"):
		document.erase("_saved_value_types")
		document["_saved_value_types"]=SavedValueTypes.describe(document)
	errors=validate(document,context)
	if not errors.is_empty():return {"ok":false,"reason_code":errors[0].reason_code,"errors":errors}
	return {"ok":true,"reason_code":"ok","document":document,"caps_changes":changes,"errors":[]}

static func compare_migration(source: Dictionary, candidate: Dictionary, source_sha256: String, context: Dictionary) -> Array:
	var planned := Migration.new().plan(source,source_sha256,context)
	if not planned.ok:return planned.errors
	var prepared := prepare_candidate(planned.candidate_document,context)
	if not prepared.ok:return prepared.errors
	return S1.differences(prepared.document,candidate)
