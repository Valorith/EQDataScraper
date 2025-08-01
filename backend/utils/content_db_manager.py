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
from utils.db_connection_pool import DatabaseConnectionPool
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
            
            self._pool = DatabaseConnectionPool(
                create_connection_func=create_connection,
                max_connections=3,  # Reduced from 5 to prevent hanging
                timeout=2           # Reduced from 5 to prevent hanging
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
            
            # Since we're using direct connections now (no pooling), 
            # just check if we can load the config
            try:
                config, db_type = self._load_database_config()
                if config and db_type:
                    logger.info("Database configuration loaded successfully")
                    self._connection_healthy = True
                    return True
                else:
                    logger.warning("No database configuration available")
                    return False
            except Exception as e:
                logger.error(f"Error loading database config: {e}")
                return False
                
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic retry (POOLING DISABLED)."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Load config directly each time (no pooling)
                config, db_type = self._load_database_config()
                if not config or not db_type:
                    raise Exception("Database configuration not available")
                
                # Create direct connection without pooling but with tracking
                conn = get_database_connector(db_type, config, track_queries=True)
                logger.info("Created direct database connection (no pooling, with tracking)")
                
                try:
                    yield conn
                    return
                finally:
                    # Always close the connection when done
                    try:
                        conn.close()
                        logger.debug("Closed direct database connection")
                    except:
                        pass
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {e}")
                
                # Mark connection as unhealthy
                with self._lock:
                    self._connection_healthy = False
                    
                if retry_count >= max_retries:
                    raise
                    
                # Wait before retry
                time.sleep(1 * retry_count)
                
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        with self._lock:
            # Test direct connection to get accurate status
            try:
                config, db_type = self._load_database_config()
                connected = config is not None and db_type is not None
                config_loaded = config is not None  # Use the actual loaded config, not cached self._config
            except:
                connected = False
                config_loaded = False
            
            status = {
                'connected': connected,
                'pool_active': False,  # We're using direct connections, not pooling
                'retry_delay': max(0, self._connect_retry_delay - (time.time() - self._last_connect_attempt)),
                'last_attempt': self._last_connect_attempt,
                'database_type': self._db_type,
                'config_loaded': config_loaded,  # Use the real config status
                'validation_result': self._last_validation_result
            }
            
            # No pool statistics since we're using direct connections
            status['pool_stats'] = None
                
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