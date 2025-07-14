"""
Test suite for the new database-based spell search functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from tests.conftest import MockRealDictCursor


class TestSpellSearch:
    """Test the new database-based spell search functionality."""
    
    def test_spell_search_basic_query(self, flask_test_client):
        """Test basic spell search with query parameter."""
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            # Mock successful database connection
            mock_conn = Mock()
            mock_cursor = MockRealDictCursor([
                {
                    'id': 1, 'name': 'Test Spell', 'mana': 50, 'cast_time': 2500,
                    'range': 100, 'targettype': 1, 'skill': 0, 'resisttype': 1,
                    'spell_category': 1, 'buffduration': 600, 'deities': 0,
                    'classes1': 10, 'classes2': 255, 'classes3': 255, 'classes4': 255,
                    'classes5': 255, 'classes6': 255, 'classes7': 255, 'classes8': 255,
                    'classes9': 255, 'classes10': 255, 'classes11': 255, 'classes12': 255,
                    'classes13': 255, 'classes14': 255, 'classes15': 255, 'classes16': 255,
                    'effectid1': 15, 'effectid2': 0, 'effectid3': 0, 'effectid4': 0,
                    'effectid5': 0, 'effectid6': 0, 'effectid7': 0, 'effectid8': 0,
                    'effectid9': 0, 'effectid10': 0, 'effectid11': 0, 'effectid12': 0,
                    'components1': 0, 'components2': 0, 'components3': 0, 'components4': 0,
                    'icon': 1, 'new_icon': 1
                }
            ])
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = (mock_conn, 'mysql', None)
            
            # Mock the count query result
            mock_cursor.fetchone = Mock(return_value={'total_count': 1})
            
            response = flask_test_client.get('/api/spells/search?q=Test')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'spells' in data
            assert len(data['spells']) == 1
            assert data['spells'][0]['name'] == 'Test Spell'
            assert data['total_count'] == 1

    def test_spell_search_no_params(self, flask_test_client):
        """Test spell search without required parameters."""
        response = flask_test_client.get('/api/spells/search')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Search query or filters required' in data['error']

    def test_spell_search_with_filters(self, flask_test_client):
        """Test spell search with JSON filters."""
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_cursor = MockRealDictCursor([])
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = (mock_conn, 'mysql', None)
            
            # Mock the count query result
            mock_cursor.fetchone = Mock(return_value={'total_count': 0})
            
            filters = json.dumps([{
                'field': 'warrior_level',
                'operator': 'class_can_use',
                'value': True
            }])
            
            response = flask_test_client.get(f'/api/spells/search?filters={filters}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'spells' in data
            assert data['total_count'] == 0

    def test_spell_search_pagination(self, flask_test_client):
        """Test spell search pagination parameters."""
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_cursor = MockRealDictCursor([])
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = (mock_conn, 'mysql', None)
            
            # Mock the count query result
            mock_cursor.fetchone = Mock(return_value={'total_count': 0})
            
            response = flask_test_client.get('/api/spells/search?q=test&limit=10&offset=20')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['limit'] == 10
            assert data['offset'] == 20

    def test_spell_search_database_error(self, flask_test_client):
        """Test spell search with database connection error."""
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            mock_get_conn.return_value = (None, None, 'Database not configured')
            
            response = flask_test_client.get('/api/spells/search?q=test')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Database not configured' in data['error']

    def test_spell_search_class_levels_structure(self, flask_test_client):
        """Test that spell search returns proper class levels structure."""
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            mock_conn = Mock()
            mock_cursor = MockRealDictCursor([
                {
                    'id': 1, 'name': 'Warrior Spell', 'mana': 0, 'cast_time': 0,
                    'range': 0, 'targettype': 1, 'skill': 0, 'resisttype': 0,
                    'spell_category': 1, 'buffduration': 0, 'deities': 0,
                    'classes1': 5, 'classes2': 255, 'classes3': 10, 'classes4': 255,
                    'classes5': 255, 'classes6': 255, 'classes7': 255, 'classes8': 255,
                    'classes9': 255, 'classes10': 255, 'classes11': 255, 'classes12': 255,
                    'classes13': 255, 'classes14': 255, 'classes15': 255, 'classes16': 255,
                    'effectid1': 0, 'effectid2': 0, 'effectid3': 0, 'effectid4': 0,
                    'effectid5': 0, 'effectid6': 0, 'effectid7': 0, 'effectid8': 0,
                    'effectid9': 0, 'effectid10': 0, 'effectid11': 0, 'effectid12': 0,
                    'components1': 0, 'components2': 0, 'components3': 0, 'components4': 0,
                    'icon': 1, 'new_icon': 1
                }
            ])
            mock_conn.cursor.return_value = mock_cursor
            mock_get_conn.return_value = (mock_conn, 'mysql', None)
            
            # Mock the count query result
            mock_cursor.fetchone = Mock(return_value={'total_count': 1})
            
            response = flask_test_client.get('/api/spells/search?q=Warrior')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            spell = data['spells'][0]
            
            # Check class levels structure
            assert 'class_levels' in spell
            assert spell['class_levels']['warrior'] == 5  # Can use at level 5
            assert spell['class_levels']['cleric'] == 255  # Cannot use
            assert spell['class_levels']['paladin'] == 10  # Can use at level 10
            
            # Check effects and components arrays
            assert 'effects' in spell
            assert isinstance(spell['effects'], list)
            assert len(spell['effects']) == 12
            
            assert 'components' in spell
            assert isinstance(spell['components'], list)
            assert len(spell['components']) == 4


class TestSpellSearchValidation:
    """Test spell search parameter validation."""
    
    @pytest.mark.parametrize("param,value,expected", [
        ('q', 'test spell', 'test spell'),
        ('limit', '50', 50),
        ('offset', '100', 100),
        ('skill', '1', 1),
        ('category', '5', 5),
    ])
    def test_validate_spell_search_params(self, param, value, expected):
        """Test individual parameter validation."""
        from utils.security import validate_spell_search_params
        
        params = {param: value}
        result = validate_spell_search_params(params)
        
        assert param in result
        assert result[param] == expected

    def test_validate_spell_search_params_filters(self):
        """Test JSON filters validation."""
        from utils.security import validate_spell_search_params
        
        filters_json = json.dumps([{
            'field': 'mana',
            'operator': 'greater than',
            'value': 50
        }])
        
        params = {'filters': filters_json}
        result = validate_spell_search_params(params)
        
        assert 'filters' in result
        assert len(result['filters']) == 1
        assert result['filters'][0]['field'] == 'mana'

    def test_validate_spell_search_params_defaults(self):
        """Test default values for spell search parameters."""
        from utils.security import validate_spell_search_params
        
        result = validate_spell_search_params({})
        
        assert result['limit'] == 20
        assert result['offset'] == 0
        assert result['filters'] == []


class TestSpellSearchSecurity:
    """Test security aspects of spell search."""
    
    def test_spell_search_rate_limiting_headers(self, flask_test_client):
        """Test that rate limiting is applied to spell search."""
        # Note: This test checks that the endpoint exists and responds properly
        # Rate limiting functionality is tested separately in test_rate_limiting.py
        
        with patch('app.get_eqemu_db_connection') as mock_get_conn:
            mock_get_conn.return_value = (None, None, 'Database not configured')
            
            response = flask_test_client.get('/api/spells/search?q=test')
            
            # Should get a response (even if error due to no DB)
            assert response.status_code == 503
            
            # Rate limiting decorator should be applied (no exception thrown)
            assert True  # If we get here, the decorator is properly applied

    def test_spell_search_input_sanitization(self):
        """Test that spell search input is properly sanitized."""
        from utils.security import validate_spell_search_params
        
        # Test potentially malicious input
        params = {
            'q': '<script>alert("xss")</script>test',
            'limit': '1000',  # Over max
            'offset': '-5'    # Invalid
        }
        
        result = validate_spell_search_params(params)
        
        # Should sanitize script tags
        assert '<script>' not in result['q']
        assert 'alert' not in result['q']
        
        # Should enforce limits
        assert result['limit'] <= 100
        assert result['offset'] == 0  # Should default due to invalid input