"""
Tests for database administration endpoints.
Tests the read-only database configuration and validation features.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extras import RealDictCursor

from routes.admin import admin_bp


class TestDatabaseAdminEndpoints:
    """Test database administration functionality."""

    def test_get_database_config_no_database(self, mock_app_with_admin):
        """Test getting database config when no database is configured."""
        app, client, admin_token = mock_app_with_admin
        
        with patch('routes.admin.os.path.exists', return_value=False):
            with patch.dict('routes.admin.os.environ', {}, clear=True):
                response = client.get(
                    '/api/admin/database/config',
                    headers={'Authorization': f'Bearer {admin_token}'}
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['data']['database']['connected'] is False
                assert data['data']['database']['status'] == 'no_database_configured'

    def test_get_database_config_with_existing_config(self, mock_app_with_admin):
        """Test getting database config when configuration exists."""
        app, client, admin_token = mock_app_with_admin
        
        mock_config = {
            'production_database_url': 'postgresql://user:pass@host:5432/db',
            'use_production_database': True,
            'database_read_only': True
        }
        
        with patch('routes.admin.os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
                with patch.dict('routes.admin.os.environ', {'DATABASE_URL': mock_config['production_database_url']}):
                    with patch('routes.admin.get_db_connection', return_value=None):
                        response = client.get(
                            '/api/admin/database/config',
                            headers={'Authorization': f'Bearer {admin_token}'}
                        )
                        
                        assert response.status_code == 200
                        data = json.loads(response.data)
                        assert data['success'] is True
                        db_info = data['data']['database']
                        assert db_info['host'] == 'host'
                        assert db_info['port'] == 5432
                        assert db_info['database'] == 'db'
                        assert db_info['username'] == 'user'

    def test_update_database_config_missing_fields(self, mock_app_with_admin):
        """Test updating database config with missing required fields."""
        app, client, admin_token = mock_app_with_admin
        
        incomplete_data = {
            'host': 'localhost',
            'port': 5432,
            # Missing database, username, password
        }
        
        response = client.post(
            '/api/admin/database/config',
            headers={'Authorization': f'Bearer {admin_token}'},
            json=incomplete_data
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required field' in data['message']

    def test_update_database_config_connection_failure(self, mock_app_with_admin):
        """Test updating database config when connection test fails."""
        app, client, admin_token = mock_app_with_admin
        
        config_data = {
            'host': 'invalid-host',
            'port': 5432,
            'database': 'testdb',
            'username': 'testuser',
            'password': 'testpass',
            'use_ssl': True
        }
        
        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection failed")):
            response = client.post(
                '/api/admin/database/config',
                headers={'Authorization': f'Bearer {admin_token}'},
                json=config_data
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Database connection test failed' in data['message']

    def test_update_database_config_success(self, mock_app_with_admin):
        """Test successful database config update with read-only mode."""
        app, client, admin_token = mock_app_with_admin
        
        config_data = {
            'host': 'localhost',
            'port': 5432,
            'database': 'eqemu',
            'username': 'readonly_user',
            'password': 'secure_password',
            'use_ssl': True
        }
        
        # Mock successful database connection
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ['PostgreSQL 13.0'],  # version query
            [1000],  # items count
            [500]   # discovered_items count
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch('psycopg2.connect', return_value=mock_connection):
            with patch('builtins.open', create=True) as mock_file:
                with patch('routes.admin.os.path.exists', return_value=True):
                    with patch('json.load', return_value={}):
                        with patch('json.dump') as mock_dump:
                            response = client.post(
                                '/api/admin/database/config',
                                headers={'Authorization': f'Bearer {admin_token}'},
                                json=config_data
                            )
                            
                            assert response.status_code == 200
                            data = json.loads(response.data)
                            assert data['success'] is True
                            assert 'READ-ONLY mode' in data['message']
                            
                            db_info = data['data']['database']
                            assert db_info['host'] == 'localhost'
                            assert db_info['read_only'] is True
                            assert db_info['status'] == 'connected'
                            
                            # Verify config was saved with read-only flag
                            mock_dump.assert_called_once()
                            saved_config = mock_dump.call_args[0][0]
                            assert saved_config['database_read_only'] is True
                            assert 'default_transaction_read_only=on' in saved_config['production_database_url']

    def test_test_database_connection_missing_fields(self, mock_app_with_admin):
        """Test database connection test with missing fields."""
        app, client, admin_token = mock_app_with_admin
        
        test_data = {
            'host': 'localhost',
            # Missing other required fields
        }
        
        response = client.post(
            '/api/admin/database/test',
            headers={'Authorization': f'Bearer {admin_token}'},
            json=test_data
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required field' in data['message']

    def test_test_database_connection_success(self, mock_app_with_admin):
        """Test successful database connection test with EQEmu tables."""
        app, client, admin_token = mock_app_with_admin
        
        test_data = {
            'host': 'localhost',
            'port': 5432,
            'database': 'eqemu',
            'username': 'testuser',
            'password': 'testpass',
            'use_ssl': False
        }
        
        # Mock database responses
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ['PostgreSQL 13.0 on x86_64-pc-linux-gnu'],  # version
            ['2023-01-01 12:00:00'],  # current time
            [True],   # items table exists
            [True],   # discovered_items table exists
            [15000],  # items count
            [8500]    # discovered_items count
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch('psycopg2.connect', return_value=mock_connection):
            with patch('time.time', side_effect=[0, 0.150]):  # 150ms connection time
                response = client.post(
                    '/api/admin/database/test',
                    headers={'Authorization': f'Bearer {admin_token}'},
                    json=test_data
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['data']['connection_successful'] is True
                assert data['data']['read_only_mode'] is True
                assert data['data']['connection_time_ms'] == 150.0
                
                tables = data['data']['tables']
                assert tables['items_exists'] is True
                assert tables['items_accessible'] is True
                assert tables['items_count'] == 15000
                assert tables['discovered_items_exists'] is True
                assert tables['discovered_items_accessible'] is True
                assert tables['discovered_items_count'] == 8500
                
                # Verify read-only transaction was set
                mock_cursor.execute.assert_any_call("SET TRANSACTION READ ONLY")

    def test_test_database_connection_tables_not_accessible(self, mock_app_with_admin):
        """Test database connection when tables exist but are not accessible."""
        app, client, admin_token = mock_app_with_admin
        
        test_data = {
            'host': 'localhost',
            'port': 5432,
            'database': 'eqemu',
            'username': 'limited_user',
            'password': 'testpass',
            'use_ssl': True
        }
        
        # Mock database responses with permission errors
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ['PostgreSQL 13.0'],  # version
            ['2023-01-01 12:00:00'],  # current time
            [True],   # items table exists
            [False],  # discovered_items table doesn't exist
        ]
        
        # Mock permission errors when trying to count
        def mock_execute(query):
            if 'COUNT(*) FROM items' in query:
                raise psycopg2.ProgrammingError("permission denied for table items")
            elif 'COUNT(*) FROM discovered_items' in query:
                raise psycopg2.ProgrammingError("relation 'discovered_items' does not exist")
        
        mock_cursor.execute.side_effect = mock_execute
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        with patch('psycopg2.connect', return_value=mock_connection):
            # Override execute for count queries specifically
            original_execute = mock_cursor.execute
            
            def selective_execute(query):
                if 'COUNT(*)' in query:
                    if 'items' in query and 'discovered_items' not in query:
                        raise psycopg2.ProgrammingError("permission denied")
                    elif 'discovered_items' in query:
                        raise psycopg2.ProgrammingError("table does not exist")
                else:
                    # Use side_effect for other queries
                    return original_execute(query)
            
            mock_cursor.execute.side_effect = selective_execute
            mock_cursor.fetchone.side_effect = [
                ['PostgreSQL 13.0'],  # version
                ['2023-01-01 12:00:00'],  # current time
                [True],   # items table exists
                [False],  # discovered_items table doesn't exist
            ]
            
            response = client.post(
                '/api/admin/database/test',
                headers={'Authorization': f'Bearer {admin_token}'},
                json=test_data
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            tables = data['data']['tables']
            assert tables['items_exists'] is True
            assert tables['items_accessible'] is False
            assert tables['items_count'] == 0
            assert tables['discovered_items_exists'] is False
            assert tables['discovered_items_accessible'] is False

    def test_test_database_connection_psycopg2_error(self, mock_app_with_admin):
        """Test database connection test with psycopg2 connection error."""
        app, client, admin_token = mock_app_with_admin
        
        test_data = {
            'host': 'unreachable-host',
            'port': 5432,
            'database': 'eqemu',
            'username': 'testuser',
            'password': 'testpass'
        }
        
        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("could not connect to server")):
            response = client.post(
                '/api/admin/database/test',
                headers={'Authorization': f'Bearer {admin_token}'},
                json=test_data
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Database connection failed' in data['message']

    def test_admin_endpoints_require_admin_role(self, mock_app_with_user):
        """Test that database admin endpoints require admin role."""
        app, client, user_token = mock_app_with_user
        
        # Test GET config endpoint
        response = client.get(
            '/api/admin/database/config',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 403
        
        # Test POST config endpoint
        response = client.post(
            '/api/admin/database/config',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'host': 'test'}
        )
        assert response.status_code == 403
        
        # Test connection test endpoint
        response = client.post(
            '/api/admin/database/test',
            headers={'Authorization': f'Bearer {user_token}'},
            json={'host': 'test'}
        )
        assert response.status_code == 403

    def test_admin_endpoints_require_authentication(self, mock_app):
        """Test that database admin endpoints require authentication."""
        app, client = mock_app
        
        # Test without authorization header
        response = client.get('/api/admin/database/config')
        assert response.status_code == 401
        
        response = client.post('/api/admin/database/config', json={})
        assert response.status_code == 401
        
        response = client.post('/api/admin/database/test', json={})
        assert response.status_code == 401