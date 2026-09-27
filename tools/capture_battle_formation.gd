extends SceneTree
## 本番の戦闘画面を使う配置見本。物語の加入・転職解放を示すものではない。
const OUTPUT := "res://docs/verification/battle-bottom-band/checks/"
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
	for area in [Rect2i(4,4,146,60),Rect2i(370,4,138,46),Rect2i(4,124,12,48)]:
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
	else:check(panel.find_child("BattleCommands",true,false)==null,"演出中はコマンド窓がない")
	for name in required:
		var column := panel.find_child(name,true,false)
		check(column!=null,"必要な窓: "+name)
		if column!=null:
			boxes[name]=(column.get_parent() as Control).get_rect()
			var style := column.get_parent().get_theme_stylebox("panel") as StyleBoxFlat
			check(style!=null and style.bg_color==Color("101c50") and style.border_color==Color.WHITE,"濃い青と白の枠: "+name)
	if panel.replay.is_empty():check(boxes.get("BattleCommands")==Rect2(4,216,148,68),"左下のコマンド窓")
	check(boxes.get("BattlePartyStatus")==Rect2(268,216,240,68),"右下の能力値窓")
	check(boxes.get("BattleEnemyList",Rect2()).position==Vector2(156,216),"下端中央の敵一覧")
	for child in panel.get_children():
		if child is PanelContainer and not child.find_child("BattleSkillName",true,false):check(child.position.y==216,"窓は下端の帯にまとめる")
	var expected: Array=panel.replay.get("snapshot",{}).get("actors",[]) if not panel.replay.is_empty() else panel.game.current_battle().snapshot()["actors"]
	for i in range(count):
		var id := "pc_%02d" % (i+1)
		var rect := arena.actor_rect(id)
		check(CharacterVisuals.appearance(arena.members[i],"battle")["region"].size==Vector2(96,96),"再制作した96px素材を使用する: "+id)
		check(rect.position.x==175+i*87+(4-count)*43-(12 if id==arena.acting_actor else 0) and rect.size==Vector2(72,72),"承認済みの72px表示と斜めの列: "+id)
		check(Rect2(0,0,512,288).encloses(rect),"画面内: "+id)
		if i>0:
			var previous := arena.actor_rect("pc_%02d" % i)
			check(rect.position.y-previous.position.y==28 and not rect.intersects(previous),"隊列順・等間隔・人物矩形の重なりなし: "+id)
			check(not rect.intersects(Rect2(previous.position+Vector2(3,0),previous.size)) and not previous.intersects(Rect2(rect.position-Vector2(3,0),rect.size)),"被弾時の最大3pxの揺れでも重ならない: "+id)
		# 透明余白を含む人物矩形の非重複を維持し、顔の非重複も別に確認する。
		var face := Rect2(rect.position+Vector2(24,6),Vector2(24,22))
		for j in range(count):
			if j!=i:check(not face.intersects(arena.actor_rect("pc_%02d" % (j+1))),"顔がほかの人物に隠れない: "+id)
		check(rect.position==arena.party_rect(i).position-Vector2(12 if id==arena.acting_actor else 0,0),"行動者だけ左へ一歩進む: "+id)
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
				check(Rect2(268,216,240,68).encloses(actor_button.get_global_rect()),"名前が右下の窓に収まる")
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
					check(Rect2(268,216,240,68).encloses(bar.get_global_rect()),"棒グラフが右下の窓に収まる")
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
	if panel.replay.is_empty():
		var command_labels: Array[String]=[]
		for button in panel.find_child("BattleCommands",true,false).find_children("*","Button",true,false):command_labels.append(button.text)
		for name in ["ターン実行","選び直す","技の効果を確認"]:check(name in command_labels,"既存操作を維持: "+name)
		if panel.target_action.is_empty():
			for name in ["攻撃","防御","回復薬","観察"]:check(name in command_labels,"既存コマンドを維持: "+name)
		var text_value := "\n".join(labels)
		for intent in panel.game.current_battle().enemy_intents():
			var foe := panel.game.current_battle().actor_by_id(intent["actor"])
			check(text_value.contains("%s HP%d/%d" % [foe.display_name,foe.hp,foe.max_hp]),"敵の名前とHPを維持")
			check(text_value.contains("%s→%s" % [intent["action"],intent["target_name"]]),"敵の行動予定を維持")

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
