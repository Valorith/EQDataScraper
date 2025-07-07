import pytest
import json
from flask import Flask
from app import app
from utils.security import validate_json_filters


class TestAdvancedFilters:
    """Comprehensive test suite for Advanced Filters functionality"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_filter_validation_text_fields(self):
        """Test text field filter validation"""
        # Valid text filters
        valid_filters = [
            {"field": "loretext", "operator": "contains", "value": "sword"},
            {"field": "loretext", "operator": "equals", "value": "Epic Weapon"}
        ]
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 2
        
        # Invalid operator for text field
        invalid_filters = [
            {"field": "loretext", "operator": "greater than", "value": "test"}
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "Invalid operator" in result["error"]
    
    def test_filter_validation_numeric_fields(self):
        """Test numeric field filter validation"""
        # Valid numeric filters
        valid_filters = [
            {"field": "price", "operator": "equals", "value": 100},
            {"field": "weight", "operator": "greater than", "value": 50},
            {"field": "damage", "operator": "less than", "value": 20},
            {"field": "ac", "operator": "between", "value": [10, 20]},
            {"field": "hp", "operator": "not equals", "value": 0}
        ]
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 5
        
        # Invalid value type for numeric field
        invalid_filters = [
            {"field": "price", "operator": "equals", "value": "not a number"}
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "must be numeric" in result["error"]
        
        # Invalid between values
        invalid_filters = [
            {"field": "ac", "operator": "between", "value": [10]}  # Need 2 values
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "requires 2 numeric values" in result["error"]
    
    def test_filter_validation_boolean_fields(self):
        """Test boolean field filter validation"""
        # Valid boolean filters
        valid_filters = [
            {"field": "magic", "operator": "is", "value": True},
            {"field": "lore", "operator": "is", "value": False},
            {"field": "nodrop", "operator": "is", "value": 1},
            {"field": "norent", "operator": "is", "value": 0}
        ]
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 4
        
        # Invalid operator for boolean field
        invalid_filters = [
            {"field": "magic", "operator": "equals", "value": True}
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "Invalid operator" in result["error"]
    
    def test_filter_validation_effect_fields(self):
        """Test effect field filter validation"""
        # Valid effect filters
        valid_filters = [
            {"field": "clickeffect", "operator": "exists", "value": True},
            {"field": "proceffect", "operator": "exists", "value": False},
            {"field": "worneffect", "operator": "exists", "value": 1},
            {"field": "focuseffect", "operator": "exists", "value": 0}
        ]
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 4
    
    def test_filter_validation_attribute_fields(self):
        """Test attribute field filter validation"""
        attributes = ["str", "sta", "agi", "dex", "wis", "int", "cha"]
        valid_filters = []
        
        for attr in attributes:
            valid_filters.append({
                "field": attr,
                "operator": "greater than",
                "value": 10
            })
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 7
    
    def test_filter_validation_resistance_fields(self):
        """Test resistance field filter validation"""
        resistances = ["mr", "fr", "cr", "dr", "pr"]
        valid_filters = []
        
        for resist in resistances:
            valid_filters.append({
                "field": resist,
                "operator": "greater than",
                "value": 5
            })
        
        result = validate_json_filters(json.dumps(valid_filters))
        assert result["is_valid"] == True
        assert len(result["filters"]) == 5
    
    def test_filter_validation_max_filters(self):
        """Test maximum filter limit"""
        # Create 11 filters (exceeds max of 10)
        too_many_filters = []
        for i in range(11):
            too_many_filters.append({
                "field": "price",
                "operator": "equals",
                "value": i
            })
        
        result = validate_json_filters(json.dumps(too_many_filters))
        assert result["is_valid"] == False
        assert "Maximum 10 filters" in result["error"]
    
    def test_filter_validation_invalid_field(self):
        """Test invalid field rejection"""
        invalid_filters = [
            {"field": "invalid_field", "operator": "equals", "value": "test"},
            {"field": "'; DROP TABLE items;--", "operator": "equals", "value": "test"}
        ]
        
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "Invalid field" in result["error"]
    
    def test_filter_validation_missing_required_fields(self):
        """Test missing required fields"""
        # Missing operator
        invalid_filters = [
            {"field": "price", "value": 100}
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "Missing required filter fields" in result["error"]
        
        # Missing value
        invalid_filters = [
            {"field": "price", "operator": "equals"}
        ]
        result = validate_json_filters(json.dumps(invalid_filters))
        assert result["is_valid"] == False
        assert "Missing required filter fields" in result["error"]
    
    def test_api_search_with_filters(self, client):
        """Test the API endpoint with various filters"""
        # Test with valid filters
        filters = [
            {"field": "magic", "operator": "is", "value": True},
            {"field": "price", "operator": "greater than", "value": 100}
        ]
        
        response = client.get(
            '/api/items/search',
            query_string={
                'q': 'sword',
                'filters': json.dumps(filters),
                'page': 1,
                'per_page': 20
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'total_count' in data
        assert 'limit' in data
        assert 'offset' in data
        
    def test_api_search_with_invalid_filters(self, client):
        """Test the API endpoint with invalid filters"""
        # Test with invalid filter structure
        invalid_filters = "not valid json"
        
        response = client.get(
            '/api/items/search',
            query_string={
                'q': 'sword',
                'filters': invalid_filters,
                'page': 1,
                'per_page': 20
            }
        )
        
        # Should still return 200 but ignore invalid filters
        assert response.status_code == 200
        
    def test_all_filter_combinations(self, client):
        """Test various combinations of filters"""
        test_cases = [
            # Text search with numeric filter
            {
                "filters": [
                    {"field": "loretext", "operator": "contains", "value": "epic"},
                    {"field": "reqlevel", "operator": "less than", "value": 50}
                ],
                "description": "Text + Numeric filters"
            },
            # Multiple numeric filters
            {
                "filters": [
                    {"field": "damage", "operator": "greater than", "value": 10},
                    {"field": "delay", "operator": "less than", "value": 30},
                    {"field": "ac", "operator": "between", "value": [5, 15]}
                ],
                "description": "Multiple numeric filters"
            },
            # Boolean flags combination
            {
                "filters": [
                    {"field": "magic", "operator": "is", "value": True},
                    {"field": "nodrop", "operator": "is", "value": False},
                    {"field": "lore", "operator": "is", "value": True}
                ],
                "description": "Multiple boolean filters"
            },
            # Attributes and resistances
            {
                "filters": [
                    {"field": "str", "operator": "greater than", "value": 10},
                    {"field": "mr", "operator": "greater than", "value": 20},
                    {"field": "hp", "operator": "greater than", "value": 50}
                ],
                "description": "Stats and resistance filters"
            },
            # Effects combination
            {
                "filters": [
                    {"field": "clickeffect", "operator": "exists", "value": True},
                    {"field": "proceffect", "operator": "exists", "value": False}
                ],
                "description": "Effect filters"
            }
        ]
        
        for test_case in test_cases:
            response = client.get(
                '/api/items/search',
                query_string={
                    'q': '',  # Empty search to test filters alone
                    'filters': json.dumps(test_case["filters"]),
                    'page': 1,
                    'per_page': 20
                }
            )
            
            assert response.status_code == 200, f"Failed for: {test_case['description']}"
            data = response.get_json()
            assert 'items' in data, f"Missing items for: {test_case['description']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])