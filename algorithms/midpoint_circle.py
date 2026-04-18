# algorithms\midpoint_circle.py
def eight_points(cx, cy, x, y):
    pts = set()
    for sx, sy in [(x,y),(-x,y),(x,-y),(-x,-y),(y,x),(-y,x),(y,-x),(-y,-x)]:
        pts.add((cx + sx, cy + sy))
    return sorted(pts)

def run_midpoint_circle(cx, cy, r):
    r_float = float(r)
    is_int  = isinstance(r, int) or (isinstance(r, float) and r.is_integer())
    if is_int:
        P = 1 - int(r_float)
        p0_str = f"1 − r = 1 − {int(r_float)} = {P}"
    else:
        P = round(5/4 - r_float, 6)
        p0_str = f"5/4 − r = 1.25 − {r_float} = {P}"

    x, y = 0, int(round(r_float))
    rows = []
    all_pixels = []

    while x <= y:
        pts = eight_points(cx, cy, x, y)
        all_pixels.extend(pts)
        x_old, y_old, P_old = x, y, P
        x += 1
        if P_old < 0:
            y_new = y_old
            new_P = P_old + 2 * x_old + 3
            dec   = "P < 0  →  y unchanged,  P+1 = P + 2xₖ + 3"
        else:
            y    -= 1
            y_new = y
            new_P = P_old + 2 * x_old + 5 - 2 * y_old
            dec   = "P ≥ 0  →  y decremented,  P+1 = P + 2xₖ + 5 − 2yₖ"
        pts_str = ", ".join(f"({px},{py})" for px, py in pts)
        rows.append({"k": len(rows), "Pₖ": P_old, "xₖ": x_old, "yₖ": y_old,
                     "x(k+1)": x, "y(k+1)": y_new, "Pₖ₊₁": new_P,
                     "Decision": dec, "8 pixels": pts_str})
        P = new_P

    seen = set(); unique_pixels = []
    for pt in all_pixels:
        if pt not in seen:
            seen.add(pt); unique_pixels.append(pt)
    return p0_str, rows, unique_pixels
