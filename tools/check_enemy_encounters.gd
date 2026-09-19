extends SceneTree

var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures.append(message)


func _run() -> void:
	var game: Variant = GameSession.new()
	_check(game.new_game(4), "新規状態を開始できる")
	_check(game.enemy_definitions.size() == 30, "敵30種類を定義する")
	_check(game.enemy_definitions.has("balm_slime"), "回復役を独立した敵として定義する")
	_check(game.has_method("start_story_battle"), "連戦の開始と保存状態を接続する")
	var encounter: Variant = game.start_battle(["slime"],111)
	_check(encounter.has_method("enemy_intents"), "敵の行動予定を確認できる")
	if not _failures.is_empty():
		_finish()
		return
	var seen: Dictionary = {}
	for index in range(StoryCampaign.total_steps()):
		for wave in StoryCampaign.battle_waves(StoryCampaign.step(index)):
			for identifier in wave:
				seen[identifier] = true
	_check(seen.size() == 30, "30種類すべてを本編の遭遇に配置する")
	var counts: Dictionary = {}
	for definition in game.enemy_definitions.values():
		var family: String = definition["family"]
		counts[family] = int(counts.get(family,0)) + 1
		_check(FileAccess.file_exists("res://assets/monsters/%s/idle.png" % definition["sprite_id"]), "実在する画像を参照する")
	for count in counts.values():
		_check(count == 6, "5系統それぞれに6種類を定義する")
	_check_ai()
	_check_waves()
	await _check_ui()
	if _failures.is_empty():
		print("ENCOUNTER_PASS: 敵30種・回復/防御/蘇生・予定の再現性・連戦保存を検証")
	_finish()


func _new_battle(ids: Array) -> BattleState:
	var game := GameSession.new()
	game.new_game(4)
	return game.start_battle(ids,512)


func _guard_party(encounter: BattleState) -> Array[Dictionary]:
	for actor in encounter.pending():
		_check(encounter.queue_action(BattleAction.guard(actor.id)).is_empty(), "通常の防御コマンドを受理する")
	return encounter.resolve_round()


func _check_ai() -> void:
	var healing := _new_battle(["balm_slime","ward_slime"])
	healing.actor_by_id("enemy_02").hp = 20
	var preview := healing.enemy_intents()
	_check(preview[0]["ability"] == "heal" and preview[0]["target"] == "enemy_02", "回復役は弱った敵側の仲間を選ぶ")
	var before_mp := healing.actor_by_id("enemy_01").mp
	var events := _guard_party(healing)
	_check(healing.actor_by_id("enemy_02").hp == 64, "敵の回復を実際に反映する")
	_check(healing.actor_by_id("enemy_01").mp == before_mp-4, "敵の回復でもMPを消費する")
	_check(events.any(func(event: Dictionary) -> bool: return event["code"] == "guard" and event["actor"] == "enemy_02"), "防御役が実際に堅守する")
	var starved := _new_battle(["balm_slime"])
	starved.actor_by_id("enemy_01").hp = 10
	starved.actor_by_id("enemy_01").mp = 0
	_check(starved.enemy_intents()[0]["ability"] == "", "MP不足の回復役は通常攻撃へ切り替える")
	var revival := _new_battle(["ash_wisp","ember_wisp"])
	revival.actor_by_id("enemy_02").hp = 0
	_check(revival.enemy_intents()[0]["ability"] == "revive", "蘇生役が戦闘不能の敵を選ぶ")
	_guard_party(revival)
	_check(revival.actor_by_id("enemy_02").hp == 28 and revival.actor_by_id("enemy_01").mp == 8, "蘇生のHPとMPを本番計算で反映する")
	var guarded := _new_battle(["ward_slime"])
	_check(guarded.enemy_intents()[0]["ability"] == "firm_guard", "防御役は最初のターンを守る")
	_guard_party(guarded)
	_check(guarded.enemy_intents()[0]["ability"] == "acid", "次のターンは攻撃へ切り替える")
	var first := _new_battle(["balm_slime","night_bat"])
	var second := _new_battle(["balm_slime","night_bat"])
	var initial := first.snapshot()
	var intent := first.enemy_intents()
	for index in range(30):
		_check(first.enemy_intents() == intent and first.snapshot() == initial, "行動予定の再表示で状態や予定を変えない")
	_check(_guard_party(first) == _guard_party(second), "予定を繰り返し見ても同じシード・入力から同じ結果を返す")


func _win(encounter: BattleState) -> bool:
	for turn in range(100):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		for actor in encounter.pending():
			encounter.queue_action(BattleAction.strike(actor.id,encounter.living(Combatant.Team.ENEMY)[0].id))
		encounter.resolve_round()
	return encounter.phase == BattleState.Phase.VICTORY


func _check_waves() -> void:
	var game: Variant = GameSession.new()
	game.new_game(4)
	game.set_world("waterway",[17,12],19)
	# 連戦の保存単体検査は、水路点検を完了した有効な前提状態から始める。
	game.set_progress_flag("circuit_waterway_cleared")
	_check(game.story_wave_count() == 3 and game.story_wave_index() == 0, "既存の進行番号で3戦の編成を読み込む")
	var old: Dictionary = game.export_state()
	var old_flags: Dictionary = old["progress_flags"]
	var encounter: BattleState = game.start_story_battle()
	_check(_win(encounter), "第1戦を実戦闘で勝利する")
	_check(game.finish_battle(), "第1戦の報酬と進捗を確定する")
	_check(game.story_wave_index() == 1 and not game.story_battle_cleared(), "第1戦だけで本編の戦闘全体をクリア扱いにしない")
	_check(not game.advance_story_step(), "残る敵を倒す前に物語を進めない")
	_check(game.export_state()["progress_flags"] == old_flags, "途中の勝利で回収フラグを変更しない")
	var won: Dictionary = game.export_state()
	_check(not game.finish_battle() and game.export_state() == won, "同じ勝利でJPや戦数を重複加算しない")
	_check(game.return_to_town(), "連戦の途中でも帰還できる")
	game.rest()
	_check(game.save_game("user://encounter_checkpoint.json"), "帰還した途中状態を保存できる")
	var restored: Variant = GameSession.new()
	_check(restored.load_game("user://encounter_checkpoint.json"), "連戦の途中状態を読み込める")
	_check(restored.export_state() == game.export_state(), "連戦進捗・JP・帰還位置が保存往復で一致する")
	_check(restored.resume_exploration(), "元の連戦地点へ戻る")
	encounter = restored.start_story_battle()
	_check(restored.current_enemy_ids() == ["ward_slime","balm_slime"], "ロード後は倒した敵を飛ばして第2戦から再開する")
	for actor in encounter.living(Combatant.Team.PARTY):
		actor.hp = 1
	_guard_party(encounter)
	for turn in range(100):
		if encounter.phase != BattleState.Phase.INPUT:
			break
		_guard_party(encounter)
	_check(encounter.phase == BattleState.Phase.DEFEAT, "第2戦で全滅する経路を検査する")
	restored.finish_battle()
	_check(restored.story_wave_index() == 1, "全滅で未討伐の戦数を加算しない")
	for wave in range(2):
		restored.rest()
		encounter = restored.start_story_battle()
		if not _win(encounter):
			_check(false, "残りの戦闘に勝利して保存検査へ進む")
			return
		restored.finish_battle()
	_check(restored.story_battle_cleared(), "全3戦の勝利で戦闘地点の完了を保存する")
	_check(restored.save_game("user://encounter_cleared.json"), "全討伐後・会話前の状態を保存する")
	var cleared := GameSession.new()
	_check(cleared.load_game("user://encounter_cleared.json"), "全討伐済みの状態を読み込む")
	var completed: Dictionary = cleared.export_state()
	_check(cleared.start_story_battle() == null and cleared.export_state() == completed, "討伐済み地点で再戦や重複報酬を発生させない")
	_check(cleared.advance_story_step() and cleared.world_state()["quest_step"] == 20, "ロード後も会話を確定して次へ進める")
	_check(cleared.export_state()["story_battle"].is_empty(), "次の地点へ進む時に連戦進捗を一度だけ消す")
	var pristine := GameSession.new()
	pristine.new_game(4)
	var legacy := pristine.export_state()
	legacy.erase("story_battle")
	_check(pristine.import_state(legacy), "新しい進捗項目のない従来セーブを読み込める")
	var broken := legacy.duplicate(true)
	broken["story_battle"] = {"step":0,"cleared":99}
	_check(not pristine.import_state(broken) and pristine.export_state() == legacy, "不正な連戦進捗を拒否し現在状態を保持する")


func _check_ui() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.set_world("waterway",[17,12],19)
	main.game.set_progress_flag("circuit_waterway_cleared")
	_check(main.submit_player_action({"kind":"interact"}), "通常操作から追加の編成と画像を使う戦闘へ入る")
	_check(main.automation_snapshot().get("mode") == "battle", "戦闘画面でエラーを出さない")
	if "--capture" in OS.get_cmdline_user_args():
		await process_frame
		await process_frame
		await process_frame
		RenderingServer.force_draw(false)
		RenderingServer.force_sync()
		_check(main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/enemy_intents.png") == OK, "実際の行動予定画面を保存する")
	main.queue_free()
	await process_frame


func _finish() -> void:
	for message in _failures:
		printerr("ENCOUNTER_FAIL: " + message)
	quit(0 if _failures.is_empty() else 1)
