#!/usr/bin/env python3
"""
Simple test to check what key code Ctrl+T produces
"""

import msvcrt
import time

print("Testing Ctrl+T key detection...")
print("Press Ctrl+T to test, or Ctrl+C to exit")

try:
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            print(f"Key pressed: {key} (hex: {key.hex()}, ord: {ord(key)})")
            
            if key == b'\x14':  # Ctrl+T
                print("✅ Ctrl+T detected using b'\\x14'!")
            elif ord(key) == 20:  # Ctrl+T alternative
                print("✅ Ctrl+T detected using ord(key) == 20!")
            elif key == b'\x03':  # Ctrl+C
                print("Exiting...")
                break
                
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting due to keyboard interrupt")
