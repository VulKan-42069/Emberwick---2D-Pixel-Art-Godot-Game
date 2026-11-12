## The keeper's house (interior). Built in code at a far-away origin of the main scene; the camera switches to `room_cam` indoors.
## Layout (local pixels, room is 16 x 10 tiles): back wall rows 0-1, floor rows 2-8, south wall row 9 with the doorway at tile 7.
extends Node2D

const T := 16
const COLS := 16
const ROWS := 10
const SRC := 14
const DOOR_TILE := 7
const Furniture := preload("res://scripts/game/furniture.gd")
const SHAFT: Texture2D = preload("res://assets/fx/light_shaft.png")
const ORDER := ["floor_a", "floor_b", "floor_c", "wall_plain", "wall_window", "wall_wains", "side_left", "side_right", "bottom_band", "door_exit"]

var room_cam: Camera2D
var bed: StaticBody2D
var desk: StaticBody2D
var bed_side_pos := Vector2(64, 74)      # where the keeper stands after getting up
var desk_front_pos := Vector2(168, 72)   # in front of the desk
var entry_pos := Vector2(DOOR_TILE * T + 8, 8 * T + 12)
var exit_trigger_pos := Vector2(DOOR_TILE * T + 8, 9 * T + 8)


func world_pos(local: Vector2) -> Vector2:
	return global_position + local


func _atlas(name: String) -> Vector2i:
	var k := ORDER.find(name)
	return Vector2i(k % 8, k / 8)


func build(tileset: TileSet, world: Node2D) -> void:
	var layer := TileMapLayer.new()
	layer.tile_set = tileset
	add_child(layer)
	var rng := RandomNumberGenerator.new()
	rng.seed = 4
	for y in ROWS:
		for x in COLS:
			var n := ""
			if x == 0:
				n = "side_left"
			elif x == COLS - 1:
				n = "side_right"
			elif y == 0:
				n = "wall_window" if x in [5, 9] else "wall_plain"
			elif y == 1:
				n = "wall_wains"
			elif y == ROWS - 1:
				n = "door_exit" if x == DOOR_TILE else "bottom_band"
			else:
				n = ["floor_a", "floor_a", "floor_a", "floor_b", "floor_c"][rng.randi() % 5]
			layer.set_cell(Vector2i(x, y), SRC, _atlas(n))

	# morning light falling from the two windows, with a few drifting dust motes
	for wx in [5, 9]:
		var s := Sprite2D.new()
		s.texture = SHAFT
		s.centered = false
		s.position = Vector2(wx * T - 4, 2 * T - 4)
		add_child(s)
		var pulse := create_tween().set_loops()
		pulse.tween_property(s, "modulate:a", 0.55, 3.0).set_trans(Tween.TRANS_SINE)
		pulse.tween_property(s, "modulate:a", 1.0, 3.0).set_trans(Tween.TRANS_SINE)
		var dust := CPUParticles2D.new()
		dust.position = Vector2(wx * T + 12, 3 * T + 8)
		dust.amount = 7
		dust.lifetime = 5.0
		dust.preprocess = 5.0
		dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		dust.emission_rect_extents = Vector2(9, 16)
		dust.direction = Vector2(0.4, 1)
		dust.spread = 30.0
		dust.initial_velocity_min = 1.0
		dust.initial_velocity_max = 3.0
		dust.gravity = Vector2.ZERO
		dust.color = Color(1, 0.94, 0.63, 0.55)
		add_child(dust)

	# furniture, feet-anchored (back-wall pieces sit just under the wall)
	_place(world, "rug", Vector2(128, 132))
	bed = _place(world, "bed", Vector2(44, 64))
	_place(world, "table", Vector2(68, 48))
	_place(world, "hearth", Vector2(120, 64))
	desk = _place(world, "desk", Vector2(160, 56))
	_place(world, "chair", Vector2(138, 74))
	_place(world, "shelf", Vector2(212, 64))
	_place(world, "plant", Vector2(220, 114))
	_place(world, "trunk", Vector2(28, 132))

	# a plug just outside the doorway so nobody can wander into the void
	var plug := StaticBody2D.new()
	plug.collision_layer = 1
	plug.position = global_position + Vector2(DOOR_TILE * T + 8, ROWS * T + 2)
	var cs := CollisionShape2D.new()
	var rs := RectangleShape2D.new()
	rs.size = Vector2(16, 4)
	cs.shape = rs
	plug.add_child(cs)
	world.add_child(plug)

	room_cam = Camera2D.new()
	room_cam.position = Vector2(COLS * T / 2.0, ROWS * T / 2.0)
	room_cam.position_smoothing_enabled = false
	add_child(room_cam)


func _place(world: Node2D, kind: String, local: Vector2) -> StaticBody2D:
	var f := Furniture.make(kind, global_position + local)
	world.add_child(f)
	return f
