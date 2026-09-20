class_name WorldMapGraphAudit
extends RefCounted
## 座標を持たないグラフの有限状態検査。ゲーム本体の戦闘や地形は対象外。

var source: Dictionary
var nodes: Array
var flags: Array
var edges: Array
var node_index: Dictionary = {}
var flag_index: Dictionary = {}
var transports: Dictionary = {}
var errors: Array = []
var warnings: Array = []
var mode_sets: Array = []
var transitions: Dictionary = {}
var reverse: Dictionary = {}
var rejected: Array = []
var initial_mask := 0

static func audit(data: Dictionary) -> Dictionary:
	var checker := WorldMapGraphAudit.new()
	return checker.run(data)

func error(code: String, detail: Variant) -> void:
	errors.append({"code": code, "detail": detail})

func number(value: Variant, minimum: int) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == floor(float(value)) and value >= minimum

func index_items(value: Variant, label: String) -> Dictionary:
	var result: Dictionary = {}
	if not value is Array:
		error("schema", label + ": 配列が必要")
		return result
	for i in range(value.size()):
		var item: Variant = value[i]
		if not item is Dictionary or not item.get("id") is String or str(item.get("id", "")).is_empty():
			error("schema", label + ": IDを持つ辞書が必要")
			continue
		if result.has(item["id"]):
			error("schema", label + ": ID重複 " + item["id"])
		result[item["id"]] = i
	return result

func references(value: Variant, index: Dictionary, label: String) -> void:
	if not value is Array:
		error("schema", label + ": 配列が必要")
		return
	var seen: Dictionary = {}
	for id in value:
		if not id is String or not index.has(id) or seen.has(id):
			error("schema", label + ": 未定義または重複参照 " + str(id))
		seen[id] = true

func validate(data: Dictionary) -> bool:
	node_index = index_items(data.get("nodes"), "拠点")
	flag_index = index_items(data.get("flags"), "フラグ")
	var transport_index := index_items(data.get("transports"), "移動手段")
	index_items(data.get("edges"), "接続")
	if not errors.is_empty():
		return false
	nodes = data["nodes"]
	flags = data["flags"]
	edges = data["edges"]
	if nodes.is_empty() or flags.size() > 12 or nodes.size() * (1 << flags.size()) > 200000:
		error("state_space_limit", "空グラフまたは全列挙の上限超過。サンプリングで代用しない")
		return false
	for endpoint in ["start_node", "completion_node"]:
		if not node_index.has(data.get(endpoint)):
			error("schema", endpoint + ": 未定義")
	var stages: Array = []
	for transport in data["transports"]:
		var stage: Variant = transport.get("stage")
		if not number(stage, 0):
			error("schema", "移動段階は重複のない非負整数")
		else:
			if int(stage) in stages:
				error("schema", "移動段階は重複のない非負整数")
			stages.append(int(stage))
		references(transport.get("unlock_flags"), flag_index, "乗り物の解放")
		references(transport.get("retains"), transport_index, "保持する移動手段")
		transports[transport["id"]] = transport
	if stages.size() != 3 or not stages.has(0) or not stages.has(1) or not stages.has(2):
		error("schema", "移動段階は0・1・2")
	for node in nodes:
		if not transports.has(node.get("required_transport")):
			error("schema", "拠点の移動手段が未定義")
		references(node.get("unlock_flags"), flag_index, "拠点の解放")
		if not number(node.get("progression_index"), 1) or not number(node.get("recommended_level"), 1):
			error("schema", "進行順・推奨レベルは正整数")
	for flag in flags:
		if not node_index.has(flag.get("producer_node")) or not flag.get("initial") is bool:
			error("schema", "フラグの設定元または初期値が不正")
		if flag.get("persistent") != true or flag.get("consumable") != false:
			error("unsupported_transition", "フラグ消費・解除はこの有限状態モデルに未定義")
		references(flag.get("requires"), flag_index, "フラグの前提")
	for edge in edges:
		if not node_index.has(edge.get("from")) or not node_index.has(edge.get("to")) or not transports.has(edge.get("required_transport")) or not edge.get("one_way") is bool:
			error("schema", "接続の端点・移動手段・方向が不正")
		references(edge.get("unlock_flags"), flag_index, "接続の解放")
	if not errors.is_empty():
		return false
	for transport in transports.values():
		for retained in transport["retains"]:
			if transports[retained]["stage"] >= transport["stage"]:
				error("schema", "保持できるのは既に解放した下位の移動手段")
	return errors.is_empty()

func held(ids: Array, mask: int) -> bool:
	for id in ids:
		if (mask & (1 << int(flag_index[id]))) == 0:
			return false
	return true

func modes(mask: int) -> Dictionary:
	var available: Dictionary = {}
	for transport in transports.values():
		if held(transport["unlock_flags"], mask):
			available[transport["id"]] = true
	var previous := -1
	while available.size() != previous:
		previous = available.size()
		for id in available.keys():
			for retained in transports[id]["retains"]:
				available[retained] = true
	return available

func open_node(index: int, mask: int) -> bool:
	var node: Dictionary = nodes[index]
	return held(node["unlock_flags"], mask) and mode_sets[mask].has(node["required_transport"])

func moves(index: int, mask: int) -> Array:
	var result: Array = []
	if not open_node(index, mask):
		return result
	var id: String = nodes[index]["id"]
	for edge in edges:
		if not held(edge["unlock_flags"], mask) or not mode_sets[mask].has(edge["required_transport"]):
			continue
		var other := ""
		if edge["from"] == id:
			other = edge["to"]
		elif not edge["one_way"] and edge["to"] == id:
			other = edge["from"]
		if not other.is_empty() and open_node(node_index[other], mask):
			result.append({"node": node_index[other], "edge": edge["id"]})
	return result

func flood(start: int, adjacency: Dictionary) -> Dictionary:
	var seen: Dictionary = {start: -1}
	var queue: Array = [start]
	var at := 0
	while at < queue.size():
		var current: int = queue[at]
		at += 1
		for target in adjacency.get(current, []):
			if not seen.has(target):
				seen[target] = current
				queue.append(target)
	return seen

func walking_reach(start: int, mask: int) -> Array:
	if not open_node(start, mask):
		return []
	var adjacency: Dictionary = {}
	for index in range(nodes.size()):
		adjacency[index] = []
		for move in moves(index, mask):
			adjacency[index].append(move["node"])
	var found := flood(start, adjacency).keys()
	found.sort()
	return found

func state_id(index: int, mask: int) -> int:
	return mask * nodes.size() + index

func describe(state: int) -> Dictionary:
	var index := state % nodes.size()
	var mask: int = state / nodes.size()
	var active: Array = []
	for i in range(flags.size()):
		if mask & (1 << i):
			active.append(flags[i]["id"])
	return {"node": nodes[index]["id"], "mask": mask, "flags": active, "available_transports": mode_sets[mask].keys()}

func add_transition(start: int, finish: int) -> void:
	if finish not in transitions[start]:
		transitions[start].append(finish)
		reverse[finish].append(start)

func make_states() -> void:
	for mask in range(1 << flags.size()):
		mode_sets.append(modes(mask))
	for mask in range(mode_sets.size()):
		for i in range(nodes.size()):
			var state := state_id(i, mask)
			if open_node(i, mask):
				transitions[state] = []
				reverse[state] = []
			else:
				rejected.append(describe(state))
	for state in transitions:
		var index: int = state % nodes.size()
		var mask: int = state / nodes.size()
		for move in moves(index, mask):
			add_transition(state, state_id(move["node"], mask))
		for f in range(flags.size()):
			var flag: Dictionary = flags[f]
			if (mask & (1 << f)) == 0 and flag["producer_node"] == nodes[index]["id"] and held(flag["requires"], mask):
				add_transition(state, state_id(index, mask | (1 << f)))

func flag_dependencies() -> Dictionary:
	var deps: Dictionary = {}
	var all_flags := (1 << flags.size()) - 1
	var start: int = node_index[source["start_node"]]
	var unrestricted := walking_reach(start, all_flags)
	for flag in flags:
		var required: Array = flag["requires"].duplicate()
		var producer: Dictionary = nodes[node_index[flag["producer_node"]]]
		for id in producer["unlock_flags"] + transports[producer["required_transport"]]["unlock_flags"]:
			if id not in required:
				required.append(id)
		# 全フラグ有効でも届かない場所を、全フラグへの依存と誤診しない。
		if node_index[flag["producer_node"]] in unrestricted:
			for id in flag_index:
				var without: int = all_flags & ~(1 << int(flag_index[id]))
				if node_index[flag["producer_node"]] not in walking_reach(start, without) and id not in required:
					required.append(id)
		required.sort()
		deps[flag["id"]] = required
	return deps

func flag_cycles(deps: Dictionary) -> Array:
	var reach: Dictionary = {}
	for id in deps:
		var seen: Array = []
		var queue: Array = deps[id].duplicate()
		while not queue.is_empty():
			var next: String = queue.pop_back()
			if next in seen:
				continue
			seen.append(next)
			queue.append_array(deps[next])
		reach[id] = seen
	var grouped: Array = []
	var cycles: Array = []
	for id in deps:
		if id in grouped or id not in reach[id]:
			continue
		var group: Array = []
		for other in deps:
			if other in reach[id] and id in reach[other]:
				group.append(other)
		group.sort()
		grouped.append_array(group)
		cycles.append(group)
	return cycles

func completion_mask() -> int:
	var node: Dictionary = nodes[node_index[source["completion_node"]]]
	var required: Array = node["unlock_flags"].duplicate()
	required.append_array(transports[node["required_transport"]]["unlock_flags"])
	var mask := 0
	while not required.is_empty():
		var id: String = required.pop_back()
		var bit: int = 1 << int(flag_index[id])
		if mask & bit:
			continue
		mask |= bit
		required.append_array(flags[flag_index[id]]["requires"])
	return mask

func historical_consistency(mask: int) -> bool:
	for f in range(flags.size()):
		if mask & (1 << f) and not held(flags[f]["requires"], mask):
			return false
	return true

func witness(state: int, parents: Dictionary) -> Array:
	var path: Array = []
	if not parents.has(state):
		return path
	var current := state
	while current >= 0:
		path.push_front(describe(current))
		current = parents[current]
	return path

func recovery_witness(state: int, winning: Dictionary) -> Array:
	var path: Array = []
	var current := state
	while current >= 0 and winning.has(current):
		path.append(describe(current))
		current = winning[current]
	return path

func run(data: Dictionary) -> Dictionary:
	source = data
	if not validate(data):
		return {"status": "FAIL", "errors": errors, "warnings": warnings, "scope": "abstract_graph"}
	var ordered: Array = nodes.duplicate()
	ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["progression_index"] < b["progression_index"])
	var previous_level := 0
	var monotonic_violations: Array = []
	for i in range(ordered.size()):
		if ordered[i]["progression_index"] != i + 1 or ordered[i]["recommended_level"] < previous_level:
			monotonic_violations.append(ordered[i]["id"])
		previous_level = int(ordered[i]["recommended_level"])
	if not monotonic_violations.is_empty():
		error("progression_order", monotonic_violations)
	for i in range(flags.size()):
		if flags[i]["initial"]:
			initial_mask |= 1 << i
	make_states()
	var initial := state_id(node_index[data["start_node"]], initial_mask)
	var reachable: Dictionary = {}
	if transitions.has(initial):
		reachable = flood(initial, transitions)
	else:
		error("initial_state_rejected", describe(initial))
	var reached_nodes: Array = []
	for state in reachable:
		var id: String = nodes[int(state) % nodes.size()]["id"]
		if id not in reached_nodes:
			reached_nodes.append(id)
	reached_nodes.sort()
	var unreachable_nodes: Array = []
	for id in node_index:
		if id not in reached_nodes:
			unreachable_nodes.append(id)
	if not unreachable_nodes.is_empty():
		error("unreachable_nodes", unreachable_nodes)
	var deps := flag_dependencies()
	var cycles := flag_cycles(deps)
	if not cycles.is_empty():
		error("flag_cycle", cycles)
	var required_mask := completion_mask()
	var end: int = node_index[data["completion_node"]]
	var winning: Dictionary = {}
	for mask in range(mode_sets.size()):
		var goal := state_id(end, mask)
		if (mask & required_mask) == required_mask and transitions.has(goal):
			winning.merge(flood(goal, reverse))
	var deadlocks: Array = []
	var reachable_deadlocks := 0
	for state in transitions:
		if winning.has(state):
			continue
		var dead := describe(state)
		dead["initially_reachable"] = reachable.has(state)
		dead["witness_from_start"] = witness(state, reachable)
		deadlocks.append(dead)
		if reachable.has(state):
			reachable_deadlocks += 1
	if not deadlocks.is_empty():
		error("deadlock", {"count": deadlocks.size(), "initially_reachable": reachable_deadlocks, "sample": deadlocks[0]})
	var mask_summary: Array = []
	var recovery_witnesses: Array = []
	for mask in range(mode_sets.size()):
		var admissible := 0
		var blocked := 0
		var normal := 0
		for i in range(nodes.size()):
			var state := state_id(i, mask)
			if transitions.has(state):
				admissible += 1
				if not winning.has(state):
					blocked += 1
			if reachable.has(state):
				normal += 1
		mask_summary.append({"mask": mask, "historically_consistent": historical_consistency(mask), "admissible": admissible, "rejected": nodes.size() - admissible, "deadlocks": blocked, "initially_reachable": normal})
		if not historical_consistency(mask):
			for i in range(nodes.size()):
				var sample := state_id(i, mask)
				if nodes[i]["required_transport"] != "walk" and transitions.has(sample) and winning.has(sample):
					recovery_witnesses.append({"source": "injected_flag_combination", "mask": mask, "path": recovery_witness(sample, winning)})
					break
	var gains: Array = []
	var initial_area := walking_reach(node_index[data["start_node"]], initial_mask)
	gains.append({"transport": "walk", "before_mask": initial_mask, "after_mask": initial_mask, "before_count": 0, "after_count": initial_area.size(), "new_count": initial_area.size()})
	for state in reachable:
		var before: int = int(state) / nodes.size()
		var index: int = int(state) % nodes.size()
		for next in transitions[state]:
			var after: int = int(next) / nodes.size()
			if before == after:
				continue
			for transport in transports:
				if mode_sets[before].has(transport) or not mode_sets[after].has(transport):
					continue
				var old_area := walking_reach(index, before)
				var new_area := walking_reach(index, after)
				var added: Array = []
				for target in new_area:
					if target not in old_area:
						added.append(nodes[target]["id"])
				gains.append({"transport": transport, "producer_node": nodes[index]["id"], "before_mask": before, "after_mask": after, "before_count": old_area.size(), "after_count": new_area.size(), "new_count": added.size(), "new_nodes": added})
	for transport in transports:
		var found := false
		for gain in gains:
			if gain["transport"] == transport:
				found = true
				if gain["new_count"] < 5:
					warnings.append({"code": "weak_transport_unlock", "transport": transport, "new_count": gain["new_count"]})
		if not found:
			error("transport_not_unlocked", transport)
	var transition_count := 0
	for targets in transitions.values():
		transition_count += targets.size()
	return {"status": "PASS" if errors.is_empty() else "FAIL", "scope": "abstract_graph", "errors": errors, "warnings": warnings,
		"node_count": nodes.size(), "edge_count": edges.size(), "reachable_nodes": reached_nodes, "unreachable_nodes": unreachable_nodes,
		"monotonic_violations": monotonic_violations, "flag_dependencies": deps, "flag_cycles": cycles,
		"flag_combination_count": mode_sets.size(), "state_count": nodes.size() * mode_sets.size(),
		"admissible_state_count": transitions.size(), "rejected_state_count": rejected.size(), "rejected_states": rejected,
		"initial_reachable_state_count": reachable.size(), "transition_count": transition_count, "deadlocks": deadlocks,
		"reachable_deadlock_count": reachable_deadlocks, "mask_summary": mask_summary, "transport_gains": gains,
		"completion_required_mask": required_mask, "completion_witness": witness(state_id(end, required_mask), reachable),
		"inconsistent_state_recovery_witnesses": recovery_witnesses,
		"terrain_verification": "NOT_RUN", "runtime_integration": "NOT_RUN"}
