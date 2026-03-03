# [dda.py](dda.py)

### problem:   
Typical DDA algorithms use floor(x + 0.5) for rounding pixel coordinates, which is only correct for positive values. 
For negative values, this formula applies asymmetrical rounding, so that -0.5 gets rounded to 0 instead of -1 
causing lines drawn in the third and fourth quadrants to be plotted with a slight positional bias relative to their mirrored counterparts in the positive quadrants   

### solution:   
round_half_away_from_zero, in place of the standard floor(x + 0.5) formula. 
The correction function `ceil(x - 0.5)` works correctly for negative values.

# [bresenham](bresenham.py)   

### Note:   
the implementation is 2d only (for now)   

# [midpoint circle](midpoint_circle.py)

### Note:
the implementation handles integer and non-integer radii with different initial decision parameters.   

for int:   
p = 1 - r   

for non-int:   
p = 5/4 - r   

# [2D Rotation](2d_rotation.py)

### description:   
Rotates a list of (x, y) points by a given angle (degrees), supporting both clockwise and counter-clockwise directions. Returns the transformed coordinates alongside a step-by-step table showing the calculation for each point.

# [2D Translation](2d_translation.py)

### Note:   
it has translation function for both points and circles

# [2D Scaling](2d_scaling.py)

### Note:
Scales a list of (x, y) points by factors Sx and Sy. Includes a separate function for scaling circles, where the radius scales uniformly with Sx.

# [2D Reflection](2d_reflection.py)

### Note:
Reflects a list of (x, y) points across a given axis. Supports five axes: x-axis, y-axis, origin, y=x, and y=−x.

# [2D Shear](2d_shear.py)

### Note:    
Shears a list of (x, y) points using horizontal (Shx) and vertical (Shy) shear factors. Both axes can be sheared simultaneously or independently.

# [Line Clipping](line_clipping.py)    
learned today at theory class (03/03/2026) :)

### Note:    
its uses Cohen-Sutherland's algorithm    
It clips a line to a rectangular viewport by assigning each endpoint a 4-bit region code (TBRL — Top, Bottom, Right, Left), then repeatedly clips until the line is either fully inside or fully rejected.
**The 4-bit region code (TBRL)**

```
bit 4 = Top    (y > ymax)
bit 3 = Bottom (y < ymin)
bit 2 = Right  (x > xmax)
bit 1 = Left   (x < xmin)
```
A point inside the viewport has code `0000`.

**The 3x3 grid regions**
```
1001 | 1000 | 1010
─────┼──────┼─────
0001 | 0000 | 0010
─────┼──────┼─────
0101 | 0100 | 0110
```

**Three outcomes per iteration**
- Both codes `0000` → **accept**, line is fully inside
- `code1 & code2 != 0` → **reject**, line is fully outside
- Otherwise → **clip** at the boundary where the outside point lies

**The intersection math**
For a line from (x1,y1) to (x2,y2), slope `m = dy/dx`:
- Clip left: `x = xmin`, `y = y1 + m(xmin - x1)`
- Clip right: `x = xmax`, `y = y1 + m(xmax - x1)`
- Clip bottom: `y = ymin`, `x = x1 + (ymin - y1)/m`
- Clip top: `y = ymax`, `x = x1 + (ymax - y1)/m`
