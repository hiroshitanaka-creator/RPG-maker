class_name ChapterOne
extends RefCounted

const WIDTH := 32
const HEIGHT := 18
const TILE_SIZE := 32
const TITLES := {"town": "段の町", "waterway": "旧水路", "cave": "地下回廊", "gate": "分け水門", "garden":"干し庭", "harbor":"河岸の町", "school":"旧教習所", "records":"記録坑道"}
const TOWNS := ["town", "garden", "harbor"]
const REQUIRED_ART := [
	"res://assets/palette/base.gpl",
	"res://assets/characters/pc_01/walk.png",
	"res://assets/characters/pc_01/portrait.png",
	"res://assets/characters/pc_02/portrait.png",
	"res://assets/characters/pc_03/portrait.png",
	"res://assets/characters/pc_04/portrait.png",
	"res://assets/tiles/field_outdoor.png",
	"res://assets/tiles/dungeon_cave.png",
	"res://assets/monsters/slime/idle.png",
	"res://assets/monsters/bat/idle.png",
	"res://assets/monsters/shell_guard/idle.png",
	"res://assets/monsters/ember_wisp/idle.png",
	"res://assets/monsters/gate_beast/idle.png"
]
const STEPS := [
	{"location":"town", "cell":[5,4], "kind":"dialogue", "objective":"町の掲示を調べる", "text":["大水の予報が出た。閉じた避難路を開くには、水門の修理札が必要だ。", "仲間は旅立ちの朝から一緒だ。それぞれの得意な役目を相談して出発しよう。", "職業と装着は『編成』から選べる。魔物職はマスターすると姿が変わる。熟練度を見ながら選ぼう。"]},
	{"location":"town", "cell":[28,14], "kind":"travel", "objective":"町の南東から旧水路へ", "destination":"waterway", "spawn":[1,12]},
	{"location":"waterway", "cell":[7,12], "kind":"battle", "objective":"水路の通り道を確保する", "enemies":["slime"], "text":["勝利すると、現在の職業にJPが入る。技は覚えた後も転職先へ持ち越せる。"]},
	{"location":"waterway", "cell":[17,5], "kind":"dialogue", "objective":"橋の古い掲示を調べる", "text":["『受け持つのは二つまで。残りは渡せ。』", "掲示の下には古い職業教習の印がある。誰に残りを渡すのかは書かれていない。"], "flag":"clue_R04_seeded"},
	{"location":"waterway", "cell":[26,5], "kind":"battle", "objective":"橋をふさぐコウモリを退ける", "enemies":["bat"], "text":["相手が速いときも、防御は攻撃が来る前に間に合う。習得した技は、装着してから使おう。"]},
	{"location":"waterway", "cell":[30,3], "kind":"travel", "objective":"水路の東から地下回廊へ", "destination":"cave", "spawn":[1,12]},
	{"location":"cave", "cell":[7,10], "kind":"battle", "objective":"硬い殻の番兵を越える", "enemies":["shell_guard"], "text":["鎧には物理が通りにくい。魔法や弱点を使うか、回復と防御で持ちこたえるかを選べる。"]},
	{"location":"cave", "cell":[20,12], "kind":"dialogue", "objective":"地下の休息所を調べる", "rest":true, "text":["昔の作業員が使った休息所が残っている。全員のHPとMPを回復した。", "マスターした職の成長は残る。魔物職のマスターによる魔物化は、転職だけでは解除されない。", "町の祠では、侵蝕が90に達する前なら魔物の技を手放して戻れる。戻す前に装着を見直そう。"]},
	{"location":"cave", "cell":[26,10], "kind":"battle", "objective":"修理札を守る残り火の精を退ける", "enemies":["ember_wisp"], "text":["水門の修理札を見つけた。まず町へ持ち帰ろう。"], "flag":"repair_token_found"},
	{"location":"cave", "cell":[30,1], "kind":"travel", "objective":"地上への通路から町へ戻る", "destination":"town", "spawn":[27,14]},
	{"location":"town", "cell":[5,4], "kind":"dialogue", "objective":"町で修理札を確認する", "rest":true, "text":["町の掲示に修理札の図がある。届け先は北東の分け水門だ。", "出発前に全員のHPとMPを回復した。現在の職と、持ち越す技を選び直せる。"]},
	{"location":"town", "cell":[29,2], "kind":"travel", "objective":"町の北東から分け水門へ", "destination":"gate", "spawn":[1,14]},
	{"location":"gate", "cell":[19,10], "kind":"battle", "objective":"水門の荒獣を退ける", "enemies":["gate_beast"], "text":["荒獣が退き、門の奥へ進めるようになった。"]},
	{"location":"gate", "cell":[27,4], "kind":"dialogue", "objective":"門の番人と打ち板を調べる", "text":["魔物の姿の番人が、板を二度打った。こちらの音を待っているようだ。", "番人の首の札には、水番の符号が刻まれている。", "板の低い位置に、二つずつ並ぶ傷がある。", "番人は修理札を確かめ、閉じた道の横にある細い通路を示した。"], "flags":["clue_R01_seeded","clue_R07_seeded"]},
	{"location":"gate", "cell":[30,4], "kind":"complete", "objective":"番人が示した通路へ進む"}
]


static func step(index: int) -> Dictionary:
	return STEPS[index].duplicate(true) if index >= 0 and index < STEPS.size() else {}


static func is_walkable(location: String, cell: Vector2i) -> bool:
	if not TITLES.has(location) or cell.x <= 0 or cell.y <= 0 or cell.x >= WIDTH-1 or cell.y >= HEIGHT-1:
		return false
	match location:
		"town":
			if (cell.x >= 9 and cell.x <= 13 and cell.y >= 5 and cell.y <= 10) or (cell.x >= 20 and cell.x <= 23 and cell.y >= 8 and cell.y <= 13):
				return false
		"waterway":
			if cell.x >= 11 and cell.x <= 13 and cell.y >= 2 and cell.y <= 15 and not cell.y in [6,12]:
				return false
			if cell.x >= 22 and cell.x <= 24 and cell.y <= 13 and cell.y != 5:
				return false
		"cave":
			if cell.x in [8,16,24] and not cell.y in [3,10,14]:
				return false
		"gate":
			if cell.y == 8 and cell.x >= 6 and cell.x <= 25 and cell.x != 12:
				return false
		"garden":
			if cell.y in [5,13] and cell.x >= 8 and cell.x <= 24 and cell.x not in [15,22]:
				return false
		"harbor":
			if cell.x in [10,21] and cell.y >= 4 and cell.y <= 15 and cell.y not in [7,12]:
				return false
		"school":
			if cell.y in [6,11] and cell.x >= 5 and cell.x <= 26 and cell.x not in [10,19]:
				return false
		"records":
			if cell.x in [9,18,25] and cell.y not in [4,10,14]:
				return false
	return true


static func walkable_cells(location: String) -> Array:
	var result: Array = []
	for y in range(HEIGHT):
		for x in range(WIDTH):
			if is_walkable(location, Vector2i(x,y)):
				result.append([x,y])
	return result


static func missing_art() -> Array[String]:
	var missing: Array[String] = []
	for path in REQUIRED_ART:
		if not FileAccess.file_exists(path):
			missing.append(path.trim_prefix("res://"))
	return missing
