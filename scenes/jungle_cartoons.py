# scenes\jungle_cartoons.py
"""
Three Cartoons in Jungle
Moving objects : three cartoon characters at different speeds/directions,
                 each with swinging arms (rotation)
Algorithms     : run_bresenham      (tree trunks, hanging vines),
                 run_midpoint_circle (character heads, jungle fruits via draw_circle),
                 run_2d_translation  (all three characters),
                 run_2d_rotation     (arm swing)
"""
import math
from engine.renderer import (
    draw_line_bresenham, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect,
)
from algorithms import run_2d_translation, run_2d_rotation

# ── palette ───────────────────────────────────────────────────────────────
SKY_COL   = (0.10, 0.22, 0.38)     # deep blue sky through jungle canopy
GROUND_COL= (0.14, 0.42, 0.12)
TRUNK_COL = (0.32, 0.16, 0.04)
FOLIAGE   = [(0.06, 0.44, 0.06), (0.10, 0.52, 0.10), (0.04, 0.36, 0.04)]
VINE_COL  = (0.18, 0.42, 0.10)
FRUIT_COL = [(0.94, 0.14, 0.14), (0.94, 0.72, 0.08), (0.58, 0.08, 0.78)]
CHAR_DEF  = [
    {"skin": (1.0, 0.80, 0.55), "body": (0.20, 0.40, 0.92), "hat": (0.90, 0.18, 0.18)},
    {"skin": (0.90, 0.62, 0.30), "body": (0.18, 0.70, 0.28), "hat": (0.92, 0.70, 0.08)},
    {"skin": (0.80, 0.48, 0.26), "body": (0.70, 0.18, 0.62), "hat": (0.18, 0.18, 0.90)},
]

GROUND_Y = -130

# Arm endpoint relative to shoulder (points straight down)
_ARM_TIP = [(0, -32)]

# ── animation state ───────────────────────────────────────────────────────
_chars = []


def init():
    global _chars
    _chars = [
        {"x": -430.0, "vx":  1.1, "arm_t": 0.0,  "arm_spd": 3.2},
        {"x":  450.0, "vx": -0.8, "arm_t": 1.5,  "arm_spd": 2.6},
        {"x": -180.0, "vx":  0.6, "arm_t": 3.0,  "arm_spd": 4.0},
    ]


def update():
    for c in _chars:
        c["x"] += c["vx"]
        if c["x"] > 480:
            c["x"] = -480.0
        elif c["x"] < -480:
            c["x"] =  480.0
        c["arm_t"] = (c["arm_t"] + math.radians(c["arm_spd"])) % (2 * math.pi)


# ── drawing helpers ───────────────────────────────────────────────────────

def _tree(cx, height, r, col_idx=0):
    """Jungle tree: twin Bresenham trunks + layered foliage + fruit."""
    fc = FOLIAGE[col_idx % len(FOLIAGE)]
    draw_line_bresenham(cx - 7, GROUND_Y, cx - 7, GROUND_Y + height, color=TRUNK_COL, size=6)
    draw_line_bresenham(cx + 7, GROUND_Y, cx + 7, GROUND_Y + height, color=TRUNK_COL, size=6)
    draw_filled_circle(cx,      GROUND_Y + height,      r,      fc)
    draw_filled_circle(cx - 20, GROUND_Y + height - 26, r - 10, fc)
    draw_filled_circle(cx + 18, GROUND_Y + height - 22, r - 8,  fc)
    # fruit cluster
    fc2 = FRUIT_COL[col_idx % len(FRUIT_COL)]
    draw_filled_circle(cx + 28, GROUND_Y + height - 12, 9, fc2)
    draw_circle(cx + 28,        GROUND_Y + height - 12, 9, (0.58, 0.06, 0.06), size=2)


def _vine(x1, y1, x2, y2):
    """Wavy vine built from short Bresenham segments."""
    segs = 8
    for i in range(segs):
        t0 = i / segs;       t1 = (i + 1) / segs
        sx = int(x1 + t0 * (x2 - x1) + math.sin(t0 * 4 * math.pi) * 12)
        sy = int(y1 + t0 * (y2 - y1))
        ex = int(x1 + t1 * (x2 - x1) + math.sin(t1 * 4 * math.pi) * 12)
        ey = int(y1 + t1 * (y2 - y1))
        draw_line_bresenham(sx, sy, ex, ey, color=VINE_COL, size=2)


def _cartoon(cx, cy, colors, arm_deg):
    skin = colors["skin"]
    body = colors["body"]
    hat  = colors["hat"]
    # legs (drawn first, behind everything)
    draw_line_bresenham(cx - 7, cy + 18, cx - 10, cy,     color=skin, size=4)
    draw_line_bresenham(cx + 7, cy + 18, cx + 10, cy,     color=skin, size=4)
    # body
    draw_rect(cx - 14, cy + 18, 28, 38, color=body, filled=True)
    # arms
    _, [(ax,  ay )] = run_2d_rotation(_ARM_TIP,  arm_deg)
    draw_line_bresenham(cx + 14, cy + 36, int(cx + 14 + ax),  int(cy + 36 + ay),  color=skin, size=4)
    _, [(ax2, ay2)] = run_2d_rotation(_ARM_TIP, -arm_deg)
    draw_line_bresenham(cx - 14, cy + 36, int(cx - 14 + ax2), int(cy + 36 + ay2), color=skin, size=4)
    # head drawn last so it always appears on top of body/arms
    draw_filled_circle(cx, cy + 56, 18, skin)
    draw_circle(cx, cy + 56, 18, (0.38, 0.18, 0.04), size=2)
    # hat
    hat_pts = [(cx - 18, cy + 74), (cx + 18, cy + 74), (cx + 12, cy + 92), (cx - 12, cy + 92)]
    draw_filled_polygon(hat_pts, hat)
    # eyes
    draw_filled_circle(cx - 7, cy + 59, 4, (0.04, 0.04, 0.04))
    draw_filled_circle(cx + 7, cy + 59, 4, (0.04, 0.04, 0.04))
    # smile
    for angle in range(200, 340, 12):
        a  = math.radians(angle)
        draw_filled_circle(int(cx + 10 * math.cos(a)), int(cy + 56 + 10 * math.sin(a)), 2, (0.28, 0.08, 0.04))


def draw():
    # jungle sky (dark canopy)
    draw_filled_polygon([(-400, GROUND_Y), (400, GROUND_Y), (400, 300), (-400, 300)], SKY_COL)
    # ground
    draw_filled_polygon([(-400, -300), (400, -300), (400, GROUND_Y), (-400, GROUND_Y)], GROUND_COL)

    # background trees
    for cx, h, r, ci in [
        (-385, 178, 55, 0), (-290, 202, 62, 1), (-188, 172, 52, 2),
        ( -90, 198, 66, 0), (   0, 176, 54, 1), ( 100, 202, 62, 2),
        ( 200, 174, 56, 0), ( 298, 192, 58, 1), ( 385, 170, 50, 2),
    ]:
        _tree(cx, h, r, ci)

    # hanging vines
    _vine(-290, GROUND_Y + 202, -262, GROUND_Y + 42)
    _vine( 100, GROUND_Y + 202,  128, GROUND_Y + 32)
    _vine( 298, GROUND_Y + 192,  282, GROUND_Y + 48)

    # foreground bushes
    for bx in [-355, -242, -58, 62, 222, 352]:
        draw_filled_circle(bx,      GROUND_Y + 14, 22, FOLIAGE[0])
        draw_filled_circle(bx + 18, GROUND_Y +  9, 18, FOLIAGE[1])

    # three animated cartoon characters
    for i, c in enumerate(_chars):
        arm_deg = math.sin(c["arm_t"]) * 22
        _, [(cx, cy)] = run_2d_translation([(0, 0)], c["x"], GROUND_Y)
        _cartoon(int(cx), int(cy), CHAR_DEF[i], arm_deg)
