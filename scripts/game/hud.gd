## Hearts, ember counter and a controls hint.
extends CanvasLayer

const HEARTS: Texture2D = preload("res://assets/ui/hearts.png")
const ITEMS: Texture2D = preload("res://assets/items/items.png")
const FONT: Font = preload("res://assets/ui/font/emberwick_font.fnt")

var _hearts: Array[TextureRect] = []
var _count: Label


func _ready() -> void:
	layer = 5


func bind(player: Node) -> void:
	for i in 3:
		var tr := TextureRect.new()
		tr.position = Vector2(6 + i * 13, 5)
		tr.size = Vector2(12, 11)
		add_child(tr)
		_hearts.append(tr)
	var ico := TextureRect.new()
	var at := AtlasTexture.new()
	at.atlas = ITEMS
	at.region = Rect2(0, 0, 16, 16)
	ico.texture = at
	ico.position = Vector2(3, 17)
	add_child(ico)
	_count = _make_label("0")
	_count.position = Vector2(20, 22)
	add_child(_count)
	for row in [["WASD MOVE  J ATTACK  E TALK", 5], ["TAB DIARY  ESC PAUSE", 14]]:
		var hint := _make_label(row[0])
		hint.position = Vector2(320 - 6 - hint.text.length() * 6, row[1])
		hint.modulate = Color(1, 1, 1, 0.7)
		add_child(hint)
	player.hp_changed.connect(_on_hp)
	player.embers_changed.connect(func(n: int): _count.text = str(n))
	_on_hp(player.hp, player.max_hp)


## Banner at the top of the screen: a new goal.
func show_objective(text: String) -> void:
	var box := ColorRect.new()
	box.color = Color(0.1, 0.1, 0.18, 0.78)
	var w := text.length() * 6 + 16
	box.size = Vector2(w, 24)
	box.position = Vector2((320 - w) / 2.0, 26)
	box.modulate.a = 0.0
	add_child(box)
	var head := _make_label("NEW OBJECTIVE")
	head.position = Vector2(8, 3)
	head.add_theme_color_override("font_color", Color("ffc44a"))
	box.add_child(head)
	var body := _make_label(text)
	body.position = Vector2(8, 13)
	box.add_child(body)
	var tw := create_tween()
	tw.tween_property(box, "modulate:a", 1.0, 0.6)
	tw.tween_interval(5.0)
	tw.tween_property(box, "modulate:a", 0.0, 1.0)
	tw.tween_callback(box.queue_free)


func _make_label(t: String) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", FONT)
	l.add_theme_font_size_override("font_size", 8)
	l.add_theme_color_override("font_color", Color("f5f0e6"))
	l.add_theme_color_override("font_shadow_color", Color("1b1b2f"))
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	return l


func _on_hp(hp: int, max_hp: int) -> void:
	for i in _hearts.size():
		var state := 2   # empty
		if hp >= (i + 1) * 2:
			state = 0
		elif hp == i * 2 + 1:
			state = 1
		var at := AtlasTexture.new()
		at.atlas = HEARTS
		at.region = Rect2(state * 12, 0, 12, 11)
		_hearts[i].texture = at
