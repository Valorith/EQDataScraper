"""
Tests for OAuth authentication routes.
Tests the authentication endpoints and OAuth flow functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from flask import Flask

from routes.auth import auth_bp
from utils.oauth import GoogleOAuth
from models.user import User, OAuthSession
from tests.conftest import TEST_JWT_SECRET, generate_test_user, generate_test_session


class TestAuthRoutes:
    """Test OAuth authentication routes."""
    
    def test_google_login_url_generation(self, flask_oauth_test_client, test_env_vars):
        """Test Google OAuth login URL generation with PKCE parameters."""
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'data' in response_data
        assert 'auth_url' in response_data['data']
        assert 'state' in response_data['data']
        
        # Verify URL contains required parameters
        auth_url = response_data['data']['auth_url']
        parsed_url = urlparse(auth_url)
        query_params = parse_qs(parsed_url.query)
        
        assert 'client_id' in query_params
        assert 'redirect_uri' in query_params
        assert 'response_type' in query_params
        assert 'scope' in query_params
        assert 'state' in query_params
        assert 'code_challenge' in query_params
        assert 'code_challenge_method' in query_params
        
        # Verify PKCE parameters
        assert query_params['code_challenge_method'][0] == 'S256'
        assert len(query_params['code_challenge'][0]) > 0
        assert query_params['response_type'][0] == 'code'
    
    @patch('routes.auth.get_db_connection')
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.oauth_storage')
    @patch('routes.auth.GoogleOAuth')
    @patch('routes.auth.User')
    @patch('routes.auth.OAuthSession')
    def test_oauth_callback_success_new_user(self, mock_oauth_session, mock_user, mock_google_oauth, 
                                           mock_oauth_storage, mock_jwt_manager, mock_get_db_connection,
                                           flask_oauth_test_client, test_env_vars, mock_google_user_info):
        """Test successful OAuth callback with new user creation."""
        # Setup mocks
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock database connection
        mock_db_conn = Mock()
        mock_get_db_connection.return_value = mock_db_conn
        
        # Mock Google OAuth token exchange - it returns user_info directly
        mock_oauth_instance.exchange_code_for_tokens.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'id_token': 'test_id_token',
            'user_info': {
                'google_id': mock_google_user_info['sub'],
                'email': mock_google_user_info['email'],
                'email_verified': mock_google_user_info['email_verified'],
                'first_name': mock_google_user_info['given_name'],
                'last_name': mock_google_user_info['family_name'],
                'avatar_url': mock_google_user_info['picture']
            }
        }
        
        # Mock user model - user doesn't exist yet
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        mock_user_instance.get_user_by_google_id.return_value = None
        mock_user_instance.get_user_preferences.return_value = {
            'theme_preference': 'dark',
            'results_per_page': 25
        }
        
        # Mock user creation
        created_user = generate_test_user(google_id=mock_google_user_info['sub'])
        mock_user_instance.create_user.return_value = created_user
        mock_user_instance.create_user_preferences.return_value = {
            'theme_preference': 'dark',
            'results_per_page': 25
        }
        
        # Mock session creation
        mock_session_instance = Mock()
        mock_oauth_session.return_value = mock_session_instance
        mock_session_instance.create_session.return_value = generate_test_session()
        
        # Mock OAuth state verification
        mock_oauth_instance.verify_state.return_value = True
        
        # Mock OAuth storage to return stored state
        mock_oauth_storage.get_oauth_state.return_value = {
            'state': 'test_state',
            'code_verifier': 'test_code_verifier'
        }
        
        # Mock JWT manager
        mock_jwt_manager.create_access_token.return_value = 'test_jwt_access_token'
        mock_jwt_manager.create_refresh_token.return_value = 'test_jwt_refresh_token'
        mock_jwt_manager.generate_local_session_token.return_value = 'test_local_session_token'
        
        # Test OAuth callback
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'code': 'test_auth_code',
            'state': 'test_state'
        })
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'access_token' in response_data['data']
        assert 'refresh_token' in response_data['data']
        assert 'user' in response_data['data']
        
        # Verify user was created
        mock_user_instance.create_user.assert_called_once()
        
        # Verify session was created
        mock_session_instance.create_session.assert_called_once()
    
    @patch('routes.auth.get_db_connection')
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.oauth_storage')
    @patch('routes.auth.GoogleOAuth')
    @patch('routes.auth.User')
    @patch('routes.auth.OAuthSession')
    def test_oauth_callback_success_existing_user(self, mock_oauth_session, mock_user, mock_google_oauth,
                                                 mock_oauth_storage, mock_jwt_manager, mock_get_db_connection,
                                                 flask_oauth_test_client, test_env_vars, mock_google_user_info):
        """Test successful OAuth callback with existing user."""
        # Setup mocks
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock database connection
        mock_db_conn = Mock()
        mock_get_db_connection.return_value = mock_db_conn
        
        # Mock Google OAuth token exchange - it returns user_info directly
        mock_oauth_instance.exchange_code_for_tokens.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'id_token': 'test_id_token',
            'user_info': {
                'google_id': mock_google_user_info['sub'],
                'email': mock_google_user_info['email'],
                'email_verified': mock_google_user_info['email_verified'],
                'first_name': mock_google_user_info['given_name'],
                'last_name': mock_google_user_info['family_name'],
                'avatar_url': mock_google_user_info['picture']
            }
        }
        
        # Mock user model - user exists
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        existing_user = generate_test_user(google_id=mock_google_user_info['sub'])
        mock_user_instance.get_user_by_google_id.return_value = existing_user
        mock_user_instance.get_user_preferences.return_value = {
            'theme_preference': 'dark',
            'results_per_page': 25
        }
        # update_user_profile needs to return the updated user dict
        mock_user_instance.update_user_profile.return_value = existing_user
        
        # Mock session creation
        mock_session_instance = Mock()
        mock_oauth_session.return_value = mock_session_instance
        mock_session_instance.create_session.return_value = generate_test_session()
        
        # Mock OAuth state verification
        mock_oauth_instance.verify_state.return_value = True
        
        # Mock OAuth storage to return stored state
        mock_oauth_storage.get_oauth_state.return_value = {
            'state': 'test_state',
            'code_verifier': 'test_code_verifier'
        }
        
        # Mock JWT manager
        mock_jwt_manager.create_access_token.return_value = 'test_jwt_access_token'
        mock_jwt_manager.create_refresh_token.return_value = 'test_jwt_refresh_token'
        mock_jwt_manager.generate_local_session_token.return_value = 'test_local_session_token'
        
        # Test OAuth callback
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'code': 'test_auth_code',
            'state': 'test_state'
        })
        
        response_data = json.loads(response.data)
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response_data}")
        assert response.status_code == 200
        
        assert response_data['success'] is True
        assert 'access_token' in response_data['data']
        assert 'user' in response_data['data']
        
        # Verify user was NOT created (already exists)
        mock_user_instance.create_user.assert_not_called()
        
        # Verify login was updated
        mock_user_instance.update_user_login.assert_called_once()
    
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_callback_invalid_state(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test OAuth callback with invalid state parameter (CSRF protection)."""
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock state verification failure
        mock_oauth_instance.verify_state.return_value = False
        
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'code': 'test_auth_code',
            'state': 'invalid_state'
        })
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Invalid' in response_data['error'] and 'state' in response_data['error']
    
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_callback_missing_code(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test OAuth callback without authorization code."""
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'state': 'test_state'
        })
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Missing' in response_data['error'] or 'code' in response_data['error']
    
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_callback_with_error(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test OAuth callback with error from Google."""
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'error': 'access_denied',
            'error_description': 'User denied access'
        })
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Missing' in response_data['error'] or 'error' in response_data['error']
        # Just check that we got an error, not the specific message since it varies
    
    @patch('routes.auth.oauth_storage')
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_callback_token_exchange_failure(self, mock_google_oauth, mock_oauth_storage, flask_oauth_test_client, test_env_vars):
        """Test OAuth callback when token exchange fails."""
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock OAuth storage to return stored state
        mock_oauth_storage.get_oauth_state.return_value = {
            'state': 'test_state',
            'code_verifier': 'test_code_verifier'
        }
        
        # Mock state verification success
        mock_oauth_instance.verify_state.return_value = True
        
        # Mock token exchange failure
        mock_oauth_instance.exchange_code_for_tokens.side_effect = Exception("Token exchange failed")
        
        response = flask_oauth_test_client.post('/api/auth/google/callback', json={
            'code': 'test_auth_code',
            'state': 'test_state'
        })
        
        assert response.status_code == 500
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'OAuth callback failed' in response_data['error']
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    @patch('routes.auth.OAuthSession')
    def test_token_refresh_success(self, mock_oauth_session, mock_user, mock_jwt_manager, 
                                  flask_oauth_test_client, test_env_vars):
        """Test successful access token refresh."""
        # Mock JWT manager
        mock_jwt_manager.refresh_access_token.return_value = {
            'access_token': 'new_access_token',
            'user': generate_test_user()
        }
        
        response = flask_oauth_test_client.post('/api/auth/refresh', 
                                              json={'refresh_token': 'valid_refresh_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'access_token' in response_data['data']
        assert 'user' in response_data['data']
        
        # Verify JWT manager was called
        mock_jwt_manager.refresh_access_token.assert_called_once()
    
    @patch('routes.auth.jwt_manager')
    def test_token_refresh_invalid_token(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test token refresh with invalid refresh token."""
        # Mock JWT manager to return None for invalid token
        mock_jwt_manager.refresh_access_token.return_value = None
        
        response = flask_oauth_test_client.post('/api/auth/refresh', 
                                              json={'refresh_token': 'invalid_refresh_token'})
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Invalid' in response_data['error'] or 'expired' in response_data['error']
    
    def test_token_refresh_missing_token(self, flask_oauth_test_client, test_env_vars):
        """Test token refresh without refresh token."""
        response = flask_oauth_test_client.post('/api/auth/refresh', json={})
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Missing' in response_data['error'] or 'required' in response_data['error']
    
    @patch('routes.auth.get_db_connection')
    @patch('utils.jwt_utils.jwt_manager')  # Mock the global jwt_manager used by decorator
    @patch('routes.auth.OAuthSession')
    def test_logout_success(self, mock_oauth_session, mock_jwt_manager, mock_get_db_connection, flask_oauth_test_client, test_env_vars):
        """Test successful logout with session cleanup."""
        # Mock database connection
        mock_db_conn = Mock()
        mock_get_db_connection.return_value = mock_db_conn
        
        # Mock JWT manager to extract user info
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'session_token': 'test_session_token',
            'type': 'access',
            'email': 'test@example.com',
            'role': 'user'
        }
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        
        # Mock session deletion
        mock_session_instance = Mock()
        mock_oauth_session.return_value = mock_session_instance
        
        response = flask_oauth_test_client.post('/api/auth/logout',
                                              json={'refresh_token': 'test_refresh_token'},
                                              headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'Logout' in response_data['message'] or 'logout' in response_data['message']
        
        # Verify session was deleted
        mock_session_instance.delete_session.assert_called_once()
    
    def test_logout_without_token(self, flask_oauth_test_client, test_env_vars):
        """Test logout without authorization header."""
        response = flask_oauth_test_client.post('/api/auth/logout')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Authorization header required' in response_data['error']
    
    @patch('routes.auth.jwt_manager')
    def test_logout_invalid_token(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test logout with invalid token."""
        mock_jwt_manager.extract_token_from_header.return_value = 'invalid_token'
        mock_jwt_manager.verify_token.return_value = None
        
        response = flask_oauth_test_client.post('/api/auth/logout',
                                              headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Invalid or expired token' in response_data['error']


class TestUserRoutes:
    """Test user management routes."""
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_get_user_profile_success(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test successful user profile retrieval."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        # Mock user model
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        user_data = generate_test_user()
        mock_user_instance.get_user_by_id.return_value = user_data
        
        # Mock user preferences
        mock_user_instance.get_user_preferences.return_value = {
            'theme_preference': 'dark',
            'results_per_page': 25
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            response = flask_oauth_test_client.get('/api/user/profile',
                                                  headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'user' in response_data['data']
        assert 'preferences' in response_data['data']
        assert response_data['data']['user']['email'] == 'test@example.com'
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_update_user_profile_success(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test successful user profile update."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        # Mock user model
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        updated_user = generate_test_user(first_name='Updated', last_name='Name')
        mock_user_instance.update_user_profile.return_value = updated_user
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            response = flask_oauth_test_client.put('/api/user/profile',
                                                  json={'first_name': 'Updated', 'last_name': 'Name'},
                                                  headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert response_data['data']['user']['first_name'] == 'Updated'
        assert response_data['data']['user']['last_name'] == 'Name'
        
        # Verify update was called
        mock_user_instance.update_user_profile.assert_called_once()
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_update_user_preferences_success(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test successful user preferences update."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        # Mock user model
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        updated_prefs = {
            'theme_preference': 'light',
            'results_per_page': 50
        }
        mock_user_instance.update_user_preferences.return_value = updated_prefs
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            response = flask_oauth_test_client.put('/api/user/preferences',
                                                  json=updated_prefs,
                                                  headers={'Authorization': 'Bearer valid_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert response_data['data']['preferences']['theme_preference'] == 'light'
        
        # Verify update was called
        mock_user_instance.update_user_preferences.assert_called_once()


class TestAdminRoutes:
    """Test admin-only routes."""
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_get_all_users_admin_success(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test admin can retrieve all users."""
        # Mock admin authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'admin_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }
        
        # Mock user model
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        mock_user_instance.get_all_users.return_value = {
            'users': [generate_test_user()],
            'total_count': 1,
            'page': 1,
            'per_page': 10
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'admin@example.com', 'role': 'admin'}
            
            response = flask_oauth_test_client.get('/api/admin/users',
                                                  headers={'Authorization': 'Bearer admin_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert 'users' in response_data['data']
        assert response_data['data']['total_count'] == 1
    
    @patch('routes.auth.jwt_manager')
    def test_get_all_users_regular_user_denied(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test regular user cannot access admin endpoints."""
        # Mock regular user authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'user_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'user@example.com',
            'role': 'user',  # Not admin
            'type': 'access'
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'user@example.com', 'role': 'user'}
            
            response = flask_oauth_test_client.get('/api/admin/users',
                                                  headers={'Authorization': 'Bearer user_token'})
        
        assert response.status_code == 403
        response_data = json.loads(response.data)
        
        assert 'error' in response_data
        assert 'Admin access required' in response_data['error']
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_update_user_role_admin_success(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test admin can update user roles."""
        # Mock admin authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'admin_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }
        
        # Mock user model
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        updated_user = generate_test_user(id=2, role='admin')
        mock_user_instance.update_user_role.return_value = updated_user
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'admin@example.com', 'role': 'admin'}
            
            response = flask_oauth_test_client.put('/api/admin/users/2/role',
                                                  json={'role': 'admin'},
                                                  headers={'Authorization': 'Bearer admin_token'})
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert response_data['success'] is True
        assert response_data['data']['user']['role'] == 'admin'
        
        # Verify update was called
        mock_user_instance.update_user_role.assert_called_once_with(user_id=2, role='admin')


class TestRateLimitingIntegration:
    """Test rate limiting on authentication endpoints."""
    
    def test_auth_endpoint_rate_limit_enforcement(self, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on auth endpoints (integration test)."""
        # Make multiple requests quickly to trigger rate limit
        responses = []
        for i in range(12):  # Exceed 10 requests per minute limit
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Should have some successful responses and some rate limited
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        assert success_count > 0
        assert rate_limited_count > 0
        assert success_count + rate_limited_count == 12
    
    @patch('routes.auth.jwt_manager')
    def test_user_endpoint_rate_limit_enforcement(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on user endpoints."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            # Make requests to exceed rate limit
            responses = []
            for i in range(65):  # Exceed 60 requests per hour limit
                response = flask_oauth_test_client.get('/api/user/profile',
                                                      headers={'Authorization': 'Bearer valid_token'})
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count > 0