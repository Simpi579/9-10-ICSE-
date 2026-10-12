#!/usr/bin/env python3
"""
Root entry point for the AI-Powered Answer Evaluation Web Application.
"""

import os
import sys

# Ensure src is on Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ui.server import start_server

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    start_server(port=port)
