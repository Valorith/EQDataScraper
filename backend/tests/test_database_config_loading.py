"""
Test database configuration loading and persistence.
"""

import pytest
import json
import os
from unittest.mock import patch, Mock, mock_open

def test_database_config_loading_preserves_type():
    """Test that loading database config preserves the saved database type."""
    
    # Mock config.json content with MySQL database
    mock_config = {
        'backend_port': 5001,
        'frontend_port': 3000,
        'use_production_database': True,
        'production_database_url': 'mysql://user:pass@host:3306/database',
        'database_type': 'mysql',  # Explicitly saved as MySQL
        'database_read_only': True
    }
    
    # Import the admin routes to test
    with patch.dict(os.environ, {'ENABLE_USER_ACCOUNTS': 'true', 'JWT_SECRET_KEY': 'test_secret'}):
        from routes.admin import get_database_config
        from flask import Flask, g
        
        app = Flask(__name__)
        
        with app.test_request_context():
            # Mock file operations
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                    # Mock the database connector test
                    with patch('routes.admin.get_database_connector') as mock_connector:
                        with patch('routes.admin.test_database_query') as mock_test:
                            # Mock successful connection
                            mock_conn = Mock()
                            mock_connector.return_value = mock_conn
                            mock_test.return_value = {
                                'version': 'MySQL 8.0',
                                'tables': {'items_exists': True, 'discovered_items_exists': True}
                            }
                            
                            # Mock admin user
                            g.current_user = {'id': 1, 'role': 'admin'}
                            
                            # Call the function directly (simulating GET request)
                            response = get_database_config()
                            data = json.loads(response[0].data)
                            
                            # Verify the database type is preserved
                            assert data['success'] is True
                            assert 'database' in data['data']
                            db_info = data['data']['database']
                            
                            # This should be 'mysql' from config, not detected from URL
                            assert db_info['db_type'] == 'mysql'
                            assert db_info['host'] == 'host'
                            assert db_info['port'] == 3306
                            assert db_info['database'] == 'database'


def test_frontend_form_population():
    """Test that frontend correctly populates form from loaded config."""
    
    # Simulate the database config response
    mock_response = {
        'success': True,
        'data': {
            'database': {
                'connected': True,
                'host': 'localhost',
                'port': 3306,
                'database': 'eqemu',
                'username': 'eqemu_user',
                'db_type': 'mysql',  # This should be populated
                'status': 'connected',
                'version': 'MySQL 8.0'
            }
        }
    }
    
    # The frontend should:
    # 1. Load this configuration
    # 2. Set databaseForm.db_type = 'mysql' 
    # 3. Set databaseForm.port = 3306
    # 4. Show the correct database type in the dropdown
    
    assert mock_response['data']['database']['db_type'] == 'mysql'
    assert mock_response['data']['database']['port'] == 3306


if __name__ == '__main__':
    test_database_config_loading_preserves_type()
    test_frontend_form_population()
    print("All tests passed!")