extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var main := (load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	main.start_new_game(4)
	main.game.play_metrics.set_source("automated")
	main.game.set_world("waterway",[17,12],19)
	if not main.game.begin_expedition("waterway"):
		quit(1);return
	main._resume_current()
	await capture(main,"campaign_field")
	var entry: Dictionary = main.game.current_story_step()
	main.game.set_world(entry["location"],entry["cell"],19,entry["section"])
	main.submit_player_action({"kind":"interact"})
	await capture(main,"campaign_record")
	while main.automation_snapshot()["mode"] == "dialogue":
		main.submit_player_action({"kind":"confirm"})
	entry = main.game.current_story_step()
	main.game.set_world(entry["location"],entry["cell"],19,entry["section"])
	var encounter: BattleState = main.game.start_story_battle()
	for turn in range(50):
		if encounter.phase != BattleState.Phase.INPUT:break
		for actor in encounter.pending():
			encounter.queue_action(BattleAction.strike(actor.id,encounter.living(Combatant.Team.ENEMY)[0].id))
		encounter.resolve_round()
	if encounter.phase != BattleState.Phase.VICTORY:
		quit(1);return
	main.game.finish_battle();main.game.advance_story_step()
	entry = main.game.current_story_step()
	main.game.set_world(entry["location"],entry["cell"],19,entry["section"])
	main._resume_current()
	main.submit_player_action({"kind":"interact"})
	await capture(main,"campaign_challenge")
	main.submit_player_action({"kind":"challenge_answer","option":entry["answer"]})
	await capture(main,"campaign_resolution")
	print("CAMPAIGN_PREVIEW_PASS: 区画・記録・課題・報酬の実描画を保存")
	quit(0)

func capture(main: Node, name: String) -> void:
	await process_frame
	await process_frame
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	if main.get_viewport().get_texture().get_image().save_png("res://docs/verification/screens/"+name+".png") != OK:
		quit(1)
