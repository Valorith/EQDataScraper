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
            self.data_dir = Path('/app/data')
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
                return config
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
        """Get database configuration."""
        config = self.load()
        
        # Check for database URL in persistent config
        db_url = config.get('production_database_url')
        
        # Note: We do NOT fall back to DATABASE_URL environment variable
        # as that's reserved for the PostgreSQL auth database
        
        if not db_url:
            return None
        
        # Return combined config
        return {
            'production_database_url': db_url,
            'database_type': config.get('database_type', 'mysql'),
            'use_production_database': config.get('use_production_database', True),
            'database_read_only': config.get('database_read_only', True),
            'database_ssl': config.get('database_ssl', True)
        }
    
    def save_database_config(self, db_url: str, db_type: str, use_ssl: bool = True) -> bool:
        """Save database configuration persistently."""
        return self.save({
            'production_database_url': db_url,
            'database_type': db_type,
            'use_production_database': True,
            'database_read_only': True,
            'database_ssl': use_ssl
        })


# Singleton instance
_persistent_config = None


def get_persistent_config() -> PersistentConfig:
    """Get the singleton persistent config instance."""
    global _persistent_config
    if _persistent_config is None:
        _persistent_config = PersistentConfig()
    return _persistent_config