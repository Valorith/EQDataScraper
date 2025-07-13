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
            
            # Track the query if tracking is enabled - use direct tracking to avoid circular imports
            if self._track_queries:
                try:
                    self._track_query_direct(query, execution_time)
                except Exception as e:
                    logger.error(f"Error tracking query: {e}")
            
            return result
            
        except Exception as e:
            # Still track failed queries
            execution_time = (time.time() - start_time) * 1000
            if self._track_queries:
                try:
                    self._track_query_direct(query, execution_time)
                    self._log_error_direct(f"Database query failed: {str(e)}")
                except Exception:
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
                    self._track_query_direct(f"{query} (batch of {len(params_list)})", execution_time)
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            if self._track_queries:
                try:
                    self._track_query_direct(f"{query} (batch)", execution_time)
                    self._log_error_direct(f"Database batch query failed: {str(e)}")
                except Exception:
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
    
    def _track_query_direct(self, query, execution_time):
        """Track query directly without importing admin routes to avoid circular dependency."""
        try:
            # Import the specific tracking function without circular dependency
            import sys
            import importlib.util
            
            # Check if admin module is already loaded to avoid circular import
            if 'routes.admin' in sys.modules:
                # Use the already loaded admin module
                admin_module = sys.modules['routes.admin']
                if hasattr(admin_module, 'track_database_query'):
                    # Parse query to extract info
                    table_name = self._extract_table_name(query)
                    query_type = self._get_query_type(query)
                    
                    # Track using the existing function
                    admin_module.track_database_query(
                        query=query,
                        execution_time=execution_time,
                        query_type=query_type,
                        table_name=table_name,
                        source_endpoint="Database Operation"
                    )
                    return
            
            # If admin not loaded, skip tracking to avoid circular import
            logger.debug("Admin module not loaded, skipping query tracking to avoid circular import")
            
        except Exception as e:
            logger.error(f"Direct query tracking failed: {e}")
    
    def _log_error_direct(self, error_message):
        """Log error directly without circular dependency."""
        logger.error(error_message)
    
    def _extract_table_name(self, query):
        """Extract table name from SQL query."""
        try:
            # Simple regex to extract table names from common SQL patterns
            import re
            
            query_upper = query.upper().strip()
            
            # Handle different SQL patterns
            if query_upper.startswith('SELECT'):
                # Look for FROM clause
                match = re.search(r'FROM\s+([`"]?)(\w+)\1', query_upper)
                if match:
                    return match.group(2).lower()
            elif query_upper.startswith('INSERT'):
                # Look for INSERT INTO
                match = re.search(r'INSERT\s+INTO\s+([`"]?)(\w+)\1', query_upper)
                if match:
                    return match.group(2).lower()
            elif query_upper.startswith('UPDATE'):
                # Look for UPDATE table
                match = re.search(r'UPDATE\s+([`"]?)(\w+)\1', query_upper)
                if match:
                    return match.group(2).lower()
            elif query_upper.startswith('DELETE'):
                # Look for DELETE FROM
                match = re.search(r'DELETE\s+FROM\s+([`"]?)(\w+)\1', query_upper)
                if match:
                    return match.group(2).lower()
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _get_query_type(self, query):
        """Extract query type from SQL query."""
        try:
            query_upper = query.upper().strip()
            
            if query_upper.startswith('SELECT'):
                return 'SELECT'
            elif query_upper.startswith('INSERT'):
                return 'INSERT'
            elif query_upper.startswith('UPDATE'):
                return 'UPDATE'
            elif query_upper.startswith('DELETE'):
                return 'DELETE'
            else:
                return 'OTHER'
                
        except Exception:
            return 'OTHER'


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