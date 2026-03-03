INSIDE = 0
LEFT   = 1
RIGHT  = 2
BOTTOM = 4
TOP    = 8

def compute_code(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def run_cohen_sutherland(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """
    Clip line (x1,y1)→(x2,y2) against rectangle [xmin,xmax] x [ymin,ymax].
    Returns clipped endpoints and a step-by-step table.
    """
    code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)
    code2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

    rows = []
    iteration = 0
    accepted = False

    while True:
        iteration += 1

        if not (code1 | code2):
            # Both inside
            accepted = True
            rows.append({
                "Iteration": iteration,
                "x1": round(x1, 4), "y1": round(y1, 4),
                "x2": round(x2, 4), "y2": round(y2, 4),
                "code1": f"{code1:04b}", "code2": f"{code2:04b}",
                "Decision": "Accept — both endpoints inside viewport",
            })
            break

        elif code1 & code2:
            # Both outside same region
            rows.append({
                "Iteration": iteration,
                "x1": round(x1, 4), "y1": round(y1, 4),
                "x2": round(x2, 4), "y2": round(y2, 4),
                "code1": f"{code1:04b}", "code2": f"{code2:04b}",
                "Decision": "Reject — both endpoints share an outside region",
            })
            break

        else:
            # Clip
            outside_code = code1 if code1 else code2

            if outside_code & TOP:
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                y = ymax
                decision = f"Clip TOP: y={ymax}"
            elif outside_code & BOTTOM:
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                y = ymin
                decision = f"Clip BOTTOM: y={ymin}"
            elif outside_code & RIGHT:
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                x = xmax
                decision = f"Clip RIGHT: x={xmax}"
            elif outside_code & LEFT:
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                x = xmin
                decision = f"Clip LEFT: x={xmin}"

            rows.append({
                "Iteration": iteration,
                "x1": round(x1, 4), "y1": round(y1, 4),
                "x2": round(x2, 4), "y2": round(y2, 4),
                "code1": f"{code1:04b}", "code2": f"{code2:04b}",
                "Decision": decision,
            })

            if outside_code == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

    if accepted:
        return rows, (round(x1,4), round(y1,4)), (round(x2,4), round(y2,4))
    else:
        return rows, None, None
