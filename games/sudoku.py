import random
from engine.input import is_key, is_special
from engine.renderer import draw_line_dda, draw_rect, draw_text
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP
from OpenGL.GLUT import GLUT_KEY_UP, GLUT_KEY_DOWN, GLUT_KEY_LEFT, GLUT_KEY_RIGHT

DISPLAY_NAME = "Sudoku Pro"

_state = {
    "grid": [],
    "solution": [],
    "original": [],
    "cursor": [4, 4],
    "lives": 3,
    "hints": 1,
    "error_cell": None,
    "error_timer": 0,
    "last_special": {},
    "last_keys": set() # Added to track normal alphanumeric keys
}

def is_safe(grid, r, c, num):
    for x in range(9):
        if grid[r][x] == num or grid[x][c] == num:
            return False
    sr, sc = r - r % 3, c - c % 3
    for i in range(3):
        for j in range(3):
            if grid[i + sr][j + sc] == num:
                return False
    return True

def solve_grid(grid):
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for n in nums:
                    if is_safe(grid, r, c, n):
                        grid[r][c] = n
                        if solve_grid(grid): return True
                        grid[r][c] = 0
                return False
    return True

def init():
    _state["lives"] = 3
    _state["hints"] = 1
    _state["cursor"] = [4, 4]
    _state["error_cell"] = None
    _state["error_timer"] = 0
    _state["last_special"] = {}
    _state["last_keys"] = set()
    
    base = [[0 for _ in range(9)] for _ in range(9)]
    solve_grid(base)
    _state["solution"] = [row[:] for row in base]
    
    puzzle = [row[:] for row in base]
    removed = 0
    while removed < 45:
        r, c = random.randint(0, 8), random.randint(0, 8)
        if puzzle[r][c] != 0:
            puzzle[r][c] = 0
            removed += 1
            
    _state["grid"] = puzzle
    _state["original"] = [row[:] for row in puzzle]

def update():
    # Always allow Reset
    if is_key(b"r") or is_key(b"R"):
        init()
        return

    if _state["lives"] <= 0:
        return

    r, c = _state["cursor"]
    
    # --- Input Debouncing Logic ---
    def just_pressed_special(key):
        is_down = is_special(key)
        was_down = _state["last_special"].get(key, False)
        _state["last_special"][key] = is_down
        return is_down and not was_down

    def just_pressed_key(k_byte):
        is_down = is_key(k_byte)
        was_down = k_byte in _state["last_keys"]
        if is_down: _state["last_keys"].add(k_byte)
        else: _state["last_keys"].discard(k_byte)
        return is_down and not was_down

    # Navigation
    if just_pressed_special(GLUT_KEY_UP):    _state["cursor"][0] = max(0, r - 1)
    if just_pressed_special(GLUT_KEY_DOWN):  _state["cursor"][0] = min(8, r + 1)
    if just_pressed_special(GLUT_KEY_LEFT):  _state["cursor"][1] = max(0, c - 1)
    if just_pressed_special(GLUT_KEY_RIGHT): _state["cursor"][1] = min(8, c + 1)

    # Number Input (Debounced)
    for i in range(1, 10):
        kb = str(i).encode()
        if just_pressed_key(kb):
            if _state["original"][r][c] == 0 and _state["grid"][r][c] == 0:
                if not is_safe(_state["grid"], r, c, i):
                    _state["lives"] -= 1  # This will now only happen ONCE per tap
                    _state["error_cell"] = [r, c]
                    _state["error_timer"] = 40
                else:
                    _state["grid"][r][c] = i

    # Hint System (Debounced)
    if just_pressed_key(b"h") or just_pressed_key(b"H"):
        if _state["hints"] > 0 and _state["grid"][r][c] == 0:
            val = _state["solution"][r][c]
            _state["grid"][r][c] = val
            _state["original"][r][c] = val
            _state["hints"] -= 1

    if _state["error_timer"] > 0:
        _state["error_timer"] -= 1
    else:
        _state["error_cell"] = None

def draw():
    draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT-WORLD_LEFT, WORLD_TOP-WORLD_BOTTOM, (0.05, 0.05, 0.08), True)
    
    cell_size = 50
    grid_size = cell_size * 9
    start_x, start_y = -grid_size // 2, grid_size // 2

    # Draw Selection
    cr, cc = _state["cursor"]
    cx, cy = start_x + (cc * cell_size), start_y - (cr * cell_size) - cell_size
    
    if _state["error_cell"] == [cr, cc]:
        draw_rect(cx, cy, cell_size, cell_size, (0.9, 0.1, 0.1), True)
    else:
        draw_rect(cx, cy, cell_size, cell_size, (0.15, 0.3, 0.6), True)
        draw_rect(cx + 3, cy + 3, cell_size - 6, cell_size - 6, (0.4, 0.8, 1.0), 1)

    # Draw Numbers
    for r in range(9):
        for c in range(9):
            val = _state["grid"][r][c]
            if val != 0:
                col = (1, 1, 1) if _state["original"][r][c] != 0 else (0, 0.9, 0.9)
                draw_text(start_x + c*cell_size + 18, start_y - r*cell_size - 35, str(val), col)

    # Draw Grid
    for i in range(10):
        thick = (i % 3 == 0)
        l_col = (1.0, 1.0, 1.0) if thick else (0.2, 0.25, 0.35)
        pos = i * cell_size
        draw_line_dda(start_x, start_y - pos, start_x + grid_size, start_y - pos, l_col)
        draw_line_dda(start_x + pos, start_y, start_x + pos, start_y - grid_size, l_col)
        if thick:
            draw_line_dda(start_x, start_y - pos - 1, start_x + grid_size, start_y - pos - 1, l_col)
            draw_line_dda(start_x + pos + 1, start_y, start_x + pos + 1, start_y - grid_size, l_col)

    # HUD
    draw_text(WORLD_LEFT + 20, WORLD_TOP - 40, f"LIVES: {_state['lives']} | HINTS: {_state['hints']}", (1, 0.2, 0.2))
    
    if _state["lives"] <= 0:
        draw_rect(-200, -50, 400, 100, (0, 0, 0), True)
        draw_text(-140, 15, "GAME OVER!", (1, 0, 0))
        draw_text(-180, -20, "OUT OF LIVES. PRESS R", (1, 1, 1))