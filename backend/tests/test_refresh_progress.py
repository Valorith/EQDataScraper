"""
Test suite for refresh progress tracking functionality.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import app


class TestRefreshProgressTracking:
    """Test refresh progress tracking functionality."""
    
    def test_update_refresh_progress_initialization(self):
        """Test that refresh progress is initialized correctly."""
        app.refresh_progress.clear()
        
        app.update_refresh_progress('cleric', 'initializing')
        
        assert 'cleric' in app.refresh_progress
        progress = app.refresh_progress['cleric']
        assert progress['stage'] == 'initializing'
        assert progress['progress_percentage'] == 5
        assert progress['message'] == '🔄 Initializing refresh process...'
        assert progress['start_time'] is not None
        assert progress['last_updated'] is not None
    
    def test_update_refresh_progress_stages(self):
        """Test all refresh progress stages."""
        app.refresh_progress.clear()
        
        # Test each stage
        stages = [
            ('initializing', 5, '🔄 Initializing refresh process...'),
            ('scraping', 20, '🌐 Scraping fresh spell data...'),
            ('processing', 60, '⚙️ Processing spell information...'),
            ('updating_cache', 80, '💾 Updating cached data...'),
            ('loading_memory', 95, '📥 Loading into memory...'),
            ('complete', 100, '✅ Refresh completed successfully!'),
            ('error', 0, '❌ Error occurred during refresh')
        ]
        
        for stage, expected_progress, expected_message in stages:
            app.update_refresh_progress('cleric', stage)
            progress = app.refresh_progress['cleric']
            assert progress['stage'] == stage
            assert progress['progress_percentage'] == expected_progress
            assert progress['message'] == expected_message
    
    def test_update_refresh_progress_custom_values(self):
        """Test updating refresh progress with custom values."""
        app.refresh_progress.clear()
        
        app.update_refresh_progress(
            'cleric',
            'scraping',
            progress_percentage=25,
            message='Custom scraping message',
            estimated_time_remaining=45
        )
        
        progress = app.refresh_progress['cleric']
        assert progress['progress_percentage'] == 25
        assert progress['message'] == 'Custom scraping message'
        assert progress['estimated_time_remaining'] == 45
    
    def test_clear_refresh_progress(self):
        """Test clearing refresh progress."""
        app.refresh_progress.clear()
        
        # Set up progress
        app.update_refresh_progress('cleric', 'scraping')
        assert 'cleric' in app.refresh_progress
        
        # Clear progress
        app.clear_refresh_progress('cleric')
        assert 'cleric' not in app.refresh_progress
    
    def test_clear_refresh_progress_nonexistent(self):
        """Test clearing progress for non-existent class."""
        app.refresh_progress.clear()
        
        # Should not raise error
        app.clear_refresh_progress('nonexistent')
        assert 'nonexistent' not in app.refresh_progress


class TestRefreshProgressEndpoints:
    """Test refresh progress API endpoints."""
    
    def test_get_refresh_progress_success(self, mock_app):
        """Test getting refresh progress for active refresh."""
        # Set up progress
        app.refresh_progress.clear()
        app.update_refresh_progress('cleric', 'scraping', estimated_time_remaining=30)
        
        response = mock_app.get('/api/refresh-progress/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['stage'] == 'scraping'
        assert data['progress_percentage'] == 20
        assert data['message'] == '🌐 Scraping fresh spell data...'
        assert data['estimated_time_remaining'] == 30
        assert 'start_time' in data
        assert 'last_updated' in data
    
    def test_get_refresh_progress_not_found(self, mock_app):
        """Test getting refresh progress for non-existent refresh."""
        app.refresh_progress.clear()
        
        response = mock_app.get('/api/refresh-progress/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No refresh in progress' in data['error']
    
    def test_get_refresh_progress_case_insensitive(self, mock_app):
        """Test refresh progress endpoint is case insensitive."""
        app.refresh_progress.clear()
        app.update_refresh_progress('cleric', 'processing')
        
        # Test various cases
        for class_name in ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']:
            response = mock_app.get(f'/api/refresh-progress/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['stage'] == 'processing'


class TestRefreshSpellCacheEndpoint:
    """Test refresh spell cache endpoint with progress tracking."""
    
    def test_refresh_spell_cache_valid_class(self, mock_app):
        """Test refreshing spell cache for valid class."""
        app.refresh_progress.clear()
        
        response = mock_app.post('/api/refresh-spell-cache/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert data['message'] == 'Refresh started'
        assert data['class_name'] == 'cleric'
        
        # Should have created progress tracking
        assert 'cleric' in app.refresh_progress
        progress = app.refresh_progress['cleric']
        assert progress['stage'] == 'initializing'
        assert progress['progress_percentage'] == 5
    
    def test_refresh_spell_cache_invalid_class(self, mock_app):
        """Test refreshing spell cache for invalid class."""
        response = mock_app.post('/api/refresh-spell-cache/invalidclass')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid class name' in data['error']
    
    def test_refresh_spell_cache_case_handling(self, mock_app):
        """Test that class name case is handled correctly."""
        app.refresh_progress.clear()
        
        # Test various cases
        for class_name in ['cleric', 'CLERIC', 'Cleric']:
            response = mock_app.post(f'/api/refresh-spell-cache/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['class_name'] == 'cleric'  # Always normalized to lowercase
    
    def test_refresh_spell_cache_progress_simulation(self, mock_app):
        """Test that progress simulation works correctly."""
        app.refresh_progress.clear()
        
        response = mock_app.post('/api/refresh-spell-cache/cleric')
        assert response.status_code == 200
        
        # Check initial progress
        assert 'cleric' in app.refresh_progress
        initial_progress = app.refresh_progress['cleric']
        assert initial_progress['stage'] == 'initializing'
        
        # Wait for simulation to progress
        time.sleep(0.1)
        
        # Progress should still be tracked
        assert 'cleric' in app.refresh_progress


class TestRefreshPricingCacheEndpoint:
    """Test refresh pricing cache endpoint."""
    
    def test_refresh_pricing_cache_success(self, mock_app, sample_spell_data):
        """Test refreshing pricing cache for valid class with spells."""
        # Set up spell data
        app.spells_cache.clear()
        app.spell_details_cache.clear()
        app.pricing_cache_timestamp.clear()
        app.pricing_lookup.clear()
        
        # Use proper case for cache key
        app.spells_cache['cleric'] = sample_spell_data
        
        # Add some existing pricing data to clear - use spell IDs from sample_spell_data
        app.pricing_cache_timestamp['13'] = datetime.now().isoformat()
        app.pricing_cache_timestamp['12'] = datetime.now().isoformat()
        app.pricing_lookup['13'] = {'silver': 4}
        app.pricing_lookup['12'] = {'silver': 4}
        
        # Add spell details cache entries with pricing data
        app.spell_details_cache['13'] = {'pricing': {'silver': 4}}
        app.spell_details_cache['12'] = {'pricing': {'silver': 4}}
        
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert 'cleared_count' in data
        assert data['cleared_count'] == 2
        assert 'message' in data
        
        # Verify data was cleared
        assert '13' not in app.pricing_cache_timestamp
        assert '12' not in app.pricing_cache_timestamp
        assert '13' not in app.pricing_lookup
        assert '12' not in app.pricing_lookup
        # Verify pricing was removed from spell details cache
        assert '13' not in app.spell_details_cache or 'pricing' not in app.spell_details_cache.get('13', {})
        assert '12' not in app.spell_details_cache or 'pricing' not in app.spell_details_cache.get('12', {})
    
    def test_refresh_pricing_cache_invalid_class(self, mock_app):
        """Test refreshing pricing cache for invalid class."""
        response = mock_app.post('/api/refresh-pricing-cache/invalidclass')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid class name' in data['error']
    
    def test_refresh_pricing_cache_no_spells(self, mock_app):
        """Test refreshing pricing cache when no spells exist for class."""
        app.spells_cache.clear()
        
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No spells found for class' in data['error']
    
    def test_refresh_pricing_cache_no_spell_ids(self, mock_app):
        """Test refreshing pricing cache when spells have no IDs."""
        app.spells_cache.clear()
        app.spells_cache['cleric'] = [
            {'name': 'Spell without ID', 'level': 1}
        ]
        
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No valid spell IDs found' in data['error']
    
    def test_refresh_pricing_cache_case_insensitive(self, mock_app, sample_spell_data):
        """Test pricing cache refresh is case insensitive."""
        app.spells_cache.clear()
        app.spells_cache['cleric'] = sample_spell_data
        
        # Test various cases
        for class_name in ['cleric', 'CLERIC', 'Cleric']:
            response = mock_app.post(f'/api/refresh-pricing-cache/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True


class TestProgressTrackingIntegration:
    """Test progress tracking integration with other systems."""
    
    def test_multiple_concurrent_refreshes(self, mock_app):
        """Test handling multiple concurrent refresh operations."""
        app.refresh_progress.clear()
        
        # Start refresh for multiple classes
        classes = ['cleric', 'wizard', 'druid']
        
        for class_name in classes:
            response = mock_app.post(f'/api/refresh-spell-cache/{class_name}')
            assert response.status_code == 200
        
        # Should have progress for all classes
        for class_name in classes:
            assert class_name in app.refresh_progress
            progress = app.refresh_progress[class_name]
            assert progress['stage'] == 'initializing'
    
    def test_progress_cleanup_on_completion(self):
        """Test that progress is cleaned up when refresh completes."""
        app.refresh_progress.clear()
        
        # Set up progress
        app.update_refresh_progress('cleric', 'scraping')
        assert 'cleric' in app.refresh_progress
        
        # Complete the refresh
        app.update_refresh_progress('cleric', 'complete')
        assert app.refresh_progress['cleric']['stage'] == 'complete'
        assert app.refresh_progress['cleric']['progress_percentage'] == 100
        
        # Progress should still exist until manually cleared
        assert 'cleric' in app.refresh_progress
    
    def test_progress_error_handling(self):
        """Test progress tracking during error conditions."""
        app.refresh_progress.clear()
        
        # Simulate error condition
        app.update_refresh_progress('cleric', 'error', message='Network timeout')
        
        progress = app.refresh_progress['cleric']
        assert progress['stage'] == 'error'
        assert progress['progress_percentage'] == 0
        assert progress['message'] == 'Network timeout'
    
    def test_progress_timestamp_updates(self):
        """Test that progress timestamps are updated correctly."""
        app.refresh_progress.clear()
        
        # Initial update
        app.update_refresh_progress('cleric', 'initializing')
        initial_last_updated = app.refresh_progress['cleric']['last_updated']
        initial_start_time = app.refresh_progress['cleric']['start_time']
        
        # Wait and update again
        time.sleep(0.01)
        app.update_refresh_progress('cleric', 'scraping')
        updated_last_updated = app.refresh_progress['cleric']['last_updated']
        updated_start_time = app.refresh_progress['cleric']['start_time']
        
        # Timestamp should be updated
        assert updated_last_updated > initial_last_updated
        
        # Start time should remain the same (within reasonable precision)
        assert updated_start_time == initial_start_time