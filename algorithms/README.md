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
