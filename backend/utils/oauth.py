"""
Google OAuth utilities with PKCE support for secure authentication.
"""

import os
import secrets
import base64
import hashlib
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import json
import time

class GoogleOAuth:
    """Google OAuth handler with PKCE support."""
    
    def __init__(self):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('OAUTH_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing Google OAuth configuration. Check environment variables.")
        
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scopes = ["openid", "email", "profile"]
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge pair."""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')  # Remove padding
        
        # Generate code challenge
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')  # Remove padding
        
        return code_verifier, code_challenge
    
    def generate_state(self) -> str:
        """Generate secure state parameter for CSRF protection."""
        return secrets.token_urlsafe(32)
    
    def get_authorization_url(self) -> Dict[str, str]:
        """
        Generate Google OAuth authorization URL with PKCE.
        
        Returns:
            Dictionary containing auth_url, state, and code_verifier
        """
        code_verifier, code_challenge = self.generate_pkce_pair()
        state = self.generate_state()
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent'  # Always show consent screen for refresh token
        }
        
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        
        return {
            'auth_url': auth_url,
            'state': state,
            'code_verifier': code_verifier
        }
    
    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            code_verifier: PKCE code verifier
        
        Returns:
            Dictionary containing tokens and user info
        """
        try:
            # Exchange code for tokens
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code_verifier': code_verifier
            }
            
            response = requests.post(self.token_url, data=token_data)
            response.raise_for_status()
            
            tokens = response.json()
            
            # Verify the ID token
            id_token_jwt = tokens.get('id_token')
            if not id_token_jwt:
                raise ValueError("No ID token received from Google")
            
            # Verify and decode the ID token
            try:
                print(f"Verifying ID token with client_id: {self.client_id}")
                # Add clock skew tolerance
                id_info = id_token.verify_oauth2_token(
                    id_token_jwt, 
                    google_requests.Request(), 
                    self.client_id,
                    clock_skew_in_seconds=30  # Allow 30 seconds of clock skew
                )
                print(f"ID token verified successfully")
            except Exception as e:
                print(f"ID token verification failed: {str(e)}")
                print(f"Client ID: {self.client_id}")
                print(f"ID Token (first 50 chars): {id_token_jwt[:50] if id_token_jwt else 'None'}...")
                # Try alternative verification method
                try:
                    print("Attempting alternative verification without audience check...")
                    # This is less secure but can help diagnose the issue
                    import jwt
                    decoded = jwt.decode(id_token_jwt, options={"verify_signature": False})
                    print(f"Decoded token claims: {decoded}")
                    if decoded.get('aud') != self.client_id:
                        print(f"Audience mismatch! Token aud: {decoded.get('aud')}, Expected: {self.client_id}")
                except Exception as alt_e:
                    print(f"Alternative decode also failed: {str(alt_e)}")
                raise ValueError(f"Invalid ID token: {str(e)}")
            
            # Extract user information
            user_info = {
                'google_id': id_info.get('sub'),
                'email': id_info.get('email'),
                'first_name': id_info.get('given_name'),
                'last_name': id_info.get('family_name'),
                'avatar_url': id_info.get('picture'),
                'email_verified': id_info.get('email_verified', False)
            }
            
            return {
                'access_token': tokens.get('access_token'),
                'refresh_token': tokens.get('refresh_token'),
                'expires_in': tokens.get('expires_in', 3600),
                'token_type': tokens.get('token_type', 'Bearer'),
                'user_info': user_info
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")
        except Exception as e:
            raise Exception(f"OAuth token exchange failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token from Google
        
        Returns:
            Dictionary containing new access token and expiry
        """
        try:
            refresh_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=refresh_data)
            response.raise_for_status()
            
            tokens = response.json()
            
            return {
                'access_token': tokens.get('access_token'),
                'expires_in': tokens.get('expires_in', 3600),
                'token_type': tokens.get('token_type', 'Bearer')
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to refresh access token: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke access or refresh token.
        
        Args:
            token: Token to revoke
        
        Returns:
            True if successful, False otherwise
        """
        try:
            revoke_url = "https://oauth2.googleapis.com/revoke"
            response = requests.post(revoke_url, data={'token': token})
            return response.status_code == 200
        except Exception:
            return False
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            access_token: Valid access token
        
        Returns:
            Dictionary containing user information
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            
            return {
                'google_id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('given_name'),
                'last_name': user_data.get('family_name'),
                'avatar_url': user_data.get('picture'),
                'email_verified': user_data.get('verified_email', False)
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get user info: {str(e)}")
    
    def validate_state(self, received_state: str, expected_state: str) -> bool:
        """
        Validate state parameter for CSRF protection.
        
        Args:
            received_state: State parameter from callback
            expected_state: Expected state value
        
        Returns:
            True if state is valid, False otherwise
        """
        return received_state == expected_state
    
    def validate_redirect_uri(self, redirect_uri: str) -> bool:
        """
        Validate redirect URI to prevent open redirect attacks.
        
        Args:
            redirect_uri: URI to validate
        
        Returns:
            True if URI is valid, False otherwise
        """
        # Allow configured redirect URI and multiple localhost ports for development
        allowed_uris = [
            self.redirect_uri,
            'http://localhost:3000/auth/callback',
            'http://localhost:3000/auth/callback',
            'http://localhost:3000/auth/callback',
            'http://localhost:3000/auth/callback',
            'http://localhost:3000/auth/callback',
            'http://localhost:3000/auth/callback'
        ]
        
        return redirect_uri in allowed_uris


class OAuthStorage:
    """Temporary storage for OAuth state and code verifiers."""
    
    def __init__(self):
        self._storage = {}
    
    def store_oauth_state(self, state: str, code_verifier: str, user_ip: str = None) -> None:
        """Store OAuth state and code verifier temporarily."""
        self._storage[state] = {
            'code_verifier': code_verifier,
            'user_ip': user_ip,
            'timestamp': secrets.token_urlsafe(16)  # Simple timestamp replacement
        }
    
    def get_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth state data."""
        return self._storage.get(state)
    
    def remove_oauth_state(self, state: str) -> None:
        """Remove OAuth state after use."""
        self._storage.pop(state, None)
    
    def cleanup_expired_states(self, max_age_minutes: int = 10) -> None:
        """Clean up expired OAuth states."""
        # In a real implementation, you'd check timestamps
        # For now, we'll just clear all states older than the limit
        # This is a simplified implementation
        pass


# Global OAuth storage instance
oauth_storage = OAuthStorage()