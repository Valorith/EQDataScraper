"""
Admin routes for user management.
"""

from flask import Blueprint, request, jsonify, g
from utils.jwt_utils import require_admin, create_error_response, create_success_response
from models.user import User, OAuthSession
from models.activity import ActivityLog
import psycopg2
from datetime import datetime, timedelta

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
            # Return basic stats without database
            return jsonify(create_success_response({
                'totalUsers': 0,
                'activeToday': 0,
                'adminUsers': 0
            }))
        
        try:
            with conn.cursor() as cursor:
                # Get user counts
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = TRUE")
                admin_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '24 hours' AND is_active = TRUE")
                active_today = cursor.fetchone()[0]
                
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
                'totalUsers': total_users,
                'activeToday': active_today,
                'adminUsers': admin_users,
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


@admin_bp.route('/admin/activities', methods=['GET'])
@require_admin
def get_recent_activities():
    """
    Get recent system activities.
    
    Query parameters:
        limit: Number of activities to return (default: 50, max: 100)
        offset: Offset for pagination (default: 0)
        action: Filter by specific action type
        user_id: Filter by specific user ID
        start_date: Filter activities after this date (ISO format)
        end_date: Filter activities before this date (ISO format)
    
    Returns:
        JSON response with recent activities
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        action = request.args.get('action')
        user_id = request.args.get('user_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Validate parameters
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
        
        # Parse dates if provided
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except:
                return create_error_response("Invalid start_date format", 400)
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except:
                return create_error_response("Invalid end_date format", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            # Return mock activities for development when no database is available
            from datetime import datetime, timedelta
            
            mock_activities = [
                {
                    'id': 1,
                    'action': 'login',
                    'user_id': 1,
                    'user_display': 'Development User',
                    'resource_type': 'session',
                    'resource_id': 'dev-session-1',
                    'details': {'method': 'google_oauth'},
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser',
                    'created_at': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'description': 'Development User logged in'
                },
                {
                    'id': 2,
                    'action': 'spell_search',
                    'user_id': 1,
                    'user_display': 'Development User',
                    'resource_type': 'spell',
                    'resource_id': 'heal',
                    'details': {'query': 'heal', 'results_count': 45},
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser',
                    'created_at': (datetime.now() - timedelta(minutes=10)).isoformat(),
                    'description': 'Development User searched for spells: "heal"'
                },
                {
                    'id': 3,
                    'action': 'cache_refresh',
                    'user_id': None,
                    'user_display': 'System',
                    'resource_type': 'cache',
                    'resource_id': 'all_classes',
                    'details': {'refreshed_classes': 16},
                    'ip_address': None,
                    'user_agent': None,
                    'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'description': 'System refreshed cache for all classes'
                },
                {
                    'id': 4,
                    'action': 'scrape_complete',
                    'user_id': 1,
                    'user_display': 'Development User',
                    'resource_type': 'class',
                    'resource_id': 'paladin',
                    'details': {'spell_count': 142, 'duration_seconds': 8.3},
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser',
                    'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'description': 'Development User completed scraping for Paladin (142 spells)'
                },
                {
                    'id': 5,
                    'action': 'spell_view',
                    'user_id': 1,
                    'user_display': 'Development User',
                    'resource_type': 'spell',
                    'resource_id': '1234',
                    'details': {'spell_name': 'Complete Heal', 'class': 'cleric'},
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser',
                    'created_at': (datetime.now() - timedelta(hours=3)).isoformat(),
                    'description': 'Development User viewed spell details: Complete Heal'
                }
            ]
            
            return jsonify(create_success_response({
                'activities': mock_activities[:limit],  # Respect the limit parameter
                'total_count': len(mock_activities)
            }))
        
        try:
            # Initialize activity log model
            activity_log = ActivityLog(conn)
            
            # Get activities
            activities = activity_log.get_recent_activities(
                limit=limit,
                offset=offset,
                user_id=user_id,
                action=action,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get total count for pagination
            total_count = activity_log.get_activity_count(
                user_id=user_id,
                action=action,
                start_date=start_date,
                end_date=end_date
            )
            
            
            # Format activities for response
            formatted_activities = []
            for activity in activities:
                formatted_activity = {
                    'id': activity['id'],
                    'action': activity['action'],
                    'user_id': activity['user_id'],
                    'user_display': activity.get('user_display', 'System'),
                    'resource_type': activity['resource_type'],
                    'resource_id': activity['resource_id'],
                    'details': activity['details'],
                    'ip_address': str(activity['ip_address']) if activity['ip_address'] else None,
                    'user_agent': activity['user_agent'],
                    'created_at': activity['created_at'].isoformat() if activity['created_at'] else None
                }
                
                # Create human-readable description
                if activity['action'] == ActivityLog.ACTION_LOGIN:
                    formatted_activity['description'] = f"{activity.get('user_display', 'User')} logged in"
                elif activity['action'] == ActivityLog.ACTION_LOGOUT:
                    formatted_activity['description'] = f"{activity.get('user_display', 'User')} logged out"
                elif activity['action'] == ActivityLog.ACTION_CACHE_REFRESH:
                    formatted_activity['description'] = f"{activity.get('user_display', 'System')} refreshed cache"
                elif activity['action'] == ActivityLog.ACTION_SCRAPE_START:
                    class_name = activity['details'].get('class_name', 'Unknown') if activity['details'] else 'Unknown'
                    formatted_activity['description'] = f"Started scraping {class_name} spells"
                elif activity['action'] == ActivityLog.ACTION_SCRAPE_COMPLETE:
                    class_name = activity['details'].get('class_name', 'Unknown') if activity['details'] else 'Unknown'
                    count = activity['details'].get('spell_count', 0) if activity['details'] else 0
                    formatted_activity['description'] = f"Completed scraping {count} {class_name} spells"
                elif activity['action'] == ActivityLog.ACTION_USER_CREATE:
                    formatted_activity['description'] = f"New user {activity.get('user_display', 'Unknown')} created"
                elif activity['action'] == ActivityLog.ACTION_USER_UPDATE:
                    formatted_activity['description'] = f"{activity.get('user_display', 'User')} updated profile"
                else:
                    formatted_activity['description'] = f"{activity['action']} by {activity.get('user_display', 'System')}"
                
                formatted_activities.append(formatted_activity)
            
            return jsonify(create_success_response({
                'activities': formatted_activities,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get activities: {str(e)}", 500)


@admin_bp.route('/admin/activities', methods=['POST'])
@require_admin
def log_activity():
    """
    Log a new activity (admin only).
    
    Expected JSON payload:
    {
        "action": "string",
        "resource_type": "string",
        "resource_id": "string",
        "details": {},
        "user_id": 123
    }
    
    Returns:
        JSON response with created activity
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        action = data.get('action')
        if not action:
            return create_error_response("Missing action field", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize activity log model
            activity_log = ActivityLog(conn)
            
            # Log the activity
            activity = activity_log.log_activity(
                action=action,
                user_id=data.get('user_id', g.current_user['id']),
                resource_type=data.get('resource_type'),
                resource_id=data.get('resource_id'),
                details=data.get('details'),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(create_success_response({
                'activity': {
                    'id': activity['id'],
                    'action': activity['action'],
                    'created_at': activity['created_at'].isoformat() if activity['created_at'] else None
                }
            }, "Activity logged"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to log activity: {str(e)}", 500)


@admin_bp.route('/admin/activities/stats', methods=['GET'])
@require_admin
def get_activity_stats():
    """
    Get activity statistics.
    
    Query parameters:
        hours: Number of hours to look back (default: 24, max: 168)
    
    Returns:
        JSON response with activity statistics
    """
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        
        # Validate parameters
        if hours < 1 or hours > 168:  # Max 7 days
            hours = 24
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            # Return empty stats without database
            return jsonify(create_success_response({
                'time_period_hours': hours,
                'total_activities': 0,
                'unique_users': 0,
                'action_counts': {},
                'most_active_users': []
            }))
        
        try:
            # Initialize activity log model
            activity_log = ActivityLog(conn)
            
            # Get activity stats
            stats = activity_log.get_activity_stats(hours=hours)
            
            return jsonify(create_success_response(stats))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to get activity stats: {str(e)}", 500)


@admin_bp.route('/admin/activities/cleanup', methods=['POST'])
@require_admin
def cleanup_old_activities():
    """
    Clean up old activities (admin only).
    
    Expected JSON payload:
    {
        "days": 90
    }
    
    Returns:
        JSON response with cleanup results
    """
    try:
        # Get request data
        data = request.get_json()
        days = data.get('days', 90) if data else 90
        
        # Validate days parameter
        if days < 30:  # Minimum 30 days retention
            return create_error_response("Minimum retention period is 30 days", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        try:
            # Initialize activity log model
            activity_log = ActivityLog(conn)
            
            # Clean up old activities
            deleted_count = activity_log.cleanup_old_activities(days=days)
            
            # Log the cleanup action
            activity_log.log_activity(
                action=ActivityLog.ACTION_ADMIN_ACTION,
                user_id=g.current_user['id'],
                resource_type=ActivityLog.RESOURCE_SYSTEM,
                details={'action': 'cleanup_activities', 'days': days, 'deleted_count': deleted_count},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(create_success_response({
                'deleted_activities': deleted_count,
                'retention_days': days
            }, f"Deleted {deleted_count} activities older than {days} days"))
            
        except Exception as e:
            return create_error_response(f"Database error: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Failed to cleanup activities: {str(e)}", 500)


@admin_bp.route('/api/cache/refresh', methods=['POST'])
@require_admin 
def refresh_all_caches():
    """
    Refresh all caches (admin only).
    
    Returns:
        JSON response confirming cache refresh
    """
    try:
        # Import cache functions from main app
        from app import save_cache_to_disk
        
        # Get database connection
        conn = get_db_connection()
        if conn:
            # Log cache refresh activity
            activity_log = ActivityLog(conn)
            activity_log.log_activity(
                action=ActivityLog.ACTION_CACHE_REFRESH,
                user_id=g.current_user['id'],
                resource_type=ActivityLog.RESOURCE_CACHE,
                resource_id='all',
                details={'action': 'manual_refresh', 'initiated_by': 'admin'},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        # Save current cache state to disk
        save_cache_to_disk()
        
        return jsonify(create_success_response({
            'message': 'All caches refreshed successfully'
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to refresh caches: {str(e)}", 500)