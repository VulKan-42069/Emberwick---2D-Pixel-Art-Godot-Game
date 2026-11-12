## Pause menu: Resume / Diary / Options / Controls / Quit to title. Freezes the game and muffles the music.
extends CanvasLayer

const MenuList := preload("res://scripts/game/menu_list.gd")
const OptionsPanel := preload("res://scripts/game/options_panel.gd")
const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")
const BOX: Texture2D = preload("res://assets/ui/dialogue_box.png")

const CONTROLS := [
	["MOVE", "WASD / ARROWS"], ["ATTACK", "J / SPACE"], ["TALK / OPEN", "E / ENTER"],
	["DIARY", "TAB / Q"], ["PAUSE", "ESC / P"],
]

var is_open := false
var _dim: ColorRect
var _panels := {}
var _main: Control
var _options: Control
var _controls: Control
var _confirm: Control


func _ready() -> void:
	layer = 30
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_dim = ColorRect.new()
	_dim.color = Color(0.03, 0.02, 0.08, 0.0)
	_dim.size = Vector2(320, 180)
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_dim)

	_panels["main"] = _panel(Vector2(98, 30), Vector2(124, 120), "PAUSED")
	_main = MenuList.new()
	_main.position = Vector2(18, 30)
	_panels["main"].add_child(_main)
	_main.setup(["RESUME", "DIARY", "OPTIONS", "CONTROLS", "QUIT TO TITLE"])
	_main.chosen.connect(_on_main)
	_main.cancelled.connect(close)

	_panels["options"] = _panel(Vector2(60, 32), Vector2(200, 116), "OPTIONS")
	_options = OptionsPanel.new()
	_options.position = Vector2(16, 26)
	_panels["options"].add_child(_options)
	_options.closed.connect(func(): _show("main"))

	_panels["controls"] = _panel(Vector2(50, 28), Vector2(220, 124), "CONTROLS")
	for i in CONTROLS.size():
		_text(_panels["controls"], CONTROLS[i][0], Vector2(20, 28 + i * 13), Color("d9d0f2"))
		_text(_panels["controls"], CONTROLS[i][1], Vector2(110, 28 + i * 13), Color("ffc44a"))
	_controls = MenuList.new()
	_controls.position = Vector2(80, 100)
	_panels["controls"].add_child(_controls)
	_controls.setup(["BACK"])
	_controls.chosen.connect(func(_i): _show("main"))
	_controls.cancelled.connect(func(): _show("main"))

	_panels["confirm"] = _panel(Vector2(66, 46), Vector2(188, 92), "LEAVE TO THE TITLE?")
	_text(_panels["confirm"], "UNSAVED PROGRESS WILL BE LOST.", Vector2(12, 24), Color("d9d0f2"))
	_confirm = MenuList.new()
	_confirm.position = Vector2(60, 42)
	_panels["confirm"].add_child(_confirm)
	_confirm.setup(["STAY", "LEAVE"])
	_confirm.chosen.connect(func(i: int): _show("main") if i == 0 else _leave())
	_confirm.cancelled.connect(func(): _show("main"))


func _panel(pos: Vector2, size: Vector2, title: String) -> Control:
	var p := NinePatchRect.new()
	p.texture = BOX
	for side in ["left", "right", "top", "bottom"]:
		p.set("patch_margin_" + side, 8)
	p.position = pos
	p.size = size
	p.visible = false
	var l := Label.new()
	l.text = title
	l.position = Vector2(0, 8)
	l.size = Vector2(size.x, 10)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_color_override("font_color", Color("ffc44a"))
	p.add_child(l)
	add_child(p)
	return p


func _text(parent: Control, text: String, pos: Vector2, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l


func _show(name: String) -> void:
	for k in _panels:
		_panels[k].visible = k == name
	_main.active = name == "main"
	_controls.active = name == "controls"
	_confirm.active = name == "confirm"
	if name == "options":
		_options.open()


func open() -> void:
	if is_open:
		return
	is_open = true
	visible = true
	get_tree().paused = true
	Audio.play_sfx("pause_in", -2.0, 0.0)
	Audio.set_pause_filter(true)
	_dim.visible = true
	_dim.color.a = 0.0
	create_tween().tween_property(_dim, "color:a", 0.62, 0.2)
	_show("main")


func close() -> void:
	if not is_open:
		return
	is_open = false
	Audio.play_sfx("pause_out", -2.0, 0.0)
	Audio.set_pause_filter(false)
	visible = false
	get_tree().paused = false


func _on_main(i: int) -> void:
	match i:
		0: close()
		1: _open_diary()
		2: _show("options")
		3: _show("controls")
		4: _show("confirm")


func _open_diary() -> void:
	var d := get_tree().get_first_node_in_group("diary")
	if d == null or d.active:
		return
	_main.active = false
	_dim.visible = false              # the diary has its own dimming
	for k in _panels:
		_panels[k].visible = false
	d.open()
	await d.closed
	if is_open:
		_dim.visible = true
		_show("main")


func _leave() -> void:
	is_open = false
	_confirm.active = false
	Audio.set_pause_filter(false)
	Audio.stop_voice()
	get_tree().paused = false
	await Transition.dissolve_out(0.8)
	get_tree().change_scene_to_file("res://scenes/title.tscn")


## Test helper: open straight onto a sub-screen, save a screenshot and quit (main.gd stops running while paused).
func debug_show(name: String, shot_path: String = "") -> void:
	open()
	_show(name)
	if shot_path != "":
		await get_tree().create_timer(0.8, true).timeout
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()
