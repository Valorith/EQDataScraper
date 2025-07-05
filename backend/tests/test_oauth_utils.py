"""Test cases for OAuth utility functions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import base64
import hashlib
from datetime import datetime, timedelta

from utils.oauth import GoogleOAuth


class TestGoogleOAuth:
    """Test cases for GoogleOAuth class."""
    
    @pytest.fixture
    def oauth_client(self):
        """Create GoogleOAuth instance with test credentials."""
        with patch.dict('os.environ', {
            'GOOGLE_CLIENT_ID': 'test-client-id',
            'GOOGLE_CLIENT_SECRET': 'test-client-secret',
            'OAUTH_REDIRECT_URI': 'http://localhost:3000/auth/callback'
        }):
            return GoogleOAuth()
    
    def test_init_with_missing_credentials(self):
        """Test initialization fails without required credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Missing required OAuth configuration"):
                GoogleOAuth()
    
    def test_get_authorization_url(self, oauth_client):
        """Test authorization URL generation."""
        result = oauth_client.get_authorization_url()
        
        # Check returned dictionary
        assert 'auth_url' in result
        assert 'state' in result
        assert 'code_verifier' in result
        
        url = result['auth_url']
        state = result['state']
        code_verifier = result['code_verifier']
        
        # Check base URL
        assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth")
        
        # Check required parameters
        assert "client_id=test-client-id" in url
        assert f"state={state}" in url
        assert "code_challenge=" in url  # Challenge is generated, just check it exists
        assert "code_challenge_method=S256" in url
        assert "response_type=code" in url
        assert "scope=openid+email+profile" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
    
    @patch('requests.post')
    def test_exchange_code_for_tokens_success(self, mock_post, oauth_client):
        """Test successful code exchange for tokens."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'id_token': 'test-id-token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        tokens = oauth_client.exchange_code_for_tokens('test-code', 'test-verifier')
        
        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://oauth2.googleapis.com/token'
        
        # Check request data
        request_data = call_args[1]['data']
        assert request_data['code'] == 'test-code'
        assert request_data['code_verifier'] == 'test-verifier'
        assert request_data['client_id'] == 'test-client-id'
        assert request_data['client_secret'] == 'test-client-secret'
        assert request_data['grant_type'] == 'authorization_code'
        
        # Check response
        assert tokens['access_token'] == 'test-access-token'
        assert tokens['refresh_token'] == 'test-refresh-token'
    
    @patch('requests.post')
    def test_exchange_code_for_tokens_failure(self, mock_post, oauth_client):
        """Test failed code exchange."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid authorization code'
        mock_response.json.return_value = {'error': 'invalid_grant'}
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to exchange code for tokens"):
            oauth_client.exchange_code_for_tokens('invalid-code', 'test-verifier')
    
    @patch('requests.post')
    def test_refresh_access_token_success(self, mock_post, oauth_client):
        """Test successful token refresh."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        new_token = oauth_client.refresh_access_token('test-refresh-token')
        
        # Verify request
        mock_post.assert_called_once()
        request_data = mock_post.call_args[1]['data']
        assert request_data['refresh_token'] == 'test-refresh-token'
        assert request_data['grant_type'] == 'refresh_token'
        
        # Check response
        assert new_token == 'new-access-token'
    
    @patch('requests.get')
    def test_get_user_info_success(self, mock_get, oauth_client):
        """Test successful user info retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'google-user-id-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://example.com/photo.jpg',
            'verified_email': True
        }
        mock_get.return_value = mock_response
        
        user_info = oauth_client.get_user_info('test-access-token')
        
        # Verify request
        mock_get.assert_called_once_with(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': 'Bearer test-access-token'}
        )
        
        # Check response
        assert user_info['google_id'] == 'google-user-id-123'
        assert user_info['email'] == 'test@example.com'
        assert user_info['first_name'] == 'Test'
        assert user_info['last_name'] == 'User'
    
    @patch('requests.get')
    def test_get_user_info_unauthorized(self, mock_get, oauth_client):
        """Test user info retrieval with invalid token."""
        # Mock unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid token'
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to get user info"):
            oauth_client.get_user_info('invalid-token')
    


class TestOAuthHelpers:
    """Test cases for OAuth helper functions."""
    
    def test_generate_state(self, oauth_client):
        """Test state token generation."""
        state1 = oauth_client.generate_state()
        state2 = oauth_client.generate_state()
        
        # Check format and uniqueness
        assert len(state1) >= 32  # URL-safe token
        assert len(state2) >= 32
        assert state1 != state2
    
    def test_generate_pkce_pair(self, oauth_client):
        """Test PKCE pair generation."""
        verifier, challenge = oauth_client.generate_pkce_pair()
        
        # Check verifier format (43 chars for 32 bytes base64)
        assert len(verifier) == 43
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' 
                  for c in verifier)
        
        # Check challenge format (43 chars for SHA256 base64)
        assert len(challenge) == 43
        assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' 
                  for c in challenge)
        
        # Verify challenge is SHA256 of verifier
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip('=')
        assert challenge == expected_challenge
    
    def test_generate_pkce_pair_randomness(self, oauth_client):
        """Test PKCE pairs are random."""
        pairs = [oauth_client.generate_pkce_pair() for _ in range(10)]
        verifiers = [v for v, _ in pairs]
        challenges = [c for _, c in pairs]
        
        # All should be unique
        assert len(set(verifiers)) == 10
        assert len(set(challenges)) == 10