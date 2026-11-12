## The lantern shrine. Interact to relight it - the mist recedes.
extends StaticBody2D

signal lit

const FRAMES: SpriteFrames = preload("res://resources/frames_shrine.tres")

var is_lit := false
var _sprite: AnimatedSprite2D


func _ready() -> void:
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = Vector2(22, 7)
	cs.shape = r
	cs.position = Vector2(0, -4)
	add_child(cs)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = FRAMES
	_sprite.offset = Vector2(0, -16)   # 32x32 cell, feet at the bottom edge
	add_child(_sprite)
	_sprite.play("unlit")


func interact(_player: Node2D) -> void:
	var dlg := get_tree().get_first_node_in_group("dialogue")
	if is_lit:
		if dlg:
			dlg.show_lines("", PackedStringArray(["The lantern burns warm and steady."]))
		return
	is_lit = true
	Audio.play_sfx("shrine_light")
	Audio.play_jingle("shrine_lit")
	_sprite.play("lit")
	get_tree().root.set_meta("shrine_lit", true)
	lit.emit()
	if dlg:
		dlg.show_lines("", PackedStringArray(["The lantern flares to life!", "The night-mist begins to recede."]))
