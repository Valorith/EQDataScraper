"""
Query tracking persistence module for saving and loading query metrics data.
"""

import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class QueryTrackingPersistence:
    """Handles persistence of query tracking data to disk."""
    
    def __init__(self, data_dir: str = "data/query_tracking"):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, "query_metrics.json")
        self.timeline_file = os.path.join(data_dir, "query_timeline.json")
        self.retention_days = 7
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def save_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Save query metrics to disk."""
        try:
            # Convert deques to lists for JSON serialization
            serializable_data = self._prepare_for_serialization(metrics_data)
            
            # Add timestamp
            serializable_data['last_saved'] = datetime.now().isoformat()
            
            # Write to file
            with open(self.metrics_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            try:
                logger.info(f"Query metrics saved to {self.metrics_file}")
            except:
                pass  # Logger may be closed during shutdown
            return True
            
        except Exception as e:
            try:
                logger.error(f"Failed to save query metrics: {e}")
            except:
                pass  # Logger may be closed during shutdown
            return False
    
    def load_metrics(self) -> Dict[str, Any]:
        """Load query metrics from disk."""
        try:
            if not os.path.exists(self.metrics_file):
                logger.info("No existing query metrics file found, starting fresh")
                return self._get_default_metrics()
            
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
            
            # Check if data is too old
            if self._is_data_expired(data):
                logger.info("Query metrics data is expired, starting fresh")
                return self._get_default_metrics()
            
            # Convert lists back to deques and defaultdicts
            metrics = self._restore_from_serialization(data)
            
            logger.info(f"Query metrics loaded from {self.metrics_file}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to load query metrics: {e}")
            return self._get_default_metrics()
    
    def save_timeline(self, timeline_data: deque) -> bool:
        """Save query timeline to disk."""
        try:
            # Convert deque to list and clean old entries
            timeline_list = list(timeline_data)
            cleaned_timeline = self._clean_timeline_data(timeline_list)
            
            timeline_dict = {
                'timeline': cleaned_timeline,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.timeline_file, 'w') as f:
                json.dump(timeline_dict, f, indent=2)
            
            try:
                logger.info(f"Query timeline saved to {self.timeline_file}")
            except:
                pass  # Logger may be closed during shutdown
            return True
            
        except Exception as e:
            try:
                logger.error(f"Failed to save query timeline: {e}")
            except:
                pass  # Logger may be closed during shutdown
            return False
    
    def load_timeline(self) -> deque:
        """Load query timeline from disk."""
        try:
            if not os.path.exists(self.timeline_file):
                logger.info("No existing query timeline file found, starting fresh")
                return deque(maxlen=168)  # 7 days * 24 hours
            
            with open(self.timeline_file, 'r') as f:
                data = json.load(f)
            
            # Check if data is too old
            if self._is_data_expired(data):
                logger.info("Query timeline data is expired, starting fresh")
                return deque(maxlen=168)
            
            # Convert back to deque
            timeline_list = data.get('timeline', [])
            cleaned_timeline = self._clean_timeline_data(timeline_list)
            
            timeline = deque(cleaned_timeline, maxlen=168)
            
            logger.info(f"Query timeline loaded from {self.timeline_file}")
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to load query timeline: {e}")
            return deque(maxlen=168)
    
    def cleanup_old_data(self) -> None:
        """Remove data files older than retention period."""
        try:
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            
            for filename in [self.metrics_file, self.timeline_file]:
                if os.path.exists(filename):
                    file_age = os.path.getmtime(filename)
                    if file_age < cutoff_time:
                        os.remove(filename)
                        logger.info(f"Removed old query tracking file: {filename}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old query tracking data: {e}")
    
    def _prepare_for_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert deques and defaultdicts to JSON-serializable format."""
        serializable = {}
        
        for key, value in data.items():
            if isinstance(value, deque):
                serializable[key] = list(value)
            elif isinstance(value, defaultdict):
                if key == 'table_sources':
                    # Special handling for nested defaultdicts
                    serializable[key] = {
                        table: dict(sources) for table, sources in value.items()
                    }
                else:
                    serializable[key] = dict(value)
            else:
                serializable[key] = value
        
        return serializable
    
    def _restore_from_serialization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore deques and defaultdicts from JSON data."""
        restored = {}
        
        for key, value in data.items():
            if key == 'query_times':
                restored[key] = deque(value, maxlen=100)
            elif key == 'slow_queries':
                restored[key] = deque(value, maxlen=20)
            elif key == 'query_types':
                restored[key] = defaultdict(int, value)
            elif key == 'tables_accessed':
                restored[key] = defaultdict(int, value)
            elif key == 'table_sources':
                # Restore nested defaultdicts
                restored[key] = defaultdict(lambda: defaultdict(int))
                for table, sources in value.items():
                    for endpoint, count in sources.items():
                        restored[key][table][endpoint] = count
            else:
                restored[key] = value
        
        return restored
    
    def _clean_timeline_data(self, timeline_list: list) -> list:
        """Clean timeline data to remove entries older than retention period."""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        cleaned = []
        for entry in timeline_list:
            if isinstance(entry, dict) and 'timestamp' in entry:
                try:
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if entry_time > cutoff_time:
                        cleaned.append(entry)
                except ValueError:
                    # Skip entries with invalid timestamps
                    continue
            else:
                # Skip entries without proper structure
                continue
        
        return cleaned
    
    def _is_data_expired(self, data: Dict[str, Any]) -> bool:
        """Check if saved data is older than retention period."""
        if 'last_saved' not in data:
            return True
        
        try:
            last_saved = datetime.fromisoformat(data['last_saved'])
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            return last_saved < cutoff_time
        except ValueError:
            return True
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default empty metrics structure."""
        return {
            'total_queries': 0,
            'query_times': deque(maxlen=100),
            'slow_queries': deque(maxlen=20),
            'query_types': defaultdict(int),
            'tables_accessed': defaultdict(int),
            'table_sources': defaultdict(lambda: defaultdict(int))
        }