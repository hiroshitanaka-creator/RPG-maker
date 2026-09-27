extends SceneTree
## 本番の戦闘画面を使う配置見本。物語の加入・転職解放を示すものではない。
const OUTPUT := "res://docs/verification/battle-fonts/formation/"
var failures: Array[String] = []
var checks := 0
var capture_enabled := false

func check(ok: bool, reason: String) -> void:
	checks+=1
	if not ok:failures.append(reason)

func _initialize() -> void:
	capture_enabled="--capture" in OS.get_cmdline_user_args()
	if capture_enabled and DisplayServer.get_name()=="headless":
		printerr("FORMATION_INVALID: 撮影には実描画が必要");quit(2);return
	root.content_scale_size=Vector2i(512,288)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.size=Vector2i(1024,576)
	call_deferred("run")

func screen(game: GameSession, event: Dictionary = {}, targets: bool = false, background: String = "plains") -> FirstRegionScreen:
	var result := FirstRegionScreen.new()
	var font := RpgFonts.get_font()
	result.theme=Theme.new();result.theme.default_font=font;result.theme.default_font_size=11
	result.game=game;result.screen_mode="battle";result.actor="pc_01"
	result.battle_background=background
	if targets:result.target_action={"kind":"potion","actor":"pc_01"}
	result.replay=event
	result.replay_members=game.export_state()["party"]
	result.replay_enemies=game.current_enemy_ids()
	root.add_child(result)
	return result

func arena_for(panel: FirstRegionScreen) -> RpgBattleView:
	for child in panel.get_children():
		if child is RpgBattleView:return child
	return null

func save_frame(name: String) -> void:
	if not capture_enabled:return
	await create_timer(0.2).timeout
	await process_frame;await process_frame
	await RenderingServer.frame_post_draw
	RenderingServer.force_draw(false);RenderingServer.force_sync()
	var frame := root.get_texture().get_image()
	check(not frame.is_empty() and frame.get_pixel(0,0)!=Color.WHITE,"白画面ではない: "+name)
	var backdrop := (load("res://assets/backgrounds/plains.png") as Texture2D).get_image()
	# 窓・人物のない空と地面で、原画と実描画のピクセルを比較する。
	var mismatches := 0
	for area in [Rect2i(8,28,50,30),Rect2i(200,146,90,50)]:
		for y in range(area.position.y,area.end.y):
			for x in range(area.position.x,area.end.x):
				if frame.get_pixel(x*2,y*2)!=backdrop.get_pixel(x,y+64):mismatches+=1
	check(mismatches==0,"背景の原寸描画: "+name+" 不一致="+str(mismatches))
	check(frame.save_png(OUTPUT+name+".png")==OK,"画像保存: "+name)

func geometry(panel: FirstRegionScreen, count: int) -> void:
	await process_frame;await process_frame
	var arena := arena_for(panel)
	check(arena!=null,"本番描画の存在")
	check(arena.background_offset().x==0 and arena.background_offset().y>=-64 and arena.background_offset().y<=0,"背景は横移動なし・上移動は64px以内")
	check(288+arena.background_offset().y>=220,"背景の下に空白が露出しない")
	for i in range(count):
		var id := "pc_%02d" % (i+1)
		var rect := arena.actor_rect(id)
		check(rect.position.x==304+i*48+(4-count)*24 and rect.size==Vector2(48,48),"承認済みの48px原寸と右下へ進む配置: "+id)
		check(Rect2(0,0,512,288).encloses(rect),"画面内: "+id)
		check(rect.end.y>=76 and rect.end.y<=220,"足元が地面にあり下端の窓より上: "+id)
		if i>0:
			var previous := arena.actor_rect("pc_%02d" % i)
			check(rect.position.y-previous.position.y==28 and not rect.intersects(previous),"隊列順・等間隔・重なりなし: "+id)
		var face := Rect2(rect.position+Vector2(12,2),Vector2(24,22))
		for j in range(count):
			if j!=i:check(not face.intersects(arena.party_rect(j)),"顔がほかの人物に隠れない: "+id)
		check(arena.effect_anchor(id)==rect.get_center(),"演出の中心: "+id)
		check(arena.cursor_rect(id).end.x<rect.position.x,"カーソルが人物を覆わない: "+id)
		for child in panel.get_children():
			if child is PanelContainer:check(not child.get_rect().intersects(rect),"文字窓が人物を覆わない: "+id)
	var bottom_windows: Array[Rect2] = []
	for child in panel.get_children():
		if child is PanelContainer and child.position.y==220:bottom_windows.append(child.get_rect())
	if panel.replay.is_empty():
		check(bottom_windows==[Rect2(0,220,216,68),Rect2(216,220,296,68)],"コマンド・能力値の窓が下端を横いっぱいに占める")
	else:check(bottom_windows==[Rect2(0,220,512,68)],"戦闘結果の窓が下端に収まる")
	var detail_buttons := 0
	var status_buttons := 0
	for button in panel.find_children("*","Button",true,false):
		check(button.text!="機構・予測","旧名称の表示がない")
		if button.text=="技の効果を確認":detail_buttons+=1
		if button.text.contains("HP") and button.text.contains("MP"):
			status_buttons+=1
			check(Rect2(216,220,296,68).encloses(button.get_global_rect()),"HP・MPの全行が窓内に収まる")
		check(button.get_theme_font("font")==RpgFonts.get_font(),"同梱Noto Sans JPを使用する")
		for letter in button.text:
			check(RpgFonts.get_font().has_char(letter.unicode_at(0)),"同梱字体の欠字なし: "+letter)
	if panel.replay.is_empty():check(detail_buttons==1 and status_buttons==count,"技の確認操作と人数分の能力値を維持")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUTPUT))
	for count in [4,3]:
		var game := GameSession.new()
		check(game.new_game(count),"共通APIで%d人の見本を準備" % count)
		var jobs := ["warrior","martial_artist","priest","mage"]
		for i in range(count):check(game.choose_job("pc_%02d" % (i+1),jobs[i]),"採用済み衣装を共通転職APIで選ぶ")
		var battle := game.start_battle(["slime"],20260927)
		check(battle!=null,"共通APIで戦闘を開始")
		var panel := screen(game)
		await geometry(panel,count)
		await save_frame("01-party-four" if count==4 else "02-party-three")
		panel.queue_free();await process_frame
		if count==3:continue
		# 実際の敵の攻撃を受け、回復薬の対象を通常の戦闘処理で用意する。
		for unit in battle.pending():check(battle.queue_action(BattleAction.guard(unit.id)).is_empty(),"対象選択前の防御入力")
		battle.resolve_round()
		panel=screen(game,{},true)
		await process_frame;await process_frame
		var selected_targets := 0
		for member in game.export_state()["party"]:
			for button in panel.find_children("*","Button",true,false):
				if button.text==member["name"]:
					button.grab_focus();await process_frame
					check(arena_for(panel).target_actor==member["id"],"通常の対象ボタンとカーソルの一致: "+member["id"])
					selected_targets+=1
		check(selected_targets>0,"味方の対象ボタンを実際に選択した")
		await save_frame("04-target-cursor")
		panel.queue_free();await process_frame
		for unit in battle.pending():check(battle.queue_action(BattleAction.strike(unit.id,"enemy_01")).is_empty(),"通常攻撃の入力")
		var events := battle.resolve_round()
		var attack_found := false
		for event in events:
			if event["code"]!="damage" or not str(event["actor"]).begins_with("pc_"):continue
			panel=screen(game,event)
			await geometry(panel,4)
			var arena := arena_for(panel)
			check(arena.acting_actor==event["actor"] and arena.effect_target==event["target"] and arena.effect_amount==event["amount"],"実戦の攻撃者・対象・数字と表示の一致")
			await save_frame("03-attack")
			panel.queue_free();await process_frame
			attack_found=true;break
		check(attack_found,"通常の戦闘結果から攻撃見本を取得")
		# 各表示状態の見本は本番と同じイベント構造を使う。戦闘の勝敗の検査ではない。
		for code in ["damage","heal","revive","fallen"]:
			var snapshot := battle.snapshot()
			for unit in snapshot["actors"]:
				if unit["id"]=="pc_04":unit["hp"]=0 if code=="fallen" else 12
			var event := {"code":code,"actor":"pc_03","target":"pc_04","amount":12,"message":"表示状態の見本："+code,"snapshot":snapshot}
			panel=screen(game,event);await process_frame
			var arena := arena_for(panel)
			arena.set_process(false);arena.set("_time",0.0);arena.queue_redraw()
			check(arena.effect_anchor("pc_04")==arena.actor_rect("pc_04").get_center(),"末尾の味方の演出位置: "+code)
			check(arena.party_hp["pc_04"]== (0 if code=="fallen" else 12),"描画時点のHP: "+code)
			await save_frame("state-"+code)
			panel.queue_free();await process_frame
	var backgrounds := GameSession.new()
	check(backgrounds.new_game(4),"14背景用の4人開始")
	check(backgrounds.start_battle(["slime"],20260927)!=null,"14背景用の通常戦闘")
	check(RpgBattleView.BACKGROUND_LAYOUT.size()==14,"14背景をすべて検査する")
	for background in RpgBattleView.BACKGROUND_LAYOUT:
		var panel := screen(backgrounds,{},false,background)
		await geometry(panel,4)
		panel.queue_free();await process_frame
	var record := {"status":"PASS" if failures.is_empty() else "FAIL","checks":checks,"failures":failures,"native_render":capture_enabled,"backgrounds":14,"font":"Noto Sans JP","scope":"本番描画による配置見本。物語の進行記録ではない。state画像は表示状態の見本","build":BuildIdentity.current()}
	PlaySessionMetrics.write_json(OUTPUT+"checks.json",record)
	for failure in failures:printerr("FORMATION_FAIL: "+failure)
	print("FORMATION_PASS: checks=%d" % checks if failures.is_empty() else "FORMATION_FAIL: failures=%d" % failures.size())
	quit(0 if failures.is_empty() else 1)
