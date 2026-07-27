"""Test configuration for value-dividend-screener."""

import sys
from pathlib import Path

# Add scripts directory to path so modules import by bare name
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
