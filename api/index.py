"""
Vercel Serverless Entrypoint for Energy-Aware Task Scheduling Framework
Exposes FastAPI ASGI app as a serverless handler for Vercel deployment.
"""

import sys
import os

# Add root and backend directories to sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, ".."))
_backend_dir = os.path.join(_root_dir, "backend")

for _p in (_root_dir, _backend_dir, _current_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import the FastAPI application
from backend.main import app

# Vercel ASGI handler
handler = app
