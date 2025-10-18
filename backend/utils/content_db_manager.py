"""
Content Database Connection Manager with automatic reconnection and retry logic.

This module manages connections to the EQEmu content database with:
- Automatic reconnection on connection loss
- Exponential backoff retry logic
- Connection pooling for efficiency
- Thread-safe operations
- Sanitization of configuration values
"""

import time
import logging
import threading
from typing import Optional, Tuple, Any, Dict
from urllib.parse import urlparse
from contextlib import contextmanager

from utils.database_connectors import get_database_connector
from utils.db_connection_pool import DatabaseConnectionPool, OriginalDatabaseConnectionPool
from utils.persistent_config import get_persistent_config
from utils.db_config_validator import validate_database_config

logger = logging.getLogger(__name__)


class ContentDatabaseManager:
    """Manages content database connections with automatic reconnection."""
    
    def __init__(self):
        """Initialize the content database manager."""
        self._pool = None
        self._lock = threading.Lock()
        self._last_connect_attempt = 0
        self._connect_retry_delay = 1  # Start with 1 second delay
        self._max_retry_delay = 10  # Max 10 seconds between retries (reduced from 60)
        self._connection_healthy = False
        self._config = None
        self._db_type = None
        self._last_validation_result = None
        
    def _sanitize_config_value(self, value: str) -> str:
        """Remove leading/trailing whitespace from configuration values."""
        if isinstance(value, str):
            return value.strip()
        return value
        
    def _sanitize_database_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string values in database configuration."""
        if not config:
            return config
            
        sanitized = {}
        for key, value in config.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value
                
        return sanitized
        
    def _load_database_config(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Load and sanitize database configuration with Railway restart handling."""
        config_manager = get_persistent_config()
        config = config_manager.get_database_config()
        
        if not config:
            logger.error("No database configuration found")
            return None, None
            
        # Log configuration source for debugging Railway restart issues
        config_source = config.get('config_source', 'unknown')
        logger.info(f"Loading database config from: {config_source}")
        
        # Sanitize the configuration
        config = self._sanitize_database_config(config)
        
        database_url = config.get('production_database_url', '')
        if not database_url:
            logger.error("No database URL found in configuration")
            return None, None
            
        # Parse database URL and extract config
        parsed = urlparse(database_url)
        db_type = config.get('database_type', 'mysql')
        
        # Validate that we have all required connection parameters
        missing_params = []
        if not parsed.hostname:
            missing_params.append('hostname')
        if not parsed.username:
            missing_params.append('username')
        if not parsed.password:
            missing_params.append('password')
        if not parsed.path or len(parsed.path) <= 1:
            missing_params.append('database')
            
        if missing_params:
            logger.error(f"Database configuration missing required parameters: {missing_params}")
            logger.info("This often happens after Railway restarts - attempting to reload from environment variables")
            
            # Force reload from environment variables
            config_manager._config = None  # Clear cached config
            config = config_manager.get_database_config()
            if config:
                database_url = config.get('production_database_url', '')
                if database_url:
                    parsed = urlparse(database_url)
                    logger.info("Successfully reloaded configuration from environment variables")
                else:
                    logger.error("Failed to reload database configuration")
                    return None, None
            else:
                logger.error("Failed to reload database configuration from environment")
                return None, None
        
        db_config = {
            'host': self._sanitize_config_value(parsed.hostname or ''),
            'port': int(parsed.port) if parsed.port else 3306,
            'database': self._sanitize_config_value(parsed.path[1:] if parsed.path else ''),
            'username': self._sanitize_config_value(parsed.username or ''),
            'password': self._sanitize_config_value(parsed.password or ''),
            'use_ssl': config.get('database_ssl', True)
        }

        # Remove empty values (but keep ssl setting even if False)
        db_config = {k: v for k, v in db_config.items() if v or k == 'use_ssl'}

        # Apply database-specific timeout defaults to keep connections responsive
        if db_type == 'mysql':
            db_config.setdefault('connect_timeout', 10)
            db_config.setdefault('read_timeout', 60)
            db_config.setdefault('write_timeout', 30)
            db_config.setdefault('autocommit', True)
        elif db_type == 'postgresql':
            db_config.setdefault('connect_timeout', 5)
        elif db_type == 'mssql':
            db_config.setdefault('timeout', 5)

        logger.info(f"Loaded database config: host={db_config.get('host')}, "
                   f"port={db_config.get('port')}, db={db_config.get('database')}, "
                   f"user={db_config.get('username')}, ssl={db_config.get('use_ssl')}")

        return db_config, db_type
        
    def _create_connection_pool(self) -> bool:
        """Create a new connection pool with retry logic."""
        try:
            # Load configuration
            self._config, self._db_type = self._load_database_config()
            if not self._config:
                return False
                
            # Create connection pool
            logger.info(f"Creating connection pool for {self._db_type} database...")
            
            # Create a connection factory function for the pool
            def create_connection():
                from utils.database_connectors import get_database_connector
                return get_database_connector(self._db_type, self._config)
            
            try:
                self._pool = OriginalDatabaseConnectionPool(
                    create_connection_func=create_connection,
                    max_connections=3,  # Reduced from 5 to prevent hanging
                    timeout=2           # Reduced from 5 to prevent hanging
                )
            except Exception as pool_error:
                logger.warning(
                    "Falling back to simplified database connection pool due to error: %s",
                    pool_error,
                )
                self._pool = DatabaseConnectionPool(
                    create_connection_func=create_connection,
                    max_connections=3,
                    timeout=2,
                )
            
            # Test the connection
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
            logger.info("✅ Database connection pool created successfully")
            self._connection_healthy = True
            self._connect_retry_delay = 1  # Reset retry delay on success
            return True
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            self._connection_healthy = False
            if self._pool:
                try:
                    self._pool.close_all()
                except:
                    pass
                self._pool = None
            return False
            
    def _ensure_connection(self) -> bool:
        """Ensure database connection is available, with non-blocking retry logic."""
        with self._lock:
            # If connection is healthy, return immediately
            if self._connection_healthy and self._pool:
                return True

            # NON-BLOCKING: Check if we should retry, but don't block
            current_time = time.time()
            if current_time - self._last_connect_attempt < self._connect_retry_delay:
                # Instead of blocking, just return False immediately
                # This prevents hanging the Flask thread
                return False

            self._last_connect_attempt = current_time

            logger.info("Attempting to establish database connection...")

            try:
                if self._create_connection_pool():
                    logger.info("Database connection pool available")
                    return True

                logger.warning("Failed to establish database connection pool")
                self._connect_retry_delay = min(self._connect_retry_delay * 2, self._max_retry_delay)
                return False
            except Exception as e:
                logger.error(f"Error establishing database connection: {e}")
                self._connect_retry_delay = min(self._connect_retry_delay * 2, self._max_retry_delay)
                return False

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic retry."""
        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            if not self._ensure_connection():
                retry_count += 1
                time.sleep(min(1 * retry_count, self._max_retry_delay))
                continue

            try:
                with self._pool.get_connection() as conn:
                    yield conn
                    return
            except Exception as e:
                last_error = e
                retry_count += 1
                logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {e}")

                with self._lock:
                    self._connection_healthy = False
                    if self._pool:
                        try:
                            self._pool.close_all()
                        except Exception as close_error:
                            logger.warning(f"Error closing connection pool after failure: {close_error}")
                        finally:
                            self._pool = None

                if retry_count < max_retries:
                    time.sleep(min(1 * retry_count, self._max_retry_delay))

        if last_error:
            raise last_error
        raise RuntimeError("Unable to acquire database connection")
                
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        with self._lock:
            pool_stats = None
            if self._pool and hasattr(self._pool, 'get_pool_stats'):
                try:
                    pool_stats = self._pool.get_pool_stats()
                except Exception as e:
                    logger.warning(f"Unable to read pool statistics: {e}")

            if self._config is None or self._db_type is None:
                try:
                    self._config, self._db_type = self._load_database_config()
                except Exception as e:
                    logger.error(f"Failed to refresh database configuration for status check: {e}")

            connected = self._connection_healthy and self._pool is not None
            config_loaded = self._config is not None

            status = {
                'connected': connected,
                'pool_active': self._pool is not None,
                'retry_delay': max(0, self._connect_retry_delay - (time.time() - self._last_connect_attempt)),
                'last_attempt': self._last_connect_attempt,
                'database_type': self._db_type,
                'config_loaded': config_loaded,
                'validation_result': self._last_validation_result,
                'pool_stats': pool_stats
            }

            return status
            
    def close(self):
        """Close the connection pool."""
        with self._lock:
            if self._pool:
                try:
                    self._pool.close_all()
                except Exception as e:
                    logger.error(f"Error closing connection pool: {e}")
                finally:
                    self._pool = None
                    self._connection_healthy = False

    def get_database_type(self) -> Optional[str]:
        """Return the configured database type if known."""
        with self._lock:
            return self._db_type


# Global instance
_content_db_manager = None


def get_content_db_manager() -> ContentDatabaseManager:
    """Get the singleton content database manager instance."""
    global _content_db_manager
    if _content_db_manager is None:
        _content_db_manager = ContentDatabaseManager()
    return _content_db_manager


def initialize_content_database():
    """Initialize content database connection on app startup."""
    manager = get_content_db_manager()
    logger.info("Initializing content database connection...")
    
    # Try to connect with retries (reduced for faster startup)
    max_attempts = 2
    for attempt in range(max_attempts):
        if manager._ensure_connection():
            logger.info("✅ Content database initialized successfully")
            return True
            
        if attempt < max_attempts - 1:
            delay = 1  # Simple 1 second delay instead of exponential backoff
            logger.info(f"Retrying in {delay} seconds... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)
            
    logger.warning("⚠️ Content database not configured - will initialize on first request")
    return False
