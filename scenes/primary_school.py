# scenes\primary_school.py
"""
Primary School  — school building and playground
Moving objects : bouncing ball (translation + simulated gravity),
                 running child (translation),
                 waving flag   (shear)
Algorithms     : run_dda            (building outlines, fence, window cross-hairs),
                 run_midpoint_circle (ball, playground circle via draw_circle),
                 run_2d_translation  (ball, child),
                 run_2d_shear        (flag wave)
"""
import math
from engine.renderer import (
    draw_line_dda, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect,
)
from algorithms import run_2d_translation, run_2d_shear

# ── palette ───────────────────────────────────────────────────────────────
SKY_COL   = (0.67, 0.85, 0.95)
GROUND_COL= (0.25, 0.60, 0.22)
BLDG_COL  = (0.90, 0.86, 0.78)
ROOF_COL  = (0.72, 0.22, 0.12)
WIN_COL   = (0.60, 0.82, 0.96)
DOOR_COL  = (0.50, 0.30, 0.10)
POLE_COL  = (0.72, 0.68, 0.64)
FLAG_GRN  = (0.04, 0.50, 0.20)
FLAG_RED  = (0.85, 0.12, 0.12)
TRUNK_COL = (0.38, 0.18, 0.04)
FOLIAGE   = (0.12, 0.52, 0.12)
BALL_COL  = (0.95, 0.28, 0.10)
SKIN      = (0.85, 0.60, 0.35)
SHIRT     = (0.28, 0.18, 0.72)
FENCE_COL = (0.74, 0.68, 0.58)

GROUND_Y = -130

# Flag polygon: rectangle relative to pole-top-left at origin, pointing right
_FLAG_BASE = [(0, 0), (72, 0), (72, -44), (0, -44)]
FLAG_POLE_X, FLAG_POLE_TOP_Y = -340, 140

# ── animation state ───────────────────────────────────────────────────────
_ball_x  = -100.0
_ball_y  =   60.0
_ball_vy =   -2.5
_ball_vx =    1.4
_child_x = -390.0
_shear_t =    0.0

BOUNCE_Y = GROUND_Y + 12    # lowest point for ball


def init():
    global _ball_x, _ball_y, _ball_vy, _ball_vx, _child_x, _shear_t
    _ball_x  = -100.0
    _ball_y  = 60.0
    _ball_vy = -2.5
    _ball_vx =  1.4
    _child_x = -390.0
    _shear_t = 0.0


def update():
    global _ball_x, _ball_y, _ball_vy, _ball_vx, _child_x, _shear_t
    # gravity
    _ball_vy -= 0.12
    _ball_y  += _ball_vy
    _ball_x  += _ball_vx
    if _ball_y <= BOUNCE_Y:
        _ball_y  = BOUNCE_Y
        _ball_vy = abs(_ball_vy) * 0.82
        if _ball_vy < 0.8:
            _ball_vy = 3.6   # re-kick when almost stopped
    if _ball_x > 210 or _ball_x < -210:
        _ball_vx *= -1
    # child
    _child_x  = _child_x + 1.1 if _child_x < 480 else -390.0
    # flag shear
    _shear_t = (_shear_t + 0.04) % (2 * math.pi)


# ── drawing helpers ───────────────────────────────────────────────────────

def _building():
    # ground floor
    draw_rect(-392, GROUND_Y, 282, 152, color=BLDG_COL, filled=True)
    # upper storey
    draw_rect(-382, GROUND_Y + 152, 262, 112, color=BLDG_COL, filled=True)
    # roof
    roof = [(-392, GROUND_Y + 264), (-110, GROUND_Y + 264),
            (-78,  GROUND_Y + 300), (-424, GROUND_Y + 300)]
    draw_filled_polygon(roof, ROOF_COL)
    # DDA outline edges
    draw_line_dda(-392, GROUND_Y, -392, GROUND_Y + 264, color=(0.70, 0.64, 0.54), size=2)
    draw_line_dda(-110, GROUND_Y, -110, GROUND_Y + 264, color=(0.70, 0.64, 0.54), size=2)
    # ground floor windows (3)
    for i in range(3):
        wx = -362 + i * 84
        wy = GROUND_Y + 52
        draw_rect(wx, wy, 42, 52, color=WIN_COL, filled=True)
        draw_line_dda(wx, wy + 26, wx + 42, wy + 26, color=(0.30, 0.50, 0.72), size=2)
        draw_line_dda(wx + 21, wy, wx + 21, wy + 52, color=(0.30, 0.50, 0.72), size=2)
    # upper floor windows (2)
    for i in range(2):
        wx = -342 + i * 112
        wy = GROUND_Y + 178
        draw_rect(wx, wy, 42, 52, color=WIN_COL, filled=True)
        draw_line_dda(wx, wy + 26, wx + 42, wy + 26, color=(0.30, 0.50, 0.72), size=2)
        draw_line_dda(wx + 21, wy, wx + 21, wy + 52, color=(0.30, 0.50, 0.72), size=2)
    # main door
    draw_rect(-269, GROUND_Y, 52, 72, color=DOOR_COL, filled=True)
    draw_line_dda(-243, GROUND_Y, -243, GROUND_Y + 72, color=(0.32, 0.18, 0.04), size=2)


def _tree(cx):
    draw_rect(cx - 6, GROUND_Y, 12, 46, color=TRUNK_COL, filled=True)
    draw_filled_circle(cx, GROUND_Y + 68, 32, FOLIAGE)


def _fence():
    """Horizontal rail + vertical posts via DDA."""
    xs, xe, y = 30, 400, GROUND_Y + 22
    draw_line_dda(xs, y, xe, y, color=FENCE_COL, size=3)
    for px in range(xs, xe + 1, 22):
        draw_line_dda(px, GROUND_Y, px, y + 8, color=FENCE_COL, size=2)


def _flag(shx):
    _, sheared = run_2d_shear(_FLAG_BASE, shx=shx, shy=0.0)
    _, placed  = run_2d_translation(sheared, FLAG_POLE_X, FLAG_POLE_TOP_Y)
    draw_filled_polygon(placed, FLAG_GRN)
    cx_disc = FLAG_POLE_X + 28 + int(shx * (-22))
    cy_disc = FLAG_POLE_TOP_Y - 22
    draw_filled_circle(cx_disc, cy_disc, 14, FLAG_RED)
    draw_circle(cx_disc, cy_disc, 14, (0.64, 0.06, 0.06), size=2)
    draw_line_dda(FLAG_POLE_X, GROUND_Y, FLAG_POLE_X, FLAG_POLE_TOP_Y + 10, color=POLE_COL, size=3)


def _child(cx, cy):
    draw_filled_circle(cx, cy + 44, 12, SKIN)
    draw_line_dda(cx, cy + 32, cx, cy + 12, color=SHIRT, size=3)
    draw_line_dda(cx, cy + 26, cx - 14, cy + 16, color=SKIN, size=2)
    draw_line_dda(cx, cy + 26, cx + 14, cy + 18, color=SKIN, size=2)
    draw_line_dda(cx, cy + 12, cx - 11, cy,      color=SHIRT, size=3)
    draw_line_dda(cx, cy + 12, cx + 11, cy,      color=SHIRT, size=3)


def draw():
    # sky
    draw_filled_polygon([(-400, GROUND_Y), (400, GROUND_Y), (400, 300), (-400, 300)], SKY_COL)
    # ground
    draw_filled_polygon([(-400, -300), (400, -300), (400, GROUND_Y), (-400, GROUND_Y)], GROUND_COL)

    # school building
    _building()

    # flag + pole
    shx = math.sin(_shear_t) * 0.20
    _flag(shx)

    # trees
    _tree( 92)
    _tree(192)
    _tree(372)

    # fence
    _fence()

    # playground circle (midpoint-circle algorithm)
    draw_circle(205, GROUND_Y + 8, 62, (0.84, 0.68, 0.28), size=2)

    # bouncing ball
    _, [(bx, by)] = run_2d_translation([(0, 0)], _ball_x, _ball_y)
    draw_filled_circle(bx, by, 12, BALL_COL)
    draw_circle(bx, by, 12, (0.74, 0.18, 0.04), size=2)

    # running child
    _, [(cx2, cy2)] = run_2d_translation([(0, 0)], _child_x, GROUND_Y)
    _child(int(cx2), int(cy2))
