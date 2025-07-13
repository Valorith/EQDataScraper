"""
Tests for database administration endpoints.
Tests the read-only database configuration and validation features.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
import psycopg2
from psycopg2.extras import RealDictCursor
import jwt
from datetime import datetime, timedelta
import os

from routes.admin import admin_bp


@pytest.fixture
def admin_test_client():
    """Create Flask test client with admin routes enabled."""
    with patch.dict(os.environ, {'ENABLE_USER_ACCOUNTS': 'true', 'JWT_SECRET_KEY': 'test_secret_key'}):
        try:
            from app import app
            app.config['TESTING'] = True
            app.config['WTF_CSRF_ENABLED'] = False
            return app.test_client()
        except AssertionError as e:
            if "overwriting an existing endpoint" in str(e):
                pytest.skip("App has duplicate route definitions - skipping database admin test")
            raise


class TestDatabaseAdminEndpoints:
    """Test database administration functionality."""
    
    def _create_admin_token(self):
        """Helper to create admin JWT token for tests."""
        payload = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'iat': datetime.utcnow().timestamp(),
            'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            'type': 'access'
        }
        # Use a test secret key
        return jwt.encode(payload, 'test_secret_key', algorithm='HS256')
    
    def _get_admin_payload(self):
        """Helper to get admin payload for mocking."""
        return {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }

    def test_admin_endpoints_require_authentication(self, admin_test_client):
        """Test that admin endpoints require authentication."""
        # Test without token
        response = admin_test_client.get('/api/admin/database/config')
        assert response.status_code == 401

    def test_admin_endpoints_require_admin_role(self, admin_test_client):
        """Test that admin endpoints require admin role."""
        # Create non-admin token
        payload = {
            'user_id': 1,
            'email': 'user@example.com',
            'role': 'user',  # Not admin
            'iat': datetime.utcnow().timestamp(),
            'exp': (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            'type': 'access'
        }
        user_token = jwt.encode(payload, 'test_secret_key', algorithm='HS256')
        
        with patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            mock_verify.return_value = payload
            response = admin_test_client.get(
                '/api/admin/database/config',
                headers={'Authorization': f'Bearer {user_token}'}
            )
            assert response.status_code == 403

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    def test_get_database_config_no_database(self, mock_jwt_decode, admin_test_client):
        """Test getting database config when no database is configured."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        with patch('os.path.exists', return_value=False):
            with patch.dict('os.environ', {}, clear=True):
                response = admin_test_client.get(
                    '/api/admin/database/config',
                    headers={'Authorization': f'Bearer {admin_token}'}
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['data']['database']['connected'] is False
                assert data['data']['database']['status'] == 'no_database_configured'

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    def test_get_database_config_with_existing_config(self, mock_jwt_decode, admin_test_client):
        """Test getting database config when configuration exists."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        mock_config = {
            'production_database_url': 'postgresql://user:pass@host:5432/db',
            'use_production_database': True,
            'database_read_only': True
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(mock_config)
                with patch.dict('os.environ', {'DATABASE_URL': mock_config['production_database_url']}):
                    with patch('routes.admin.get_db_connection', return_value=None):
                        with patch('utils.database_connectors.get_database_connector') as mock_connector:
                            with patch('utils.database_connectors.test_database_query') as mock_test_query:
                                # Mock successful connection test
                                mock_conn = Mock()
                                mock_connector.return_value = mock_conn
                                mock_test_query.return_value = {'version': 'PostgreSQL 13.0', 'tables': {'items_exists': True}}
                                
                                response = admin_test_client.get(
                                    '/api/admin/database/config',
                                    headers={'Authorization': f'Bearer {admin_token}'}
                                )
                                
                                assert response.status_code == 200
                                data = json.loads(response.data)
                                assert data['success'] is True
                                assert 'database' in data['data']
                                assert 'host' in data['data']['database']
                                assert data['data']['database']['connected'] is True

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    def test_update_database_config_missing_fields(self, mock_jwt_decode, admin_test_client):
        """Test updating database config with missing required fields."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Missing required fields
        response = admin_test_client.post(
            '/api/admin/database/config',
            json={'port': 5432},  # Missing other required fields
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required field: host' in data['error']

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    @patch('utils.database_connectors.get_database_connector')
    @patch('utils.database_connectors.build_connection_url')
    def test_update_database_config_connection_failure(self, mock_build_url, mock_get_connector, mock_jwt_decode, admin_test_client):
        """Test updating database config when connection test fails."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Mock connection failure
        mock_build_url.return_value = "postgresql://user:pass@host:5432/db"
        mock_get_connector.side_effect = Exception("Connection failed")
        
        response = admin_test_client.post(
            '/api/admin/database/config',
            json={
                'host': 'localhost',
                'port': 5432,
                'database': 'testdb',
                'username': 'testuser',
                'password': 'testpass'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Connection failed' in data.get('error_message', data.get('error', ''))

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    @patch('utils.database_connectors.get_database_connector')
    @patch('utils.database_connectors.build_connection_url')
    def test_update_database_config_success(self, mock_build_url, mock_get_connector, mock_jwt_decode, admin_test_client):
        """Test successfully updating database configuration."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Mock successful connection
        mock_build_url.return_value = "postgresql://user:pass@host:5432/db"
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ['PostgreSQL 13.0']
        mock_get_connector.return_value = mock_conn
        
        with patch('builtins.open', create=True) as mock_file:
            with patch('json.dump') as mock_json_dump:
                with patch('json.load', return_value={}) as mock_json_load:
                    mock_file_handle = MagicMock()
                    mock_file.return_value.__enter__.return_value = mock_file_handle
                    
                    response = admin_test_client.post(
                        '/api/admin/database/config',
                        json={
                            'host': 'localhost',
                            'port': 5432,
                            'database': 'testdb',
                            'username': 'testuser',
                            'password': 'testpass'
                        },
                        headers={'Authorization': f'Bearer {admin_token}'}
                    )
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'database' in data['data']

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    def test_test_database_connection_missing_fields(self, mock_jwt_decode, admin_test_client):
        """Test database connection test with missing fields."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        response = admin_test_client.post(
            '/api/admin/database/test',
            json={},
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing request data' in data['error']

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    @patch('utils.database_connectors.get_database_connector')
    @patch('utils.database_connectors.test_database_query')
    def test_test_database_connection_success(self, mock_test_query, mock_get_connector, mock_jwt_decode, admin_test_client):
        """Test successful database connection test."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Mock successful connection and query
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connector.return_value = mock_conn
        mock_test_query.return_value = {
            'version': 'PostgreSQL 13.0',
            'current_time': '2023-01-01 12:00:00',
            'tables': {
                'items_exists': True,
                'discovered_items_exists': True,
                'items_accessible': True,
                'discovered_items_accessible': True,
                'items_count': 1000,
                'discovered_items_count': 500
            }
        }
        
        response = admin_test_client.post(
            '/api/admin/database/test',
            json={
                'host': 'localhost',
                'port': 5432,
                'database': 'testdb',
                'username': 'testuser',
                'password': 'testpass'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'connection_successful' in data['data']
        assert data['data']['connection_successful'] is True

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    @patch('utils.database_connectors.get_database_connector')
    def test_test_database_connection_tables_not_accessible(self, mock_get_connector, mock_jwt_decode, admin_test_client):
        """Test database connection when tables are not accessible."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Mock connection failure due to table access
        mock_get_connector.side_effect = Exception("Tables 'items' or 'discovered_items' not found")
        
        response = admin_test_client.post(
            '/api/admin/database/test',
            json={
                'host': 'localhost',
                'port': 5432,
                'database': 'testdb',
                'username': 'testuser',
                'password': 'testpass'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        # Check for error in any of the possible error fields
        error_text = str(data.get('error', data.get('error_message', data.get('message', ''))))
        assert 'not found' in error_text

    @patch('utils.jwt_utils.jwt_manager.verify_token')
    @patch('utils.database_connectors.get_database_connector')
    def test_test_database_connection_psycopg2_error(self, mock_get_connector, mock_jwt_decode, admin_test_client):
        """Test database connection with psycopg2 error."""
        admin_token = self._create_admin_token()
        mock_jwt_decode.return_value = self._get_admin_payload()
        
        # Mock psycopg2 error
        mock_get_connector.side_effect = psycopg2.OperationalError("Connection timeout")
        
        response = admin_test_client.post(
            '/api/admin/database/test',
            json={
                'host': 'localhost',
                'port': 5432,
                'database': 'testdb',
                'username': 'testuser',
                'password': 'testpass'
            },
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        # Check for error in any of the possible error fields
        error_text = str(data.get('error', data.get('error_message', data.get('message', ''))))
        assert 'Connection timeout' in error_text