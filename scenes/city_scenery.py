# scenes\city_scenery.py
"""
City Scenery  (night scene)
Moving objects : car (translation), cloud (translation)
Algorithms     : run_bresenham       (building edges),
                 run_midpoint_circle  (wheels, street-lamp glow via draw_circle),
                 run_2d_translation   (car, cloud),
                 run_cohen_sutherland (clip road lane-markings to viewport)
"""
from engine.renderer import (
    draw_line_bresenham, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect, draw_line_raw,
)
from algorithms import run_2d_translation, run_cohen_sutherland

# ── palette ───────────────────────────────────────────────────────────────
NIGHT_SKY = (0.05, 0.05, 0.15)
ROAD      = (0.28, 0.28, 0.30)
PAVEMENT  = (0.42, 0.42, 0.44)
BLDG1     = (0.24, 0.24, 0.38)
BLDG2     = (0.30, 0.20, 0.20)
BLDG3     = (0.18, 0.28, 0.24)
WIN_LIT   = (1.0,  0.95, 0.60)
WIN_DARK  = (0.10, 0.12, 0.22)
LAMP_COL  = (1.0,  0.92, 0.60)
CAR_COL   = (0.85, 0.15, 0.10)
WHEEL_C   = (0.12, 0.12, 0.12)
CLOUD     = (0.78, 0.78, 0.84)
MOON_COL  = (0.96, 0.96, 0.82)

ROAD_Y   = -200   # top of road / base of buildings
ROAD_BOT = -300   # screen bottom

# Car body polygon relative to (0, ROAD_Y) — six-sided silhouette
_CAR_BODY = [
    (-45, ROAD_Y),     (-45, ROAD_Y + 22),
    (-28, ROAD_Y + 38), (28, ROAD_Y + 38),
    ( 45, ROAD_Y + 22), (45, ROAD_Y),
]
_WHEEL_L = [(-28, ROAD_Y)]
_WHEEL_R = [( 28, ROAD_Y)]

# Cloud polygon (centred at origin)
_CLOUD_BASE = [(-55, 8), (-35, 22), (0, 28), (35, 22), (55, 8), (45, -8), (-45, -8)]

# ── animation state ───────────────────────────────────────────────────────
_car_x   = -460.0
_cloud_x = -430.0


def init():
    global _car_x, _cloud_x
    _car_x   = -460.0
    _cloud_x = -430.0


def update():
    global _car_x, _cloud_x
    _car_x   = _car_x   + 1.8 if _car_x   < 480 else -480.0
    _cloud_x = _cloud_x + 0.4 if _cloud_x < 480 else -480.0


# ── drawing helpers ───────────────────────────────────────────────────────

def _building(x, y_bot, w, h, col, win_rows=3, win_cols=2):
    """Filled building with Bresenham edge outlines and lit windows."""
    draw_rect(x, y_bot, w, h, color=col, filled=True)
    bx2, by2 = x + w, y_bot + h
    # Bresenham outlines for left, right, and top edges
    draw_line_bresenham(x,   y_bot, x,   by2, color=(0.62, 0.62, 0.68), size=1)
    draw_line_bresenham(bx2, y_bot, bx2, by2, color=(0.62, 0.62, 0.68), size=1)
    draw_line_bresenham(x,   by2,  bx2, by2,  color=(0.62, 0.62, 0.68), size=1)
    # windows
    ww     = max(6, w // (win_cols + 1) - 4)
    wh     = 10
    x_gap  = w // (win_cols + 1)
    y_step = h // (win_rows + 1)
    for row in range(1, win_rows + 1):
        for col in range(1, win_cols + 1):
            wx  = x + col * x_gap - ww // 2
            wy  = y_bot + row * y_step - wh // 2
            lit = (row + col) % 3 != 0
            draw_rect(wx, wy, ww, wh, color=WIN_LIT if lit else WIN_DARK, filled=True)


def _streetlamp(x):
    draw_line_bresenham(x, ROAD_Y, x, ROAD_Y + 70, color=(0.68, 0.68, 0.70), size=2)
    draw_line_bresenham(x, ROAD_Y + 70, x + 18, ROAD_Y + 80, color=(0.68, 0.68, 0.70), size=2)
    draw_filled_circle(x + 18, ROAD_Y + 80, 6, LAMP_COL)
    draw_circle(x + 18, ROAD_Y + 80, 12, (0.90, 0.84, 0.38), size=1)


def _car(offset_x):
    _, body = run_2d_translation(_CAR_BODY, offset_x, 0)
    _, wl   = run_2d_translation(_WHEEL_L,  offset_x, 0)
    _, wr   = run_2d_translation(_WHEEL_R,  offset_x, 0)
    draw_filled_polygon(body, CAR_COL)
    for (wx, wy) in [wl[0], wr[0]]:
        draw_filled_circle(wx, wy, 10, WHEEL_C)
        draw_circle(wx, wy, 10, (0.45, 0.28, 0.05), size=2)


def draw():
    # sky
    draw_filled_polygon([(-400, -300), (400, -300), (400, 300), (-400, 300)], NIGHT_SKY)

    # moon
    draw_filled_circle(310, 240, 28, MOON_COL)
    draw_circle(310, 240, 28, (0.88, 0.86, 0.68), size=2)

    # stars
    for sx, sy in [(-350,260),(-300,282),(-200,270),(-120,252),(50,290),(160,262),(220,280),(-60,285)]:
        draw_filled_circle(sx, sy, 2, (1.0, 1.0, 1.0))

    # buildings
    _building(-395, ROAD_Y, 100, 220, BLDG1, win_rows=5, win_cols=2)
    _building(-272, ROAD_Y,  80, 280, BLDG2, win_rows=6, win_cols=2)
    _building(-168, ROAD_Y, 120, 180, BLDG3, win_rows=4, win_cols=3)
    _building(  82, ROAD_Y,  88, 260, BLDG1, win_rows=6, win_cols=2)
    _building( 198, ROAD_Y, 110, 200, BLDG2, win_rows=5, win_cols=2)
    _building( 322, ROAD_Y,  78, 300, BLDG3, win_rows=7, win_cols=2)

    # pavement strip
    draw_filled_polygon(
        [(-400, ROAD_Y - 18), (400, ROAD_Y - 18), (400, ROAD_Y), (-400, ROAD_Y)],
        PAVEMENT,
    )

    # road surface
    draw_filled_polygon(
        [(-400, ROAD_BOT), (400, ROAD_BOT), (400, ROAD_Y - 18), (-400, ROAD_Y - 18)],
        ROAD,
    )

    # lane markings — generated wide, clipped to road viewport via Cohen-Sutherland
    lane_y = (ROAD_Y - 18 + ROAD_BOT) // 2
    for x0 in range(-560, 560, 60):
        _, p1, p2 = run_cohen_sutherland(
            x0, lane_y, x0 + 30, lane_y,
            -400, ROAD_BOT, 400, ROAD_Y - 18,
        )
        if p1 and p2:
            draw_line_raw(p1[0], p1[1], p2[0], p2[1], color=(0.96, 0.90, 0.10), width=2)

    # streetlamps
    _streetlamp(-340)
    _streetlamp(-100)
    _streetlamp( 140)
    _streetlamp( 370)

    # cloud
    _, cloud_pts = run_2d_translation(_CLOUD_BASE, _cloud_x, 248)
    draw_filled_polygon(cloud_pts, CLOUD)

    # car
    _car(_car_x)
