"""Import the local gsconfig tree, never a pip-installed copy."""

import sys
from pathlib import Path

# WHY: a pip-installed gsconfig on the runner would otherwise shadow the tree under test.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
