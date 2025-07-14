#!/usr/bin/env python3
"""
Debug the connection pool issue with detailed logging.
"""
import os
import sys
import logging
import signal
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def debug_connection_pool():
    """Debug the connection pool get_connection method."""
    print("Debugging connection pool with detailed logging...")
    
    def timeout_handler(signum, frame):
        print("❌ Connection pool get_connection timed out!")
        sys.exit(1)
    
    # Set 15 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        from utils.db_connection_pool import DatabaseConnectionPool
        
        call_count = 0
        def dummy_conn():
            nonlocal call_count
            call_count += 1
            print(f"  Creating dummy connection #{call_count}")
            return f"test_connection_{call_count}"
        
        print("Creating connection pool...")
        pool = DatabaseConnectionPool(dummy_conn, max_connections=2, timeout=1)
        print("✅ Connection pool created")
        
        print("Getting connection (this is where it hangs)...")
        print("  Calling pool.get_connection()...")
        
        # Try the context manager step by step
        print("  Entering context manager...")
        context = pool.get_connection()
        print("  Context manager created")
        
        print("  Calling __enter__()...")
        conn = context.__enter__()
        print(f"  Got connection from __enter__(): {conn}")
        
        # Simulate some work
        print("  Simulating work with connection...")
        time.sleep(0.1)
        
        print("  Calling __exit__()...")
        context.__exit__(None, None, None)
        print("  __exit__() completed")
        
        print("✅ Connection retrieved successfully")
        
        # Cancel timeout
        signal.alarm(0)
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    debug_connection_pool()