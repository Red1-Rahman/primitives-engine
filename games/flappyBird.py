# games\flappyBird.py
DISPLAY_NAME = "Flappy Bird"

import os
import random
from math import pi, cos, sin
from OpenGL.GL import *
from engine.input import is_key
from engine.renderer import draw_rect, draw_filled_polygon, draw_text
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP

_state = {}
_texture_id = None
_texture_loaded = False

# ─────────────────────────────────────────────
#  TEXTURE LOADING & HELPERS
# ─────────────────────────────────────────────

def _load_bird_texture():
    """Attempts to load the bird.png asset as an OpenGL texture."""
    global _texture_id, _texture_loaded
    if _texture_loaded: 
        return

    path = os.path.join("games", "assets-flappyBird", "bird.png")
    if not os.path.exists(path):
        _texture_loaded = True
        return

    try:
        from PIL import Image
        img = Image.open(path).convert("RGBA")
        # Flip vertically since OpenGL expects bottom-to-top image data
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.tobytes("raw", "RGBA")
        
        _texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, _texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    except Exception as e:
        print(f"[Flappy Bird] Failed to load bird texture: {e}")
    finally:
        _texture_loaded = True

def _draw_filled_circle(cx, cy, r, color=(1.0, 1.0, 1.0), segments=30):
    """Local helper for filled circles to guarantee availability."""
    glColor4f(*color, 1.0)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        angle = 2 * pi * i / segments
        glVertex2f(cx + r * cos(angle), cy + r * sin(angle))
    glEnd()

# ─────────────────────────────────────────────
#  ENGINE API
# ─────────────────────────────────────────────

def init():
    _load_bird_texture()
        
    _state["bird_x"] = -200
    _state["bird_y"] = 0
    _state["bird_vy"] = 0
    _state["radius"] = 18
    _state["gravity"] = -0.45
    _state["flap_strength"] = 7.5
    
    _state["pillars"] = []
    _state["score"] = 0
    _state["game_over"] = False
    _state["space_pressed"] = False
    
    _spawn_pillar(WORLD_RIGHT)


def _spawn_pillar(x):
    # Keep gap away from absolute top and bottom
    gap_y = random.uniform(WORLD_BOTTOM + 180, WORLD_TOP - 180)
    gap_size = 150
    _state["pillars"].append({
        "x": x,
        "width": 60,
        "gap_bottom": gap_y - gap_size / 2,
        "gap_top": gap_y + gap_size / 2,
        "passed": False
    })


def update():
    space_down = is_key(b" ")
    space_just_pressed = space_down and not _state["space_pressed"]
    _state["space_pressed"] = space_down

    if _state["game_over"]:
        # Restart on space
        if space_just_pressed:
            init()
        return

    # 1. Update Bird
    if space_just_pressed:
        _state["bird_vy"] = _state["flap_strength"]
        
    _state["bird_vy"] += _state["gravity"]
    _state["bird_y"] += _state["bird_vy"]

    # 2. Update Pillars
    speed = 4.0
    for p in _state["pillars"]:
        p["x"] -= speed

    # Spawn new pillar if the last one moved far enough
    if _state["pillars"] and _state["pillars"][-1]["x"] < WORLD_RIGHT - 250:
        _spawn_pillar(WORLD_RIGHT + 50)

    # Clean up off-screen pillars
    if _state["pillars"] and _state["pillars"][0]["x"] < WORLD_LEFT - 100:
        _state["pillars"].pop(0)

    # 3. Collision & Scoring
    bx = _state["bird_x"]
    by = _state["bird_y"]
    br = _state["radius"] - 2 # slightly forgiving hitbox

    # Ground or Sky collision
    if by - br < WORLD_BOTTOM or by + br > WORLD_TOP:
        _state["game_over"] = True

    # Pillar collision & score
    for p in _state["pillars"]:
        px = p["x"]
        pw = p["width"]

        # AABB intersection test
        if bx + br > px and bx - br < px + pw:
            if by - br < p["gap_bottom"] or by + br > p["gap_top"]:
                _state["game_over"] = True

        # Score update
        if not p["passed"] and bx > px + pw:
            _state["score"] += 1
            p["passed"] = True


def draw():
    # ─── BACKGROUND ─────────────────────────────────────────────
    # Sky Background
    draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM, 
              color=(0.53, 0.81, 0.92), filled=True)
    
    # Sun
    _draw_filled_circle(150, 180, 50, color=(1.0, 0.9, 0.2))

    # Back Dune (Dusty)
    draw_filled_polygon([
        (WORLD_LEFT, WORLD_BOTTOM), (WORLD_LEFT, -20),
        (-120, 60), (80, -80), (280, 40), (WORLD_RIGHT, -40),
        (WORLD_RIGHT, WORLD_BOTTOM)
    ], color=(0.82, 0.70, 0.53))
    
    # Front Dune (Dusty)
    draw_filled_polygon([
        (WORLD_LEFT, WORLD_BOTTOM), (WORLD_LEFT, -80),
        (-250, 20), (-20, -140), (180, -10), (380, -100),
        (WORLD_RIGHT, -60), (WORLD_RIGHT, WORLD_BOTTOM)
    ], color=(0.89, 0.76, 0.58))


    # ─── PILLARS ────────────────────────────────────────────────
    for p in _state["pillars"]:
        px, pw = p["x"], p["width"]
        
        # Bottom Pillar Fill & Outline
        bottom_h = p["gap_bottom"] - WORLD_BOTTOM
        draw_rect(px, WORLD_BOTTOM, pw, bottom_h, color=(0.4, 0.8, 0.4), filled=True)
        draw_rect(px, WORLD_BOTTOM, pw, bottom_h, color=(0.1, 0.4, 0.1), width=2.0)
        # Bottom Pillar Cap
        draw_rect(px - 4, p["gap_bottom"] - 20, pw + 8, 20, color=(0.3, 0.7, 0.3), filled=True)
        draw_rect(px - 4, p["gap_bottom"] - 20, pw + 8, 20, color=(0.1, 0.4, 0.1), width=2.0)

        # Top Pillar Fill & Outline
        top_h = WORLD_TOP - p["gap_top"]
        draw_rect(px, p["gap_top"], pw, top_h, color=(0.4, 0.8, 0.4), filled=True)
        draw_rect(px, p["gap_top"], pw, top_h, color=(0.1, 0.4, 0.1), width=2.0)
        # Top Pillar Cap
        draw_rect(px - 4, p["gap_top"], pw + 8, 20, color=(0.3, 0.7, 0.3), filled=True)
        draw_rect(px - 4, p["gap_top"], pw + 8, 20, color=(0.1, 0.4, 0.1), width=2.0)


    # ─── BIRD ───────────────────────────────────────────────────
    bx = _state["bird_x"]
    by = _state["bird_y"]
    br = _state["radius"]

    if _texture_id is not None:
        # Draw Textured Quad
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, _texture_id)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(bx - br, by - br)
        glTexCoord2f(1.0, 0.0); glVertex2f(bx + br, by - br)
        glTexCoord2f(1.0, 1.0); glVertex2f(bx + br, by + br)
        glTexCoord2f(0.0, 1.0); glVertex2f(bx - br, by + br)
        glEnd()
        glDisable(GL_TEXTURE_2D)
    else:
        # Fallback Primitive Bird
        _draw_filled_circle(bx, by, br, color=(0.9, 0.8, 0.1))
        # Wing
        _draw_filled_circle(bx - 4, by - 2, br * 0.6, color=(1.0, 1.0, 1.0))
        # Eye
        _draw_filled_circle(bx + 6, by + 5, 3, color=(0.0, 0.0, 0.0))
        # Beak
        draw_filled_polygon([(bx + br - 2, by), (bx + br + 8, by - 3), (bx + br - 2, by - 6)], color=(0.9, 0.4, 0.1))


    # ─── UI ─────────────────────────────────────────────────────
    # Score Shadow & Text
    draw_text(WORLD_LEFT + 22, WORLD_TOP - 32, f"Score: {_state['score']}", color=(0.0, 0.0, 0.0))
    draw_text(WORLD_LEFT + 20, WORLD_TOP - 30, f"Score: {_state['score']}", color=(1.0, 1.0, 1.0))

    if _state["game_over"]:
        # Game Over Overlay
        draw_rect(-120, -40, 240, 80, color=(0.0, 0.0, 0.0, 0.7), filled=True)
        draw_text(-60, 10, "GAME OVER", color=(1.0, 0.3, 0.3))
        draw_text(-85, -15, "Press SPACE to Restart", color=(1.0, 1.0, 1.0))