#!/usr/bin/env python3
"""
Test script to verify keyboard handling for Ctrl+R
"""

import msvcrt
import time
import sys

def test_keyboard_handler():
    """Test keyboard handler for Windows"""
    print("Testing keyboard handler for Windows...")
    print("Press any key to see its code, or Ctrl+R to test restart")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch()
                print(f"Key pressed: {key} (hex: {key.hex()}, dec: {ord(key)})")
                
                if key == b'\x12':  # Ctrl+R
                    print("✅ Ctrl+R detected correctly!")
                elif key == b'\x03':  # Ctrl+C
                    print("Ctrl+C detected - exiting")
                    break
                    
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting due to keyboard interrupt")

if __name__ == "__main__":
    test_keyboard_handler()
