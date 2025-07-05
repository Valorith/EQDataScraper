"""
Authentication routes for Google OAuth integration.
"""

from flask import Blueprint, request, jsonify, g
from utils.oauth import GoogleOAuth, oauth_storage
from utils.jwt_utils import jwt_manager, require_auth, create_error_response, create_success_response
from models.user import User, OAuthSession
import psycopg2

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    """Get database connection - will be injected by main app."""
    # This will be set by the main app when registering the blueprint
    return getattr(g, 'db_connection', None)


@auth_bp.route('/auth/google/login', methods=['GET'])
def google_login():
    """
    Generate Google OAuth authorization URL.
    
    Returns:
        JSON response with authorization URL
    """
    try:
        # Initialize Google OAuth
        google_oauth = GoogleOAuth()
        
        # Generate authorization URL with PKCE
        auth_data = google_oauth.get_authorization_url()
        
        # Store state and code verifier temporarily
        oauth_storage.store_oauth_state(
            auth_data['state'],
            auth_data['code_verifier'],
            request.remote_addr
        )
        
        return jsonify(create_success_response({
            'auth_url': auth_data['auth_url'],
            'state': auth_data['state']
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to generate authorization URL: {str(e)}", 500)


@auth_bp.route('/auth/google/callback', methods=['POST'])
def google_callback():
    """
    Handle Google OAuth callback.
    
    Expected JSON payload:
    {
        "code": "authorization_code_from_google",
        "state": "state_parameter"
    }
    
    Returns:
        JSON response with tokens and user info
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        code = data.get('code')
        state = data.get('state')
        
        if not code or not state:
            return create_error_response("Missing code or state parameter", 400)
        
        # Retrieve stored OAuth state
        stored_state = oauth_storage.get_oauth_state(state)
        if not stored_state:
            return create_error_response("Invalid or expired state parameter", 400)
        
        # Clean up used state
        oauth_storage.remove_oauth_state(state)
        
        # Initialize Google OAuth
        google_oauth = GoogleOAuth()
        
        # Exchange code for tokens
        token_data = google_oauth.exchange_code_for_tokens(
            code, 
            stored_state['code_verifier']
        )
        
        user_info = token_data['user_info']
        
        # Validate required user info
        if not user_info.get('email') or not user_info.get('google_id'):
            return create_error_response("Invalid user information from Google", 400)
        
        if not user_info.get('email_verified'):
            return create_error_response("Email not verified with Google", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize models
            user_model = User(conn)
            oauth_session_model = OAuthSession(conn)
            
            # Check if user exists
            user = user_model.get_user_by_google_id(user_info['google_id'])
            
            if not user:
                # Create new user
                user = user_model.create_user(
                    google_id=user_info['google_id'],
                    email=user_info['email'],
                    first_name=user_info.get('first_name'),
                    last_name=user_info.get('last_name'),
                    avatar_url=user_info.get('avatar_url')
                )
            else:
                # Update existing user's login time and profile
                user_model.update_user_login(user['id'])
                user = user_model.update_user_profile(
                    user['id'],
                    first_name=user_info.get('first_name'),
                    last_name=user_info.get('last_name'),
                    avatar_url=user_info.get('avatar_url')
                )
            
            # Generate local session token
            local_session_token = jwt_manager.generate_local_session_token()
            
            # Create OAuth session
            oauth_session = oauth_session_model.create_session(
                user_id=user['id'],
                google_access_token=token_data['access_token'],
                google_refresh_token=token_data.get('refresh_token'),
                expires_in=token_data.get('expires_in', 3600),
                local_session_token=local_session_token,
                ip_address=request.remote_addr
            )
            
            # Create JWT tokens
            access_token = jwt_manager.create_access_token(
                user['id'],
                user['email'],
                user['role']
            )
            
            refresh_token = jwt_manager.create_refresh_token(
                user['id'],
                local_session_token
            )
            
            # Get user preferences
            user_preferences = user_model.get_user_preferences(user['id'])
            
            # Return success response
            return jsonify(create_success_response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'avatar_url': user['avatar_url'],
                    'role': user['role']
                },
                'preferences': user_preferences
            }, "Login successful"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"OAuth callback failed: {str(e)}", 500)


@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token.
    
    Expected JSON payload:
    {
        "refresh_token": "jwt_refresh_token"
    }
    
    Returns:
        JSON response with new access token
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return create_error_response("Missing refresh token", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize models
            user_model = User(conn)
            oauth_session_model = OAuthSession(conn)
            
            # Refresh access token
            token_data = jwt_manager.refresh_access_token(
                refresh_token,
                user_model,
                oauth_session_model
            )
            
            if not token_data:
                return create_error_response("Invalid or expired refresh token", 401)
            
            return jsonify(create_success_response({
                'access_token': token_data['access_token'],
                'user': token_data['user']
            }, "Token refreshed"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Token refresh failed: {str(e)}", 500)


@auth_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user and revoke session.
    
    Expected JSON payload:
    {
        "refresh_token": "jwt_refresh_token"
    }
    
    Returns:
        JSON response confirming logout
    """
    try:
        # Get request data
        data = request.get_json()
        refresh_token = data.get('refresh_token') if data else None
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize models
            oauth_session_model = OAuthSession(conn)
            
            if refresh_token:
                # Verify refresh token to get session token
                payload = jwt_manager.verify_token(refresh_token)
                if payload and payload.get('type') == 'refresh':
                    session_token = payload.get('session_token')
                    if session_token:
                        # Delete session
                        oauth_session_model.delete_session(session_token)
                        
                        # Try to revoke Google tokens
                        try:
                            google_oauth = GoogleOAuth()
                            session = oauth_session_model.get_session_by_token(session_token)
                            if session and session.get('google_access_token'):
                                google_oauth.revoke_token(session['google_access_token'])
                        except Exception:
                            pass  # Don't fail logout if token revocation fails
            
            return jsonify(create_success_response({}, "Logout successful"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Logout failed: {str(e)}", 500)


@auth_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """
    Check authentication status.
    
    Returns:
        JSON response with authentication status
    """
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify(create_success_response({
                'authenticated': False
            }))
        
        # Extract and verify token
        token = jwt_manager.extract_token_from_header(auth_header)
        if not token:
            return jsonify(create_success_response({
                'authenticated': False
            }))
        
        payload = jwt_manager.verify_token(token)
        if not payload or payload.get('type') != 'access':
            return jsonify(create_success_response({
                'authenticated': False
            }))
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Get user info
            user_model = User(conn)
            user = user_model.get_user_by_id(payload.get('user_id'))
            
            if not user:
                return jsonify(create_success_response({
                    'authenticated': False
                }))
            
            return jsonify(create_success_response({
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'avatar_url': user['avatar_url'],
                    'role': user['role']
                }
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Status check failed: {str(e)}", 500)


@auth_bp.route('/auth/cleanup', methods=['POST'])
@require_auth
def cleanup_sessions():
    """
    Clean up expired sessions (admin only).
    
    Returns:
        JSON response with cleanup results
    """
    try:
        # Check admin role
        if g.current_user.get('role') != 'admin':
            return create_error_response("Admin access required", 403)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Clean up expired sessions
            oauth_session_model = OAuthSession(conn)
            deleted_count = oauth_session_model.cleanup_expired_sessions()
            
            return jsonify(create_success_response({
                'deleted_sessions': deleted_count
            }, "Session cleanup completed"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Session cleanup failed: {str(e)}", 500)