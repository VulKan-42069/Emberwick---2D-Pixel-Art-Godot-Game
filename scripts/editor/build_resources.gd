## Builds the TileSet and every SpriteFrames resource from the generated sheets.
## Run: Godot --headless --path <project> --script res://scripts/editor/build_resources.gd
extends SceneTree

const T := 16
const META := "res://tools/build/"

# Our blob bit flags -> Godot peering bits (clockwise from north).
const BITS := {
	1: TileSet.CELL_NEIGHBOR_TOP_SIDE,
	2: TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER,
	4: TileSet.CELL_NEIGHBOR_RIGHT_SIDE,
	8: TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER,
	16: TileSet.CELL_NEIGHBOR_BOTTOM_SIDE,
	32: TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER,
	64: TileSet.CELL_NEIGHBOR_LEFT_SIDE,
	128: TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER,
}

# Terrain set index == position in this list (main.gd relies on it).
const OVERLAYS := ["dirt", "sand", "water", "cliff", "cobble", "ruin_wall"]
const BLOCKING := ["water", "cliff", "ruin_wall"]
const COLORS := {
	"dirt": Color("a8693c"), "sand": Color("e6c987"), "water": Color("2e72a8"),
	"cliff": Color("646a80"), "cobble": Color("9ba0b3"), "ruin_wall": Color("3c3f55"),
}


func _init() -> void:
	DirAccess.make_dir_recursive_absolute("res://resources")
	_build_tileset()
	_build_frames()
	print("resources built")
	quit()


func _json(path: String) -> Variant:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _tex(path: String) -> Texture2D:
	return load(path) as Texture2D


func _full_tile_collision(td: TileData) -> void:
	td.add_collision_polygon(0)
	td.set_collision_polygon_points(0, 0, PackedVector2Array([Vector2(-8, -8), Vector2(8, -8), Vector2(8, 8), Vector2(-8, 8)]))


# ------------------------------------------------------------------ tileset
func _build_tileset() -> void:
	var meta: Dictionary = _json(META + "terrain_meta.json")
	var ts := TileSet.new()
	ts.tile_size = Vector2i(T, T)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(0, 1)
	ts.set_physics_layer_collision_mask(0, 0)

	for i in OVERLAYS.size():
		var name: String = OVERLAYS[i]
		ts.add_terrain_set()
		ts.set_terrain_set_mode(i, TileSet.TERRAIN_MODE_MATCH_CORNERS_AND_SIDES)
		ts.add_terrain(i)
		ts.set_terrain_name(i, 0, name)
		ts.set_terrain_color(i, 0, COLORS[name])

		var src := TileSetAtlasSource.new()
		src.texture = _tex("res://assets/tilesets/terrain_%s.png" % name)
		src.texture_region_size = Vector2i(T, T)
		ts.add_source(src, i)                                  # source id == terrain set index
		var water: bool = name == "water"
		for k in 47:
			var c := Vector2i(int(meta.atlas[name][k][0]), int(meta.atlas[name][k][1]))
			src.create_tile(c)
			if water:
				src.set_tile_animation_columns(c, 4)
				src.set_tile_animation_frames_count(c, int(meta.water_frames))
				for f in int(meta.water_frames):
					src.set_tile_animation_frame_duration(c, f, 0.2)
			var td := src.get_tile_data(c, 0)
			td.terrain_set = i
			td.terrain = 0
			var bits: int = int(meta.blob_bits[k])
			for flag in BITS:
				if bits & flag:
					td.set_terrain_peering_bit(BITS[flag], 0)
			if name in BLOCKING:
				_full_tile_collision(td)

	# plain grass variants (source 10): 8x2 grid, flowers rarer than plain grass
	var grass := TileSetAtlasSource.new()
	grass.texture = _tex("res://assets/tilesets/terrain_grass.png")
	grass.texture_region_size = Vector2i(T, T)
	ts.add_source(grass, 10)
	for y in 2:
		for x in 8:
			grass.create_tile(Vector2i(x, y))
			grass.get_tile_data(Vector2i(x, y), 0).probability = 1.0 if (y == 0 and x < 4) else 0.15

	# village pieces (source 11)
	var vmeta: Dictionary = _json(META + "village_meta.json")
	var village := TileSetAtlasSource.new()
	village.texture = _tex("res://assets/tilesets/village.png")
	village.texture_region_size = Vector2i(T, T)
	ts.add_source(village, 11)
	var vorder: Array = vmeta.village.order
	for k in vorder.size():
		var c := Vector2i(k % 8, k / 8)
		village.create_tile(c)
		if not str(vorder[k]).begins_with("bridge"):
			_full_tile_collision(village.get_tile_data(c, 0))

	# ruin pieces (source 12): walls block, floors/stairs/pit/doorway don't
	var ruin := TileSetAtlasSource.new()
	ruin.texture = _tex("res://assets/tilesets/ruin.png")
	ruin.texture_region_size = Vector2i(T, T)
	ts.add_source(ruin, 12)
	var rorder: Array = vmeta.ruin.order
	for k in rorder.size():
		var c := Vector2i(k % 8, k / 8)
		ruin.create_tile(c)
		if str(rorder[k]) == "wall_cracked":
			_full_tile_collision(ruin.get_tile_data(c, 0))

	# animated wall torch (source 13)
	var torch := TileSetAtlasSource.new()
	torch.texture = _tex("res://assets/tilesets/torch.png")
	torch.texture_region_size = Vector2i(T, T)
	ts.add_source(torch, 13)
	torch.create_tile(Vector2i(0, 0))
	torch.set_tile_animation_columns(Vector2i(0, 0), 4)
	torch.set_tile_animation_frames_count(Vector2i(0, 0), 4)
	for f in 4:
		torch.set_tile_animation_frame_duration(Vector2i(0, 0), f, 0.14)

	# interior of the player's house (source 14): everything except floors and the doorway blocks movement
	var imeta: Dictionary = _json(META + "interior_meta.json")
	var interior := TileSetAtlasSource.new()
	interior.texture = _tex("res://assets/tilesets/interior.png")
	interior.texture_region_size = Vector2i(T, T)
	ts.add_source(interior, 14)
	var iorder: Array = imeta.tiles.order
	for k in iorder.size():
		var c := Vector2i(k % 8, k / 8)
		interior.create_tile(c)
		var nm := str(iorder[k])
		if not nm.begins_with("floor") and nm != "door_exit":
			_full_tile_collision(interior.get_tile_data(c, 0))

	var err := ResourceSaver.save(ts, "res://resources/tileset.tres")
	print("tileset saved: ", err)


# ------------------------------------------------------------------ sprite frames
func _add_anim(sf: SpriteFrames, anim: String, tex: Texture2D, cell: Vector2i, row: int, count: int, fps: float, loop: bool, x0: int = 0) -> void:
	sf.add_animation(anim)
	sf.set_animation_speed(anim, fps)
	sf.set_animation_loop(anim, loop)
	for i in count:
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2(x0 + i * cell.x, row * cell.y, cell.x, cell.y)
		sf.add_frame(anim, at)


func _new_frames() -> SpriteFrames:
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	return sf


func _save(sf: SpriteFrames, name: String) -> void:
	print("frames ", name, ": ", ResourceSaver.save(sf, "res://resources/frames_%s.tres" % name))


func _build_frames() -> void:
	# player
	var pm: Dictionary = _json(META + "player_meta.json")
	var ptex := _tex("res://assets/characters/player.png")
	var psf := _new_frames()
	for anim in pm.animations:
		var a: Dictionary = pm.animations[anim]
		_add_anim(psf, anim, ptex, Vector2i(32, 32), int(a.row), int(a.frames), float(a.fps), bool(a.loop))
	_save(psf, "player")

	# npcs + cat
	var nm: Dictionary = _json(META + "npc_meta.json")
	for who in nm:
		var info: Dictionary = nm[who]
		var cell := Vector2i(int(info.cell[0]), int(info.cell[1]))
		var tex := _tex("res://assets/characters/%s.png" % who)
		var sf := _new_frames()
		for anim in info.animations:
			var a: Dictionary = info.animations[anim]
			_add_anim(sf, anim, tex, cell, int(a.row), int(a.frames), float(a.fps), true)
		_save(sf, who)

	# enemies
	var em: Dictionary = _json(META + "enemy_meta.json")
	var slime := _new_frames()
	_add_anim(slime, "hop", _tex("res://assets/enemies/slime.png"), Vector2i(16, 16), 0, 4, float(em.slime.fps), true)
	_save(slime, "slime")
	var bat := _new_frames()
	_add_anim(bat, "fly", _tex("res://assets/enemies/bat.png"), Vector2i(16, 16), 0, 4, float(em.bat.fps), true)
	_save(bat, "bat")
	var shade := _new_frames()
	var rows: Array = em.shade.rows
	for r in rows.size():
		_add_anim(shade, "move_%s" % rows[r], _tex("res://assets/enemies/shade.png"), Vector2i(16, 24), r, 4, float(em.shade.fps), true)
	_save(shade, "shade")

	# effects (one resource, many animations)
	var fx := _new_frames()
	var dirs := ["down", "up", "left", "right"]
	for r in dirs.size():
		_add_anim(fx, "slash_%s" % dirs[r], _tex("res://assets/fx/slash.png"), Vector2i(32, 32), r, 3, 14.0, false)
	_add_anim(fx, "hit_spark", _tex("res://assets/fx/hit_spark.png"), Vector2i(16, 16), 0, 3, 16.0, false)
	_add_anim(fx, "dust_puff", _tex("res://assets/fx/dust_puff.png"), Vector2i(16, 16), 0, 4, 10.0, false)
	_add_anim(fx, "mist_puff", _tex("res://assets/fx/mist_puff.png"), Vector2i(16, 16), 0, 4, 10.0, false)
	_save(fx, "fx")

	# lantern shrine and village lamp post
	var shrine := _new_frames()
	var stex := _tex("res://assets/props/shrine.png")
	_add_anim(shrine, "unlit", stex, Vector2i(32, 32), 0, 1, 1.0, false)
	_add_anim(shrine, "lit", stex, Vector2i(32, 32), 0, 4, 6.0, true, 32)
	_save(shrine, "shrine")
	var lamp := _new_frames()
	var ltex := _tex("res://assets/props/village_props.png")
	_add_anim(lamp, "unlit", ltex, Vector2i(16, 32), 0, 1, 1.0, false, 64)
	_add_anim(lamp, "lit", ltex, Vector2i(16, 32), 0, 2, 5.0, true, 80)
	_save(lamp, "lamp_post")
