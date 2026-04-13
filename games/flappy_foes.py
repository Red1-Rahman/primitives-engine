from dataclasses import dataclass
from pathlib import Path

from OpenGL.GL import (
	GL_BLEND,
	GL_LINEAR,
	GL_ONE_MINUS_SRC_ALPHA,
	GL_QUADS,
	GL_RGBA,
	GL_SRC_ALPHA,
	GL_TEXTURE_2D,
	GL_TEXTURE_MAG_FILTER,
	GL_TEXTURE_MIN_FILTER,
	GL_UNSIGNED_BYTE,
	glBegin,
	glBindTexture,
	glBlendFunc,
	glColor3f,
	glDisable,
	glEnable,
	glEnd,
	glGenTextures,
	glTexCoord2f,
	glTexImage2D,
	glTexParameteri,
	glVertex2f,
)

from algorithms import run_bresenham, run_dda, run_midpoint_circle
from engine.input import is_key
from engine.renderer import draw_point, draw_rect, draw_text
from engine.window import WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP

DISPLAY_NAME = "Flappy Foes"

try:
	from PIL import Image
except Exception:
	Image = None


@dataclass
class Bird:
	name: str
	x: float
	y: float
	vel_y: float
	width: float
	height: float
	facing: int
	jump_keys: tuple[bytes, ...]
	shoot_keys: tuple[bytes, ...]
	color: tuple[float, float, float]
	lives: int
	shoot_cd: float = 0.0
	flap_prev: bool = False
	shoot_prev: bool = False
	invuln: float = 0.0
	alive: bool = True


@dataclass
class Bullet:
	x: float
	y: float
	prev_x: float
	prev_y: float
	vx: float
	owner: str
	color: tuple[float, float, float]
	ttl: float


VIEW_W = WORLD_RIGHT - WORLD_LEFT
VIEW_H = WORLD_TOP - WORLD_BOTTOM

BG_COLOR = (232 / 255, 225 / 255, 217 / 255)
LINE_COLOR = (0.22, 0.20, 0.16)
TEXT_COLOR = (0.16, 0.15, 0.13)

PURPLE = (0.66, 0.30, 0.86)
CYAN = (0.20, 0.77, 0.85)

BIRD_W = 58.0
BIRD_H = 42.0

LEFT_X = WORLD_LEFT + 130.0
RIGHT_X = WORLD_RIGHT - 130.0

FLAP_FORCE = 6.0
GRAVITY = -0.32
MAX_FALL_SPEED = -11.0
MAX_RISE_SPEED = 12.0

FPS = 60.0
DT = 1.0 / FPS

SHOOT_COOLDOWN = 0.9
BULLET_SPEED = 9.0
BULLET_RADIUS = 5
BULLET_TTL = 2.2

LIVES_TOTAL = 3
RESPAWN_INVULN = 0.7

ARENA_FLOOR = WORLD_BOTTOM + 3.0
ARENA_CEILING = WORLD_TOP - 3.0

ASSET_DIR = Path(__file__).resolve().parent / "assets-flappy_foes"
ASSET_LEFT = ASSET_DIR / "bird-left.png"
ASSET_RIGHT = ASSET_DIR / "bird-right.png"

_birds: dict[str, Bird] = {}
_bullets: list[Bullet] = []
_winner_text = ""
_match_over = False

_tex_left = None
_tex_right = None
_texture_attempted = False


def _clamp(v, lo, hi):
	return max(lo, min(hi, v))


def _any_pressed(keys: tuple[bytes, ...]):
	return any(is_key(k) for k in keys)


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


def _bird_bounds(bird: Bird):
	hw = bird.width * 0.5
	hh = bird.height * 0.5
	return bird.x - hw, bird.x + hw, bird.y - hh, bird.y + hh


def _spawn_bullet(owner: str):
	bird = _birds[owner]
	if not bird.alive:
		return

	bx = bird.x + bird.facing * (bird.width * 0.56)
	by = bird.y
	_bullets.append(
		Bullet(
			x=bx,
			y=by,
			prev_x=bx,
			prev_y=by,
			vx=BULLET_SPEED * bird.facing,
			owner=owner,
			color=bird.color,
			ttl=BULLET_TTL,
		)
	)
	bird.shoot_cd = SHOOT_COOLDOWN


def _lose_life(player_id: str):
	global _winner_text, _match_over

	bird = _birds[player_id]
	if not bird.alive:
		return

	bird.lives -= 1
	bird.vel_y = 0.0
	bird.y = 0.0
	bird.invuln = RESPAWN_INVULN

	if bird.lives <= 0:
		bird.alive = False

	alive_players = [p for p in _birds.values() if p.alive]
	if len(alive_players) <= 1:
		_match_over = True
		if len(alive_players) == 1:
			_winner_text = f"{alive_players[0].name} wins"
		else:
			_winner_text = "Draw"


def _reset_match_state():
	global _birds, _bullets, _winner_text, _match_over

	_birds = {
		"left": Bird(
			name="Purple Bird",
			x=LEFT_X,
			y=0.0,
			vel_y=0.0,
			width=BIRD_W,
			height=BIRD_H,
			facing=1,
			jump_keys=(b"w", b"W"),
			shoot_keys=(b"q", b"Q", b"e", b"E"),
			color=PURPLE,
			lives=LIVES_TOTAL,
		),
		"right": Bird(
			name="Cyan Bird",
			x=RIGHT_X,
			y=0.0,
			vel_y=0.0,
			width=BIRD_W,
			height=BIRD_H,
			facing=-1,
			jump_keys=(b"i", b"I"),
			shoot_keys=(b"u", b"U", b"o", b"O"),
			color=CYAN,
			lives=LIVES_TOTAL,
		),
	}

	_bullets = []
	_winner_text = ""
	_match_over = False


def _update_birds():
	for bird in _birds.values():
		jump_now = _any_pressed(bird.jump_keys)
		shoot_now = _any_pressed(bird.shoot_keys)

		if bird.shoot_cd > 0.0:
			bird.shoot_cd = max(0.0, bird.shoot_cd - DT)
		if bird.invuln > 0.0:
			bird.invuln = max(0.0, bird.invuln - DT)

		if not bird.alive:
			bird.flap_prev = jump_now
			bird.shoot_prev = shoot_now
			continue

		if jump_now and not bird.flap_prev:
			bird.vel_y = FLAP_FORCE
		bird.flap_prev = jump_now

		if shoot_now and not bird.shoot_prev and bird.shoot_cd <= 0.0:
			_spawn_bullet("left" if bird.facing > 0 else "right")
		bird.shoot_prev = shoot_now

		bird.vel_y += GRAVITY
		bird.vel_y = _clamp(bird.vel_y, MAX_FALL_SPEED, MAX_RISE_SPEED)
		bird.y += bird.vel_y

		_, _, bottom, top = _bird_bounds(bird)
		if bottom <= ARENA_FLOOR or top >= ARENA_CEILING:
			_lose_life("left" if bird.facing > 0 else "right")


def _update_bullets():
	for bullet in _bullets[:]:
		bullet.prev_x = bullet.x
		bullet.prev_y = bullet.y
		bullet.x += bullet.vx
		bullet.ttl -= DT

		if bullet.ttl <= 0.0 or bullet.x < WORLD_LEFT - 20 or bullet.x > WORLD_RIGHT + 20:
			_bullets.remove(bullet)
			continue

		target_id = "right" if bullet.owner == "left" else "left"
		target = _birds[target_id]
		if not target.alive or target.invuln > 0.0:
			continue

		l, r, b, t = _bird_bounds(target)
		if l <= bullet.x <= r and b <= bullet.y <= t:
			_bullets.remove(bullet)
			_lose_life(target_id)


def _draw_bresenham_line(x1, y1, x2, y2, color, size=2.0):
	ix1, iy1 = int(round(x1)), int(round(y1))
	ix2, iy2 = int(round(x2)), int(round(y2))
	_, _, rows = run_bresenham(ix1, iy1, ix2, iy2)
	draw_point(ix1, iy1, size=size, color=color)
	for row in rows:
		draw_point(row["x(i+1)"], row["y(i+1)"], size=size, color=color)


def _draw_dda_segment(x1, y1, x2, y2, color, size=2.0, stride=1):
	_, _, rows = run_dda(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)))
	for i, row in enumerate(rows):
		if i % stride == 0:
			draw_point(row["x (rounded)"], row["y (rounded)"], size=size, color=color)


def _draw_bullet(bullet: Bullet):
	_draw_dda_segment(bullet.prev_x, bullet.prev_y, bullet.x, bullet.y, bullet.color, size=2.0, stride=1)
	_, _, pixels = run_midpoint_circle(int(round(bullet.x)), int(round(bullet.y)), BULLET_RADIUS)
	for px, py in pixels:
		draw_point(px, py, size=2.0, color=bullet.color)


def _draw_life_icons(start_x, y, lives, color):
	spacing = 20
	for i in range(lives):
		cx = int(round(start_x + i * spacing))
		cy = int(round(y))
		_, _, pixels = run_midpoint_circle(cx, cy, 6)
		for px, py in pixels:
			draw_point(px, py, size=2.0, color=color)


def _draw_bird(player_id: str):
	bird = _birds[player_id]
	l, r, b, t = _bird_bounds(bird)

	if bird.invuln > 0.0 and int(bird.invuln * 20) % 2 == 0:
		return

	if player_id == "left" and _tex_left is not None:
		_draw_sprite(_tex_left, l, b, bird.width, bird.height)
	elif player_id == "right" and _tex_right is not None:
		_draw_sprite(_tex_right, l, b, bird.width, bird.height)
	else:
		draw_rect(l, b, bird.width, bird.height, color=bird.color, filled=True)
		draw_rect(l, b, bird.width, bird.height, color=LINE_COLOR, width=1.0)


def init():
	global _tex_left, _tex_right, _texture_attempted

	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	if not _texture_attempted:
		_tex_left = _load_texture(ASSET_LEFT)
		_tex_right = _load_texture(ASSET_RIGHT)
		_texture_attempted = True

	_reset_match_state()


def update():
	if is_key(b"r") or is_key(b"R"):
		init()
		return

	if _match_over:
		for bird in _birds.values():
			bird.flap_prev = _any_pressed(bird.jump_keys)
			bird.shoot_prev = _any_pressed(bird.shoot_keys)
		return

	_update_birds()
	_update_bullets()


def draw():
	draw_rect(WORLD_LEFT, WORLD_BOTTOM, VIEW_W, VIEW_H, color=BG_COLOR, filled=True)

	_draw_bresenham_line(WORLD_LEFT, ARENA_FLOOR, WORLD_RIGHT, ARENA_FLOOR, LINE_COLOR, size=2.0)
	_draw_bresenham_line(WORLD_LEFT, ARENA_CEILING, WORLD_RIGHT, ARENA_CEILING, LINE_COLOR, size=2.0)
	_draw_dda_segment(0, ARENA_FLOOR + 8, 0, ARENA_CEILING - 8, color=(0.35, 0.31, 0.27), size=2.0, stride=2)

	for bullet in _bullets:
		_draw_bullet(bullet)

	_draw_bird("left")
	_draw_bird("right")

	draw_text(WORLD_LEFT + 16, WORLD_TOP - 30, "Purple (W jump, Q/E shoot)", color=PURPLE)
	draw_text(WORLD_RIGHT - 300, WORLD_TOP - 30, "Cyan (I jump, U/O shoot)", color=CYAN)

	left = _birds["left"]
	right = _birds["right"]
	_draw_life_icons(WORLD_LEFT + 30, WORLD_TOP - 54, max(0, left.lives), PURPLE)
	_draw_life_icons(WORLD_RIGHT - 90, WORLD_TOP - 54, max(0, right.lives), CYAN)

	draw_text(
		WORLD_LEFT + 16,
		WORLD_BOTTOM + 20,
		f"Cooldowns  Purple: {left.shoot_cd:.1f}s   Cyan: {right.shoot_cd:.1f}s   |   R restart, ESC quit",
		color=TEXT_COLOR,
	)

	if _match_over:
		draw_text(-92, 12, _winner_text, color=(0.20, 0.18, 0.12))
		draw_text(-138, -16, "Press R to start a new match", color=(0.20, 0.18, 0.12))
