## Mist slime / mist bat / shade. Wander, chase the player when close, hurt on touch.
extends CharacterBody2D

const FX := preload("res://scripts/game/fx.gd")
const Pickup := preload("res://scripts/game/pickup.gd")
const SHADOW: Texture2D = preload("res://assets/fx/shadow.png")

const CFG := {
	"slime": {"hp": 2, "speed": 20.0, "frames": "res://resources/frames_slime.tres", "offset": Vector2(0, -8), "sense": 70.0, "flying": false},
	"bat": {"hp": 1, "speed": 44.0, "frames": "res://resources/frames_bat.tres", "offset": Vector2(0, -3), "sense": 90.0, "flying": true},
	"shade": {"hp": 4, "speed": 16.0, "frames": "res://resources/frames_shade.tres", "offset": Vector2(0, -12), "sense": 80.0, "flying": false},
}

var kind := "slime"
var hp := 2
var sprite: AnimatedSprite2D
var player: Node2D
var home := Vector2.ZERO
var facing := "down"

var _cfg: Dictionary
var _hurtbox: Area2D
var _timer := 0.0
var _dir := Vector2.ZERO
var _knock := Vector2.ZERO
var _flash := 0.0
var _t := randf() * TAU


func _ready() -> void:
	_cfg = CFG[kind]
	hp = _cfg.hp
	home = global_position
	add_to_group("enemies")
	collision_layer = 4
	collision_mask = 0 if _cfg.flying else 1
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = Vector2(10, 6)
	cs.shape = r
	cs.position = Vector2(0, -3)
	add_child(cs)

	if kind == "bat":  # bats hover: little ground shadow, sprite floats above it
		var sh := Sprite2D.new()
		var at := AtlasTexture.new()
		at.atlas = SHADOW
		at.region = Rect2(0, 0, 16, 6)
		sh.texture = at
		sh.position = Vector2(0, -2)
		sh.z_index = -1
		add_child(sh)

	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = load(_cfg.frames)
	sprite.offset = _cfg.offset
	add_child(sprite)
	sprite.play(_anim())
	sprite.frame_changed.connect(_on_frame)

	_hurtbox = Area2D.new()
	_hurtbox.collision_layer = 0
	_hurtbox.collision_mask = 2
	var hs := CollisionShape2D.new()
	var hr := RectangleShape2D.new()
	hr.size = Vector2(10, 10)
	hs.shape = hr
	hs.position = Vector2(0, -6)
	_hurtbox.add_child(hs)
	add_child(_hurtbox)
	player = get_tree().get_first_node_in_group("player")


func _on_frame() -> void:
	if kind == "slime" and sprite.frame == 1:
		Audio.play_sfx_at("slime_hop", global_position, -4.0)
	elif kind == "bat" and sprite.frame == 0:
		Audio.play_sfx_at("bat_flap", global_position, -8.0)


func _anim() -> String:
	return {"slime": "hop", "bat": "fly"}.get(kind, "move_" + facing)


func _physics_process(delta: float) -> void:
	_t += delta
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(2.5, 2.5, 2.5) if _flash > 0.0 else Color.WHITE

	var to_player := Vector2.INF
	if player and not player.dead:
		to_player = player.global_position - global_position
	if to_player.length() < _cfg.sense:
		_dir = to_player.normalized()
	else:
		_timer -= delta
		if _timer <= 0.0:
			_timer = randf_range(0.8, 2.0)
			var back := home - global_position
			if back.length() > 64.0:
				_dir = back.normalized()
			else:
				_dir = Vector2.from_angle(randf() * TAU) if randf() < 0.6 else Vector2.ZERO

	var spd: float = _cfg.speed
	if kind == "slime":  # hop: only travel while airborne
		spd = spd * 2.4 if sprite.frame in [1, 2] else 0.0
	if kind == "bat":
		sprite.position.y = -14.0 + sin(_t * 6.0) * 2.0
		_dir = _dir.rotated(sin(_t * 3.0) * 0.04)

	velocity = _dir * spd + _knock
	_knock = _knock.move_toward(Vector2.ZERO, 400.0 * delta)
	move_and_slide()

	if kind == "shade" and _dir != Vector2.ZERO:
		var f := "right" if _dir.x > 0 else "left"
		if absf(_dir.y) > absf(_dir.x):
			f = "down" if _dir.y > 0 else "up"
		if f != facing:
			facing = f
			sprite.play(_anim())

	for b in _hurtbox.get_overlapping_bodies():
		if b.has_method("hurt"):
			b.hurt(global_position, 1)


func take_hit(dmg: int, from: Vector2) -> void:
	hp -= dmg
	_flash = 0.12
	_knock = (global_position - from).normalized() * 140.0
	FX.spawn(get_parent(), "hit_spark", global_position + Vector2(0, -6))
	Audio.play_sfx_at("sword_hit", global_position)
	if hp <= 0:
		Audio.play_sfx_at("enemy_die", global_position)
		FX.spawn(get_parent(), "mist_puff", global_position)
		var roll := randf()
		if roll < 0.7:
			Pickup.spawn(get_parent(), "shard", global_position)
		elif roll < 0.9:
			Pickup.spawn(get_parent(), "heart", global_position)
		queue_free()
