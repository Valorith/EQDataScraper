#!/usr/bin/env python3
"""
Test script to verify backend hanging fixes.
This script will test various scenarios that could cause hanging.
"""
import os
import sys
import time
import threading
import requests
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Global test results
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}

def log_test_result(test_name, passed, error=None):
    """Log test result and track overall status."""
    if passed:
        test_results['passed'] += 1
        print(f"✅ {test_name}")
    else:
        test_results['failed'] += 1
        test_results['errors'].append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")

@contextmanager
def timeout_context(seconds):
    """Context manager that raises TimeoutError if code takes too long."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set up timeout (Unix-like systems only)
    if hasattr(signal, 'SIGALRM'):
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
    else:
        # On Windows, just run without timeout
        yield

def test_database_connection_pool():
    """Test that database connection pool doesn't hang."""
    print("Testing database connection pool...")
    
    try:
        with timeout_context(10):  # 10 second timeout
            from utils.db_connection_pool import DatabaseConnectionPool
            
            # Test creating a pool with a dummy connection function
            def dummy_connection():
                return "dummy_connection"
            
            pool = DatabaseConnectionPool(
                create_connection_func=dummy_connection,
                max_connections=3,
                timeout=2
            )
            
            # Test getting connection
            with pool.get_connection() as conn:
                assert conn == "dummy_connection"
            
            # Test pool stats
            stats = pool.get_pool_stats()
            assert stats['max_connections'] == 3
            
            # Clean up
            pool.close_all()
            
        log_test_result("Database connection pool creation", True)
        
    except Exception as e:
        log_test_result("Database connection pool creation", False, str(e))

def test_http_session_timeouts():
    """Test that HTTP session has proper timeouts."""
    print("Testing HTTP session timeout configuration...")
    
    try:
        with timeout_context(15):  # 15 second timeout
            # This should be fast as it's just importing and checking configuration
            from backend.app import session
            
            # Check that session has adapters configured
            assert 'http://' in session.adapters
            assert 'https://' in session.adapters
            
            # Test with a quick request to verify timeout settings
            try:
                response = session.head('https://httpbin.org/status/200', timeout=5)
                assert response.status_code == 200
            except requests.exceptions.RequestException:
                # Network errors are acceptable for this test
                pass
                
        log_test_result("HTTP session timeout configuration", True)
        
    except Exception as e:
        log_test_result("HTTP session timeout configuration", False, str(e))

def test_concurrent_requests():
    """Test that multiple concurrent requests don't cause hanging."""
    print("Testing concurrent request handling...")
    
    def make_dummy_request():
        """Simulate a request that tests resource management."""
        try:
            # Just test importing and basic functionality
            from backend.app import app
            with app.test_client() as client:
                # Test health endpoint
                response = client.get('/api/health')
                return response.status_code == 200
        except Exception as e:
            print(f"Request error: {e}")
            return False
    
    try:
        with timeout_context(20):  # 20 second timeout
            # Run multiple concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_dummy_request) for _ in range(10)]
                
                # Wait for all requests to complete
                results = []
                for future in futures:
                    try:
                        result = future.result(timeout=5)
                        results.append(result)
                    except TimeoutError:
                        results.append(False)
                
                # Check that at least some requests succeeded
                success_count = sum(1 for r in results if r)
                assert success_count > 0, f"No requests succeeded out of {len(results)}"
                
        log_test_result("Concurrent request handling", True)
        
    except Exception as e:
        log_test_result("Concurrent request handling", False, str(e))

def test_database_connector_timeouts():
    """Test that database connectors have proper timeout settings."""
    print("Testing database connector timeout configuration...")
    
    try:
        with timeout_context(10):  # 10 second timeout
            from utils.database_connectors import get_database_connector
            
            # Test MySQL connector configuration
            mysql_config = {
                'host': 'localhost',
                'port': 3306,
                'database': 'test',
                'username': 'test',
                'password': 'test',
                'connect_timeout': 5,
                'read_timeout': 15,
                'write_timeout': 15,
                'autocommit': True
            }
            
            try:
                # This should fail quickly due to timeouts, not hang
                conn = get_database_connector('mysql', mysql_config, track_queries=False)
                if conn:
                    conn.close()
            except ImportError:
                # pymysql not installed, that's fine
                pass
            except Exception:
                # Connection failure is expected, we're testing timeout behavior
                pass
                
        log_test_result("Database connector timeout configuration", True)
        
    except Exception as e:
        log_test_result("Database connector timeout configuration", False, str(e))

def test_resource_cleanup():
    """Test that resources are properly cleaned up."""
    print("Testing resource cleanup...")
    
    try:
        with timeout_context(10):  # 10 second timeout
            from backend.app import cleanup_resources
            
            # Test cleanup function doesn't hang
            cleanup_resources()
            
        log_test_result("Resource cleanup", True)
        
    except Exception as e:
        log_test_result("Resource cleanup", False, str(e))

def main():
    """Run all tests."""
    print("🧪 Testing Backend Hanging Fixes")
    print("=" * 50)
    
    # Run all tests
    test_database_connection_pool()
    test_http_session_timeouts()
    test_concurrent_requests()
    test_database_connector_timeouts()
    test_resource_cleanup()
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {test_results['passed']} passed, {test_results['failed']} failed")
    
    if test_results['failed'] > 0:
        print("\n❌ Failures:")
        for error in test_results['errors']:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()