import math

POINT_LABELS = [chr(65 + i % 26) + (str(i // 26) if i >= 26 else "") 
                for i in range(1000)]

def run_2d_rotation(points, theta_deg, clockwise=False):
    """Rotate a list of (x,y) points by theta_deg degrees."""
    theta = math.radians(theta_deg)
    if clockwise:
        theta = -theta
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    if clockwise:
        xp_header = "x' = x·cosθ + y·sinθ"
        yp_header = "y' = −x·sinθ + y·cosθ"
    else:
        xp_header = "x' = x·cosθ − y·sinθ"
        yp_header = "y' = x·sinθ + y·cosθ"

    rows = []
    new_points = []
    for i, (x, y) in enumerate(points):
        xp = x * cos_t - y * sin_t
        yp = x * sin_t + y * cos_t
        rows.append({
            "Point": POINT_LABELS[i],
            "x": x,
            "y": y,
            "cos θ": round(cos_t, 6),
            "sin θ": round(sin_t, 6),
            xp_header: round(xp, 4),
            yp_header: round(yp, 4),
        })
        new_points.append((round(xp, 4), round(yp, 4)))
    return rows, new_points
