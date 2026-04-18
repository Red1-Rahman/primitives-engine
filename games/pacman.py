# games\pacman.py
"""
Pacman mini-game  —  proper Pacman with mouth, direction, ghosts, and maze.
Player       : yellow Pacman (GL_TRIANGLE_FAN with animated mouth wedge)
Collectibles : green GL_POINTS (+10), red GL_POINTS (-10)
Ghosts       : 4 enemies, random movement, touch = -25 points, -1 life
Win condition : reach 100 points
Lose condition: score drops below -50  OR  lives reach 0

Controls:
- W/A/S/D  : move Pacman (mouth faces direction)
- R        : restart
- ESC      : quit (handled by engine.input)
"""
from math import cos, hypot, pi, sin
import random

from OpenGL.GL import (
    GL_LINES, GL_POINTS, GL_TRIANGLE_FAN,
    glBegin, glColor3f, glColor4f, glEnd,
    glLineWidth, glPointSize, glPopMatrix,
    glPushMatrix, glRotatef, glTranslatef, glVertex2f,
)
from OpenGL.GLUT import glutSetWindowTitle

from engine.input    import is_key
from engine.renderer import draw_point, draw_rect, draw_text, draw_circle
from engine.window   import (
    WORLD_BOTTOM, WORLD_LEFT, WORLD_RIGHT, WORLD_TOP,
    init_window, start_loop,
)

DISPLAY_NAME = "Pacman"

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
PACMAN_RADIUS  = 18.0
PACMAN_SPEED   = 3.0
GHOST_RADIUS   = 16.0
GHOST_SPEED    = 1.4
POINT_SIZE     = 7.0
COLLECT_RADIUS = PACMAN_RADIUS + 8
GHOST_HIT_R    = PACMAN_RADIUS + GHOST_RADIUS - 4
TARGET_SCORE   = 100
SCORE_LOSE     = -50
GHOST_PENALTY  = 25
MAX_LIVES      = 3

GREEN_COUNT = 15
RED_COUNT   = 8

PACMAN_COLOR = (1.0, 1.0, 0.0)
BG_COLOR     = (0.03, 0.03, 0.08)
WALL_COLOR   = (0.15, 0.30, 0.80)
GREEN_COLOR  = (0.20, 0.95, 0.20)
RED_COLOR    = (0.95, 0.20, 0.20)
LIFE_COLOR   = (1.00, 1.00, 0.00)

GHOST_COLORS = [
    (1.00, 0.18, 0.18),
    (1.00, 0.60, 0.80),
    (0.18, 0.90, 0.90),
    (1.00, 0.60, 0.18),
]

_TITLE_BASE = "Pacman  |  W/A/S/D  |  R restart"

# ─────────────────────────────────────────────
#  MAZE
# ─────────────────────────────────────────────
_WALLS = [
    (-390, -290, 780,  14),
    (-390,  276, 780,  14),
    (-390, -290,  14, 580),
    ( 376, -290,  14, 580),
    (-300,  160, 180,  12),
    ( 120,  160, 180,  12),
    (-300, -172, 180,  12),
    ( 120, -172, 180,  12),
    (-160,   60, 320,  12),
    (-160,  -72, 320,  12),
    (-240,  -60,  12, 132),
    ( 228,  -60,  12, 132),
    (-110,  100,  12, 100),
    (  98,  100,  12, 100),
    (-110, -200,  12, 100),
    (  98, -200,  12, 100),
]


def _collides_wall(nx, ny, r=PACMAN_RADIUS):
    for wx, wy, ww, wh in _WALLS:
        cx = max(wx, min(nx, wx + ww))
        cy = max(wy, min(ny, wy + wh))
        if hypot(nx - cx, ny - cy) < r:
            return True
    return False


# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────
_pac_x     = 0.0
_pac_y     = 0.0
_pac_angle = 0.0
_mouth_t   = 0.0
_moving    = False

_score          = 0
_lives          = MAX_LIVES
_game_over      = False
_player_won     = False
_prev_score     = None
_prev_lives     = None
_prev_game_over = None

_collectibles = []
_ghosts       = []


# ─────────────────────────────────────────────
#  SPAWN HELPERS
# ─────────────────────────────────────────────

def _safe_pos(r=20.0):
    for _ in range(200):
        x = random.uniform(WORLD_LEFT + 30, WORLD_RIGHT - 30)
        y = random.uniform(WORLD_BOTTOM + 30, WORLD_TOP - 30)
        if not _collides_wall(x, y, r) and hypot(x, y) > 60:
            return x, y
    return 100.0, 100.0


def _spawn_collectible(value):
    x, y = _safe_pos(10.0)
    return {"x": x, "y": y, "value": value,
            "color": GREEN_COLOR if value > 0 else RED_COLOR}


def _spawn_ghost(color):
    x, y = _safe_pos(GHOST_RADIUS)
    angle = random.uniform(0, 2 * pi)
    return {
        "x": x, "y": y,
        "vx": GHOST_SPEED * cos(angle),
        "vy": GHOST_SPEED * sin(angle),
        "color": color,
        "hit_timer": 0,
    }


def _reset():
    global _pac_x, _pac_y, _pac_angle, _mouth_t, _moving
    global _score, _lives, _game_over, _player_won
    global _prev_score, _prev_lives, _prev_game_over

    _pac_x = _pac_y = 0.0
    _pac_angle = 0.0
    _mouth_t   = 0.0
    _moving    = False
    _score     = 0
    _lives     = MAX_LIVES
    _game_over = False
    _player_won = False
    _prev_score     = None
    _prev_lives     = None
    _prev_game_over = None

    _collectibles.clear()
    for _ in range(GREEN_COUNT):
        _collectibles.append(_spawn_collectible(10))
    for _ in range(RED_COUNT):
        _collectibles.append(_spawn_collectible(-10))

    _ghosts.clear()
    for color in GHOST_COLORS:
        _ghosts.append(_spawn_ghost(color))


# ─────────────────────────────────────────────
#  TITLE
# ─────────────────────────────────────────────

def _set_title():
    global _prev_score, _prev_lives, _prev_game_over
    if (_prev_score     == _score and
        _prev_lives     == _lives and
        _prev_game_over == _game_over):
        return
    if _game_over:
        state = "YOU WIN!" if _player_won else "GAME OVER"
    else:
        state = "RUNNING"
    glutSetWindowTitle(
        f"{_TITLE_BASE}  |  Score: {_score}  |  Lives: {_lives}  |  {state}".encode()
    )
    _prev_score     = _score
    _prev_lives     = _lives
    _prev_game_over = _game_over


# ─────────────────────────────────────────────
#  DRAW PACMAN
# ─────────────────────────────────────────────

def _draw_pacman():
    if _moving:
        mouth_half = 5 + 30 * abs(sin(_mouth_t * 0.18))
    else:
        mouth_half = 5.0

    start_rad = (_pac_angle + mouth_half) * pi / 180
    end_rad   = (_pac_angle + 360 - mouth_half) * pi / 180

    glColor3f(*PACMAN_COLOR)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(_pac_x, _pac_y)
    steps = 80
    for i in range(steps + 1):
        t     = i / steps
        angle = start_rad + t * (end_rad - start_rad)
        glVertex2f(
            _pac_x + PACMAN_RADIUS * cos(angle),
            _pac_y + PACMAN_RADIUS * sin(angle),
        )
    glEnd()

    eye_angle = (_pac_angle + 70) * pi / 180
    ex = _pac_x + PACMAN_RADIUS * 0.55 * cos(eye_angle)
    ey = _pac_y + PACMAN_RADIUS * 0.55 * sin(eye_angle)
    glColor3f(0.0, 0.0, 0.0)
    glPointSize(5.0)
    glBegin(GL_POINTS)
    glVertex2f(ex, ey)
    glEnd()


# ─────────────────────────────────────────────
#  DRAW GHOST
# ─────────────────────────────────────────────

def _draw_ghost(g):
    cx, cy = g["x"], g["y"]
    r      = GHOST_RADIUS
    rc, gc, bc = g["color"]

    if g["hit_timer"] > 0 and (g["hit_timer"] // 4) % 2 == 0:
        glColor3f(1.0, 1.0, 1.0)
    else:
        glColor3f(rc, gc, bc)

    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(61):
        a = pi * i / 60
        glVertex2f(cx + r * cos(a), cy + r * sin(a))
    glEnd()

    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy - r)
    glVertex2f(cx - r, cy)
    glVertex2f(cx - r, cy - r)
    glVertex2f(cx + r, cy - r)
    glVertex2f(cx + r, cy)
    glEnd()

    glColor3f(rc * 0.7, gc * 0.7, bc * 0.7)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy - r)
    for i in range(7):
        bx = cx - r + i * (2 * r / 6)
        by = cy - r + (4 if i % 2 == 0 else -4)
        glVertex2f(bx, by)
    glEnd()

    for ex_off in (-r * 0.35, r * 0.35):
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx + ex_off, cy + r * 0.2)
        for i in range(17):
            a = 2 * pi * i / 16
            glVertex2f(cx + ex_off + 4 * cos(a),
                       cy + r * 0.2 + 5 * sin(a))
        glEnd()
        glColor3f(0.1, 0.1, 0.9)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx + ex_off + 1, cy + r * 0.2)
        for i in range(9):
            a = 2 * pi * i / 8
            glVertex2f(cx + ex_off + 1 + 2 * cos(a),
                       cy + r * 0.2 + 2.5 * sin(a))
        glEnd()


# ─────────────────────────────────────────────
#  DRAW LIVES  (mini Pacman icons)
# ─────────────────────────────────────────────

def _draw_lives():
    for i in range(_lives):
        lx = WORLD_RIGHT - 30 - i * 28
        ly = WORLD_TOP - 26
        glColor3f(*LIFE_COLOR)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(lx, ly)
        for j in range(51):
            t = j / 50
            a = (25 + t * 310) * pi / 180
            glVertex2f(lx + 10 * cos(a), ly + 10 * sin(a))
        glEnd()


# ─────────────────────────────────────────────
#  DRAW WALLS
# ─────────────────────────────────────────────

def _draw_walls():
    for wx, wy, ww, wh in _WALLS:
        draw_rect(wx, wy, ww, wh, color=WALL_COLOR, filled=True)
        draw_rect(wx, wy, ww, wh, color=(0.4, 0.6, 1.0), width=1.5)


# ─────────────────────────────────────────────
#  UPDATE GHOSTS
# ─────────────────────────────────────────────

def _update_ghosts():
    global _score, _lives, _game_over, _player_won

    for g in _ghosts:
        if g["hit_timer"] > 0:
            g["hit_timer"] -= 1

        nx = g["x"] + g["vx"]
        ny = g["y"] + g["vy"]

        if _collides_wall(nx, ny, GHOST_RADIUS - 2):
            angle = random.uniform(0, 2 * pi)
            g["vx"] = GHOST_SPEED * cos(angle)
            g["vy"] = GHOST_SPEED * sin(angle)
        else:
            g["x"] = nx
            g["y"] = ny

        if random.random() < 0.01:
            angle = random.uniform(0, 2 * pi)
            g["vx"] = GHOST_SPEED * cos(angle)
            g["vy"] = GHOST_SPEED * sin(angle)

        g["x"] = max(WORLD_LEFT  + GHOST_RADIUS, min(WORLD_RIGHT  - GHOST_RADIUS, g["x"]))
        g["y"] = max(WORLD_BOTTOM + GHOST_RADIUS, min(WORLD_TOP   - GHOST_RADIUS, g["y"]))

        # Ghost hits Pacman
        if g["hit_timer"] == 0:
            if hypot(_pac_x - g["x"], _pac_y - g["y"]) < GHOST_HIT_R:
                _score -= GHOST_PENALTY
                _lives -= 1
                g["hit_timer"] = 90

                # Lose conditions
                if _lives <= 0 or _score <= SCORE_LOSE:
                    _game_over  = True
                    _player_won = False


# ─────────────────────────────────────────────
#  LIFECYCLE
# ─────────────────────────────────────────────

def init():
    _reset()
    _set_title()


def update():
    global _pac_x, _pac_y, _pac_angle, _mouth_t, _moving
    global _score, _game_over, _player_won

    if _game_over:
        if is_key(b"r") or is_key(b"R"):
            init()
        _set_title()
        return

    # ── Move Pacman ──
    dx = dy = 0
    if is_key(b"w") or is_key(b"W"):  dy =  1
    if is_key(b"s") or is_key(b"S"):  dy = -1
    if is_key(b"a") or is_key(b"A"):  dx = -1
    if is_key(b"d") or is_key(b"D"):  dx =  1

    _moving = (dx != 0 or dy != 0)

    if _moving:
        if   dx > 0: _pac_angle = 0
        elif dx < 0: _pac_angle = 180
        elif dy > 0: _pac_angle = 90
        elif dy < 0: _pac_angle = 270

        nx = _pac_x + dx * PACMAN_SPEED
        ny = _pac_y + dy * PACMAN_SPEED
        if not _collides_wall(nx, ny):
            _pac_x, _pac_y = nx, ny

        _mouth_t += 1

    _pac_x = max(WORLD_LEFT  + PACMAN_RADIUS, min(WORLD_RIGHT  - PACMAN_RADIUS, _pac_x))
    _pac_y = max(WORLD_BOTTOM + PACMAN_RADIUS, min(WORLD_TOP   - PACMAN_RADIUS, _pac_y))

    # ── Collect dots ──
    for i, p in enumerate(_collectibles):
        if hypot(_pac_x - p["x"], _pac_y - p["y"]) < COLLECT_RADIUS:
            _score += p["value"]
            _collectibles[i] = _spawn_collectible(p["value"])

    # ── Win check ──
    if _score >= TARGET_SCORE:
        _game_over  = True
        _player_won = True

    # ── Lose check (score threshold) ──
    if _score <= SCORE_LOSE and not _game_over:
        _game_over  = True
        _player_won = False

    _update_ghosts()

    if is_key(b"r") or is_key(b"R"):
        init()
        return

    _set_title()


def draw():
    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
              color=BG_COLOR, filled=True)

    _draw_walls()

    for p in _collectibles:
        draw_point(p["x"], p["y"], size=POINT_SIZE, color=p["color"])

    for g in _ghosts:
        _draw_ghost(g)

    _draw_pacman()
    _draw_lives()

    draw_text(WORLD_LEFT + 18, WORLD_TOP - 26,
              f"Score: {_score} / {TARGET_SCORE}  |  Ghost = -25pts -1 life")
    draw_text(WORLD_LEFT + 18, WORLD_TOP - 48,
              "W/A/S/D  |  Green +10  |  Red -10  |  R restart  |  ESC quit",
              color=(0.7, 0.75, 0.85))

    if _game_over:
        if _player_won:
            draw_text(-110,  15, "YOU WIN!  Score reached 100!",  color=(0.2, 1.0, 0.45))
            draw_text( -90, -15, "Press R to play again",         color=(0.9, 0.9, 0.9))
        else:
            if _lives <= 0:
                msg = "GAME OVER  —  You ran out of lives!"
            else:
                msg = "GAME OVER  —  Score dropped below -50!"
            draw_text(-140,  15, msg,                color=(1.0, 0.25, 0.25))
            draw_text( -90, -15, "Press R to retry", color=(0.9, 0.9, 0.9))


def run():
    init_window("Pacman", draw, update)
    init()
    print("W/A/S/D to move | R restart | ESC quit")
    start_loop()


if __name__ == "__main__":
    run()