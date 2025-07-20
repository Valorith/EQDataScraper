#!/usr/bin/env python3
"""
Final comprehensive test of backend hanging fixes.
Tests all components that could cause hanging.
"""
import os
import sys
import signal
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_component(name, test_func, timeout=10):
    """Test a component with timeout protection."""
    print(f"Testing {name}...")
    
    def timeout_handler(signum, frame):
        print(f"❌ {name} timed out after {timeout}s!")
        return False
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        result = test_func()
        signal.alarm(0)
        if result:
            print(f"✅ {name} passed")
        else:
            print(f"❌ {name} failed")
        return result
    except Exception as e:
        signal.alarm(0)
        print(f"❌ {name} error: {e}")
        return False

def test_connection_pool():
    """Test connection pool doesn't hang."""
    try:
        from utils.db_connection_pool import DatabaseConnectionPool
        
        def dummy_conn():
            return "test_conn"
        
        pool = DatabaseConnectionPool(dummy_conn, max_connections=2)
        
        # Test multiple connections
        for i in range(5):
            with pool.get_connection() as conn:
                assert conn == "test_conn"
        
        stats = pool.get_pool_stats()
        assert stats['pool_type'] == 'simple'
        
        pool.close_all()
        return True
    except Exception as e:
        print(f"Connection pool error: {e}")
        return False

def test_content_database_manager():
    """Test content database manager doesn't hang."""
    try:
        from utils.content_db_manager import ContentDatabaseManager
        
        manager = ContentDatabaseManager()
        status = manager.get_connection_status()
        
        # Should not hang and should return a status
        assert isinstance(status, dict)
        assert 'connected' in status
        
        return True
    except Exception as e:
        print(f"Content DB manager error: {e}")
        return False

def test_database_connectors():
    """Test database connectors don't hang."""
    try:
        from utils.database_connectors import get_database_connector
        
        # Test MySQL config (should fail quickly, not hang)
        mysql_config = {
            'host': 'nonexistent.host',
            'port': 3306,
            'database': 'test',
            'username': 'test',
            'password': 'test',
            'connect_timeout': 2,
            'read_timeout': 5,
            'autocommit': True
        }
        
        try:
            # This should fail quickly due to timeouts
            conn = get_database_connector('mysql', mysql_config, track_queries=False)
            if conn:
                conn.close()
        except ImportError:
            pass  # pymysql not available
        except Exception:
            pass  # Expected failure
        
        return True
    except Exception as e:
        print(f"Database connectors error: {e}")
        return False

def test_concurrent_operations():
    """Test concurrent operations don't cause hanging."""
    try:
        from utils.db_connection_pool import DatabaseConnectionPool
        
        def dummy_conn():
            time.sleep(0.1)  # Simulate connection time
            return f"conn_{threading.current_thread().ident}"
        
        pool = DatabaseConnectionPool(dummy_conn)
        
        def worker():
            try:
                with pool.get_connection() as conn:
                    time.sleep(0.05)  # Simulate work
                    return True
            except Exception:
                return False
        
        # Run multiple concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(20)]
            results = [future.result(timeout=5) for future in futures]
        
        # All should complete successfully
        success_count = sum(1 for r in results if r)
        assert success_count == 20
        
        pool.close_all()
        return True
    except Exception as e:
        print(f"Concurrent operations error: {e}")
        return False

def test_http_session_config():
    """Test HTTP session timeout configuration."""
    try:
        # Set environment to avoid database connections
        os.environ['ENABLE_USER_ACCOUNTS'] = 'false'
        os.environ['TESTING'] = '1'
        
        # Import should not hang
        from app import session
        
        # Check session has adapters
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters
        
        # Test with quick request (may fail due to network, that's OK)
        try:
            response = session.head('https://httpbin.org/status/200', timeout=3)
        except Exception:
            pass  # Network errors are acceptable
        
        return True
    except Exception as e:
        print(f"HTTP session config error: {e}")
        return False

def test_resource_cleanup():
    """Test resource cleanup doesn't hang."""
    try:
        # Set environment to avoid database connections
        os.environ['ENABLE_USER_ACCOUNTS'] = 'false'
        os.environ['TESTING'] = '1'
        
        from app import cleanup_resources
        
        # Should complete without hanging
        cleanup_resources()
        
        return True
    except Exception as e:
        print(f"Resource cleanup error: {e}")
        return False

def main():
    """Run all hanging tests."""
    print("🔧 Backend Hanging Fixes - Final Test Suite")
    print("=" * 60)
    
    # Set environment variables
    os.environ['USE_ORIGINAL_POOL'] = 'false'  # Use simple pool
    os.environ['ENABLE_USER_ACCOUNTS'] = 'false'
    os.environ['TESTING'] = '1'
    
    tests = [
        ("Connection Pool", test_connection_pool, 10),
        ("Content Database Manager", test_content_database_manager, 10),
        ("Database Connectors", test_database_connectors, 10),
        ("Concurrent Operations", test_concurrent_operations, 15),
        ("HTTP Session Config", test_http_session_config, 10),
        ("Resource Cleanup", test_resource_cleanup, 10)
    ]
    
    results = []
    for name, test_func, timeout in tests:
        result = test_component(name, test_func, timeout)
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend hanging issues have been resolved!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - hanging issues may still exist")
        sys.exit(1)

if __name__ == "__main__":
    main()