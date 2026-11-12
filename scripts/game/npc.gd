## Villager: idles or wanders, turns to face the player and talks.
extends CharacterBody2D

@export var display_name := "Villager"
@export var lines: PackedStringArray = []
@export var lines_after: PackedStringArray = []   # said once the shrine is lit
@export var frames: SpriteFrames
@export var sprite_offset := Vector2(0, -12)
@export var wander_radius := 0.0
@export var speed := 18.0
@export var voice_id := ""   # voice files are <voice_id>_a<line> (before the shrine) / _b<line> (after)

var facing := "down"
var talking := false
var _home := Vector2.ZERO
var _timer := 1.0
var _dir := Vector2.ZERO
var _sprite: AnimatedSprite2D


func _ready() -> void:
	_home = global_position
	collision_layer = 8
	collision_mask = 1
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = Vector2(8, 5)
	cs.shape = r
	cs.position = Vector2(0, -3)
	add_child(cs)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = frames
	_sprite.offset = sprite_offset
	add_child(_sprite)
	_sprite.play("idle_down")


func _physics_process(delta: float) -> void:
	if talking or wander_radius <= 0.0:
		velocity = Vector2.ZERO
		return
	_timer -= delta
	if _timer <= 0.0:
		_timer = randf_range(1.0, 3.0)
		var back := _home - global_position
		if back.length() > wander_radius:
			_dir = back.normalized()
		elif randf() < 0.5:
			_dir = [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN].pick_random()
		else:
			_dir = Vector2.ZERO
	velocity = _dir * speed
	move_and_slide()
	if get_slide_collision_count() > 0:
		_dir = Vector2.ZERO
	if _dir != Vector2.ZERO:
		facing = "right" if _dir.x > 0 else "left" if _dir.x < 0 else "down" if _dir.y > 0 else "up"
		_play("walk_" + facing)
	else:
		_play("idle_" + facing)


func _play(anim: String) -> void:
	if _sprite.animation != anim:
		_sprite.play(anim)


func interact(player: Node2D) -> void:
	var d := player.global_position - global_position
	facing = "right" if absf(d.x) > absf(d.y) and d.x > 0 else "left" if absf(d.x) > absf(d.y) else "down" if d.y > 0 else "up"
	talking = true
	get_tree().root.set_meta("met_" + display_name.to_lower(), true)   # story flag for the diary
	_play("idle_" + facing)
	var after: bool = get_tree().root.get_meta("shrine_lit", false) and not lines_after.is_empty()
	var say := lines_after if after else lines
	var dlg := get_tree().get_first_node_in_group("dialogue")
	if dlg:
		dlg.closed.connect(func(): talking = false, CONNECT_ONE_SHOT)
		dlg.show_lines(display_name, say, "" if voice_id == "" else voice_id + ("_b" if after else "_a"))
