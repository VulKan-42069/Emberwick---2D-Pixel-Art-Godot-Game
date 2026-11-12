## Demo world: village in the middle, the Mistwood beyond the river (east), the old ruin to the north.
## Builds everything in code so the assets can be seen in use. Debug: pass `-- --shot=out.png [--at=x,y] [--lit] [--attack]`.
extends Node2D

const Player := preload("res://scripts/game/player.gd")
const Npc := preload("res://scripts/game/npc.gd")
const Enemy := preload("res://scripts/game/enemy.gd")
const Prop := preload("res://scripts/game/prop.gd")
const Shrine := preload("res://scripts/game/shrine.gd")
const Dialogue := preload("res://scripts/game/dialogue.gd")
const Pickup := preload("res://scripts/game/pickup.gd")
const Hud := preload("res://scripts/game/hud.gd")
const House := preload("res://scripts/game/house.gd")
const Intro := preload("res://scripts/game/intro.gd")
const Diary := preload("res://scripts/game/diary.gd")
const PauseMenu := preload("res://scripts/game/pause_menu.gd")
const MIST: Texture2D = preload("res://assets/fx/mist_overlay.png")

const W := 64
const H := 40
const T := 16
# Terrain set index == TileSet source id (see scripts/editor/build_resources.gd)
const DIRT := 0
const SAND := 1
const WATER := 2
const CLIFF := 3
const COBBLE := 4
const RUINWALL := 5
const SRC_GRASS := 10
const SRC_VILLAGE := 11
const SRC_RUIN := 12
const SRC_TORCH := 13
const HOUSE_ORIGIN := Vector2(2048, 0)       # the interior lives far from the village, in the same scene
const HOUSE_DOOR_CELL := Vector2i(14, 19)   # doorstep of the keeper's house (the western one)

var tileset: TileSet
var rng := RandomNumberGenerator.new()
var layers := {}
var world: Node2D
var player: CharacterBody2D
var shrine: StaticBody2D
var lamps: Array[AnimatedSprite2D] = []
var occupied := {}            # cells that trees/bushes must avoid
var vorder: Array = []
var mist: TextureRect
var _t := 0.0
var _zone_check := 0.0
var _frame := 0
var _shot := ""
var _debug_attack := false
var _debug_talk := false
var _debug_chest := false
var _debug_door := ""
var _diary_shot := ""
var _pause_shot := ""
var _leave_test := false
var _pause_state := "main"
var pause_menu: CanvasLayer
var first_npc: Node
var house: Node2D
var hud: CanvasLayer
var player_cam: Camera2D
var indoors := false
var music_lock := false      # a cutscene is in charge of the music
var cutscene := false
var _door_busy := false


func _ready() -> void:
	for flag in ["shrine_lit", "met_elder", "entered_ruin"]:
		get_tree().root.set_meta(flag, false)
	rng.seed = 7
	Player.ensure_input()
	tileset = load("res://resources/tileset.tres")
	var vmeta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tools/build/village_meta.json"))
	vorder = vmeta.village.order
	for n in ["ground", "sand", "dirt", "cobble", "water", "cliff", "floor", "ruinwall", "walls", "decor"]:
		var l := TileMapLayer.new()
		l.name = n
		l.tile_set = tileset
		add_child(l)
		layers[n] = l
	house = House.new()
	house.position = HOUSE_ORIGIN
	add_child(house)
	_build_terrain()
	world = Node2D.new()
	world.name = "World"
	world.y_sort_enabled = true
	add_child(world)
	_spawn_player()
	house.build(tileset, world)
	player_cam.make_current()
	_make_trigger(Vector2(HOUSE_DOOR_CELL.x * T + 8, HOUSE_DOOR_CELL.y * T + 6), Vector2(12, 6), func(): _use_door(true))
	_make_trigger(house.world_pos(house.exit_trigger_pos), Vector2(12, 8), func(): _use_door(false))
	_spawn_props()
	_spawn_npcs()
	_spawn_enemies()
	_build_ui()
	_apply_debug_args()
	if get_tree().root.get_meta("intro_done", false):
		Transition.fade_in(0.8)           # back here after a game over
	elif OS.get_cmdline_user_args().has("--skip-intro"):
		get_tree().root.set_meta("intro_done", true)
		Transition.clear()
	else:
		var intro := Intro.new()
		add_child(intro)
		intro.run(self)


# ------------------------------------------------------------------ doors and the house
func _make_trigger(pos: Vector2, size: Vector2, cb: Callable) -> void:
	var a := Area2D.new()
	a.collision_layer = 0
	a.collision_mask = 2
	a.position = pos
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = size
	cs.shape = r
	a.add_child(cs)
	a.body_entered.connect(func(b: Node): if b == player: cb.call())
	add_child(a)


func _set_indoors(v: bool) -> void:
	indoors = v
	if v:
		house.room_cam.make_current()
	else:
		player_cam.make_current()
	mist.visible = not v


## Cutscene helper: jump into the house (and its camera) while the screen is covered.
func enter_house_instant() -> void:
	_set_indoors(true)
	player.global_position = house.world_pos(house.bed_side_pos)


func _use_door(entering: bool) -> void:
	if _door_busy or cutscene:
		return
	_door_busy = true
	player.locked = true
	Audio.play_sfx("door_open", -2.0)
	await Transition.iris_close(Transition.screen_pos(player), 0.55)
	_set_indoors(entering)
	if entering:
		player.global_position = house.world_pos(house.entry_pos)
		player.face("up")
	else:
		player.global_position = Vector2(HOUSE_DOOR_CELL.x * T + 8, (HOUSE_DOOR_CELL.y + 1) * T + 8)
		player.face("down")
	await get_tree().process_frame
	await get_tree().process_frame
	Audio.play_sfx("door_close", -4.0)
	await Transition.iris_open(Transition.screen_pos(player), 0.55)
	player.locked = false
	await get_tree().create_timer(0.4).timeout
	_door_busy = false


# ------------------------------------------------------------------ terrain
func _rect(x: int, y: int, w: int, h: int) -> Dictionary:
	var d := {}
	for yy in range(y, y + h):
		for xx in range(x, x + w):
			d[Vector2i(xx, yy)] = true
	return d


func _ellipse(cx: float, cy: float, rx: float, ry: float) -> Dictionary:
	var d := {}
	for y in H:
		for x in W:
			var nx := (x + 0.5 - cx) / rx
			var ny := (y + 0.5 - cy) / ry
			if nx * nx + ny * ny <= 1.0:
				d[Vector2i(x, y)] = true
	return d


func _union(a: Dictionary, b: Dictionary) -> Dictionary:
	var d := a.duplicate()
	d.merge(b)
	return d


func _minus(a: Dictionary, b: Dictionary) -> Dictionary:
	var d := a.duplicate()
	for k in b:
		d.erase(k)
	return d


func _paint(layer: String, cells: Dictionary, terrain_set: int) -> void:
	var arr: Array[Vector2i] = []
	for c in cells:
		arr.append(c)
	(layers[layer] as TileMapLayer).set_cells_terrain_connect(arr, terrain_set, 0)
	occupied.merge(cells)


func _vcoord(tile_name: String) -> Vector2i:
	var k := vorder.find(tile_name)
	return Vector2i(k % 8, k / 8)


func _build_terrain() -> void:
	var ground: TileMapLayer = layers.ground
	for y in H:
		for x in W:
			var r := rng.randf()
			var c := Vector2i(rng.randi_range(0, 3), 0)
			if r > 0.93:
				c = Vector2i(rng.randi_range(0, 7), 1)
			elif r > 0.85:
				c = Vector2i(rng.randi_range(4, 7), 0)
			ground.set_cell(Vector2i(x, y), SRC_GRASS, c)

	var river := _minus(_rect(42, 7, 2, 33), _rect(42, 21, 2, 1))        # gap at y=21 for the bridge
	var pond := _ellipse(8, 28, 3.6, 2.8)
	var water := _union(river, pond)
	_paint("sand", _union(_union(_ellipse(8, 28, 6.5, 5.0), pond), _rect(41, 7, 4, 33)), SAND)
	var dirt := _union(_union(_rect(4, 21, 38, 2), _rect(44, 21, 18, 2)), _union(_rect(31, 10, 2, 12), _rect(14, 19, 1, 2)))
	_paint("dirt", dirt, DIRT)
	_paint("cobble", _rect(22, 17, 18, 10), COBBLE)
	_paint("water", water, WATER)
	_paint("cliff", _union(_rect(0, 0, 24, 6), _rect(40, 0, 24, 6)), CLIFF)

	# ruin: a ring of raised wall around a floor, with a 2-tile doorway in the south wall
	var ring := _minus(_minus(_rect(24, 0, 16, 10), _rect(26, 2, 12, 6)), _rect(31, 8, 2, 2))
	_paint("ruinwall", ring, RUINWALL)
	var floor_cells := _rect(24, 0, 16, 10)
	for c in floor_cells:
		var r := rng.randf()
		var f := Vector2i(0, 0) if r < 0.55 else Vector2i(1, 0) if r < 0.8 else Vector2i(2, 0) if r < 0.9 else Vector2i(3, 0)
		(layers.floor as TileMapLayer).set_cell(c, SRC_RUIN, f)
	(layers.floor as TileMapLayer).set_cell(Vector2i(36, 5), SRC_RUIN, Vector2i(7, 0))   # a pit
	occupied.merge(floor_cells)
	for t in [Vector2i(30, 9), Vector2i(33, 9), Vector2i(29, 1), Vector2i(34, 1)]:
		(layers.decor as TileMapLayer).set_cell(t, SRC_TORCH, Vector2i(0, 0))

	# bridge over the river
	for x in [42, 43]:
		(layers.decor as TileMapLayer).set_cell(Vector2i(x, 21), SRC_VILLAGE, _vcoord("bridge_h"))
	# houses
	for ox_oy in [Vector2i(24, 12), Vector2i(34, 12), Vector2i(12, 14)]:
		_house(ox_oy.x, ox_oy.y, ox_oy.y > 13)
		occupied.merge(_rect(ox_oy.x - 1, ox_oy.y, 6, 7))


func _house(ox: int, oy: int, with_fence: bool) -> void:
	var rows := [
		["roof_tl", "roof_t", "roof_t", "roof_tr"], ["roof_ml", "roof_m", "roof_chimney", "roof_mr"],
		["roof_bl", "roof_b", "roof_b", "roof_br"], ["wall_up_left", "wall_up_window", "door_top", "wall_up_right"],
		["wall_low_left", "wall_low", "door_bottom", "wall_low_right"],
	]
	for ry in rows.size():
		for rx in 4:
			(layers.walls as TileMapLayer).set_cell(Vector2i(ox + rx, oy + ry), SRC_VILLAGE, _vcoord(rows[ry][rx]))
	for x in range(ox - 1, ox + 5) if with_fence else []:   # little garden fence in front
		if x == ox + 2:
			continue
		var n := "fence_h"
		if x == ox - 1:
			n = "fence_h_left"
		elif x == ox + 4:
			n = "fence_h_right"
		(layers.walls as TileMapLayer).set_cell(Vector2i(x, oy + 6), SRC_VILLAGE, _vcoord(n))


# ------------------------------------------------------------------ entities
func _spawn_player() -> void:
	player = Player.new()
	player.position = Vector2(31 * T + 8, 25 * T)
	world.add_child(player)
	var cam := Camera2D.new()
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = W * T
	cam.limit_bottom = H * T
	cam.position_smoothing_enabled = false
	player.add_child(cam)
	player_cam = cam
	player.died.connect(func():
		await get_tree().create_timer(1.0).timeout
		await Transition.fade_out(0.9)
		get_tree().reload_current_scene())


func _prop(kind: String, px: float, py: float, say: PackedStringArray = []) -> void:
	world.add_child(Prop.make(kind, Vector2(px, py), say))


func _spawn_props() -> void:
	# village
	_prop("well", 32 * T, 24 * T)
	for p in [Vector2(23, 19), Vector2(38, 19), Vector2(23, 26), Vector2(38, 26)]:
		_lamp(p.x * T + 8, p.y * T)
	_prop("barrel", 35 * T + 8, 25 * T)
	_prop("barrel", 36 * T + 8, 25 * T + 2)
	_prop("crate", 38 * T + 8, 23 * T + 4)
	_prop("pot", 24 * T + 8, 23 * T)
	_prop("pot", 25 * T + 8, 24 * T)
	_prop("signpost", 30 * T + 8, 11 * T, PackedStringArray(["NORTH: THE OLD RUIN.", "THE FIRST LANTERN SHRINE STANDS WITHIN."]))
	_prop("signpost", 40 * T + 8, 20 * T + 8, PackedStringArray(["EAST: THE MISTWOOD.", "BEWARE OF SLIMES AND BATS!"]))
	# ruin interior
	shrine = Shrine.new()
	shrine.position = Vector2(32 * T, 5 * T + 8)
	shrine.lit.connect(_on_shrine_lit)
	world.add_child(shrine)
	_prop("pillar", 27 * T + 8, 4 * T + 12)
	_prop("pillar", 36 * T + 8, 4 * T + 12)
	_prop("pillar_broken", 35 * T + 8, 7 * T + 8)
	_prop("rubble", 28 * T, 6 * T + 8)
	_prop("chest_closed", 27 * T + 8, 6 * T + 12)
	# trees, bushes and rocks scattered over free ground
	var trees := 0
	var tries := 0
	while trees < 90 and tries < 2000:
		tries += 1
		var c := Vector2i(rng.randi_range(1, W - 2), rng.randi_range(7, H - 2))
		var forest := c.x >= 46
		if not forest and rng.randf() < 0.75:
			continue
		if _blocked(c, 2):
			continue
		occupied[c] = true
		_prop("tree_large" if rng.randf() < 0.65 else "tree_small", c.x * T + 8, c.y * T + 16)
		trees += 1
	for i in 40:
		var c := Vector2i(rng.randi_range(1, W - 2), rng.randi_range(7, H - 2))
		if _blocked(c, 1):
			continue
		occupied[c] = true
		var r := rng.randf()
		_prop("bush" if r < 0.45 else "bush_berries" if r < 0.7 else "rock" if r < 0.88 else "rock_small", c.x * T + 8, c.y * T + 16)


func _blocked(c: Vector2i, margin: int) -> bool:
	for dy in range(-margin, margin + 1):
		for dx in range(-margin, margin + 1):
			if occupied.has(c + Vector2i(dx, dy)):
				return true
	return false


func _lamp(px: float, py: float) -> void:
	var body := StaticBody2D.new()
	body.position = Vector2(px, py)
	body.collision_layer = 1
	var cs := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = Vector2(6, 4)
	cs.shape = r
	cs.position = Vector2(0, -3)
	body.add_child(cs)
	var s := AnimatedSprite2D.new()
	s.sprite_frames = load("res://resources/frames_lamp_post.tres")
	s.offset = Vector2(0, -16)
	body.add_child(s)
	s.play("unlit")
	lamps.append(s)
	world.add_child(body)


func _npc(who: String, display: String, px: float, py: float, lines: Array, after: Array, wander: float, off := Vector2(0, -12), spd := 18.0, voice := "") -> void:
	var n := Npc.new()
	n.display_name = display
	n.frames = load("res://resources/frames_%s.tres" % who)
	n.sprite_offset = off
	n.lines = PackedStringArray(lines)
	n.lines_after = PackedStringArray(after)
	n.wander_radius = wander
	n.speed = spd
	n.voice_id = voice
	n.position = Vector2(px, py)
	world.add_child(n)
	if first_npc == null:
		first_npc = n


func _spawn_npcs() -> void:
	_npc("elder", "Elder", 28 * T + 8, 21 * T, [
		"The lanterns have gone out, and the night-mist creeps closer every evening.",
		"Take your sword, lantern-keeper. Slimes and bats now roam the Mistwood to the east.",
		"The first shrine lies in the old ruin to the north. Relight it!"],
		["Look, the mist is thinning already! You have done well, lantern-keeper."], 0.0, Vector2(0, -12), 18.0, "elder")
	_npc("shopkeeper", "Shopkeeper", 37 * T + 8, 22 * T, [
		"Welcome! I have nothing to sell just yet.",
		"But bring me ember shards and we shall talk business!"],
		["Business is picking up now the lanterns are back. Thank you!"], 0.0, Vector2(0, -12), 18.0, "shopkeeper")
	_npc("child", "Child", 26 * T, 24 * T, [
		"I saw a glow in the ruin last night. Honest!",
		"Try hitting the bushes and pots. Sometimes they hide hearts."],
		["The mist is going away! Can I carry the lantern next time?"], 40.0, Vector2(0, -12), 20.0, "child")
	_npc("cat", "Cat", 33 * T, 19 * T, ["MEOW."], ["MEOW. PURR."], 48.0, Vector2(0, -8), 22.0)


func _enemy(kind: String, px: float, py: float) -> void:
	var e := Enemy.new()
	e.kind = kind
	e.position = Vector2(px, py)
	world.add_child(e)


func _spawn_enemies() -> void:
	for p in [Vector2(50, 14), Vector2(53, 28), Vector2(49, 33), Vector2(57, 17), Vector2(15, 36)]:
		_enemy("slime", p.x * T, p.y * T)
	for p in [Vector2(54, 10), Vector2(56, 24), Vector2(60, 34)]:
		_enemy("bat", p.x * T, p.y * T)
	for p in [Vector2(29, 5), Vector2(35, 5)]:
		_enemy("shade", p.x * T, p.y * T)


# ------------------------------------------------------------------ ui + mist
func _build_ui() -> void:
	var dlg := Dialogue.new()
	add_child(dlg)
	hud = Hud.new()
	add_child(hud)
	hud.bind(player)
	add_child(Diary.new())
	pause_menu = PauseMenu.new()
	add_child(pause_menu)
	var cl := CanvasLayer.new()
	cl.layer = 4
	add_child(cl)
	mist = TextureRect.new()
	mist.texture = MIST
	mist.stretch_mode = TextureRect.STRETCH_TILE
	mist.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	mist.size = Vector2(320 + 64, 180 + 64)
	mist.modulate = Color(1, 1, 1, 0.4)
	mist.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cl.add_child(mist)


func _on_shrine_lit() -> void:
	create_tween().tween_property(mist, "modulate:a", 0.0, 4.0)
	for l in lamps:
		l.play("lit")


func _process(delta: float) -> void:
	_t += delta
	_zone_check -= delta
	if _zone_check <= 0.0 and player != null:
		_zone_check = 0.4
		var tp := player.global_position / T
		var in_ruin := not indoors and tp.x >= 24 and tp.x < 40 and tp.y < 10.5
		if in_ruin:
			get_tree().root.set_meta("entered_ruin", true)
		if not music_lock:
			Audio.play_music("ruin" if in_ruin else "mistwood" if (not indoors and tp.x >= 44) else "village")
	mist.position = Vector2(-fmod(_t * 5.0, 64.0), -fmod(_t * 2.5, 64.0))
	if _leave_test:
		_frame += 1
		if _frame == 20:
			pause_menu.open()
			pause_menu._leave()
			_leave_test = false
	if _pause_shot != "":
		_frame += 1
		if _frame == 20:
			pause_menu.debug_show(_pause_state, _pause_shot)
	if _diary_shot != "":
		_frame += 1
		if _frame == 10:
			for f in ["met_elder", "entered_ruin", "shrine_lit"]:
				get_tree().root.set_meta(f, true)
			get_tree().get_first_node_in_group("diary").open()
		elif _frame == 480:
			get_viewport().get_texture().get_image().save_png(_diary_shot)
			get_tree().quit()
	if _debug_door != "":
		_frame += 1
		match _frame:
			5: player.global_position = Vector2(HOUSE_DOOR_CELL.x * T + 8, HOUSE_DOOR_CELL.y * T + 6)
			22: _grab("door_1_closing")
			60: _grab("door_2_black_or_inside")
			150: _grab("door_3_inside")
			230: player.global_position = house.world_pos(house.exit_trigger_pos)
			248: _grab("door_4_leaving")
			420:
				_grab("door_5_outside")
				print("DOOR TEST: indoors=", indoors, " player=", player.global_position, " locked=", player.locked)
				get_tree().quit()
	if _debug_chest:
		_frame += 1
		if _frame == 5:   # an item stuck in the strip against the south wall, and the chest opened from just below it
			player.global_position = Vector2(27 * T + 8, 6 * T + 12 + 10)
			Pickup.spawn(world, "shard", Vector2(27 * T + 8, 8 * T - 1))
		elif _frame == 12:
			for c in world.get_children():
				if "kind" in c and c.kind == "chest_closed":
					c.interact(player)
		elif _frame == 160:
			print("EMBERS=", player.embers)
			get_tree().quit()
	if _shot != "":
		_frame += 1
		if _debug_attack and _frame == 12:
			player._attack()
		if _debug_talk and _frame == 8:
			player.global_position = first_npc.global_position + Vector2(0, 14)
			first_npc.interact(player)
		if _frame == 30:
			var img := get_viewport().get_texture().get_image()
			img.save_png(_shot)
			get_tree().quit()


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("pause") or cutscene or _door_busy or player == null or player.dead:
		return
	for g in ["dialogue", "diary"]:
		var n := get_tree().get_first_node_in_group(g)
		if n and n.active:
			return
	pause_menu.open()
	get_viewport().set_input_as_handled()


func _press(action: String) -> void:
	for pressed in [true, false]:
		var e := InputEventAction.new()
		e.action = action
		e.pressed = pressed
		Input.parse_input_event(e)
	await get_tree().create_timer(0.25, true).timeout


## Test: drive the pause menu through the real input path.
func _key_test() -> void:
	await get_tree().create_timer(0.5, true).timeout
	await _press("pause")
	print("KEY TEST 1 pause -> open=", pause_menu.is_open, " tree.paused=", get_tree().paused)
	await _press("ui_down")
	await _press("ui_down")
	print("KEY TEST 2 two downs -> cursor on item ", pause_menu._main.index, " (2 = OPTIONS)")
	await _press("ui_up")
	await _press("ui_up")
	await _press("ui_accept")
	print("KEY TEST 3 accept on RESUME -> open=", pause_menu.is_open, " tree.paused=", get_tree().paused)
	await _press("pause")
	await _press("pause")
	print("KEY TEST 4 Esc twice -> open=", pause_menu.is_open, " tree.paused=", get_tree().paused)
	get_tree().quit()


func _grab(shot_name: String) -> void:
	get_viewport().get_texture().get_image().save_png("%s/%s.png" % [_debug_door, shot_name])


func _apply_debug_args() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shot="):
			_shot = a.substr(7)
		elif a.begins_with("--at="):
			var p := a.substr(5).split(",")
			player.global_position = Vector2(float(p[0]) * T, float(p[1]) * T)
		elif a == "--lit":
			shrine.is_lit = true
			shrine._sprite.play("lit")
			get_tree().root.set_meta("shrine_lit", true)
			mist.modulate.a = 0.0
			for l in lamps:
				l.play("lit")
		elif a == "--attack":
			_debug_attack = true
		elif a == "--talk":
			_debug_talk = true
		elif a == "--chest":
			_debug_chest = true
		elif a == "--key-test":
			_key_test()
		elif a == "--leave-test":
			_leave_test = true
		elif a.begins_with("--pause-shot="):
			_pause_shot = a.substr(13)
		elif a.begins_with("--pause-state="):
			_pause_state = a.substr(14)
		elif a.begins_with("--diary-shot="):
			_diary_shot = a.substr(13)
		elif a.begins_with("--door-shots="):
			_debug_door = a.substr(13)
			DirAccess.make_dir_recursive_absolute(_debug_door)
