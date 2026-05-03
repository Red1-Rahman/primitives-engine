# main.py
"""
Primitives Engine — main entry point
Mode selection screen drawn with OpenGL primitives.
Arrow keys to highlight, Enter to confirm, Backspace/Delete to go back.
Tab toggles a full selector list; use Up/Down + Enter to choose.
ESC to quit.
"""
import os
import platform
import importlib
import pkgutil
from math import cos, pi, sin

# On Linux (especially Wayland sessions), force the GLX backend for GLUT.
if platform.system() == "Linux":
    os.environ.setdefault("PYOPENGL_PLATFORM", "glx")

from OpenGL.GL import (
    GL_TRIANGLE_FAN, glBegin, glColor3f, glColor4f,
    glEnd, glVertex2f,
)
from OpenGL.GLUT import (
    glutSetWindowTitle,
)

from engine.window   import init_window, start_loop, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP, WORLD_BOTTOM
from engine.input    import is_key, is_action
from engine.renderer import draw_text, draw_rect, draw_circle, draw_line_bresenham

import scenes.village_scenery           as s1
import scenes.city_scenery              as s2
import scenes.interior_design           as s3
import scenes.village_hut_bazar         as s4
import scenes.shadhinota                as s5
import scenes.primary_school            as s6
import scenes.jungle_cartoons           as s7
import scenes.KnowlegeTower             as s8

import games as games_pkg

# ─────────────────────────────────────────────
#  SCENES
# ─────────────────────────────────────────────
_SCENES = [s1, s2, s3, s4, s5, s6, s7, s8 ]
_SCENE_NAMES = [
    "Village Scenery",
    "City Scenery",
    "Interior Design",
    "Village Hut-Bazar",
    "Bangladesher Shadhinota",
    "Primary School",
    "Three Cartoons in Jungle",
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
_screen         = "menu"
_menu_cursor    = 0
_current        = 0
_browse_cursor  = 0
_selector_open  = False

_ITEMS  = []
_NAMES  = []
_GAMES  = []

_last_keys     = set()
_last_up       = False
_last_down     = False
_last_enter    = False
_last_back     = False
_last_next     = False
_last_prev     = False
_last_tab      = False


# ─────────────────────────────────────────────
#  MENU DRAWING
# ─────────────────────────────────────────────

def _draw_filled_circle(cx, cy, r, sides=48):
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(sides + 1):
        a = 2 * pi * i / sides
        glVertex2f(cx + r * cos(a), cy + r * sin(a))
    glEnd()


def _draw_menu():
    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.03, 0.03, 0.10), filled=True)

    draw_line_bresenham(WORLD_LEFT + 20, WORLD_TOP - 20,
                        WORLD_RIGHT - 20, WORLD_TOP - 20,
                        color=(0.2, 0.5, 1.0), size=2)
    draw_line_bresenham(WORLD_LEFT + 20, WORLD_BOTTOM + 20,
                        WORLD_RIGHT - 20, WORLD_BOTTOM + 20,
                        color=(0.2, 0.5, 1.0), size=2)

    for cx, cy in [
        (WORLD_LEFT  + 20, WORLD_TOP    - 20),
        (WORLD_RIGHT - 20, WORLD_TOP    - 20),
        (WORLD_LEFT  + 20, WORLD_BOTTOM + 20),
        (WORLD_RIGHT - 20, WORLD_BOTTOM + 20),
    ]:
        draw_circle(cx, cy, 10, color=(0.2, 0.5, 1.0), size=2)

    draw_text(-145, 180, "PRIMITIVES  ENGINE",
              color=(0.9, 0.9, 1.0))
    draw_line_bresenham(-200, 160, 200, 160, color=(0.3, 0.3, 0.6), size=1)

    options     = ["  Scenes", "  Games"]
    option_y    = [60, -20]
    option_cols = [(0.6, 0.8, 1.0), (0.4, 0.9, 0.5)]

    for i, (label, oy, col) in enumerate(zip(options, option_y, option_cols)):
        if i == _menu_cursor:
            draw_rect(-180, oy - 10, 360, 38,
                      color=(0.10, 0.18, 0.36), filled=True)
            draw_rect(-180, oy - 10, 360, 38,
                      color=(0.3, 0.6, 1.0), width=1.5)
            glColor3f(1.0, 1.0, 0.2)
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(-155, oy + 9)
            glVertex2f(-170, oy + 18)
            glVertex2f(-170, oy)
            glEnd()
            draw_text(-140, oy + 4, label, color=(1.0, 1.0, 1.0))
        else:
            draw_text(-140, oy + 4, label, color=(0.5, 0.55, 0.65))

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

    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.03, 0.03, 0.10), filled=True)

    draw_line_bresenham(WORLD_LEFT + 20, WORLD_TOP - 35,
                        WORLD_RIGHT - 20, WORLD_TOP - 35,
                        color=(0.2, 0.5, 1.0), size=1)
    draw_text(WORLD_LEFT + 30, WORLD_TOP - 28,
              f"{mode_name} Mode  |  TAB toggle  |  UP/DOWN + ENTER select  |  Backspace/Delete = back",
              color=(0.5, 0.6, 0.8))
    draw_text(WORLD_LEFT + 30, WORLD_BOTTOM + 20,
              f"Selected:  {_NAMES[_browse_cursor]}  |  Running: {_NAMES[_current]}",
              color=(0.3, 0.8, 0.4))

    start_y = 200
    step_y  = 36
    max_rows = max(1, int((start_y - (WORLD_BOTTOM + 65)) // step_y) + 1)

    total = len(_NAMES)
    if total <= max_rows:
        first = 0
    else:
        half = max_rows // 2
        first = max(0, _browse_cursor - half)
        first = min(first, total - max_rows)
    last = min(total, first + max_rows)

    for row, i in enumerate(range(first, last)):
        name = _NAMES[i]
        oy = start_y - row * step_y

        if i == _browse_cursor:
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
            draw_text(-308, oy + 2, f"{name}",
                      color=(1.0, 1.0, 1.0))
        else:
            draw_text(-308, oy + 2, f"{name}",
                      color=(0.5, 0.55, 0.65))

    if total > max_rows:
        draw_text(WORLD_RIGHT - 200, WORLD_TOP - 28,
                  f"{_browse_cursor + 1}/{total}",
                  color=(0.7, 0.75, 0.85))

    draw_line_bresenham(WORLD_LEFT + 20, WORLD_BOTTOM + 35,
                        WORLD_RIGHT - 20, WORLD_BOTTOM + 35,
                        color=(0.2, 0.5, 1.0), size=1)


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
    global _screen, _ITEMS, _NAMES, _current, _browse_cursor, _selector_open
    _screen = mode
    if mode == "scenes":
        _ITEMS = _SCENES
        _NAMES = _SCENE_NAMES
    else:
        _ITEMS = _GAMES
        _NAMES = [_module_name(m) for m in _GAMES]
    _current = 0
    _browse_cursor = _current
    _selector_open = False
    _ITEMS[_current].init()
    glutSetWindowTitle(
        f"Primitives Engine  |  {_NAMES[_current]}".encode()
    )
    print(f"\n[{mode.title()} mode]  {_NAMES[_current]}")


def _go_back():
    global _screen, _selector_open
    _screen = "menu"
    _selector_open = False
    glutSetWindowTitle(b"Primitives Engine  |  Select Mode")


# ─────────────────────────────────────────────
#  DISPLAY & UPDATE
# ─────────────────────────────────────────────

def _display():
    if _screen == "menu":
        _draw_menu()
    elif _screen in ("scenes", "games"):
        _ITEMS[_current].draw()
        if _selector_open:
            _draw_switcher()


def _update():
    global _menu_cursor, _screen
    global _last_keys, _last_up, _last_down
    global _last_enter, _last_back, _last_next, _last_prev
    global _browse_cursor, _selector_open, _last_tab

    up_now    = is_action("ui_up")
    down_now  = is_action("ui_down")
    enter_now = is_action("ui_confirm")
    back_now  = is_action("ui_back")
    tab_now   = is_action("ui_toggle_selector")

    if _screen == "menu":
        if up_now and not _last_up:
            _menu_cursor = (_menu_cursor - 1) % 2
        if down_now and not _last_down:
            _menu_cursor = (_menu_cursor + 1) % 2
        if enter_now and not _last_enter:
            _enter_mode("scenes" if _menu_cursor == 0 else "games")

    elif _screen in ("scenes", "games"):
        if tab_now and not _last_tab:
            _selector_open = not _selector_open
            if _selector_open:
                _browse_cursor = _current

        if _selector_open:
            if back_now and not _last_back:
                _selector_open = False
            if up_now and not _last_up:
                _browse_cursor = (_browse_cursor - 1) % len(_ITEMS)
            if down_now and not _last_down:
                _browse_cursor = (_browse_cursor + 1) % len(_ITEMS)
            if enter_now and not _last_enter:
                _switch_to(_browse_cursor)
                _selector_open = False
        else:
            _ITEMS[_current].update()

            if back_now and not _last_back:
                _go_back()

            # N / P cycle 
            next_now = is_action("ui_next")
            prev_now = is_action("ui_prev")
            if next_now and not _last_next:
                _switch_to((_current + 1) % len(_ITEMS))
            if prev_now and not _last_prev:
                _switch_to((_current - 1) % len(_ITEMS))
            _last_next = next_now
            _last_prev = prev_now

        if _selector_open:
            _last_next = False
            _last_prev = False

    _last_tab = tab_now
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