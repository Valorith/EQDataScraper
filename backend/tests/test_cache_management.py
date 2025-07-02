"""
Test suite for cache management functionality.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import app


class TestCacheStorage:
    """Test cache storage and loading functionality."""
    
    def test_file_cache_save_load(self, temp_cache_dir, sample_spell_data):
        """Test saving and loading cache from files."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        current_time = datetime.now().isoformat()
        app.pricing_cache_timestamp['202'] = current_time
        
        # Force file-based cache
        with patch('app.USE_DATABASE_CACHE', False):
            app.save_cache_to_storage()
        
        # Verify files were created
        assert os.path.exists(os.path.join(temp_cache_dir, 'spells_cache.json'))
        assert os.path.exists(os.path.join(temp_cache_dir, 'cache_metadata.json'))
        
        # Clear memory and reload
        app.spells_cache.clear()
        app.cache_timestamp.clear()
        app.pricing_cache_timestamp.clear()
        
        with patch('app.USE_DATABASE_CACHE', False):
            app.load_cache_from_files()
        
        # Verify data was loaded correctly
        assert 'cleric' in app.spells_cache
        assert len(app.spells_cache['cleric']) == 2
        assert 'cleric' in app.cache_timestamp
        assert '202' in app.pricing_cache_timestamp
    
    def test_cache_directory_creation(self, temp_cache_dir):
        """Test that cache directory is created if it doesn't exist."""
        # Remove cache directory
        import shutil
        if os.path.exists(temp_cache_dir):
            shutil.rmtree(temp_cache_dir)
        
        # Force file-based cache
        with patch('app.USE_DATABASE_CACHE', False):
            app.save_cache_to_storage()
        
        # Verify directory was recreated
        assert os.path.exists(temp_cache_dir)


class TestCacheExpiry:
    """Test cache expiry logic."""
    
    def test_spell_cache_expiry(self):
        """Test spell cache expiry detection."""
        # Test fresh cache (not expired)
        fresh_time = datetime.now().isoformat()
        app.cache_timestamp['cleric'] = fresh_time
        assert app.is_cache_expired('cleric') == False
        
        # Test expired cache
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        app.cache_timestamp['cleric'] = expired_time
        assert app.is_cache_expired('cleric') == True
        
        # Test missing cache (considered expired)
        assert app.is_cache_expired('nonexistent') == True
    
    def test_pricing_cache_expiry(self):
        """Test pricing cache expiry detection."""
        # Test fresh pricing (not expired)
        fresh_time = datetime.now().isoformat()
        app.pricing_cache_timestamp['202'] = fresh_time
        assert app.is_pricing_cache_expired('202') == False
        
        # Test expired pricing (>1 week)
        expired_time = (datetime.now() - timedelta(days=8)).isoformat()
        app.pricing_cache_timestamp['202'] = expired_time
        assert app.is_pricing_cache_expired('202') == True
        
        # Test missing pricing (considered expired)
        assert app.is_pricing_cache_expired('999') == True
    
    def test_clear_expired_cache_spells(self, sample_spell_data):
        """Test clearing expired spell cache."""
        # Set up expired spell cache
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = expired_time
        app.last_scrape_time['cleric'] = expired_time
        
        # Clear expired cache
        app.clear_expired_cache()
        
        # Verify expired data was removed
        assert 'cleric' not in app.spells_cache
        assert 'cleric' not in app.cache_timestamp


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_can_scrape_class_rate_limiting(self):
        """Test rate limiting for class scraping."""
        # Test no previous scrape (can scrape)
        assert app.can_scrape_class('cleric') == True
        
        # Test recent scrape (rate limited)
        recent_time = datetime.now().isoformat()
        app.last_scrape_time['cleric'] = recent_time
        assert app.can_scrape_class('cleric') == False
        
        # Test old scrape (can scrape again)
        old_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        app.last_scrape_time['cleric'] = old_time
        assert app.can_scrape_class('cleric') == True


class TestCacheValidation:
    """Test cache validation and integrity checks."""
    
    def test_missing_cache_files_handling(self, temp_cache_dir):
        """Test handling of missing cache files."""
        # Clear all cache data
        app.spells_cache.clear()
        app.cache_timestamp.clear()
        
        # Try to load from empty directory
        with patch('app.USE_DATABASE_CACHE', False):
            app.load_cache_from_files()
        
        # Should handle gracefully without crashing
        assert isinstance(app.spells_cache, dict)
        assert isinstance(app.cache_timestamp, dict)
    
    def test_corrupted_cache_file_handling(self, temp_cache_dir):
        """Test handling of corrupted cache files."""
        # Create corrupted cache file
        corrupted_file = os.path.join(temp_cache_dir, 'spells_cache.json')
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json content}')
        
        # Should handle gracefully without crashing
        with patch('app.USE_DATABASE_CACHE', False):
            app.load_cache_from_files()
        
        assert isinstance(app.spells_cache, dict)


class TestCacheMetrics:
    """Test cache metrics and status reporting."""
    
    def test_cache_status_metrics(self, mock_app, sample_spell_data, sample_spell_details):
        """Test cache status endpoint metrics."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        app.pricing_cache_timestamp['202'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/cache/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify memory cache metrics
        assert data['memory_cache']['classes'] >= 1
        assert data['memory_cache']['spell_details'] >= 1
        assert data['memory_cache']['pricing_timestamps'] >= 1
        
        # Verify configuration
        assert 'config' in data
        assert data['config']['spell_cache_expiry_hours'] == 1  # Test config
    
    def test_health_endpoint_metrics(self, mock_app, sample_spell_data):
        """Test health endpoint cache metrics."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        
        response = mock_app.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert 'cached_classes' in data
        assert 'cached_spell_details' in data
        assert 'timestamp' in data


class TestCacheOperations:
    """Test cache operations like clear and save."""
    
    def test_manual_cache_save(self, mock_app, sample_spell_data):
        """Test manual cache save endpoint."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        
        response = mock_app.post('/api/cache/save')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['message'] == 'Cache saved successfully'
        assert 'cached_classes' in data
    
    def test_manual_cache_clear(self, mock_app, sample_spell_data):
        """Test manual cache clear endpoint."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        app.spell_details_cache['202'] = {'pricing': {'silver': 4}}
        
        response = mock_app.post('/api/cache/clear')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['message'] == 'Cache cleared successfully'
        
        # Verify cache was actually cleared
        assert len(app.spells_cache) == 0
        assert len(app.spell_details_cache) == 0


class TestDatabaseFallback:
    """Test database/file cache fallback behavior."""
    
    def test_database_unavailable_fallback(self, temp_cache_dir):
        """Test fallback to file cache when database is unavailable."""
        with patch('app.USE_DATABASE_CACHE', False):
            # Should use file-based cache without errors
            app.load_cache_from_files()
            app.save_cache_to_storage()
        
        # No exceptions should be raised
        assert True
    
    def test_cache_initialization(self):
        """Test cache initialization doesn't crash."""
        # Clear everything
        app.spells_cache.clear()
        app.spell_details_cache.clear()
        app.cache_timestamp.clear()
        
        # Initialize cache (should handle missing data gracefully)
        app.load_all_pricing_to_memory()
        
        # Should create empty but valid cache structures
        assert isinstance(app.spells_cache, dict)
        assert isinstance(app.spell_details_cache, dict)
        assert isinstance(app.pricing_lookup, dict)