## A vertical menu: ember-shard cursor, highlighted entry, keyboard (W/S, arrows, Enter/E) and mouse. Used by the title and pause menus.
extends Control

signal chosen(index: int)
signal cancelled

const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")
const ITEMS: Texture2D = preload("res://assets/items/items.png")
const NORMAL := Color("d9d0f2")
const HOT := Color("ffc44a")
const OFF := Color("6a4f96")
const LINE := 15.0

var index := 0
var active := true
var _labels: Array[Label] = []
var _enabled: Array[bool] = []
var _cursor: TextureRect
var _t := 0.0


func setup(items: Array, enabled: Array = []) -> void:
	for l in _labels:
		l.queue_free()
	_labels.clear()
	_enabled.clear()
	for i in items.size():
		var l := Label.new()
		l.text = str(items[i])
		l.add_theme_font_override("font", FONT)
		l.add_theme_font_size_override("font_size", 8)
		l.add_theme_color_override("font_shadow_color", Color("1b1b2f"))
		l.add_theme_constant_override("shadow_offset_x", 1)
		l.add_theme_constant_override("shadow_offset_y", 1)
		l.position = Vector2(20, i * LINE)
		l.size = Vector2(120, 11)
		l.mouse_filter = Control.MOUSE_FILTER_STOP
		l.gui_input.connect(_on_label_input.bind(i))
		l.mouse_entered.connect(_hover.bind(i))
		add_child(l)
		_labels.append(l)
		_enabled.append(enabled.is_empty() or bool(enabled[i]))
	if _cursor == null:
		_cursor = TextureRect.new()
		var at := AtlasTexture.new()
		at.atlas = ITEMS
		at.region = Rect2(0, 0, 16, 16)
		_cursor.texture = at
		_cursor.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_cursor)
	index = 0
	while index < _enabled.size() - 1 and not _enabled[index]:
		index += 1
	_apply(false)


func _apply(animate: bool = true) -> void:
	for i in _labels.size():
		var l := _labels[i]
		l.add_theme_color_override("font_color", OFF if not _enabled[i] else HOT if i == index else NORMAL)
		var x := 24.0 if i == index else 20.0
		if animate:
			create_tween().tween_property(l, "position:x", x, 0.08).set_trans(Tween.TRANS_SINE)
		else:
			l.position.x = x
	_cursor.position.y = index * LINE - 4.0


func _process(delta: float) -> void:
	_t += delta
	if _cursor:
		_cursor.position.x = -2.0 + sin(_t * 5.0) * 1.5
		_cursor.visible = active


func _hover(i: int) -> void:
	if active and _enabled[i] and i != index:
		index = i
		Audio.play_sfx("menu_move", 0.0, 0.03)
		_apply()


func _on_label_input(event: InputEvent, i: int) -> void:
	if active and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		index = i
		_apply()
		_choose()


func _step(dir: int) -> void:
	var n := _labels.size()
	for _k in n:
		index = posmod(index + dir, n)
		if _enabled[index]:
			break
	Audio.play_sfx("menu_move", 0.0, 0.03)
	_apply()


func _choose() -> void:
	if _enabled[index]:
		Audio.play_sfx("menu_select", 0.0, 0.0)
		chosen.emit(index)


func _unhandled_input(event: InputEvent) -> void:
	if not active or not is_visible_in_tree():
		return
	if event.is_action_pressed("ui_down") or event.is_action_pressed("move_down"):
		_step(1)
	elif event.is_action_pressed("ui_up") or event.is_action_pressed("move_up"):
		_step(-1)
	elif event.is_action_pressed("ui_accept") or event.is_action_pressed("interact"):
		_choose()
	elif event.is_action_pressed("ui_cancel") or event.is_action_pressed("pause"):
		Audio.play_sfx("menu_back", 0.0, 0.0)
		cancelled.emit()
	else:
		return
	get_viewport().set_input_as_handled()
