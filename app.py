"""
Energy-Aware Dynamic Task Scheduling Framework for Big Data Processing
Root Entrypoint Launcher - Delegates execution to frontend/app.py.
"""

import os
import sys

# Ensure frontend and backend are in Python path
_root_dir = os.path.dirname(os.path.abspath(__file__))
_frontend_dir = os.path.join(_root_dir, "frontend")
_backend_dir = os.path.join(_root_dir, "backend")

for _p in (_frontend_dir, _backend_dir, _root_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load and execute frontend application
_target_app = os.path.join(_frontend_dir, "app.py")
if os.path.exists(_target_app):
    with open(_target_app, "r", encoding="utf-8") as _f:
        _code = _f.read()
    exec(compile(_code, _target_app, "exec"), globals())
else:
    raise FileNotFoundError(f"Frontend entrypoint not found at: {_target_app}")
