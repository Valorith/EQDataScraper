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
    
    def __init__(self, create_connection_func, max_connections=10, timeout=2):
        """
        Initialize connection pool with reduced limits to prevent hanging.
        
        Args:
            create_connection_func: Function that creates a new database connection
            max_connections: Maximum number of connections in the pool (reduced from 20)
            timeout: Connection timeout in seconds (reduced from 5)
        """
        self.create_connection = create_connection_func
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = Queue(maxsize=max_connections)
        self.all_connections = []
        self.lock = threading.Lock()
        self._closed = False
        
    def _create_new_connection(self):
        """Create a new connection with simplified timeout protection."""
        try:
            conn = self.create_connection()
            
            with self.lock:
                self.all_connections.append(conn)
            logger.info(f"Created new database connection (total: {len(self.all_connections)})")
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise
        
    def _is_connection_alive(self, conn):
        """Check if a connection is still alive."""
        try:
            # Handle test/dummy connections
            if isinstance(conn, str):
                return True  # Dummy connections are always "alive"
                
            # Different databases have different ways to check
            if hasattr(conn, 'ping'):
                # MySQL
                conn.ping(reconnect=False)
            elif hasattr(conn, 'cursor'):
                # PostgreSQL/Generic - try a simple query
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            else:
                # Unknown connection type, assume it's alive
                return True
                
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
                        # Wait for a connection to become available with shorter timeout
                        logger.warning(f"Connection pool full ({self.max_connections} connections), waiting up to {self.timeout}s...")
                        try:
                            conn = self.pool.get(timeout=self.timeout)
                            if not self._is_connection_alive(conn):
                                logger.warning("Retrieved dead connection from pool, creating new one")
                                try:
                                    conn.close()
                                except:
                                    pass
                                # Try to create a new connection even if pool is full
                                conn = self._create_new_connection()
                        except Empty:
                            # Pool is full and no connections available - this can cause hanging
                            logger.error(f"Connection pool exhausted! No connections available after {self.timeout}s timeout")
                            raise Exception("Database connection pool exhausted - all connections in use")
            
            # Yield the connection for use
            yield conn
            
        finally:
            # Return connection to pool
            if conn and not self._closed:
                try:
                    # Only rollback if connection has this method
                    if hasattr(conn, 'rollback'):
                        conn.rollback()
                    self.pool.put(conn)
                except:
                    # Connection is broken, don't return to pool
                    logger.warning("Failed to return connection to pool")
                    try:
                        if hasattr(conn, 'close'):
                            conn.close()
                    except:
                        pass
                        
    def get_pool_stats(self):
        """Get statistics about the connection pool."""
        with self.lock:
            return {
                'total_connections': len(self.all_connections),
                'available_connections': self.pool.qsize(),
                'in_use_connections': len(self.all_connections) - self.pool.qsize(),
                'max_connections': self.max_connections,
                'is_closed': self._closed
            }
    
    def close_all(self):
        """Close all connections in the pool."""
        self._closed = True
        
        # Close all connections
        with self.lock:
            # Empty the pool
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    if hasattr(conn, 'close'):
                        conn.close()
                except:
                    pass
                    
            # Close any connections that might be in use
            for conn in self.all_connections:
                try:
                    if hasattr(conn, 'close'):
                        conn.close()
                except:
                    pass
                    
            self.all_connections.clear()


# Global connection pool instance
_connection_pool = None
_pool_lock = threading.Lock()


def get_connection_pool(create_connection_func, max_connections=20):
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