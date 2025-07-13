"""
Tests for admin activities endpoint and activity logging system.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g


@pytest.fixture
def flask_admin_test_client():
    """Create Flask test client with OAuth enabled for admin testing."""
    import os
    from unittest.mock import patch
    
    # Set up test environment variables
    test_env = {
        'ENABLE_USER_ACCOUNTS': 'true',
        'JWT_SECRET_KEY': 'test_jwt_secret_key_for_testing_only',
        'ENCRYPTION_KEY': 'test_encryption_key_for_testing_only',
        'GOOGLE_CLIENT_ID': 'test-client-id',
        'GOOGLE_CLIENT_SECRET': 'test-client-secret',
        'OAUTH_REDIRECT_URI': 'http://localhost:3000/auth/callback',
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
    }
    
    with patch.dict(os.environ, test_env):
        with patch('app.psycopg2.connect') as mock_connect:
            # Mock database connection
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Import app with OAuth enabled
            from app import app
            app.config['TESTING'] = True
            app.config['WTF_CSRF_ENABLED'] = False
            
            return app.test_client()

@pytest.fixture
def admin_user_data():
    """Mock admin user data"""
    return {
        'id': 1,
        'email': 'admin@test.com',
        'role': 'admin',
        'is_admin': True,
        'is_active': True
    }

@pytest.fixture
def regular_user_data():
    """Mock regular user data"""
    return {
        'id': 2,
        'email': 'user@test.com', 
        'role': 'user',
        'is_admin': False,
        'is_active': True
    }

@pytest.fixture
def mock_activities_data():
    """Mock activity log data"""
    from models.activity import ActivityLog
    
    return [
        {
            'id': 1,
            'action': ActivityLog.ACTION_LOGIN,
            'user_id': 1,
            'user_display': 'Admin User',
            'resource_type': 'session',
            'resource_id': 'session_123',
            'details': {'method': 'google_oauth'},
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Browser',
            'created_at': datetime.now() - timedelta(minutes=5)
        },
        {
            'id': 2,
            'action': 'user_view',
            'user_id': 2,
            'user_display': 'Regular User',
            'resource_type': 'profile',
            'resource_id': 'profile_2',
            'details': {'page': 'profile'},
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Browser',
            'created_at': datetime.now() - timedelta(minutes=10)
        }
    ]

class TestAdminActivitiesEndpoint:
    """Test the admin activities endpoint"""
    
    def test_activities_endpoint_requires_auth(self, flask_admin_test_client):
        """Test that activities endpoint requires authentication"""
        response = flask_admin_test_client.get('/api/admin/activities')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Authorization header required' in data['error']
    
    def test_activities_endpoint_requires_admin(self, flask_admin_test_client, regular_user_data):
        """Test that activities endpoint requires admin privileges"""
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid token but for regular user (not admin)
            mock_extract.return_value = 'valid_token'
            mock_verify.return_value = {
                'user_id': 2,
                'email': 'user@test.com',
                'role': 'user',  # Not admin
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities',
                                headers={'Authorization': 'Bearer valid_token'})
            assert response.status_code == 403
    
    @patch('routes.admin.get_db_connection')
    def test_activities_endpoint_no_database(self, mock_get_db, flask_admin_test_client, admin_user_data):
        """Test activities endpoint when no database connection available"""
        mock_get_db.return_value = None
        
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid admin token
            mock_extract.return_value = 'admin_token'
            mock_verify.return_value = {
                'user_id': 1,
                'email': 'admin@test.com',
                'role': 'admin',
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities',
                                headers={'Authorization': 'Bearer admin_token'})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            # When no database connection, returns mock activities for development
            assert 'activities' in data['data']
            assert 'total_count' in data['data']
            assert len(data['data']['activities']) > 0  # Should have mock activities
            assert data['data']['total_count'] > 0
    
    @patch('routes.admin.get_db_connection')
    @patch('routes.admin.ActivityLog')
    def test_activities_endpoint_with_data(self, mock_activity_log, mock_get_db, 
                                         flask_admin_test_client, admin_user_data, mock_activities_data):
        """Test activities endpoint returns formatted activity data"""
        # Mock database connection
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        
        # Mock ActivityLog
        mock_activity_instance = Mock()
        mock_activity_log.return_value = mock_activity_instance
        mock_activity_instance.get_recent_activities.return_value = mock_activities_data
        mock_activity_instance.get_activity_count.return_value = len(mock_activities_data)
        
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid admin token
            mock_extract.return_value = 'admin_token'
            mock_verify.return_value = {
                'user_id': 1,
                'email': 'admin@test.com',
                'role': 'admin',
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities?limit=5',
                                headers={'Authorization': 'Bearer admin_token'})
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert 'activities' in data['data']
            assert 'total_count' in data['data']
            assert len(data['data']['activities']) == 2
            assert data['data']['total_count'] == 2
            
            # Check first activity formatting
            first_activity = data['data']['activities'][0]
            assert first_activity['action'] == 'login'
            assert first_activity['user_display'] == 'Admin User'
            assert 'description' in first_activity
            assert 'created_at' in first_activity
    
    @patch('routes.admin.get_db_connection')
    @patch('routes.admin.ActivityLog')
    def test_activities_endpoint_pagination(self, mock_activity_log, mock_get_db, 
                                          flask_admin_test_client, admin_user_data, mock_activities_data):
        """Test activities endpoint pagination parameters"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        
        mock_activity_instance = Mock()
        mock_activity_log.return_value = mock_activity_instance
        mock_activity_instance.get_recent_activities.return_value = mock_activities_data[:2]
        mock_activity_instance.get_activity_count.return_value = len(mock_activities_data)
        
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid admin token
            mock_extract.return_value = 'admin_token'
            mock_verify.return_value = {
                'user_id': 1,
                'email': 'admin@test.com',
                'role': 'admin',
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities?limit=2&offset=0',
                                headers={'Authorization': 'Bearer admin_token'})
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify pagination was passed to ActivityLog
            mock_activity_instance.get_recent_activities.assert_called_with(
                limit=2, offset=0, user_id=None, action=None, 
                start_date=None, end_date=None
            )
    
    @patch('routes.admin.get_db_connection')
    @patch('routes.admin.ActivityLog') 
    def test_activities_endpoint_filtering(self, mock_activity_log, mock_get_db,
                                         flask_admin_test_client, admin_user_data):
        """Test activities endpoint filtering by action and user"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        
        mock_activity_instance = Mock()
        mock_activity_log.return_value = mock_activity_instance
        mock_activity_instance.get_recent_activities.return_value = []
        mock_activity_instance.get_activity_count.return_value = 0
        
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid admin token
            mock_extract.return_value = 'admin_token'
            mock_verify.return_value = {
                'user_id': 1,
                'email': 'admin@test.com',
                'role': 'admin',
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities?action=login&user_id=1',
                                headers={'Authorization': 'Bearer admin_token'})
            assert response.status_code == 200
            
            # Verify filtering was passed to ActivityLog
            mock_activity_instance.get_recent_activities.assert_called_with(
                limit=50, offset=0, user_id=1, action='login',
                start_date=None, end_date=None
            )

class TestActivityDescriptionFormatting:
    """Test activity description formatting"""
    
    @patch('routes.admin.get_db_connection')
    def test_login_activity_description(self, mock_get_db, flask_admin_test_client):
        """Test login activity description formatting"""
        mock_conn = Mock()
        mock_get_db.return_value = mock_conn
        
        # Import ActivityLog to use the correct action constants
        from models.activity import ActivityLog
        
        login_activity = {
            'id': 1,
            'action': ActivityLog.ACTION_LOGIN,
            'user_id': 1,
            'user_display': 'Test User',
            'resource_type': 'session',
            'resource_id': 'session_123',
            'details': {'method': 'google_oauth'},
            'ip_address': '127.0.0.1',
            'user_agent': 'Test Browser',
            'created_at': datetime.now()
        }
        
        # Mock the ActivityLog constructor and methods
        with patch('routes.admin.ActivityLog') as mock_activity_log:
            mock_activity_instance = Mock()
            mock_activity_log.return_value = mock_activity_instance
            mock_activity_instance.get_recent_activities.return_value = [login_activity]
            mock_activity_instance.get_activity_count.return_value = 1
            
            # Set the ACTION_LOGIN constant on the mocked class
            mock_activity_log.ACTION_LOGIN = 'login'
            
            with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
                 patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
                
                # Mock a valid admin token
                mock_extract.return_value = 'admin_token'
                mock_verify.return_value = {
                    'user_id': 1,
                    'email': 'admin@test.com',
                    'role': 'admin',
                    'type': 'access'
                }
                
                response = flask_admin_test_client.get('/api/admin/activities',
                                    headers={'Authorization': 'Bearer admin_token'})
                data = json.loads(response.data)
                
                activity = data['data']['activities'][0]
                assert activity['description'] == 'Test User logged in'
    

class TestActivityLoggingIntegration:
    """Test activity logging integration"""
    
    @patch('routes.admin.get_db_connection')
    def test_activity_logging_database_error(self, mock_get_db, flask_admin_test_client):
        """Test activity logging handles database errors gracefully"""
        mock_get_db.side_effect = Exception("Database connection failed")
        
        with patch('utils.jwt_utils.jwt_manager.extract_token_from_header') as mock_extract, \
             patch('utils.jwt_utils.jwt_manager.verify_token') as mock_verify:
            
            # Mock a valid admin token
            mock_extract.return_value = 'admin_token'
            mock_verify.return_value = {
                'user_id': 1,
                'email': 'admin@test.com',
                'role': 'admin',
                'type': 'access'
            }
            
            response = flask_admin_test_client.get('/api/admin/activities',
                                headers={'Authorization': 'Bearer admin_token'})
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Failed to get activities' in data['error']