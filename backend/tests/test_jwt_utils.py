"""
Tests for JWT utilities and authentication decorators.
Tests JWT token creation, validation, and security features.
"""

import pytest
import jwt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask, request, g

from utils.jwt_utils import (
    JWTManager, jwt_manager, require_auth, require_admin, 
    get_current_user, create_error_response, create_success_response
)
from tests.conftest import TEST_JWT_SECRET


class TestJWTManager:
    """Test JWTManager class functionality."""
    
    def test_init_with_env_vars(self, test_env_vars):
        """Test JWTManager initialization with environment variables."""
        jwt_mgr = JWTManager()
        assert jwt_mgr.secret_key == TEST_JWT_SECRET
        assert jwt_mgr.algorithm == 'HS256'
        assert jwt_mgr.access_token_expire_minutes == 60
        assert jwt_mgr.refresh_token_expire_days == 30
    
    def test_init_without_env_vars(self):
        """Test JWTManager initialization fails without JWT_SECRET_KEY."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                JWTManager()
            assert "JWT_SECRET_KEY environment variable is required" in str(exc_info.value)
    
    def test_generate_local_session_token(self, test_env_vars):
        """Test local session token generation."""
        jwt_mgr = JWTManager()
        token = jwt_mgr.generate_local_session_token()
        
        assert isinstance(token, str)
        assert len(token) > 10  # Should be a reasonable length
        
        # Generate another token and ensure they're different
        token2 = jwt_mgr.generate_local_session_token()
        assert token != token2
    
    def test_create_access_token(self, test_env_vars):
        """Test access token creation."""
        jwt_mgr = JWTManager()
        token = jwt_mgr.create_access_token(
            user_id=1,
            user_email="test@example.com",
            user_role="user"
        )
        
        assert isinstance(token, str)
        
        # Decode and verify token contents
        decoded = jwt.decode(token, TEST_JWT_SECRET, algorithms=['HS256'])
        assert decoded['user_id'] == 1
        assert decoded['email'] == "test@example.com"
        assert decoded['role'] == "user"
        assert decoded['type'] == 'access'
        assert 'iat' in decoded
        assert 'exp' in decoded
    
    def test_create_refresh_token(self, test_env_vars):
        """Test refresh token creation."""
        jwt_mgr = JWTManager()
        token = jwt_mgr.create_refresh_token(
            user_id=1,
            session_token="test_session_token"
        )
        
        assert isinstance(token, str)
        
        # Decode and verify token contents
        decoded = jwt.decode(token, TEST_JWT_SECRET, algorithms=['HS256'])
        assert decoded['user_id'] == 1
        assert decoded['session_token'] == "test_session_token"
        assert decoded['type'] == 'refresh'
        assert 'iat' in decoded
        assert 'exp' in decoded
    
    def test_verify_valid_token(self, test_env_vars):
        """Test verification of valid token."""
        jwt_mgr = JWTManager()
        
        # Create a token
        token = jwt_mgr.create_access_token(1, "test@example.com", "user")
        
        # Verify the token
        payload = jwt_mgr.verify_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 1
        assert payload['email'] == "test@example.com"
        assert payload['role'] == "user"
    
    def test_verify_expired_token(self, test_env_vars):
        """Test verification of expired token."""
        jwt_mgr = JWTManager()
        
        # Create an expired token by manipulating time
        past_time = datetime.utcnow() - timedelta(hours=2)
        
        with patch('utils.jwt_utils.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = past_time
            token = jwt_mgr.create_access_token(1, "test@example.com", "user")
        
        # Verify the expired token
        payload = jwt_mgr.verify_token(token)
        assert payload is None  # Should return None for expired token
    
    def test_verify_invalid_token(self, test_env_vars):
        """Test verification of invalid/malformed token."""
        jwt_mgr = JWTManager()
        
        # Test with completely invalid token
        payload = jwt_mgr.verify_token("invalid.token.here")
        assert payload is None
        
        # Test with token signed with different secret
        wrong_token = jwt.encode(
            {'user_id': 1, 'exp': datetime.utcnow() + timedelta(hours=1)},
            'wrong_secret',
            algorithm='HS256'
        )
        payload = jwt_mgr.verify_token(wrong_token)
        assert payload is None
    
    def test_extract_token_from_header_valid(self, test_env_vars):
        """Test extracting token from valid Authorization header."""
        jwt_mgr = JWTManager()
        
        auth_header = "Bearer test_token_here"
        token = jwt_mgr.extract_token_from_header(auth_header)
        
        assert token == "test_token_here"
    
    def test_extract_token_from_header_invalid(self, test_env_vars):
        """Test extracting token from invalid Authorization header."""
        jwt_mgr = JWTManager()
        
        # Test various invalid formats
        assert jwt_mgr.extract_token_from_header(None) is None
        assert jwt_mgr.extract_token_from_header("") is None
        assert jwt_mgr.extract_token_from_header("InvalidFormat") is None
        assert jwt_mgr.extract_token_from_header("Basic username:password") is None
        assert jwt_mgr.extract_token_from_header("Bearer") is None  # Missing token
    
    @patch('models.user.User')
    @patch('models.user.OAuthSession')
    def test_refresh_access_token_success(self, mock_oauth_session, mock_user, test_env_vars):
        """Test successful access token refresh."""
        jwt_mgr = JWTManager()
        
        # Create a valid refresh token
        refresh_token = jwt_mgr.create_refresh_token(1, "test_session_token")
        
        # Mock user and session models
        mock_user_instance = Mock()
        mock_session_instance = Mock()
        
        # Mock session exists and is valid
        mock_session_instance.get_session_by_token.return_value = {
            'id': 1,
            'user_id': 1
        }
        
        # Mock user exists
        mock_user_instance.get_user_by_id.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'role': 'user'
        }
        
        # Test token refresh
        result = jwt_mgr.refresh_access_token(
            refresh_token, 
            mock_user_instance, 
            mock_session_instance
        )
        
        assert result is not None
        assert 'access_token' in result
        assert 'user' in result
        assert result['user']['id'] == 1
        
        # Verify session last used was updated
        mock_session_instance.update_session_last_used.assert_called_once()
    
    @patch('models.user.User')
    @patch('models.user.OAuthSession')
    def test_refresh_access_token_invalid_token(self, mock_oauth_session, mock_user, test_env_vars):
        """Test token refresh with invalid refresh token."""
        jwt_mgr = JWTManager()
        
        mock_user_instance = Mock()
        mock_session_instance = Mock()
        
        # Test with invalid token
        result = jwt_mgr.refresh_access_token(
            "invalid_token", 
            mock_user_instance, 
            mock_session_instance
        )
        
        assert result is None
    
    @patch('models.user.User')
    @patch('models.user.OAuthSession')
    def test_refresh_access_token_session_not_found(self, mock_oauth_session, mock_user, test_env_vars):
        """Test token refresh when session doesn't exist."""
        jwt_mgr = JWTManager()
        
        # Create a valid refresh token
        refresh_token = jwt_mgr.create_refresh_token(1, "nonexistent_session")
        
        mock_user_instance = Mock()
        mock_session_instance = Mock()
        
        # Mock session not found
        mock_session_instance.get_session_by_token.return_value = None
        
        result = jwt_mgr.refresh_access_token(
            refresh_token, 
            mock_user_instance, 
            mock_session_instance
        )
        
        assert result is None


class TestAuthenticationDecorators:
    """Test authentication decorators."""
    
    def test_require_auth_decorator_with_valid_token(self, test_env_vars):
        """Test require_auth decorator with valid token."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer valid_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'valid_token'
                mock_verify.return_value = {
                    'user_id': 1,
                    'email': 'test@example.com',
                    'role': 'user',
                    'type': 'access'
                }
                
                @require_auth
                def protected_route():
                    return {'user_id': g.current_user['id']}
                
                result = protected_route()
                
                assert result['user_id'] == 1
                assert g.current_user['email'] == 'test@example.com'
    
    def test_require_auth_decorator_without_token(self):
        """Test require_auth decorator without Authorization header."""
        app = Flask(__name__)
        
        with app.test_request_context():
            @require_auth
            def protected_route():
                return {'success': True}
            
            response, status = protected_route()
            
            assert status == 401
            assert 'error' in response.json
            assert 'Authorization header required' in response.json['error']
    
    def test_require_auth_decorator_with_invalid_token(self, test_env_vars):
        """Test require_auth decorator with invalid token."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer invalid_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'invalid_token'
                mock_verify.return_value = None  # Invalid token
                
                @require_auth
                def protected_route():
                    return {'success': True}
                
                response, status = protected_route()
                
                assert status == 401
                assert 'error' in response.json
                assert 'Invalid or expired token' in response.json['error']
    
    def test_require_admin_decorator_with_admin_user(self, test_env_vars):
        """Test require_admin decorator with admin user."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer admin_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'admin_token'
                mock_verify.return_value = {
                    'user_id': 1,
                    'email': 'admin@example.com',
                    'role': 'admin',
                    'type': 'access'
                }
                
                @require_admin
                def admin_route():
                    return {'admin_user_id': g.current_user['id']}
                
                result = admin_route()
                
                assert result['admin_user_id'] == 1
                assert g.current_user['role'] == 'admin'
    
    def test_require_admin_decorator_with_regular_user(self, test_env_vars):
        """Test require_admin decorator with regular user (should fail)."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer user_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'user_token'
                mock_verify.return_value = {
                    'user_id': 1,
                    'email': 'user@example.com',
                    'role': 'user',  # Not admin
                    'type': 'access'
                }
                
                @require_admin
                def admin_route():
                    return {'success': True}
                
                response, status = admin_route()
                
                assert status == 403
                assert 'error' in response.json
                assert 'Admin access required' in response.json['error']


class TestUtilityFunctions:
    """Test utility functions for authentication."""
    
    def test_get_current_user_with_valid_token(self, test_env_vars):
        """Test get_current_user with valid token."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer valid_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'valid_token'
                mock_verify.return_value = {
                    'user_id': 1,
                    'email': 'test@example.com',
                    'role': 'user',
                    'type': 'access'
                }
                
                user = get_current_user()
                
                assert user is not None
                assert user['id'] == 1
                assert user['email'] == 'test@example.com'
                assert user['role'] == 'user'
    
    def test_get_current_user_without_token(self):
        """Test get_current_user without token."""
        app = Flask(__name__)
        
        with app.test_request_context():
            user = get_current_user()
            assert user is None
    
    def test_get_current_user_with_invalid_token(self, test_env_vars):
        """Test get_current_user with invalid token."""
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': 'Bearer invalid_token'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = 'invalid_token'
                mock_verify.return_value = None
                
                user = get_current_user()
                assert user is None
    
    def test_create_error_response(self):
        """Test error response creation."""
        app = Flask(__name__)
        
        with app.app_context():
            response, status = create_error_response("Test error message", 400)
            
            assert status == 400
            assert response.json['error'] == "Test error message"
            assert 'timestamp' in response.json
    
    def test_create_success_response(self):
        """Test success response creation."""
        test_data = {'key': 'value'}
        response = create_success_response(test_data, "Success message")
        
        assert response['success'] is True
        assert response['data'] == test_data
        assert response['message'] == "Success message"
        assert 'timestamp' in response
    
    def test_create_success_response_without_message(self):
        """Test success response creation without message."""
        test_data = {'key': 'value'}
        response = create_success_response(test_data)
        
        assert response['success'] is True
        assert response['data'] == test_data
        assert 'message' not in response
        assert 'timestamp' in response


class TestJWTSecurity:
    """Test JWT security features."""
    
    def test_token_tampering_detection(self, test_env_vars):
        """Test that tampered tokens are rejected."""
        jwt_mgr = JWTManager()
        
        # Create a valid token
        token = jwt_mgr.create_access_token(1, "test@example.com", "user")
        
        # Tamper with the token
        parts = token.split('.')
        tampered_token = parts[0] + '.tampered.' + parts[2]
        
        # Verify tampered token is rejected
        payload = jwt_mgr.verify_token(tampered_token)
        assert payload is None
    
    def test_token_signature_validation(self, test_env_vars):
        """Test that tokens with wrong signatures are rejected."""
        jwt_mgr = JWTManager()
        
        # Create token with wrong secret
        wrong_token = jwt.encode(
            {
                'user_id': 1,
                'email': 'test@example.com',
                'role': 'user',
                'exp': datetime.utcnow() + timedelta(hours=1),
                'type': 'access'
            },
            'wrong_secret_key',
            algorithm='HS256'
        )
        
        # Verify token is rejected
        payload = jwt_mgr.verify_token(wrong_token)
        assert payload is None
    
    def test_token_type_validation(self, test_env_vars):
        """Test that token type is properly validated."""
        jwt_mgr = JWTManager()
        
        # Create refresh token
        refresh_token = jwt_mgr.create_refresh_token(1, "session_token")
        
        app = Flask(__name__)
        
        with app.test_request_context(
            headers={'Authorization': f'Bearer {refresh_token}'}
        ):
            with patch.object(jwt_manager, 'extract_token_from_header') as mock_extract, \
                 patch.object(jwt_manager, 'verify_token') as mock_verify:
                
                mock_extract.return_value = refresh_token
                # Return actual decoded refresh token
                mock_verify.return_value = {
                    'user_id': 1,
                    'session_token': 'session_token',
                    'type': 'refresh'  # Wrong type for access
                }
                
                @require_auth
                def protected_route():
                    return {'success': True}
                
                response, status = protected_route()
                
                assert status == 401
                assert 'Invalid or expired token' in response.json['error']