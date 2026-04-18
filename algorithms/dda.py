# algorithms\dda.py
import math

def run_dda(x1, y1, x2, y2):
    def round_half_away_from_zero(v: float) -> int:
        return int(math.floor(v + 0.5)) if v >= 0 else int(math.ceil(v - 0.5))

    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))

    if steps == 0:
        return None, None, [{"x (rounded)": x1, "y (rounded)": y1}]

    slope_str = None
    slope_note = ""

    if dx == 0:
        slope_str = "undefined (vertical line)"
        slope_val = None
    else:
        slope_val = dy / dx
        slope_str = f"{dy}/{dx} = {slope_val:.4f}"

    if abs(dx) >= abs(dy):
        slope_note = f"|slope| ≤ 1  →  step along X axis  (steps = {steps})"
    else:
        slope_note = f"|slope| > 1  →  step along Y axis  (steps = {steps})"

    x_inc = dx / steps
    y_inc = dy / steps

    rows = []
    for i in range(steps + 1):
        cx = x1 + i * x_inc
        cy = y1 + i * y_inc
        rows.append({
            "Step (i)": i,
            "x (exact)": round(cx, 4),
            "y (exact)": round(cy, 4),
            "x (rounded)": round_half_away_from_zero(cx),
            "y (rounded)": round_half_away_from_zero(cy),
        })

    return slope_str, slope_note, rows
