POINT_LABELS = [chr(65 + i % 26) + (str(i // 26) if i >= 26 else "") 
                for i in range(1000)]

def run_2d_translation(points, tx, ty):
    """Translate a list of (x, y) points by (tx, ty)."""
    rows = []
    new_points = []
    for i, (x, y) in enumerate(points):
        xp = x + tx
        yp = y + ty
        rows.append({
            "Point": POINT_LABELS[i],
            "x": x,
            "y": y,
            "Tx": tx,
            "Ty": ty,
            "x' = x + Tx": round(xp, 4),
            "y' = y + Ty": round(yp, 4),
        })
        new_points.append((round(xp, 4), round(yp, 4)))
    return rows, new_points


def run_2d_translation_circle(cx, cy, r, tx, ty):
    """Translate a circle centre by (tx, ty); radius is unchanged."""
    new_cx = round(cx + tx, 4)
    new_cy = round(cy + ty, 4)
    rows = [
        {"Attribute": "Center x",
         "Original": cx,
         "Formula": f"x' = x + Tx = {cx} + ({tx})",
         "New": new_cx},
        {"Attribute": "Center y",
         "Original": cy,
         "Formula": f"y' = y + Ty = {cy} + ({ty})",
         "New": new_cy},
        {"Attribute": "Radius r",
         "Original": r,
         "Formula": "r  (unchanged)",
         "New": r},
    ]
    return rows, new_cx, new_cy
