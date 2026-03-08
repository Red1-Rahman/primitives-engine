POINT_LABELS = [chr(65 + i % 26) + (str(i // 26) if i >= 26 else "") 
                for i in range(1000)]

AXES = ("x-axis", "y-axis", "origin", "y=x", "y=-x")

def run_2d_reflection(points, axis):
    """
    Reflect a list of (x, y) points across a given axis.
    axis: 'x-axis' | 'y-axis' | 'origin' | 'y=x' | 'y=-x'
    """
    rows = []
    new_points = []
    for i, (x, y) in enumerate(points):
        if axis == "x-axis":
            xp, yp = x, -y
            formula = "x' = x,  y' = −y"
        elif axis == "y-axis":
            xp, yp = -x, y
            formula = "x' = −x,  y' = y"
        elif axis == "origin":
            xp, yp = -x, -y
            formula = "x' = −x,  y' = −y"
        elif axis == "y=x":
            xp, yp = y, x
            formula = "x' = y,  y' = x"
        elif axis == "y=-x":
            xp, yp = -y, -x
            formula = "x' = −y,  y' = −x"
        else:
            raise ValueError(f"Unknown axis: {axis}")

        rows.append({
            "Point": POINT_LABELS[i],
            "x": x,
            "y": y,
            "Axis": axis,
            "Formula": formula,
            "x'": round(xp, 4),
            "y'": round(yp, 4),
        })
        new_points.append((round(xp, 4), round(yp, 4)))
    return rows, new_points
