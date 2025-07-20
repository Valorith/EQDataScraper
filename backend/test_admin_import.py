#!/usr/bin/env python3
"""Test if admin module can be imported successfully."""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import admin module...")
    from routes.admin import admin_bp, system_metrics
    print("✅ Successfully imported admin_bp")
    print(f"✅ system_metrics type: {type(system_metrics)}")
    print(f"✅ system_metrics keys: {list(system_metrics.keys())}")
except Exception as e:
    print(f"❌ Failed to import admin module: {e}")
    import traceback
    traceback.print_exc()