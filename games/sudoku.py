from engine.input import is_key, is_special, is_mouse, mouse_pos
from engine.renderer import draw_line_dda, draw_rect, draw_text
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP

DISPLAY_NAME = "Sudoku"

# Game State
_state = {
    "grid": [],
    "original": [],  # To keep track of fixed numbers
    "cursor": [0, 0], # [row, col]
    "solved": False
}

def init():
    # Example starting puzzle (0 = empty)
    # In a full version, you could use a generator here
    _state["grid"] = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    # Deep copy to identify fixed cells
    _state["original"] = [row[:] for row in _state["grid"]]
    _state["cursor"] = [0, 0]
    _state["solved"] = False

def update():
    row, col = _state["cursor"]

    # Navigation (Using arrow keys or WASD via is_key)
    if is_key(b"w") or is_key(b"W"): _state["cursor"][0] = max(0, row - 1)
    if is_key(b"s") or is_key(b"S"): _state["cursor"][0] = min(8, row + 1)
    if is_key(b"a") or is_key(b"A"): _state["cursor"][1] = max(0, col - 1)
    if is_key(b"d") or is_key(b"D"): _state["cursor"][1] = min(8, col + 1)

    # Number Input (1-9)
    for i in range(1, 10):
        if is_key(str(i).encode()):
            # Only allow editing if the cell wasn't part of the starting puzzle
            if _state["original"][row][col] == 0:
                _state["grid"][row][col] = i

    # Clear cell
    if is_key(b"0") or is_key(b" "):
        if _state["original"][row][col] == 0:
            _state["grid"][row][col] = 0

    # Reset
    if is_key(b"r") or is_key(b"R"):
        init()

def draw():
    # Background
    draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=(0.1, 0.1, 0.12), filled=True)

    cell_size = 40
    start_x = (WORLD_RIGHT // 2) - (cell_size * 4.5)
    start_y = (WORLD_TOP // 2) + (cell_size * 4.5)

    # Draw Grid
    for i in range(10):
        # Thicker lines for 3x3 boundaries
        thickness = 3 if i % 3 == 0 else 1
        color = (0.8, 0.8, 0.8) if i % 3 == 0 else (0.4, 0.4, 0.4)
        
        # Horizontal lines
        draw_line_dda(start_x, start_y - i * cell_size, 
                      start_x + 9 * cell_size, start_y - i * cell_size)
        # Vertical lines
        draw_line_dda(start_x + i * cell_size, start_y, 
                      start_x + i * cell_size, start_y - 9 * cell_size)

    # Draw Numbers and Cursor
    for r in range(9):
        for c in range(9):
            x = start_x + c * cell_size + 15
            y = start_y - r * cell_size - 30
            val = _state["grid"][r][c]

            # Highlight Cursor
            if _state["cursor"] == [r, c]:
                draw_rect(start_x + c * cell_size, start_y - (r+1) * cell_size, 
                          cell_size, cell_size, color=(0.2, 0.5, 0.8), filled=True)

            # Draw Number
            if val != 0:
                # Fixed numbers are white, user numbers are light blue
                text_color = (1, 1, 1) if _state["original"][r][c] != 0 else (0.4, 0.7, 1.0)
                draw_text(x, y, str(val))

    # Instructions
    draw_text(WORLD_LEFT + 20, WORLD_BOTTOM + 40, "WASD: Move | 1-9: Place | 0/Space: Clear | R: Reset", (0.7, 0.7, 0.7))
    draw_text(WORLD_LEFT + 20, WORLD_TOP - 30, "SUDOKU MODULE", (1, 0.8, 0))
