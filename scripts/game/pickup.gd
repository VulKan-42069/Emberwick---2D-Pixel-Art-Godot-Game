## Ember shards, hearts and coins lying on the ground.
extends Area2D

const ITEMS: Texture2D = preload("res://assets/items/items.png")
const INDEX := {"shard": 0, "heart": 1, "coin": 2, "key": 3, "potion": 4}

var kind := "shard"
var _sprite: Sprite2D
var _player: Node2D
var _t := randf() * TAU


static func spawn(parent: Node, item: String, pos: Vector2) -> Area2D:
	var p: Area2D = (load("res://scripts/game/pickup.gd") as GDScript).new()
	p.kind = item
	parent.add_child(p)
	p.global_position = pos
	return p


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2
	var cs := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = 7.0
	cs.shape = c
	cs.position = Vector2(0, -6)
	add_child(cs)
	_sprite = Sprite2D.new()
	var at := AtlasTexture.new()
	at.atlas = ITEMS
	at.region = Rect2(INDEX[kind] * 16, 0, 16, 16)
	_sprite.texture = at
	_sprite.position = Vector2(0, -8)
	add_child(_sprite)
	body_entered.connect(_on_body)
	_player = get_tree().get_first_node_in_group("player")


func _process(delta: float) -> void:
	_t += delta
	_sprite.position.y = -8.0 + sin(_t * 4.0) * 1.5
	if _player != null and not _player.dead:   # magnet: slide toward the player when close, ignoring walls
		var to: Vector2 = _player.global_position - global_position
		var d := to.length()
		if d < 30.0 and d > 1.0:
			global_position += to / d * minf(d, 80.0 * delta)


func _on_body(body: Node) -> void:
	if body.has_method("collect"):
		body.collect(kind)
		queue_free()
