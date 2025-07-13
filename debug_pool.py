#!/usr/bin/env python3
"""
Debug the connection pool issue.
"""
import os
import sys
import signal
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def debug_connection_pool():
    """Debug the connection pool get_connection method."""
    print("Debugging connection pool...")
    
    def timeout_handler(signum, frame):
        print("❌ Connection pool get_connection timed out!")
        sys.exit(1)
    
    # Set 15 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        from utils.db_connection_pool import DatabaseConnectionPool
        
        def dummy_conn():
            print("  Creating dummy connection")
            return "test_connection"
        
        print("Creating connection pool...")
        pool = DatabaseConnectionPool(dummy_conn, max_connections=2, timeout=1)
        print("✅ Connection pool created")
        
        print("Getting connection (this is where it hangs)...")
        print("  Calling pool.get_connection()...")
        with pool.get_connection() as conn:
            print(f"  Got connection: {conn}")
            assert conn == "test_connection"
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