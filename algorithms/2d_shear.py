POINT_LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def run_2d_shear(points, shx=0.0, shy=0.0):
    """
    Shear a list of (x, y) points.
    shx: shear factor along X (shifts x based on y)
    shy: shear factor along Y (shifts y based on x)
    """
    rows = []
    new_points = []
    for i, (x, y) in enumerate(points):
        xp = x + shx * y
        yp = shy * x + y
        rows.append({
            "Point": POINT_LABELS[i],
            "x": x,
            "y": y,
            "Shx": shx,
            "Shy": shy,
            "x' = x + Shx·y": round(xp, 4),
            "y' = Shy·x + y": round(yp, 4),
        })
        new_points.append((round(xp, 4), round(yp, 4)))
    return rows, new_points
