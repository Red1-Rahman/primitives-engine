import sys
from OpenGL.GLUT import *

# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────

keys         = {}   # regular keys  e.g. b'a', b' '
special_keys = {}   # arrow keys    e.g. GLUT_KEY_LEFT

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