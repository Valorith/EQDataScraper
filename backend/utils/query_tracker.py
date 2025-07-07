"""
Database query tracking wrapper for monitoring query performance.
"""

import time
import logging

logger = logging.getLogger(__name__)


class TrackedCursor:
    """Wrapper for database cursor that tracks query execution."""
    
    def __init__(self, cursor, db_type='postgresql'):
        self.cursor = cursor
        self.db_type = db_type
        self._track_queries = True
        
    def execute(self, query, params=None):
        """Execute query and track metrics."""
        start_time = time.time()
        
        try:
            if params:
                result = self.cursor.execute(query, params)
            else:
                result = self.cursor.execute(query)
            
            # Calculate execution time in milliseconds
            execution_time = (time.time() - start_time) * 1000
            
            # Track the query if tracking is enabled
            if self._track_queries:
                try:
                    from routes.admin import track_database_query
                    track_database_query(query, execution_time)
                except ImportError:
                    pass  # Admin routes not available
                except Exception as e:
                    logger.error(f"Error tracking query: {e}")
            
            return result
            
        except Exception as e:
            # Still track failed queries
            execution_time = (time.time() - start_time) * 1000
            if self._track_queries:
                try:
                    from routes.admin import track_database_query, log_system_error
                    track_database_query(query, execution_time)
                    log_system_error(f"Database query failed: {str(e)}", "Database")
                except ImportError:
                    pass
            raise
    
    def executemany(self, query, params_list):
        """Execute many queries and track metrics."""
        start_time = time.time()
        
        try:
            result = self.cursor.executemany(query, params_list)
            
            # Calculate execution time in milliseconds
            execution_time = (time.time() - start_time) * 1000
            
            # Track the query if tracking is enabled
            if self._track_queries:
                try:
                    from routes.admin import track_database_query
                    track_database_query(f"{query} (batch of {len(params_list)})", execution_time)
                except ImportError:
                    pass
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            if self._track_queries:
                try:
                    from routes.admin import track_database_query, log_system_error
                    track_database_query(f"{query} (batch)", execution_time)
                    log_system_error(f"Database batch query failed: {str(e)}", "Database")
                except ImportError:
                    pass
            raise
    
    def fetchone(self):
        """Fetch one row."""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all rows."""
        return self.cursor.fetchall()
    
    def fetchmany(self, size=None):
        """Fetch many rows."""
        if size:
            return self.cursor.fetchmany(size)
        return self.cursor.fetchmany()
    
    def close(self):
        """Close cursor."""
        return self.cursor.close()
    
    @property
    def rowcount(self):
        """Get row count."""
        return self.cursor.rowcount
    
    @property
    def description(self):
        """Get cursor description."""
        return self.cursor.description
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class TrackedConnection:
    """Wrapper for database connection that provides tracked cursors."""
    
    def __init__(self, connection, db_type='postgresql'):
        self.connection = connection
        self.db_type = db_type
        self._track_queries = True
        
    def cursor(self):
        """Get a tracked cursor."""
        original_cursor = self.connection.cursor()
        return TrackedCursor(original_cursor, self.db_type)
    
    def commit(self):
        """Commit transaction."""
        return self.connection.commit()
    
    def rollback(self):
        """Rollback transaction."""
        return self.connection.rollback()
    
    def close(self):
        """Close connection."""
        return self.connection.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_tracked_connection(connection, db_type='postgresql'):
    """Create a tracked connection wrapper."""
    return TrackedConnection(connection, db_type)