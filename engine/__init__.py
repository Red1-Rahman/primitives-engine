"""Engine package bootstrap utilities.

Ensures the project root is importable so sibling packages like
`scenes` and `games` can be imported consistently.
"""

import os
import sys


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
	sys.path.insert(0, _PROJECT_ROOT)

