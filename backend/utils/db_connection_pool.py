"""
Database connection pooling for EQEmu database connections.
Maintains a pool of reusable connections to prevent connection exhaustion.
"""

import threading
import time
import logging
from queue import Queue, Empty
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Thread-safe database connection pool."""
    
    def __init__(self, create_connection_func, max_connections=5, timeout=30):
        """
        Initialize connection pool.
        
        Args:
            create_connection_func: Function that creates a new database connection
            max_connections: Maximum number of connections in the pool
            timeout: Connection timeout in seconds
        """
        self.create_connection = create_connection_func
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = Queue(maxsize=max_connections)
        self.all_connections = []
        self.lock = threading.Lock()
        self._closed = False
        
    def _create_new_connection(self):
        """Create a new connection and add it to tracking."""
        conn = self.create_connection()
        with self.lock:
            self.all_connections.append(conn)
        return conn
        
    def _is_connection_alive(self, conn):
        """Check if a connection is still alive."""
        try:
            # Different databases have different ways to check
            if hasattr(conn, 'ping'):
                # MySQL
                conn.ping(reconnect=False)
            else:
                # PostgreSQL/Generic - try a simple query
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return True
        except:
            return False
            
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Usage:
            with pool.get_connection() as conn:
                # Use connection
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM items")
        """
        if self._closed:
            raise RuntimeError("Connection pool is closed")
            
        conn = None
        try:
            # Try to get an existing connection from the pool
            try:
                conn = self.pool.get(timeout=0.1)
                # Check if connection is still alive
                if not self._is_connection_alive(conn):
                    logger.warning("Dead connection found in pool, creating new one")
                    try:
                        conn.close()
                    except:
                        pass
                    conn = self._create_new_connection()
            except Empty:
                # No connections available, create a new one if under limit
                with self.lock:
                    if len(self.all_connections) < self.max_connections:
                        conn = self._create_new_connection()
                    else:
                        # Wait for a connection to become available
                        conn = self.pool.get(timeout=self.timeout)
                        if not self._is_connection_alive(conn):
                            try:
                                conn.close()
                            except:
                                pass
                            conn = self._create_new_connection()
            
            # Yield the connection for use
            yield conn
            
        finally:
            # Return connection to pool
            if conn and not self._closed:
                try:
                    # Rollback any uncommitted transaction
                    conn.rollback()
                    self.pool.put(conn)
                except:
                    # Connection is broken, don't return to pool
                    logger.warning("Failed to return connection to pool")
                    try:
                        conn.close()
                    except:
                        pass
                        
    def close_all(self):
        """Close all connections in the pool."""
        self._closed = True
        
        # Close all connections
        with self.lock:
            # Empty the pool
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                except:
                    pass
                    
            # Close any connections that might be in use
            for conn in self.all_connections:
                try:
                    conn.close()
                except:
                    pass
                    
            self.all_connections.clear()


# Global connection pool instance
_connection_pool = None
_pool_lock = threading.Lock()


def get_connection_pool(create_connection_func, max_connections=5):
    """Get or create the global connection pool."""
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool is None:
            _connection_pool = DatabaseConnectionPool(
                create_connection_func,
                max_connections=max_connections
            )
    
    return _connection_pool


def close_connection_pool():
    """Close the global connection pool."""
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool:
            _connection_pool.close_all()
            _connection_pool = None