# scenes\KnowlegeTower.py
import math

from engine.renderer import (
	draw_line_dda,
	draw_line_bresenham,
	draw_circle,
	draw_rect,
	draw_polygon,
	draw_filled_polygon,
	draw_text,
)
from algorithms import run_2d_translation


# ---------------------------------------------------------------------------
# Source-space (reference drawing) -> engine world-space mapping helpers
# ---------------------------------------------------------------------------
SRC_W, SRC_H = 900.0, 700.0
WORLD_W, WORLD_H = 800.0, 600.0


def _mx(x):
	return (x / SRC_W) * WORLD_W - 400.0


def _my(y):
	return (y / SRC_H) * WORLD_H - 300.0


def _mw(w):
	return (w / SRC_W) * WORLD_W


def _mh(h):
	return (h / SRC_H) * WORLD_H


def _srect(x, y, w, h, color, filled=True, width=1.0):
	draw_rect(_mx(x), _my(y), _mw(w), _mh(h), color=color, filled=filled, width=width)


def _sline_dda(x1, y1, x2, y2, color, size=1.0):
	draw_line_dda(_mx(x1), _my(y1), _mx(x2), _my(y2), color=color, size=size)


def _sline_bres(x1, y1, x2, y2, color, size=1.0):
	draw_line_bresenham(_mx(x1), _my(y1), _mx(x2), _my(y2), color=color, size=size)


def _spoly(points, color, filled=True, width=1.0, closed=True):
	mapped = [(_mx(x), _my(y)) for x, y in points]
	if filled:
		draw_filled_polygon(mapped, color=color)
	else:
		draw_polygon(mapped, color=color, width=width, closed=closed)


def _ellipse_points(cx, cy, rx, ry, a1=0.0, a2=360.0, segments=64):
	pts = []
	for i in range(segments + 1):
		t = math.radians(a1 + (a2 - a1) * i / segments)
		pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
	return pts


def _draw_filled_ellipse(cx, cy, rx, ry, color, segments=64):
	_spoly(_ellipse_points(cx, cy, rx, ry, 0, 360, segments), color=color, filled=True)


def _draw_ellipse_outline(cx, cy, rx, ry, color, width=1.0, segments=64):
	_spoly(
		_ellipse_points(cx, cy, rx, ry, 0, 360, segments),
		color=color,
		filled=False,
		width=width,
		closed=True,
	)


def _draw_arc_outline(cx, cy, rx, ry, a1, a2, color, width=1.0, segments=64):
	_spoly(
		_ellipse_points(cx, cy, rx, ry, a1, a2, segments),
		color=color,
		filled=False,
		width=width,
		closed=False,
	)


def _draw_arc_band(cx, cy, rx_in, ry_in, rx_out, ry_out, a1, a2, color, segments=72):
	outer = _ellipse_points(cx, cy, rx_out, ry_out, a1, a2, segments)
	inner = _ellipse_points(cx, cy, rx_in, ry_in, a2, a1, segments)
	_spoly(outer + inner, color=color, filled=True)


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
SKY_TOP = (0.42, 0.72, 0.95)
SKY_BOT = (0.65, 0.88, 1.0)
LAWN = (0.28, 0.62, 0.22)
PAVEMENT = (0.78, 0.76, 0.70)

BODY = (0.88, 0.90, 0.92)
BODY2 = (0.86, 0.88, 0.90)
GLASS = (0.30, 0.52, 0.78)
FRAME = (0.75, 0.80, 0.85)
OUTLINE = (0.58, 0.64, 0.70)
WHITE_BAND = (0.95, 0.95, 0.95)

COPPER = (0.56, 0.29, 0.09)
COPPER_DARK = (0.35, 0.18, 0.05)
COPPER_HL = (0.72, 0.40, 0.12)

PALM_TRUNK = (0.42, 0.28, 0.12)
PALM_LEAF = (0.14, 0.55, 0.16)


# ---------------------------------------------------------------------------
# Building layout in source coordinates (the reference code's coordinate space)
# ---------------------------------------------------------------------------
GY = 195

LW_X = 75
LW_W = 220
LW_FH = 32
LW_FL = 10
LW_Y = GY
LW_TOP = LW_Y + LW_FH * LW_FL

ELEV_X = 236
ELEV_W = 36

RW_X = 560
RW_W = 265
RW_FH = 32
RW_FL = 10
RW_Y = GY
RW_TOP = RW_Y + RW_FH * RW_FL

CW_X = 290
CW_W = 275
CW_Y = GY + 110
CW_TOP = LW_TOP

ROT_CX = (LW_X + LW_W + RW_X) // 2
ROT_BASE_Y = GY + 55
ROT_TOP_Y = RW_TOP - 32
ROT_CY = (ROT_BASE_Y + ROT_TOP_Y) // 2
ROT_RY = (ROT_TOP_Y - ROT_BASE_Y) // 2
ROT_RX = 145

CAN_CX = ROT_CX
CAN_CY = ROT_TOP_Y - 14
CAN_RX_OUT = ROT_RX + 42
CAN_RY_OUT = 26
CAN_RX_IN = ROT_RX - 8
CAN_RY_IN = 14
CAN_A1, CAN_A2 = 12, 168

ENT_CANOPY_Y = GY + 90
ENT_CANOPY_H = 14
ENT_CANOPY_HALF_W = 96

STAIR_STEPS = 6
STAIR_SH = 11
STAIR_TOP_W = 220
STAIR_EXPAND = 14


# ---------------------------------------------------------------------------
# Animation state
# ---------------------------------------------------------------------------
_cloud_x = 0.0


def init():
	global _cloud_x
	_cloud_x = 0.0


def update():
	global _cloud_x
	_cloud_x += 0.55
	if _cloud_x > 250.0:
		_cloud_x = -250.0


# ---------------------------------------------------------------------------
# Scene pieces
# ---------------------------------------------------------------------------
def _draw_sky_ground():
	_srect(0, 170, 900, 530, SKY_TOP, filled=True)
	_srect(0, 170, 900, 240, SKY_BOT, filled=True)
	_srect(0, 0, 900, 210, LAWN, filled=True)
	_srect(200, 155, 500, 50, PAVEMENT, filled=True)


def _draw_cloud(cx, cy, scale):
	c = (1.0, 1.0, 1.0)
	parts = [
		(0, 0, 38, 22),
		(-30, -5, 25, 16),
		(28, -4, 26, 17),
		(-10, 10, 18, 12),
		(12, 10, 20, 13),
	]
	for dx, dy, rx, ry in parts:
		_draw_filled_ellipse(cx + dx * scale, cy + dy * scale, rx * scale, ry * scale, c, segments=36)


def _draw_clouds():
	_, [(dx, _)] = run_2d_translation([(0.0, 0.0)], _cloud_x, 0.0)
	_draw_cloud(130 + dx, 630, 1.0)
	_draw_cloud(380 + dx, 660, 1.3)
	_draw_cloud(650 + dx, 650, 1.1)
	_draw_cloud(820 + dx, 620, 0.85)
	_draw_cloud(60 + dx, 600, 0.7)

	# repeating set for seamless wrap
	_draw_cloud(-120 + dx, 640, 1.0)
	_draw_cloud(140 + dx, 610, 0.8)


def _window_grid(x, y, w, h, cols, rows):
	bay_w = w / cols
	floor_h = h / rows
	for col in range(cols):
		bx = x + col * bay_w + 8
		bw = bay_w - 16
		for fl in range(rows):
			wy = y + fl * floor_h + 7
			wh = floor_h - 14
			_srect(bx, wy, bw, wh, GLASS, filled=True)
			_srect(bx, wy, bw, wh, FRAME, filled=False, width=1.0)


def _draw_left_wing():
	_srect(LW_X, LW_Y, LW_W, LW_FH * LW_FL, BODY, filled=True)

	for fl in range(1, LW_FL + 1):
		y = LW_Y + fl * LW_FH
		_sline_bres(LW_X, y, LW_X + LW_W, y, color=(1.0, 1.0, 1.0), size=1.0)

	_window_grid(LW_X, LW_Y, LW_W, LW_FH * LW_FL, cols=4, rows=LW_FL)

	_srect(LW_X, LW_Y, LW_W, LW_FH * LW_FL, OUTLINE, filled=False, width=2.0)
	_srect(LW_X - 2, LW_TOP, LW_W + 4, 12, WHITE_BAND, filled=True)
	_srect(LW_X - 2, LW_TOP, LW_W + 4, 12, OUTLINE, filled=False, width=1.5)


def _draw_elevator_tower():
	tx, tw, ty, th = ELEV_X, ELEV_W, GY, LW_FH * LW_FL + 34
	_srect(tx, ty, tw, th, (0.68, 0.81, 0.92), filled=True)
	_srect(tx - 2, ty + th, tw + 4, 8, (0.84, 0.88, 0.93), filled=True)

	seg_h = th / 13
	for i in range(13):
		sy = ty + i * seg_h + 3
		sh = seg_h - 5
		_srect(tx + 5, sy, tw - 10, sh, (0.30, 0.55, 0.82), filled=True)

	_srect(tx, ty, tw, th, (0.50, 0.60, 0.70), filled=False, width=1.4)
	_srect(tx - 2, ty + th, tw + 4, 8, (0.50, 0.60, 0.70), filled=False, width=1.0)


def _draw_right_wing():
	_srect(RW_X, RW_Y, RW_W, RW_FH * RW_FL, BODY, filled=True)

	for fl in range(1, RW_FL + 1):
		y = RW_Y + fl * RW_FH
		_sline_bres(RW_X, y, RW_X + RW_W, y, color=(1.0, 1.0, 1.0), size=1.0)

	_window_grid(RW_X, RW_Y, RW_W, RW_FH * RW_FL, cols=5, rows=RW_FL)

	for fl in range(1, RW_FL + 1):
		y = RW_Y + fl * RW_FH - 4
		_srect(RW_X - 5, y, RW_W + 10, 5, (0.94, 0.94, 0.94), filled=True)

	_srect(RW_X, RW_Y, RW_W, RW_FH * RW_FL, OUTLINE, filled=False, width=2.0)
	_srect(RW_X - 2, RW_TOP, RW_W + 4, 12, WHITE_BAND, filled=True)
	_srect(RW_X - 2, RW_TOP, RW_W + 4, 12, OUTLINE, filled=False, width=1.5)


def _draw_center_block():
	_srect(CW_X, CW_Y, CW_W, CW_TOP - CW_Y, BODY2, filled=True)
	floor_h = (CW_TOP - CW_Y) / 6

	for fl in range(1, 7):
		y = CW_Y + fl * floor_h
		_sline_bres(CW_X, y, CW_X + CW_W, y, color=(0.95, 0.95, 0.95), size=1.0)

	bay_w = CW_W / 3
	for col in range(3):
		bx = CW_X + col * bay_w + 10
		bw = bay_w - 20
		for fl in range(3, 6):
			wy = CW_Y + fl * floor_h + 6
			wh = floor_h - 11
			_srect(bx, wy, bw, wh, GLASS, filled=True)
			_srect(bx, wy, bw, wh, FRAME, filled=False, width=1.0)


def _draw_rotunda():
	# D-like front body: top arc + flat bottom edge
	top_arc = _ellipse_points(ROT_CX, ROT_CY, ROT_RX, ROT_RY, 180, 0, 72)
	body_pts = [(ROT_CX - ROT_RX, ROT_BASE_Y)] + top_arc + [(ROT_CX + ROT_RX, ROT_BASE_Y)]
	_spoly(body_pts, (0.88, 0.90, 0.95), filled=True)

	# Floor bands clipped to the curved shape
	for i in range(1, 9):
		yb = ROT_BASE_Y + i * (ROT_TOP_Y - ROT_BASE_Y) / 9
		dy = yb - ROT_CY
		if abs(dy) <= ROT_RY:
			frac = math.sqrt(max(0.0, 1.0 - (dy / ROT_RY) ** 2))
			span = ROT_RX * frac
			_sline_dda(ROT_CX - span, yb, ROT_CX + span, yb, color=(0.72, 0.76, 0.84), size=1.0)

	# Vertical ribs and glass strips
	for ang in [22, 44, 66, 90, 114, 136, 158]:
		t = math.radians(ang)
		x = ROT_CX + ROT_RX * math.cos(t)
		y = ROT_CY + ROT_RY * math.sin(t)
		_sline_bres(x, ROT_BASE_Y + 2, x, y, color=(0.94, 0.96, 0.99), size=2.0)

	usable_h = ROT_TOP_Y - ROT_BASE_Y - 16
	row_h = usable_h / 5
	for row in range(5):
		yb = ROT_BASE_Y + 8 + row * row_h
		wh = max(16, row_h - 10)
		mid_y = yb + 12
		dy = mid_y - ROT_CY
		if abs(dy) > ROT_RY:
			continue
		frac = math.sqrt(max(0.0, 1.0 - (dy / ROT_RY) ** 2))
		span = ROT_RX * frac
		for p in [-0.86, -0.62, -0.38, -0.14, 0.14, 0.38, 0.62, 0.86]:
			cxw = ROT_CX + span * p
			ww = 13
			if abs(cxw - ROT_CX) + ww * 0.5 <= span + 1:
				_srect(cxw - ww * 0.5, yb, ww, wh, (0.28, 0.50, 0.76), filled=True)

	_draw_arc_outline(ROT_CX, ROT_CY, ROT_RX, ROT_RY, 0, 180, color=(0.40, 0.46, 0.60), width=2.0, segments=72)
	_sline_bres(ROT_CX - ROT_RX, ROT_CY, ROT_CX - ROT_RX, ROT_BASE_Y, color=(0.40, 0.46, 0.60), size=1.5)
	_sline_bres(ROT_CX + ROT_RX, ROT_CY, ROT_CX + ROT_RX, ROT_BASE_Y, color=(0.40, 0.46, 0.60), size=1.5)


def _draw_rotunda_canopy():
	_draw_arc_band(
		CAN_CX,
		CAN_CY,
		CAN_RX_IN,
		CAN_RY_IN,
		CAN_RX_OUT,
		CAN_RY_OUT,
		CAN_A1,
		CAN_A2,
		color=COPPER,
	)
	_draw_arc_outline(CAN_CX, CAN_CY, CAN_RX_IN, CAN_RY_IN, CAN_A1, CAN_A2, color=COPPER_DARK, width=1.8, segments=72)
	_draw_arc_outline(CAN_CX, CAN_CY, CAN_RX_OUT, CAN_RY_OUT, CAN_A1, CAN_A2, color=COPPER_DARK, width=1.8, segments=72)
	_draw_arc_outline(
		CAN_CX,
		CAN_CY,
		CAN_RX_OUT - 3,
		CAN_RY_OUT - 2,
		CAN_A1,
		CAN_A2,
		color=COPPER_HL,
		width=1.2,
		segments=72,
	)


def _draw_entrance_canopy_and_door():
	col_y = GY
	col_h = ENT_CANOPY_Y - col_y
	for cx in [CAN_CX - 54, CAN_CX + 44]:
		_srect(cx, col_y, 10, col_h, (0.93, 0.93, 0.95), filled=True)
		_srect(cx, col_y, 10, col_h, (0.72, 0.74, 0.78), filled=False, width=1.0)

	_srect(CAN_CX - ENT_CANOPY_HALF_W, ENT_CANOPY_Y, ENT_CANOPY_HALF_W * 2, ENT_CANOPY_H, COPPER, filled=True)
	_srect(
		CAN_CX - ENT_CANOPY_HALF_W,
		ENT_CANOPY_Y,
		ENT_CANOPY_HALF_W * 2,
		ENT_CANOPY_H,
		COPPER_DARK,
		filled=False,
		width=1.4,
	)

	ly = GY
	lh = ENT_CANOPY_Y - ly
	lx = CAN_CX - 66
	lw = 132
	_srect(lx, ly, lw, lh, (0.50, 0.68, 0.85), filled=True)

	for dx in [CAN_CX - 38, CAN_CX - 12, CAN_CX + 14]:
		_srect(dx, ly, 24, lh, GLASS, filled=True)
		_srect(dx, ly, 24, lh, (0.80, 0.90, 0.95), filled=False, width=1.0)
		_sline_bres(dx + 12, ly, dx + 12, ly + lh, color=(0.70, 0.80, 0.90), size=1.0)

	for i in range(1, 5):
		vx = lx + i * (lw / 5)
		_sline_bres(vx, ly, vx, ly + lh, color=(0.75, 0.80, 0.85), size=1.0)
	_srect(lx, ly, lw, lh, (0.60, 0.68, 0.78), filled=False, width=1.2)


def _draw_stairs():
	sx = CAN_CX - STAIR_TOP_W / 2
	for i in range(STAIR_STEPS):
		spread = i * STAIR_EXPAND
		x = sx - spread
		w = STAIR_TOP_W + 2 * spread
		y = GY - (i + 1) * STAIR_SH
		shade = 0.80 - i * 0.03
		_srect(x, y, w, STAIR_SH, (shade, shade, min(1.0, shade + 0.02)), filled=True)
		_sline_bres(x, y, x + w, y, color=(0.60, 0.62, 0.66), size=1.0)
		_sline_bres(x, y + STAIR_SH, x + w, y + STAIR_SH, color=(0.60, 0.62, 0.66), size=1.0)


def _draw_palm(x, y, h=70):
	_srect(x - 4, y, 8, h, PALM_TRUNK, filled=True)
	_srect(x - 4, y, 8, h, (0.32, 0.20, 0.08), filled=False, width=1.0)

	tx, ty = x, y + h
	fronds = [
		(-35, 22),
		(-22, 30),
		(-8, 35),
		(8, 35),
		(22, 30),
		(35, 22),
		(-18, 18),
		(18, 18),
		(0, 38),
	]
	for dx, dy in fronds:
		_sline_dda(tx, ty, tx + dx, ty + dy, PALM_LEAF, size=2.0)


def _draw_palms():
	_draw_palm(340, GY - 45, 65)
	_draw_palm(565, GY - 45, 65)
	_draw_palm(310, GY - 40, 55)
	_draw_palm(595, GY - 40, 55)


def _draw_signage_and_label():
	sx = RW_X + 10
	sy = RW_TOP + 14
	sw = RW_W - 20
	sh = 18
	_srect(sx, sy, sw, sh, (0.10, 0.18, 0.45), filled=True)
	_srect(sx, sy, sw, sh, (1.0, 1.0, 1.0), filled=False, width=1.2)

	draw_text(
		_mx(290),
		_my(16),
		"DIU - Knowledge Tower (AB4 Building)",
		color=(0.10, 0.12, 0.35),
	)


def _draw_corner_points():
	for x, y in [
		(LW_X, LW_Y),
		(LW_X + LW_W, LW_Y),
		(LW_X, LW_TOP),
		(LW_X + LW_W, LW_TOP),
		(RW_X, RW_Y),
		(RW_X + RW_W, RW_Y),
		(RW_X, RW_TOP),
		(RW_X + RW_W, RW_TOP),
	]:
		draw_circle(_mx(x), _my(y), 2, color=(0.45, 0.50, 0.55), size=1.0)


def draw():
	_draw_sky_ground()
	_draw_clouds()

	# Building layers (back to front)
	_draw_center_block()
	_draw_left_wing()
	_draw_right_wing()
	_draw_elevator_tower()
	_draw_rotunda()
	_draw_rotunda_canopy()
	_draw_entrance_canopy_and_door()
	_draw_stairs()
	_draw_palms()
	_draw_corner_points()
	_draw_signage_and_label()
