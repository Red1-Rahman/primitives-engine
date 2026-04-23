# engine\input.py
import sys
from OpenGL.GLUT import *

# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────

keys         = {}   # regular keys  e.g. b'a', b' '
special_keys = {}   # arrow keys    e.g. GLUT_KEY_LEFT

# Action bindings let apps query semantic actions instead of raw key bytes.
# This keeps controls portable across platforms (e.g., macOS Delete vs Backspace).
_action_bindings = {
    "ui_up": {
        "keys": set(),
        "special": {GLUT_KEY_UP},
    },
    "ui_down": {
        "keys": set(),
        "special": {GLUT_KEY_DOWN},
    },
    "ui_confirm": {
        "keys": {b"\r", b"\n"},
        "special": set(),
    },
    "ui_back": {
        "keys": {b"\x08", b"\x7f"},
        "special": set(),
    },
    "ui_toggle_selector": {
        "keys": {b"\t"},
        "special": set(),
    },
    "ui_next": {
        "keys": {b"n", b"N"},
        "special": set(),
    },
    "ui_prev": {
        "keys": {b"p", b"P"},
        "special": set(),
    },
}

mouse = {
    "x":       0,
    "y":       0,
    "left":    False,
    "right":   False,
    "middle":  False,
}

# ─────────────────────────────────────────────
#  KEYBOARD
# ─────────────────────────────────────────────

def _keyboard_down(key, x, y):
    keys[key] = True
    if key == b'\x1b':   # ESC → quit
        sys.exit(0)


def _keyboard_up(key, x, y):
    keys[key] = False


def _special_down(key, x, y):
    special_keys[key] = True


def _special_up(key, x, y):
    special_keys[key] = False


# ─────────────────────────────────────────────
#  MOUSE
# ─────────────────────────────────────────────

def _mouse_click(button, state, x, y):
    pressed = (state == GLUT_DOWN)
    if button == GLUT_LEFT_BUTTON:
        mouse["left"]   = pressed
    elif button == GLUT_RIGHT_BUTTON:
        mouse["right"]  = pressed
    elif button == GLUT_MIDDLE_BUTTON:
        mouse["middle"] = pressed
    mouse["x"] = x
    mouse["y"] = y


def _mouse_move(x, y):
    mouse["x"] = x
    mouse["y"] = y


# ─────────────────────────────────────────────
#  HELPERS  (call these in scene/update)
# ─────────────────────────────────────────────

def is_key(key) -> bool:
    """Check if a regular key is currently held. e.g. is_key(b'a')"""
    return keys.get(key, False)


def is_special(key) -> bool:
    """Check if a special key is held. e.g. is_special(GLUT_KEY_LEFT)"""
    return special_keys.get(key, False)


def _normalize_regular_key(key):
    if isinstance(key, bytes):
        return key
    if isinstance(key, str):
        return key.encode()
    raise TypeError("Regular key bindings must be bytes or str.")


def bind_action(action, keys=None, special=None, append=False):
    """
    Bind a semantic action to one or more regular/special keys.

    Examples:
        bind_action("ui_back", keys=[b"\x08", b"\x7f"])
        bind_action("ui_confirm", keys=["e"], append=True)
    """
    if action not in _action_bindings:
        _action_bindings[action] = {"keys": set(), "special": set()}

    binding = _action_bindings[action]
    if not append:
        binding["keys"].clear()
        binding["special"].clear()

    if keys:
        for key in keys:
            binding["keys"].add(_normalize_regular_key(key))

    if special:
        for key in special:
            binding["special"].add(key)


def get_action_bindings(action):
    """Return a copy of the current binding for an action."""
    if action not in _action_bindings:
        return {"keys": set(), "special": set()}
    binding = _action_bindings[action]
    return {
        "keys": set(binding["keys"]),
        "special": set(binding["special"]),
    }


def is_action(action) -> bool:
    """Check whether any key bound to an action is currently held."""
    binding = _action_bindings.get(action)
    if not binding:
        return False
    if any(is_key(key) for key in binding["keys"]):
        return True
    if any(is_special(key) for key in binding["special"]):
        return True
    return False


def is_mouse(button="left") -> bool:
    """Check if a mouse button is held. button: 'left'|'right'|'middle'"""
    return mouse.get(button, False)


def mouse_pos():
    """Return current mouse (x, y) in screen pixels."""
    return mouse["x"], mouse["y"]


# ─────────────────────────────────────────────
#  REGISTER  (call once from window.py)
# ─────────────────────────────────────────────

def register_input():
    """Register all GLUT input callbacks."""
    glutKeyboardFunc(_keyboard_down)
    glutKeyboardUpFunc(_keyboard_up)
    glutSpecialFunc(_special_down)
    glutSpecialUpFunc(_special_up)
    glutMouseFunc(_mouse_click)
    glutPassiveMotionFunc(_mouse_move)
    glutMotionFunc(_mouse_move)