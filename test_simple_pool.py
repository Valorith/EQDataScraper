#!/usr/bin/env python3
"""
Test the simple connection pool.
"""
import os
import sys
import signal
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_simple_pool():
    """Test the simple connection pool."""
    print("Testing simple connection pool...")
    
    def timeout_handler(signum, frame):
        print("❌ Simple connection pool timed out!")
        sys.exit(1)
    
    # Set 10 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)
    
    try:
        from utils.simple_connection_pool import SimpleConnectionPool
        
        call_count = 0
        def dummy_conn():
            nonlocal call_count
            call_count += 1
            print(f"  Creating dummy connection #{call_count}")
            return f"test_connection_{call_count}"
        
        print("Creating simple connection pool...")
        pool = SimpleConnectionPool(dummy_conn, max_connections=2)
        print("✅ Simple connection pool created")
        
        print("Getting connection...")
        with pool.get_connection() as conn:
            print(f"  Got connection: {conn}")
            assert conn == "test_connection_1"
            print("  Working with connection...")
            time.sleep(0.1)
        print("✅ Connection retrieved successfully")
        
        print("Getting another connection...")
        with pool.get_connection() as conn:
            print(f"  Got connection: {conn}")
            assert conn == "test_connection_2"
        print("✅ Second connection retrieved successfully")
        
        # Cancel timeout
        signal.alarm(0)
        print("✅ All simple pool tests passed")
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_simple_pool()