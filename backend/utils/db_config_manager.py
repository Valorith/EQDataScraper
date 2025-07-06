"""
Database configuration manager with automatic reload on config changes.
"""

import os
import json
import threading
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseConfigManager:
    """Manages database configuration with automatic reload on changes."""
    
    def __init__(self, config_path):
        self.config_path = config_path
        self._config = None
        self._last_modified = None
        self._lock = threading.Lock()
        self._reload_callbacks = []
        
    def add_reload_callback(self, callback):
        """Add a callback to be called when config reloads."""
        self._reload_callbacks.append(callback)
        
    def get_config(self):
        """Get current configuration, reloading if file has changed."""
        with self._lock:
            # Check if config file has been modified
            try:
                stat = os.stat(self.config_path)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                # Only reload if more than 1 second has passed to avoid false positives
                should_reload = (self._last_modified is None or 
                               (mtime > self._last_modified and 
                                (mtime - self._last_modified) > timedelta(seconds=1)))
                
                if should_reload:
                    # Reload configuration
                    self._load_config()
                    self._last_modified = mtime
                    
                    # Call reload callbacks only if config was already loaded before
                    if self._config is not None:
                        for callback in self._reload_callbacks:
                            try:
                                callback()
                            except Exception as e:
                                logger.error(f"Error in config reload callback: {e}")
                            
            except OSError:
                # File doesn't exist
                if self._config is None:
                    self._config = {}
                    
        return self._config
        
    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = json.load(f)
                logger.info("Database configuration reloaded")
        except Exception as e:
            logger.error(f"Error loading database configuration: {e}")
            if self._config is None:
                self._config = {}
                
    def invalidate(self):
        """Force config reload on next access."""
        with self._lock:
            self._last_modified = None