## Opening sequence: black screen with embers and story text -> the keeper wakes up (eyelid transition) -> inner thoughts ->
## walks to the desk -> reads the diary -> more thoughts -> free play. Esc skips it at any moment.
## Debug flags: --autoplay (auto-advance, 5x faster), --intro-shots=<dir> (save screenshots at key moments).
extends Node

const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")

const STORY := [
	"LONG AGO, THE LANTERNS OF EMBERWICK\nHELD BACK THE NIGHT-MIST.",
	"EACH DUSK, THE KEEPER LIT THEM ONE BY ONE,\nAND THE VILLAGE SLEPT IN PEACE.",
	"BUT THE FLAMES GREW WEAK...",
	"AND ON A QUIET MORNING,\nTHE LAST KEEPER AWOKE.",
]

var main: Node2D
var player: CharacterBody2D
var house: Node2D
var _cards: CanvasLayer
var _skipped := false
var _done := false
var _fast := false
var _asleep := false
var _speed := 1.0
var _shots := ""
var _tweens: Array[Tween] = []     # killed on skip so nothing animates freed labels
var _dlg: Node
var _diary: Node


func run(m: Node2D) -> void:
	main = m
	player = m.player
	house = m.house
	_dlg = get_tree().get_first_node_in_group("dialogue")
	_diary = get_tree().get_first_node_in_group("diary")
	var args := OS.get_cmdline_user_args()
	if args.has("--autoplay"):
		_speed = 0.2
	for a in args:
		if a.begins_with("--skip-after="):
			get_tree().create_timer(float(a.substr(13))).timeout.connect(skip_now)
		if a.begins_with("--intro-shots="):
			_shots = a.substr(14)
			DirAccess.make_dir_recursive_absolute(_shots)
	main.cutscene = true
	main.music_lock = true
	player.locked = true
	player.asleep = true
	main.hud.visible = false

	await _title_cards()
	if _skipped:
		return
	await _wake_up()
	if _skipped:
		return
	await _morning()
	if _skipped:
		return
	await _hand_over()


# ------------------------------------------------------------------ helpers
func _tw() -> Tween:
	var t := create_tween()
	_tweens.append(t)
	return t


func _d(x: float) -> float:
	return x * _speed


func _wait(sec: float) -> void:
	var t := 0.0
	while t < sec * _speed and not _skipped and not _fast:
		await get_tree().process_frame
		t += get_process_delta_time()


func _shot(name: String) -> void:
	if _shots == "":
		return
	await get_tree().process_frame
	await get_tree().process_frame
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_shots, name])


func _label(text: String, size: int, color: Color, y: float, h: float) -> Label:
	var l := Label.new()
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART   # before text/size, see diary.gd
	l.custom_minimum_size = Vector2(300, 0)
	l.text = text
	l.position = Vector2(10, y)
	l.size = Vector2(300, h)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.modulate.a = 0.0
	_cards.add_child(l)
	return l


func _think(lines: Array, shot_name: String = "") -> void:
	if _skipped:
		return
	_dlg.show_lines("", PackedStringArray(lines), "", "thought")
	if shot_name != "":
		await get_tree().create_timer(_d(1.6)).timeout
		await _shot(shot_name)
	await _dlg.closed


func _unhandled_input(event: InputEvent) -> void:
	if _done or _skipped or _cards == null and not main.cutscene:
		return
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		skip_now()
	elif _cards != null and (event.is_action_pressed("interact") or event.is_action_pressed("attack")):
		_fast = true     # hurry the current title card along


# ------------------------------------------------------------------ title cards
func _title_cards() -> void:
	_cards = CanvasLayer.new()
	_cards.layer = 90
	add_child(_cards)
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.size = Vector2(320, 180)
	_cards.add_child(bg)
	_embers()
	Transition.clear()                       # the cards have their own black backdrop
	Audio.play_music("mistwood", 5.0)
	await _wait(1.4)
	if _skipped:
		return

	var title := _label("EMBERWICK", 24, Color("ffc44a"), 58, 30)
	var sub := _label("A TALE OF LANTERNS AND MIST", 8, Color("9a86c8"), 96, 12)
	Audio.play_sfx("title_chime", -4.0, 0.0)
	var tw := _tw().set_parallel(true)
	tw.tween_property(title, "modulate:a", 1.0, _d(2.2))
	tw.tween_property(sub, "modulate:a", 1.0, _d(3.2))
	tw.tween_property(title, "position:y", 54.0, _d(5.0)).set_trans(Tween.TRANS_SINE)   # a slow drift upward
	await _wait(2.8)
	await _shot("01_title")
	_fast = false
	await _wait(2.6)
	if _skipped:
		return
	var out := _tw().set_parallel(true)
	out.tween_property(title, "modulate:a", 0.0, _d(1.4))
	out.tween_property(sub, "modulate:a", 0.0, _d(1.0))
	await _wait(1.8)

	for i in STORY.size():
		if _skipped:
			return
		_fast = false
		var card := _label(STORY[i], 8, Color("f5f0e6"), 60, 60)
		card.visible_ratio = 0.0
		card.modulate.a = 1.0
		var type := _tw()
		type.tween_property(card, "visible_ratio", 1.0, _d(STORY[i].length() * 0.06))
		await _wait(STORY[i].length() * 0.06 + 1.9)
		if _skipped:
			return
		if i == 1:
			await _shot("02_story")
		type.kill()
		var fade := _tw()
		fade.tween_property(card, "modulate:a", 0.0, _d(1.0))
		await _wait(1.2)
		if _skipped:
			return
		card.queue_free()
	_fast = false


func _embers() -> void:
	var p := CPUParticles2D.new()
	p.position = Vector2(160, 188)
	p.amount = 46
	p.lifetime = 10.0
	p.preprocess = 8.0
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(170, 2)
	p.direction = Vector2(0.15, -1)
	p.spread = 20.0
	p.initial_velocity_min = 8.0
	p.initial_velocity_max = 24.0
	p.gravity = Vector2.ZERO
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.0
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 0.25, 0.7, 1.0])
	g.colors = PackedColorArray([Color("ffc44a"), Color("f08a2a"), Color("c8601f"), Color(0.78, 0.38, 0.12, 0.0)])
	p.color_ramp = g
	_cards.add_child(p)


# ------------------------------------------------------------------ waking up
func _zzz_loop() -> void:
	while _asleep and not _skipped:
		var z := Label.new()
		z.text = "Z"
		z.add_theme_font_override("font", FONT)
		z.add_theme_font_size_override("font_size", 8)
		z.add_theme_color_override("font_color", Color("f5f0e6"))
		z.z_index = 50
		z.position = house.global_position + Vector2(50, 36)
		main.world.add_child(z)
		var tw := create_tween().set_parallel(true)
		tw.tween_property(z, "position", z.position + Vector2(10, -14), 2.0)
		tw.tween_property(z, "modulate:a", 0.0, 2.0).set_delay(0.6)
		tw.chain().tween_callback(z.queue_free)
		await get_tree().create_timer(0.9).timeout


func _wake_up() -> void:
	main.enter_house_instant()
	house.bed.set_state("asleep")
	Transition.cover(2)                      # eyelids shut
	_cards.queue_free()
	_cards = null
	_asleep = true
	_zzz_loop()
	await _wait(1.2)
	if _skipped:
		return
	Audio.play_music("village", 6.0)
	await Transition.eye(1.0, 0.7, _d(1.7))   # first slow, heavy-lidded peek
	await _shot("03_peek")
	await _wait(0.7)
	await Transition.eye(0.7, 1.0, _d(0.5))
	await _wait(0.6)
	if _skipped:
		return
	await Transition.eye(1.0, 0.3, _d(1.2))
	await _wait(0.2)
	await Transition.eye(0.3, 1.0, _d(0.35))
	await _wait(0.4)
	if _skipped:
		return
	_asleep = false
	Audio.play_sfx("bed_rustle", -3.0)
	house.bed.set_state("sit")
	await Transition.eye(1.0, 0.0, _d(1.5))   # eyes fully open as he sits up
	await _shot("04_awake")
	Transition.bars(true, _d(0.8))
	await _wait(0.9)
	await _think([
		"...Mmh. Is it morning already?",
		"The lantern by my bed went out sometime in the night.",
		"That has never happened before...",
	], "05_think")


# ------------------------------------------------------------------ the diary
func _morning() -> void:
	if _skipped:
		return
	house.bed.set_state("empty")
	Audio.play_sfx("bed_rustle", -4.0)
	player.global_position = house.world_pos(house.bed_side_pos)
	player.face("down")
	player.asleep = false
	await _wait(0.9)
	await _shot("06_up")
	if _skipped:
		return
	await player.walk_to(house.world_pos(house.desk_front_pos), 42.0)
	player.face("up")
	await _wait(0.6)
	await _think(["Right. What did I write down for today?"])
	if _skipped:
		return
	if _shots != "":
		_diary.revealed.connect(func(): _shot("07_diary"), CONNECT_ONE_SHOT)
	_diary.open()
	await _diary.closed
	if _skipped:
		return
	await _wait(0.5)
	await _think([
		"The Elder wants to see me in the village square.",
		"And every lantern in Emberwick dark... I should hurry.",
	], "08_think2")


func _hand_over() -> void:
	if _skipped:
		return
	Transition.bars(false, _d(0.7))
	_finish()
	await _shot("09_free")
	await get_tree().create_timer(1.3).timeout
	await _shot("10_objective")


func _finish() -> void:
	_done = true
	main.cutscene = false
	main.music_lock = false
	get_tree().root.set_meta("intro_done", true)
	player.asleep = false
	player.locked = false
	main.hud.visible = true
	main.hud.show_objective("MEET THE ELDER IN THE VILLAGE SQUARE")


# ------------------------------------------------------------------ skipping
func skip_now() -> void:
	if _skipped or _done:
		return
	_skipped = true
	_asleep = false
	for t in _tweens:
		if t.is_valid():
			t.kill()
	Transition.stop()
	if _cards:
		_cards.queue_free()
		_cards = null
	Transition.clear()
	if _dlg:
		_dlg.force_close()
	if _diary:
		_diary.force_close()
	Transition.bars(false, 0.4)
	if not main.indoors:
		main.enter_house_instant()
	house.bed.set_state("empty")
	player.global_position = house.world_pos(house.bed_side_pos)
	player.face("down")
	Audio.play_music("village", 1.5)
	_finish()
	if OS.get_cmdline_user_args().has("--autoplay"):
		print("SKIPPED: locked=", player.locked, " indoors=", main.indoors, " cutscene=", main.cutscene, " hud=", main.hud.visible)
