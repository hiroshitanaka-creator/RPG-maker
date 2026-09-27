extends SceneTree
## 本番の戦闘画面を使う配置見本。物語の加入・転職解放を示すものではない。
const OUTPUT := "res://docs/verification/battle-layout-exact/checks/"
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

func screen(game: GameSession, event: Dictionary = {}, targets: bool = false, background: String = "temple") -> FirstRegionScreen:
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
	var backdrop := (load("res://assets/backgrounds/temple.png") as Texture2D).get_image()
	# 窓・人物のない空と地面で、原画と実描画のピクセルを比較する。
	var mismatches := 0
	for area in [Rect2i(4,4,300,52),Rect2i(4,72,20,60)]:
		for y in range(area.position.y,area.end.y):
			for x in range(area.position.x,area.end.x):
				if frame.get_pixel(x*2,y*2)!=backdrop.get_pixel(x,y):mismatches+=1
	check(mismatches==0,"背景の原寸描画: "+name+" 不一致="+str(mismatches))
	check(frame.save_png(OUTPUT+name+".png")==OK,"画像保存: "+name)

func geometry(panel: FirstRegionScreen, count: int) -> void:
	await process_frame;await process_frame
	var arena := arena_for(panel)
	check(arena!=null,"本番描画の存在")
	check(arena.background_offset()==Vector2.ZERO,"背景を移動・切り抜きせず全画面へ描く")
	var boxes: Dictionary={}
	var required := ["BattleEnemyList","BattlePartyStatus"]
	if panel.replay.is_empty():required.append("BattleCommands")
	else:
		check(panel.find_child("BattleCommands",true,false)==null,"演出中はコマンド窓がない")
		for button in panel.find_children("*","Button",true,false):
			if button.text=="表示をスキップ  Enter":
				var style := button.get_theme_stylebox("normal") as StyleBoxFlat
				check(style!=null and style.bg_color==Color("101c50") and style.border_color==Color.WHITE,"スキップ表示に青地と白枠がある")
	for name in required:
		var column := panel.find_child(name,true,false)
		check(column!=null,"必要な窓: "+name)
		if column!=null:
			boxes[name]=(column.get_parent() as Control).get_rect()
			var style := column.get_parent().get_theme_stylebox("panel") as StyleBoxFlat
			check(style!=null and style.bg_color==Color("101c50") and style.border_color==Color.WHITE,"濃い青と白の枠: "+name)
	if panel.replay.is_empty():check(boxes.get("BattleCommands")==Rect2(4,223,148,65),"左下のコマンド窓")
	check(boxes.get("BattlePartyStatus")==Rect2(268,223,240,65),"右下の能力値窓")
	check(boxes.get("BattleEnemyList",Rect2()).position==Vector2(156,223),"下端中央の敵一覧")
	for child in panel.get_children():
		if child is PanelContainer and not child.find_child("BattleSkillName",true,false):check(child.position.y==223,"窓は下端の帯にまとめる")
	var expected: Array=panel.replay.get("snapshot",{}).get("actors",[]) if not panel.replay.is_empty() else panel.game.current_battle().snapshot()["actors"]
	for i in range(count):
		var id := "pc_%02d" % (i+1)
		var rect := arena.actor_rect(id)
		check(CharacterVisuals.appearance(arena.members[i],"battle")["region"].size==Vector2(96,96),"再制作した96px素材を使用する: "+id)
		check(rect.position.x==356+i*20-(30 if id==arena.acting_actor else 0) and rect.size==Vector2(72,72),"承認済みの72px表示と斜めの列: "+id)
		check(Rect2(0,0,512,288).encloses(rect),"画面内: "+id)
		check(arena.party_rect(i).get_center().x==392+i*20 and arena.party_rect(i).end.y==112+i*34,"指定された足元座標: "+id)
		for enemy_index in range(arena.enemy_ids.size()):
			check(not rect.grow(3).intersects(arena.actor_rect("enemy_%02d" % (enemy_index+1)).grow(3)),"前進と被弾を含め敵に重ならない: "+id)
		if i>0:
			var previous := arena.actor_rect("pc_%02d" % i)
			check(rect.position.y-previous.position.y==34,"隊列順・等間隔: "+id)
		# 頭・顔は独立した実描画の画素検査で、前景の不透明画素と照合する。
		check(rect.position==arena.party_rect(i).position-Vector2(30 if id==arena.acting_actor else 0,0),"行動者だけ左へ一歩進む: "+id)
		check(arena.effect_anchor(id)==rect.get_center(),"演出の中心: "+id)
		check(arena.cursor_rect(id).end.x<rect.position.x,"カーソルが人物を覆わない: "+id)
		for child in panel.get_children():
			if child is PanelContainer:check(not child.get_rect().intersects(rect),"文字窓が人物を覆わない: "+id)
		for unit in expected:
			if unit["id"]!=id:continue
			var actor_button := panel.find_child("Status_"+id,true,false) as Button
			check(actor_button!=null and actor_button.text.begins_with(str(unit["name"])),"人数分の名前と人物選択ボタンを維持: "+id)
			if actor_button!=null:
				var active := id==(arena.acting_actor if not panel.replay.is_empty() else panel.actor)
				check(actor_button.get_theme_color("font_disabled_color" if actor_button.disabled else "font_color")== (Color("ffe36b") if active else Color.WHITE),"行動者の名前を黄色で表示: "+id)
				check(Rect2(268,223,240,65).encloses(actor_button.get_global_rect()),"名前が右下の窓に収まる")
				for kind in ["HP","MP"]:
					var value_text := "%s%d/%d" % [kind,unit[kind.to_lower()],unit["max_"+kind.to_lower()]]
					var found := false
					for child in actor_button.get_parent().get_children():
						if child is Label and child.text==value_text:found=true
					check(found,"人物の数値表記も維持: "+kind+id)
			for kind in ["HP","MP"]:
				var bar := panel.find_child(kind+"_"+id,true,false) as ProgressBar
				check(bar!=null,"人物別の棒グラフ: "+kind+id)
				if bar!=null:
					check(bar.value==int(unit[kind.to_lower()]) and bar.max_value==maxi(1,int(unit["max_"+kind.to_lower()])),"棒グラフが実際の値と一致: "+kind+id)
					check(Rect2(268,223,240,65).encloses(bar.get_global_rect()),"棒グラフが右下の窓に収まる")
	var labels: Array[String]=[]
	for control in panel.find_children("*","Control",true,false):
		if control is Label:
			labels.append(control.text)
			check(control.get_theme_font("font")==RpgFonts.get_font(),"表示文字にも同梱字体を使用する")
			for letter in control.text:
				if letter not in ["\n","\r","\t"]:check(RpgFonts.get_font().has_char(letter.unicode_at(0)),"表示文字の欠字なし: "+letter)
	for button in panel.find_children("*","Button",true,false):
		check(button.text!="機構・予測","旧名称の表示がない")
		check(button.get_theme_font("font")==RpgFonts.get_font(),"同梱Noto Sans JPを使用する")
		for letter in button.text:check(RpgFonts.get_font().has_char(letter.unicode_at(0)),"同梱字体の欠字なし: "+letter)
	# スクロール外の文字は窓と画面に収まり、字体が必要とする行高を確保する。
	for control in panel.find_children("*","Control",true,false):
		if not (control is Button or control is Label) or not control.is_visible_in_tree():continue
		var ancestor := control.get_parent()
		var inside_scroll := false
		var enclosing: PanelContainer
		while ancestor!=panel and ancestor!=null:
			if ancestor is ScrollContainer:inside_scroll=true
			if ancestor is PanelContainer:enclosing=ancestor
			ancestor=ancestor.get_parent()
		if inside_scroll:continue
		var rectangle: Rect2=control.get_global_rect()
		check(Rect2(0,0,512,288).encloses(rectangle),"文字が画面内に収まる: "+control.text)
		if enclosing!=null:check(enclosing.get_global_rect().encloses(rectangle),"文字が窓の内側に収まる: "+control.text)
		var font_size: int=control.get_theme_font_size("font_size")
		var font: Font=control.get_theme_font("font")
		check(font_size>=10 and rectangle.size.y>=font.get_height(font_size),"漢字の大きさと行高を維持: "+control.text)
	if panel.replay.is_empty():
		var action_scroll := panel.find_child("BattleActionScroll",true,false) as ScrollContainer
		var round_actions := panel.find_child("BattleRoundActions",true,false) as Control
		check(action_scroll!=null and round_actions!=null,"対象欄と操作欄がある")
		if action_scroll!=null and round_actions!=null:
			check(action_scroll.clip_contents and not action_scroll.get_global_rect().intersects(round_actions.get_global_rect()),"対象欄が操作欄と重ならず領域外へ描かれない")
			check(Rect2(4,223,148,65).encloses(round_actions.get_global_rect()),"ターン実行などの操作欄が65pxの窓内に収まる")
		var command_labels: Array[String]=[]
		for button in panel.find_child("BattleCommands",true,false).find_children("*","Button",true,false):command_labels.append(button.text)
		for name in ["ターン実行","選び直す","技の効果を確認"]:check(name in command_labels,"既存操作を維持: "+name)
		if panel.target_action.is_empty():
			for name in ["攻撃","防御","回復薬","観察"]:check(name in command_labels,"既存コマンドを維持: "+name)
		if panel.target_action.is_empty():
			var enemy_window := panel.find_child("BattleEnemyList",true,false)
			for label in enemy_window.find_children("*","Label",true,false):
				check(not label.text.contains("HP") and not label.text.contains("→"),"通常の敵一覧は名前と数だけ")
			check(panel.find_child("BattleTargetDetails",true,false)==null,"入力対象を選ぶ前は個体詳細を出さない")
	# 敵は足元順に描き、最大5体でも全身が隠れない。
	var order := arena.enemy_draw_order()
	for i in range(arena.enemy_ids.size()):
		var enemy_rect := arena.actor_rect("enemy_%02d" % (i+1))
		check(enemy_rect.size==arena.enemy_region(arena.enemy_ids[i]).size*0.75,"敵は素材実寸の75%表示")
		var points := [Vector2(110,120),Vector2(215,134),Vector2(90,178),Vector2(180,200),Vector2(270,186)]
		var priority := [3,1,0,4,2]
		check(Vector2(enemy_rect.get_center().x,enemy_rect.end.y)==points[i if arena.enemy_ids.size()==5 else priority[i]],"敵の足元は見本の5点と中央優先順に一致")
		check(Rect2(0,0,350,216).encloses(enemy_rect),"敵は左側の戦場内に収まる")
		for j in range(i):check(not enemy_rect.grow(3).intersects(arena.actor_rect("enemy_%02d" % (j+1)).grow(3)),"敵同士は被弾の揺れも含めて重ならない")
		if i>0:check(arena.enemy_feet(order[i]).y>=arena.enemy_feet(order[i-1]).y,"奥の敵から手前の敵の順に描く")

func run() -> void:
	var head_path := "res://docs/verification/battle-layout-exact/head-pixels.json"
	check(FileAccess.file_exists(head_path),"頭・顔の実描画画素検査の記録が存在する")
	if FileAccess.file_exists(head_path):
		var head: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(head_path))
		var expected_build := BuildIdentity.current()
		var recorded_build: Dictionary=head.get("build",{})
		check(head.get("status")=="PASS" and recorded_build.get("id")==expected_build["id"] and recorded_build.get("engine")==expected_build["engine"] and int(recorded_build.get("files",-1))==expected_build["files"] and int(recorded_build.get("version",-1))==expected_build["version"],"同じ版で頭・顔の遮蔽0画素を確認済み")
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
			for button in panel.find_child("BattleCommands",true,false).find_children("*","Button",true,false):
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
	# 同種敵の集約、各行動者の前進、技名の帯を本番表示で追加確認する。
	var grouped := GameSession.new();check(grouped.new_game(4),"集約表示用の4人開始")
	var grouped_battle := grouped.start_battle(["slime","slime","shell_guard"],20260927)
	var grouped_panel := screen(grouped)
	await process_frame;await process_frame
	var heading_count := 0
	for label in grouped_panel.find_child("BattleEnemyList",true,false).find_children("*","Label",true,false):
		if label.text=="水路スライム 2":heading_count+=1
	check(heading_count==1,"同じ敵2体は見出し1件に集約する")
	check(grouped_panel.find_child("BattleSkillName",true,false)==null,"入力中は技名の帯を出さない")
	grouped_panel.queue_free();await process_frame
	for i in range(4):
		var identifier := "pc_%02d" % (i+1)
		var event := {"code":"ability","actor":identifier,"target":"enemy_01","ability_name":"火球","amount":0,"snapshot":grouped_battle.snapshot()}
		var panel := screen(grouped,event)
		await geometry(panel,4)
		var banner := panel.find_child("BattleSkillName",true,false)
		check(banner!=null and banner.get_parent().get_rect()==Rect2(156,4,200,24),"技名の帯を上中央だけに表示")
		if banner!=null:check(banner.get_child(0).text=="火球","発動した技名と一致")
		var arena := arena_for(panel)
		for j in range(4):
			var id := "pc_%02d" % (j+1)
			arena.focus_target(id)
			check(arena.cursor_rect(id).get_center().y==arena.actor_rect(id).get_center().y,"前進中も対象カーソルが追従: "+id)
			check(arena.effect_anchor(id)==arena.actor_rect(id).get_center(),"前進中も演出が追従: "+id)
		panel.queue_free();await process_frame
	# 入力画面に戻ると全員が元の列へ戻る。
	grouped_panel=screen(grouped);await geometry(grouped_panel,4)
	check(arena_for(grouped_panel).acting_actor.is_empty(),"行動後は前進を解除する")
	grouped_panel.queue_free();await process_frame
	# 5体は撮影専用入力。通常ゲームの戦闘上限を拡張しない。
	var five := preload("res://tools/battle_five_enemy_preview.gd").new();five.prepare()
	var five_panel := screen(five);await geometry(five_panel,4)
	five_panel.queue_free();await process_frame
	for game in [grouped,five]:
		var panel := FirstRegionScreen.new()
		panel.theme=Theme.new();panel.theme.default_font=RpgFonts.get_font()
		panel.game=game;panel.screen_mode="battle";panel.actor="pc_01"
		panel.target_action={"kind":"attack","actor":"pc_01"}
		root.add_child(panel);await geometry(panel,4)
		var buttons := panel.find_child("BattleCommands",true,false).find_children("*","Button",true,false)
		var checked := 0
		for button in buttons:
			if button.text in ["戻る","ターン実行","選び直す","技の効果を確認"]:continue
			button.grab_focus();await process_frame;await process_frame
			var selection_scroll := panel.find_child("BattleActionScroll",true,false) as ScrollContainer
			check(selection_scroll.get_global_rect().encloses(button.get_global_rect()),"選択中の敵名はスクロール領域内に見える")
			var identifier := arena_for(panel).target_actor
			var foe: Combatant=game.current_battle().actor_by_id(identifier)
			var detail := panel.find_child("BattleTargetDetails",true,false) as Label
			check(detail!=null and detail.visible,"対象選択中は詳細が見える")
			if detail!=null:
				check(detail.text.contains("%s HP%d/%d" % [foe.display_name,foe.hp,foe.max_hp]),"選んだ個体の実際のHPと名前が一致")
				for intent in game.current_battle().enemy_intents():
					if intent["actor"]==identifier:check(detail.text.contains("%s→%s" % [intent["action"],intent["target_name"]]),"選んだ個体の行動予定が一致")
			checked+=1
		check(checked==game.current_enemy_ids().size(),"同名の敵を含む全対象を選択した")
		panel.queue_free();await process_frame
	var backgrounds := GameSession.new()
	check(backgrounds.new_game(4),"14背景用の4人開始")
	var jobs := ["warrior","martial_artist","priest","mage"]
	for i in range(4):check(backgrounds.choose_job("pc_%02d" % (i+1),jobs[i]),"14背景でも新しい4職の素材を確認")
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
