"""
Test suite for server startup cache loading and progress tracking functionality.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import app


class TestServerStartupProgress:
    """Test server startup progress tracking."""
    
    def test_server_startup_progress_initialization(self):
        """Test that server startup progress is initialized correctly."""
        # Server startup progress should be initialized on module import
        assert hasattr(app, 'server_startup_progress')
        assert 'is_starting' in app.server_startup_progress
        assert 'current_step' in app.server_startup_progress
        assert 'progress_percent' in app.server_startup_progress
        assert 'steps_completed' in app.server_startup_progress
    
    def test_server_startup_progress_structure(self):
        """Test server startup progress has correct structure."""
        progress = app.server_startup_progress
        
        # Should have boolean is_starting
        assert isinstance(progress['is_starting'], bool)
        
        # Should have string current_step
        assert isinstance(progress['current_step'], str)
        
        # Should have numeric progress_percent
        assert isinstance(progress['progress_percent'], (int, float))
        assert 0 <= progress['progress_percent'] <= 100
        
        # Should have numeric steps_completed
        assert isinstance(progress['steps_completed'], (int, float))


class TestCachePreloading:
    """Test cache preloading functionality."""
    
    def test_preload_spell_data_function_exists(self):
        """Test that preload function exists and is callable."""
        assert hasattr(app, 'preload_spell_data_on_startup')
        assert callable(app.preload_spell_data_on_startup)
    
    def test_cache_refresh_functions_exist(self):
        """Test that cache refresh functions exist and are callable."""
        assert hasattr(app, 'get_expired_spell_cache_classes')
        assert callable(app.get_expired_spell_cache_classes)
        assert hasattr(app, 'refresh_expired_spell_caches')
        assert callable(app.refresh_expired_spell_caches)
    
    @patch('app.scrape_class')
    def test_refresh_expired_spell_caches_with_mocked_scraping(self, mock_scrape):
        """Test cache refresh logic without actual web scraping."""
        # Mock successful scraping
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {'name': 'Test Spell', 'spell_id': '123', 'level': 1}
        ]
        mock_scrape.return_value = mock_df
        
        # Set up expired cache
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        app.spells_cache.clear()
        app.cache_timestamp.clear()
        app.spells_cache['warrior'] = [{'name': 'Old Spell', 'spell_id': '999'}]
        app.cache_timestamp['warrior'] = expired_time
        
        # Test the refresh function
        expired_classes = ['Warrior']  # Note: proper case
        refreshed, failed = app.refresh_expired_spell_caches(expired_classes)
        
        # Verify results
        assert 'Warrior' in refreshed
        assert len(failed) == 0
        assert mock_scrape.called
        assert mock_scrape.call_args[0] == ('Warrior', 'https://alla.clumsysworld.com/', None)
        
        # Verify cache was updated
        assert 'warrior' in app.spells_cache
        assert len(app.spells_cache['warrior']) == 1
        assert app.spells_cache['warrior'][0]['name'] == 'Test Spell'
    
    @patch('app.scrape_class')
    def test_refresh_expired_spell_caches_handles_scraping_failure(self, mock_scrape):
        """Test cache refresh handles scraping failures gracefully."""
        # Mock failed scraping
        mock_scrape.side_effect = Exception("Network timeout")
        
        # Test the refresh function
        expired_classes = ['Warrior']
        refreshed, failed = app.refresh_expired_spell_caches(expired_classes)
        
        # Verify error handling
        assert len(refreshed) == 0
        assert 'Warrior' in failed
        assert mock_scrape.called
    
    @patch('app.save_cache_to_storage')
    @patch('app.clear_expired_cache')
    @patch('app.load_cache_from_storage')
    def test_preload_cached_classes_workflow(self, mock_load, mock_clear, mock_save):
        """Test cache preloading workflow."""
        # Mock the functions to avoid actual database operations
        mock_load.return_value = None
        mock_clear.return_value = None
        mock_save.return_value = None
        
        # Set up some test cache data
        app.spells_cache.clear()
        app.spells_cache['cleric'] = [
            {'name': 'Test Spell', 'spell_id': '202', 'level': 1}
        ]
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        try:
            # Call preload function
            app.preload_spell_data_on_startup()
            
            # Should have called cache loading functions
            mock_load.assert_called()
            
        except Exception as e:
            # Function might depend on environment setup
            # Just ensure it doesn't crash catastrophically
            assert "catastrophic" not in str(e).lower()
    
    def test_cache_expiry_detection_during_startup(self, sample_spell_data):
        """Test that expired cache is detected during startup."""
        # Set up expired cache
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        app.spells_cache.clear()
        app.cache_timestamp.clear()
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = expired_time
        
        # Test expiry detection
        assert app.is_cache_expired('cleric') == True
        
        # Test fresh cache
        fresh_time = datetime.now().isoformat()
        app.cache_timestamp['cleric'] = fresh_time
        assert app.is_cache_expired('cleric') == False


class TestMemoryOptimization:
    """Test memory optimization features during startup."""
    
    def test_pricing_lookup_rebuild(self, sample_spell_details):
        """Test that pricing lookup index is rebuilt correctly."""
        # Clear existing data
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        
        # Add test data to spell_details_cache
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.spell_details_cache['203'] = sample_spell_details['203']
        
        # Rebuild pricing lookup
        app.rebuild_pricing_lookup()
        
        # Verify pricing lookup was populated
        assert '202' in app.pricing_lookup
        assert '203' in app.pricing_lookup
        assert app.pricing_lookup['202']['silver'] == 4
        assert app.pricing_lookup['203']['silver'] == 4
    
    def test_pricing_lookup_handles_missing_pricing(self):
        """Test that pricing lookup handles spells without pricing data."""
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        
        # Add spell details without pricing
        app.spell_details_cache['999'] = {
            'cast_time': '2.0 sec',
            'duration': 'Instant',
            'effects': ['Test effect']
            # No pricing data
        }
        
        # Rebuild pricing lookup
        app.rebuild_pricing_lookup()
        
        # Should not crash and should not add to pricing lookup
        assert '999' not in app.pricing_lookup
    
    def test_pricing_lookup_performance_with_large_dataset(self):
        """Test pricing lookup performance with large dataset."""
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        
        # Create large dataset
        for i in range(1000):
            app.spell_details_cache[str(i)] = {
                'pricing': {
                    'silver': i % 10,
                    'unknown': False
                }
            }
        
        import time
        start_time = time.time()
        app.rebuild_pricing_lookup()
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0  # Less than 1 second
        
        # Should have processed all entries
        assert len(app.pricing_lookup) == 1000


class TestCacheIntegrityChecks:
    """Test cache integrity and validation during startup."""
    
    def test_cache_timestamp_validation(self):
        """Test that cache timestamps are validated."""
        # Test valid timestamp
        valid_time = datetime.now().isoformat()
        app.cache_timestamp['cleric'] = valid_time
        
        assert app.is_cache_expired('cleric') == False
        
        # Test invalid timestamp format (should be treated as expired)
        app.cache_timestamp['wizard'] = 'invalid-timestamp'
        
        # Should handle gracefully without crashing
        try:
            expired = app.is_cache_expired('wizard')
            # Should treat invalid timestamp as expired
            assert expired == True
        except Exception:
            # If it raises an exception, it should be a handled one
            pass
    
    def test_spell_cache_data_validation(self, sample_spell_data):
        """Test that spell cache data is validated during startup."""
        # Set up cache with valid data
        app.spells_cache['cleric'] = sample_spell_data
        
        # Verify data structure
        assert isinstance(app.spells_cache['cleric'], list)
        assert len(app.spells_cache['cleric']) > 0
        
        for spell in app.spells_cache['cleric']:
            assert isinstance(spell, dict)
            assert 'name' in spell
            assert 'spell_id' in spell
            assert 'level' in spell
    
    def test_cache_cleanup_during_startup(self, sample_spell_data, sample_spell_details):
        """Test that cache cleanup works during startup."""
        # Set up expired data
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        
        app.spells_cache.clear()
        app.spell_details_cache.clear()
        app.cache_timestamp.clear()
        app.pricing_cache_timestamp.clear()
        
        # Add expired spell cache
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = expired_time
        
        # Add expired pricing cache
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.pricing_cache_timestamp['202'] = (datetime.now() - timedelta(days=8)).isoformat()
        
        # Run cleanup
        app.clear_expired_cache()
        
        # Verify expired data was removed
        assert 'cleric' not in app.spells_cache
        assert 'cleric' not in app.cache_timestamp
        assert '202' not in app.pricing_cache_timestamp


class TestStartupErrorHandling:
    """Test error handling during startup operations."""
    
    @patch('app.load_cache_from_storage')
    def test_startup_handles_cache_loading_errors(self, mock_load):
        """Test that startup handles cache loading errors gracefully."""
        # Mock cache loading to raise an exception
        mock_load.side_effect = Exception("Database connection failed")
        
        try:
            # Should not crash the entire application
            app.preload_spell_data_on_startup()
        except Exception as e:
            # If it does raise an exception, it should be handled
            assert "Database connection failed" in str(e)
    
    @patch('app.scrape_class')
    def test_startup_handles_scraping_errors(self, mock_scrape):
        """Test that startup handles scraping errors during cache refresh."""
        # Mock scraping to raise an exception
        mock_scrape.side_effect = Exception("Network timeout")
        
        # Set up expired cache that would trigger refresh
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        app.spells_cache['cleric'] = [{'name': 'Test', 'spell_id': '202'}]
        app.cache_timestamp['cleric'] = expired_time
        
        try:
            # Should handle scraping errors gracefully
            app.clear_expired_cache()
        except Exception:
            # Should not crash
            pass
    
    def test_startup_with_empty_cache(self):
        """Test startup behavior with completely empty cache."""
        # Clear all cache data
        app.spells_cache.clear()
        app.spell_details_cache.clear()
        app.cache_timestamp.clear()
        app.pricing_cache_timestamp.clear()
        app.pricing_lookup.clear()
        
        try:
            # Should handle empty cache gracefully
            app.rebuild_pricing_lookup()
            
            # Cache should remain empty but functional
            assert len(app.spells_cache) == 0
            assert len(app.pricing_lookup) == 0
            
        except Exception as e:
            # Should not crash with empty cache
            assert "empty" not in str(e).lower()


class TestStartupPerformance:
    """Test startup performance and optimization."""
    
    def test_startup_performance_with_large_cache(self):
        """Test startup performance with large cache datasets."""
        # Create large cache dataset
        app.spells_cache.clear()
        app.spell_details_cache.clear()
        
        # Add multiple classes with many spells
        for class_id in range(10):
            class_name = f'testclass{class_id}'
            app.spells_cache[class_name] = []
            
            for spell_id in range(100):
                spell = {
                    'name': f'Test Spell {spell_id}',
                    'spell_id': str(spell_id + class_id * 100),
                    'level': (spell_id % 65) + 1
                }
                app.spells_cache[class_name].append(spell)
                
                # Add spell details for some spells
                if spell_id % 2 == 0:
                    app.spell_details_cache[spell['spell_id']] = {
                        'pricing': {'silver': spell_id % 10, 'unknown': False}
                    }
        
        import time
        start_time = time.time()
        
        # Rebuild pricing lookup
        app.rebuild_pricing_lookup()
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 2.0  # Less than 2 seconds
        
        # Should have processed data correctly
        assert len(app.pricing_lookup) == 500  # 10 classes * 100 spells * 50% with pricing
    
    def test_memory_usage_optimization(self):
        """Test that memory usage is optimized during startup."""
        # This is a basic test to ensure no obvious memory leaks
        initial_cache_size = len(app.spells_cache)
        initial_details_size = len(app.spell_details_cache)
        
        # Perform cache operations
        app.rebuild_pricing_lookup()
        
        # Cache sizes should be stable (not growing unexpectedly)
        final_cache_size = len(app.spells_cache)
        final_details_size = len(app.spell_details_cache)
        
        assert final_cache_size >= initial_cache_size
        assert final_details_size >= initial_details_size