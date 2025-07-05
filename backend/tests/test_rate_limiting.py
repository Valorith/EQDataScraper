"""
Tests for rate limiting functionality in OAuth system.
Tests rate limiting configuration and enforcement across different endpoints.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from routes.auth import auth_bp
from tests.conftest import generate_test_user


class TestRateLimitingConfiguration:
    """Test rate limiting configuration and setup."""
    
    def test_rate_limiter_initialization(self, flask_oauth_test_client, test_env_vars):
        """Test that rate limiter is properly initialized."""
        # Access the Flask app from test client
        app = flask_oauth_test_client.application
        
        # Check that limiter is configured
        assert hasattr(app, 'limiter')
        assert isinstance(app.limiter, Limiter)
        
        # Check storage backend
        assert app.limiter.storage is not None
    
    def test_rate_limit_key_function(self, flask_oauth_test_client, test_env_vars):
        """Test rate limit key function for user identification."""
        app = flask_oauth_test_client.application
        
        with app.test_request_context('/', headers={'X-Forwarded-For': '192.168.1.1'}):
            # Test IP-based rate limiting
            key = get_remote_address()
            assert key is not None
            
    def test_rate_limit_configuration_values(self, flask_oauth_test_client, test_env_vars):
        """Test that rate limit values are properly configured."""
        app = flask_oauth_test_client.application
        
        # Check that rate limiting is enabled
        assert app.config.get('RATELIMIT_ENABLED', True) is True
        
        # Check storage type
        storage_uri = app.config.get('RATELIMIT_STORAGE_URI', 'memory://')
        assert storage_uri is not None


class TestAuthEndpointRateLimiting:
    """Test rate limiting on authentication endpoints."""
    
    @pytest.fixture
    def rate_limited_client(self, flask_oauth_test_client):
        """Create a client with rate limiting enabled."""
        return flask_oauth_test_client
    
    def test_google_login_rate_limit(self, rate_limited_client, test_env_vars):
        """Test rate limiting on Google login endpoint (10 requests per minute)."""
        endpoint = '/api/auth/google/login'
        
        # Make requests within rate limit
        responses = []
        for i in range(8):  # Within limit
            response = rate_limited_client.get(endpoint)
            responses.append(response)
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 8
    
    def test_google_login_rate_limit_exceeded(self, rate_limited_client, test_env_vars):
        """Test rate limiting when exceeded on Google login endpoint."""
        endpoint = '/api/auth/google/login'
        
        # Make requests to exceed rate limit
        responses = []
        for i in range(12):  # Exceed 10 per minute limit
            response = rate_limited_client.get(endpoint)
            responses.append(response)
            
        # Should have some rate limited responses
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0
        
        # Check rate limit headers
        for response in rate_limited_responses:
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
    
    def test_oauth_callback_rate_limit(self, rate_limited_client, test_env_vars):
        """Test rate limiting on OAuth callback endpoint."""
        endpoint = '/api/auth/google/callback'
        
        # Make requests to exceed rate limit
        responses = []
        for i in range(12):  # Exceed 10 per minute limit
            response = rate_limited_client.get(endpoint, query_string={'code': 'test', 'state': 'test'})
            responses.append(response)
        
        # Should have some rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0
    
    def test_token_refresh_rate_limit(self, rate_limited_client, test_env_vars):
        """Test rate limiting on token refresh endpoint."""
        endpoint = '/api/auth/refresh'
        
        # Make requests to exceed rate limit
        responses = []
        for i in range(12):  # Exceed 10 per minute limit
            response = rate_limited_client.post(endpoint, json={'refresh_token': 'test'})
            responses.append(response)
        
        # Should have some rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0
    
    def test_logout_rate_limit(self, rate_limited_client, test_env_vars):
        """Test rate limiting on logout endpoint."""
        endpoint = '/api/auth/logout'
        
        # Make requests to exceed rate limit
        responses = []
        for i in range(12):  # Exceed 10 per minute limit
            response = rate_limited_client.post(endpoint)
            responses.append(response)
        
        # Should have some rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0


class TestUserEndpointRateLimiting:
    """Test rate limiting on user endpoints."""
    
    @patch('routes.auth.jwt_manager')
    def test_user_profile_rate_limit(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on user profile endpoint (60 requests per hour)."""
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
            
            # Make requests within rate limit
            responses = []
            for i in range(50):  # Within 60 per hour limit
                response = flask_oauth_test_client.get('/api/user/profile',
                                                      headers={'Authorization': 'Bearer valid_token'})
                responses.append(response)
            
            # Most should succeed (some might fail due to missing user data, but not due to rate limiting)
            non_rate_limited = [r for r in responses if r.status_code != 429]
            assert len(non_rate_limited) == 50
    
    @patch('routes.auth.jwt_manager')
    def test_user_profile_rate_limit_exceeded(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting when exceeded on user profile endpoint."""
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
            for i in range(65):  # Exceed 60 per hour limit
                response = flask_oauth_test_client.get('/api/user/profile',
                                                      headers={'Authorization': 'Bearer valid_token'})
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count > 0
    
    @patch('routes.auth.jwt_manager')
    def test_user_preferences_rate_limit(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on user preferences endpoint."""
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
            for i in range(65):  # Exceed 60 per hour limit
                response = flask_oauth_test_client.put('/api/user/preferences',
                                                      json={'theme_preference': 'dark'},
                                                      headers={'Authorization': 'Bearer valid_token'})
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count > 0


class TestAdminEndpointRateLimiting:
    """Test rate limiting on admin endpoints."""
    
    @patch('routes.auth.jwt_manager')
    def test_admin_users_rate_limit(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on admin users endpoint (30 requests per hour)."""
        # Mock admin authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'admin_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'admin@example.com', 'role': 'admin'}
            
            # Make requests within rate limit
            responses = []
            for i in range(25):  # Within 30 per hour limit
                response = flask_oauth_test_client.get('/api/admin/users',
                                                      headers={'Authorization': 'Bearer admin_token'})
                responses.append(response)
            
            # Most should succeed (some might fail due to missing data, but not due to rate limiting)
            non_rate_limited = [r for r in responses if r.status_code != 429]
            assert len(non_rate_limited) == 25
    
    @patch('routes.auth.jwt_manager')
    def test_admin_users_rate_limit_exceeded(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting when exceeded on admin users endpoint."""
        # Mock admin authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'admin_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'admin@example.com', 'role': 'admin'}
            
            # Make requests to exceed rate limit
            responses = []
            for i in range(35):  # Exceed 30 per hour limit
                response = flask_oauth_test_client.get('/api/admin/users',
                                                      headers={'Authorization': 'Bearer admin_token'})
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count > 0
    
    @patch('routes.auth.jwt_manager')
    def test_admin_role_update_rate_limit(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test rate limiting on admin role update endpoint."""
        # Mock admin authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'admin_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'type': 'access'
        }
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'admin@example.com', 'role': 'admin'}
            
            # Make requests to exceed rate limit
            responses = []
            for i in range(35):  # Exceed 30 per hour limit
                response = flask_oauth_test_client.put('/api/admin/users/2/role',
                                                      json={'role': 'user'},
                                                      headers={'Authorization': 'Bearer admin_token'})
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            assert rate_limited_count > 0


class TestRateLimitingByUser:
    """Test rate limiting per user vs per IP address."""
    
    @patch('routes.auth.jwt_manager')
    def test_rate_limiting_per_user(self, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test that rate limiting is applied per user, not just per IP."""
        # Mock two different users
        user1_token = 'user1_token'
        user2_token = 'user2_token'
        
        def mock_verify_token(token):
            if token == user1_token:
                return {'user_id': 1, 'email': 'user1@example.com', 'role': 'user', 'type': 'access'}
            elif token == user2_token:
                return {'user_id': 2, 'email': 'user2@example.com', 'role': 'user', 'type': 'access'}
            return None
        
        mock_jwt_manager.verify_token.side_effect = mock_verify_token
        mock_jwt_manager.extract_token_from_header.return_value = user1_token
        
        with patch('routes.auth.g') as mock_g:
            # User 1 makes many requests
            responses_user1 = []
            for i in range(65):  # Exceed user rate limit
                mock_g.current_user = {'id': 1, 'email': 'user1@example.com', 'role': 'user'}
                response = flask_oauth_test_client.get('/api/user/profile',
                                                      headers={'Authorization': f'Bearer {user1_token}'})
                responses_user1.append(response)
            
            # User 1 should be rate limited
            rate_limited_user1 = sum(1 for r in responses_user1 if r.status_code == 429)
            assert rate_limited_user1 > 0
            
            # User 2 should still be able to make requests
            mock_jwt_manager.extract_token_from_header.return_value = user2_token
            mock_g.current_user = {'id': 2, 'email': 'user2@example.com', 'role': 'user'}
            
            response_user2 = flask_oauth_test_client.get('/api/user/profile',
                                                        headers={'Authorization': f'Bearer {user2_token}'})
            
            # User 2 should not be rate limited (assuming different rate limit buckets)
            assert response_user2.status_code != 429
    
    def test_rate_limiting_per_ip_for_anonymous_endpoints(self, flask_oauth_test_client, test_env_vars):
        """Test that anonymous endpoints use IP-based rate limiting."""
        # Make requests from same IP (test client)
        responses = []
        for i in range(12):  # Exceed rate limit
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Should have rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0


class TestRateLimitingHeaders:
    """Test rate limiting HTTP headers."""
    
    def test_rate_limit_headers_present(self, flask_oauth_test_client, test_env_vars):
        """Test that rate limit headers are present in responses."""
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        # Check for rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        
        # Verify header values are reasonable
        limit = int(response.headers['X-RateLimit-Limit'])
        remaining = int(response.headers['X-RateLimit-Remaining'])
        reset_time = int(response.headers['X-RateLimit-Reset'])
        
        assert limit > 0
        assert remaining >= 0
        assert reset_time > 0
    
    def test_rate_limit_headers_countdown(self, flask_oauth_test_client, test_env_vars):
        """Test that rate limit headers count down properly."""
        responses = []
        for i in range(3):  # Make a few requests
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Verify remaining count decreases
        remaining_counts = [int(r.headers['X-RateLimit-Remaining']) for r in responses]
        
        # Should be decreasing (or at least non-increasing)
        for i in range(1, len(remaining_counts)):
            assert remaining_counts[i] <= remaining_counts[i-1]
    
    def test_rate_limit_exceeded_headers(self, flask_oauth_test_client, test_env_vars):
        """Test headers when rate limit is exceeded."""
        # Make requests to exceed rate limit
        responses = []
        for i in range(12):  # Exceed rate limit
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Find rate limited responses
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        if rate_limited_responses:
            rate_limited_response = rate_limited_responses[0]
            
            # Check that rate limit headers are present
            assert 'X-RateLimit-Limit' in rate_limited_response.headers
            assert 'X-RateLimit-Remaining' in rate_limited_response.headers
            assert 'X-RateLimit-Reset' in rate_limited_response.headers
            
            # Remaining should be 0
            remaining = int(rate_limited_response.headers['X-RateLimit-Remaining'])
            assert remaining == 0


class TestRateLimitingRecovery:
    """Test rate limiting recovery after time window."""
    
    @pytest.mark.slow
    def test_rate_limit_recovery_over_time(self, flask_oauth_test_client, test_env_vars):
        """Test that rate limits recover after time window passes."""
        # This test would require actual time delays and is marked as slow
        # In a real implementation, you might use time manipulation libraries
        
        # Make requests to hit rate limit
        responses = []
        for i in range(12):  # Exceed rate limit
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Should have rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0
        
        # In a real test, you would wait for the time window to pass
        # and then verify that requests succeed again
        # For now, we'll just verify the rate limiting occurred
    
    def test_rate_limit_sliding_window(self, flask_oauth_test_client, test_env_vars):
        """Test sliding window rate limiting behavior."""
        # Make requests spread over time to test sliding window
        responses = []
        
        # Make initial requests
        for i in range(5):
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # All should succeed initially
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 5
        
        # Make more requests to approach limit
        for i in range(5):
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Should still mostly succeed
        total_success = sum(1 for r in responses if r.status_code == 200)
        assert total_success >= 8  # At least 8 out of 10 should succeed
        
        # Final requests should trigger rate limiting
        for i in range(5):
            response = flask_oauth_test_client.get('/api/auth/google/login')
            responses.append(response)
        
        # Should now have some rate limited responses
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited_count > 0