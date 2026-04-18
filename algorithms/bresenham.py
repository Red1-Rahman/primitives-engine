# algorithms\bresenham.py
import math
def run_bresenham(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x2 >= x1 else -1
    sy = 1 if y2 >= y1 else -1
    orig_dx = x2 - x1
    orig_dy = y2 - y1
    slope_str = None
    slope_note = ""
    if orig_dx == 0:
        slope_str = "undefined (vertical line)"
    else:
        slope_val = orig_dy / orig_dx
        slope_str = f"{orig_dy}/{orig_dx} = {slope_val:.4f}"
    rows = []
    # ── Case: |slope| ≤ 1  (drive along X) ───────────────────────────────────
    if dx >= dy:
        slope_note = f"|slope| ≤ 1  →  drive along X axis"
        P = 2 * dy - dx
        cx, cy = x1, y1

        total_steps = dx
        for i in range(total_steps):
            nx = cx + sx
            if P < 0:
                ny = cy
                new_P = P + 2 * dy
            else:
                ny = cy + sy
                new_P = P + 2 * dy - 2 * dx

            rows.append({
                "i": i,
                "Pᵢ": P,
                "xᵢ": cx,
                "yᵢ": cy,
                "x(i+1)": nx,
                "y(i+1)": ny,
                "Decision": "P < 0  →  y unchanged" if P < 0 else "P ≥ 0  →  y incremented",
            })
            cx, cy, P = nx, ny, new_P
    # ── Case: |slope| > 1  (drive along Y) ───────────────────────────────────
    else:
        slope_note = f"|slope| > 1  →  drive along Y axis"
        P = 2 * dx - dy
        cx, cy = x1, y1

        total_steps = dy
        for i in range(total_steps):
            ny = cy + sy
            if P < 0:
                nx = cx
                new_P = P + 2 * dx
            else:
                nx = cx + sx
                new_P = P + 2 * dx - 2 * dy
            rows.append({
                "i": i,
                "Pᵢ": P,
                "xᵢ": cx,
                "yᵢ": cy,
                "x(i+1)": nx,
                "y(i+1)": ny,
                "Decision": "P < 0  →  x unchanged" if P < 0 else "P ≥ 0  →  x incremented",
            })
            cx, cy, P = nx, ny, new_P

    return slope_str, slope_note, rows
