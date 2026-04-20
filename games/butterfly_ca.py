"""
Butterfly CA Trail — butterfly_ca.py

A butterfly drifts through Perlin-noise-driven flight, injecting energy into a
2D cellular-automaton grid that spreads, decays, and dithers into a glowing trail.

Controls:
  R       — reset
  SPACE   — toggle pause
    WASD    — steer butterfly
  +/-     — speed up / slow down butterfly
    X       — toggle dithering
  C       — cycle colour palette
"""

DISPLAY_NAME = "🦋 Butterfly CA Trail"

# ── imports ──────────────────────────────────────────────────────────────────
import math, random
from engine.input   import is_key
from engine.renderer import draw_point, draw_rect, draw_text
from engine.window  import WORLD_LEFT, WORLD_RIGHT, WORLD_BOTTOM, WORLD_TOP

# ── tuneable constants ────────────────────────────────────────────────────────
CELL_SIZE   = 6          # pixels per grid cell
INJECT_AMT  = 0.88       # baseline energy dropped per frame
DECAY       = 0.014      # energy lost per frame
DIFFUSE     = 0.11       # fraction shared with neighbours
SPARKLE     = 0.0006     # chance of random spark per frame
SPEED_BASE  = 0.55       # butterfly world-units / frame
FLAP_SPEED  = 0.14       # wing flap rate
MANUAL_SPEED = 1.05      # speed when player is steering
STEER_BLEND_AUTO   = 0.18
STEER_BLEND_MANUAL = 0.34

# ── palettes (name, [(r,g,b) thresholds from low→high]) ──────────────────────
PALETTES = [
    ("Aurora",    [(0.02,0.02,0.08),(0.05,0.18,0.35),(0.12,0.55,0.62),
                   (0.65,0.95,0.72),(0.98,0.98,0.90)]),
    ("Ember",     [(0.04,0.01,0.01),(0.35,0.05,0.02),(0.80,0.28,0.02),
                   (0.97,0.72,0.12),(0.99,0.97,0.85)]),
    ("Neon Dusk", [(0.02,0.01,0.06),(0.28,0.04,0.38),(0.70,0.08,0.55),
                   (0.92,0.55,0.90),(0.98,0.90,0.99)]),
    ("Frost",     [(0.02,0.04,0.08),(0.06,0.20,0.45),(0.18,0.55,0.82),
                   (0.72,0.88,0.97),(0.96,0.98,1.00)]),
]

# ── Perlin noise (simple 2-D, no deps) ───────────────────────────────────────
def _fade(t): return t*t*t*(t*(t*6-15)+10)
def _lerp(a,b,t): return a+t*(b-a)
def _grad(h,x,y):
    h &= 3
    if h==0: return  x+y
    if h==1: return -x+y
    if h==2: return  x-y
    return         -x-y

_PERM = list(range(256))
random.shuffle(_PERM)
_PERM *= 2

def perlin2(x, y):
    xi,yi = int(math.floor(x))&255, int(math.floor(y))&255
    xf,yf = x-math.floor(x), y-math.floor(y)
    u,v   = _fade(xf), _fade(yf)
    a  = _PERM[xi]+yi;   aa=_PERM[a]; ab=_PERM[a+1]
    b  = _PERM[xi+1]+yi; ba=_PERM[b]; bb=_PERM[b+1]
    return _lerp(_lerp(_grad(_PERM[aa],xf,yf),   _grad(_PERM[ba],xf-1,yf),   u),
                 _lerp(_grad(_PERM[ab],xf,yf-1), _grad(_PERM[bb],xf-1,yf-1), u), v)

# ── dithering kernel (Bayer 4×4) ─────────────────────────────────────────────
_BAYER = [[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
def bayer(gx, gy): return _BAYER[gy&3][gx&3] / 16.0

# ── state ─────────────────────────────────────────────────────────────────────
_s = {}

def _key_down_any(*keys):
    return any(is_key(k) for k in keys)

def _just_pressed_any(*keys):
    prev = _s.setdefault('prev_keys', {})
    fired = False
    for key in keys:
        down = is_key(key)
        if down and not prev.get(key, False):
            fired = True
        prev[key] = down
    return fired

def _world_to_grid(wx, wy, cols, rows):
    nx = (wx - WORLD_LEFT)  / (WORLD_RIGHT - WORLD_LEFT)
    ny = (wy - WORLD_BOTTOM)/ (WORLD_TOP   - WORLD_BOTTOM)
    return int(nx*cols), int(ny*rows)

def _grid_to_world(gx, gy, cols, rows):
    cx = WORLD_LEFT  + (gx+0.5)/(cols) * (WORLD_RIGHT-WORLD_LEFT)
    cy = WORLD_BOTTOM+ (gy+0.5)/(rows) * (WORLD_TOP-WORLD_BOTTOM)
    return cx, cy

def init():
    W = int(WORLD_RIGHT - WORLD_LEFT)
    H = int(WORLD_TOP   - WORLD_BOTTOM)
    cols = W // CELL_SIZE
    rows = H // CELL_SIZE

    grid  = [[0.0]*rows for _ in range(cols)]
    ngrid = [[0.0]*rows for _ in range(cols)]

    # butterfly starts near centre
    bx = (WORLD_LEFT+WORLD_RIGHT)*0.5
    by = (WORLD_BOTTOM+WORLD_TOP)*0.5

    _s.update(dict(
        cols=cols, rows=rows,
        grid=grid, ngrid=ngrid,
        bx=bx, by=by,
        bvx=SPEED_BASE, bvy=0.0,
        heading=0.0,
        t=0.0,          # noise time
        flap=0.0,       # wing phase
        paused=False,
        speed_mult=1.0,
        dither=True,
        palette_idx=0,
        frame=0,
        prev_keys={},
    ))

def _inject_ellipse(cx, cy, heading, r_fwd, r_lat, amount, skew=0.0):
    grid = _s['grid']
    cols, rows = _s['cols'], _s['rows']
    c, s = math.cos(heading), math.sin(heading)
    bound = int(max(r_fwd, r_lat) + 3)
    fden = max(0.1, r_fwd*r_fwd)
    lden = max(0.1, r_lat*r_lat)

    for gx in range(int(cx)-bound, int(cx)+bound+1):
        if not (0 <= gx < cols):
            continue
        for gy in range(int(cy)-bound, int(cy)+bound+1):
            if not (0 <= gy < rows):
                continue
            dx = gx - cx
            dy = gy - cy
            fwd = dx*c + dy*s
            lat = -dx*s + dy*c
            fwd += skew * lat
            d = (fwd*fwd)/fden + (lat*lat)/lden
            if d <= 1.0:
                w = (1.0 - d)
                grid[gx][gy] = min(1.0, grid[gx][gy] + amount*w*w)

def _inject_wingbeat(gx, gy, heading, flap):
    beat = math.sin(flap*2.0)
    wing_open = abs(math.sin(flap))
    pulse = 0.70 + 0.50*max(0.0, beat)

    fx, fy = math.cos(heading), math.sin(heading)
    nx, ny = -fy, fx

    rear = 1.5 + 1.8*wing_open
    span = 2.0 + 2.7*wing_open

    # core wake keeps the trail coherent and directional.
    _inject_ellipse(
        gx - fx*rear,
        gy - fy*rear,
        heading,
        r_fwd=2.4 + 1.0*wing_open,
        r_lat=0.8 + 0.2*(1.0-wing_open),
        amount=INJECT_AMT*0.54*pulse,
        skew=0.0,
    )

    # asymmetric left/right lobes encode wing beats into the trail.
    for side, bias in ((1.0, max(0.0, beat)), (-1.0, max(0.0, -beat))):
        cx = gx + nx*side*span - fx*(rear + 0.5)
        cy = gy + ny*side*span - fy*(rear + 0.5)
        _inject_ellipse(
            cx,
            cy,
            heading,
            r_fwd=2.8 + 0.9*wing_open,
            r_lat=1.0 + 0.4*wing_open,
            amount=INJECT_AMT*(0.62 + 0.40*bias),
            skew=0.24*side*beat,
        )

        tipx = gx + nx*side*(span + 1.3*wing_open) - fx*(rear + 1.9)
        tipy = gy + ny*side*(span + 1.3*wing_open) - fy*(rear + 1.9)
        _inject_ellipse(
            tipx,
            tipy,
            heading,
            r_fwd=1.7,
            r_lat=0.8,
            amount=INJECT_AMT*0.33*(0.7 + 0.3*bias),
            skew=0.18*side,
        )

def _ca_step():
    grid  = _s['grid']
    ngrid = _s['ngrid']
    cols, rows = _s['cols'], _s['rows']
    t = _s['t']
    for gx in range(cols):
        for gy in range(rows):
            v = grid[gx][gy]
            # blend cardinal and diagonal diffusion for smoother wake ribbons.
            nb4 = 0.0; cnt4 = 0
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                nx2, ny2 = gx+dx, gy+dy
                if 0<=nx2<cols and 0<=ny2<rows:
                    nb4 += grid[nx2][ny2]; cnt4+=1

            nb_diag = 0.0; cnt_diag = 0
            for dx,dy in ((-1,-1),(-1,1),(1,-1),(1,1)):
                nx2, ny2 = gx+dx, gy+dy
                if 0<=nx2<cols and 0<=ny2<rows:
                    nb_diag += grid[nx2][ny2]; cnt_diag+=1

            if cnt4:
                v += DIFFUSE*0.78*(nb4/cnt4 - v)
            if cnt_diag:
                v += DIFFUSE*0.26*(nb_diag/cnt_diag - v)

            # slight non-linear decay helps keep bright streak cores alive.
            v -= DECAY*(0.72 + 0.55*v)

            # sparkle
            if random.random() < SPARKLE:
                pv = perlin2(gx*0.07+t*0.3, gy*0.07+t*0.3)
                if pv > 0.1:
                    v += 0.25*pv
            ngrid[gx][gy] = max(0.0, min(1.0, v))
    # swap
    _s['grid'], _s['ngrid'] = ngrid, grid

def _map_color(v, gx, gy):
    pal = PALETTES[_s['palette_idx']][1]
    n   = len(pal)-1
    if _s['dither']:
        v = max(0.0, min(1.0, v + (bayer(gx,gy)-0.5)*0.25))
    idx = min(int(v*n), n-1)
    t2  = v*n - idx
    r0,g0,b0 = pal[idx]
    r1,g1,b1 = pal[min(idx+1,n)]
    return r0+(r1-r0)*t2, g0+(g1-g0)*t2, b0+(b1-b0)*t2

def update():
    # --- key controls ---
    if _just_pressed_any(b'r', b'R'):
        init(); return
    if _just_pressed_any(b' '):
        _s['paused'] = not _s['paused']
    if _key_down_any(b'+', b'='):
        _s['speed_mult'] = min(3.0, _s['speed_mult']+0.05)
    if _key_down_any(b'-'):
        _s['speed_mult'] = max(0.2, _s['speed_mult']-0.05)
    if _just_pressed_any(b'x', b'X'):
        _s['dither'] = not _s['dither']
    if _just_pressed_any(b'c', b'C'):
        _s['palette_idx'] = (_s['palette_idx']+1) % len(PALETTES)

    if _s['paused']: return

    dt = _s['speed_mult']
    t  = _s['t']
    ix = (1 if _key_down_any(b'd', b'D') else 0) - (1 if _key_down_any(b'a', b'A') else 0)
    iy = (1 if _key_down_any(b'w', b'W') else 0) - (1 if _key_down_any(b's', b'S') else 0)
    manual = (ix != 0 or iy != 0)

    # steer by Perlin flow unless player overrides with WASD.
    angle_noise = perlin2(t*1.1, 0.5) * math.pi * 2.5
    nfx, nfy = math.cos(angle_noise), math.sin(angle_noise)

    if manual:
        im = math.hypot(ix, iy) or 1.0
        ix, iy = ix/im, iy/im
        spd = MANUAL_SPEED * dt * (0.92 + 0.16*abs(perlin2(t*0.7, 7.7)))
        tvx = ix*spd + nfx*0.10*dt
        tvy = iy*spd + nfy*0.10*dt
        blend = STEER_BLEND_MANUAL
    else:
        speed_noise = 0.82 + 0.38*abs(perlin2(t*0.7, 9.3))
        spd = SPEED_BASE * dt * speed_noise
        tvx = nfx*spd
        tvy = nfy*spd
        blend = STEER_BLEND_AUTO

    _s['bvx'] = _lerp(_s['bvx'], tvx, blend)
    _s['bvy'] = _lerp(_s['bvy'], tvy, blend)

    mag = math.hypot(_s['bvx'], _s['bvy'])
    cap = (MANUAL_SPEED if manual else SPEED_BASE*1.35) * dt
    if mag > cap and mag > 1e-6:
        k = cap / mag
        _s['bvx'] *= k
        _s['bvy'] *= k

    bx = _s['bx'] + _s['bvx']
    by = _s['by'] + _s['bvy']

    # bounce off world edges with noise perturbation
    pad = (WORLD_RIGHT-WORLD_LEFT)*0.05
    if bx < WORLD_LEFT+pad:
        _s['bvx'] =  abs(_s['bvx']) + random.uniform(0,0.3)*dt
    if bx > WORLD_RIGHT-pad:
        _s['bvx'] = -abs(_s['bvx']) - random.uniform(0,0.3)*dt
    if by < WORLD_BOTTOM+pad:
        _s['bvy'] =  abs(_s['bvy']) + random.uniform(0,0.3)*dt
    if by > WORLD_TOP-pad:
        _s['bvy'] = -abs(_s['bvy']) - random.uniform(0,0.3)*dt

    bx = max(WORLD_LEFT+pad, min(WORLD_RIGHT-pad, bx))
    by = max(WORLD_BOTTOM+pad, min(WORLD_TOP-pad, by))
    _s['bx'], _s['by'] = bx, by

    if abs(_s['bvx']) + abs(_s['bvy']) > 1e-6:
        _s['heading'] = math.atan2(_s['bvy'], _s['bvx'])

    # inject asymmetric wing-beat energy into the grid.
    gx, gy = _world_to_grid(bx, by, _s['cols'], _s['rows'])
    _inject_wingbeat(gx, gy, _s['heading'], _s['flap'])

    # CA step
    _ca_step()

    _s['flap'] += FLAP_SPEED * dt * (0.8 + 0.4*abs(perlin2(t*2.1, 3.7)))
    _s['t']    += 0.012 * dt
    _s['frame']+= 1

def draw():
    # background
    draw_rect(WORLD_LEFT, WORLD_BOTTOM,
              WORLD_RIGHT-WORLD_LEFT, WORLD_TOP-WORLD_BOTTOM,
              color=(0.01,0.01,0.04), filled=True)

    grid = _s['grid']
    cols, rows = _s['cols'], _s['rows']
    cs  = CELL_SIZE

    # draw CA grid
    for gx in range(cols):
        for gy in range(rows):
            v = grid[gx][gy]
            if v < 0.015: continue
            wx, wy = _grid_to_world(gx, gy, cols, rows)
            r,g,b  = _map_color(v, gx, gy)
            draw_rect(wx - cs*0.5, wy - cs*0.5, cs, cs, color=(r,g,b), filled=True)

    # draw butterfly
    bx, by = _s['bx'], _s['by']
    flap   = _s['flap']
    heading = _s['heading']

    def orient(local_fwd, local_lat):
        c, s = math.cos(heading), math.sin(heading)
        return bx + local_fwd*c - local_lat*s, by + local_fwd*s + local_lat*c

    pal_hi = PALETTES[_s['palette_idx']][1][-1]
    pal_mid= PALETTES[_s['palette_idx']][1][-2]
    pal_low= PALETTES[_s['palette_idx']][1][2]

    wing_open = abs(math.sin(flap))
    for side in (-1, 1):
        wing_phase = 0.5 + 0.5*math.sin(flap*2.0 + (0.0 if side > 0 else 1.1))
        span = 7.0 + 6.5*wing_open + wing_phase*1.6
        steps = int(span) + 1
        for i in range(steps):
            frac = i / max(steps-1, 1)
            arch = math.sin(frac*math.pi)
            lat = side*(2.0 + span*frac)

            fwd_up = -0.8 + 5.0*arch*(1.0-0.12*frac)
            fwd_low = -1.4 + 2.7*arch*(1.0-0.26*frac)

            wx2, wy2 = orient(fwd_up, lat)
            wx3, wy3 = orient(fwd_low, lat*0.86)

            alpha = 1.0 - frac*0.60
            r = pal_hi[0]*alpha + pal_mid[0]*(1-alpha)
            g = pal_hi[1]*alpha + pal_mid[1]*(1-alpha)
            b = pal_hi[2]*alpha + pal_mid[2]*(1-alpha)
            draw_point(wx2, wy2, color=(r,g,b))
            draw_point(wx3, wy3, color=(r*0.82,g*0.82,b*0.82))

            # tip sparkle gives each wing a clear silhouette.
            if frac > 0.80 and i % 2 == 0:
                twx, twy = orient(fwd_up-0.5, lat + side*0.3)
                draw_point(twx, twy, color=pal_hi)

    # segmented body aligned with heading.
    for i in range(-6, 7):
        frac = abs(i) / 6.0
        bmix = 0.35 + 0.65*(1.0-frac)
        color = (
            pal_mid[0]*(1.0-bmix) + pal_hi[0]*bmix,
            pal_mid[1]*(1.0-bmix) + pal_hi[1]*bmix,
            pal_mid[2]*(1.0-bmix) + pal_hi[2]*bmix,
        )
        wx2, wy2 = orient(i*0.62, 0.0)
        draw_point(wx2, wy2, color=color)

    # head and antennae.
    hx, hy = orient(4.7, 0.0)
    draw_point(hx, hy, color=pal_hi)
    for side in (-1, 1):
        for k in range(1, 5):
            wx2, wy2 = orient(4.1 + k*0.8, side*(0.35 + 0.45*k))
            tint = 0.5 + 0.5*(1.0-k/5.0)
            draw_point(wx2, wy2, color=(pal_low[0]*tint, pal_low[1]*tint, pal_low[2]*tint))

    # HUD
    pal_name = PALETTES[_s['palette_idx']][0]
    draw_text(WORLD_LEFT+8, WORLD_TOP-20,
              f"🦋 Butterfly CA Trail  |  palette: {pal_name}  |  "
              f"speed: {_s['speed_mult']:.1f}x  |  "
              f"dither: {'on' if _s['dither'] else 'off'}",
              color=(0.5,0.5,0.6))
    draw_text(WORLD_LEFT+8, WORLD_TOP-38,
              "WASD=steer  R=reset  SPACE=pause  +/-=speed  X=dither  C=palette",
              color=(0.3,0.3,0.4))