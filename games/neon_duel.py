from __future__ import annotations
import math
import random

from OpenGL.GL import (
    GL_LINES,
    GL_POINTS,
    GL_QUADS,
    GL_TRIANGLES,
    glBegin,
    glColor3f,
    glEnd,
    glLineWidth,
    glPointSize,
    glVertex2f,
)

from engine.input import is_key
from engine.renderer import draw_text
from engine.window import WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP

DISPLAY_NAME = "Neon Duel"

# Optional import to align with environments that install pyopengl_accelerate.
try:
    import OpenGL_accelerate as _ogl_accel  # noqa: F401
except Exception:
    _ogl_accel = None


# ------------------------------
# Constants
# ------------------------------
VIEW_W = WORLD_RIGHT - WORLD_LEFT
VIEW_H = WORLD_TOP - WORLD_BOTTOM

PLAYER_SIZE = 24.0
PLAYER_SPEED = 4.0
PLAYER_LIVES = 5

BULLET_SPEED = 8.4
BULLET_TTL = 110
SHOOT_COOLDOWN = 14
INVULN_FRAMES = 40

HIT_REWARD = 10
BONUS_REWARD = 5
TARGET_SCORE = 80

ROUND_TIME_FRAMES = 60 * 80
BONUS_SIZE = 14.0
BONUS_RESPAWN_FRAMES = 220

STAR_COUNT = 90


# ------------------------------
# State
# ------------------------------
_p1 = {}
_p2 = {}

_bullets = []
_stars = []

_bonus = {"x": 0.0, "y": 0.0, "active": True, "respawn": 0}

_timer_frames = ROUND_TIME_FRAMES
_frame = 0
_game_over = False
_result_text = ""
_result_reason = ""

_last_p1_shoot = False
_last_p2_shoot = False


# ------------------------------
# Utility
# ------------------------------
def _clamp(value, low, high):
    return max(low, min(high, value))


def _distance(a_x, a_y, b_x, b_y):
    return math.hypot(a_x - b_x, a_y - b_y)


def _format_time(frames):
    seconds = max(0, frames // 60)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _new_player(side):
    if side == 1:
        return {
            "name": "P1",
            "x": WORLD_LEFT + 130.0,
            "y": 0.0,
            "facing": 1.0,
            "color": (0.20, 0.92, 0.98),
            "score": 0,
            "lives": PLAYER_LIVES,
            "cooldown": 0,
            "invuln": 0,
        }
    return {
        "name": "P2",
        "x": WORLD_RIGHT - 130.0,
        "y": 0.0,
        "facing": -1.0,
        "color": (0.98, 0.38, 0.24),
        "score": 0,
        "lives": PLAYER_LIVES,
        "cooldown": 0,
        "invuln": 0,
    }


def _respawn_player(player, side):
    margin = PLAYER_SIZE + 22.0
    if side == 1:
        player["x"] = WORLD_LEFT + 130.0
    else:
        player["x"] = WORLD_RIGHT - 130.0
    player["y"] = random.uniform(WORLD_BOTTOM + margin, WORLD_TOP - margin)


def _build_stars():
    _stars.clear()
    for _ in range(STAR_COUNT):
        _stars.append(
            {
                "x": random.uniform(WORLD_LEFT + 5, WORLD_RIGHT - 5),
                "y": random.uniform(WORLD_BOTTOM + 5, WORLD_TOP - 5),
                "phase": random.uniform(0.0, math.pi * 2),
            }
        )


def _spawn_bonus():
    margin = 80.0
    _bonus["x"] = random.uniform(WORLD_LEFT + margin, WORLD_RIGHT - margin)
    _bonus["y"] = random.uniform(WORLD_BOTTOM + margin, WORLD_TOP - margin)
    _bonus["active"] = True
    _bonus["respawn"] = 0


def _reset_match():
    global _p1, _p2, _bullets
    global _timer_frames, _frame
    global _game_over, _result_text, _result_reason
    global _last_p1_shoot, _last_p2_shoot

    _p1 = _new_player(1)
    _p2 = _new_player(2)
    _bullets = []

    _timer_frames = ROUND_TIME_FRAMES
    _frame = 0
    _game_over = False
    _result_text = ""
    _result_reason = ""

    _spawn_bonus()

    _last_p1_shoot = False
    _last_p2_shoot = False


def _player_hitbox_contains(player, x, y):
    half = PLAYER_SIZE * 0.5
    return (
        abs(x - player["x"]) <= half
        and abs(y - player["y"]) <= half
    )


def _apply_hit_reward(attacker, defender, defender_side):
    attacker["score"] += HIT_REWARD
    defender["lives"] -= 1
    defender["invuln"] = INVULN_FRAMES
    _respawn_player(defender, defender_side)


def _apply_bonus_reward(player):
    player["score"] += BONUS_REWARD


def _decide_result_text():
    if _p1["score"] > _p2["score"]:
        return "PLAYER 1 WINS"
    if _p2["score"] > _p1["score"]:
        return "PLAYER 2 WINS"
    if _p1["lives"] > _p2["lives"]:
        return "PLAYER 1 WINS"
    if _p2["lives"] > _p1["lives"]:
        return "PLAYER 2 WINS"
    return "DRAW"


def _end_game(reason):
    global _game_over, _result_text, _result_reason
    if _game_over:
        return
    _game_over = True
    _result_reason = reason
    _result_text = _decide_result_text()


def _spawn_bullet(player, owner_id):
    if player["cooldown"] > 0:
        return

    offset = PLAYER_SIZE * 0.6
    direction = player["facing"]
    bullet = {
        "owner": owner_id,
        "x": player["x"] + direction * offset,
        "y": player["y"],
        "vx": direction * BULLET_SPEED,
        "ttl": BULLET_TTL,
    }
    _bullets.append(bullet)
    player["cooldown"] = SHOOT_COOLDOWN


def _move_player(player, up, down, left, right):
    dx = 0.0
    dy = 0.0

    if up:
        dy += 1.0
    if down:
        dy -= 1.0
    if left:
        dx -= 1.0
    if right:
        dx += 1.0

    if dx != 0.0:
        player["facing"] = 1.0 if dx > 0 else -1.0

    if dx == 0.0 and dy == 0.0:
        return

    length = math.hypot(dx, dy)
    dx /= length
    dy /= length

    half = PLAYER_SIZE * 0.5
    player["x"] += dx * PLAYER_SPEED
    player["y"] += dy * PLAYER_SPEED
    player["x"] = _clamp(player["x"], WORLD_LEFT + half, WORLD_RIGHT - half)
    player["y"] = _clamp(player["y"], WORLD_BOTTOM + half, WORLD_TOP - half)


def _update_bullets_and_hits():
    for bullet in _bullets[:]:
        bullet["x"] += bullet["vx"]
        bullet["ttl"] -= 1

        if bullet["ttl"] <= 0:
            _bullets.remove(bullet)
            continue

        if bullet["x"] < WORLD_LEFT - 20 or bullet["x"] > WORLD_RIGHT + 20:
            _bullets.remove(bullet)
            continue

        if bullet["owner"] == 1:
            target = _p2
            target_side = 2
            attacker = _p1
        else:
            target = _p1
            target_side = 1
            attacker = _p2

        if target["invuln"] > 0:
            continue

        if _player_hitbox_contains(target, bullet["x"], bullet["y"]):
            _apply_hit_reward(attacker, target, target_side)
            _bullets.remove(bullet)


def _update_bonus_pickup():
    if _bonus["active"]:
        if _distance(_p1["x"], _p1["y"], _bonus["x"], _bonus["y"]) <= PLAYER_SIZE * 0.65:
            _apply_bonus_reward(_p1)
            _bonus["active"] = False
            _bonus["respawn"] = BONUS_RESPAWN_FRAMES
            return
        if _distance(_p2["x"], _p2["y"], _bonus["x"], _bonus["y"]) <= PLAYER_SIZE * 0.65:
            _apply_bonus_reward(_p2)
            _bonus["active"] = False
            _bonus["respawn"] = BONUS_RESPAWN_FRAMES
            return
    else:
        _bonus["respawn"] -= 1
        if _bonus["respawn"] <= 0:
            _spawn_bonus()


def _update_objectives():
    if _p1["lives"] <= 0 or _p2["lives"] <= 0:
        _end_game("A player ran out of lives")
        return

    if _p1["score"] >= TARGET_SCORE or _p2["score"] >= TARGET_SCORE:
        _end_game("Target score reached")
        return

    if _timer_frames <= 0:
        _end_game("Time limit reached")


# ------------------------------
# Drawing helpers
# ------------------------------
def _draw_background():
    glColor3f(0.03, 0.03, 0.06)
    glBegin(GL_QUADS)
    glVertex2f(WORLD_LEFT, WORLD_BOTTOM)
    glVertex2f(WORLD_RIGHT, WORLD_BOTTOM)
    glVertex2f(WORLD_RIGHT, WORLD_TOP)
    glVertex2f(WORLD_LEFT, WORLD_TOP)
    glEnd()

    glPointSize(2.0)
    glBegin(GL_POINTS)
    for s in _stars:
        twinkle = 0.55 + 0.45 * math.sin(_frame * 0.05 + s["phase"])
        glColor3f(0.25 * twinkle, 0.75 * twinkle, 1.0 * twinkle)
        glVertex2f(s["x"], s["y"])
    glEnd()


def _draw_arena_lines():
    glLineWidth(2.0)
    glColor3f(0.16, 0.50, 0.95)
    glBegin(GL_LINES)
    glVertex2f(WORLD_LEFT + 10, WORLD_TOP - 10)
    glVertex2f(WORLD_RIGHT - 10, WORLD_TOP - 10)

    glVertex2f(WORLD_LEFT + 10, WORLD_BOTTOM + 10)
    glVertex2f(WORLD_RIGHT - 10, WORLD_BOTTOM + 10)

    glVertex2f(WORLD_LEFT + 10, WORLD_BOTTOM + 10)
    glVertex2f(WORLD_LEFT + 10, WORLD_TOP - 10)

    glVertex2f(WORLD_RIGHT - 10, WORLD_BOTTOM + 10)
    glVertex2f(WORLD_RIGHT - 10, WORLD_TOP - 10)
    glEnd()

    glLineWidth(1.0)
    glColor3f(0.15, 0.35, 0.60)
    glBegin(GL_LINES)
    dash = 18.0
    gap = 10.0
    y = WORLD_BOTTOM + 18.0
    while y < WORLD_TOP - 18.0:
        y2 = min(y + dash, WORLD_TOP - 18.0)
        glVertex2f(0.0, y)
        glVertex2f(0.0, y2)
        y += dash + gap
    glEnd()


def _draw_player(player):
    half = PLAYER_SIZE * 0.5
    x0 = player["x"] - half
    x1 = player["x"] + half
    y0 = player["y"] - half
    y1 = player["y"] + half

    r, g, b = player["color"]
    if player["invuln"] > 0 and (player["invuln"] // 4) % 2 == 0:
        r, g, b = 1.0, 1.0, 1.0

    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()

    glColor3f(min(1.0, r + 0.20), min(1.0, g + 0.20), min(1.0, b + 0.20))
    glBegin(GL_TRIANGLES)
    if player["facing"] > 0:
        glVertex2f(x1, player["y"])
        glVertex2f(x1 + 10.0, player["y"] + 5.0)
        glVertex2f(x1 + 10.0, player["y"] - 5.0)
    else:
        glVertex2f(x0, player["y"])
        glVertex2f(x0 - 10.0, player["y"] + 5.0)
        glVertex2f(x0 - 10.0, player["y"] - 5.0)
    glEnd()

    glPointSize(4.0)
    glColor3f(0.05, 0.05, 0.08)
    glBegin(GL_POINTS)
    glVertex2f(player["x"], player["y"])
    glEnd()


def _draw_bullets():
    glColor3f(1.0, 0.95, 0.30)
    for b in _bullets:
        x = b["x"]
        y = b["y"]
        glBegin(GL_TRIANGLES)
        if b["vx"] > 0:
            glVertex2f(x + 7.0, y)
            glVertex2f(x - 5.0, y + 4.0)
            glVertex2f(x - 5.0, y - 4.0)
        else:
            glVertex2f(x - 7.0, y)
            glVertex2f(x + 5.0, y + 4.0)
            glVertex2f(x + 5.0, y - 4.0)
        glEnd()


def _draw_bonus():
    if not _bonus["active"]:
        return

    half = BONUS_SIZE * 0.5
    x0 = _bonus["x"] - half
    x1 = _bonus["x"] + half
    y0 = _bonus["y"] - half
    y1 = _bonus["y"] + half

    glColor3f(0.95, 0.80, 0.18)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0)
    glVertex2f(x1, y0)
    glVertex2f(x1, y1)
    glVertex2f(x0, y1)
    glEnd()

    glPointSize(5.0)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_POINTS)
    glVertex2f(_bonus["x"], _bonus["y"])
    glEnd()


def _draw_hud():
    draw_text(
        WORLD_LEFT + 16,
        WORLD_TOP - 26,
        f"P1 Score { _p1['score'] }  Lives { _p1['lives'] }",
        color=(0.32, 0.95, 1.0),
    )
    draw_text(
        WORLD_RIGHT - 265,
        WORLD_TOP - 26,
        f"P2 Score { _p2['score'] }  Lives { _p2['lives'] }",
        color=(1.0, 0.45, 0.30),
    )
    draw_text(
        -46,
        WORLD_TOP - 26,
        _format_time(_timer_frames),
        color=(0.95, 0.95, 1.0),
    )

    draw_text(
        WORLD_LEFT + 16,
        WORLD_BOTTOM + 18,
        "P1: W A S D + F  |  P2: I J K L + H  |  Bonus square +5  |  Hit +10  |  R restart",
        color=(0.78, 0.82, 0.90),
    )


def _draw_game_over_overlay():
    glColor3f(0.02, 0.02, 0.03)
    glBegin(GL_QUADS)
    glVertex2f(-210, -90)
    glVertex2f(210, -90)
    glVertex2f(210, 90)
    glVertex2f(-210, 90)
    glEnd()

    glLineWidth(2.0)
    glColor3f(0.65, 0.65, 0.75)
    glBegin(GL_LINES)
    glVertex2f(-210, -90)
    glVertex2f(210, -90)
    glVertex2f(210, -90)
    glVertex2f(210, 90)
    glVertex2f(210, 90)
    glVertex2f(-210, 90)
    glVertex2f(-210, 90)
    glVertex2f(-210, -90)
    glEnd()

    draw_text(-70, 44, "GAME OVER", color=(1.0, 0.36, 0.36))
    draw_text(-88, 20, _result_text, color=(0.94, 0.94, 1.0))
    draw_text(-155, -4, _result_reason, color=(0.75, 0.80, 0.90))
    draw_text(
        -166,
        -28,
        f"Final: P1 {_p1['score']} ({_p1['lives']} lives)  |  P2 {_p2['score']} ({_p2['lives']} lives)",
        color=(0.90, 0.90, 0.98),
    )
    draw_text(-92, -54, "Press R to restart", color=(0.96, 0.96, 0.96))


# ------------------------------
# Module API
# ------------------------------
def init():
    random.seed()
    if not _stars:
        _build_stars()
    _reset_match()


def update():
    global _timer_frames, _frame
    global _last_p1_shoot, _last_p2_shoot

    _frame += 1

    restart_now = is_key(b"r") or is_key(b"R")
    if restart_now:
        init()
        return

    if _game_over:
        return

    _move_player(
        _p1,
        up=is_key(b"w") or is_key(b"W"),
        down=is_key(b"s") or is_key(b"S"),
        left=is_key(b"a") or is_key(b"A"),
        right=is_key(b"d") or is_key(b"D"),
    )
    _move_player(
        _p2,
        up=is_key(b"i") or is_key(b"I"),
        down=is_key(b"k") or is_key(b"K"),
        left=is_key(b"j") or is_key(b"J"),
        right=is_key(b"l") or is_key(b"L"),
    )

    p1_shoot_now = is_key(b"f") or is_key(b"F")
    p2_shoot_now = is_key(b"h") or is_key(b"H")

    if p1_shoot_now and not _last_p1_shoot:
        _spawn_bullet(_p1, owner_id=1)
    if p2_shoot_now and not _last_p2_shoot:
        _spawn_bullet(_p2, owner_id=2)

    _last_p1_shoot = p1_shoot_now
    _last_p2_shoot = p2_shoot_now

    if _p1["cooldown"] > 0:
        _p1["cooldown"] -= 1
    if _p2["cooldown"] > 0:
        _p2["cooldown"] -= 1
    if _p1["invuln"] > 0:
        _p1["invuln"] -= 1
    if _p2["invuln"] > 0:
        _p2["invuln"] -= 1

    _update_bullets_and_hits()
    _update_bonus_pickup()

    _timer_frames = max(0, _timer_frames - 1)
    _update_objectives()


def draw():
    _draw_background()
    _draw_arena_lines()
    _draw_bonus()
    _draw_player(_p1)
    _draw_player(_p2)
    _draw_bullets()
    _draw_hud()

    if _game_over:
        _draw_game_over_overlay()