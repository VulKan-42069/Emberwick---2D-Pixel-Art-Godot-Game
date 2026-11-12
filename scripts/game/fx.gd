## One-shot effect sprites (hit spark, puffs).
extends RefCounted

const FRAMES: SpriteFrames = preload("res://resources/frames_fx.tres")


static func spawn(parent: Node, anim: String, pos: Vector2, offset: Vector2 = Vector2(0, -8)) -> AnimatedSprite2D:
	var s := AnimatedSprite2D.new()
	s.sprite_frames = FRAMES
	s.offset = offset
	s.z_index = 5
	parent.add_child(s)
	s.global_position = pos
	s.play(anim)
	s.animation_finished.connect(s.queue_free)
	return s
