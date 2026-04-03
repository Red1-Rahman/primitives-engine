"""
Interior Design  — a furnished room
Moving objects : ceiling fan (rotation), clock minute hand (rotation)
Algorithms     : run_dda            (furniture edges, floor planks),
                 run_midpoint_circle (clock face, lamp glow via draw_circle),
                 run_2d_rotation     (fan blades, clock hand),
                 run_2d_translation  (position rotated blades at fan hub)
"""
import math
from engine.renderer import (
    draw_line_dda, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect,
)
from algorithms import run_2d_rotation, run_2d_translation

# ── palette ───────────────────────────────────────────────────────────────
WALL_COL    = (0.92, 0.88, 0.80)
FLOOR_COL   = (0.60, 0.38, 0.16)
WIN_COL     = (0.60, 0.82, 0.96)
CURTAIN_COL = (0.78, 0.22, 0.22)
DOOR_COL    = (0.52, 0.32, 0.10)
TABLE_COL   = (0.48, 0.28, 0.08)
CHAIR_COL   = (0.38, 0.20, 0.06)
SHELF_COL   = (0.42, 0.26, 0.08)
BOOK_COLS   = [
    (0.85, 0.15, 0.15), (0.15, 0.62, 0.15), (0.15, 0.15, 0.85),
    (0.85, 0.62, 0.10), (0.60, 0.18, 0.60), (0.90, 0.48, 0.10),
]
FAN_COL     = (0.80, 0.60, 0.20)
FAN_HUB     = (0.30, 0.30, 0.30)
CLOCK_COL   = (0.95, 0.95, 0.90)
HAND_COL    = (0.10, 0.10, 0.10)
LAMP_COL    = (1.0,  0.94, 0.68)

FLOOR_Y  = -140
CEIL_Y   =  255
FAN_CX, FAN_CY = 0, 180

# One fan blade: a rectangle pointing right from near-origin
_BLADE = [(-8, -5), (62, -5), (62, 5), (-8, 5)]

# ── animation state ───────────────────────────────────────────────────────
_fan_angle   = 0.0
_clock_angle = 90.0   # 90° = 12 o'clock in standard math coords


def init():
    global _fan_angle, _clock_angle
    _fan_angle   = 0.0
    _clock_angle = 90.0


def update():
    global _fan_angle, _clock_angle
    _fan_angle   = (_fan_angle   + 3.0)  % 360
    _clock_angle = (_clock_angle - 0.05) % 360    # clockwise = decreasing CCW angle


# ── drawing helpers ───────────────────────────────────────────────────────

def _chair(cx):
    draw_rect(cx - 18, FLOOR_Y + 36, 36, 8, color=CHAIR_COL, filled=True)
    draw_rect(cx + 12, FLOOR_Y + 36, 6,  40, color=CHAIR_COL, filled=True)
    draw_line_dda(cx - 12, FLOOR_Y + 36, cx - 12, FLOOR_Y, color=CHAIR_COL, size=2)
    draw_line_dda(cx + 15, FLOOR_Y + 36, cx + 15, FLOOR_Y, color=CHAIR_COL, size=2)


def _bookshelf(x, y, w=88, h=145):
    draw_rect(x, y, w, h, color=SHELF_COL, filled=True)
    for i in range(1, 4):
        sy = y + i * h // 4
        draw_line_dda(x, sy, x + w, sy, color=(0.28, 0.16, 0.04), size=2)
    # books on bottom two shelves
    for i, bc in enumerate(BOOK_COLS):
        draw_rect(x + 6 + i * 13, y + 3, 9, h // 4 - 6, color=bc, filled=True)
    for i, bc in enumerate(BOOK_COLS[:4]):
        draw_rect(x + 6 + i * 18, y + h // 4 + 3, 14, h // 4 - 6, color=bc, filled=True)


def _clock(cx, cy, r):
    draw_filled_circle(cx, cy, r, CLOCK_COL)
    draw_circle(cx, cy, r, (0.30, 0.30, 0.30), size=2)
    # 12 tick marks via DDA
    for i in range(12):
        a  = math.radians(i * 30)
        ix = int(cx + (r - 5) * math.cos(a))
        iy = int(cy + (r - 5) * math.sin(a))
        ox = int(cx +  r      * math.cos(a))
        oy = int(cy +  r      * math.sin(a))
        draw_line_dda(ix, iy, ox, oy, color=(0.20, 0.20, 0.20), size=2)
    # minute hand — rotated each frame via run_2d_rotation
    hand_r  = int(r * 0.72)
    _, [(hx, hy)] = run_2d_rotation([(0, hand_r)], _clock_angle, clockwise=True)
    draw_line_dda(cx, cy, int(cx + hx), int(cy + hy), color=HAND_COL, size=3)
    # hour hand (static at 3 o'clock)
    _, [(hx2, hy2)] = run_2d_rotation([(0, int(r * 0.50))], 0)
    draw_line_dda(cx, cy, int(cx + hx2), int(cy + hy2), color=HAND_COL, size=4)


def _fan():
    """4 blades — each rotated by current angle then translated to hub."""
    for i in range(4):
        blade_angle = _fan_angle + i * 90
        _, rotated = run_2d_rotation(_BLADE, blade_angle)
        _, placed  = run_2d_translation(rotated, FAN_CX, FAN_CY)
        draw_filled_polygon(placed, FAN_COL)
    draw_filled_circle(FAN_CX, FAN_CY, 10, FAN_HUB)
    draw_circle(FAN_CX, FAN_CY, 10, (0.50, 0.50, 0.50), size=2)
    draw_line_dda(FAN_CX, FAN_CY, FAN_CX, CEIL_Y, color=(0.52, 0.52, 0.52), size=3)


def draw():
    # wall (full background)
    draw_filled_polygon([(-400, FLOOR_Y), (400, FLOOR_Y), (400, CEIL_Y), (-400, CEIL_Y)], WALL_COL)

    # floor
    draw_filled_polygon([(-400, -300), (400, -300), (400, FLOOR_Y), (-400, FLOOR_Y)], FLOOR_COL)
    # floor planks via DDA
    for fy in range(-300, FLOOR_Y, 22):
        draw_line_dda(-400, fy, 400, fy, color=(0.48, 0.28, 0.06), size=1)

    # window (left side of back wall)
    draw_rect(-322, 18, 132, 152, color=WIN_COL,  filled=True)
    draw_rect(-322, 18, 132, 152, color=(0.30, 0.20, 0.08), width=3)
    draw_line_dda(-256, 18, -256, 170, color=(0.30, 0.20, 0.08), size=2)
    draw_line_dda(-322, 94, -190,  94, color=(0.30, 0.20, 0.08), size=2)
    # curtains
    draw_filled_polygon([(-342, 8), (-290, 8), (-322, 178), (-362, 178)], CURTAIN_COL)
    draw_filled_polygon([(-175, 8), (-162, 8), (-182, 178), (-175, 178)], CURTAIN_COL)

    # door (right wall)
    draw_rect(278, FLOOR_Y, 82, 132, color=DOOR_COL, filled=True)
    draw_rect(278, FLOOR_Y, 82, 132, color=(0.28, 0.16, 0.04), width=2)
    draw_filled_circle(286, FLOOR_Y + 66, 5, (0.82, 0.68, 0.08))

    # bookshelf (far left)
    _bookshelf(-396, FLOOR_Y)

    # table + table lamp
    draw_rect(-102, FLOOR_Y + 42, 182, 12, color=TABLE_COL, filled=True)
    draw_line_dda(-92, FLOOR_Y + 42, -92, FLOOR_Y, color=TABLE_COL, size=4)
    draw_line_dda( 72, FLOOR_Y + 42,  72, FLOOR_Y, color=TABLE_COL, size=4)
    draw_line_dda(-12, FLOOR_Y + 54, -12, FLOOR_Y + 92, color=(0.60, 0.60, 0.60), size=2)
    draw_filled_circle(-12, FLOOR_Y + 96, 14, LAMP_COL)
    draw_circle(-12, FLOOR_Y + 96, 14, (0.88, 0.78, 0.28), size=2)

    # chairs
    _chair(-158)
    _chair(  96)

    # wall clock
    _clock(158, 115, 36)

    # ceiling fan (animated)
    _fan()
