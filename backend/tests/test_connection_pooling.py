"""
Comprehensive test suite for database connection pooling.
Tests various scenarios to ensure pool stability in production.
"""

import unittest
import threading
import time
import random
from unittest.mock import Mock, patch, MagicMock
from queue import Queue, Empty

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_connection_pool import DatabaseConnectionPool
from utils.content_db_manager import ContentDatabaseManager


class MockConnection:
    """Mock database connection for testing."""
    def __init__(self, conn_id, should_fail=False):
        self.conn_id = conn_id
        self.closed = False
        self.should_fail = should_fail
        self.cursor_created = False
        
    def cursor(self):
        if self.closed:
            raise Exception("Connection is closed")
        if self.should_fail:
            raise Exception("Connection failed")
        self.cursor_created = True
        return MockCursor()
        
    def close(self):
        self.closed = True
        
    def rollback(self):
        if self.closed:
            raise Exception("Connection is closed")
            
    def ping(self, reconnect=False):
        if self.closed or self.should_fail:
            raise Exception("Connection lost")


class MockCursor:
    """Mock database cursor for testing."""
    def __init__(self):
        self.closed = False
        
    def execute(self, query):
        if self.closed:
            raise Exception("Cursor is closed")
        return True
        
    def fetchone(self):
        return {"result": 1}
        
    def close(self):
        self.closed = True


class TestConnectionPool(unittest.TestCase):
    """Test the DatabaseConnectionPool class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.conn_counter = 0
        
    def create_mock_connection(self, should_fail=False):
        """Create a mock connection."""
        self.conn_counter += 1
        return MockConnection(self.conn_counter, should_fail)
        
    def test_basic_pool_operations(self):
        """Test basic pool operations: create, get, return."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=3,
            timeout=1
        )
        
        # Get a connection
        with pool.get_connection() as conn:
            self.assertIsNotNone(conn)
            self.assertFalse(conn.closed)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            
        # Connection should be returned to pool
        self.assertEqual(pool.pool.qsize(), 1)
        
        # Get multiple connections
        conns = []
        for i in range(3):
            conn_context = pool.get_connection()
            conn = conn_context.__enter__()
            conns.append((conn_context, conn))
            
        # Pool should be empty
        self.assertEqual(pool.pool.qsize(), 0)
        
        # Return connections
        for conn_context, conn in conns:
            conn_context.__exit__(None, None, None)
            
        # All connections should be back in pool
        self.assertEqual(pool.pool.qsize(), 3)
        
        pool.close_all()
        
    def test_pool_max_connections_limit(self):
        """Test that pool respects max connections limit."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=2,
            timeout=0.5
        )
        
        # Get max connections
        conn1_ctx = pool.get_connection()
        conn1 = conn1_ctx.__enter__()
        conn2_ctx = pool.get_connection()
        conn2 = conn2_ctx.__enter__()
        
        # Try to get one more - should timeout
        start_time = time.time()
        with self.assertRaises(Empty):
            with pool.get_connection() as conn3:
                pass
                
        elapsed = time.time() - start_time
        self.assertGreater(elapsed, 0.4)  # Should have waited
        self.assertLess(elapsed, 1.0)  # But not too long
        
        # Return one connection
        conn1_ctx.__exit__(None, None, None)
        
        # Now we should be able to get a connection
        with pool.get_connection() as conn3:
            self.assertIsNotNone(conn3)
            
        conn2_ctx.__exit__(None, None, None)
        pool.close_all()
        
    def test_dead_connection_handling(self):
        """Test that dead connections are replaced."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=2,
            timeout=1
        )
        
        # Get a connection and break it
        with pool.get_connection() as conn:
            conn_id = conn.conn_id
            conn.should_fail = True
            
        # Next get should detect dead connection and create new one
        with pool.get_connection() as conn:
            self.assertNotEqual(conn.conn_id, conn_id)
            self.assertFalse(conn.should_fail)
            
        pool.close_all()
        
    def test_concurrent_access(self):
        """Test thread-safe concurrent access to pool."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=5,
            timeout=2
        )
        
        results = Queue()
        errors = Queue()
        
        def worker(worker_id):
            """Worker thread that uses connections."""
            try:
                for i in range(10):
                    with pool.get_connection() as conn:
                        # Simulate work
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        time.sleep(random.uniform(0.01, 0.05))
                        results.put(f"Worker {worker_id} iteration {i} success")
            except Exception as e:
                errors.put(f"Worker {worker_id} error: {str(e)}")
                
        # Start multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
            
        # Wait for all threads
        for t in threads:
            t.join()
            
        # Check results
        self.assertEqual(errors.qsize(), 0)
        self.assertEqual(results.qsize(), 100)  # 10 workers * 10 iterations
        
        pool.close_all()
        
    def test_connection_leak_prevention(self):
        """Test that connections are not leaked on errors."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=2,
            timeout=1
        )
        
        # Simulate error during connection use
        try:
            with pool.get_connection() as conn:
                raise Exception("Simulated error")
        except:
            pass
            
        # Connection should still be returned to pool
        time.sleep(0.1)  # Give time for cleanup
        self.assertEqual(pool.pool.qsize(), 1)
        
        # Pool should still be usable
        with pool.get_connection() as conn:
            self.assertIsNotNone(conn)
            
        pool.close_all()
        
    def test_pool_closure(self):
        """Test proper pool closure."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=3,
            timeout=1
        )
        
        # Create some connections
        with pool.get_connection() as conn:
            pass
        with pool.get_connection() as conn:
            pass
            
        # Close pool
        pool.close_all()
        self.assertTrue(pool._closed)
        
        # Should not be able to get connections
        with self.assertRaises(RuntimeError):
            with pool.get_connection() as conn:
                pass


class TestContentDatabaseManager(unittest.TestCase):
    """Test the ContentDatabaseManager class."""
    
    @patch('utils.content_db_manager.get_persistent_config')
    @patch('utils.content_db_manager.get_database_connector')
    def test_connection_retry_logic(self, mock_get_connector, mock_get_config):
        """Test automatic reconnection with exponential backoff."""
        # Mock config
        mock_config_manager = Mock()
        mock_config_manager.get_database_config.return_value = {
            'production_database_url': 'mysql://user:pass@host:3306/db',
            'database_type': 'mysql',
            'database_ssl': True
        }
        mock_get_config.return_value = mock_config_manager
        
        # First attempts fail, then succeed
        mock_get_connector.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            MockConnection(1)  # Success on third try
        ]
        
        manager = ContentDatabaseManager()
        
        # First attempt fails
        self.assertFalse(manager._ensure_connection())
        self.assertEqual(manager._connect_retry_delay, 2)  # Should double
        
        # Wait and try again
        time.sleep(0.1)
        manager._last_connect_attempt = 0  # Reset timer for test
        self.assertFalse(manager._ensure_connection())
        self.assertEqual(manager._connect_retry_delay, 4)  # Should double again
        
        # Third attempt succeeds
        manager._last_connect_attempt = 0  # Reset timer for test
        self.assertTrue(manager._ensure_connection())
        self.assertEqual(manager._connect_retry_delay, 1)  # Should reset
        
    @patch('utils.content_db_manager.get_persistent_config')
    def test_config_sanitization(self, mock_get_config):
        """Test that configuration values are sanitized."""
        # Mock config with whitespace
        mock_config_manager = Mock()
        mock_config_manager.get_database_config.return_value = {
            'production_database_url': '  mysql://user:pass@host:3306/db  ',
            'database_type': ' mysql ',
            'database_ssl': True
        }
        mock_get_config.return_value = mock_config_manager
        
        manager = ContentDatabaseManager()
        config, db_type = manager._load_database_config()
        
        # Check sanitization
        self.assertEqual(config['host'], 'host')  # No whitespace
        self.assertEqual(config['username'], 'user')  # No whitespace
        self.assertEqual(db_type, 'mysql')  # No whitespace
        
    def test_status_reporting(self):
        """Test connection status reporting."""
        manager = ContentDatabaseManager()
        
        # Initial status
        status = manager.get_connection_status()
        self.assertFalse(status['connected'])
        self.assertFalse(status['pool_active'])
        self.assertEqual(status['retry_delay'], 1)
        
        # After failed attempt
        manager._connect_retry_delay = 8
        manager._last_connect_attempt = time.time()
        status = manager.get_connection_status()
        self.assertEqual(status['retry_delay'], 8)
        self.assertIsNotNone(status['last_attempt'])


class TestProductionScenarios(unittest.TestCase):
    """Test scenarios that might occur in production."""
    
    def test_database_restart_recovery(self):
        """Test recovery when database is restarted."""
        # Create a connection that will fail after some uses
        fail_after = 5
        use_count = 0
        
        def create_connection():
            nonlocal use_count
            use_count += 1
            return MockConnection(use_count, should_fail=(use_count > fail_after))
            
        pool = DatabaseConnectionPool(
            create_connection_func=create_connection,
            max_connections=3,
            timeout=1
        )
        
        # Use connections successfully
        for i in range(5):
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                
        # Now connections start failing (simulating DB restart)
        # Pool should create new connections
        fail_after = 10  # Allow new connections to work
        
        for i in range(5):
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                
        pool.close_all()
        
    def test_long_running_queries(self):
        """Test pool behavior with long-running queries."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=2,
            timeout=2
        )
        
        def long_query():
            with pool.get_connection() as conn:
                time.sleep(1)  # Simulate long query
                return True
                
        # Run multiple long queries in parallel
        threads = []
        for i in range(4):
            t = threading.Thread(target=long_query)
            threads.append(t)
            t.start()
            
        # All should complete eventually
        for t in threads:
            t.join(timeout=5)
            self.assertFalse(t.is_alive())
            
        pool.close_all()
        
    def test_memory_leak_prevention(self):
        """Test that pool doesn't leak memory with connection cycling."""
        pool = DatabaseConnectionPool(
            create_connection_func=self.create_mock_connection,
            max_connections=5,
            timeout=1
        )
        
        initial_connections = len(pool.all_connections)
        
        # Simulate many connection uses
        for i in range(100):
            with pool.get_connection() as conn:
                if i % 10 == 0:
                    # Occasionally break connections
                    conn.should_fail = True
                    
        # Should not have more connections than max
        self.assertLessEqual(len(pool.all_connections), pool.max_connections)
        
        pool.close_all()


if __name__ == '__main__':
    unittest.main()