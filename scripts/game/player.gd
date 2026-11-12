## The lantern-keeper: 4-direction movement, sword attack, interact, damage.
extends CharacterBody2D

signal hp_changed(hp: int, max_hp: int)
signal embers_changed(count: int)
signal died

const FX := preload("res://scripts/game/fx.gd")
const FRAMES: SpriteFrames = preload("res://resources/frames_player.tres")
const SPEED := 72.0
const SPRITE_OFFSET := Vector2(0, -14)  # 32x32 cell, feet bottom edge at y=30

const REACH := {
	"right": Vector2(13, -9), "left": Vector2(-13, -9), "up": Vector2(0, -22), "down": Vector2(0, 3),
}

var facing := "down"
var attacking := false
var locked := false
var asleep := false       # invisible (in bed during the intro)
var scripted := false    # a cutscene is moving the player
var dead := false
var max_hp := 6
var hp := 6
var embers := 0
var invuln := 0.0
var hurt_time := 0.0
var knock := Vector2.ZERO

var sprite: AnimatedSprite2D
var slash: AnimatedSprite2D
var hit_area: Area2D
var interact_area: Area2D


static func ensure_input() -> void:
	var keys := {
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP], "move_down": [KEY_S, KEY_DOWN],
		"attack": [KEY_J, KEY_SPACE], "interact": [KEY_E, KEY_ENTER], "diary": [KEY_TAB, KEY_Q], "pause": [KEY_ESCAPE, KEY_P],
	}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for k in keys[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = k
			InputMap.action_add_event(action, ev)


func _ready() -> void:
	ensure_input()
	add_to_group("player")
	collision_layer = 2
	collision_mask = 1 | 8
	var body := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(8, 5)
	body.shape = rect
	body.position = Vector2(0, -3)
	add_child(body)

	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = FRAMES
	sprite.offset = SPRITE_OFFSET
	add_child(sprite)
	sprite.play("idle_down")
	sprite.animation_finished.connect(_on_anim_finished)
	sprite.frame_changed.connect(_on_frame_changed)

	slash = AnimatedSprite2D.new()
	slash.sprite_frames = FX.FRAMES
	slash.offset = SPRITE_OFFSET
	slash.visible = false
	slash.z_index = 1
	add_child(slash)

	hit_area = _make_area(Vector2(16, 14), 4 | 8)
	interact_area = _make_area(Vector2(12, 12), 8)
	_aim_areas()


func _make_area(size: Vector2, mask: int) -> Area2D:
	var a := Area2D.new()
	a.collision_layer = 0
	a.collision_mask = mask
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = size
	cs.shape = r
	a.add_child(cs)
	add_child(a)
	return a


func _aim_areas() -> void:
	hit_area.position = REACH[facing]
	var cs: CollisionShape2D = hit_area.get_child(0)
	(cs.shape as RectangleShape2D).size = Vector2(14, 16) if facing in ["left", "right"] else Vector2(18, 12)
	interact_area.position = REACH[facing] * 0.8


func _dir_name(d: Vector2) -> String:
	if absf(d.x) > absf(d.y):
		return "right" if d.x > 0 else "left"
	if absf(d.y) > absf(d.x):
		return "down" if d.y > 0 else "up"
	# perfect diagonal: keep facing if it still matches an input axis
	if (facing == "left" and d.x < 0) or (facing == "right" and d.x > 0) or (facing == "up" and d.y < 0) or (facing == "down" and d.y > 0):
		return facing
	return "right" if d.x > 0 else "left"


func _process(_delta: float) -> void:
	sprite.visible = not asleep and (invuln <= 0.0 or int(invuln * 20.0) % 2 == 0)


func _physics_process(delta: float) -> void:
	if dead or scripted:
		return
	invuln = maxf(0.0, invuln - delta)
	if hurt_time > 0.0:
		hurt_time -= delta
		velocity = knock
		knock = knock.move_toward(Vector2.ZERO, 500.0 * delta)
		move_and_slide()
		return
	if attacking or locked:
		velocity = Vector2.ZERO
		if locked and not attacking:
			_play("idle_" + facing)
		return
	var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	if dir != Vector2.ZERO:
		facing = _dir_name(dir)
		velocity = dir * SPEED
		_play("walk_" + facing)
	else:
		velocity = Vector2.ZERO
		_play("idle_" + facing)
	move_and_slide()
	_aim_areas()


func _play(anim: String) -> void:
	if sprite.animation != anim:
		sprite.play(anim)


func _unhandled_input(event: InputEvent) -> void:
	if locked or dead or hurt_time > 0.0:
		return
	if event.is_action_pressed("attack") and not attacking:
		_attack()
	elif event.is_action_pressed("diary") and not attacking:
		var d := get_tree().get_first_node_in_group("diary")
		if d and not d.active:
			d.open()
	elif event.is_action_pressed("interact") and not attacking:
		for b in interact_area.get_overlapping_bodies():
			if b.has_method("interact"):
				b.interact(self)
				return


## Cutscene movement: walks to a point without collisions or input, with the walk animation.
func walk_to(target: Vector2, speed: float = 46.0) -> void:
	scripted = true
	while global_position.distance_to(target) > 1.5:
		var dir := target - global_position
		facing = _dir_name(dir)
		_play("walk_" + facing)
		global_position += dir.normalized() * minf(dir.length(), speed * get_physics_process_delta_time())
		await get_tree().physics_frame
	scripted = false
	_play("idle_" + facing)


func face(dir_name: String) -> void:
	facing = dir_name
	_play("idle_" + facing)
	_aim_areas()


func _attack() -> void:
	attacking = true
	Audio.play_sfx("sword_swing")
	_aim_areas()
	sprite.play("attack_" + facing)
	slash.visible = true
	slash.play("slash_" + facing)


func _on_frame_changed() -> void:
	if attacking and sprite.animation.begins_with("attack") and sprite.frame == 1:
		for b in hit_area.get_overlapping_bodies():
			if b.has_method("take_hit"):
				b.take_hit(1, global_position)


func _on_anim_finished() -> void:
	if sprite.animation.begins_with("attack"):
		attacking = false
		slash.visible = false
	elif sprite.animation == "death":
		died.emit()


func hurt(from: Vector2, dmg: int = 1) -> void:
	if invuln > 0.0 or dead:
		return
	hp = maxi(0, hp - dmg)
	hp_changed.emit(hp, max_hp)
	Audio.play_sfx("player_hurt")
	invuln = 1.0
	attacking = false
	slash.visible = false
	if hp <= 0:
		dead = true
		Audio.play_jingle("game_over", true)
		velocity = Vector2.ZERO
		sprite.play("death")
		return
	hurt_time = 0.22
	knock = (global_position - from).normalized() * 120.0
	sprite.play("hurt_" + facing)


func collect(kind: String) -> void:
	match kind:
		"shard":
			Audio.play_sfx("pickup_shard")
			embers += 1
			embers_changed.emit(embers)
		"heart":
			Audio.play_sfx("pickup_heart")
			hp = mini(max_hp, hp + 2)
			hp_changed.emit(hp, max_hp)
		"coin":
			Audio.play_sfx("pickup_shard")
			embers += 1
			embers_changed.emit(embers)
