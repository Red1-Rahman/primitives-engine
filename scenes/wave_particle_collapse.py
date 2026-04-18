# scenes\wave_particle_collapse.py
"""
True Emergent Wave Simulation — 2D Finite Difference Time Domain (FDTD)
Moving objects : None. This is a grid-based scalar field simulation.
Algorithms     : Numerical integration of the 2D wave equation.
Renderer       : draw_rect (drawing the simulation grid cells)
"""
import math
from engine.renderer import draw_rect
from engine.input import is_mouse, mouse_pos

# ── Simulation Constants ──────────────────────────────────────────────────
# To keep pure Python running smoothly, we use a coarse grid.
# Screen is 800x600, so a 100x75 grid means each cell is 8x8 pixels.
GRID_W = 100
GRID_H = 75
CELL_SIZE = 8

# Wave equation parameters
WAVE_SPEED = 0.45       # Must be < 0.5 for stability in 2D FDTD
DAMPING = 0.998         # Slight decay to prevent energy buildup
EMITTER_FREQ = 0.4      # Oscillation speed of the source

# Geometry in grid coordinates
EMITTER_X = 15
EMITTER_Y = GRID_H // 2
BARRIER_X = 40
SLIT_SIZE = 4
SLIT_1_Y = (GRID_H // 2) - 10
SLIT_2_Y = (GRID_H // 2) + 10

# ── State ─────────────────────────────────────────────────────────────────
# We need three grids to calculate the timeline: past, present, future.
_u_prev = [[0.0 for _ in range(GRID_W)] for _ in range(GRID_H)]
_u_curr = [[0.0 for _ in range(GRID_W)] for _ in range(GRID_H)]
_u_next = [[0.0 for _ in range(GRID_W)] for _ in range(GRID_H)]

_time = 0.0
_walls = [[False for _ in range(GRID_W)] for _ in range(GRID_H)]

def init():
    global _u_prev, _u_curr, _u_next, _time, _walls
    _time = 0.0
    
    # Reset grids
    for y in range(GRID_H):
        for x in range(GRID_W):
            _u_prev[y][x] = 0.0
            _u_curr[y][x] = 0.0
            _u_next[y][x] = 0.0
            _walls[y][x] = False

    # Build the double-slit barrier
    for y in range(GRID_H):
        # Leave gaps for the two slits
        if abs(y - SLIT_1_Y) <= SLIT_SIZE or abs(y - SLIT_2_Y) <= SLIT_SIZE:
            continue
        _walls[y][BARRIER_X] = True
        _walls[y][BARRIER_X + 1] = True # Make it 2 cells thick to prevent tunneling


def update():
    global _u_prev, _u_curr, _u_next, _time

    _time += 1.0

    # 1. Drive the emitter (Continuous sine wave source)
    _u_curr[EMITTER_Y][EMITTER_X] = math.sin(_time * EMITTER_FREQ) * 2.0

    # Optional: Mouse interaction to create ripples!
    if is_mouse("left"):
        mx, my = mouse_pos()
        # Convert window pixels to grid indices
        gx = int(mx / (800 / GRID_W))
        gy = int(my / (600 / GRID_H))
        if 1 < gx < GRID_W - 1 and 1 < gy < GRID_H - 1:
            _u_curr[gy][gx] = 5.0 # Large amplitude spike

    # 2. Compute the Wave Equation (FDTD step)
    for y in range(1, GRID_H - 1):
        for x in range(1, GRID_W - 1):
            if _walls[y][x]:
                _u_next[y][x] = 0.0
                continue

            # Laplacian: sum of 4 neighbors minus 4 * center
            laplacian = (
                _u_curr[y+1][x] + 
                _u_curr[y-1][x] + 
                _u_curr[y][x+1] + 
                _u_curr[y][x-1] - 
                4.0 * _u_curr[y][x]
            )

            # Integration step
            new_val = (2.0 * _u_curr[y][x]) - _u_prev[y][x] + (WAVE_SPEED * laplacian)
            _u_next[y][x] = new_val * DAMPING

    # 3. Swap buffers (time marches forward)
    # prev = curr, curr = next
    for y in range(GRID_H):
        for x in range(GRID_W):
            _u_prev[y][x] = _u_curr[y][x]
            _u_curr[y][x] = _u_next[y][x]


def draw():
    # Clear background
    draw_rect(-400, -300, 800, 600, color=(0.02, 0.04, 0.14), filled=True)

    # Render the grid
    for y in range(GRID_H):
        for x in range(GRID_W):
            if _walls[y][x]:
                # Draw barrier blocks
                px = -400 + (x * CELL_SIZE)
                py =  300 - (y * CELL_SIZE) - CELL_SIZE
                draw_rect(px, py, CELL_SIZE, CELL_SIZE, color=(0.3, 0.3, 0.4), filled=True)
                continue

            amp = _u_curr[y][x]
            
            # Optimization: don't draw empty space
            if abs(amp) < 0.05:
                continue

            # Convert amplitude to a color intensity
            # Positive peaks = Cyan/Blue, Negative troughs = Darker Blue
            intensity = min(1.0, max(0.0, abs(amp)))
            
            if amp > 0:
                color = (0.0, intensity * 0.8, intensity) # Cyan peaks
            else:
                color = (intensity * 0.5, 0.0, intensity) # Purple troughs

            # Map grid coordinates (0 to 100, 0 to 75) to OpenGL (-400 to 400, 300 to -300)
            px = -400 + (x * CELL_SIZE)
            py =  300 - (y * CELL_SIZE) - CELL_SIZE
            
            # Fill the cell
            draw_rect(px, py, CELL_SIZE, CELL_SIZE, color=color, filled=True)