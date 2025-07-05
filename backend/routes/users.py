"""
User management routes for profile and preferences.
"""

from flask import Blueprint, request, jsonify, g
from utils.jwt_utils import require_auth, create_error_response, create_success_response
from models.user import User
import psycopg2

users_bp = Blueprint('users', __name__)

def get_db_connection():
    """Get database connection - will be injected by main app."""
    return getattr(g, 'db_connection', None)


@users_bp.route('/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get current user's profile and preferences.
    
    Returns:
        JSON response with user profile and preferences
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # Get user info
            user = user_model.get_user_by_id(g.current_user['id'])
            if not user:
                return create_error_response("User not found", 404)
            
            # Get user preferences
            preferences = user_model.get_user_preferences(g.current_user['id'])
            
            return jsonify(create_success_response({
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'avatar_url': user['avatar_url'],
                    'role': user['role'],
                    'display_name': user['display_name'],
                    'anonymous_mode': user['anonymous_mode'],
                    'avatar_class': user['avatar_class'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                },
                'preferences': preferences
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get profile: {str(e)}", 500)


@users_bp.route('/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update current user's profile.
    
    Expected JSON payload:
    {
        "first_name": "John",
        "last_name": "Doe"
    }
    
    Returns:
        JSON response with updated user profile
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        # Validate allowed fields
        allowed_fields = ['first_name', 'last_name', 'display_name', 'anonymous_mode', 'avatar_class']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                
                # Special validation for boolean fields
                if field == 'anonymous_mode':
                    if value is not None and not isinstance(value, bool):
                        return create_error_response(f"Field '{field}' must be a boolean", 400)
                    update_data[field] = value
                else:
                    # Validate string fields
                    if value is not None and not isinstance(value, str):
                        return create_error_response(f"Field '{field}' must be a string", 400)
                    if value is not None and len(value.strip()) == 0:
                        value = None  # Convert empty strings to None
                    update_data[field] = value
        
        if not update_data:
            return create_error_response("No valid fields to update", 400)
        
        # Validate business rules: anonymous_mode can only be enabled if display_name is set
        if update_data.get('anonymous_mode') is True:
            # Check if display_name is being set in this request or already exists
            display_name = update_data.get('display_name')
            if not display_name:
                # Need to check existing display_name from database
                conn = get_db_connection()
                if not conn:
                    return create_error_response("Database connection failed", 500)
                
                try:
                    user_model = User(conn)
                    current_user = user_model.get_user_by_id(g.current_user['id'])
                    if not current_user or not current_user.get('display_name'):
                        return create_error_response("Cannot enable anonymous mode without setting a display name first", 400)
                except Exception as e:
                    return create_error_response(f"Database error: {str(e)}", 500)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # Update user profile
            updated_user = user_model.update_user_profile(
                g.current_user['id'],
                first_name=update_data.get('first_name'),
                last_name=update_data.get('last_name'),
                display_name=update_data.get('display_name'),
                anonymous_mode=update_data.get('anonymous_mode'),
                avatar_class=update_data.get('avatar_class')
            )
            
            return jsonify(create_success_response({
                'user': {
                    'id': updated_user['id'],
                    'email': updated_user['email'],
                    'first_name': updated_user['first_name'],
                    'last_name': updated_user['last_name'],
                    'avatar_url': updated_user['avatar_url'],
                    'role': updated_user['role'],
                    'display_name': updated_user['display_name'],
                    'anonymous_mode': updated_user['anonymous_mode'],
                    'avatar_class': updated_user['avatar_class'],
                    'updated_at': updated_user['updated_at'].isoformat() if updated_user['updated_at'] else None
                }
            }, "Profile updated successfully"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to update profile: {str(e)}", 500)


@users_bp.route('/user/preferences', methods=['GET'])
@require_auth
def get_preferences():
    """
    Get current user's preferences.
    
    Returns:
        JSON response with user preferences
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # Get user preferences
            preferences = user_model.get_user_preferences(g.current_user['id'])
            
            if not preferences:
                # Create default preferences if they don't exist
                preferences = user_model.create_user_preferences(g.current_user['id'])
            
            return jsonify(create_success_response({
                'preferences': preferences
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get preferences: {str(e)}", 500)


@users_bp.route('/user/preferences', methods=['PUT'])
@require_auth
def update_preferences():
    """
    Update current user's preferences.
    
    Expected JSON payload:
    {
        "theme_preference": "dark",
        "results_per_page": 25
    }
    
    Returns:
        JSON response with updated preferences
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        # Validate and prepare update data
        update_data = {}
        
        # Validate theme_preference
        if 'theme_preference' in data:
            theme_preference = data['theme_preference']
            if theme_preference is not None:
                if not isinstance(theme_preference, str):
                    return create_error_response("theme_preference must be a string", 400)
                theme_preference = theme_preference.strip().lower()
                if theme_preference not in ['light', 'dark', 'auto']:
                    return create_error_response("theme_preference must be 'light', 'dark', or 'auto'", 400)
            update_data['theme_preference'] = theme_preference
        
        # Validate results_per_page
        if 'results_per_page' in data:
            results_per_page = data['results_per_page']
            if results_per_page is not None:
                if not isinstance(results_per_page, int):
                    return create_error_response("results_per_page must be an integer", 400)
                if results_per_page < 10 or results_per_page > 100:
                    return create_error_response("results_per_page must be between 10 and 100", 400)
            update_data['results_per_page'] = results_per_page
        
        if not update_data:
            return create_error_response("No valid preferences to update", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # Update user preferences
            updated_preferences = user_model.update_user_preferences(
                g.current_user['id'],
                theme_preference=update_data.get('theme_preference'),
                results_per_page=update_data.get('results_per_page')
            )
            
            return jsonify(create_success_response({
                'preferences': updated_preferences
            }, "Preferences updated successfully"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to update preferences: {str(e)}", 500)


@users_bp.route('/user/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """
    Get current user's active sessions.
    
    Returns:
        JSON response with user sessions
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            from models.user import OAuthSession
            
            # Initialize session model
            oauth_session_model = OAuthSession(conn)
            
            # Get user sessions
            sessions = oauth_session_model.get_user_sessions(g.current_user['id'])
            
            # Format sessions for response (hide sensitive data)
            formatted_sessions = []
            for session in sessions:
                formatted_sessions.append({
                    'id': session['id'],
                    'created_at': session['created_at'].isoformat() if session['created_at'] else None,
                    'last_used': session['last_used'].isoformat() if session['last_used'] else None,
                    'ip_address': str(session['ip_address']) if session['ip_address'] else None,
                    'expires_at': session['token_expires_at'].isoformat() if session['token_expires_at'] else None
                })
            
            return jsonify(create_success_response({
                'sessions': formatted_sessions,
                'total_count': len(formatted_sessions)
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get sessions: {str(e)}", 500)


@users_bp.route('/user/sessions/<int:session_id>', methods=['DELETE'])
@require_auth
def delete_user_session(session_id):
    """
    Delete a specific user session.
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        JSON response confirming deletion
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            from models.user import OAuthSession
            
            # Initialize session model
            oauth_session_model = OAuthSession(conn)
            
            # Get user sessions to verify ownership
            sessions = oauth_session_model.get_user_sessions(g.current_user['id'])
            session_to_delete = None
            
            for session in sessions:
                if session['id'] == session_id:
                    session_to_delete = session
                    break
            
            if not session_to_delete:
                return create_error_response("Session not found or not owned by user", 404)
            
            # Delete the session
            oauth_session_model.delete_session(session_to_delete['local_session_token'])
            
            return jsonify(create_success_response({}, "Session deleted successfully"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to delete session: {str(e)}", 500)