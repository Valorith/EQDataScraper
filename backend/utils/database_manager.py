"""
Database Manager with automatic reconnection and monitoring.

This module provides a centralized database manager that:
- Monitors database connections with 30-second health checks
- Automatically attempts reconnection if disconnected
- Loads configuration from environment variables when needed
- Provides status information for the Database Diagnostics modal
- Prevents race conditions by starting timer after app initialization
"""

import time
import logging
import threading
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from utils.content_db_manager import get_content_db_manager
from utils.persistent_config import get_persistent_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database manager with automatic reconnection and monitoring."""
    
    def __init__(self):
        """Initialize the database manager."""
        self._timer = None
        self._timer_lock = threading.Lock()
        self._running = False
        self._check_interval = 30  # 30 seconds
        self._start_time = None
        self._next_check_time = None
        self._last_check_result = None
        self._check_count = 0
        self._consecutive_failures = 0
        self._max_retry_attempts = 10
        self._inactive_due_to_failures = False
        
    def start_monitoring(self, delay_start: float = 5.0):
        """
        Start the database monitoring timer.
        
        Args:
            delay_start: Delay in seconds before starting to prevent race conditions
        """
        with self._timer_lock:
            if self._running:
                logger.warning("Database monitoring is already running")
                return
                
            self._running = True
            self._start_time = datetime.now()
            self._next_check_time = self._start_time + timedelta(seconds=delay_start)
            
            logger.info(f"Starting database monitoring in {delay_start} seconds (check interval: {self._check_interval}s)")
            
            # Start the timer with initial delay
            self._timer = threading.Timer(delay_start, self._run_monitoring_loop)
            self._timer.daemon = True  # Don't prevent app shutdown
            self._timer.start()
            
    def stop_monitoring(self):
        """Stop the database monitoring timer."""
        with self._timer_lock:
            if not self._running:
                return
                
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
                
            logger.info("Database monitoring stopped")
            
    def _run_monitoring_loop(self):
        """Main monitoring loop that runs every 30 seconds."""
        while self._running:
            try:
                self._perform_health_check()
                self._check_count += 1
                
                # Schedule next check
                if self._running:
                    self._next_check_time = datetime.now() + timedelta(seconds=self._check_interval)
                    self._timer = threading.Timer(self._check_interval, self._run_monitoring_loop)
                    self._timer.daemon = True
                    self._timer.start()
                    break  # Exit this loop iteration
                    
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
                # Continue running even if there's an error
                if self._running:
                    time.sleep(self._check_interval)
                    
    def _perform_health_check(self):
        """Perform a database health check with actual connection testing and retry logic."""
        check_time = datetime.now()
        
        # Check if we've exceeded max retry attempts
        if self._inactive_due_to_failures:
            logger.debug("Database manager inactive due to consecutive failures")
            self._last_check_result = {
                'timestamp': check_time,
                'connected': False,
                'config_loaded': False,
                'consecutive_failures': self._consecutive_failures,
                'inactive_reason': f'Exceeded {self._max_retry_attempts} consecutive failures',
                'manager_active': False
            }
            return
        
        try:
            # First check if we can load config to determine config_loaded status
            from utils.content_db_manager import get_content_db_manager
            db_manager = get_content_db_manager()
            status = db_manager.get_connection_status()
            config_available = status.get('config_loaded', False)
            
            # Test actual database connection with sanitized config
            connection_successful = self._test_database_connection()
            
            if connection_successful:
                # Reset failure count on successful connection
                self._consecutive_failures = 0
                logger.debug("Database connection test successful")
                
                self._last_check_result = {
                    'timestamp': check_time,
                    'connected': True,
                    'config_loaded': True,  # If connection works, config must be loaded
                    'consecutive_failures': self._consecutive_failures,
                    'manager_active': True
                }
            else:
                # Connection failed - increment failure count
                self._consecutive_failures += 1
                logger.warning(f"Database connection failed (attempt {self._consecutive_failures}/{self._max_retry_attempts})")
                
                # Check if we should go inactive
                if self._consecutive_failures >= self._max_retry_attempts:
                    self._inactive_due_to_failures = True
                    logger.error(f"Database manager going inactive after {self._max_retry_attempts} consecutive failures")
                    
                    # Stop the monitoring timer
                    self.stop_monitoring()
                
                self._last_check_result = {
                    'timestamp': check_time,
                    'connected': False,
                    'config_loaded': config_available,  # Use actual config status from content_db_manager
                    'consecutive_failures': self._consecutive_failures,
                    'manager_active': not self._inactive_due_to_failures,
                    'retry_attempts_remaining': max(0, self._max_retry_attempts - self._consecutive_failures)
                }
            
        except Exception as e:
            # Exception during health check
            self._consecutive_failures += 1
            logger.error(f"Database health check exception (attempt {self._consecutive_failures}/{self._max_retry_attempts}): {e}")
            
            # Check if we should go inactive
            if self._consecutive_failures >= self._max_retry_attempts:
                self._inactive_due_to_failures = True
                logger.error(f"Database manager going inactive after {self._max_retry_attempts} consecutive failures")
                self.stop_monitoring()
            
            self._last_check_result = {
                'timestamp': check_time,
                'connected': False,
                'config_loaded': False,
                'consecutive_failures': self._consecutive_failures,
                'error': str(e),
                'manager_active': not self._inactive_due_to_failures,
                'retry_attempts_remaining': max(0, self._max_retry_attempts - self._consecutive_failures)
            }
            
    def _load_config_from_env(self):
        """Load database configuration from environment variables."""
        try:
            # Check if we have the production database URL in environment
            db_url = os.environ.get('PRODUCTION_DATABASE_URL')
            if not db_url:
                # Try alternative environment variable names
                db_url = os.environ.get('DATABASE_URL_CONTENT')
                
            if db_url:
                logger.info("Found database URL in environment, updating configuration...")
                
                # Force reload configuration from environment
                config_manager = get_persistent_config()
                config_manager._config = None  # Clear cached config
                
                # This will trigger a reload from environment variables
                config_manager.get_database_config()
                
                logger.info("Database configuration reloaded from environment")
            else:
                logger.warning("No database URL found in environment variables")
                
        except Exception as e:
            logger.error(f"Failed to load configuration from environment: {e}")
            
    def _test_database_connection(self) -> bool:
        """Test actual database connection using the same logic as Admin Dashboard."""
        try:
            # Import the same function that Admin Dashboard uses for connection testing
            # This ensures consistency between the two systems
            import sys
            if 'app' in sys.modules:
                from app import get_eqemu_db_connection
            else:
                # Fallback if app module not available
                logger.warning("App module not available, using fallback connection test")
                return self._fallback_connection_test()
            
            # Use the exact same connection test that Admin Dashboard uses
            test_conn, db_type, error = get_eqemu_db_connection()
            
            if test_conn:
                try:
                    # Perform the same test query as Admin Dashboard
                    cursor = test_conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    
                    # Verify we actually got a result
                    if result is None:
                        logger.warning("Database connection test returned no result")
                        return False
                    
                    logger.debug("Database connection test successful")
                    return True
                    
                except Exception as query_error:
                    logger.warning(f"Database query test failed: {query_error}")
                    return False
                finally:
                    # Always close the connection
                    try:
                        test_conn.close()
                    except:
                        pass
            else:
                logger.warning(f"Database connection failed: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing database connection: {e}")
            return False
            
    def _fallback_connection_test(self) -> bool:
        """Fallback connection test when app module is not available."""
        try:
            from utils.content_db_manager import get_content_db_manager
            db_manager = get_content_db_manager()
            
            # First, check if configuration is actually available
            try:
                config, db_type = db_manager._load_database_config()
                if not config or not db_type:
                    logger.warning("Database configuration not available for connection test")
                    return False
            except Exception as config_error:
                logger.warning(f"Failed to load database configuration: {config_error}")
                return False
            
            # Try to get an actual connection directly
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    
                    # Verify we actually got a result
                    if result is None:
                        logger.warning("Database connection test returned no result")
                        return False
                    
                    logger.debug("Database connection test successful (fallback)")
                    return True
                    
            except Exception as conn_error:
                logger.warning(f"Database connection test failed: {conn_error}")
                return False
                
        except Exception as e:
            logger.error(f"Error in fallback connection test: {e}")
            return False
            
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status for the Database Diagnostics modal."""
        with self._timer_lock:
            now = datetime.now()
            
            # Calculate time until next check
            time_to_next_check = 0
            if self._next_check_time and self._running:
                delta = self._next_check_time - now
                time_to_next_check = max(0, int(delta.total_seconds()))
                
            # Calculate uptime
            uptime_seconds = 0
            if self._start_time:
                uptime_seconds = int((now - self._start_time).total_seconds())
                
            status = {
                'monitoring_active': self._running,
                'check_interval': self._check_interval,
                'time_to_next_check': time_to_next_check,
                'next_check_time': self._next_check_time.isoformat() if self._next_check_time else None,
                'uptime_seconds': uptime_seconds,
                'total_checks': self._check_count,
                'last_check': self._last_check_result,
                'start_time': self._start_time.isoformat() if self._start_time else None
            }
            
            return status
            
    def force_check(self) -> Dict[str, Any]:
        """Force an immediate health check and return the result."""
        logger.info("Forcing immediate database health check...")
        self._perform_health_check()
        return self._last_check_result
        
    def is_running(self) -> bool:
        """Check if monitoring is currently running."""
        return self._running


# Global instance
_database_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the singleton database manager instance."""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


def initialize_database_manager(delay_start: float = 5.0):
    """Initialize and start the database manager."""
    manager = get_database_manager()
    if not manager.is_running():
        manager.start_monitoring(delay_start)
        logger.info("✅ Database manager initialized and monitoring started")
    else:
        logger.info("Database manager already running")


def shutdown_database_manager():
    """Shutdown the database manager."""
    manager = get_database_manager()
    if manager.is_running():
        manager.stop_monitoring()
        logger.info("Database manager shutdown complete")