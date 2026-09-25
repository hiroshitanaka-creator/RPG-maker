class_name JobMastery
extends RefCounted
## 実績一覧とは独立した、人物別・現在職での修練進捗。
const METRICS := ["physical","magic","multi","revive","steal","heal","guard","status","shot","song","acid","wind","breath_attack"]

static func valid_definition(job: Dictionary, abilities: Dictionary) -> bool:
	var rule: Variant=job.get("mastery_action")
	if not rule is Dictionary or rule.get("metric") not in METRICS:return false
	var n: Variant=rule.get("required")
	if not (n is int or n is float) or float(n)<1 or float(n)!=floor(float(n)):return false
	if not rule.get("description") is String or rule["description"].is_empty():return false
	var skill: Variant=rule.get("training_ability")
	return skill is String and skill in job.get("abilities",[]) and abilities.has(skill) and IntegratedProgression.threshold(job,skill)<int(job["mastery_cost"])

static func active(actor: Dictionary) -> bool:
	var own: Variant=actor.get("integrated",{})
	return own is Dictionary and own.has("mastery")

static func initial(legacy: Array = []) -> Dictionary:
	return {"counts":{},"legacy_masters":legacy.duplicate()}

static func count(actor: Dictionary, job_id: String) -> int:
	return int(actor.get("integrated",{}).get("mastery",{}).get("counts",{}).get(job_id,0))

static func ready(actor: Dictionary, job: Dictionary) -> bool:
	return not active(actor) or job["id"] in actor["integrated"]["mastery"]["legacy_masters"] or count(actor,job["id"])>=int(job["mastery_action"]["required"])

static func valid(actor: Dictionary, jobs: Dictionary) -> bool:
	if not active(actor):return true
	var own: Variant=actor["integrated"]["mastery"]
	if not own is Dictionary or not own.get("counts") is Dictionary or not own.get("legacy_masters") is Array:return false
	for id in own["counts"]:
		if not id is String or not jobs.has(id) or not own["counts"][id] is int or own["counts"][id]<0 or own["counts"][id]>int(jobs[id]["mastery_action"]["required"]):return false
	var seen: Array=[]
	for id in own["legacy_masters"]:
		if id not in actor["mastered_jobs"] or id in seen:return false
		seen.append(id)
	for id in actor["mastered_jobs"]:
		if not ready(actor,jobs[id]):return false
	return true

static func matches(metric: String, code: String, ability: Dictionary, amount: int) -> bool:
	match metric:
		"physical":return code=="damage" and amount>0 and ability.get("kind","physical")=="physical"
		"magic":return code=="damage" and amount>0 and ability.get("kind")=="magic"
		"multi":return code=="damage" and amount>0 and int(ability.get("hits",1))>1
		"revive","steal":return code==metric and amount>0
		"heal":return code=="heal" and amount>0
		"guard":return code=="guard" or (code=="effect" and ability.get("kind") in ["deflect_physical","deflect_magic"])
		"status":return code in ["status_applied","seal_break"]
		"shot":return code=="damage" and amount>0 and ability.get("id") in ["quick_shot","ice_arrow"]
		"song":return code in ["damage","heal"] and amount>0 and ability.get("id") in ["sound_wave","soothing_song"]
		"acid","wind","breath_attack":
			return code=="damage" and amount>0 and ability.get("id")=={"acid":"acid","wind":"wind_blade","breath_attack":"flame_breath"}[metric]
	return false
