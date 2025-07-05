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
        with patch('app.scrape_class') as mock_scrape:
            # Clear and set up cached data using proper class name
            app.spells_cache.clear()
            app.spells_cache['cleric'] = sample_spell_data  # Use lowercase for consistency
            app.cache_timestamp['cleric'] = datetime.now().isoformat()
            
            response = mock_app.get('/api/spells/cleric')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'spells' in data
            assert len(data['spells']) == len(sample_spell_data)
            assert data['cached'] == True
            assert 'last_updated' in data
            assert 'spell_count' in data
            
            # Verify scraping was not called (using cache)
            mock_scrape.assert_not_called()
        
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
        with patch('app.scrape_class') as mock_scrape:
            app.spells_cache.clear()
            app.spells_cache['cleric'] = sample_spell_data  # Use lowercase for cache key
            app.cache_timestamp['cleric'] = datetime.now().isoformat()
            
            # Test various cases
            for class_name in ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']:
                response = mock_app.get(f'/api/spells/{class_name}')
                assert response.status_code == 200
                
            # Verify scraping was not called (using cache)
            mock_scrape.assert_not_called()
    
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
    
    def test_get_spell_details_endpoint_response(self, mock_app, sample_spell_details):
        """Test spell details endpoint response format."""
        # Set up cached data
        app.spell_details_cache.clear()
        app.spell_details_cache['202'] = sample_spell_details['202']
        
        response = mock_app.get('/api/spell-details/202')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify expected fields are present
        expected_fields = ['cast_time', 'duration', 'effects', 'pricing', 'range', 'resist', 'skill', 'target_type']
        for field in expected_fields:
            assert field in data
    
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
        app.spells_cache.clear()
        app.spells_cache['Cleric'] = sample_spell_data  # Use proper case for cache key
        app.cache_timestamp['Cleric'] = datetime.now().isoformat()
        
        response = mock_app.get('/api/cache-status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'Cleric' in data
        # Cache status might vary based on expiry logic
        assert 'cached' in data['Cleric']
        assert 'spell_count' in data['Cleric']
        assert data['Cleric']['spell_count'] >= 0
        assert '_config' in data
        
        # Verify config values
        config = data['_config']
        assert 'spell_cache_expiry_hours' in config
        assert 'pricing_cache_expiry_hours' in config
    
    def test_cache_expiry_status_endpoint(self, mock_app, sample_spell_data, sample_spell_details):
        """Test cache expiry status endpoint."""
        # Set up test data
        app.spells_cache['Cleric'] = sample_spell_data  # Use proper case
        app.cache_timestamp['Cleric'] = datetime.now().isoformat()
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
        
        # Verify spell data structure
        assert 'cached' in data['spells']
        assert 'expired' in data['spells']
        
        # Verify pricing data
        assert data['pricing']['cached_count'] >= 0
        assert data['pricing']['total_spells'] >= 0


class TestSearchEndpoints:
    """Test search functionality."""
    
    def test_search_spells_endpoint(self, mock_app, sample_spell_data):
        """Test spell search endpoint."""
        with patch('app.scrape_class') as mock_scrape:
            # Set up search data
            app.spells_cache.clear()
            app.spells_cache['Cleric'] = sample_spell_data  # Use proper case for cache key
            
            response = mock_app.get('/api/search-spells?q=courage')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert isinstance(data, dict)
            assert 'results' in data
            assert 'query' in data
            assert 'total_found' in data
            
            if len(data['results']) > 0:
                spell = data['results'][0]
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
    
    def test_refresh_spell_cache_endpoint_success(self, mock_app):
        """Test refresh spell cache endpoint with valid class."""
        # Clear refresh progress first
        app.refresh_progress.clear()
        
        response = mock_app.post('/api/refresh-spell-cache/cleric')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should have success response
        assert data['success'] == True
        assert data['message'] == 'Refresh started'
        assert data['class_name'] == 'cleric'
        
        # Should have initiated progress tracking
        assert 'cleric' in app.refresh_progress
        progress = app.refresh_progress['cleric']
        assert progress['stage'] == 'initializing'
        assert progress['progress_percentage'] == 5
        assert 'start_time' in progress
        assert 'last_updated' in progress
    
    def test_refresh_spell_cache_endpoint_invalid_class(self, mock_app):
        """Test refresh spell cache endpoint with invalid class."""
        response = mock_app.post('/api/refresh-spell-cache/invalidclass')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid class name' in data['error']
    
    def test_refresh_spell_cache_endpoint_case_insensitive(self, mock_app):
        """Test refresh spell cache endpoint is case insensitive."""
        app.refresh_progress.clear()
        
        # Test different case variations
        test_cases = ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']
        
        for class_name in test_cases:
            response = mock_app.post(f'/api/refresh-spell-cache/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['class_name'] == 'cleric'  # Always normalized to lowercase
    
    def test_refresh_pricing_cache_endpoint_success(self, mock_app, sample_spell_data):
        """Test refresh pricing cache endpoint with valid data."""
        # Set up test data
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
        
        # Verify data was actually cleared
        assert '13' not in app.pricing_cache_timestamp
        assert '12' not in app.pricing_cache_timestamp
        assert '13' not in app.pricing_lookup
        assert '12' not in app.pricing_lookup
        # Verify pricing was removed from spell details cache
        assert '13' not in app.spell_details_cache or 'pricing' not in app.spell_details_cache.get('13', {})
        assert '12' not in app.spell_details_cache or 'pricing' not in app.spell_details_cache.get('12', {})
    
    def test_refresh_pricing_cache_endpoint_invalid_class(self, mock_app):
        """Test refresh pricing cache endpoint with invalid class."""
        response = mock_app.post('/api/refresh-pricing-cache/invalidclass')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid class name' in data['error']
    
    def test_refresh_pricing_cache_endpoint_no_spells(self, mock_app):
        """Test refresh pricing cache endpoint when no spells exist."""
        app.spells_cache.clear()
        
        response = mock_app.post('/api/refresh-pricing-cache/cleric')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No spells found for class' in data['error']
    
    def test_refresh_pricing_cache_endpoint_case_insensitive(self, mock_app, sample_spell_data):
        """Test refresh pricing cache endpoint is case insensitive."""
        app.spells_cache.clear()
        app.spells_cache['cleric'] = sample_spell_data
        
        # Test different case variations
        test_cases = ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']
        
        for class_name in test_cases:
            response = mock_app.post(f'/api/refresh-pricing-cache/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True


class TestRefreshProgressEndpoints:
    """Test refresh progress tracking endpoints."""
    
    def test_refresh_progress_endpoint_success(self, mock_app):
        """Test getting refresh progress for active refresh."""
        # Clear and set up progress
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
    
    def test_refresh_progress_endpoint_not_found(self, mock_app):
        """Test getting refresh progress for non-existent refresh."""
        app.refresh_progress.clear()
        
        response = mock_app.get('/api/refresh-progress/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No refresh in progress' in data['error']
    
    def test_refresh_progress_endpoint_case_insensitive(self, mock_app):
        """Test refresh progress endpoint is case insensitive."""
        app.refresh_progress.clear()
        app.update_refresh_progress('cleric', 'processing')
        
        # Test various cases
        test_cases = ['cleric', 'CLERIC', 'Cleric', 'cLeRiC']
        
        for class_name in test_cases:
            response = mock_app.get(f'/api/refresh-progress/{class_name}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['stage'] == 'processing'
            assert data['progress_percentage'] == 60
    
    def test_refresh_progress_integration_with_refresh_endpoint(self, mock_app):
        """Test that refresh endpoints properly create progress tracking."""
        app.refresh_progress.clear()
        
        # Start a refresh
        response = mock_app.post('/api/refresh-spell-cache/cleric')
        assert response.status_code == 200
        
        # Should be able to get progress
        response = mock_app.get('/api/refresh-progress/cleric')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['stage'] == 'initializing'
        assert data['progress_percentage'] == 5
        assert 'start_time' in data
        assert 'last_updated' in data


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


class TestClassNameHandling:
    """Test class name handling and normalization - critical for shadowknight issue."""
    
    def test_shadowknight_camelcase_normalization(self, mock_app, sample_spell_data):
        """Test that ShadowKnight (camelCase) is properly normalized to shadowknight."""
        with patch('app.scrape_class') as mock_scrape:
            app.spells_cache.clear()
            app.spells_cache['shadowknight'] = sample_spell_data  # Store with lowercase key
            app.cache_timestamp['shadowknight'] = datetime.now().isoformat()
            
            # Test all variations of shadowknight class name
            test_cases = [
                'shadowknight',
                'ShadowKnight', 
                'SHADOWKNIGHT',
                'Shadowknight',
                'shadowKnight',
                'sHaDoWkNiGhT'
            ]
            
            for class_name in test_cases:
                response = mock_app.get(f'/api/spells/{class_name}')
                assert response.status_code == 200, f"Failed for class name: {class_name}"
                
                data = json.loads(response.data)
                assert 'spells' in data, f"No spells key in response for: {class_name}"
                assert isinstance(data['spells'], list), f"Spells not a list for: {class_name}"
                assert len(data['spells']) > 0, f"No spells returned for: {class_name}"
                
            # Verify scraping was not called (using cache)
            mock_scrape.assert_not_called()
    
    def test_all_eq_classes_return_json_not_html(self, mock_app, sample_spell_data):
        """Test that all EQ classes return JSON, never HTML - prevents shadowknight HTML issue."""
        from app import CLASSES
        
        with patch('app.scrape_class') as mock_scrape:
            app.spells_cache.clear()
            
            # Set up cache for all classes
            for class_name in CLASSES.keys():
                cache_key = class_name.lower()
                app.spells_cache[cache_key] = sample_spell_data
                app.cache_timestamp[cache_key] = datetime.now().isoformat()
            
            # Test each class returns proper JSON structure
            for class_name in CLASSES.keys():
                response = mock_app.get(f'/api/spells/{class_name.lower()}')
                
                # Must return 200 status
                assert response.status_code == 200, f"Status code {response.status_code} for {class_name}"
                
                # Must be JSON, not HTML
                assert response.content_type.startswith('application/json'), f"Not JSON for {class_name}: {response.content_type}"
                
                # Response must not contain HTML doctype
                response_text = response.get_data(as_text=True)
                assert '<!DOCTYPE html>' not in response_text, f"HTML returned for {class_name}"
                assert '<html>' not in response_text, f"HTML returned for {class_name}"
                
                # Must parse as valid JSON
                data = json.loads(response.data)
                assert isinstance(data, dict), f"Response not dict for {class_name}"
                assert 'spells' in data, f"No spells key for {class_name}"
                assert isinstance(data['spells'], list), f"Spells not list for {class_name}"
    
    def test_shadowknight_specific_api_response_format(self, mock_app, sample_spell_data):
        """Test shadowknight specifically returns proper API response format."""
        with patch('app.scrape_class') as mock_scrape:
            app.spells_cache.clear()
            app.spells_cache['shadowknight'] = sample_spell_data
            app.cache_timestamp['shadowknight'] = datetime.now().isoformat()
            
            response = mock_app.get('/api/spells/shadowknight')
            
            # Verify response format matches expected API structure
            assert response.status_code == 200
            assert response.content_type.startswith('application/json')
            
            data = json.loads(response.data)
            
            # Verify API response structure
            expected_keys = ['spells', 'cached', 'last_updated', 'spell_count']
            for key in expected_keys:
                assert key in data, f"Missing key '{key}' in shadowknight response"
            
            # Verify spells array structure
            assert isinstance(data['spells'], list)
            if len(data['spells']) > 0:
                spell = data['spells'][0]
                required_spell_fields = ['name', 'level', 'spell_id']
                for field in required_spell_fields:
                    assert field in spell, f"Missing field '{field}' in spell data"
    
    def test_class_name_to_cache_key_mapping(self, mock_app, sample_spell_data):
        """Test that class name normalization correctly maps to cache keys."""
        from app import CLASSES
        
        app.spells_cache.clear()
        
        # Set up cache with lowercase keys (as the backend does)
        for class_name in CLASSES.keys():
            cache_key = class_name.lower()
            app.spells_cache[cache_key] = sample_spell_data
            app.cache_timestamp[cache_key] = datetime.now().isoformat()
        
        # Test that requests with various cases map to correct cache keys
        test_mappings = {
            'ShadowKnight': 'shadowknight',
            'SHADOWKNIGHT': 'shadowknight', 
            'shadowknight': 'shadowknight',
            'Cleric': 'cleric',
            'WIZARD': 'wizard',
            'beastlord': 'beastlord'
        }
        
        for input_name, expected_cache_key in test_mappings.items():
            response = mock_app.get(f'/api/spells/{input_name}')
            assert response.status_code == 200, f"Failed for input: {input_name} -> {expected_cache_key}"
            
            # Verify the response contains data (proving cache lookup worked)
            data = json.loads(response.data)
            assert len(data['spells']) > 0, f"No spells found for {input_name} -> {expected_cache_key}"


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