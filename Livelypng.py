import obspython as obs

# ============================================================
# CONFIG
# ============================================================
SOURCE_NAME = "vtuber"
TILT_ANGLE  = 6.0
DURATION    = 0.25

BEZIER_X1 = 0.34
BEZIER_Y1 = 0.12
BEZIER_X2 = 0.09
BEZIER_Y2 = 0.98

SHIFT_DROP = 20.0
CTRL_DROP  = 80.0
# ============================================================

tilted_sceneitem = None
base_rotation  = 0.0
base_pos_x     = 0.0
base_pos_y     = 0.0

# --- Tilt animation state ---
target_tilt    = 0.0
current_tilt   = 0.0
anim_start_tilt = 0.0
is_tilt_animating = False
anim_tilt_start_time = 0.0

# --- Drop animation state ---
target_drop    = 0.0
current_drop   = 0.0
anim_start_drop = 0.0
is_drop_animating = False
anim_drop_start_time = 0.0

keys_held = {'a': False, 'd': False, 'shift': False, 'ctrl': False}

# ============================================================
# EASING
# ============================================================

def cubic_bezier(t, p0, p1, p2, p3):
    u = t
    for _ in range(8):
        x  = 3*(1-u)*(1-u)*u*p0 + 3*(1-u)*u*u*p2 + u*u*u
        dx = 3*(1-u)*(1-u)*p0 + 6*(1-u)*u*(p2-p0) + 3*u*u*(1-p2)
        if abs(dx) < 1e-6:
            break
        u = u - (x - t) / dx
        u = max(0.0, min(1.0, u))
    y = 3*(1-u)*(1-u)*u*p1 + 3*(1-u)*u*u*p3 + u*u*u
    return y

def ease_value(t):
    return cubic_bezier(t, BEZIER_X1, BEZIER_Y1, BEZIER_X2, BEZIER_Y2)

# ============================================================
# SCENE ITEM HELPERS
# ============================================================

def get_sceneitem(name):
    scene_as_source = obs.obs_frontend_get_current_scene()
    if not scene_as_source:
        return None
    scene = obs.obs_scene_from_source(scene_as_source)
    item = obs.obs_scene_find_source_recursive(scene, name)
    obs.obs_source_release(scene_as_source)
    return item

# ============================================================
# TILT / DROP LOGIC
# ============================================================

def resolve_tilt():
    a = keys_held['a']
    d = keys_held['d']
    if a and d:
        return 0.0
    elif a:
        return -TILT_ANGLE
    elif d:
        return TILT_ANGLE
    else:
        return 0.0

def resolve_drop():
    if keys_held['ctrl']:
        return CTRL_DROP
    elif keys_held['shift']:
        return SHIFT_DROP
    else:
        return 0.0

def find_and_cache_item():
    global tilted_sceneitem, base_rotation, base_pos_x, base_pos_y
    item = get_sceneitem(SOURCE_NAME)
    if item:
        tilted_sceneitem = item
        base_rotation = obs.obs_sceneitem_get_rot(item)
        pos = obs.vec2()
        obs.obs_sceneitem_get_pos(item, pos)
        base_pos_x = pos.x
        base_pos_y = pos.y
    return item is not None

def start_tilt_animation(to_tilt):
    global target_tilt, anim_start_tilt, anim_tilt_start_time, is_tilt_animating
    target_tilt = to_tilt
    anim_start_tilt = current_tilt
    anim_tilt_start_time = obs.obs_get_video_frame_time() / 1000000000.0
    is_tilt_animating = True

def start_drop_animation(to_drop):
    global target_drop, anim_start_drop, anim_drop_start_time, is_drop_animating
    target_drop = to_drop
    anim_start_drop = current_drop
    anim_drop_start_time = obs.obs_get_video_frame_time() / 1000000000.0
    is_drop_animating = True

# ============================================================
# OBS CALLBACKS
# ============================================================

def script_tick(seconds):
    global current_tilt, current_drop, is_tilt_animating, is_drop_animating

    if tilted_sceneitem is None:
        if not find_and_cache_item():
            is_tilt_animating = False
            is_drop_animating = False
            return

    now = obs.obs_get_video_frame_time() / 1000000000.0

    # --- Tilt ---
    if is_tilt_animating:
        elapsed = now - anim_tilt_start_time
        progress = min(elapsed / DURATION, 1.0)
        eased = ease_value(progress)
        current_tilt = anim_start_tilt + (target_tilt - anim_start_tilt) * eased
        if progress >= 1.0:
            is_tilt_animating = False
            current_tilt = target_tilt

    # --- Drop ---
    if is_drop_animating:
        elapsed = now - anim_drop_start_time
        progress = min(elapsed / DURATION, 1.0)
        eased = ease_value(progress)
        current_drop = anim_start_drop + (target_drop - anim_start_drop) * eased
        if progress >= 1.0:
            is_drop_animating = False
            current_drop = target_drop

    # Apply both every frame
    obs.obs_sceneitem_set_rot(tilted_sceneitem, base_rotation + current_tilt)
    new_pos = obs.vec2()
    obs.vec2_set(new_pos, base_pos_x, base_pos_y + current_drop)
    obs.obs_sceneitem_set_pos(tilted_sceneitem, new_pos)

def tilt_left(pressed):
    keys_held['a'] = pressed
    start_tilt_animation(resolve_tilt())

def tilt_right(pressed):
    keys_held['d'] = pressed
    start_tilt_animation(resolve_tilt())

def drop_shift(pressed):
    keys_held['shift'] = pressed
    start_drop_animation(resolve_drop())

def drop_ctrl(pressed):
    keys_held['ctrl'] = pressed
    start_drop_animation(resolve_drop())

def restore():
    global tilted_sceneitem, current_tilt, current_drop
    global target_tilt, target_drop, is_tilt_animating, is_drop_animating
    keys_held['a'] = False
    keys_held['d'] = False
    keys_held['shift'] = False
    keys_held['ctrl'] = False
    target_tilt = 0.0
    target_drop = 0.0
    current_tilt = 0.0
    current_drop = 0.0
    is_tilt_animating = False
    is_drop_animating = False
    if tilted_sceneitem:
        obs.obs_sceneitem_set_rot(tilted_sceneitem, base_rotation)
        pos = obs.vec2()
        obs.vec2_set(pos, base_pos_x, base_pos_y)
        obs.obs_sceneitem_set_pos(tilted_sceneitem, pos)
    tilted_sceneitem = None

hotkey_a = None
hotkey_d = None
hotkey_shift = None
hotkey_ctrl = None

def script_description():
    return "<h2>LivelyPNG</h2><p>Configura las variables abajo y recarga el script para aplicar cambios.</p>"

def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "source_name", SOURCE_NAME)
    obs.obs_data_set_default_double(settings, "tilt_angle",  TILT_ANGLE)
    obs.obs_data_set_default_double(settings, "duration_ms", DURATION * 1000)
    obs.obs_data_set_default_double(settings, "shift_drop",  SHIFT_DROP)
    obs.obs_data_set_default_double(settings, "ctrl_drop",   CTRL_DROP)
    obs.obs_data_set_default_double(settings, "bezier_x1",   BEZIER_X1)
    obs.obs_data_set_default_double(settings, "bezier_y1",   BEZIER_Y1)
    obs.obs_data_set_default_double(settings, "bezier_x2",   BEZIER_X2)
    obs.obs_data_set_default_double(settings, "bezier_y2",   BEZIER_Y2)

def script_properties():
    props = obs.obs_properties_create()

    # --- General ---
    obs.obs_properties_add_text(
        props, "source_name", "Nombre del source", obs.OBS_TEXT_DEFAULT)

    obs.obs_properties_add_float_slider(
        props, "tilt_angle", "Ángulo de tilt (°)", 0.0, 45.0, 0.5)

    obs.obs_properties_add_float_slider(
        props, "duration_ms", "Duración animación (ms)", 50.0, 1000.0, 10.0)

    # --- Drop ---
    grp_drop = obs.obs_properties_create()
    obs.obs_properties_add_float_slider(
        grp_drop, "shift_drop", "Drop con Shift (px)", 0.0, 300.0, 1.0)
    obs.obs_properties_add_float_slider(
        grp_drop, "ctrl_drop",  "Drop con Ctrl (px)",  0.0, 300.0, 1.0)
    obs.obs_properties_add_group(
        props, "drop_group", "Drop vertical", obs.OBS_GROUP_NORMAL, grp_drop)

    # --- Bezier ---
    grp_bez = obs.obs_properties_create()
    obs.obs_properties_add_float_slider(grp_bez, "bezier_x1", "X1", 0.0, 1.0, 0.01)
    obs.obs_properties_add_float_slider(grp_bez, "bezier_y1", "Y1", 0.0, 1.0, 0.01)
    obs.obs_properties_add_float_slider(grp_bez, "bezier_x2", "X2", 0.0, 1.0, 0.01)
    obs.obs_properties_add_float_slider(grp_bez, "bezier_y2", "Y2", 0.0, 1.0, 0.01)
    obs.obs_properties_add_group(
        props, "bezier_group", "Curva Bezier (easing)", obs.OBS_GROUP_NORMAL, grp_bez)

    return props

def script_update(settings):
    global SOURCE_NAME, TILT_ANGLE, DURATION
    global SHIFT_DROP, CTRL_DROP
    global BEZIER_X1, BEZIER_Y1, BEZIER_X2, BEZIER_Y2

    SOURCE_NAME = obs.obs_data_get_string(settings, "source_name")
    TILT_ANGLE  = obs.obs_data_get_double(settings, "tilt_angle")
    DURATION    = obs.obs_data_get_double(settings, "duration_ms") / 1000.0
    SHIFT_DROP  = obs.obs_data_get_double(settings, "shift_drop")
    CTRL_DROP   = obs.obs_data_get_double(settings, "ctrl_drop")
    BEZIER_X1   = obs.obs_data_get_double(settings, "bezier_x1")
    BEZIER_Y1   = obs.obs_data_get_double(settings, "bezier_y1")
    BEZIER_X2   = obs.obs_data_get_double(settings, "bezier_x2")
    BEZIER_Y2   = obs.obs_data_get_double(settings, "bezier_y2")

def script_load(settings):
    global hotkey_a, hotkey_d, hotkey_shift, hotkey_ctrl
    hotkey_a = obs.obs_hotkey_register_frontend("smooth_tilt_left", "Smooth Tilt Left (A)", tilt_left)
    hotkey_d = obs.obs_hotkey_register_frontend("smooth_tilt_right", "Smooth Tilt Right (D)", tilt_right)
    hotkey_shift = obs.obs_hotkey_register_frontend("smooth_drop_shift", "Smooth Drop (Shift)", drop_shift)
    hotkey_ctrl = obs.obs_hotkey_register_frontend("smooth_drop_ctrl", "Smooth Drop Heavy (Ctrl)", drop_ctrl)

    a_array = obs.obs_data_get_array(settings, "tilt_a_hotkey")
    d_array = obs.obs_data_get_array(settings, "tilt_d_hotkey")
    shift_array = obs.obs_data_get_array(settings, "tilt_shift_hotkey")
    ctrl_array = obs.obs_data_get_array(settings, "tilt_ctrl_hotkey")
    obs.obs_hotkey_load(hotkey_a, a_array)
    obs.obs_hotkey_load(hotkey_d, d_array)
    obs.obs_hotkey_load(hotkey_shift, shift_array)
    obs.obs_hotkey_load(hotkey_ctrl, ctrl_array)
    obs.obs_data_array_release(a_array)
    obs.obs_data_array_release(d_array)
    obs.obs_data_array_release(shift_array)
    obs.obs_data_array_release(ctrl_array)

def script_save(settings):
    a_array = obs.obs_hotkey_save(hotkey_a)
    d_array = obs.obs_hotkey_save(hotkey_d)
    shift_array = obs.obs_hotkey_save(hotkey_shift)
    ctrl_array = obs.obs_hotkey_save(hotkey_ctrl)
    obs.obs_data_set_array(settings, "tilt_a_hotkey", a_array)
    obs.obs_data_set_array(settings, "tilt_d_hotkey", d_array)
    obs.obs_data_set_array(settings, "tilt_shift_hotkey", shift_array)
    obs.obs_data_set_array(settings, "tilt_ctrl_hotkey", ctrl_array)
    obs.obs_data_array_release(a_array)
    obs.obs_data_array_release(d_array)
    obs.obs_data_array_release(shift_array)
    obs.obs_data_array_release(ctrl_array)

def script_unload():
    restore()