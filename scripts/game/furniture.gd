## Furniture in the player's house. Feet-anchored like every other prop. The desk opens the diary; the rest shares a thought.
extends StaticBody2D

const SHEET: Texture2D = preload("res://assets/props/interior_props.png")

# Same rectangles as tools/gen_interior.py (RECTS).
const RECTS := {
	"bed_asleep": Rect2(0, 0, 24, 32), "bed_sit": Rect2(32, 0, 24, 32), "bed_empty": Rect2(64, 0, 24, 32),
	"desk": Rect2(96, 0, 32, 24), "hearth": Rect2(128, 0, 32, 32), "shelf": Rect2(0, 32, 32, 32),
	"rug": Rect2(32, 32, 32, 24), "table": Rect2(64, 32, 16, 16), "chair": Rect2(80, 32, 16, 16),
	"plant": Rect2(96, 32, 16, 24), "trunk": Rect2(112, 32, 16, 16),
}
# kind -> collision [size, centre relative to the feet]; no entry = walk-through
const BODY := {
	"bed": [Vector2(24, 22), Vector2(0, -11)], "desk": [Vector2(32, 12), Vector2(0, -6)],
	"hearth": [Vector2(28, 10), Vector2(0, -5)], "shelf": [Vector2(28, 10), Vector2(0, -5)],
	"table": [Vector2(12, 8), Vector2(0, -4)], "chair": [Vector2(10, 6), Vector2(0, -3)],
	"plant": [Vector2(10, 6), Vector2(0, -3)], "trunk": [Vector2(12, 8), Vector2(0, -4)],
}
const THOUGHTS := {
	"bed": ["No time to sleep in. The lanterns need me."],
	"shelf": ["Old tales of the Keepers. I know them all by heart."],
	"hearth": ["The fire still crackles. At least something here is still burning."],
	"table": ["My bedside lantern. Dark... it has never gone out before."],
	"chair": ["Not now."],
	"trunk": ["Spare wicks and lamp oil. Nothing else of use."],
	"plant": ["Even the plant looks worried."],
}

var kind := "bed"
var _sprite: Sprite2D
var _fire: AnimatedSprite2D


static func make(k: String, pos: Vector2) -> StaticBody2D:
	var f: StaticBody2D = (load("res://scripts/game/furniture.gd") as GDScript).new()
	f.kind = k
	f.position = pos
	return f


func _region_name() -> String:
	return "bed_asleep" if kind == "bed" else kind


func _ready() -> void:
	var r: Rect2 = RECTS[_region_name()]
	if kind == "hearth":
		_fire = AnimatedSprite2D.new()
		var sf := SpriteFrames.new()
		sf.remove_animation("default")
		sf.add_animation("burn")
		sf.set_animation_speed("burn", 7.0)
		for i in 4:
			var at := AtlasTexture.new()
			at.atlas = SHEET
			at.region = Rect2(r.position.x + i * 32, r.position.y, 32, 32)
			sf.add_frame("burn", at)
		_fire.sprite_frames = sf
		_fire.offset = Vector2(0, -16)
		add_child(_fire)
		_fire.play("burn")
	else:
		var at := AtlasTexture.new()
		at.atlas = SHEET
		at.region = r
		_sprite = Sprite2D.new()
		_sprite.texture = at
		_sprite.offset = Vector2(0, -r.size.y / 2.0)
		add_child(_sprite)
		if kind == "rug":
			z_index = -1
	collision_mask = 0
	if BODY.has(kind):
		collision_layer = 8
		var cs := CollisionShape2D.new()
		var rs := RectangleShape2D.new()
		rs.size = BODY[kind][0]
		cs.shape = rs
		cs.position = BODY[kind][1]
		add_child(cs)
	else:
		collision_layer = 0


## Bed only: "asleep", "sit" or "empty".
func set_state(state: String) -> void:
	(_sprite.texture as AtlasTexture).region = RECTS["bed_" + state]


func interact(_player: Node2D) -> void:
	if kind == "desk":
		var d := get_tree().get_first_node_in_group("diary")
		if d and not d.active:
			d.open()
		return
	var dlg := get_tree().get_first_node_in_group("dialogue")
	if dlg and THOUGHTS.has(kind):
		dlg.show_lines("", PackedStringArray(THOUGHTS[kind]), "", "thought")
