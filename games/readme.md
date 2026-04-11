# Games Guide

Write game modules only.

## Required module API

- You must define: init(), update(), draw().
- Optional: DISPLAY_NAME = "Your Game Name".
- main.py auto-loads modules in games/ that expose callable init/update/draw.

## Core imports

from engine.input import is_key, is_special, is_mouse, mouse_pos
from engine.renderer import draw_point, draw_line_dda, draw_line_bresenham, draw_circle, draw_rect, draw_polygon, draw_filled_polygon, draw_text
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP
from algorithms import ...

## Algorithms

- run_dda(x1, y1, x2, y2): DDA line rasterization; returns slope info and rounded pixel rows.
- run_bresenham(x1, y1, x2, y2): integer line rasterization; returns slope info and step decision rows.
- run_midpoint_circle(cx, cy, r): midpoint circle rasterization; returns initial decision string, steps, and unique circle pixels.
- run_cohen_sutherland(x1, y1, x2, y2, xmin, ymin, xmax, ymax): clips one line to a viewport; returns steps and clipped endpoints or None.
- sutherland_hodgman(polygon, xmin, ymin, xmax, ymax): clips a polygon to a rectangular viewport; returns clipped polygon points.
- run_2d_translation(points, tx, ty): translates point list; returns table plus transformed points.
- run_2d_translation_circle(cx, cy, r, tx, ty): translates circle center; radius stays unchanged.
- run_2d_rotation(points, theta_deg, clockwise=False): rotates points by angle in degrees; returns table plus rotated points.
- run_2d_scaling(points, sx, sy): scales point list non-uniformly on x/y; returns table plus scaled points.
- run_2d_scaling_circle(cx, cy, r, sx, sy): scales circle center and radius (radius uses sx in this engine).
- run_2d_reflection(points, axis): reflects points across x-axis, y-axis, origin, y=x, or y=-x.
- run_2d_shear(points, shx=0.0, shy=0.0): shears points in x and/or y; returns table plus sheared points.

## Minimal game template

DISPLAY_NAME = "My Game"

from engine.input import is_key
from engine.renderer import draw_rect, draw_text
from engine.window import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP

\_state = {}

def init():
\_state["score"] = 0

def update():
if is_key(b"r") or is_key(b"R"):
init()

def draw():
draw_rect(WORLD_LEFT, WORLD_BOTTOM, WORLD_RIGHT - WORLD_LEFT, WORLD_TOP - WORLD_BOTTOM,
color=(0.06, 0.06, 0.09), filled=True)
draw_text(WORLD_LEFT + 16, WORLD_TOP - 28, f"Score: {\_state['score']}")

## Avoid

- Do not create while loops or call glutMainLoop() in a game module.
- Do not call init_window() or start_loop() for launcher mode.
- Do not block update() with long tasks, sleep, or input() calls.
- Do not rely on file names starting with \_ (those are skipped by discovery).

best regards - Redwan Rahman
