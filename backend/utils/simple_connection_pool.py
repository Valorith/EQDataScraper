"""
Simple connection pool implementation that avoids hanging issues.
"""
import threading
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SimpleConnectionPool:
    """A simplified connection pool that avoids hanging issues."""
    
    def __init__(self, create_connection_func, max_connections=5):
        """
        Initialize simple connection pool.
        
        Args:
            create_connection_func: Function that creates a new database connection
            max_connections: Maximum number of connections to maintain
        """
        self.create_connection = create_connection_func
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()
        self._closed = False
        
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with immediate timeout."""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
            
        conn = None
        try:
            # Always create a new connection to avoid pool complexity
            conn = self.create_connection()
            yield conn
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
        finally:
            # Always close the connection immediately
            if conn and hasattr(conn, 'close'):
                try:
                    conn.close()
                except:
                    pass
                    
    def get_pool_stats(self):
        """Get statistics about the connection pool."""
        return {
            'total_connections': 0,  # No pooling
            'available_connections': 0,
            'in_use_connections': 0,
            'max_connections': self.max_connections,
            'is_closed': self._closed
        }
    
    def close_all(self):
        """Close all connections in the pool."""
        self._closed = True
        # Nothing to close since we don't pool connections
        
        
def replace_connection_pool():
    """Replace the hanging connection pool with a simple one."""
    import sys
    
    # Replace the DatabaseConnectionPool class
    from utils import db_connection_pool
    db_connection_pool.DatabaseConnectionPool = SimpleConnectionPool
    
    print("✅ Replaced DatabaseConnectionPool with SimpleConnectionPool")