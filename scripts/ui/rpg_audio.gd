class_name RpgAudio
extends Node
## BGMを切り替える再生器と、重ねて鳴らせる効果音の再生器を分ける。
## 設計参照: Newold / Godot RPG Creator、MIT。コードの複写なし。
var _music: Array[AudioStreamPlayer] = []
var _effects: Array[AudioStreamPlayer] = []
var _current := ""
var _slot := 0
var _effect_slot := 0
var _fade: Tween

func _ready() -> void:
	for i in range(2):
		var player := AudioStreamPlayer.new()
		add_child(player)
		_music.append(player)
	for i in range(6):
		var player := AudioStreamPlayer.new()
		player.volume_db=-8.0
		add_child(player)
		_effects.append(player)

func play_music(identifier: String) -> void:
	if identifier == _current or _music.is_empty():return
	_current=identifier
	if is_instance_valid(_fade):_fade.kill()
	var old: AudioStreamPlayer=_music[_slot]
	_slot=1-_slot
	var next: AudioStreamPlayer=_music[_slot]
	next.stop()
	var stream := load("res://assets/audio/bgm/"+identifier+".ogg") as AudioStreamOggVorbis
	next.stream=stream.duplicate()
	(next.stream as AudioStreamOggVorbis).loop=identifier!="victory"
	next.volume_db=-40.0
	next.play()
	_fade=create_tween().set_parallel(true)
	_fade.tween_property(next,"volume_db",-14.0,0.25)
	_fade.tween_property(old,"volume_db",-40.0,0.25)
	_fade.chain().tween_callback(old.stop)

func effect(identifier: String) -> void:
	if _effects.is_empty():return
	var player: AudioStreamPlayer=_effects[_effect_slot]
	_effect_slot=(_effect_slot+1)%_effects.size()
	player.stream=load("res://assets/audio/se/"+identifier+".wav")
	player.play()

func snapshot() -> Dictionary:
	return {"music":_current,"music_players":_music.size(),"effect_players":_effects.size(),"playing":not _music.is_empty() and _music[_slot].playing}

func shutdown() -> void:
	if is_instance_valid(_fade):_fade.kill()
	_fade=null
	var had_stream := false
	for player in _music+_effects:
		had_stream=had_stream or player.stream!=null
		player.stop()
		player.stream=null
	_current=""
	if had_stream:
		# stop()の解放は音声スレッド側で完了する。終了直前にその処理を待つ。
		# Godot #76745 と同じ終了競合を小さい再現例でも確認した。
		# ゲームと自動検査で同じ終了処理を使い、警告の除外はしない。
		var drain_ms := clampi(ceili((AudioServer.get_output_latency()+AudioServer.get_time_to_next_mix())*1000.0)+30,100,250)
		OS.delay_msec(drain_ms)

func _exit_tree() -> void:
	shutdown()
