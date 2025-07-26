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
from typing import Optional, Dict, Any, List
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
        self._logs = []  # Store detailed logs for debugging
        self._max_log_entries = 50  # Keep last 50 log entries
        self._environment = self._detect_environment()
        
    def _detect_environment(self) -> str:
        """Detect if we're running in development, production, or Railway."""
        import os
        
        # Check for Railway environment
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            return 'railway'
        
        # Check for production indicators
        if (os.environ.get('NODE_ENV') == 'production' or 
            os.environ.get('PYTHON_ENV') == 'production' or
            os.environ.get('DATABASE_URL')):  # Railway uses DATABASE_URL
            return 'production'
        
        # Check if we're in a development environment
        if (os.environ.get('NODE_ENV') == 'development' or 
            os.environ.get('ENABLE_DEV_AUTH') == 'true'):
            return 'development'
        
        # Default to development
        return 'development'
        
    def _should_run_monitoring(self) -> bool:
        """Determine if monitoring should run based on environment."""
        if self._environment == 'development':
            # In development, allow monitoring to run but with simplified config check
            # This prevents hanging issues while still allowing testing
            self._add_log('info', 'Development environment: Monitoring enabled for testing')
            return True
        
        # In production/Railway, always run monitoring
        self._add_log('info', f'{self._environment.title()} environment: Monitoring enabled')
        return True
        
    def _add_log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a log entry for debugging purposes."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'message': message,
            'details': details or {}
        }
        
        # Thread-safe log addition
        with self._timer_lock:
            self._logs.append(log_entry)
            # Keep only the last N entries
            if len(self._logs) > self._max_log_entries:
                self._logs = self._logs[-self._max_log_entries:]
        
        # Also log to standard logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"DatabaseManager: {message}")
        
    def start_monitoring(self, delay_start: float = 5.0):
        """
        Start the database monitoring timer.
        
        Args:
            delay_start: Delay in seconds before starting to prevent race conditions
        """
        with self._timer_lock:
            if self._running:
                self._add_log('warning', 'Database monitoring is already running')
                return
            
            # Check if monitoring should run in this environment
            if not self._should_run_monitoring():
                self._add_log('info', f'Database monitoring disabled in {self._environment} environment')
                # Set a fake "running" state for UI purposes, but don't actually start timer
                self._running = False
                self._last_check_result = {
                    'timestamp': datetime.now(),
                    'connected': False,
                    'config_loaded': False,
                    'consecutive_failures': 0,
                    'manager_active': False,
                    'environment_disabled': True,
                    'environment': self._environment
                }
                return
                
            self._running = True
            self._start_time = datetime.now()
            self._next_check_time = self._start_time + timedelta(seconds=delay_start)
            
            self._add_log('info', f'Starting database monitoring in {delay_start}s (environment: {self._environment}, interval: {self._check_interval}s)')
            
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
        
        self._add_log('debug', f'Starting health check #{self._check_count + 1}', {
            'consecutive_failures': self._consecutive_failures,
            'max_attempts': self._max_retry_attempts,
            'inactive': self._inactive_due_to_failures
        })
        
        # Check if we've exceeded max retry attempts
        if self._inactive_due_to_failures:
            self._add_log('warning', 'Database manager inactive due to consecutive failures', {
                'reason': f'Exceeded {self._max_retry_attempts} consecutive failures'
            })
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
            self._add_log('info', 'Testing database connection...', {'attempt': self._consecutive_failures + 1})
            connection_successful = self._test_database_connection()
            
            if connection_successful:
                # Reset failure count on successful connection
                self._consecutive_failures = 0
                self._add_log('info', '✅ Database connection test successful')
                
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
                self._add_log('warning', f'❌ Database connection failed', {
                    'attempt': self._consecutive_failures,
                    'max_attempts': self._max_retry_attempts
                })
                
                # Try to automatically reload saved configuration on first few failures
                if self._consecutive_failures <= 3:
                    self._add_log('info', f'🔄 Attempting automatic config reload', {
                        'failure_count': self._consecutive_failures,
                        'reload_attempts_remaining': 4 - self._consecutive_failures
                    })
                    if self._attempt_config_reload():
                        self._add_log('info', '✅ Config reload successful, retesting connection...')
                        # Test connection again after reload
                        connection_successful = self._test_database_connection()
                        if connection_successful:
                            self._consecutive_failures = 0
                            self._add_log('info', '🎉 Database connection restored after config reload!')
                            self._last_check_result = {
                                'timestamp': check_time,
                                'connected': True,
                                'config_loaded': True,
                                'consecutive_failures': self._consecutive_failures,
                                'manager_active': True,
                                'config_auto_reloaded': True
                            }
                            return
                        else:
                            self._add_log('warning', '❌ Connection still failed after config reload')
                    else:
                        self._add_log('error', '❌ Automatic config reload failed')
                else:
                    self._add_log('warning', f'⚠️ Skipping auto-reload (failure {self._consecutive_failures} > 3)')
                
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
            
    def _attempt_config_reload(self) -> bool:
        """Attempt to reload and apply saved database configuration using same logic as admin UI."""
        try:
            self._add_log('info', '🔄 Starting automatic config reload (admin UI logic)...')
            
            # Step 1: Call the same API endpoint that "Load Saved" uses
            self._add_log('debug', 'Step 1: Getting stored configuration via API...')
            stored_config = self._get_stored_config_via_api()
            if not stored_config:
                self._add_log('error', 'No stored configuration found via API')
                return False
                
            self._add_log('debug', 'Stored config retrieved successfully', {
                'has_host': bool(stored_config.get('host')),
                'has_database': bool(stored_config.get('database_name')),
                'has_username': bool(stored_config.get('username')),
                'has_password': bool(stored_config.get('password')),
                'database_type': stored_config.get('database_type'),
                'use_ssl': stored_config.get('database_ssl')
            })
                
            # Step 2: Process config the same way the frontend does (with trimming)
            self._add_log('debug', 'Step 2: Processing config with frontend logic...')
            config_data = {
                'db_type': (stored_config.get('database_type', 'mysql') or 'mysql').strip(),
                'host': (stored_config.get('host', '') or '').strip(),
                'port': stored_config.get('port', 3306),
                'database': (stored_config.get('database_name', '') or '').strip(),
                'username': (stored_config.get('username', '') or '').strip(),
                'password': (stored_config.get('password', '') or '').strip(),
                'use_ssl': stored_config.get('database_ssl', True)
            }
            
            self._add_log('info', 'Config processed successfully', {
                'host': config_data['host'],
                'database': config_data['database'],
                'username': config_data['username'],
                'port': config_data['port'],
                'db_type': config_data['db_type'],
                'use_ssl': config_data['use_ssl']
            })
            
            # Step 3: Save configuration using same logic as "Save Configuration" button
            self._add_log('debug', 'Step 3: Saving config via API logic...')
            return self._save_config_via_api(config_data)
                
        except Exception as e:
            self._add_log('error', f'Exception during automatic config reload: {str(e)}', {
                'exception_type': type(e).__name__
            })
            return False
            
    def _get_stored_config_via_api(self):
        """Get stored configuration using the same API endpoint as 'Load Saved' button."""
        try:
            # Import here to avoid circular imports
            import sys
            if 'routes.admin' not in sys.modules:
                from routes.admin import get_stored_database_config
            
            # Simulate the API call that frontend makes
            from utils.persistent_config import get_persistent_config
            from urllib.parse import urlparse
            
            persistent_config = get_persistent_config()
            db_config = persistent_config.get_database_config()
            
            if not db_config:
                return None
                
            db_url = db_config.get('production_database_url')
            if not db_url:
                return None
                
            # Parse URL same way as the admin endpoint does
            parsed = urlparse(db_url)
            
            return {
                'database_type': db_config.get('database_type', 'mysql'),
                'host': parsed.hostname,
                'port': int(parsed.port) if parsed.port else 3306,
                'database_name': parsed.path[1:] if parsed.path else '',
                'username': parsed.username,
                'password': parsed.password,
                'database_ssl': db_config.get('database_ssl', True)
            }
            
        except Exception as e:
            logger.error(f"Error getting stored config via API logic: {e}")
            return None
            
    def _save_config_via_api(self, config_data) -> bool:
        """Save configuration using the same logic as 'Save Configuration' button."""
        try:
            # Import here to avoid circular imports  
            from utils.persistent_config import get_persistent_config
            from utils.content_db_manager import get_content_db_manager
            
            # Build database URL same way the admin API does
            if config_data['use_ssl']:
                protocol = 'mysql' if config_data['db_type'] == 'mysql' else config_data['db_type']
                db_url = f"{protocol}://{config_data['username']}:{config_data['password']}@{config_data['host']}:{config_data['port']}/{config_data['database']}?sslmode=require"
            else:
                protocol = 'mysql' if config_data['db_type'] == 'mysql' else config_data['db_type']
                db_url = f"{protocol}://{config_data['username']}:{config_data['password']}@{config_data['host']}:{config_data['port']}/{config_data['database']}"
            
            # Save using persistent config same as admin API
            persistent_config = get_persistent_config()
            persistent_config.save_database_config(
                database_url=db_url,
                database_type=config_data['db_type'],
                database_ssl=config_data['use_ssl'],
                database_read_only=True  # Always read-only like admin saves
            )
            
            # Clear content manager cache to force reload
            content_manager = get_content_db_manager()
            content_manager._config = None
            content_manager._connection_healthy = False
            
            logger.info("✅ Database configuration saved using admin UI logic")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config via API logic: {e}")
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
            
    def get_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent database manager logs for debugging."""
        with self._timer_lock:
            logs = self._logs.copy()
            if limit:
                logs = logs[-limit:]
            return logs
            
    def force_check(self) -> Dict[str, Any]:
        """Force an immediate health check and return the result."""
        logger.info("Forcing immediate database health check...")
        self._perform_health_check()
        return self._last_check_result
        
    def is_running(self) -> bool:
        """Check if monitoring is currently running."""
        return self._running
        
    def restart_monitoring(self, delay_start: float = 5.0) -> bool:
        """Restart monitoring after it has gone inactive due to failures."""
        with self._timer_lock:
            if self._running:
                logger.warning("Database monitoring is already running")
                return False
                
            # Reset failure state
            self._inactive_due_to_failures = False
            self._consecutive_failures = 0
            self._last_check_result = None
            
            logger.info("🔄 Restarting database monitoring after successful config reload")
            
            # Start monitoring again
            self.start_monitoring(delay_start)
            return True


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
    
    # Add initialization log
    manager._add_log('info', 'Database Manager initialized', {
        'environment': manager._environment,
        'check_interval': manager._check_interval,
        'max_retry_attempts': manager._max_retry_attempts,
        'delay_start': delay_start
    })
    
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


def restart_database_manager(force: bool = False) -> bool:
    """Restart database manager monitoring, optionally forcing restart even if active."""
    manager = get_database_manager()
    
    manager._add_log('info', f'Restart requested', {
        'force': force,
        'currently_running': manager.is_running(),
        'inactive_due_to_failures': manager._inactive_due_to_failures
    })
    
    # Stop current monitoring if running
    if manager.is_running():
        if not force:
            manager._add_log('warning', 'Manager already running, use force=True to restart')
            return False
        manager.stop_monitoring()
        manager._add_log('info', 'Stopped existing monitoring for restart')
    
    # Reset failure state
    manager._inactive_due_to_failures = False
    manager._consecutive_failures = 0
    manager._last_check_result = None
    
    # Check if monitoring should run in this environment before attempting start
    if not manager._should_run_monitoring():
        manager._add_log('warning', f'Cannot restart: monitoring disabled in {manager._environment} environment')
        return False
    
    # Start monitoring
    manager.start_monitoring(1.0)  # Quick start for manual restart
    
    # Verify that monitoring actually started
    success = manager.is_running()
    if success:
        manager._add_log('info', 'Database Manager restarted successfully')
    else:
        manager._add_log('error', 'Database Manager restart failed - monitoring did not start')
    
    return success


def check_and_restart_inactive_manager():
    """Check if manager is inactive due to failures and attempt restart with config reload."""
    manager = get_database_manager()
    
    # Check if manager is inactive due to failures
    if manager._inactive_due_to_failures and not manager.is_running():
        logger.info("🔄 Detected inactive database manager, attempting automatic restart...")
        
        # Try to reload configuration and restart
        if manager._attempt_config_reload():
            logger.info("Config reload successful, restarting monitoring...")
            if manager.restart_monitoring():
                logger.info("✅ Database manager successfully restarted after config reload")
                return True
            else:
                logger.warning("Failed to restart database manager after config reload")
        else:
            logger.warning("Config reload failed, cannot restart database manager")
            
    return False