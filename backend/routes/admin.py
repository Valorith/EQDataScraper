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


@admin_bp.route('/admin/database/config', methods=['GET'])
@require_admin
def get_database_config():
    """
    Get current database configuration (admin only).
    
    Returns:
        JSON response with database connection info
    """
    try:
        import json
        import os
        
        # Load current config from config.json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
        config = {}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config.json - production_database_url present: {bool(config.get('production_database_url'))}")
        else:
            logger.warning(f"config.json not found at {config_path}")
        
        # Prefer saved config over environment variable for production database
        # This ensures the configured database persists across deployments
        current_db_url = config.get('production_database_url', '') or os.environ.get('DATABASE_URL', '')
        
        # Parse URL to get connection details (without password)
        if current_db_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(current_db_url)
                
                # Use saved database type from config first, fall back to URL detection
                db_type = config.get('database_type')
                
                if not db_type:
                    # Detect database type from URL only if not saved
                    if 'mysql' in current_db_url.lower():
                        db_type = 'mysql'
                    elif 'mssql' in current_db_url.lower() or 'sqlserver' in current_db_url.lower():
                        db_type = 'mssql'
                    elif 'postgresql' in current_db_url.lower() or 'postgres' in current_db_url.lower():
                        db_type = 'postgresql'
                    else:
                        db_type = 'postgresql'  # default
                
                # Set default port based on detected type
                default_port = 5432
                if db_type == 'mysql':
                    default_port = 3306
                elif db_type == 'mssql':
                    default_port = 1433
                
                db_info = {
                    'host': parsed.hostname,
                    'port': parsed.port or default_port,
                    'database': parsed.path[1:] if parsed.path else '',
                    'username': parsed.username,
                    'connected': True,
                    'connection_type': 'environment' if os.environ.get('DATABASE_URL') else 'config',
                    'db_type': db_type,
                    'use_ssl': config.get('database_ssl', True)  # Include SSL setting
                }
                
                # Test EQEmu database connection
                try:
                    # Import database connector utils
                    import sys
                    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if backend_path not in sys.path:
                        sys.path.append(backend_path)
                    from utils.database_connectors import get_database_connector, test_database_query
                    
                    # Create connection config from saved settings
                    test_config = {
                        'host': db_info['host'],
                        'port': db_info['port'],
                        'database': db_info['database'],
                        'username': db_info['username'],
                        'password': parsed.password,  # Include password for testing
                        'use_ssl': config.get('database_ssl', True)
                    }
                    
                    # Test the EQEmu database connection
                    test_conn = get_database_connector(db_type, test_config)
                    test_result = test_database_query(test_conn, db_type)
                    test_conn.close()
                    
                    db_info['version'] = test_result.get('version', 'Unknown')
                    db_info['status'] = 'connected'
                    db_info['connected'] = True
                    
                    # Add table info if available
                    if test_result.get('tables'):
                        db_info['items_table_exists'] = test_result['tables'].get('items_exists', False)
                        db_info['discovered_items_table_exists'] = test_result['tables'].get('discovered_items_exists', False)
                        
                except Exception as e:
                    db_info['status'] = 'disconnected'
                    db_info['error'] = str(e)
                    db_info['connected'] = False
                
            except Exception as e:
                db_info = {
                    'connected': False,
                    'status': 'invalid_url',
                    'error': str(e)
                }
        else:
            # No database URL configured
            logger.info("No EQEmu database URL found in config.json or environment")
            db_type = config.get('database_type', 'mysql')
            db_info = {
                'connected': False,
                'status': 'no_database_configured',
                'db_type': db_type,
                'host': None,
                'port': None,
                'database': None,
                'username': None,
                'message': 'EQEmu database not configured. Please configure through admin dashboard.'
            }
        
        return jsonify(create_success_response({
            'database': db_info,
            'use_database_cache': config.get('use_production_database', False)
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to get database config: {str(e)}", 500)


@admin_bp.route('/admin/database/config', methods=['POST'])
@require_admin
def update_database_config():
    """
    Update database configuration (admin only) - READ-ONLY ACCESS.
    This will configure the connection but all database operations will be read-only.
    
    Expected JSON payload:
    {
        "host": "string",
        "port": 5432,
        "database": "string",
        "username": "string",
        "password": "string",
        "use_ssl": true
    }
    
    Returns:
        JSON response with updated configuration
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        # Validate required fields
        required_fields = ['host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f"Missing required field: {field}", 400)
        
        # Build connection URL with read-only parameters
        from utils.database_connectors import build_connection_url, get_database_connector
        
        db_type = data.get('db_type', 'postgresql')
        host = data['host']
        port = data['port']
        database = data['database']
        username = data['username']
        password = data['password']
        use_ssl = data.get('use_ssl', True)
        
        config = {
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password,
            'use_ssl': use_ssl
        }
        
        # Build appropriate connection URL
        connection_url = build_connection_url(db_type, config)
        
        # Test connection with read-only mode
        try:
            test_conn = get_database_connector(db_type, config)
            cursor = test_conn.cursor()
            try:
                # Ensure read-only mode where supported
                if db_type == 'postgresql':
                    cursor.execute("SET TRANSACTION READ ONLY")
                elif db_type == 'mysql':
                    cursor.execute("SET SESSION TRANSACTION READ ONLY")
                # SQL Server: rely on user permissions
                
                # Get version to verify connection
                if db_type == 'postgresql':
                    cursor.execute('SELECT version();')
                    version = cursor.fetchone()[0]
                elif db_type == 'mysql':
                    cursor.execute('SELECT VERSION();')
                    result = cursor.fetchone()
                    version = result.get('VERSION()') if isinstance(result, dict) else result[0]
                elif db_type == 'mssql':
                    cursor.execute('SELECT @@VERSION;')
                    version = cursor.fetchone()[0]
                else:
                    version = 'Unknown'
                
                # Test that we can access the required tables
                cursor.execute("SELECT COUNT(*) FROM items")
                items_accessible = True
                
                try:
                    cursor.execute("SELECT COUNT(*) FROM discovered_items")
                    discovered_items_accessible = True
                except:
                    discovered_items_accessible = False
                    
            finally:
                cursor.close()
            
            test_conn.close()
            
        except Exception as e:
            return create_error_response(f"Database connection test failed: {str(e)}", 400)
        
        # Update config.json
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
        config = {}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        config['production_database_url'] = connection_url
        config['use_production_database'] = True
        config['database_read_only'] = True  # Mark as read-only
        config['database_type'] = db_type  # Save database type
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Invalidate the database configuration cache to force reload
        try:
            # Access the Flask app's db_config_manager if available
            from flask import current_app
            if hasattr(current_app, 'db_config_manager'):
                current_app.db_config_manager.invalidate()
                logger.info("Database configuration cache invalidated after save")
        except Exception as e:
            logger.warning(f"Could not invalidate database config cache: {e}")
        
        # Log configuration change (if we have a working OAuth database connection)
        try:
            conn = get_db_connection()
            if conn:
                activity_log = ActivityLog(conn)
                activity_log.log_activity(
                    action=ActivityLog.ACTION_ADMIN_ACTION,
                    user_id=g.current_user['id'],
                    resource_type=ActivityLog.RESOURCE_SYSTEM,
                    resource_id='database_config',
                    details={
                    'action': 'update_database_config_readonly',
                    'host': host,
                    'port': port,
                    'database': database,
                    'username': username,
                    'use_ssl': use_ssl,
                    'read_only': True
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as e:
            # Log error but don't fail the save operation
            print(f"Warning: Could not log activity: {str(e)}")
        
        return jsonify(create_success_response({
            'message': 'Database configuration updated successfully (READ-ONLY mode)',
            'database': {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'use_ssl': use_ssl,
                'status': 'connected',
                'version': version,
                'read_only': True,
                'items_accessible': items_accessible,
                'discovered_items_accessible': discovered_items_accessible
            }
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to update database config: {str(e)}", 500)


@admin_bp.route('/admin/database/test', methods=['POST'])
@require_admin
def test_database_connection():
    """
    Test database connection with provided credentials (admin only) - READ-ONLY MODE.
    
    Expected JSON payload:
    {
        "host": "string",
        "port": 5432,
        "database": "string",
        "username": "string",
        "password": "string",
        "use_ssl": true
    }
    
    Returns:
        JSON response with connection test results
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return create_error_response("Missing request data", 400)
        
        # Validate required fields
        required_fields = ['host', 'port', 'database', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f"Missing required field: {field}", 400)
        
        # Test connection in READ-ONLY mode
        import time
        from utils.database_connectors import get_database_connector, test_database_query
        
        db_type = data.get('db_type', 'postgresql')  # Default to PostgreSQL for backwards compatibility
        host = data['host']
        port = data['port']
        database = data['database']
        username = data['username']
        password = data['password']
        use_ssl = data.get('use_ssl', True)
        
        test_config = {
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password,
            'use_ssl': use_ssl
        }
        
        start_time = time.time()
        
        try:
            test_conn = get_database_connector(db_type, test_config)
            
            # Test basic operations in READ-ONLY mode
            cursor = test_conn.cursor()
            try:
                # Set to read-only mode for PostgreSQL
                if db_type == 'postgresql':
                    cursor.execute("SET TRANSACTION READ ONLY")
                elif db_type == 'mysql':
                    cursor.execute("SET SESSION TRANSACTION READ ONLY")
                # SQL Server doesn't have a simple read-only transaction mode, rely on user permissions
                
                # Run database-specific tests
                test_results = test_database_query(test_conn, db_type)
                
                version = test_results['version']
                current_time = test_results['current_time']
                tables_info = test_results['tables']
                
                items_table_exists = tables_info.get('items_exists', False)
                discovered_items_table_exists = tables_info.get('discovered_items_exists', False)
                items_accessible = tables_info.get('items_accessible', False)
                items_count = tables_info.get('items_count', 0)
                discovered_items_accessible = tables_info.get('discovered_items_accessible', False)
                discovered_items_count = tables_info.get('discovered_items_count', 0)
            finally:
                cursor.close()
            
            test_conn.close()
            
            connection_time = round((time.time() - start_time) * 1000, 2)
            
            return jsonify(create_success_response({
                'connection_successful': True,
                'connection_time_ms': connection_time,
                'database_version': version,
                'server_time': str(current_time),  # Convert to string instead of isoformat
                'read_only_mode': True,
                'tables': {
                    'items_exists': items_table_exists,
                    'items_accessible': items_accessible,
                    'items_count': items_count,
                    'discovered_items_exists': discovered_items_table_exists,
                    'discovered_items_accessible': discovered_items_accessible,
                    'discovered_items_count': discovered_items_count
                },
                'message': 'Database connection successful (READ-ONLY mode)'
            }))
            
        except Exception as e:
            # Determine error type based on exception class
            is_connection_error = True  # Most database errors are connection-related
            
            # Try to import database-specific modules for better error detection
            try:
                if 'psycopg2' in str(type(e).__module__):
                    is_connection_error = isinstance(e, psycopg2.OperationalError)
            except:
                pass
            
            # Connection-level errors (host not found, auth failed, etc.)
            error_details = {
                'error_type': 'connection_error',
                'error_message': str(e),
                'details': {}
            }
            
            error_str = str(e).lower()
            if 'could not translate host name' in error_str or 'name or service not known' in error_str:
                error_details['details']['issue'] = 'Host not found'
                error_details['details']['suggestion'] = 'Check that the hostname is correct and accessible from this server'
            elif 'connection refused' in error_str:
                error_details['details']['issue'] = 'Connection refused'
                error_details['details']['suggestion'] = f'Check that PostgreSQL is running on {host}:{port} and accepting connections'
            elif 'password authentication failed' in error_str or 'authentication failed' in error_str:
                error_details['details']['issue'] = 'Authentication failed'
                error_details['details']['suggestion'] = 'Check username and password are correct'
            elif 'database' in error_str and 'does not exist' in error_str:
                error_details['details']['issue'] = 'Database not found'
                error_details['details']['suggestion'] = f'The database "{database}" does not exist on the server'
            elif 'timeout' in error_str:
                error_details['details']['issue'] = 'Connection timeout'
                error_details['details']['suggestion'] = 'Server is not responding. Check network connectivity and firewall rules'
            elif 'ssl' in error_str:
                error_details['details']['issue'] = 'SSL connection error'
                error_details['details']['suggestion'] = 'Try toggling the SSL option or check server SSL configuration'
            else:
                error_details['details']['issue'] = 'Connection failed'
                error_details['details']['suggestion'] = 'Check server logs for more details'
            
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'error': error_details
            }), 400
            
        except psycopg2.ProgrammingError as e:
            # SQL/permission errors
            error_details = {
                'error_type': 'permission_error',
                'error_message': str(e),
                'details': {
                    'issue': 'Permission denied or SQL error',
                    'suggestion': 'Check that the user has proper permissions to access the database and tables'
                }
            }
            return jsonify({
                'success': False,
                'message': 'Database permission error',
                'error': error_details
            }), 400
            
        except psycopg2.Error as e:
            # Other PostgreSQL errors
            error_details = {
                'error_type': 'database_error',
                'error_message': str(e),
                'details': {
                    'issue': 'Database error',
                    'suggestion': 'An unexpected database error occurred'
                }
            }
            return jsonify({
                'success': False,
                'message': 'Database error',
                'error': error_details
            }), 400
            
        except Exception as e:
            # Non-PostgreSQL errors
            error_details = {
                'error_type': 'general_error',
                'error_message': str(e),
                'details': {
                    'issue': 'Unexpected error',
                    'suggestion': 'An unexpected error occurred during connection test'
                }
            }
            return jsonify({
                'success': False,
                'message': 'Connection test failed',
                'error': error_details
            }), 500
        
    except Exception as e:
        return create_error_response(f"Failed to test database connection: {str(e)}", 500)


# Note: Database initialization endpoint removed for read-only access
# The EQEmu database should already have the required tables:
# - items: Main items table with EQEmu schema
# - discovered_items: Tracks which items have been discovered by players