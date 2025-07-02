"""
Test suite for API endpoints and data flow.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
import app


class TestSpellEndpoints:
    """Test spell-related API endpoints."""
    
    def test_get_spells_valid_class(self, mock_app, sample_spell_data):
        """Test getting spells for a valid class."""
        # Set up cached data
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/spells/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'spells' in data
        assert len(data['spells']) == 2
        assert data['cached'] == True
        assert 'last_updated' in data
        assert 'spell_count' in data
        
        # Verify spell data structure
        spell = data['spells'][0]
        required_fields = ['name', 'level', 'mana', 'skill', 'target_type', 'spell_id', 'effects', 'icon']
        for field in required_fields:
            assert field in spell
    
    def test_get_spells_invalid_class(self, mock_app):
        """Test getting spells for invalid class."""
        response = mock_app.get('/api/spells/invalidclass')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert 'error' in data
        assert 'available_classes' in data
    
    def test_get_spells_case_insensitive(self, mock_app, sample_spell_data):
        """Test class name case insensitivity."""
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        # Test various cases
        for class_name in ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']:
            response = mock_app.get(f'/api/spells/{class_name}')
            assert response.status_code == 200
    
    def test_get_classes_endpoint(self, mock_app):
        """Test get classes endpoint."""
        response = mock_app.get('/api/classes')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify class structure
        class_data = data[0]
        assert 'name' in class_data
        assert 'id' in class_data
        assert 'color' in class_data


class TestSpellDetailsEndpoints:
    """Test spell details API endpoints."""
    
    def test_get_spell_details_cached(self, mock_app, sample_spell_details):
        """Test getting cached spell details."""
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        response = mock_app.get('/api/spell-details/202')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify complete spell details
        expected_fields = ['cast_time', 'duration', 'effects', 'pricing', 'range', 'resist', 'skill', 'target_type']
        for field in expected_fields:
            assert field in data
        
        assert data['pricing']['silver'] == 4
    
    @patch('app.fetch_spell_details')
    def test_get_spell_details_fetch_new(self, mock_fetch, mock_app, sample_spell_details):
        """Test fetching new spell details."""
        # Mock the fetch function
        mock_fetch.return_value = sample_spell_details['202']
        
        response = mock_app.get('/api/spell-details/999')
        
        assert response.status_code == 200
        mock_fetch.assert_called_once_with('999')
    
    def test_spell_pricing_bulk_endpoint(self, mock_app, sample_spell_details):
        """Test bulk spell pricing endpoint."""
        # Set up cached pricing
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.spell_details_cache['203'] = sample_spell_details['203']
        app.pricing_lookup['202'] = sample_spell_details['202']['pricing']
        app.pricing_lookup['203'] = sample_spell_details['203']['pricing']
        
        request_data = {'spell_ids': ['202', '203']}
        response = mock_app.post('/api/spell-pricing', 
                                json=request_data,
                                content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'pricing' in data
        assert '202' in data['pricing']
        assert '203' in data['pricing']
        assert data['pricing']['202']['silver'] == 4
        assert 'cached_count' in data


class TestCacheStatusEndpoints:
    """Test cache status and management endpoints."""
    
    def test_cache_status_endpoint(self, mock_app, sample_spell_data):
        """Test cache status endpoint."""
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/cache-status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'cleric' in data
        assert data['cleric']['cached'] == True
        assert data['cleric']['spell_count'] == 2
        assert '_config' in data
        
        # Verify config values
        config = data['_config']
        assert 'spell_cache_expiry_hours' in config
        assert 'pricing_cache_expiry_hours' in config
    
    def test_cache_expiry_status_endpoint(self, mock_app, sample_spell_data, sample_spell_details):
        """Test cache expiry status endpoint."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        app.spell_details_cache['202'] = sample_spell_details['202']
        app.pricing_cache_timestamp['202'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/cache-expiry-status/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify structure
        assert 'class_name' in data
        assert 'spells' in data
        assert 'pricing' in data
        assert 'expiry_config' in data
        
        # Verify spell data
        assert data['spells']['cached'] == True
        assert data['spells']['expired'] == False
        
        # Verify pricing data
        assert data['pricing']['cached_count'] >= 1
        assert data['pricing']['total_spells'] == 2


class TestSearchEndpoints:
    """Test search functionality."""
    
    def test_search_spells_endpoint(self, mock_app, sample_spell_data):
        """Test spell search endpoint."""
        # Set up search data
        app.spells_cache['cleric'] = sample_spell_data
        
        response = mock_app.get('/api/search-spells?q=courage')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        if len(data) > 0:
            spell = data[0]
            assert 'name' in spell
            assert 'spell_id' in spell
            assert 'classes' in spell
    
    def test_search_spells_no_query(self, mock_app):
        """Test search endpoint with no query."""
        response = mock_app.get('/api/search-spells')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_search_spells_empty_query(self, mock_app):
        """Test search endpoint with empty query."""
        response = mock_app.get('/api/search-spells?q=')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestRefreshEndpoints:
    """Test cache refresh endpoints."""
    
    def test_refresh_spell_cache_endpoint(self, mock_app):
        """Test refresh spell cache endpoint."""
        with patch('app.scrape_class') as mock_scrape:
            mock_scrape.return_value = [{'name': 'Test Spell', 'spell_id': '123'}]
            
            response = mock_app.post('/api/refresh-spell-cache/cleric')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] == True
            assert 'spell_count' in data
    
    def test_refresh_pricing_cache_endpoint(self, mock_app, sample_spell_data):
        """Test refresh pricing cache endpoint."""
        # Set up test data
        app.spells_cache['cleric'] = sample_spell_data
        app.pricing_cache_timestamp['202'] = datetime.now().isoformat()
        
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] == True
        assert 'cleared_count' in data
        assert 'total_spells' in data


class TestErrorHandling:
    """Test API error handling."""
    
    def test_invalid_spell_id_format(self, mock_app):
        """Test handling of invalid spell ID formats."""
        response = mock_app.get('/api/spell-details/invalid_id')
        
        # Should handle gracefully (may return 404 or empty data)
        assert response.status_code in [200, 404, 500]
    
    def test_missing_request_data(self, mock_app):
        """Test handling of missing request data."""
        response = mock_app.post('/api/spell-pricing',
                                content_type='application/json')
        
        # Should handle missing JSON gracefully
        assert response.status_code in [400, 500]
    
    def test_malformed_json_request(self, mock_app):
        """Test handling of malformed JSON."""
        response = mock_app.post('/api/spell-pricing',
                                data='invalid json',
                                content_type='application/json')
        
        # Should handle malformed JSON gracefully
        assert response.status_code in [400, 500]


class TestDataValidation:
    """Test data validation in API responses."""
    
    def test_spell_data_validation(self, mock_app, sample_spell_data):
        """Test that spell data contains required fields."""
        app.spells_cache['cleric'] = sample_spell_data
        app.cache_timestamp['cleric'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/spells/cleric')
        data = json.loads(response.data)
        
        for spell in data['spells']:
            # Verify required fields are present
            assert isinstance(spell['name'], str)
            assert isinstance(spell['level'], int)
            assert isinstance(spell['spell_id'], str)
            
            # Verify optional fields are handled properly
            assert spell.get('pricing') is None or isinstance(spell['pricing'], dict)
    
    def test_pricing_data_validation(self, mock_app, sample_spell_details):
        """Test that pricing data has correct structure."""
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        response = mock_app.get('/api/spell-details/202')
        data = json.loads(response.data)
        
        pricing = data['pricing']
        
        # Verify pricing structure
        assert isinstance(pricing['platinum'], int)
        assert isinstance(pricing['gold'], int)
        assert isinstance(pricing['silver'], int)
        assert isinstance(pricing['bronze'], int)
        
        # Unknown field should be boolean if present
        if 'unknown' in pricing:
            assert isinstance(pricing['unknown'], bool)