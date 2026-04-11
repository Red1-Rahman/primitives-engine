# Scenes Guide

Write scene modules only.

## Required module API

- You must define: init(), update(), draw().
- init(): reset all state.
- update(): update state only.
- draw(): render only.

## Register your scene

- Import your module in main.py.
- Add module to \_SCENES in main.py.
- Add matching title to \_SCENE_NAMES in main.py (same index).

## Core imports

from engine.renderer import draw_line_dda, draw_line_bresenham, draw_circle, draw_rect, draw_polygon, draw_filled_polygon, draw_text
from engine.input import is_key, is_special, is_mouse, mouse_pos
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

## Minimal scene template

from engine.renderer import draw_rect

def init():
pass

def update():
pass

def draw():
draw_rect(-400, -300, 800, 600, color=(0.1, 0.1, 0.1), filled=True)

## Avoid

- Do not create while loops or call glutMainLoop() inside a scene.
- Do not call init_window() or start_loop() from scene modules.
- Do not mutate engine callbacks or projection state from scene code.
- Do not forget to register the scene in main.py.

best regards - Redwan Rahman
