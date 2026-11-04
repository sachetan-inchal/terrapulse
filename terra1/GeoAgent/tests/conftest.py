"""Pytest configuration and global path resolution for black-box test suites."""

import sys
from pathlib import Path

# GeoAgent directory (where environmental and geoagent live)
GEOAGENT_DIR = Path(__file__).resolve().parent.parent
# Terrapulse root directory (where backend lives)
TERRAPULSE_ROOT = GEOAGENT_DIR.parent.parent

for p in (str(GEOAGENT_DIR), str(TERRAPULSE_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

