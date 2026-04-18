# algorithms\scaling2d.py
POINT_LABELS = [chr(65 + i % 26) + (str(i // 26) if i >= 26 else "") 
                for i in range(1000)]

def run_2d_scaling(points, sx, sy):
    """Scale a list of (x, y) points by (sx, sy)."""
    rows = []
    new_points = []
    for i, (x, y) in enumerate(points):
        xp = x * sx
        yp = y * sy
        rows.append({
            "Point": POINT_LABELS[i],
            "x": x,
            "y": y,
            "Sx": sx,
            "Sy": sy,
            "x' = x · Sx": round(xp, 4),
            "y' = y · Sy": round(yp, 4),
        })
        new_points.append((round(xp, 4), round(yp, 4)))
    return rows, new_points


def run_2d_scaling_circle(cx, cy, r, sx, sy):
    """Scale a circle. If sx == sy, radius scales uniformly."""
    new_cx = round(cx * sx, 4)
    new_cy = round(cy * sy, 4)
    new_r  = round(r * sx, 4)  # uniform scale assumed
    rows = [
        {"Attribute": "Center x", "Original": cx,
         "Formula": f"x' = x · Sx = {cx} × {sx}", "New": new_cx},
        {"Attribute": "Center y", "Original": cy,
         "Formula": f"y' = y · Sy = {cy} × {sy}", "New": new_cy},
        {"Attribute": "Radius r",  "Original": r,
         "Formula": f"r' = r · Sx = {r} × {sx}",  "New": new_r},
    ]
    return rows, new_cx, new_cy, new_r
