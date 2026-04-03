"""
Primitives Engine — main entry point
At startup choose Scenes or Games mode.
Use number keys to switch items in the selected mode.
ESC to quit (handled by input.py).
"""
import importlib
import pkgutil

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

import games as games_pkg

_SCENES = [s1, s2, s3, s4, s5, s6, s7]
_SCENE_NAMES = [
    "Village Scenery",
    "City Scenery",
    "Interior Design",
    "Village Hut-Bazar",
    "Bangladesher Shadhinota",
    "Primary School",
    "Three Cartoons in Jungle",
]

_DIGIT_KEYS = [b"1", b"2", b"3", b"4", b"5", b"6", b"7", b"8", b"9", b"0"]


def _discover_games():
    """Auto-load all game modules that expose init/update/draw."""
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


def _choose_mode(has_games):
    """Ask launcher mode before entering GLUT loop."""
    print("Select launcher mode:")
    print("  1) Scenes")
    print("  2) Games")
    if not has_games:
        print("  (No valid games found yet. Defaulting to Scenes.)")
        return "scenes"

    while True:
        try:
            choice = input("Enter 1 or 2: ").strip().lower()
        except EOFError:
            return "scenes"

        if choice in ("1", "s", "scene", "scenes"):
            return "scenes"
        if choice in ("2", "g", "game", "games"):
            return "games"
        print("Invalid input. Please type 1 for Scenes or 2 for Games.")


def _switch_hint(item_count):
    if item_count <= 0:
        return "No items"
    if item_count <= 9:
        return f"Press 1-{item_count} to switch"
    if item_count == 10:
        return "Press 1-9 and 0 to switch"
    return "Press 1-9 and 0 to switch  |  N/P for next/prev"


def _print_switch_menu():
    print(f"\n{_MODE_NAME} mode loaded:")
    for i, name in enumerate(_NAMES, start=1):
        key = "0" if i == 10 else str(i)
        if i <= 10:
            print(f"  {key}) {name}")
        else:
            print(f"  -  {name}")
    print(_switch_hint(len(_ITEMS)))
    print("ESC to quit")


_ITEMS = _SCENES
_NAMES = _SCENE_NAMES
_MODE_NAME = "Scenes"


def _configure_mode():
    global _ITEMS, _NAMES, _MODE_NAME

    games = _discover_games()
    mode = _choose_mode(bool(games))

    if mode == "games":
        _ITEMS = games
        _NAMES = [_module_name(m) for m in _ITEMS]
        _MODE_NAME = "Games"
    else:
        _ITEMS = _SCENES
        _NAMES = _SCENE_NAMES
        _MODE_NAME = "Scenes"

    if not _ITEMS:
        raise RuntimeError("No runnable modules found for selected mode.")

_current   = 0
_last_keys = set()     # track previously-pressed keys to fire only on new press
_last_next = False
_last_prev = False


def _set_title():
    hint = _switch_hint(len(_ITEMS))
    title = f"Primitives Engine  |  {_MODE_NAME} Mode  |  {hint}  |  {_NAMES[_current]}"
    glutSetWindowTitle(title.encode())


def _switch_to(index):
    global _current
    if index < 0 or index >= len(_ITEMS) or index == _current:
        return
    _current = index
    _ITEMS[_current].init()
    _set_title()
    print(f"[{_MODE_NAME} {index + 1}] {_NAMES[index]}")


def _display():
    _ITEMS[_current].draw()


def _update():
    global _last_keys, _last_next, _last_prev

    _ITEMS[_current].update()

    # Detect which number keys are freshly pressed this frame
    pressed = set()
    key_count = min(len(_ITEMS), len(_DIGIT_KEYS))
    for i, key in enumerate(_DIGIT_KEYS[:key_count]):
        if is_key(key):
            pressed.add(i)

    for i in pressed - _last_keys:   # newly pressed this frame
        _switch_to(i)

    # If there are more than 10 modules, allow cycling through all with N/P.
    next_pressed = is_key(b"n") or is_key(b"N")
    prev_pressed = is_key(b"p") or is_key(b"P")

    if len(_ITEMS) > len(_DIGIT_KEYS):
        if next_pressed and not _last_next:
            _switch_to((_current + 1) % len(_ITEMS))
        if prev_pressed and not _last_prev:
            _switch_to((_current - 1) % len(_ITEMS))

    _last_next = next_pressed
    _last_prev = prev_pressed

    _last_keys = pressed


if __name__ == "__main__":
    _configure_mode()
    _print_switch_menu()
    init_window(
        f"Primitives Engine  |  {_MODE_NAME} Mode  |  {_switch_hint(len(_ITEMS))}  |  {_NAMES[_current]}",
        _display,
        _update,
    )
    _ITEMS[_current].init()
    _set_title()
    start_loop()
