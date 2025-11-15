#!/usr/bin/env python3
"""Test script to verify imports are working"""

import os
import sys

# Add 05_src to path
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_05_src_dir = os.path.abspath(os.path.join(_current_file_dir, '..'))
if _05_src_dir not in sys.path:
    sys.path.insert(0, _05_src_dir)

print(f"Added to path: {_05_src_dir}")
print(f"Logger exists: {os.path.exists(os.path.join(_05_src_dir, 'utils/logger.py'))}")

try:
    from utils.logger import get_logger
    print("✓ Successfully imported utils.logger")
except ImportError as e:
    print(f"✗ Failed to import utils.logger: {e}")
    print(f"sys.path: {sys.path[:5]}")

try:
    # Test importing chat_engine
    sys.path.insert(0, os.path.join(_current_file_dir, 'src'))
    from src.core.chat_engine import ChatEngine
    print("✓ Successfully imported ChatEngine")
except ImportError as e:
    print(f"✗ Failed to import ChatEngine: {e}")
    import traceback
    traceback.print_exc()

