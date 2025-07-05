"""
Admin routes for user management.
"""

from flask import Blueprint, request, jsonify, g
from utils.jwt_utils import require_admin, create_error_response, create_success_response
from models.user import User, OAuthSession
import psycopg2

admin_bp = Blueprint('admin', __name__)

def get_db_connection():
    """Get database connection - will be injected by main app."""
    return getattr(g, 'db_connection', None)


@admin_bp.route('/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    """
    Get all users with pagination (admin only).
    
    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        search: Search term for email or name
    
    Returns:
        JSON response with paginated user list
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        # Validate parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # If search is provided, we need custom query
            if search:
                with conn.cursor() as cursor:
                    # Search in email, first_name, and last_name
                    search_pattern = f"%{search}%"
                    
                    # Count total results
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE is_active = TRUE 
                        AND (
                            email ILIKE %s 
                            OR first_name ILIKE %s 
                            OR last_name ILIKE %s
                            OR CONCAT(first_name, ' ', last_name) ILIKE %s
                        )
                    """, (search_pattern, search_pattern, search_pattern, search_pattern))
                    total_count = cursor.fetchone()[0]
                    
                    # Get paginated results
                    offset = (page - 1) * per_page
                    cursor.execute("""
                        SELECT id, google_id, email, first_name, last_name, avatar_url, role, 
                               is_active, created_at, updated_at, last_login
                        FROM users 
                        WHERE is_active = TRUE 
                        AND (
                            email ILIKE %s 
                            OR first_name ILIKE %s 
                            OR last_name ILIKE %s
                            OR CONCAT(first_name, ' ', last_name) ILIKE %s
                        )
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (search_pattern, search_pattern, search_pattern, search_pattern, per_page, offset))
                    
                    users = []
                    for row in cursor.fetchall():
                        users.append({
                            'id': row[0],
                            'google_id': row[1],
                            'email': row[2],
                            'first_name': row[3],
                            'last_name': row[4],
                            'avatar_url': row[5],
                            'role': row[6],
                            'is_active': row[7],
                            'created_at': row[8].isoformat() if row[8] else None,
                            'updated_at': row[9].isoformat() if row[9] else None,
                            'last_login': row[10].isoformat() if row[10] else None
                        })
                    
                    result = {
                        'users': users,
                        'total_count': total_count,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': (total_count + per_page - 1) // per_page,
                        'search': search
                    }
            else:
                # Use model method for regular pagination
                result = user_model.get_all_users(page, per_page)
                
                # Format dates for JSON serialization
                for user in result['users']:
                    user['created_at'] = user['created_at'].isoformat() if user['created_at'] else None
                    user['updated_at'] = user['updated_at'].isoformat() if user['updated_at'] else None
                    user['last_login'] = user['last_login'].isoformat() if user['last_login'] else None
            
            return jsonify(create_success_response(result))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get users: {str(e)}", 500)


@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_details(user_id):
    """
    Get detailed information about a specific user (admin only).
    
    Args:
        user_id: User ID to get details for
    
    Returns:
        JSON response with user details, preferences, and sessions
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize models
            user_model = User(conn)
            oauth_session_model = OAuthSession(conn)
            
            # Get user info
            user = user_model.get_user_by_id(user_id)
            if not user:
                return create_error_response("User not found", 404)
            
            # Get user preferences
            preferences = user_model.get_user_preferences(user_id)
            
            # Get user sessions
            sessions = oauth_session_model.get_user_sessions(user_id)
            
            # Format sessions for response
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
                'user': {
                    'id': user['id'],
                    'google_id': user['google_id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'avatar_url': user['avatar_url'],
                    'role': user['role'],
                    'is_active': user['is_active'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                },
                'preferences': preferences,
                'sessions': formatted_sessions,
                'session_count': len(formatted_sessions)
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get user details: {str(e)}", 500)


@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user_role(user_id):
    """
    Update user role (admin only).
    
    Args:
        user_id: User ID to update
    
    Expected JSON payload:
    {
        "role": "admin" | "user"
    }
    
    Returns:
        JSON response with updated user info
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        role = data.get('role')
        if not role:
            return create_error_response("Missing role field", 400)
        
        # Validate role
        if role not in ['user', 'admin']:
            return create_error_response("Role must be 'user' or 'admin'", 400)
        
        # Prevent self-demotion from admin
        if user_id == g.current_user['id'] and role != 'admin':
            return create_error_response("Cannot change your own admin role", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize user model
            user_model = User(conn)
            
            # Check if user exists
            user = user_model.get_user_by_id(user_id)
            if not user:
                return create_error_response("User not found", 404)
            
            # Update user role
            updated_user = user_model.update_user_role(user_id, role)
            
            return jsonify(create_success_response({
                'user': {
                    'id': updated_user['id'],
                    'email': updated_user['email'],
                    'first_name': updated_user['first_name'],
                    'last_name': updated_user['last_name'],
                    'role': updated_user['role'],
                    'updated_at': updated_user['updated_at'].isoformat() if updated_user['updated_at'] else None
                }
            }, f"User role updated to {role}"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to update user role: {str(e)}", 500)


@admin_bp.route('/admin/users/<int:user_id>/sessions', methods=['DELETE'])
@require_admin
def delete_user_sessions(user_id):
    """
    Delete all sessions for a specific user (admin only).
    
    Args:
        user_id: User ID to delete sessions for
    
    Returns:
        JSON response confirming session deletion
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize models
            user_model = User(conn)
            oauth_session_model = OAuthSession(conn)
            
            # Check if user exists
            user = user_model.get_user_by_id(user_id)
            if not user:
                return create_error_response("User not found", 404)
            
            # Get and delete all user sessions
            sessions = oauth_session_model.get_user_sessions(user_id)
            deleted_count = 0
            
            for session in sessions:
                oauth_session_model.delete_session(session['local_session_token'])
                deleted_count += 1
            
            return jsonify(create_success_response({
                'deleted_sessions': deleted_count
            }, f"Deleted {deleted_count} sessions for user"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to delete user sessions: {str(e)}", 500)


@admin_bp.route('/admin/stats', methods=['GET'])
@require_admin
def get_admin_stats():
    """
    Get admin dashboard statistics.
    
    Returns:
        JSON response with system statistics
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            with conn.cursor() as cursor:
                # Get user counts
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = TRUE")
                admin_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '30 days' AND is_active = TRUE")
                active_users_30d = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '7 days' AND is_active = TRUE")
                new_users_7d = cursor.fetchone()[0]
                
                # Get session counts
                cursor.execute("SELECT COUNT(*) FROM oauth_sessions")
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM oauth_sessions WHERE last_used > NOW() - INTERVAL '24 hours'")
                active_sessions_24h = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM oauth_sessions WHERE token_expires_at < NOW()")
                expired_sessions = cursor.fetchone()[0]
                
                # Get recent registrations
                cursor.execute("""
                    SELECT email, first_name, last_name, created_at
                    FROM users 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent_users = []
                for row in cursor.fetchall():
                    recent_users.append({
                        'email': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'created_at': row[3].isoformat() if row[3] else None
                    })
            
            return jsonify(create_success_response({
                'users': {
                    'total': total_users,
                    'admins': admin_users,
                    'active_30d': active_users_30d,
                    'new_7d': new_users_7d
                },
                'sessions': {
                    'total': total_sessions,
                    'active_24h': active_sessions_24h,
                    'expired': expired_sessions
                },
                'recent_users': recent_users
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get admin stats: {str(e)}", 500)


@admin_bp.route('/admin/cleanup', methods=['POST'])
@require_admin
def admin_cleanup():
    """
    Perform system cleanup tasks (admin only).
    
    Returns:
        JSON response with cleanup results
    """
    try:
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize session model
            oauth_session_model = OAuthSession(conn)
            
            # Clean up expired sessions
            deleted_sessions = oauth_session_model.cleanup_expired_sessions()
            
            # Clean up OAuth state storage
            from utils.oauth import oauth_storage
            oauth_storage.cleanup_expired_states()
            
            return jsonify(create_success_response({
                'deleted_sessions': deleted_sessions,
                'oauth_states_cleaned': True
            }, "System cleanup completed"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to perform cleanup: {str(e)}", 500)