## Dialogue box using the 9-slice panel and the bitmap font. Locks the player while open.
## style "thought" shows the keeper's inner voice (pale blue text, tinted panel, no name).
extends CanvasLayer

signal closed

const BOX: Texture2D = preload("res://assets/ui/dialogue_box.png")
const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")
const CHARS_PER_SEC := 50.0
const NORMAL := Color("f5f0e6")
const THOUGHT := Color("a6e0f0")

var active := false
var _lines: PackedStringArray = []
var _idx := 0
var _shown := 0.0
var _opened_frame := -1
var _voice_prefix := ""
var _cps := CHARS_PER_SEC
var _blip_at := 0
var _was_locked := false
var _autoplay := false
var _auto_t := 0.0
var _panel: NinePatchRect
var _name: Label
var _text: Label


func _ready() -> void:
	add_to_group("dialogue")
	layer = 10
	_autoplay = OS.get_cmdline_user_args().has("--autoplay")
	_panel = NinePatchRect.new()
	_panel.texture = BOX
	for side in ["left", "right", "top", "bottom"]:
		_panel.set("patch_margin_" + side, 8)
	_panel.position = Vector2(8, 120)
	_panel.size = Vector2(304, 54)
	add_child(_panel)

	_name = _label(Color("ffc44a"))
	_name.position = Vector2(8, 6)
	_name.size = Vector2(280, 9)
	_panel.add_child(_name)
	_text = _label(NORMAL)
	_text.position = Vector2(8, 17)
	_text.size = Vector2(288, 30)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.add_theme_constant_override("line_spacing", 3)
	_panel.add_child(_text)
	_panel.visible = false


func _label(color: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_color_override("font_color", color)
	l.add_theme_constant_override("outline_size", 0)
	return l


func show_lines(speaker: String, lines: PackedStringArray, voice_prefix: String = "", style: String = "") -> void:
	if active or lines.is_empty():
		return
	active = true
	_lines = lines
	_voice_prefix = voice_prefix
	_idx = 0
	_opened_frame = Engine.get_process_frames()
	var thought := style == "thought"
	_name.text = speaker
	_text.add_theme_color_override("font_color", THOUGHT if thought else NORMAL)
	_panel.modulate = Color(0.74, 0.8, 1.0) if thought else Color.WHITE
	_panel.visible = true
	var p := get_tree().get_first_node_in_group("player")
	_was_locked = p != null and p.locked
	_set_player_locked(true)
	_show_line()


func _show_line() -> void:
	_text.text = _lines[_idx]
	_text.visible_characters = 0
	_shown = 0.0
	_blip_at = 0
	_auto_t = 0.0
	_cps = CHARS_PER_SEC
	var vlen := Audio.play_voice(_voice_prefix + str(_idx)) if _voice_prefix != "" else 0.0
	if vlen > 0.0:   # reveal the text in step with the spoken line
		_cps = maxf(8.0, _text.text.length() / (vlen * 0.85))


func _set_player_locked(v: bool) -> void:
	var p := get_tree().get_first_node_in_group("player")
	if p:
		p.locked = v


func _process(delta: float) -> void:
	if not active:
		return
	if _text.visible_characters < _text.text.length():
		_shown += delta * _cps
		_text.visible_characters = int(_shown)
		if _voice_prefix == "" and int(_shown) >= _blip_at:
			Audio.play_sfx("ui_blip", -8.0, 0.1)
			_blip_at = int(_shown) + 3
	elif _autoplay:
		_auto_t += delta
		if _auto_t > 0.7:
			_advance()


func _unhandled_input(event: InputEvent) -> void:
	if not active or Engine.get_process_frames() == _opened_frame:
		return
	if event.is_action_pressed("interact") or event.is_action_pressed("attack"):
		get_viewport().set_input_as_handled()
		if _text.visible_characters < _text.text.length():
			_text.visible_characters = _text.text.length()
			return
		_advance()


func _advance() -> void:
	_idx += 1
	if _idx >= _lines.size():
		_set_player_locked(_was_locked)   # restore first: whoever waits on `closed` may unlock the player right away
		_close()
	else:
		_show_line()


func _close() -> void:
	active = false
	Audio.stop_voice()
	_panel.visible = false
	closed.emit()


## Used when a cutscene is skipped: closes without touching the player's lock.
func force_close() -> void:
	if active:
		_close()
