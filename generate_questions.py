#!/usr/bin/env python3
"""
Root runner for AI-Powered Assessment Question Generator & Validator.
"""

import os
import sys

# Add src to python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from cli import run_cli

if __name__ == "__main__":
    run_cli()
