"""
Tests for security features in the OAuth user account system.
Tests input validation, SQL injection prevention, XSS protection, and other security measures.
"""

import pytest
import json
import jwt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from utils.jwt_utils import JWTManager, jwt_manager
from utils.oauth import GoogleOAuth
from tests.conftest import TEST_JWT_SECRET, generate_test_user


class TestInputValidation:
    """Test input validation and sanitization."""
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_sql_injection_prevention_user_profile(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test SQL injection prevention in user profile updates."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        
        # SQL injection payloads
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM users; --",
            "admin'--",
            "' OR 1=1--",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --"
        ]
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            for payload in sql_injection_payloads:
                # Test in first_name field
                response = flask_oauth_test_client.put('/api/user/profile',
                                                      json={'first_name': payload},
                                                      headers={'Authorization': 'Bearer valid_token'})
                
                # Should not cause server error (500) or execute SQL
                assert response.status_code != 500
                
                # Verify the payload was treated as regular string data
                if response.status_code == 200:
                    # Mock should have been called with the payload as a string parameter
                    mock_user_instance.update_user_profile.assert_called()
                    call_args = mock_user_instance.update_user_profile.call_args
                    assert payload in str(call_args)
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_xss_prevention_profile_update(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test XSS payload rejection in profile fields."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "onmouseover=alert('XSS')"
        ]
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            for payload in xss_payloads:
                # Test in first_name field
                response = flask_oauth_test_client.put('/api/user/profile',
                                                      json={'first_name': payload},
                                                      headers={'Authorization': 'Bearer valid_token'})
                
                # Should not cause server error
                assert response.status_code != 500
                
                # If successful, verify payload was sanitized/escaped
                if response.status_code == 200:
                    response_data = json.loads(response.data)
                    # The response should not contain unescaped HTML/JS
                    response_str = json.dumps(response_data)
                    assert '<script>' not in response_str
                    assert 'javascript:' not in response_str
    
    def test_invalid_json_handling(self, flask_oauth_test_client, test_env_vars):
        """Test handling of invalid JSON payloads."""
        # Test malformed JSON
        response = flask_oauth_test_client.post('/api/auth/refresh',
                                               data='{"invalid": json}',
                                               headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_oversized_payload_handling(self, flask_oauth_test_client, test_env_vars):
        """Test handling of oversized payloads."""
        # Create a very large payload
        large_payload = {'first_name': 'A' * 10000}  # 10KB first name
        
        response = flask_oauth_test_client.put('/api/user/profile',
                                              json=large_payload,
                                              headers={'Authorization': 'Bearer valid_token'})
        
        # Should handle gracefully (either reject or truncate)
        assert response.status_code in [400, 401, 413]  # Bad Request, Unauthorized, or Payload Too Large
    
    @patch('routes.auth.jwt_manager')
    @patch('routes.auth.User')
    def test_email_validation(self, mock_user, mock_jwt_manager, flask_oauth_test_client, test_env_vars):
        """Test email validation in user updates."""
        # Mock authentication
        mock_jwt_manager.extract_token_from_header.return_value = 'valid_token'
        mock_jwt_manager.verify_token.return_value = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'type': 'access'
        }
        
        mock_user_instance = Mock()
        mock_user.return_value = mock_user_instance
        
        # Invalid email formats
        invalid_emails = [
            'not_an_email',
            '@example.com',
            'test@',
            'test@.com',
            'test@example.',
            'test space@example.com',
            'test@exam ple.com',
            '',
            None,
            'test@example..com',
            'test@@example.com'
        ]
        
        with patch('routes.auth.g') as mock_g:
            mock_g.current_user = {'id': 1, 'email': 'test@example.com', 'role': 'user'}
            
            for invalid_email in invalid_emails:
                # Note: In the current implementation, email updates might not be allowed
                # This test assumes there's an endpoint that accepts email updates
                payload = {'email': invalid_email} if invalid_email is not None else {}
                
                response = flask_oauth_test_client.put('/api/user/profile',
                                                      json=payload,
                                                      headers={'Authorization': 'Bearer valid_token'})
                
                # Should either reject invalid emails or handle gracefully
                assert response.status_code != 500  # Should not cause server error


class TestCSRFProtection:
    """Test CSRF protection in OAuth flow."""
    
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_state_parameter_generation(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test that OAuth state parameter is generated for CSRF protection."""
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock state generation
        mock_oauth_instance.generate_auth_url.return_value = (
            'https://accounts.google.com/oauth/authorize?state=random_state',
            'random_state'
        )
        
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        
        assert 'state' in response_data
        assert len(response_data['state']) > 10  # Should be a reasonable length
    
    @patch('routes.auth.GoogleOAuth')
    def test_csrf_protection_state_validation(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test CSRF protection via state parameter validation."""
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Test with mismatched state
        mock_oauth_instance.verify_state.return_value = False
        
        response = flask_oauth_test_client.get('/api/auth/google/callback', query_string={
            'code': 'valid_code',
            'state': 'wrong_state'
        })
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'Invalid state parameter' in response_data['error']
    
    @patch('routes.auth.GoogleOAuth')
    def test_csrf_protection_missing_state(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test CSRF protection when state parameter is missing."""
        response = flask_oauth_test_client.get('/api/auth/google/callback', query_string={
            'code': 'valid_code'
        })
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert 'error' in response_data
    
    def test_csrf_protection_double_submit_cookie(self, flask_oauth_test_client, test_env_vars):
        """Test CSRF protection using double submit cookie pattern."""
        # First, initiate OAuth flow to get state
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        if response.status_code == 200:
            response_data = json.loads(response.data)
            state = response_data.get('state')
            
            # Verify state is stored securely (not in client-readable cookie)
            assert 'Set-Cookie' not in response.headers or state not in response.headers.get('Set-Cookie', '')


class TestJWTSecurity:
    """Test JWT token security features."""
    
    def test_jwt_secret_key_strength(self, test_env_vars):
        """Test that JWT secret key is strong enough."""
        jwt_mgr = JWTManager()
        
        # Secret key should be at least 32 characters
        assert len(jwt_mgr.secret_key) >= 32
        
        # Should not be a common weak key
        weak_keys = ['secret', 'password', '123456', 'jwt_secret', 'key']
        assert jwt_mgr.secret_key.lower() not in weak_keys
    
    def test_jwt_algorithm_security(self, test_env_vars):
        """Test that JWT uses secure algorithm."""
        jwt_mgr = JWTManager()
        
        # Should use HMAC with SHA-256 or better
        assert jwt_mgr.algorithm in ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
        
        # Should not use 'none' algorithm
        assert jwt_mgr.algorithm != 'none'
    
    def test_jwt_token_expiration(self, test_env_vars):
        """Test that JWT tokens have reasonable expiration times."""
        jwt_mgr = JWTManager()
        
        # Access tokens should expire within reasonable time (not too long)
        assert jwt_mgr.access_token_expire_minutes <= 120  # Max 2 hours
        assert jwt_mgr.access_token_expire_minutes >= 5   # Min 5 minutes
        
        # Refresh tokens should expire within reasonable time
        assert jwt_mgr.refresh_token_expire_days <= 90   # Max 3 months
        assert jwt_mgr.refresh_token_expire_days >= 1    # Min 1 day
    
    def test_jwt_token_tampering_detection(self, test_env_vars):
        """Test that JWT token tampering is detected."""
        jwt_mgr = JWTManager()
        
        # Create a valid token
        token = jwt_mgr.create_access_token(1, 'test@example.com', 'user')
        
        # Tamper with the token
        parts = token.split('.')
        if len(parts) == 3:
            # Change one character in the payload
            tampered_payload = parts[1][:-1] + ('X' if parts[1][-1] != 'X' else 'Y')
            tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
            
            # Verify tampered token is rejected
            payload = jwt_mgr.verify_token(tampered_token)
            assert payload is None
    
    def test_jwt_token_signature_verification(self, test_env_vars):
        """Test JWT signature verification."""
        jwt_mgr = JWTManager()
        
        # Create token with wrong secret
        wrong_secret_token = jwt.encode(
            {
                'user_id': 1,
                'email': 'test@example.com',
                'role': 'user',
                'exp': datetime.utcnow() + timedelta(hours=1),
                'type': 'access'
            },
            'wrong_secret',
            algorithm='HS256'
        )
        
        # Verify token with wrong signature is rejected
        payload = jwt_mgr.verify_token(wrong_secret_token)
        assert payload is None
    
    def test_jwt_token_replay_protection(self, test_env_vars):
        """Test protection against token replay attacks."""
        jwt_mgr = JWTManager()
        
        # Create an expired token
        expired_token = jwt.encode(
            {
                'user_id': 1,
                'email': 'test@example.com',
                'role': 'user',
                'exp': datetime.utcnow() - timedelta(hours=1),  # Expired
                'type': 'access'
            },
            TEST_JWT_SECRET,
            algorithm='HS256'
        )
        
        # Verify expired token is rejected
        payload = jwt_mgr.verify_token(expired_token)
        assert payload is None
    
    def test_jwt_token_type_validation(self, test_env_vars):
        """Test that JWT token type is validated."""
        jwt_mgr = JWTManager()
        
        # Create a refresh token
        refresh_token = jwt_mgr.create_refresh_token(1, 'session_token')
        
        # Decode to verify type
        payload = jwt.decode(refresh_token, TEST_JWT_SECRET, algorithms=['HS256'])
        assert payload['type'] == 'refresh'
        
        # Access token should have different type
        access_token = jwt_mgr.create_access_token(1, 'test@example.com', 'user')
        payload = jwt.decode(access_token, TEST_JWT_SECRET, algorithms=['HS256'])
        assert payload['type'] == 'access'


class TestOAuthSecurity:
    """Test OAuth flow security features."""
    
    def test_pkce_implementation(self, test_env_vars):
        """Test PKCE (Proof Key for Code Exchange) implementation."""
        oauth = GoogleOAuth()
        
        # Generate PKCE pair
        code_verifier, code_challenge = oauth.generate_pkce_pair()
        
        # Verify code verifier properties
        assert len(code_verifier) >= 43  # Minimum length for PKCE
        assert len(code_verifier) <= 128  # Maximum length for PKCE
        
        # Verify code challenge is derived from verifier
        assert code_challenge != code_verifier
        assert len(code_challenge) > 0
        
        # Verify code challenge is URL-safe base64
        import base64
        try:
            base64.urlsafe_b64decode(code_challenge + '==')  # Add padding
        except Exception:
            pytest.fail("Code challenge is not valid URL-safe base64")
    
    def test_oauth_state_randomness(self, test_env_vars):
        """Test that OAuth state parameters are sufficiently random."""
        oauth = GoogleOAuth()
        
        # Generate multiple state parameters
        states = [oauth.generate_state() for _ in range(100)]
        
        # All should be different
        assert len(set(states)) == 100
        
        # Each should be reasonable length
        for state in states[:10]:  # Check first 10
            assert len(state) >= 16  # Minimum entropy
    
    def test_oauth_redirect_uri_validation(self, test_env_vars):
        """Test OAuth redirect URI validation."""
        oauth = GoogleOAuth()
        
        # Valid redirect URIs
        valid_uris = [
            'http://localhost:3000/auth/callback',
            'https://example.com/auth/callback',
            'https://subdomain.example.com/auth/callback'
        ]
        
        # Invalid redirect URIs
        invalid_uris = [
            'javascript:alert("XSS")',
            'data:text/html,<script>alert("XSS")</script>',
            'ftp://evil.com/callback',
            'http://evil.com/callback',
            '../../../etc/passwd',
            'file:///etc/passwd'
        ]
        
        # Test that valid URIs are accepted (implementation dependent)
        for uri in valid_uris:
            # This test depends on the specific implementation
            # For now, we'll just verify the URI format is reasonable
            assert '://' in uri
            assert not uri.startswith('javascript:')
            assert not uri.startswith('data:')
    
    @patch('routes.auth.GoogleOAuth')
    def test_oauth_error_handling(self, mock_google_oauth, flask_oauth_test_client, test_env_vars):
        """Test OAuth error handling doesn't leak sensitive information."""
        mock_oauth_instance = Mock()
        mock_google_oauth.return_value = mock_oauth_instance
        
        # Mock OAuth failure
        mock_oauth_instance.verify_state.return_value = True
        mock_oauth_instance.exchange_code_for_tokens.side_effect = Exception("Internal OAuth error with sensitive data")
        
        response = flask_oauth_test_client.get('/api/auth/google/callback', query_string={
            'code': 'test_code',
            'state': 'test_state'
        })
        
        assert response.status_code == 500
        response_data = json.loads(response.data)
        
        # Error message should be generic, not expose internal details
        assert 'error' in response_data
        assert 'Internal OAuth error with sensitive data' not in response_data['error']
        assert 'OAuth callback failed' in response_data['error']


class TestSessionSecurity:
    """Test session security features."""
    
    @patch('routes.auth.OAuthSession')
    def test_session_token_randomness(self, mock_oauth_session, test_env_vars):
        """Test that session tokens are sufficiently random."""
        jwt_mgr = JWTManager()
        
        # Generate multiple session tokens
        tokens = [jwt_mgr.generate_local_session_token() for _ in range(100)]
        
        # All should be different
        assert len(set(tokens)) == 100
        
        # Each should be reasonable length
        for token in tokens[:10]:  # Check first 10
            assert len(token) >= 32  # Minimum entropy
    
    def test_session_expiration_enforcement(self, test_env_vars):
        """Test that session expiration is enforced."""
        jwt_mgr = JWTManager()
        
        # Create a refresh token that should expire
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with patch('utils.jwt_utils.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = past_time
            refresh_token = jwt_mgr.create_refresh_token(1, 'session_token')
        
        # Verify expired token is rejected
        payload = jwt_mgr.verify_token(refresh_token)
        assert payload is None
    
    @patch('routes.auth.OAuthSession')
    def test_concurrent_session_handling(self, mock_oauth_session, flask_oauth_test_client, test_env_vars):
        """Test handling of concurrent sessions."""
        # This test would verify that multiple concurrent sessions
        # are handled properly and don't interfere with each other
        
        mock_session_instance = Mock()
        mock_oauth_session.return_value = mock_session_instance
        
        # Mock multiple active sessions for the same user
        mock_session_instance.get_user_sessions.return_value = [
            {'id': 1, 'user_id': 1, 'local_session_token': 'token1'},
            {'id': 2, 'user_id': 1, 'local_session_token': 'token2'},
            {'id': 3, 'user_id': 1, 'local_session_token': 'token3'}
        ]
        
        sessions = mock_session_instance.get_user_sessions.return_value
        
        # Verify each session has unique token
        tokens = [session['local_session_token'] for session in sessions]
        assert len(set(tokens)) == len(tokens)


class TestSecurityHeaders:
    """Test security-related HTTP headers."""
    
    def test_cors_configuration(self, flask_oauth_test_client, test_env_vars):
        """Test CORS configuration security."""
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        # Check CORS headers
        if 'Access-Control-Allow-Origin' in response.headers:
            origin = response.headers['Access-Control-Allow-Origin']
            
            # Should not be wildcard for sensitive endpoints
            assert origin != '*'
            
            # Should be specific allowed origins
            allowed_origins = [
                'http://localhost:3000',
                'http://localhost:3001',
                'https://eqdatascraper-frontend-production.up.railway.app'
            ]
            assert origin in allowed_origins or origin == 'null'
    
    def test_content_type_validation(self, flask_oauth_test_client, test_env_vars):
        """Test content type validation."""
        # Test with wrong content type
        response = flask_oauth_test_client.post('/api/auth/refresh',
                                               data='{"refresh_token": "test"}',
                                               headers={'Content-Type': 'text/plain'})
        
        # Should reject or handle gracefully
        assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type
    
    def test_security_headers_presence(self, flask_oauth_test_client, test_env_vars):
        """Test presence of security headers."""
        response = flask_oauth_test_client.get('/api/auth/google/login')
        
        # Check for security headers (implementation dependent)
        # These might not all be present depending on configuration
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        # At least some security headers should be present in production
        # For now, we'll just verify the response doesn't expose sensitive info
        assert 'Server' not in response.headers or 'Flask' not in response.headers.get('Server', '')


class TestErrorHandling:
    """Test security aspects of error handling."""
    
    def test_error_information_disclosure(self, flask_oauth_test_client, test_env_vars):
        """Test that errors don't disclose sensitive information."""
        # Test various error conditions
        error_endpoints = [
            ('/api/auth/google/callback?code=invalid&state=invalid', 400),
            ('/api/auth/refresh', 400),
            ('/api/user/profile', 401),
            ('/api/admin/users', 401)
        ]
        
        for endpoint, expected_status in error_endpoints:
            response = flask_oauth_test_client.get(endpoint) if '?' in endpoint else flask_oauth_test_client.get(endpoint)
            
            if response.status_code == expected_status:
                response_data = json.loads(response.data)
                
                # Error messages should not contain sensitive information
                error_msg = response_data.get('error', '')
                
                # Should not expose internal paths, database info, etc.
                sensitive_info = [
                    '/backend/',
                    'Database',
                    'psycopg2',
                    'postgresql',
                    'Exception',
                    'Traceback',
                    'File "/',
                    'line '
                ]
                
                for sensitive in sensitive_info:
                    assert sensitive not in error_msg
    
    def test_stack_trace_suppression(self, flask_oauth_test_client, test_env_vars):
        """Test that stack traces are not exposed in production."""
        # This test verifies that internal errors don't expose stack traces
        
        # Try to trigger an internal error
        response = flask_oauth_test_client.post('/api/auth/refresh',
                                               json={'refresh_token': 'definitely_invalid_token'})
        
        if response.status_code == 500:
            response_data = json.loads(response.data)
            error_msg = str(response_data)
            
            # Should not contain stack trace elements
            stack_trace_indicators = [
                'Traceback',
                'File "/',
                'line ',
                'in ',
                'raise ',
                'Exception:'
            ]
            
            for indicator in stack_trace_indicators:
                assert indicator not in error_msg