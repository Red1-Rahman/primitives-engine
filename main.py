"""
Primitives Engine — main entry point
Press 1-7 to switch between scenes.
ESC to quit (handled by input.py).
"""
from engine.window import init_window, start_loop
from engine.input  import is_key
from OpenGL.GLUT   import glutSetWindowTitle

import scenes.village_scenery   as s1
import scenes.city_scenery      as s2
import scenes.interior_design   as s3
import scenes.village_hut_bazar as s4
import scenes.shadhinota        as s5
import scenes.primary_school    as s6
import scenes.jungle_cartoons   as s7

_SCENES = [s1, s2, s3, s4, s5, s6, s7]
_NAMES  = [
    "Village Scenery",
    "City Scenery",
    "Interior Design",
    "Village Hut-Bazar",
    "Bangladesher Shadhinota",
    "Primary School",
    "Three Cartoons in Jungle",
]

_current   = 0
_last_keys = set()     # track previously-pressed keys to fire only on new press


def _display():
    _SCENES[_current].draw()


def _update():
    global _current, _last_keys

    _SCENES[_current].update()

    # Detect which number keys are freshly pressed this frame
    pressed = set()
    for i, key in enumerate([b'1', b'2', b'3', b'4', b'5', b'6', b'7']):
        if is_key(key):
            pressed.add(i)

    for i in pressed - _last_keys:   # newly pressed this frame
        if i != _current:
            _current = i
            _SCENES[_current].init()
            title = f"Primitives Engine  |  Press 1-7 to switch  |  {_NAMES[_current]}"
            glutSetWindowTitle(title.encode())
            print(f"[Scene {i + 1}] {_NAMES[i]}")

    _last_keys = pressed


if __name__ == "__main__":
    for s in _SCENES:
        s.init()
    init_window(
        f"Primitives Engine  |  Press 1-7 to switch  |  {_NAMES[_current]}",
        _display,
        _update,
    )
    start_loop()
