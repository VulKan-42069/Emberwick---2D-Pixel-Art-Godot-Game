## Static world objects: trees, rocks, crates, breakable bushes/pots, chests, signs, lamp posts, well, pillars...
## Configure `kind` (and optionally `text`) before adding to the tree.
extends StaticBody2D

const FX := preload("res://scripts/game/fx.gd")
const Pickup := preload("res://scripts/game/pickup.gd")
const PROPS: Texture2D = preload("res://assets/props/props.png")
const VILLAGE: Texture2D = preload("res://assets/props/village_props.png")
const RUIN: Texture2D = preload("res://assets/props/ruin_props.png")
const TREE_L: Texture2D = preload("res://assets/props/tree_large.png")
const TREE_S: Texture2D = preload("res://assets/props/tree_small.png")

const IDX := {"bush": 0, "bush_berries": 1, "bush_cut": 2, "rock": 3, "rock_small": 4, "push_block": 5, "pot": 6,
	"pot_broken": 7, "chest_closed": 8, "chest_open": 9, "signpost": 10}

# kind -> [texture, region, sprite offset (feet at origin), collision size, collision pos, layer]
# layer 1 = solid world, 8 = interactable / breakable
var kind := "rock"
var text: PackedStringArray = []

var _sprite: Sprite2D
var _shape: CollisionShape2D
var _opened := false


static func make(k: String, pos: Vector2, say: PackedStringArray = []) -> StaticBody2D:
	var p: StaticBody2D = (load("res://scripts/game/prop.gd") as GDScript).new()
	p.kind = k
	p.text = say
	p.position = pos
	return p


func _region(i: int) -> Rect2:
	return Rect2((i % 8) * 16, (i / 8) * 16, 16, 16)


func _setup() -> Array:
	match kind:
		"tree_large": return [TREE_L, Rect2(0, 0, 32, 40), Vector2(0, -20), Vector2(8, 5), Vector2(0, -3), 1]
		"tree_small": return [TREE_S, Rect2(0, 0, 24, 32), Vector2(0, -16), Vector2(6, 5), Vector2(0, -3), 1]
		"well": return [VILLAGE, Rect2(0, 0, 32, 32), Vector2(0, -16), Vector2(24, 9), Vector2(0, -6), 1]
		"barrel": return [VILLAGE, Rect2(32, 0, 16, 16), Vector2(0, -8), Vector2(10, 7), Vector2(0, -4), 1]
		"crate": return [VILLAGE, Rect2(48, 0, 16, 16), Vector2(0, -8), Vector2(12, 8), Vector2(0, -4), 1]
		"pillar": return [RUIN, Rect2(0, 0, 16, 24), Vector2(0, -12), Vector2(10, 5), Vector2(0, -3), 1]
		"pillar_broken": return [RUIN, Rect2(16, 0, 16, 24), Vector2(0, -12), Vector2(10, 5), Vector2(0, -3), 1]
		"rubble": return [RUIN, Rect2(32, 0, 16, 24), Vector2(0, -12), Vector2(0, 0), Vector2(0, 0), 0]
		"rock", "rock_small", "push_block":
			return [PROPS, _region(IDX[kind]), Vector2(0, -8), Vector2(12, 8), Vector2(0, -4), 1]
		_:  # bush, bush_berries, pot, chest_closed, signpost
			return [PROPS, _region(IDX[kind]), Vector2(0, -8), Vector2(12, 8), Vector2(0, -4), 8]


func _ready() -> void:
	var s := _setup()
	var at := AtlasTexture.new()
	at.atlas = s[0]
	at.region = s[1]
	_sprite = Sprite2D.new()
	_sprite.texture = at
	_sprite.offset = s[2]
	add_child(_sprite)
	collision_layer = s[5]
	collision_mask = 0
	if s[5] != 0:
		_shape = CollisionShape2D.new()
		var r := RectangleShape2D.new()
		r.size = s[3]
		_shape.shape = r
		_shape.position = s[4]
		add_child(_shape)


func _swap(region_index: int) -> void:
	(_sprite.texture as AtlasTexture).region = _region(region_index)


func _drop(chance_shard: float, chance_heart: float) -> void:
	var roll := randf()
	if roll < chance_shard:
		Pickup.spawn(get_parent(), "shard", global_position)
	elif roll < chance_shard + chance_heart:
		Pickup.spawn(get_parent(), "heart", global_position)


func take_hit(_dmg: int, _from: Vector2) -> void:
	if kind in ["bush", "bush_berries"]:
		Audio.play_sfx("bush_cut")
		FX.spawn(get_parent(), "dust_puff", global_position)
		_swap(IDX["bush_cut"])
		kind = "bush_cut"
		_shape.set_deferred("disabled", true)
		collision_layer = 0
		_drop(0.3, 0.25)
	elif kind == "pot":
		Audio.play_sfx("pot_break")
		FX.spawn(get_parent(), "dust_puff", global_position)
		_swap(IDX["pot_broken"])
		kind = "pot_broken"
		_shape.set_deferred("disabled", true)
		collision_layer = 0
		_drop(0.4, 0.3)


func interact(player: Node2D) -> void:
	var dlg := get_tree().get_first_node_in_group("dialogue")
	if kind == "signpost" and dlg:
		dlg.show_lines("Sign", text)
	elif kind == "chest_closed" and not _opened:
		_opened = true
		Audio.play_sfx("chest_open")
		kind = "chest_open"
		_swap(IDX["chest_open"])
		# spawn on the side the player opened it from, so they are always reachable (walls can be right behind a chest)
		var away := player.global_position - global_position
		var dir := away.normalized() if away.length() > 1.0 else Vector2.DOWN
		var side := Vector2(-dir.y, dir.x)
		for i in 3:
			Pickup.spawn(get_parent(), "shard", global_position + dir * 16.0 + side * (-9.0 + i * 9.0))
		if dlg:
			dlg.show_lines("", PackedStringArray(["You found 3 ember shards!"]))
