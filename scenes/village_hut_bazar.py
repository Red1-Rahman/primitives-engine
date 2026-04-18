# scenes\village_hut_bazar.py
"""
Village Hut-Bazar  — a rural marketplace
Moving objects : person walking (translation),
                 cart rolling leftward (translation, wheels via rotation)
Algorithms     : run_bresenham      (stall posts/roof edges, person body),
                 run_midpoint_circle (baskets, pond via draw_circle),
                 run_2d_translation  (person, cart),
                 run_2d_rotation     (cart wheel spokes)
"""
from engine.renderer import (
    draw_line_bresenham, draw_circle, draw_filled_circle,
    draw_polygon, draw_filled_polygon, draw_rect,
)
from algorithms import run_2d_translation, run_2d_rotation

# ── palette ───────────────────────────────────────────────────────────────
SKY_COL  = (0.67, 0.84, 0.94)
GROUND   = (0.62, 0.50, 0.28)
PATH     = (0.74, 0.64, 0.40)
POND     = (0.26, 0.58, 0.88)
STALL    = (0.68, 0.46, 0.18)
ROOF_COL = (0.48, 0.24, 0.06)
VEG_COL  = (0.18, 0.58, 0.18)
TRUNK    = (0.38, 0.18, 0.04)
SKIN     = (0.85, 0.55, 0.30)
SHIRT    = (0.20, 0.14, 0.62)
CART_COL = (0.52, 0.32, 0.10)
WHEEL_C  = (0.20, 0.10, 0.04)
KEEPER_SHIRT = (0.92, 0.88, 0.75)   # cream shirt for shopkeepers
CUST_SHIRT2  = (0.62, 0.18, 0.18)   # red shirt for second customer
CUST_SHIRT3  = (0.18, 0.44, 0.62)   # blue shirt for third customer (browsing)

GROUND_Y = -130
POND_CX, POND_CY = 310, GROUND_Y - 55

# Cart geometry relative to (0, GROUND_Y)
_CART_BODY = [(-42, 0),  (-42, 20), (42, 20), (42, 0)]
_WHEEL_L   = [(-26, 0)]
_WHEEL_R   = [( 26, 0)]
_SPOKE_TIP = [(0, 13)]    # rotated to find spoke end-point

# ── animation state ───────────────────────────────────────────────────────
_person_x   = -430.0
_customer2_x = 460.0
_cart_x    = 450.0
_wheel_ang = 0.0


def init():
    global _person_x, _customer2_x, _cart_x, _wheel_ang
    _person_x    = -430.0
    _customer2_x =  460.0
    _cart_x      =  450.0
    _wheel_ang   =  0.0


def update():
    global _person_x, _customer2_x, _cart_x, _wheel_ang
    _person_x    = _person_x    + 0.9  if _person_x    < 480  else -430.0
    _customer2_x = _customer2_x - 1.1  if _customer2_x > -480 else  460.0
    _cart_x      = _cart_x      - 1.3  if _cart_x      > -480 else  450.0
    _wheel_ang   = (_wheel_ang + 4) % 360


# ── drawing helpers ───────────────────────────────────────────────────────

def _shopkeeper(cx):
    """Static figure standing behind the counter — only upper body visible above it."""
    cy = GROUND_Y
    # body above counter level
    draw_line_bresenham(cx, cy + 50, cx, cy + 34, color=KEEPER_SHIRT, size=3)
    # arms resting on counter
    draw_line_bresenham(cx, cy + 44, cx - 18, cy + 36, color=SKIN, size=2)
    draw_line_bresenham(cx, cy + 44, cx + 18, cy + 36, color=SKIN, size=2)
    # head drawn last so it sits above body and baskets
    draw_filled_circle(cx, cy + 66, 12, SKIN)
    draw_circle(cx, cy + 66, 12, (0.48, 0.28, 0.08), size=2)


def _browsing_person(cx, cy, shirt_col):
    """Static customer looking at a stall (arms slightly forward)."""
    draw_filled_circle(cx, cy + 54, 14, SKIN)
    draw_circle(cx, cy + 54, 14, (0.48, 0.28, 0.08), size=2)
    draw_line_bresenham(cx, cy + 40, cx, cy + 14, color=shirt_col, size=3)
    # both arms reaching forward toward the stall
    draw_line_bresenham(cx, cy + 34, cx + 14, cy + 22, color=SKIN, size=2)
    draw_line_bresenham(cx, cy + 34, cx + 18, cy + 30, color=SKIN, size=2)
    draw_line_bresenham(cx, cy + 14, cx - 10, cy,      color=shirt_col, size=3)
    draw_line_bresenham(cx, cy + 14, cx + 10, cy,      color=shirt_col, size=3)


def _stall(cx, item_col):
    """One market stall: Bresenham posts + slant roof + counter + baskets."""
    hw = 46
    post_h = 68
    for px in [cx - hw, cx - hw // 2, cx + hw // 2, cx + hw]:
        draw_line_bresenham(px, GROUND_Y, px, GROUND_Y + post_h, color=(0.35, 0.18, 0.05), size=2)
    roof = [
        (cx - hw - 12, GROUND_Y + post_h),
        (cx + hw + 12, GROUND_Y + post_h),
        (cx + hw + 22, GROUND_Y + post_h + 26),
        (cx - hw - 22, GROUND_Y + post_h + 26),
    ]
    draw_filled_polygon(roof, ROOF_COL)
    draw_line_bresenham(roof[0][0], roof[0][1], roof[3][0], roof[3][1], color=(0.28, 0.10, 0.02), size=2)
    draw_line_bresenham(roof[1][0], roof[1][1], roof[2][0], roof[2][1], color=(0.28, 0.10, 0.02), size=2)
    # counter shelf
    draw_rect(cx - hw + 6, GROUND_Y + 28, (hw - 6) * 2, 10, color=STALL, filled=True)
    # baskets on counter (midpoint-circle rings)
    for i in range(3):
        bx = cx - 22 + i * 22
        by = GROUND_Y + 42
        draw_filled_circle(bx, by, 10, item_col)
        draw_circle(bx, by, 10, (0.28, 0.16, 0.02), size=2)
    # shopkeeper drawn last so head appears above counter and baskets
    _shopkeeper(cx)


def _tree(cx):
    draw_rect(cx - 6, GROUND_Y, 12, 46, color=TRUNK, filled=True)
    draw_filled_circle(cx, GROUND_Y + 68, 32, VEG_COL)


def _person(cx, cy):
    """Stick figure using Bresenham lines."""
    # head
    draw_filled_circle(cx, cy + 54, 14, SKIN)
    draw_circle(cx, cy + 54, 14, (0.48, 0.28, 0.08), size=2)
    # body
    draw_line_bresenham(cx, cy + 40, cx, cy + 14, color=SHIRT, size=3)
    # arms (one forward, one back to simulate walking)
    draw_line_bresenham(cx, cy + 34, cx - 16, cy + 18, color=SKIN, size=2)
    draw_line_bresenham(cx, cy + 34, cx + 16, cy + 26, color=SKIN, size=2)
    # legs
    draw_line_bresenham(cx, cy + 14, cx - 12, cy,      color=SHIRT, size=3)
    draw_line_bresenham(cx, cy + 14, cx + 10, cy,      color=SHIRT, size=3)


def _cart(offset_x):
    _, body = run_2d_translation(_CART_BODY, offset_x, GROUND_Y)
    draw_filled_polygon(body, CART_COL)
    # wheels with rotating spokes
    for wpt in [_WHEEL_L, _WHEEL_R]:
        _, [(wx, wy)] = run_2d_translation(wpt, offset_x, GROUND_Y)
        draw_filled_circle(wx, wy, 14, WHEEL_C)
        draw_circle(wx, wy, 14, (0.48, 0.28, 0.06), size=2)
        for i in range(4):
            spoke_angle = _wheel_ang + i * 90
            _, [(sx, sy)] = run_2d_rotation(_SPOKE_TIP, spoke_angle)
            draw_line_bresenham(int(wx), int(wy), int(wx + sx), int(wy + sy), color=(0.68, 0.42, 0.12), size=2)


def draw():
    # sky
    draw_filled_polygon([(-400, GROUND_Y), (400, GROUND_Y), (400, 300), (-400, 300)], SKY_COL)
    # ground
    draw_filled_polygon([(-400, -300), (400, -300), (400, GROUND_Y), (-400, GROUND_Y)], GROUND)
    # dirt path along bottom
    draw_filled_polygon(
        [(-400, GROUND_Y - 42), (400, GROUND_Y - 42), (400, GROUND_Y), (-400, GROUND_Y)],
        PATH,
    )

    # market stalls
    _stall(-250, (0.78, 0.48, 0.14))
    _stall(-110, (0.20, 0.58, 0.20))
    _stall(  28, (0.88, 0.14, 0.14))
    _stall( 162, (0.88, 0.68, 0.18))

    # trees
    _tree(-375)
    _tree( 240)
    _tree( 375)

    # static browsing customers in front of stalls (drawn before cart so cart passes in front)
    _browsing_person(-172, GROUND_Y, CUST_SHIRT2)
    _browsing_person(  66, GROUND_Y, CUST_SHIRT3)

    # walking customer 1 (left → right)
    _, [(px, py)] = run_2d_translation([(0, 0)], _person_x, GROUND_Y)
    _person(int(px), int(py))

    # walking customer 2 (right → left)
    _, [(px2, py2)] = run_2d_translation([(0, 0)], _customer2_x, GROUND_Y)
    _person(int(px2), int(py2))

    # cart (animated) — drawn last so it passes in front of everyone
    _cart(_cart_x)
