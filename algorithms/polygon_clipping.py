def inside(p, edge, xmin, ymin, xmax, ymax):
    x, y = p
    if edge == 'LEFT':   return x >= xmin
    if edge == 'RIGHT':  return x <= xmax
    if edge == 'BOTTOM': return y >= ymin
    return y <= ymax  # TOP

def intersect(s, p, edge, xmin, ymin, xmax, ymax):
    sx, sy = s; px, py = p
    if edge == 'LEFT':
        t = (xmin - sx) / (px - sx);  return (xmin, sy + t*(py-sy))
    elif edge == 'RIGHT':
        t = (xmax - sx) / (px - sx);  return (xmax, sy + t*(py-sy))
    elif edge == 'BOTTOM':
        t = (ymin - sy) / (py - sy);  return (sx + t*(px-sx), ymin)
    else:  # TOP
        t = (ymax - sy) / (py - sy);  return (sx + t*(px-sx), ymax)

def clip_edge(polygon, edge, xmin, ymin, xmax, ymax):
    output = []
    if not polygon:
        return output
    s = polygon[-1]
    for p in polygon:
        p_in = inside(p, edge, xmin, ymin, xmax, ymax)
        s_in = inside(s, edge, xmin, ymin, xmax, ymax)
        if s_in and p_in:
            output.append(p)                                           # In -> In
        elif s_in and not p_in:
            output.append(intersect(s, p, edge, xmin, ymin, xmax, ymax))  # In -> Out
        elif not s_in and p_in:
            output.append(intersect(s, p, edge, xmin, ymin, xmax, ymax))  # Out -> In
            output.append(p)
        # Out -> Out: add nothing
        s = p
    return output

def sutherland_hodgman(polygon, xmin, ymin, xmax, ymax):
    for edge in ['LEFT', 'RIGHT', 'BOTTOM', 'TOP']:
        polygon = clip_edge(polygon, edge, xmin, ymin, xmax, ymax)
        if not polygon:
            break
    return polygon
