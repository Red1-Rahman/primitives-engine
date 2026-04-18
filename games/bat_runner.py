# games\bat_runner.py
import math
import random
from dataclasses import dataclass
from pathlib import Path

from OpenGL.GL import (
	GL_BLEND,
	GL_LINE_STRIP,
	GL_ONE_MINUS_SRC_ALPHA,
	GL_QUADS,
	GL_RGBA,
	GL_SRC_ALPHA,
	GL_TEXTURE_2D,
	GL_TEXTURE_MAG_FILTER,
	GL_TEXTURE_MIN_FILTER,
	GL_TRIANGLES,
	GL_UNSIGNED_BYTE,
	GL_LINEAR,
	glBegin,
	glBindTexture,
	glBlendFunc,
	glColor3f,
	glDisable,
	glEnable,
	glEnd,
	glGenTextures,
	glLineWidth,
	glTexCoord2f,
	glTexImage2D,
	glTexParameteri,
	glVertex2f,
)

from engine.input import is_key
from engine.renderer import draw_rect, draw_text
from engine.window import WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP

DISPLAY_NAME = "Bat Runner"

try:
	from PIL import Image
except Exception:
	Image = None


# World viewport is [-400, 400] x [-300, 300] in this engine.
VIEW_W = WORLD_RIGHT - WORLD_LEFT
VIEW_H = WORLD_TOP - WORLD_BOTTOM

SEGMENT_WIDTH = 60.0
EXTRA_BUFFER = SEGMENT_WIDTH * 8

BASE_CENTER_Y = 0.0
BASE_GAP = 185.0
MIN_GAP = 130.0
MAX_GAP = 230.0

MAX_CENTER_DELTA = 8.0
MAX_GAP_DELTA = 7.0

SCROLL_SPEED = 3.2

BAT_X = -220.0
BAT_WIDTH = 54.0
BAT_HEIGHT = 38.0

FLAP_FORCE = 6.0
GRAVITY = -0.32
MAX_FALL_SPEED = -11.0
MAX_RISE_SPEED = 12.0

COUNTDOWN_TOTAL = 2.0

SPIKE_MIN_SIZE = 16.0
SPIKE_MAX_SIZE = 38.0
SPIKE_CHANCE = 0.20
SPIKE_SPAN = 0.28

ASSET_BAT = Path(__file__).resolve().parent / "assets-bat_runner" / "bat.png"


@dataclass
class Spike:
	side: str
	size: float
	start_t: float
	end_t: float


@dataclass
class Segment:
	x: float
	center_y: float
	gap: float
	spike: Spike | None = None


_segments: list[Segment] = []
_segment_start_index = 0

_scroll_x = 0.0
_bat_y = 0.0
_bat_vel_y = 0.0
_score = 0
_game_over = False
_countdown_remaining = COUNTDOWN_TOTAL
_countdown_active = True
_last_flap_pressed = False

_tex_bat = None
_texture_attempted = False


def _clamp(value, low, high):
	return max(low, min(high, value))


def _lerp(a, b, t):
	return a + (b - a) * t


def _edge_jitter(world_x):
	index = world_x / SEGMENT_WIDTH
	return math.sin(index * 0.52) * 3.0


def _noise_1d(value, seed=0.0):
	# Deterministic fallback (no external noise dependency).
	return 0.62 * math.sin((value + seed) * 2.09) + 0.38 * math.sin((value + seed) * 0.71)


def _make_spike(gap):
	if gap < MIN_GAP + SPIKE_MIN_SIZE + 10.0:
		return None
	if random.random() >= SPIKE_CHANCE:
		return None

	max_size = min(SPIKE_MAX_SIZE, gap - MIN_GAP - 8.0)
	if max_size < SPIKE_MIN_SIZE:
		return None

	start_t = 0.34 + random.random() * 0.10
	end_t = start_t + SPIKE_SPAN
	side = "floor" if random.random() < 0.5 else "ceiling"
	size = random.uniform(SPIKE_MIN_SIZE, max_size)
	return Spike(side=side, size=size, start_t=start_t, end_t=end_t)


def _generate_next_segment(prev, segment_index):
	noise_val = _noise_1d(segment_index * 0.045)
	center_wave = noise_val * 42.0 + math.sin(segment_index * 0.035 + 1.6) * 18.0
	target_center = BASE_CENTER_Y + center_wave
	center_delta = _clamp(target_center - prev.center_y + random.uniform(-4.0, 4.0), -MAX_CENTER_DELTA, MAX_CENTER_DELTA)
	center_y = prev.center_y + center_delta

	gap_noise = _noise_1d(segment_index * 0.058, seed=37.0)
	target_gap = BASE_GAP + gap_noise * 24.0 + math.sin(segment_index * 0.055 + 0.8) * 12.0 + random.uniform(-5.0, 5.0)
	gap_delta = _clamp(target_gap - prev.gap, -MAX_GAP_DELTA, MAX_GAP_DELTA)
	gap = _clamp(prev.gap + gap_delta, MIN_GAP, MAX_GAP)

	min_center = WORLD_BOTTOM + 22.0 + gap * 0.5
	max_center = WORLD_TOP - 22.0 - gap * 0.5
	center_y = _clamp(center_y, min_center, max_center)

	return Segment(
		x=prev.x + SEGMENT_WIDTH,
		center_y=center_y,
		gap=gap,
		spike=_make_spike(gap),
	)


def _build_initial_cave():
	global _segments, _segment_start_index

	_segments = [Segment(x=0.0, center_y=BASE_CENTER_Y, gap=BASE_GAP, spike=None)]
	_segment_start_index = 0

	while _segments[-1].x < VIEW_W + EXTRA_BUFFER:
		segment_index = _segment_start_index + len(_segments)
		_segments.append(_generate_next_segment(_segments[-1], segment_index))


def _ensure_cave_ahead(world_x):
	target_x = world_x + EXTRA_BUFFER
	while _segments[-1].x < target_x:
		segment_index = _segment_start_index + len(_segments)
		_segments.append(_generate_next_segment(_segments[-1], segment_index))


def _prune_old_segments():
	global _segment_start_index

	min_world_x = max(0.0, _scroll_x - SEGMENT_WIDTH * 3)
	keep_from = int(min_world_x // SEGMENT_WIDTH)

	while _segment_start_index < keep_from and len(_segments) > 2:
		_segments.pop(0)
		_segment_start_index += 1


def _segment_for_world_x(world_x):
	index = int(world_x // SEGMENT_WIDTH)
	index = _clamp(index, _segment_start_index, _segment_start_index + len(_segments) - 2)
	local_index = index - _segment_start_index
	left = _segments[local_index]
	right = _segments[local_index + 1]
	t = _clamp((world_x - left.x) / SEGMENT_WIDTH, 0.0, 1.0)
	return left, right, t


def _cave_bounds_at(world_x):
	_ensure_cave_ahead(world_x)
	left, right, t = _segment_for_world_x(world_x)

	center_y = _lerp(left.center_y, right.center_y, t)
	gap = _lerp(left.gap, right.gap, t)

	floor_y = center_y - gap * 0.5
	ceiling_y = center_y + gap * 0.5

	spike = left.spike
	if spike and spike.start_t <= t <= spike.end_t:
		mid_t = (spike.start_t + spike.end_t) * 0.5
		half_span = max(0.001, (spike.end_t - spike.start_t) * 0.5)
		spike_factor = 1.0 - abs(t - mid_t) / half_span
		spike_factor = _clamp(spike_factor, 0.0, 1.0)

		if spike.side == "floor":
			floor_y += spike.size * spike_factor
		else:
			ceiling_y -= spike.size * spike_factor

	jitter = _edge_jitter(world_x)
	floor_y += jitter
	ceiling_y += jitter

	return floor_y, ceiling_y


def _bat_world_x(screen_x):
	return _scroll_x + (screen_x - WORLD_LEFT)


def _bat_bounds():
	half_w = BAT_WIDTH * 0.5
	half_h = BAT_HEIGHT * 0.5
	return BAT_X - half_w, BAT_X + half_w, _bat_y - half_h, _bat_y + half_h


def _bat_collides():
	left, right, bottom, top = _bat_bounds()

	if bottom <= WORLD_BOTTOM or top >= WORLD_TOP:
		return True

	sample_points = [left, left + BAT_WIDTH * 0.25, left + BAT_WIDTH * 0.5, left + BAT_WIDTH * 0.75, right]
	for sx in sample_points:
		world_x = _bat_world_x(sx)
		floor_y, ceiling_y = _cave_bounds_at(world_x)
		if bottom <= floor_y or top >= ceiling_y:
			return True

	return False


def _load_texture(path):
	if Image is None:
		return None
	if not path.exists():
		return None

	img = Image.open(path).convert("RGBA")
	img = img.transpose(Image.FLIP_TOP_BOTTOM)
	data = img.tobytes()

	tid = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, tid)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	return tid


def _draw_sprite(tid, x, y, w, h):
	glEnable(GL_TEXTURE_2D)
	glBindTexture(GL_TEXTURE_2D, tid)
	glColor3f(1.0, 1.0, 1.0)

	glBegin(GL_QUADS)
	glTexCoord2f(0.0, 0.0)
	glVertex2f(x, y)
	glTexCoord2f(1.0, 0.0)
	glVertex2f(x + w, y)
	glTexCoord2f(1.0, 1.0)
	glVertex2f(x + w, y + h)
	glTexCoord2f(0.0, 1.0)
	glVertex2f(x, y + h)
	glEnd()

	glDisable(GL_TEXTURE_2D)


def _reset_game():
	global _scroll_x, _bat_y, _bat_vel_y
	global _game_over, _score
	global _countdown_remaining, _countdown_active
	global _last_flap_pressed

	_scroll_x = 0.0
	_bat_y = 0.0
	_bat_vel_y = 0.0
	_score = 0
	_game_over = False
	_countdown_remaining = COUNTDOWN_TOTAL
	_countdown_active = True
	_last_flap_pressed = False
	_build_initial_cave()


def _draw_spike(screen_x, spike, floor_y, ceiling_y):
	spike_mid = (spike.start_t + spike.end_t) * 0.5
	spike_half = (spike.end_t - spike.start_t) * 0.5

	if spike.side == "floor":
		base_y = floor_y
		tip_y = floor_y + spike.size
	else:
		base_y = ceiling_y
		tip_y = ceiling_y - spike.size

	glBegin(GL_TRIANGLES)
	glVertex2f(screen_x + SEGMENT_WIDTH * (spike_mid - spike_half), base_y)
	glVertex2f(screen_x + SEGMENT_WIDTH * (spike_mid + spike_half), base_y)
	glVertex2f(screen_x + SEGMENT_WIDTH * spike_mid, tip_y)
	glEnd()


def _draw_cave():
	first_visible = max(_segment_start_index, int(_scroll_x // SEGMENT_WIDTH) - 1)
	last_visible = int((_scroll_x + VIEW_W) // SEGMENT_WIDTH) + 2

	_ensure_cave_ahead(_scroll_x + VIEW_W)

	glColor3f(0.07, 0.07, 0.10)
	for index in range(first_visible, last_visible):
		local = index - _segment_start_index
		if local < 0 or local + 1 >= len(_segments):
			continue

		left = _segments[local]
		right = _segments[local + 1]

		left_floor, left_ceiling = _cave_bounds_at(left.x)
		right_floor, right_ceiling = _cave_bounds_at(right.x)

		x0 = WORLD_LEFT + (left.x - _scroll_x)
		x1 = WORLD_LEFT + (right.x - _scroll_x)

		glBegin(GL_QUADS)
		glVertex2f(x0, WORLD_BOTTOM)
		glVertex2f(x1, WORLD_BOTTOM)
		glVertex2f(x1, right_floor)
		glVertex2f(x0, left_floor)
		glEnd()

		glColor3f(0.11, 0.10, 0.08)
		glBegin(GL_QUADS)
		glVertex2f(x0, left_ceiling)
		glVertex2f(x1, right_ceiling)
		glVertex2f(x1, WORLD_TOP)
		glVertex2f(x0, WORLD_TOP)
		glEnd()

		if left.spike is not None:
			glColor3f(0.52, 0.34, 0.16)
			_draw_spike(x0, left.spike, left_floor, left_ceiling)

	glColor3f(0.22, 0.19, 0.15)
	glLineWidth(2.0)
	glBegin(GL_LINE_STRIP)
	for index in range(first_visible, last_visible + 1):
		local = index - _segment_start_index
		if local < 0 or local >= len(_segments):
			continue
		floor_y, _ = _cave_bounds_at(_segments[local].x)
		glVertex2f(WORLD_LEFT + (_segments[local].x - _scroll_x), floor_y)
	glEnd()

	glBegin(GL_LINE_STRIP)
	for index in range(first_visible, last_visible + 1):
		local = index - _segment_start_index
		if local < 0 or local >= len(_segments):
			continue
		_, ceiling_y = _cave_bounds_at(_segments[local].x)
		glVertex2f(WORLD_LEFT + (_segments[local].x - _scroll_x), ceiling_y)
	glEnd()


def _draw_bat():
	half_w = BAT_WIDTH * 0.5
	half_h = BAT_HEIGHT * 0.5
	x = BAT_X - half_w
	y = _bat_y - half_h

	if _tex_bat is not None:
		_draw_sprite(_tex_bat, x, y, BAT_WIDTH, BAT_HEIGHT)
	else:
		draw_rect(x, y, BAT_WIDTH, BAT_HEIGHT, color=(0.92, 0.92, 0.95), filled=True)
		draw_rect(x, y, BAT_WIDTH, BAT_HEIGHT, color=(0.10, 0.10, 0.14), width=1.0)


def init():
	global _tex_bat, _texture_attempted

	random.seed()
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	if not _texture_attempted:
		_tex_bat = _load_texture(ASSET_BAT)
		_texture_attempted = True

	_reset_game()


def update():
	global _scroll_x, _bat_y, _bat_vel_y
	global _score, _game_over
	global _countdown_active, _countdown_remaining
	global _last_flap_pressed

	flap_now = is_key(b"w") or is_key(b"W") or is_key(b" ")
	restart_now = is_key(b"r") or is_key(b"R")

	if restart_now:
		init()
		return

	if _game_over:
		_last_flap_pressed = flap_now
		return

	if _countdown_active:
		_countdown_remaining = max(0.0, _countdown_remaining - (1.0 / 60.0))
		if _countdown_remaining <= 0.0:
			_countdown_active = False
		_last_flap_pressed = flap_now
		return

	if flap_now and not _last_flap_pressed:
		_bat_vel_y = FLAP_FORCE
	_last_flap_pressed = flap_now

	_scroll_x += SCROLL_SPEED
	_ensure_cave_ahead(_scroll_x + VIEW_W)
	_prune_old_segments()

	_bat_vel_y += GRAVITY
	_bat_vel_y = _clamp(_bat_vel_y, MAX_FALL_SPEED, MAX_RISE_SPEED)
	_bat_y += _bat_vel_y

	if _bat_collides():
		_game_over = True

	_score = int(_scroll_x // 10)


def draw():
	draw_rect(
		WORLD_LEFT,
		WORLD_BOTTOM,
		VIEW_W,
		VIEW_H,
		color=(0.03, 0.03, 0.05),
		filled=True,
	)

	_draw_cave()
	_draw_bat()

	draw_text(WORLD_LEFT + 14, WORLD_TOP - 26, f"Score: {_score}", color=(1.0, 0.95, 0.25))
	draw_text(
		WORLD_LEFT + 14,
		WORLD_BOTTOM + 18,
		"W or SPACE flap | R restart | ESC quit",
		color=(0.88, 0.88, 0.94),
	)

	if _countdown_active and not _game_over:
		if _countdown_remaining > 1.0:
			c = "2"
		elif _countdown_remaining > 0.0:
			c = "1"
		else:
			c = "GO"
		draw_text(-8, 12, c, color=(1.0, 0.95, 0.25))

	if _game_over:
		draw_text(-78, 20, "GAME OVER", color=(1.0, 0.35, 0.35))
		draw_text(-142, -6, "Press R to generate a new cave", color=(0.95, 0.95, 0.95))

