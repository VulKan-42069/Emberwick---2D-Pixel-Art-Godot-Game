## Autoload "Transition": full-screen transitions drawn by one shader, plus cinematic letterbox bars.
##   fade     plain fade to / from black
##   iris     pixelated circle that closes on / opens from a point (used for doors)
##   eye      an eyelid that opens and shuts (waking up)
##   dissolve ordered-dither dissolve
## progress 1.0 = screen fully covered, 0.0 = fully clear. The screen starts covered so the first frame is never a flash of game.
extends CanvasLayer

const SHADER := """
shader_type canvas_item;
uniform int mode = 0;
uniform float progress = 1.0;
uniform vec2 center = vec2(160.0, 90.0);

float bayer4(vec2 p) {
	float m[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	int idx = int(mod(p.x, 4.0)) + int(mod(p.y, 4.0)) * 4;
	return (m[idx] + 0.5) / 16.0;
}

void fragment() {
	vec2 res = vec2(320.0, 180.0);
	vec2 px = floor(UV * res);
	float a = 0.0;
	if (mode == 0) {
		a = progress;
	} else if (mode == 1) {
		vec2 q = (floor(px / 4.0) + 0.5) * 4.0;
		float maxr = length(max(center, res - center));
		a = step((1.0 - progress) * maxr, length(q - center));
	} else if (mode == 2) {
		vec2 q = (px + 0.5) / res - 0.5;
		float open = 1.0 - progress;
		float ry = max(open * 0.78, 0.0001);
		float d = (q.x / 0.85) * (q.x / 0.85) + (q.y / ry) * (q.y / ry);
		a = d > 1.0 ? 1.0 : (d > 0.8 ? step(bayer4(px), (d - 0.8) / 0.2) : 0.0);
		if (open <= 0.001) { a = 1.0; }
	} else {
		a = step(bayer4(px), progress);
	}
	COLOR = vec4(0.0, 0.0, 0.0, a);
}
"""

const BAR := 12.0

var _rect: ColorRect
var _mat: ShaderMaterial
var _tween: Tween
var _top: ColorRect
var _bottom: ColorRect
var _bar_tween: Tween


func _ready() -> void:
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	var bars := CanvasLayer.new()
	bars.layer = 8                      # above the HUD, below dialogue
	add_child(bars)
	_top = _bar(Vector2(0, -BAR))
	_bottom = _bar(Vector2(0, 180))
	bars.add_child(_top)
	bars.add_child(_bottom)
	_rect = ColorRect.new()
	_rect.size = Vector2(320, 180)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	_rect.material = _mat
	add_child(_rect)
	cover()


func _bar(pos: Vector2) -> ColorRect:
	var r := ColorRect.new()
	r.color = Color.BLACK
	r.position = pos
	r.size = Vector2(320, BAR)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


func _set_mode(mode: int, p: float) -> void:
	_mat.set_shader_parameter("mode", mode)
	_mat.set_shader_parameter("progress", p)


## Instantly cover the screen (mode 0 = black, 2 = eyelids shut).
func cover(mode: int = 0) -> void:
	stop()
	_set_mode(mode, 1.0)


func clear() -> void:
	stop()
	_set_mode(0, 0.0)


func stop() -> void:
	if _tween:
		_tween.kill()
		_tween = null


func _run(mode: int, from: float, to: float, dur: float, trans: Tween.TransitionType, ease_type: Tween.EaseType) -> void:
	stop()
	_set_mode(mode, from)
	if dur <= 0.0:
		_set_mode(mode, to)
		return
	_tween = create_tween()
	_tween.tween_method(func(v: float): _mat.set_shader_parameter("progress", v), from, to, dur).set_trans(trans).set_ease(ease_type)
	await _tween.finished


func fade_out(dur: float = 0.8) -> void:
	await _run(0, 0.0, 1.0, dur, Tween.TRANS_SINE, Tween.EASE_IN_OUT)


func fade_in(dur: float = 1.0) -> void:
	await _run(0, 1.0, 0.0, dur, Tween.TRANS_SINE, Tween.EASE_IN_OUT)


func iris_close(center: Vector2, dur: float = 0.6) -> void:
	_mat.set_shader_parameter("center", center)
	Audio.play_sfx("wipe_whoosh", -6.0, 0.02)
	await _run(1, 0.0, 1.0, dur, Tween.TRANS_QUAD, Tween.EASE_IN)


func iris_open(center: Vector2, dur: float = 0.6) -> void:
	_mat.set_shader_parameter("center", center)
	await _run(1, 1.0, 0.0, dur, Tween.TRANS_QUAD, Tween.EASE_OUT)


## Eyelids: progress 1 = shut, 0 = wide open.
func eye(from: float, to: float, dur: float) -> void:
	await _run(2, from, to, dur, Tween.TRANS_SINE, Tween.EASE_IN_OUT)


func dissolve_out(dur: float = 0.8) -> void:
	await _run(3, 0.0, 1.0, dur, Tween.TRANS_LINEAR, Tween.EASE_IN_OUT)


func dissolve_in(dur: float = 0.8) -> void:
	await _run(3, 1.0, 0.0, dur, Tween.TRANS_LINEAR, Tween.EASE_IN_OUT)


## Screen-space position (in the 320x180 viewport) of a world node, for iris centres.
func screen_pos(node: Node2D, lift: float = 10.0) -> Vector2:
	return node.get_global_transform_with_canvas().origin + Vector2(0, -lift)


## Slide the cinematic letterbox bars in or out.
func bars(show: bool, dur: float = 0.6) -> void:
	if _bar_tween:
		_bar_tween.kill()
	_bar_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_bar_tween.tween_property(_top, "position:y", 0.0 if show else -BAR, dur)
	_bar_tween.tween_property(_bottom, "position:y", 180.0 - BAR if show else 180.0, dur)
	await _bar_tween.finished
