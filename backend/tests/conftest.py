"""Pytest configuration. Adds backend to path so imports match backend layout."""
import sys
from pathlib import Path

# Add backend directory to path so we can use same imports as backend code
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
