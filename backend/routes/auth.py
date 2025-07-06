"""
Authentication routes for Google OAuth integration.
"""

from flask import Blueprint, request, jsonify, g
from utils.oauth import GoogleOAuth, oauth_storage
from utils.jwt_utils import jwt_manager, require_auth, create_error_response, create_success_response
from models.user import User, OAuthSession
from models.activity import ActivityLog
import psycopg2
import traceback  # Import at module level to avoid dynamic import issues
import logging
import os

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
        # Get the origin from the request to determine the actual frontend port
        origin = request.headers.get('Origin', 'http://localhost:3000')
        
        # Initialize Google OAuth with dynamic redirect URI
        google_oauth = GoogleOAuth()
        
        # Override redirect URI based on request origin for local development
        # In production, use the configured redirect URI
        if 'localhost' in origin and 'localhost' in google_oauth.redirect_uri:
            google_oauth.redirect_uri = f"{origin}/auth/callback"
        
        # Log the redirect URI being used for debugging
        safe_log(f"[OAuth Login] Origin: {origin}")
        safe_log(f"[OAuth Login] Using redirect URI: {google_oauth.redirect_uri}")
        safe_log(f"[OAuth Login] Environment OAUTH_REDIRECT_URI: {os.environ.get('OAUTH_REDIRECT_URI', 'NOT SET')}")
        
        # Generate authorization URL with PKCE
        auth_data = google_oauth.get_authorization_url()
        
        # Store state and code verifier temporarily
        oauth_storage.store_oauth_state(
            auth_data['state'],
            auth_data['code_verifier'],
            request.remote_addr
        )
        
        # Log the generated auth URL for debugging
        safe_log(f"[OAuth Login] Generated auth URL (first 100 chars): {auth_data['auth_url'][:100]}...")
        
        return jsonify(create_success_response({
            'auth_url': auth_data['auth_url'],
            'state': auth_data['state']
        }))
        
    except Exception as e:
        safe_log(f"[OAuth Login Error] {str(e)}")
        return create_error_response(f"Failed to generate authorization URL: {str(e)}", 500)


@auth_bp.route('/auth/google/callback', methods=['GET'])
def google_callback_get():
    """
    Handle GET requests to the callback endpoint.
    This should not normally happen - the frontend should POST the code.
    
    Returns:
        JSON error response explaining the issue
    """
    # Log the request details to understand why GET is being called
    safe_log("[OAuth] Unexpected GET request to callback endpoint")
    safe_log(f"[OAuth] GET request headers: {dict(request.headers)}")
    safe_log(f"[OAuth] GET request args: {dict(request.args)}")
    
    # Check if this is a direct redirect from Google (which shouldn't happen)
    if 'code' in request.args:
        # This might be a misconfiguration - Google is redirecting to the API instead of frontend
        code = request.args.get('code')
        state = request.args.get('state')
        
        # Log the redirect issue
        safe_log(f"[OAuth] Direct redirect from Google detected!")
        safe_log(f"[OAuth] This suggests OAUTH_REDIRECT_URI might be set to the backend URL instead of frontend")
        safe_log(f"[OAuth] Code present: {bool(code)}, State present: {bool(state)}")
        
        # Build the correct frontend redirect URL
        frontend_base = os.environ.get('FRONTEND_URL', 'https://eqdatascraper-frontend-production.up.railway.app')
        correct_redirect = f"{frontend_base}/auth/callback?code={code}&state={state}"
        
        # Return HTML that redirects to the frontend
        return f"""
        <html>
        <head>
            <title>Redirecting...</title>
            <meta http-equiv="refresh" content="0; url={correct_redirect}">
        </head>
        <body>
            <p>Redirecting to complete authentication...</p>
            <p>If you are not redirected, <a href="{correct_redirect}">click here</a>.</p>
        </body>
        </html>
        """, 200, {'Content-Type': 'text/html'}
    
    return create_error_response(
        "Method not allowed. Use POST to submit OAuth callback data.", 
        405
    )


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
        
        # Get the origin from the request to determine the actual frontend port
        origin = request.headers.get('Origin', 'http://localhost:3000')
        
        # Initialize Google OAuth with dynamic redirect URI
        google_oauth = GoogleOAuth()
        
        # Override redirect URI based on request origin for local development
        # In production, use the configured redirect URI
        if 'localhost' in origin and 'localhost' in google_oauth.redirect_uri:
            google_oauth.redirect_uri = f"{origin}/auth/callback"
        
        # Exchange code for tokens
        try:
            safe_log(f"[OAuth Debug] Exchanging code for tokens")
            safe_log(f"[OAuth Debug] Client ID: {google_oauth.client_id[:10]}...")
            safe_log(f"[OAuth Debug] Redirect URI: {google_oauth.redirect_uri}")
            safe_log(f"[OAuth Debug] Original Origin: {origin}")
            safe_log(f"[OAuth Debug] Code: {code[:10]}...")
            safe_log(f"[OAuth Debug] State: {state}")
            
            # Add diagnostic info to help debug
            safe_log(f"[OAuth Debug] Environment OAUTH_REDIRECT_URI: {os.environ.get('OAUTH_REDIRECT_URI', 'NOT SET')}")
            
            token_data = google_oauth.exchange_code_for_tokens(
                code, 
                stored_state['code_verifier']
            )
        except Exception as e:
            safe_log(f"[OAuth Error] Token exchange failed: {str(e)}")
            safe_log(f"[OAuth Error] Error type: {type(e).__name__}")
            # Log more details for debugging
            safe_log(f"[OAuth Error] Traceback: {traceback.format_exc()}")
            # Include redirect URI in error response for debugging
            return create_error_response(f"Failed to exchange code for tokens: {str(e)} (redirect_uri: {google_oauth.redirect_uri})", 500)
        
        user_info = token_data['user_info']
        
        # Validate required user info
        if not user_info.get('email') or not user_info.get('google_id'):
            return create_error_response("Invalid user information from Google", 400)
        
        if not user_info.get('email_verified'):
            return create_error_response("Email not verified with Google", 400)
        
        # Get database connection
        conn = get_db_connection()
        
        # For local development without database, create a simple in-memory user
        if not conn:
            safe_log("Warning: No database connection, using in-memory user storage")
            # Create JWT tokens without database
            access_token = jwt_manager.create_access_token(
                user_id=user_info['google_id'],  # Use Google ID as user ID
                email=user_info['email'],
                is_admin=False  # Default to non-admin
            )
            
            refresh_token = jwt_manager.create_refresh_token(
                user_id=user_info['google_id'],
                email=user_info['email']
            )
            
            # Return simplified response without database
            return jsonify(create_success_response({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user_info['google_id'],
                    'email': user_info['email'],
                    'first_name': user_info.get('first_name'),
                    'last_name': user_info.get('last_name'),
                    'avatar_url': user_info.get('avatar_url'),
                    'is_admin': False,
                    'is_active': True
                },
                'preferences': {
                    'theme_preference': 'auto',
                    'results_per_page': 20
                }
            }))
        
        try:
            # Initialize models
            user_model = User(conn)
            oauth_session_model = OAuthSession(conn)
            activity_log = ActivityLog(conn)
            
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
                
                # Log user creation
                activity_log.log_activity(
                    action=ActivityLog.ACTION_USER_CREATE,
                    user_id=user['id'],
                    resource_type=ActivityLog.RESOURCE_USER,
                    resource_id=str(user['id']),
                    details={'email': user['email']},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
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
            
            # Log login activity
            activity_log.log_activity(
                action=ActivityLog.ACTION_LOGIN,
                user_id=user['id'],
                resource_type=ActivityLog.RESOURCE_SESSION,
                resource_id=str(oauth_session['id']),
                details={'method': 'google_oauth'},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
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
                    'avatar_class': user.get('avatar_class'),
                    'display_name': user.get('display_name'),
                    'anonymous_mode': user.get('anonymous_mode', False),
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
            activity_log = ActivityLog(conn)
            
            if refresh_token:
                # Verify refresh token to get session token
                payload = jwt_manager.verify_token(refresh_token)
                if payload and payload.get('type') == 'refresh':
                    session_token = payload.get('session_token')
                    if session_token:
                        # Get session before deleting for logging
                        session = oauth_session_model.get_session_by_token(session_token)
                        
                        # Delete session
                        oauth_session_model.delete_session(session_token)
                        
                        # Try to revoke Google tokens
                        try:
                            google_oauth = GoogleOAuth()
                            if session and session.get('google_access_token'):
                                google_oauth.revoke_token(session['google_access_token'])
                        except Exception:
                            pass  # Don't fail logout if token revocation fails
                        
                        # Log logout activity
                        if session:
                            activity_log.log_activity(
                                action=ActivityLog.ACTION_LOGOUT,
                                user_id=session['user_id'],
                                resource_type=ActivityLog.RESOURCE_SESSION,
                                resource_id=str(session['id']),
                                ip_address=request.remote_addr,
                                user_agent=request.headers.get('User-Agent')
                            )
            
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
                    'avatar_class': user.get('avatar_class'),
                    'display_name': user.get('display_name'),
                    'anonymous_mode': user.get('anonymous_mode', False),
                    'role': user['role']
                }
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Status check failed: {str(e)}", 500)


@auth_bp.route('/auth/debug-config', methods=['GET'])
def debug_oauth_config():
    """
    Debug endpoint to check OAuth configuration (remove in production).
    
    Returns:
        JSON response with OAuth configuration
    """
    try:
        # Only allow in development or with special header
        if not (os.environ.get('FLASK_ENV') == 'development' or 
                request.headers.get('X-Debug-Token') == os.environ.get('DEBUG_TOKEN', 'no-token-set')):
            return create_error_response("Not available", 404)
        
        google_oauth = GoogleOAuth()
        
        # Test redirect URI matching
        frontend_redirect = os.environ.get('OAUTH_REDIRECT_URI', 'NOT SET')
        origin = request.headers.get('Origin', 'No origin header')
        
        return jsonify(create_success_response({
            'client_id': google_oauth.client_id[:20] + '...' if google_oauth.client_id else 'NOT SET',
            'redirect_uri': google_oauth.redirect_uri,
            'env_redirect_uri': os.environ.get('OAUTH_REDIRECT_URI', 'NOT SET'),
            'client_id_set': bool(os.environ.get('GOOGLE_CLIENT_ID')),
            'client_secret_set': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
            'request_origin': origin,
            'frontend_url': os.environ.get('FRONTEND_URL', 'NOT SET'),
            'scopes': google_oauth.scopes,
            'auth_url': google_oauth.auth_url,
            'token_url': google_oauth.token_url
        }))
    except Exception as e:
        return create_error_response(f"Failed to get config: {str(e)}", 500)


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