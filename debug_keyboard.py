#!/usr/bin/env python3
"""
Debug keyboard handler threading issue
"""

import msvcrt
import threading
import time

class KeyboardTest:
    def __init__(self):
        self.running = True
        self.keyboard_running = True
        self.restart_requested = False
        self.keyboard_thread = None
    
    def start_keyboard_listener(self):
        """Start keyboard listener thread"""
        self.keyboard_thread = threading.Thread(target=self._keyboard_listener_windows, daemon=True)
        self.keyboard_thread.start()
        print("Keyboard listener started")
    
    def _keyboard_listener_windows(self):
        """Windows keyboard listener"""
        print("DEBUG: Keyboard listener thread starting")
        try:
            while self.running and self.keyboard_running:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    print(f"DEBUG: Key detected: {key} (hex: {key.hex()}, ord: {ord(key)})")
                    
                    if key == b'\x14' or ord(key) == 20:  # Ctrl+T
                        self.restart_requested = True
                        print("🔄 Ctrl+T detected - restart requested!")
                        
                time.sleep(0.05)
        except Exception as e:
            print(f"DEBUG: Exception in keyboard listener: {e}")
        finally:
            print("DEBUG: Keyboard listener thread exiting")
    
    def run(self):
        """Main test loop"""
        print("Starting keyboard test...")
        print("Press Ctrl+T to test restart, Ctrl+C to exit")
        
        self.start_keyboard_listener()
        
        try:
            while self.running:
                if self.restart_requested:
                    print("RESTART DETECTED!")
                    self.restart_requested = False
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
            self.running = False
            self.keyboard_running = False

if __name__ == "__main__":
    test = KeyboardTest()
    test.run()
