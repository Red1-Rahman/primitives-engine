"""
Village Scenery
Moving objects : sun (translation), three birds (translation)
Algorithms     : run_dda            (hut roof outlines, bird wings),
                 run_midpoint_circle (sun outline via draw_circle),
                 run_2d_translation  (sun, birds),
                 run_2d_reflection   (right mountain mirrored from left)
"""
from engine.renderer import (
    draw_line_dda, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect,
)
from algorithms import run_2d_translation, run_2d_reflection

# ── palette ───────────────────────────────────────────────────────────────
SKY     = (0.53, 0.81, 0.98)
GROUND  = (0.18, 0.55, 0.18)
RIVER   = (0.26, 0.56, 0.88)
SUN_COL = (1.0,  0.92, 0.10)
MTN     = (0.52, 0.52, 0.57)
MTN2    = (0.47, 0.47, 0.52)
WALL1   = (0.82, 0.65, 0.30)
WALL2   = (0.78, 0.58, 0.24)
ROOF1   = (0.72, 0.22, 0.12)
ROOF2   = (0.62, 0.20, 0.10)
TRUNK   = (0.40, 0.20, 0.05)
FOLIAGE = (0.10, 0.50, 0.10)
DOOR    = (0.28, 0.14, 0.04)
BIRD    = (0.08, 0.08, 0.08)

GROUND_Y = -130

# River polygon flowing through the lower-centre of the scene
RIVER_PTS = [
    (-85, GROUND_Y), (-85, -300), (-45, -300),
    (45, -300), (85, -300), (85, GROUND_Y),
    (45, -148), (-45, -148),
]

# Left mountain triangle; right mountain = reflection across y-axis
MTN_L = [(-400, GROUND_Y), (-185, GROUND_Y), (-305, 20)]

# ── animation state ───────────────────────────────────────────────────────
_bird1_x = -440.0
_bird2_x = -260.0


def init():
    global _bird1_x, _bird2_x
    _bird1_x = -440.0
    _bird2_x = -260.0


def update():
    global _bird1_x, _bird2_x
    _bird1_x = _bird1_x + 1.2  if _bird1_x < 460 else -460.0
    _bird2_x = _bird2_x + 0.85 if _bird2_x < 460 else -460.0


# ── drawing helpers ───────────────────────────────────────────────────────

def _hut(cx, wall_col, roof_col):
    hw, wh = 32, 52
    draw_rect(cx - hw, GROUND_Y, hw * 2, wh, color=wall_col, filled=True)
    draw_rect(cx - 9,  GROUND_Y, 18,     26, color=DOOR,     filled=True)
    roof = [
        (cx - hw - 14, GROUND_Y + wh),
        (cx + hw + 14, GROUND_Y + wh),
        (cx,           GROUND_Y + wh + 43),
    ]
    draw_filled_polygon(roof, roof_col)
    # DDA outlines for the two slanting roof edges
    draw_line_dda(roof[0][0], roof[0][1], roof[2][0], roof[2][1], color=(0.18, 0.08, 0.0), size=2)
    draw_line_dda(roof[1][0], roof[1][1], roof[2][0], roof[2][1], color=(0.18, 0.08, 0.0), size=2)
    # chimney
    draw_rect(cx + 14, GROUND_Y + wh + 10, 10, 22, color=(0.55, 0.28, 0.10), filled=True)


def _tree(cx, r=32):
    draw_rect(cx - 6, GROUND_Y, 12, 44, color=TRUNK, filled=True)
    draw_filled_circle(cx, GROUND_Y + 44 + int(r * 0.65), r, FOLIAGE)


def _bird(cx, cy):
    """Tiny V-shape via two DDA segments."""
    draw_line_dda(cx - 13, cy - 6, cx,      cy,     color=BIRD, size=2)
    draw_line_dda(cx,      cy,     cx + 13, cy - 6, color=BIRD, size=2)


def draw():
    # sky
    draw_filled_polygon([(-400, GROUND_Y), (400, GROUND_Y), (400, 300), (-400, 300)], SKY)

    # mountains: left drawn directly, right = y-axis reflection of left
    draw_filled_polygon(MTN_L, MTN)
    _, mtn_r = run_2d_reflection(MTN_L, "y-axis")
    draw_filled_polygon(mtn_r, MTN2)

    # ground
    draw_filled_polygon([(-400, -300), (400, -300), (400, GROUND_Y), (-400, GROUND_Y)], GROUND)

    # river
    draw_filled_polygon(RIVER_PTS, RIVER)

    # sun — fixed position top-right
    draw_filled_circle(310, 210, 35, SUN_COL)
    draw_circle(310, 210, 35, (1.0, 0.75, 0.0), size=2)   # midpoint-circle outline

    # huts
    _hut(-240, WALL1, ROOF1)
    _hut( 240, WALL2, ROOF2)

    # trees
    _tree(-155)
    _tree(-78, r=27)
    _tree(108)
    _tree(345, r=30)

    # birds — translate base position each frame
    _, [(b1x, b1y)] = run_2d_translation([(0, 0)], _bird1_x,      185)
    _, [(b2x, b2y)] = run_2d_translation([(0, 0)], _bird2_x,      215)
    _, [(b3x, b3y)] = run_2d_translation([(0, 0)], _bird1_x - 35, 163)
    _bird(int(b1x), int(b1y))
    _bird(int(b2x), int(b2y))
    _bird(int(b3x), int(b3y))
