"""
Pytest configuration for miningtoolbox-mcp tests.

This file automatically adds the src/ directory to the Python path,
enabling tests to import the miningtoolbox module without manual PYTHONPATH setup.
"""
import sys
import os

# Add src/ to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
