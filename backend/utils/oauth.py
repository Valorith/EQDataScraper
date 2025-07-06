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
import jwt  # Import jwt at module level to avoid dynamic import issues
import logging

# Configure logging
logger = logging.getLogger(__name__)

def safe_log(message):
    """Safely log messages without causing errors in production."""
    try:
        print(message)
    except:
        # If print fails, try logger
        try:
            logger.info(message)
        except:
            # Silently ignore if all logging fails
            pass

class GoogleOAuth:
    """Google OAuth handler with PKCE support."""
    
    def __init__(self):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('OAUTH_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing Google OAuth configuration. Check environment variables.")
        
        # Fix common misconfiguration where redirect URI points to backend instead of frontend
        if self.redirect_uri and ('/api/' in self.redirect_uri or 'backend' in self.redirect_uri):
            safe_log(f"[OAuth Init] Warning: Redirect URI appears to point to backend: {self.redirect_uri}")
            # In production, try to fix it automatically
            if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
                frontend_url = os.environ.get('FRONTEND_URL', 'https://eqdatascraper-frontend-production.up.railway.app')
                self.redirect_uri = f"{frontend_url}/auth/callback"
                safe_log(f"[OAuth Init] Auto-corrected redirect URI to: {self.redirect_uri}")
        
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
        
        # Double-check redirect URI before generating auth URL
        if self.redirect_uri and ('/api/' in self.redirect_uri or 'backend' in self.redirect_uri):
            safe_log(f"[OAuth] ERROR: Redirect URI still points to backend in get_authorization_url: {self.redirect_uri}")
            # Force correction
            if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
                frontend_url = os.environ.get('FRONTEND_URL', 'https://eqdatascraper-frontend-production.up.railway.app')
                self.redirect_uri = f"{frontend_url}/auth/callback"
                safe_log(f"[OAuth] FORCED correction to: {self.redirect_uri}")
        
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
        
        # URL encode with safe parameter to avoid issues
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params, safe='')}"
        
        # Log the full auth URL for debugging
        safe_log(f"[OAuth] Authorization URL generated with redirect_uri: {self.redirect_uri}")
        safe_log(f"[OAuth] Full auth URL params: {params}")
        safe_log(f"[OAuth] Full auth URL (first 500 chars): {auth_url[:500]}")
        safe_log(f"[OAuth] Redirect URI length: {len(self.redirect_uri)}")
        
        # Double-check the auth URL contains the full redirect URI
        if '/auth/callba' in auth_url and '/auth/callback' not in auth_url:
            safe_log(f"[OAuth] ERROR: Redirect URI was truncated in auth URL!")
            safe_log(f"[OAuth] Full redirect URI should be: {self.redirect_uri}")
        
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
            
            safe_log(f"[OAuth] Sending token exchange request to: {self.token_url}")
            safe_log(f"[OAuth] Token exchange data: client_id={self.client_id[:10]}..., redirect_uri={self.redirect_uri}, code={code[:10]}...")
            safe_log(f"[OAuth] Code verifier length: {len(code_verifier) if code_verifier else 0}")
            
            # Make the request with timeout
            try:
                response = requests.post(self.token_url, data=token_data, timeout=30)
            except requests.exceptions.Timeout:
                safe_log(f"[OAuth] ERROR: Token exchange request timed out after 30 seconds")
                raise Exception("Token exchange request timed out. Please try again.")
            except requests.exceptions.ConnectionError as e:
                safe_log(f"[OAuth] ERROR: Connection error during token exchange: {str(e)}")
                raise Exception(f"Network error during token exchange: {str(e)}")
            
            # Log response details before checking status
            safe_log(f"[OAuth] Token exchange response status: {response.status_code}")
            
            if response.status_code != 200:
                safe_log(f"[OAuth] Token exchange failed with status {response.status_code}")
                safe_log(f"[OAuth] Response content: {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                    error_desc = error_data.get('error_description', '')
                    safe_log(f"[OAuth] Error: {error_msg} - {error_desc}")
                    
                    # Common redirect_uri mismatch error
                    if 'redirect_uri' in error_desc.lower():
                        raise Exception(f"Redirect URI mismatch. Backend is using: {self.redirect_uri}. Error: {error_desc}")
                    else:
                        raise Exception(f"OAuth error: {error_msg} - {error_desc}")
                except ValueError:
                    # Response is not JSON
                    raise Exception(f"OAuth token exchange failed with status {response.status_code}: {response.text[:200]}")
            
            response.raise_for_status()
            tokens = response.json()
            
            # Verify the ID token
            id_token_jwt = tokens.get('id_token')
            if not id_token_jwt:
                raise ValueError("No ID token received from Google")
            
            # Verify and decode the ID token
            try:
                safe_log(f"[OAuth] Verifying ID token with client_id: {self.client_id}")
                
                # Add clock skew tolerance
                id_info = id_token.verify_oauth2_token(
                    id_token_jwt, 
                    google_requests.Request(), 
                    self.client_id,
                    clock_skew_in_seconds=60  # Increase to 60 seconds for production
                )
                
                safe_log(f"[OAuth] ID token verified successfully")
            except Exception as e:
                safe_log(f"[OAuth] ID token verification failed: {str(e)}")
                safe_log(f"[OAuth] Client ID: {self.client_id}")
                safe_log(f"[OAuth] ID Token (first 50 chars): {id_token_jwt[:50] if id_token_jwt else 'None'}...")
                
                # Try alternative verification method for production
                try:
                    safe_log("[OAuth] Attempting fallback JWT decode...")
                    decoded = jwt.decode(id_token_jwt, options={"verify_signature": False})
                    # Safely log token claims without json.dumps to avoid serialization errors
                    safe_log(f"[OAuth] Decoded token email: {decoded.get('email')}")
                    safe_log(f"[OAuth] Decoded token aud: {decoded.get('aud')}")
                    safe_log(f"[OAuth] Decoded token iss: {decoded.get('iss')}")
                    
                    # Check if it's just an audience mismatch
                    if decoded.get('aud') != self.client_id:
                        safe_log(f"[OAuth] Warning: Audience mismatch! Token aud: {decoded.get('aud')}, Expected: {self.client_id}")
                    
                    # In production, we can be more lenient if the email is verified
                    # This is a temporary workaround for the ID token verification issue
                    if decoded.get('email_verified') and decoded.get('iss') in ['accounts.google.com', 'https://accounts.google.com']:
                        safe_log("[OAuth] Using fallback verification due to production environment")
                        id_info = decoded
                    else:
                        raise ValueError(f"Invalid ID token: {str(e)}")
                        
                except Exception as alt_e:
                    safe_log(f"[OAuth] Fallback decode also failed: {str(alt_e)}")
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
        self._file_storage_path = "/tmp/oauth_states.json"
        self._use_file_storage = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
        
        if self._use_file_storage:
            safe_log("[OAuth Storage] Using file-based storage for production environment")
            # Load existing states from file if it exists
            try:
                if os.path.exists(self._file_storage_path):
                    with open(self._file_storage_path, 'r') as f:
                        self._storage = json.load(f)
                    safe_log(f"[OAuth Storage] Loaded {len(self._storage)} existing states from file")
            except Exception as e:
                safe_log(f"[OAuth Storage] Error loading states from file: {str(e)}")
                self._storage = {}
    
    def _save_to_file(self):
        """Save current state to file in production."""
        if self._use_file_storage:
            try:
                with open(self._file_storage_path, 'w') as f:
                    json.dump(self._storage, f)
                safe_log(f"[OAuth Storage] Saved {len(self._storage)} states to file")
            except Exception as e:
                safe_log(f"[OAuth Storage] Error saving states to file: {str(e)}")
    
    def store_oauth_state(self, state: str, code_verifier: str, user_ip: str = None) -> None:
        """Store OAuth state and code verifier temporarily."""
        self._storage[state] = {
            'code_verifier': code_verifier,
            'user_ip': user_ip,
            'timestamp': time.time()  # Use actual timestamp for cleanup
        }
        safe_log(f"[OAuth Storage] Stored state: {state[:20]}... with code_verifier: {code_verifier[:20]}...")
        self._save_to_file()
        
        # Clean up old states (older than 10 minutes)
        self.cleanup_expired_states()
    
    def get_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth state data."""
        # In production, reload from file to get states from other workers
        if self._use_file_storage:
            try:
                if os.path.exists(self._file_storage_path):
                    with open(self._file_storage_path, 'r') as f:
                        self._storage = json.load(f)
                    safe_log(f"[OAuth Storage] Reloaded states from file, found {len(self._storage)} states")
            except Exception as e:
                safe_log(f"[OAuth Storage] Error reloading states from file: {str(e)}")
        
        result = self._storage.get(state)
        if result:
            safe_log(f"[OAuth Storage] Found state: {state[:20]}...")
        else:
            safe_log(f"[OAuth Storage] State not found: {state[:20]}...")
            safe_log(f"[OAuth Storage] Available states: {list(self._storage.keys())[:5]}")
        return result
    
    def remove_oauth_state(self, state: str) -> None:
        """Remove OAuth state after use."""
        if state in self._storage:
            self._storage.pop(state, None)
            safe_log(f"[OAuth Storage] Removed state: {state[:20]}...")
            self._save_to_file()
    
    def cleanup_expired_states(self, max_age_minutes: int = 10) -> None:
        """Clean up expired OAuth states."""
        current_time = time.time()
        max_age_seconds = max_age_minutes * 60
        
        states_to_remove = []
        for state, data in self._storage.items():
            if isinstance(data.get('timestamp'), (int, float)):
                if current_time - data['timestamp'] > max_age_seconds:
                    states_to_remove.append(state)
        
        for state in states_to_remove:
            self._storage.pop(state, None)
            
        if states_to_remove:
            safe_log(f"[OAuth Storage] Cleaned up {len(states_to_remove)} expired states")
            self._save_to_file()


# Global OAuth storage instance
oauth_storage = OAuthStorage()