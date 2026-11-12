## Autoload "Audio": zone music with crossfades, sound effects, jingles and dialogue voice lines.
## Everything is looked up by file name under res://assets/audio/{sfx,music,voice}/ and silently skipped if missing.
extends Node

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const VOICE_DIR := "res://assets/audio/voice/"
const MUSIC_DB := -9.0
const DUCKED_DB := -18.0
const VOICE_GAIN := 0.55   # NPC voice lines at 55% volume (45% quieter)
const SFX_DB := -3.0
const SETTINGS := "user://settings.cfg"
const KINDS := ["music", "sfx", "voice"]   # each has a 0..10 step the player can set (10 = as designed)

var _cache := {}
var _variants := {}
var _sfx: Array[AudioStreamPlayer] = []
var _music: Array[AudioStreamPlayer] = []
var _active := 0
var _current := ""
var _voice: AudioStreamPlayer
var _jingle: AudioStreamPlayer
var _voice_playing := false
var _jingle_playing := false
var _bus_tween: Tween
var _steps := {"music": 10, "sfx": 10, "voice": 10}
var fullscreen := false
var _pause_fx := -1


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_bus("Music", MUSIC_DB)
	_ensure_bus("SFX", SFX_DB)
	_ensure_bus("Voice", linear_to_db(VOICE_GAIN))
	_load_settings()
	var lp := AudioEffectLowPassFilter.new()        # muffles the music while the game is paused
	lp.cutoff_hz = 800.0
	var music_bus := AudioServer.get_bus_index("Music")
	AudioServer.add_bus_effect(music_bus, lp)
	_pause_fx = AudioServer.get_bus_effect_count(music_bus) - 1
	AudioServer.set_bus_effect_enabled(music_bus, _pause_fx, false)
	for i in 8:
		_sfx.append(_player("SFX"))
	for i in 2:
		var m := _player("Music")
		m.volume_db = -60.0
		_music.append(m)
	_voice = _player("Voice")
	_voice.finished.connect(func():
		_voice_playing = false
		_update_duck())
	_jingle = _player("Music")
	_jingle.finished.connect(func():
		_jingle_playing = false
		_update_duck())


# ------------------------------------------------------------------ user settings
func _step_db(kind: String) -> float:
	var s: int = _steps[kind]
	return -80.0 if s <= 0 else linear_to_db(s / 10.0)


func _base_db(kind: String) -> float:
	return {"music": MUSIC_DB, "sfx": SFX_DB, "voice": linear_to_db(VOICE_GAIN)}[kind]


func get_step(kind: String) -> int:
	return _steps[kind]


func set_step(kind: String, step: int, save: bool = true) -> void:
	_steps[kind] = clampi(step, 0, 10)
	_apply_volumes()
	if save:
		save_settings()


func set_fullscreen(v: bool, save: bool = true) -> void:
	fullscreen = v
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if v else DisplayServer.WINDOW_MODE_WINDOWED)
	if save:
		save_settings()


func _apply_volumes() -> void:
	for kind in ["sfx", "voice"]:
		AudioServer.set_bus_volume_db(AudioServer.get_bus_index(kind.capitalize() if kind != "sfx" else "SFX"), _base_db(kind) + _step_db(kind) if _steps[kind] > 0 else -80.0)
	_update_duck()


func _load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS) == OK:
		for kind in KINDS:
			_steps[kind] = clampi(int(cfg.get_value("audio", kind, 10)), 0, 10)
		fullscreen = bool(cfg.get_value("display", "fullscreen", false))
	if fullscreen:
		set_fullscreen(true, false)
	_apply_volumes()


func save_settings() -> void:
	var cfg := ConfigFile.new()
	for kind in KINDS:
		cfg.set_value("audio", kind, _steps[kind])
	cfg.set_value("display", "fullscreen", fullscreen)
	cfg.save(SETTINGS)


## Low-pass the music while a menu is open.
func set_pause_filter(on: bool) -> void:
	if _pause_fx >= 0:
		AudioServer.set_bus_effect_enabled(AudioServer.get_bus_index("Music"), _pause_fx, on)


func _exit_tree() -> void:
	for p in _sfx + _music + [_voice, _jingle]:
		p.stop()
		p.stream = null
	_cache.clear()
	_variants.clear()


func _ensure_bus(bus: String, db: float) -> void:
	if AudioServer.get_bus_index(bus) != -1:
		return
	AudioServer.add_bus()
	var i := AudioServer.bus_count - 1
	AudioServer.set_bus_name(i, bus)
	AudioServer.set_bus_send(i, "Master")
	AudioServer.set_bus_volume_db(i, db)


func _player(bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = bus
	add_child(p)
	return p


func _load(path: String) -> AudioStream:
	if _cache.has(path):
		return _cache[path]
	var s: AudioStream = null
	if ResourceLoader.exists(path):
		s = load(path)
	_cache[path] = s
	return s


# ------------------------------------------------------------------ sfx
## A sound can have variants: <name>.wav and/or <name>_1.wav ... <name>_6.wav. One is picked at random each time.
func _pick(sfx_name: String) -> AudioStream:
	if not _variants.has(sfx_name):
		var list: Array[AudioStream] = []
		var base := _load(SFX_DIR + sfx_name + ".wav")
		if base:
			list.append(base)
		for i in range(1, 7):
			var v := _load(SFX_DIR + "%s_%d.wav" % [sfx_name, i])
			if v:
				list.append(v)
		_variants[sfx_name] = list
	var options: Array = _variants[sfx_name]
	return null if options.is_empty() else options[randi() % options.size()]


func play_sfx(sfx_name: String, volume_db: float = 0.0, pitch_var: float = 0.06) -> void:
	var s := _pick(sfx_name)
	if s == null:
		return
	var p := _sfx[0]
	for c in _sfx:
		if not c.playing:
			p = c
			break
	p.stream = s
	p.volume_db = volume_db
	p.pitch_scale = 1.0 + randf_range(-pitch_var, pitch_var)
	p.play()


## Quieter with distance from the player; inaudible beyond ~220 px.
func play_sfx_at(sfx_name: String, pos: Vector2, volume_db: float = 0.0) -> void:
	var pl := get_tree().get_first_node_in_group("player")
	var d := 0.0 if pl == null else pos.distance_to(pl.global_position)
	if d > 220.0:
		return
	play_sfx(sfx_name, volume_db - d / 9.0)


# ------------------------------------------------------------------ music
func play_music(track: String, fade: float = 2.0) -> void:
	if track == _current:
		return
	var s := _load(MUSIC_DIR + track + ".ogg")
	if s == null:
		return
	_current = track
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = true
	var old := _music[_active]
	_active = 1 - _active
	var nw := _music[_active]
	nw.stream = s
	nw.volume_db = -60.0
	nw.play()
	var tw := create_tween().set_parallel(true)
	tw.tween_property(nw, "volume_db", 0.0, fade)
	tw.tween_property(old, "volume_db", -60.0, fade)
	tw.chain().tween_callback(old.stop)


func stop_music(fade: float = 1.0) -> void:
	_current = ""
	for m in _music:
		if m.playing:
			create_tween().tween_property(m, "volume_db", -60.0, fade)


## Short stinger over the music (the music ducks while it plays). `silence_music` for game over.
func play_jingle(jingle_name: String, silence_music: bool = false) -> void:
	var s := _load(MUSIC_DIR + jingle_name + ".ogg")
	if s == null:
		return
	if silence_music:
		stop_music(0.4)
	if s is AudioStreamOggVorbis:
		(s as AudioStreamOggVorbis).loop = false
	_jingle.stream = s
	_jingle.play()
	_jingle_playing = true
	_update_duck()


# ------------------------------------------------------------------ voice
## Plays res://assets/audio/voice/<key>.wav; returns its length in seconds (0 if there is none).
func play_voice(key: String) -> float:
	var s := _load(VOICE_DIR + key + ".wav")
	if s == null:
		stop_voice()
		return 0.0
	_voice.stream = s
	_voice.play()
	_voice_playing = true
	_update_duck()
	return s.get_length()


func stop_voice() -> void:
	_voice.stop()
	_voice_playing = false
	_update_duck()


func _update_duck() -> void:
	var target := (DUCKED_DB if (_voice_playing or _jingle_playing) else MUSIC_DB) + _step_db("music")
	if _steps["music"] <= 0:
		target = -80.0
	var bus := AudioServer.get_bus_index("Music")
	if _bus_tween:
		_bus_tween.kill()
	_bus_tween = create_tween()
	_bus_tween.tween_method(func(v: float): AudioServer.set_bus_volume_db(bus, v), AudioServer.get_bus_volume_db(bus), target, 0.3)
