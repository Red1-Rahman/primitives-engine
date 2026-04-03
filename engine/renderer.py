import math
from OpenGL.GL import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, glutBitmapCharacter
from algorithms.dda import run_dda
from algorithms.bresenham import run_bresenham
from algorithms.midpoint_circle import run_midpoint_circle


# ─────────────────────────────────────────────
#  COLOR
# ─────────────────────────────────────────────

def set_color(r, g, b, a=1.0):
    glColor4f(r, g, b, a)


# ─────────────────────────────────────────────
#  POINT
# ─────────────────────────────────────────────

def draw_point(x, y, size=2.0, color=(1.0, 1.0, 1.0)):
    set_color(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


# ─────────────────────────────────────────────
#  LINES
# ─────────────────────────────────────────────

def draw_line_dda(x1, y1, x2, y2, color=(1.0, 1.0, 1.0), size=2.0):
    """Draw a line using the DDA algorithm."""
    _, _, rows = run_dda(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)))
    set_color(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    for row in rows:
        glVertex2f(row["x (rounded)"], row["y (rounded)"])
    glEnd()


def draw_line_bresenham(x1, y1, x2, y2, color=(1.0, 1.0, 1.0), size=2.0):
    """Draw a line using the Bresenham algorithm."""
    ix1, iy1, ix2, iy2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))
    _, _, rows = run_bresenham(ix1, iy1, ix2, iy2)
    set_color(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(ix1, iy1)  # starting point is not emitted by the algorithm
    for row in rows:
        glVertex2f(row["x(i+1)"], row["y(i+1)"])
    glEnd()


def draw_line_raw(x1, y1, x2, y2, color=(1.0, 1.0, 1.0), width=1.0):
    """Draw a line directly via GL_LINES (no algorithm, fast)."""
    set_color(*color)
    glLineWidth(width)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()
    glLineWidth(1.0)


# ─────────────────────────────────────────────
#  CIRCLE
# ─────────────────────────────────────────────

def draw_circle(cx, cy, r, color=(1.0, 1.0, 1.0), size=2.0):
    """Draw a circle using the Midpoint Circle algorithm."""
    _, _, pixels = run_midpoint_circle(cx, cy, r)
    set_color(*color)
    glPointSize(size)
    glBegin(GL_POINTS)
    for px, py in pixels:
        glVertex2f(px, py)
    glEnd()


# ─────────────────────────────────────────────
#  POLYGON
# ─────────────────────────────────────────────

def draw_polygon(points, color=(1.0, 1.0, 1.0), width=1.0, closed=True):
    """
    Draw a polygon from a list of (x, y) points.
    closed=True  → GL_LINE_LOOP  (last point connects back to first)
    closed=False → GL_LINE_STRIP (open path)
    """
    set_color(*color)
    glLineWidth(width)
    mode = GL_LINE_LOOP if closed else GL_LINE_STRIP
    glBegin(mode)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()
    glLineWidth(1.0)


def draw_filled_polygon(points, color=(1.0, 1.0, 1.0, 0.5)):
    """Draw a filled polygon using GL_POLYGON."""
    set_color(*color)
    glBegin(GL_POLYGON)
    for x, y in points:
        glVertex2f(x, y)
    glEnd()


# ─────────────────────────────────────────────
#  RECTANGLE  (convenience wrapper)
# ─────────────────────────────────────────────

def draw_rect(x, y, w, h, color=(1.0, 1.0, 1.0), width=1.0, filled=False):
    """
    Draw a rectangle.
    (x, y) is the bottom-left corner.
    """
    points = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
    if filled:
        draw_filled_polygon(points, color)
    else:
        draw_polygon(points, color, width)


def draw_filled_circle(cx, cy, r, color=(1.0, 1.0, 1.0), segments=60):
    """Draw a filled circle using GL_TRIANGLE_FAN."""
    set_color(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        glVertex2f(cx + r * math.cos(angle), cy + r * math.sin(angle))
    glEnd()


# ─────────────────────────────────────────────
#  TEXT
# ─────────────────────────────────────────────

def draw_text(x, y, text, color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_HELVETICA_18):
    """Draw bitmap text at world position (x, y)."""
    set_color(*color)
    glRasterPos2f(x, y)
    for ch in str(text):
        glutBitmapCharacter(font, ord(ch))