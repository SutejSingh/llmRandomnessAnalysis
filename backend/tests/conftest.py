"""Pytest configuration. Adds backend and tests root to path so imports match backend layout."""
import sys
from pathlib import Path

# Add backend directory (parent of tests/) so that "from stats import ...", "from analysis_service import ..." work
tests_dir = Path(__file__).resolve().parent
backend_dir = tests_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))
