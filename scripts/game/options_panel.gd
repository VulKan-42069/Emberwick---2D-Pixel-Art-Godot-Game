## Options: music / sound / voice volume (0-10, 10 = as designed) and fullscreen. Saved by the Audio autoload.
extends Control

signal closed

const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")
const ITEMS: Texture2D = preload("res://assets/items/items.png")
const NORMAL := Color("d9d0f2")
const HOT := Color("ffc44a")
const LINE := 15.0
const KINDS := ["music", "sfx", "voice"]
const NAMES := ["MUSIC", "SOUND", "VOICE", "FULLSCREEN", "BACK"]

var index := 0
var active := false
var _names: Array[Label] = []
var _segments: Array = []     # per slider row: Array[ColorRect]
var _full_value: Label
var _cursor: TextureRect
var _t := 0.0


func _ready() -> void:
	for i in NAMES.size():
		var l := _label(NAMES[i], Vector2(20, i * LINE))
		_names.append(l)
	for i in KINDS.size():
		var segs: Array[ColorRect] = []
		for k in 10:
			var r := ColorRect.new()
			r.size = Vector2(6, 7)
			r.position = Vector2(92 + k * 8, i * LINE + 1)
			r.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(r)
			segs.append(r)
		_segments.append(segs)
	_full_value = _label("OFF", Vector2(92, 3 * LINE))
	_cursor = TextureRect.new()
	var at := AtlasTexture.new()
	at.atlas = ITEMS
	at.region = Rect2(0, 0, 16, 16)
	_cursor.texture = at
	_cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_cursor)
	refresh()


func _label(text: String, pos: Vector2) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.size = Vector2(80, 11)
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_color_override("font_shadow_color", Color("1b1b2f"))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


func open() -> void:
	index = 0
	active = true
	refresh()


func refresh() -> void:
	for i in NAMES.size():
		_names[i].add_theme_color_override("font_color", HOT if i == index else NORMAL)
		_names[i].position.x = 24.0 if i == index else 20.0
	for i in KINDS.size():
		var step: int = Audio.get_step(KINDS[i])
		for k in 10:
			_segments[i][k].color = (HOT if i == index else Color("f08a2a")) if k < step else Color("3c3f55")
	_full_value.text = "ON" if Audio.fullscreen else "OFF"
	_full_value.add_theme_color_override("font_color", HOT if index == 3 else NORMAL)
	_cursor.position.y = index * LINE - 4.0


func _process(delta: float) -> void:
	_t += delta
	if _cursor:
		_cursor.position.x = -2.0 + sin(_t * 5.0) * 1.5
		_cursor.visible = active


func _adjust(dir: int) -> void:
	if index < 3:
		Audio.set_step(KINDS[index], Audio.get_step(KINDS[index]) + dir)
		Audio.play_sfx("menu_move", 0.0, 0.0)
	elif index == 3:
		Audio.set_fullscreen(not Audio.fullscreen)
		Audio.play_sfx("menu_select")
	refresh()


func _unhandled_input(event: InputEvent) -> void:
	if not active or not is_visible_in_tree():
		return
	if event.is_action_pressed("ui_down") or event.is_action_pressed("move_down"):
		index = posmod(index + 1, NAMES.size())
		Audio.play_sfx("menu_move", 0.0, 0.03)
		refresh()
	elif event.is_action_pressed("ui_up") or event.is_action_pressed("move_up"):
		index = posmod(index - 1, NAMES.size())
		Audio.play_sfx("menu_move", 0.0, 0.03)
		refresh()
	elif event.is_action_pressed("ui_left") or event.is_action_pressed("move_left"):
		_adjust(-1)
	elif event.is_action_pressed("ui_right") or event.is_action_pressed("move_right"):
		_adjust(1)
	elif event.is_action_pressed("ui_accept") or event.is_action_pressed("interact"):
		if index == 4:
			_close()
		elif index == 3:
			_adjust(1)
		else:
			_adjust(1 if Audio.get_step(KINDS[index]) < 10 else -10)   # wrap round to 0 on accept
	elif event.is_action_pressed("ui_cancel") or event.is_action_pressed("pause"):
		_close()
	else:
		return
	get_viewport().set_input_as_handled()


func _close() -> void:
	Audio.play_sfx("menu_back")
	active = false
	closed.emit()
