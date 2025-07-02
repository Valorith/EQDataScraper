"""
Test suite for the pricing system - critical component that had bugs during deprecation.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import app


class TestPricingCache:
    """Test pricing cache functionality."""
    
    def test_fetch_single_spell_pricing_success(self, mock_requests, sample_spell_details):
        """Test successful pricing fetch stores data correctly."""
        # Clear cache
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        app.pricing_cache_timestamp.clear()
        
        # Mock successful response
        mock_requests.return_value.text = """
        <table>
            <tr><td>Vendor Price:</td><td>4 silver</td></tr>
        </table>
        """
        
        with patch('app.parse_spell_details_from_html') as mock_parse:
            mock_parse.return_value = sample_spell_details['202']
            
            result = app.fetch_single_spell_pricing('202')
            
            # Verify result
            assert result['silver'] == 4
            assert result['unknown'] == False
            
            # Verify data was cached correctly
            assert '202' in app.spell_details_cache
            assert '202' in app.pricing_lookup
            assert '202' in app.pricing_cache_timestamp
            
            # Verify cache contents
            assert app.spell_details_cache['202']['pricing']['silver'] == 4
            assert app.pricing_lookup['202']['silver'] == 4
    
    def test_fetch_single_spell_pricing_failure(self, mock_requests):
        """Test pricing fetch failure stores unknown pricing."""
        # Clear cache
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        app.pricing_cache_timestamp.clear()
        
        # Mock failed response
        mock_requests.return_value.status_code = 404
        
        result = app.fetch_single_spell_pricing('999')
        
        # Verify unknown result
        assert result['unknown'] == True
        assert result['silver'] == 0
        
        # Verify failed data was cached
        assert '999' in app.spell_details_cache
        assert '999' in app.pricing_lookup
        assert '999' in app.pricing_cache_timestamp
        
        assert app.spell_details_cache['999']['pricing']['unknown'] == True
    
    def test_pricing_cache_expiry(self, sample_spell_details):
        """Test pricing cache expiry logic."""
        # Set up expired timestamp
        expired_time = (datetime.now() - timedelta(days=8)).isoformat()
        app.pricing_cache_timestamp['202'] = expired_time
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        # Test expiry check
        assert app.is_pricing_cache_expired('202') == True
        
        # Test non-expired
        fresh_time = datetime.now().isoformat()
        app.pricing_cache_timestamp['203'] = fresh_time
        assert app.is_pricing_cache_expired('203') == False
    
    def test_clear_expired_cache_pricing(self, sample_spell_details):
        """Test that expired pricing cache is properly cleared."""
        # Set up expired pricing data
        expired_time = (datetime.now() - timedelta(days=8)).isoformat()
        app.pricing_cache_timestamp['202'] = expired_time
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.pricing_lookup['202'] = sample_spell_details['202']['pricing']
        
        # Clear expired cache
        app.clear_expired_cache()
        
        # Verify expired data was removed
        assert '202' not in app.pricing_cache_timestamp
        assert '202' not in app.pricing_lookup
        # spell_details_cache should have pricing removed but entry preserved if other data exists
        if '202' in app.spell_details_cache:
            assert 'pricing' not in app.spell_details_cache['202']


class TestCacheRefresh:
    """Test cache refresh functionality."""
    
    def test_refresh_pricing_cache_clears_all_data(self, mock_app, sample_spell_details):
        """Test that pricing cache refresh clears all related data."""
        # Set up data in all storage locations
        app.spells_cache['cleric'] = [{'spell_id': '202'}, {'spell_id': '203'}]
        app.pricing_cache_timestamp['202'] = datetime.now().isoformat()
        app.pricing_cache_timestamp['203'] = datetime.now().isoformat()
        app.pricing_lookup['202'] = {'silver': 4}
        app.pricing_lookup['203'] = {'silver': 4}
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.spell_details_cache['203'] = sample_spell_details['203']
        
        # Refresh pricing cache
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['cleared_count'] == 2
        
        # Verify data was cleared
        assert '202' not in app.pricing_cache_timestamp
        assert '203' not in app.pricing_cache_timestamp
        assert '202' not in app.pricing_lookup
        assert '203' not in app.pricing_lookup


class TestCacheStatusEndpoint:
    """Test cache status endpoint functionality."""
    
    def test_cache_expiry_status_with_pricing(self, mock_app, sample_spell_details):
        """Test cache expiry status endpoint with pricing data."""
        # Set up test data
        app.spells_cache['cleric'] = [
            {'spell_id': '202'},
            {'spell_id': '203'},
            {'spell_id': '999'}  # No pricing
        ]
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        # Add pricing data for some spells
        current_time = datetime.now().isoformat()
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.spell_details_cache['203'] = sample_spell_details['203']
        app.pricing_cache_timestamp['202'] = current_time
        app.pricing_cache_timestamp['203'] = current_time
        
        response = mock_app.get('/api/cache-expiry-status/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify pricing data
        assert data['pricing']['cached_count'] == 2
        assert data['pricing']['total_spells'] == 3
        assert data['pricing']['most_recent_timestamp'] is not None
        
        # Verify spell data
        assert data['spells']['cached'] == True
        assert data['spells']['count'] == 3
    
    def test_missing_timestamp_auto_creation(self, mock_app, sample_spell_details):
        """Test that missing timestamps are automatically created."""
        # Set up pricing data without timestamps
        app.spells_cache['cleric'] = [{'spell_id': '202'}]
        app.spell_details_cache['202'] = sample_spell_details['202']
        # Deliberately don't set pricing_cache_timestamp
        
        response = mock_app.get('/api/cache-expiry-status/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should auto-create timestamp and count the pricing
        assert data['pricing']['cached_count'] == 1
        assert data['pricing']['most_recent_timestamp'] is not None
        assert '202' in app.pricing_cache_timestamp


class TestAPIEndpoints:
    """Test API endpoints return correct data."""
    
    def test_spells_endpoint_with_pricing(self, mock_app, sample_spell_data, sample_spell_details):
        """Test spells endpoint returns pricing data."""
        # Set up cache data
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        # Add pricing data
        for spell_id in ['202', '203']:
            app.spell_details_cache[spell_id] = sample_spell_details[spell_id]
            app.pricing_lookup[spell_id] = sample_spell_details[spell_id]['pricing']
        
        response = mock_app.get('/api/spells/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify spells have pricing data applied
        spells = data['spells']
        assert len(spells) == 2
        
        # Find spells by ID and check pricing
        spell_202 = next(s for s in spells if s['spell_id'] == '202')
        assert spell_202['pricing']['silver'] == 4
        assert spell_202['pricing']['unknown'] == False
    
    def test_spell_details_endpoint(self, mock_app, sample_spell_details):
        """Test spell details endpoint."""
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        response = mock_app.get('/api/spell-details/202')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify complete spell details
        assert data['cast_time'] == '1.5 sec'
        assert data['pricing']['silver'] == 4
        assert data['pricing']['unknown'] == False
    
    def test_health_endpoint(self, mock_app, sample_spell_details):
        """Test health endpoint shows correct cache counts."""
        # Set up some cache data
        app.spells_cache['cleric'] = [{'spell_id': '202'}]
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        response = mock_app.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert data['cached_classes'] == 1
        assert data['cached_pricing'] == 0  # Deprecated pricing_cache
        assert data['cached_spell_details'] == 1


class TestDataConsistency:
    """Test data consistency across storage systems."""
    
    def test_pricing_lookup_sync(self, sample_spell_details):
        """Test that pricing_lookup stays in sync with spell_details_cache."""
        # Clear everything
        app.spell_details_cache.clear()
        app.pricing_lookup.clear()
        
        # Add to spell_details_cache
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        # Rebuild pricing lookup
        app.rebuild_pricing_lookup_index()
        
        # Verify sync
        assert '202' in app.pricing_lookup
        assert app.pricing_lookup['202']['silver'] == 4
    
    def test_cache_save_load_consistency(self, temp_cache_dir):
        """Test that cache save/load maintains data consistency."""
        # Set up data
        app.spell_details_cache['202'] = {'pricing': {'silver': 4}}
        app.pricing_cache_timestamp['202'] = datetime.now().isoformat()
        
        # Save to files
        with patch('app.USE_DATABASE_CACHE', False):
            app.save_cache_to_storage()
        
        # Clear memory
        app.spell_details_cache.clear()
        app.pricing_cache_timestamp.clear()
        
        # Load from files
        with patch('app.USE_DATABASE_CACHE', False):
            app.load_cache_from_files()
        
        # Verify data integrity
        assert '202' in app.spell_details_cache
        assert '202' in app.pricing_cache_timestamp
        assert app.spell_details_cache['202']['pricing']['silver'] == 4