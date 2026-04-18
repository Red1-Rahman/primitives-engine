# main.py
"""
Primitives Engine — main entry point
Mode selection screen drawn with OpenGL primitives.
Arrow keys to highlight, Enter to confirm, Backspace to go back.
Number keys to switch scenes/games after selecting a mode.
ESC to quit.
"""
import importlib
import pkgutil
from math import cos, pi, sin

from OpenGL.GL import (
    GL_TRIANGLE_FAN, glBegin, glColor3f, glColor4f,
    glEnd, glVertex2f,
)
from OpenGL.GLUT import (
    GLUT_KEY_DOWN, GLUT_KEY_UP,
    glutSetWindowTitle,
)

from engine.window   import init_window, start_loop, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP, WORLD_BOTTOM
from engine.input    import is_key, is_special
from engine.renderer import draw_text, draw_rect, draw_circle, draw_line_bresenham

import scenes.village_scenery       as s1
import scenes.city_scenery          as s2
import scenes.interior_design       as s3
import scenes.village_hut_bazar     as s4
import scenes.shadhinota            as s5
import scenes.primary_school        as s6
import scenes.jungle_cartoons       as s7
import scenes.wave_particle_collapse as s8
import scenes.KnowlegeTower         as s9

import games as games_pkg

# ─────────────────────────────────────────────
#  SCENES
# ─────────────────────────────────────────────
_SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9]
_SCENE_NAMES = [
    "Village Scenery",
    "City Scenery",
    "Interior Design",
    "Village Hut-Bazar",
    "Bangladesher Shadhinota",
    "Primary School",
    "Three Cartoons in Jungle",
    "Wave-Particle Collapse",
    "Knowledge Tower",
]

# ─────────────────────────────────────────────
#  GAME DISCOVERY
# ─────────────────────────────────────────────
def _discover_games():
    modules = []
    prefix = games_pkg.__name__ + "."
    for mod in pkgutil.iter_modules(games_pkg.__path__):
        if mod.name.startswith("_"):
            continue
        module = importlib.import_module(prefix + mod.name)
        if all(callable(getattr(module, fn, None)) for fn in ("init", "update", "draw")):
            modules.append(module)
    modules.sort(key=lambda m: m.__name__)
    return modules


def _module_name(module):
    custom = getattr(module, "DISPLAY_NAME", None)
    if isinstance(custom, str) and custom.strip():
        return custom.strip()
    return module.__name__.split(".")[-1].replace("_", " ").title()


# ─────────────────────────────────────────────
#  APP STATE
# ─────────────────────────────────────────────
# Screens: "menu" | "scenes" | "games"
_screen        = "menu"
_menu_cursor   = 0          # 0 = Scenes, 1 = Games
_current       = 0          # active scene/game index

_ITEMS  = []
_NAMES  = []
_GAMES  = []

_DIGIT_KEYS   = [b"1", b"2", b"3", b"4", b"5", b"6", b"7", b"8", b"9", b"0"]
_last_keys    = set()
_last_up      = False
_last_down    = False
_last_enter   = False
_last_back    = False
_last_next    = False
_last_prev    = False


# ─────────────────────────────────────────────
#  MENU DRAWING  (all primitives)
# ─────────────────────────────────────────────

def _draw_filled_circle(cx, cy, r, sides=48):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(sides + 1):
        a = 2 * pi * i / sides
        glVertex2f(cx + r * cos(a), cy + r * sin(a))
    glEnd()


def _draw_menu():
    # Background
    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.03, 0.03, 0.10), filled=True)

    # Decorative top border — Bresenham line
    draw_line_bresenham(WORLD_LEFT + 20, WORLD_TOP - 20,
                        WORLD_RIGHT - 20, WORLD_TOP - 20,
                        color=(0.2, 0.5, 1.0), size=2)
    draw_line_bresenham(WORLD_LEFT + 20, WORLD_BOTTOM + 20,
                        WORLD_RIGHT - 20, WORLD_BOTTOM + 20,
                        color=(0.2, 0.5, 1.0), size=2)

    # Corner circles — midpoint circle algorithm
    for cx, cy in [
        (WORLD_LEFT  + 20, WORLD_TOP    - 20),
        (WORLD_RIGHT - 20, WORLD_TOP    - 20),
        (WORLD_LEFT  + 20, WORLD_BOTTOM + 20),
        (WORLD_RIGHT - 20, WORLD_BOTTOM + 20),
    ]:
        draw_circle(cx, cy, 10, color=(0.2, 0.5, 1.0), size=2)

    # Title
    draw_text(-145, 180, "PRIMITIVES  ENGINE",
              color=(0.9, 0.9, 1.0))
    draw_line_bresenham(-200, 160, 200, 160, color=(0.3, 0.3, 0.6), size=1)

    # Menu options
    options     = ["  Scenes", "  Games"]
    option_y    = [60, -20]
    option_cols = [(0.6, 0.8, 1.0), (0.4, 0.9, 0.5)]

    for i, (label, oy, col) in enumerate(zip(options, option_y, option_cols)):
        if i == _menu_cursor:
            # Highlight box
            draw_rect(-180, oy - 10, 360, 38,
                      color=(0.10, 0.18, 0.36), filled=True)
            draw_rect(-180, oy - 10, 360, 38,
                      color=(0.3, 0.6, 1.0), width=1.5)
            # Arrow indicator
            glColor3f(1.0, 1.0, 0.2)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(-155, oy + 9)
            glVertex2f(-170, oy + 18)
            glVertex2f(-170, oy)
            glEnd()
            draw_text(-140, oy + 4, label, color=(1.0, 1.0, 1.0))
        else:
            draw_text(-140, oy + 4, label, color=(0.5, 0.55, 0.65))

    # Instructions
    draw_text(-165, -100, "UP / DOWN   arrow keys to move",
              color=(0.4, 0.4, 0.55))
    draw_text(-130, -128, "ENTER   to confirm",
              color=(0.4, 0.4, 0.55))
    draw_text(-100, -156, "ESC   to quit",
              color=(0.4, 0.4, 0.55))


# ─────────────────────────────────────────────
#  SCENE / GAME LIST DRAWING
# ─────────────────────────────────────────────

def _draw_switcher():
    mode_name = "Scenes" if _screen == "scenes" else "Games"

    # Background
    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.03, 0.03, 0.10), filled=True)

    # Header
    draw_line_bresenham(WORLD_LEFT + 20, WORLD_TOP - 35,
                        WORLD_RIGHT - 20, WORLD_TOP - 35,
                        color=(0.2, 0.5, 1.0), size=1)
    draw_text(WORLD_LEFT + 30, WORLD_TOP - 28,
              f"{mode_name} Mode  |  Backspace = back  |  ESC = quit",
              color=(0.5, 0.6, 0.8))
    draw_text(WORLD_LEFT + 30, WORLD_BOTTOM + 20,
          f"Now running:  {_NAMES[_current]}  |  Release Tab to play",
          color=(0.3, 0.8, 0.4))

    # List
    start_y = 200
    step_y  = 36
    for i, name in enumerate(_NAMES):
        oy = start_y - i * step_y
        key_label = "0" if i == 9 else str(i + 1) if i < 10 else "–"

        if i == _current:
            draw_rect(-340, oy - 8, 680, 30,
                      color=(0.10, 0.18, 0.36), filled=True)
            draw_rect(-340, oy - 8, 680, 30,
                      color=(0.3, 0.6, 1.0), width=1.5)
            glColor3f(1.0, 1.0, 0.2)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(-320, oy + 7)
            glVertex2f(-335, oy + 16)
            glVertex2f(-335, oy - 2)
            glEnd()
            draw_text(-308, oy + 2, f"[{key_label}]  {name}",
                      color=(1.0, 1.0, 1.0))
        else:
            draw_text(-308, oy + 2, f"[{key_label}]  {name}",
                      color=(0.5, 0.55, 0.65))

    # Running scene/game label at bottom
    draw_line_bresenham(WORLD_LEFT + 20, WORLD_BOTTOM + 35,
                        WORLD_RIGHT - 20, WORLD_BOTTOM + 35,
                        color=(0.2, 0.5, 1.0), size=1)
    draw_text(WORLD_LEFT + 30, WORLD_BOTTOM + 20,
              f"Now running:  {_NAMES[_current]}",
              color=(0.3, 0.8, 0.4))


# ─────────────────────────────────────────────
#  SWITCH HELPERS
# ─────────────────────────────────────────────

def _switch_to(index):
    global _current
    if index < 0 or index >= len(_ITEMS) or index == _current:
        return
    _current = index
    _ITEMS[_current].init()
    glutSetWindowTitle(
        f"Primitives Engine  |  {_NAMES[_current]}".encode()
    )
    print(f"  → {_NAMES[_current]}")


def _enter_mode(mode):
    global _screen, _ITEMS, _NAMES, _current
    _screen = mode
    if mode == "scenes":
        _ITEMS = _SCENES
        _NAMES = _SCENE_NAMES
    else:
        _ITEMS = _GAMES
        _NAMES = [_module_name(m) for m in _GAMES]
    _current = 0
    _ITEMS[_current].init()
    glutSetWindowTitle(
        f"Primitives Engine  |  {_NAMES[_current]}".encode()
    )
    print(f"\n[{mode.title()} mode]  {_NAMES[_current]}")


def _go_back():
    global _screen
    _screen = "menu"
    glutSetWindowTitle(b"Primitives Engine  |  Select Mode")


# ─────────────────────────────────────────────
#  DISPLAY & UPDATE
# ─────────────────────────────────────────────

def _display():
    if _screen == "menu":
        _draw_menu()
    elif _screen in ("scenes", "games"):
        _ITEMS[_current].draw()
        # Only show switcher overlay while Tab is held
        if is_key(b"\t"):
            _draw_switcher()


def _update():
    global _menu_cursor, _screen
    global _last_keys, _last_up, _last_down
    global _last_enter, _last_back, _last_next, _last_prev

    up_now    = is_special(GLUT_KEY_UP)
    down_now  = is_special(GLUT_KEY_DOWN)
    enter_now = is_key(b"\r") or is_key(b"\n")
    back_now  = is_key(b"\x08")   # Backspace

    if _screen == "menu":
        if up_now and not _last_up:
            _menu_cursor = (_menu_cursor - 1) % 2
        if down_now and not _last_down:
            _menu_cursor = (_menu_cursor + 1) % 2
        if enter_now and not _last_enter:
            _enter_mode("scenes" if _menu_cursor == 0 else "games")

    elif _screen in ("scenes", "games"):
        _ITEMS[_current].update()

        if back_now and not _last_back:
            _go_back()

        # Number key switching
        pressed = set()
        key_count = min(len(_ITEMS), len(_DIGIT_KEYS))
        for i, key in enumerate(_DIGIT_KEYS[:key_count]):
            if is_key(key):
                pressed.add(i)
        for i in pressed - _last_keys:
            _switch_to(i)

        # N / P cycle if more than 10
        next_now = is_key(b"n") or is_key(b"N")
        prev_now = is_key(b"p") or is_key(b"P")
        if len(_ITEMS) > len(_DIGIT_KEYS):
            if next_now and not _last_next:
                _switch_to((_current + 1) % len(_ITEMS))
            if prev_now and not _last_prev:
                _switch_to((_current - 1) % len(_ITEMS))
        _last_next = next_now
        _last_prev = prev_now

        _last_keys = pressed

    _last_up    = up_now
    _last_down  = down_now
    _last_enter = enter_now
    _last_back  = back_now


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    _GAMES = _discover_games()

    if not _GAMES:
        print("No valid games found in games/. Only Scenes mode will be available.")

    init_window(
        "Primitives Engine  |  Select Mode",
        _display,
        _update,
    )
    glutSetWindowTitle(b"Primitives Engine  |  Select Mode")
    start_loop()