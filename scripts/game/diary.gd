## The keeper's diary: a book that opens over a dimmed screen and is "written" line by line.
## It reads the story flags (met_elder, entered_ruin, shrine_lit) so it can be reopened later with TAB.
extends CanvasLayer

signal closed
signal revealed

const BOOK: Texture2D = preload("res://assets/ui/diary_book.png")
const BOXES: Texture2D = preload("res://assets/ui/checkbox.png")
const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")
const INK := Color("4a2c24")
const DONE_INK := Color("9a7a5a")
const HEAD := Color("7c2a3a")
const BOOK_POS := Vector2(48, 21)

var active := false
var _was_locked := false
var _revealing := false
var _can_close := false
var _autoplay := false
var _dim: ColorRect
var _book: TextureRect
var _hint: Label
var _labels: Array[Label] = []
var _reveal: Tween
var _anim: Tween
var _blink: Tween


func _ready() -> void:
	add_to_group("diary")
	process_mode = Node.PROCESS_MODE_ALWAYS    # it can be opened from the pause menu
	layer = 20
	_autoplay = OS.get_cmdline_user_args().has("--autoplay")


func _flag(name: String) -> bool:
	return bool(get_tree().root.get_meta(name, false))


func _tasks() -> Array:
	return [
		["SEE THE ELDER IN THE VILLAGE SQUARE", _flag("met_elder")],
		["FIND OUT WHY THE LANTERNS FAILED", _flag("entered_ruin")],
		["RELIGHT THE FIRST SHRINE", _flag("shrine_lit")],
	]


func _notes() -> String:
	if _flag("shrine_lit"):
		return "THE FIRST LANTERN BURNS AGAIN! THE MIST IS FADING. PERHAPS THE OTHER SHRINES CAN BE LIT TOO."
	if _flag("met_elder"):
		return "THE ELDER SAYS THE FIRST SHRINE LIES IN THE OLD RUIN, NORTH OF THE SQUARE. MIND THE SHADES."
	return "THE LANTERNS WENT DARK LAST NIGHT. THE MIST CREEPS CLOSER. THE ELDER WANTS TO SEE ME. EMBERWICK NEEDS ITS KEEPER."


func _text(parent: Control, text: String, pos: Vector2, width: float, color: Color) -> Label:
	var l := Label.new()
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART   # before text/size: a label's size is clamped to its unwrapped text
	l.custom_minimum_size = Vector2(width, 0)
	l.text = text
	l.position = pos
	l.size = Vector2(width, 9)
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_constant_override("line_spacing", 0)   # 9 px lines, aligned with the ruled page
	l.add_theme_color_override("font_color", color)
	l.visible_ratio = 0.0
	parent.add_child(l)
	_labels.append(l)
	return l


func open() -> void:
	if active:
		return
	active = true
	var p := get_tree().get_first_node_in_group("player")
	_was_locked = p != null and p.locked
	if p:
		p.locked = true
	_labels.clear()
	_build()
	Audio.play_sfx("diary_open")
	_anim = create_tween().set_parallel(true)
	_anim.tween_property(_dim, "color:a", 0.72, 0.35)
	_anim.tween_property(_book, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_anim.tween_property(_book, "position:y", BOOK_POS.y, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_anim.tween_property(_book, "modulate:a", 1.0, 0.3)
	await _anim.finished
	_write()
	await _reveal.finished
	_finish_reveal()
	if _autoplay:
		await get_tree().create_timer(1.0).timeout
		if active:
			_close()


func _build() -> void:
	_dim = ColorRect.new()
	_dim.color = Color(0, 0, 0, 0)
	_dim.size = Vector2(320, 180)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_dim)
	_book = TextureRect.new()
	_book.texture = BOOK
	_book.position = BOOK_POS + Vector2(0, 14)
	_book.size = BOOK.get_size()
	_book.pivot_offset = BOOK.get_size() / 2.0
	_book.scale = Vector2(0.06, 0.9)
	_book.modulate.a = 0.0
	add_child(_book)
	_text(_book, "TO DO TODAY", Vector2(16, 14), 90, HEAD)
	var y := 32.0
	for t in _tasks():
		var box := TextureRect.new()
		var at := AtlasTexture.new()
		at.atlas = BOXES
		at.region = Rect2(7 if t[1] else 0, 0, 7, 7)
		box.texture = at
		box.position = Vector2(16, y)
		_book.add_child(box)
		_text(_book, t[0], Vector2(27, y), 80, DONE_INK if t[1] else INK)
		y += 29.0
	_text(_book, "NOTES", Vector2(124, 14), 90, HEAD)
	_text(_book, _notes(), Vector2(124, 32), 90, INK)
	_text(_book, "- THE KEEPER", Vector2(140, 116), 70, HEAD)


func _write() -> void:
	_revealing = true
	_reveal = create_tween()
	for i in _labels.size():
		var l := _labels[i]
		if i == 4:   # turning to the right page
			_reveal.tween_callback(func(): Audio.play_sfx("page_turn", -2.0))
			_reveal.tween_interval(0.25)
		_reveal.tween_property(l, "visible_ratio", 1.0, clampf(l.text.length() * 0.028, 0.2, 2.2))


func _finish_reveal() -> void:
	if _reveal:
		_reveal.kill()
	for l in _labels:
		l.visible_ratio = 1.0
	_revealing = false
	_can_close = true
	if _hint == null:
		_hint = Label.new()
		_hint.text = "PRESS E TO CLOSE"
		_hint.add_theme_font_override("font", FONT)
		_hint.add_theme_font_size_override("font_size", 8)
		_hint.add_theme_color_override("font_color", Color("f5f0e6"))
		_hint.position = Vector2(160 - 8 * 6, 164)
		add_child(_hint)
		_blink = create_tween().set_loops()
		_blink.tween_property(_hint, "modulate:a", 0.25, 0.7)
		_blink.tween_property(_hint, "modulate:a", 1.0, 0.7)
	revealed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if not active:
		return
	if event.is_action_pressed("interact") or event.is_action_pressed("attack") or event.is_action_pressed("diary") or event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		if _revealing:
			_finish_reveal()
		elif _can_close:
			_close()


func _close() -> void:
	_can_close = false
	Audio.play_sfx("diary_close")
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_book, "scale", Vector2(0.06, 0.9), 0.3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	tw.tween_property(_book, "modulate:a", 0.0, 0.3)
	tw.tween_property(_dim, "color:a", 0.0, 0.35)
	if _hint:
		tw.tween_property(_hint, "modulate:a", 0.0, 0.2)
	await tw.finished
	_teardown()
	var p := get_tree().get_first_node_in_group("player")
	if p:
		p.locked = _was_locked
	closed.emit()


func _teardown() -> void:
	if _blink:
		_blink.kill()
		_blink = null
	for c in get_children():
		c.queue_free()
	_hint = null
	_labels.clear()
	active = false


## Used when a cutscene is skipped.
func force_close() -> void:
	if not active:
		return
	for t in [_anim, _reveal]:
		if t:
			t.kill()
	_teardown()
	closed.emit()
