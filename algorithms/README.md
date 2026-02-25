# [dda.py](dda.py)

### problem:   
Typical DDA algorithms use floor(x + 0.5) for rounding pixel coordinates, which is only correct for positive values. 
For negative values, this formula applies asymmetrical rounding, so that -0.5 gets rounded to 0 instead of -1 
causing lines drawn in the third and fourth quadrants to be plotted with a slight positional bias relative to their mirrored counterparts in the positive quadrants   

### solution:   
round_half_away_from_zero, in place of the standard floor(x + 0.5) formula. 
The correction function `ceil(x - 0.5)` works correctly for negative values.
