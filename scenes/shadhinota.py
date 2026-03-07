"""
Bangladesher Shadhinota — Independence Day scene
Moving objects : waving flag (shear), sun/flower decorations
Algorithms     : run_bresenham       (Memorial structural lines),
                 run_midpoint_circle  (Flag red disc, flower petals),
                 run_2d_shear         (Flag wave animation),
                 sutherland_hodgman   (Clip Bangladesh map)
"""
import math
from engine.renderer import (
    draw_line_bresenham, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect, draw_line_raw,
)
from algorithms import run_2d_translation, run_2d_shear, sutherland_hodgman

# ── palette ───────────────────────────────────────────────────────────────
SKY_COL      = (0.52, 0.80, 0.98)
GROUND_COL   = (0.20, 0.55, 0.20)
SOUDH_COL    = (0.90, 0.90, 0.90)  # Light concrete
SOUDH_OUT    = (0.60, 0.60, 0.60)
FLAG_GRN     = (0.0,  0.50, 0.22)
FLAG_RED     = (0.85, 0.10, 0.10)
POLE_COL     = (0.40, 0.40, 0.40)
MAP_COL      = (0.22, 0.62, 0.26)
MAP_OUT      = (0.10, 0.40, 0.14)
MAP_FRAME    = (0.44, 0.24, 0.06)
FLOWER_COL   = [(1.0, 0.28, 0.28), (1.0, 0.78, 0.18), (0.88, 0.18, 0.78)]

GROUND_Y = -130
MEMORIAL_CX = 140

# Bangladesh map outline (Updated with accurate high-fidelity coordinates)
_BD_MAP = [
    (-54.6, -73.3), (-52.1, -68.6), (-47.8, -68.6), (-42.7, -68.9), (-47.9, -72.5), 
    (-42.2, -71.9), (-35.9, -61.4), (-28.4, -58.5), (-26.9, -65.4), (-23.7, -63.0), 
    (-18.5, -50.7), (-18.3, -31.8), (17.8, -27.2), (30.1, -28.0), (40.7, -27.2), 
    (57.6, -26.0), (63.7, -20.0), (58.3, -17.9), (56.9, -6.7), (50.1, 2.5), 
    (44.2, 8.2), (41.1, 10.2), (32.8, 16.7), (30.1, 25.8), (33.6, 46.5), 
    (36.8, 44.8), (42.9, 48.6), (49.6, 35.0), (55.4, 25.3), (58.7, 29.5), 
    (64.0, 54.5), (69.3, 89.8), (66.4, 112.7), (61.8, 106.4), (58.5, 113.4), 
    (60.9, 127.5), (51.2, 107.2), (49.6, 90.7), (44.2, 73.4), (31.7, 56.9), 
    (28.5, 62.9), (26.5, 70.8), (18.4, 65.8), (11.8, 61.8), (9.8, 56.5), 
    (7.7, 51.1), (7.8, 52.5), (5.4, 58.3), (8.4, 61.0), (13.4, 73.4), 
    (7.2, 86.2), (5.8, 86.0), (3.9, 85.5), (6.4, 76.5), (3.3, 82.7), 
    (-4.1, 91.7), (-9.8, 89.5), (-9.7, 86.2), (-13.4, 84.3), (-14.3, 74.1), 
    (-14.2, 78.3), (-14.6, 83.5), (-17.6, 93.0), (-22.1, 93.3), (-25.7, 83.6), 
    (-26.8, 96.4), (-28.2, 94.0), (-31.0, 90.2), (-33.6, 93.0), (-36.2, 96.3), 
    (-39.7, 86.2), (-39.3, 81.4), (-41.8, 66.5), (-41.5, 58.2), (-44.9, 48.2), 
    (-47.4, 41.6), (-48.0, 33.5), (-51.3, 20.4), (-50.3, 10.1), (-56.0, 5.1), 
    (-67.7, -5.1), (-66.4, -17.5), (-58.9, -19.8), (-53.6, -27.4), (-49.0, -27.8), 
    (-46.7, -30.9), (-49.3, -34.1), (-53.3, -37.8), (-60.8, -45.3), (-68.3, -60.6), 
    (-62.0, -70.9), (-63.7, -75.2), (-56.4, -75.5)
]
_MAP_OX, _MAP_OY = -165, 100
# Frame sized to fully contain the flipped map extents (X: ±~69, Y: -28..+176) with padding
_FRAME = (_MAP_OX - 78, _MAP_OY - 140, _MAP_OX + 78, _MAP_OY + 85)

# Flag geometry
_FLAG_BASE = [(0, 0), (110, 0), (110, -65), (0, -65)]
FLAG_POLE_X, FLAG_POLE_TOP_Y = -40, 180


# ── animation state ───────────────────────────────────────────────────────
_shear_t = 0.0


def init():
    global _shear_t
    _shear_t = 0.0


def update():
    global _shear_t
    _shear_t = (_shear_t + 0.04) % (2 * math.pi)


# ── drawing helpers ───────────────────────────────────────────────────────

def _jatiyo_sriti_shoudho():
    """Draws the National Martyrs' Memorial with 7 triangular segments."""
    cx = MEMORIAL_CX
    by = GROUND_Y
    slabs = [(180, 60), (150, 85), (120, 115), (90, 150), (65, 190), (40, 230), (15, 270)]
    for width, height in slabs:
        pts = [(cx - width, by), (cx, by + height), (cx + width, by)]
        draw_filled_polygon(pts, SOUDH_COL)
        for i in range(len(pts)):
            p1, p2 = pts[i], pts[(i + 1) % len(pts)]
            draw_line_bresenham(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]), color=SOUDH_OUT, size=1)
    draw_rect(cx - 200, by - 10, 400, 10, color=(0.5, 0.5, 0.5), filled=True)


def _flag(shx):
    """Waving flag with shear transformation."""
    _, sheared = run_2d_shear(_FLAG_BASE, shx=shx, shy=0.0)
    _, placed  = run_2d_translation(sheared, FLAG_POLE_X, FLAG_POLE_TOP_Y)
    draw_filled_polygon(placed, FLAG_GRN)
    cx_disc = FLAG_POLE_X + 45 + int(shx * -30)
    cy_disc = FLAG_POLE_TOP_Y - 33
    draw_filled_circle(cx_disc, cy_disc, 22, FLAG_RED)
    draw_line_bresenham(FLAG_POLE_X, GROUND_Y, FLAG_POLE_X, FLAG_POLE_TOP_Y + 10, color=POLE_COL, size=4)


def _map():
    """Detailed Bangladesh map clipped using Sutherland-Hodgman."""
    shifted = [(x + _MAP_OX, -y + _MAP_OY) for x, y in _BD_MAP]
    xmin, ymin, xmax, ymax = _FRAME
    clipped = sutherland_hodgman(shifted, xmin, ymin, xmax, ymax)
    draw_rect(xmin - 5, ymin - 5, xmax - xmin + 10, ymax - ymin + 10, color=MAP_FRAME, filled=True)
    draw_rect(xmin, ymin, xmax - xmin, ymax - ymin, color=(0.95, 0.95, 0.90), filled=True)

    if clipped:
        draw_filled_polygon(clipped, MAP_COL)
        draw_polygon(clipped, MAP_OUT, width=2)


def draw():
    draw_filled_polygon([(-400, GROUND_Y), (400, GROUND_Y), (400, 400), (-400, 400)], SKY_COL)
    draw_filled_polygon([(-400, -400), (400, -400), (400, GROUND_Y), (-400, GROUND_Y)], GROUND_COL)
    _map()
    _jatiyo_sriti_shoudho()
    shx = math.sin(_shear_t) * 0.15
    _flag(shx)
    for i, fx in enumerate([-200, -170, -140, 10, 40, 70]):
        col = FLOWER_COL[i % len(FLOWER_COL)]
        draw_filled_circle(fx, GROUND_Y + 10, 8, col)
        draw_line_bresenham(fx, GROUND_Y, fx, GROUND_Y + 10, color=(0.1, 0.4, 0.1), size=2)
