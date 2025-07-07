"""
Persistent configuration management for production deployments.

This module handles configuration that needs to persist across deployments,
particularly database configuration. It uses a data directory that persists
on Railway and other deployment platforms.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PersistentConfig:
    """Manages persistent configuration across deployments."""
    
    def __init__(self):
        """Initialize persistent config manager."""
        # Determine the persistent data directory
        # Railway provides /app/data as a persistent volume
        # Fall back to local .data directory for development
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            # Try multiple possible persistent directories on Railway
            possible_dirs = [
                Path('/app/data'),  # Railway persistent volume
                Path('/data'),      # Alternative persistent volume
                Path('/persist'),   # Another possible location
                Path.home() / '.eqdata'  # User home directory fallback
            ]
            
            self.data_dir = None
            for dir_path in possible_dirs:
                try:
                    # Test if we can create the directory
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Test if we can write to it
                    test_file = dir_path / '.write_test'
                    test_file.write_text('test')
                    test_file.unlink()  # Remove test file
                    self.data_dir = dir_path
                    logger.info(f"Using persistent directory: {self.data_dir}")
                    break
                except Exception as e:
                    logger.warning(f"Cannot use {dir_path}: {e}")
            
            if not self.data_dir:
                # Ultimate fallback - use environment variable storage
                logger.warning("No writable persistent directory found, will use environment fallback")
                self.data_dir = Path('/tmp/.eqdata')  # Temporary fallback
        else:
            # Use a hidden directory in project root for local development
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / '.data'
        
        # Ensure data directory exists
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.config_file = self.data_dir / 'persistent_config.json'
            self._available = True
            logger.info(f"Persistent config initialized. Data directory: {self.data_dir}")
            logger.info(f"Config file path: {self.config_file}")
            
            # Log directory permissions for debugging
            import stat
            st = os.stat(self.data_dir)
            logger.info(f"Directory permissions: {oct(st.st_mode)}")
            logger.info(f"Directory writable: {os.access(self.data_dir, os.W_OK)}")
        except Exception as e:
            logger.warning(f"Could not create persistent data directory: {e}")
            self.config_file = None
            self._available = False
    
    def load(self) -> Dict[str, Any]:
        """Load persistent configuration."""
        if not self._available or not self.config_file or not self.config_file.exists():
            logger.info("No persistent config file found or not available")
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded persistent config with {len(config)} keys")
                
                # Sanitize string values by stripping whitespace
                sanitized_config = {}
                for key, value in config.items():
                    if isinstance(value, str):
                        sanitized_config[key] = value.strip()
                    else:
                        sanitized_config[key] = value
                        
                return sanitized_config
        except Exception as e:
            logger.error(f"Error loading persistent config: {e}")
            return {}
    
    def save(self, config: Dict[str, Any]) -> bool:
        """Save configuration persistently."""
        if not self._available or not self.config_file:
            logger.warning("Persistent storage not available")
            return False
        
        try:
            # Merge with existing config
            existing = self.load()
            existing.update(config)
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(existing, f, indent=2)
            
            logger.info(f"Saved persistent config with {len(existing)} keys")
            return True
        except Exception as e:
            logger.error(f"Error saving persistent config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value."""
        return self.save({key: value})
    
    def get_database_config(self) -> Optional[Dict[str, Any]]:
        """Get database configuration - reverted to PR #40 working logic."""
        logger.info("Getting database configuration...")
        
        # REVERT TO PR #40 WORKING LOGIC: Check persistent storage first
        config = self.load()
        logger.info(f"Loaded persistent config keys: {list(config.keys())}")
        
        # Check for database URL in persistent config
        db_url = config.get('production_database_url')
        
        # If not in file, check environment variable as backup
        # Use a specific env var for content database to avoid confusion with auth database
        if not db_url:
            logger.info("No database URL in persistent storage, checking environment variables...")
            db_url = os.environ.get('EQEMU_DATABASE_URL')
            if db_url:
                logger.info("Loaded database URL from EQEMU_DATABASE_URL environment variable")
                # Also get other settings from environment
                db_type = os.environ.get('EQEMU_DATABASE_TYPE', 'mysql')
                use_ssl = os.environ.get('EQEMU_DATABASE_SSL', 'true').lower() == 'true'
                
                # Save to persistent storage for next time
                self.save_database_config(db_url, db_type, use_ssl)
                
                # Return config from environment variables
                return {
                    'production_database_url': db_url,
                    'database_type': db_type,
                    'use_production_database': True,
                    'database_read_only': True,
                    'database_ssl': use_ssl,
                    'database_name': os.environ.get('EQEMU_DATABASE_NAME', ''),
                    'database_password': os.environ.get('EQEMU_DATABASE_PW', ''),
                    'database_port': os.environ.get('EQEMU_DATABASE_PORT', ''),
                    'config_source': 'environment_variables'
                }
        
        # Note: We do NOT fall back to DATABASE_URL environment variable
        # as that's reserved for the PostgreSQL auth database
        
        if not db_url:
            logger.warning("No database configuration found")
            return None
        
        logger.info(f"Using database URL from persistent storage: {db_url[:30]}...")
        
        # Return combined config from persistent storage
        return {
            'production_database_url': db_url,
            'database_type': config.get('database_type', os.environ.get('EQEMU_DATABASE_TYPE', 'mysql')),
            'use_production_database': config.get('use_production_database', True),
            'database_read_only': config.get('database_read_only', True),
            'database_ssl': config.get('database_ssl', True),
            'database_name': config.get('database_name', ''),
            'database_password': config.get('database_password', ''),
            'database_port': config.get('database_port', ''),
            'config_source': 'persistent_storage'
        }
    
    def save_database_config(self, db_url: str, db_type: str, use_ssl: bool = True, 
                           db_name: str = '', db_password: str = '', db_port: str = '') -> bool:
        """Save database configuration persistently."""
        # Sanitize all string inputs by stripping whitespace
        config = {
            'production_database_url': db_url.strip() if db_url else '',
            'database_type': db_type.strip() if db_type else 'mysql',
            'use_production_database': True,
            'database_read_only': True,
            'database_ssl': use_ssl,
            'database_name': db_name.strip() if db_name else '',
            'database_password': db_password.strip() if db_password else '',
            'database_port': db_port.strip() if db_port else ''
        }
        
        # Also update environment variables if we're on Railway
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            logger.info("Attempting to update Railway environment variables (note: this requires Railway API)")
            # Note: Direct env var updates from within the app won't persist across deploys
            # Users need to set these through Railway dashboard or CLI
        
        return self.save(config)


# Singleton instance
_persistent_config = None


def get_persistent_config() -> PersistentConfig:
    """Get the singleton persistent config instance."""
    global _persistent_config
    if _persistent_config is None:
        _persistent_config = PersistentConfig()
    return _persistent_config