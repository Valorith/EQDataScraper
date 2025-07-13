"""
JWT utilities for secure token management.
"""

import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify, current_app

class JWTManager:
    """JWT token manager for user authentication."""
    
    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY')
        if not self.secret_key:
            # Use a default key for testing, but warn about it
            if os.environ.get('TESTING') == 'true':
                self.secret_key = 'test_jwt_secret_key_for_testing_only'
            else:
                raise ValueError("JWT_SECRET_KEY environment variable is required")
        
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30   # 30 days
    
    def generate_local_session_token(self) -> str:
        """Generate a secure local session token."""
        return secrets.token_urlsafe(32)
    
    def create_access_token(self, user_id: int, user_email: str, user_role: str = 'user') -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User ID
            user_email: User email
            user_role: User role (user/admin)
        
        Returns:
            JWT access token
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'email': user_email,
            'role': user_role,
            'iat': now,
            'exp': now + timedelta(minutes=self.access_token_expire_minutes),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int, session_token: str) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User ID
            session_token: Local session token
        
        Returns:
            JWT refresh token
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'session_token': session_token,
            'iat': now,
            'exp': now + timedelta(days=self.refresh_token_expire_days),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def extract_token_from_header(self, auth_header: str) -> Optional[str]:
        """
        Extract token from Authorization header.
        
        Args:
            auth_header: Authorization header value
        
        Returns:
            Token or None if invalid format
        """
        if not auth_header:
            return None
        
        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]
    
    def refresh_access_token(self, refresh_token: str, user_model, oauth_session_model) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: JWT refresh token
            user_model: User model instance
            oauth_session_model: OAuth session model instance
        
        Returns:
            New tokens or None if refresh failed
        """
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            if not payload or payload.get('type') != 'refresh':
                return None
            
            user_id = payload.get('user_id')
            session_token = payload.get('session_token')
            
            # Verify session still exists
            session = oauth_session_model.get_session_by_token(session_token)
            if not session or session['user_id'] != user_id:
                return None
            
            # Get current user
            user = user_model.get_user_by_id(user_id)
            if not user:
                return None
            
            # Generate new access token
            new_access_token = self.create_access_token(
                user['id'], 
                user['email'], 
                user['role']
            )
            
            # Update session last used
            oauth_session_model.update_session_last_used(session['id'])
            
            return {
                'access_token': new_access_token,
                'user': user
            }
            
        except Exception:
            return None


# Global JWT manager instance
try:
    jwt_manager = JWTManager()
except ValueError as e:
    # Handle case where JWT_SECRET_KEY is not set during testing
    if 'JWT_SECRET_KEY' in str(e):
        # Set a test environment variable and try again
        os.environ['JWT_SECRET_KEY'] = 'test_jwt_secret_key_for_testing_only'
        jwt_manager = JWTManager()
    else:
        raise


def require_auth(f):
    """
    Decorator to require authentication for protected routes.
    
    Usage:
        @require_auth
        def protected_route():
            # Access current_user from flask.g
            user = g.current_user
            return jsonify({'user': user})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        # DEV MODE BYPASS: Skip authentication in development mode
        if current_app.config.get('DEV_MODE_AUTH_BYPASS', False):
            g.current_user = {
                'id': 1,
                'email': 'dev@localhost.dev',
                'role': 'admin'
            }
            return f(*args, **kwargs)
        
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        # Extract token
        token = jwt_manager.extract_token_from_header(auth_header)
        if not token:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in flask.g for use in route
        g.current_user = {
            'id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin role for protected routes.
    
    Usage:
        @require_admin
        def admin_route():
            # Access current_user from flask.g
            user = g.current_user
            return jsonify({'admin_user': user})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import g
        
        # DEV MODE BYPASS: Skip authentication in development mode
        if current_app.config.get('DEV_MODE_AUTH_BYPASS', False):
            g.current_user = {
                'id': 1,
                'email': 'dev@localhost.dev',
                'role': 'admin'
            }
            return f(*args, **kwargs)
        
        # First check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = jwt_manager.extract_token_from_header(auth_header)
        if not token:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        payload = jwt_manager.verify_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check admin role
        if payload.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Store user info in flask.g for use in route
        g.current_user = {
            'id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token without requiring authentication.
    Useful for optional authentication.
    
    Returns:
        User info or None if no valid token
    """
    try:
        from flask import g
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        token = jwt_manager.extract_token_from_header(auth_header)
        if not token:
            return None
        
        payload = jwt_manager.verify_token(token)
        if not payload or payload.get('type') != 'access':
            return None
        
        return {
            'id': payload.get('user_id'),
            'email': payload.get('email'),
            'role': payload.get('role')
        }
        
    except Exception:
        return None


def create_error_response(message: str, status_code: int = 400) -> tuple:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
    
    Returns:
        Tuple of (response, status_code)
    """
    return jsonify({
        'error': message,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code


def create_success_response(data: Dict[str, Any], message: str = None) -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
    
    Returns:
        Standardized response dictionary
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    return response