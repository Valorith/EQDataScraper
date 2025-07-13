"""
Admin routes for user management.
"""

from flask import Blueprint, request, jsonify, g
from utils.jwt_utils import require_admin, require_auth, create_error_response, create_success_response
from models.user import User, OAuthSession
from models.activity import ActivityLog
import psycopg2
from datetime import datetime, timedelta
import logging
import os
import psutil
import time
from collections import defaultdict, deque
import json
import threading
import atexit
from utils.query_tracking_persistence import QueryTrackingPersistence

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Initialize query tracking persistence
query_persistence = QueryTrackingPersistence()

# Timeline data persistence
TIMELINE_DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'timeline_data.json')

def save_timeline_data(timeline_data):
    """Save timeline data to disk."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(TIMELINE_DATA_FILE), exist_ok=True)
        
        # Convert deque to list and filter out entries older than 7 days
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        timeline_list = []
        for entry in timeline_data:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time > seven_days_ago:
                # Convert defaultdict to regular dict for JSON serialization
                entry_copy = entry.copy()
                entry_copy['tables'] = dict(entry_copy['tables'])
                timeline_list.append(entry_copy)
        
        # Save to file
        with open(TIMELINE_DATA_FILE, 'w') as f:
            json.dump(timeline_list, f, indent=2)
            
        try:
            logger.info(f"Timeline data saved to {TIMELINE_DATA_FILE} ({len(timeline_list)} entries)")
        except:
            pass  # Logger may be closed during shutdown
        
    except Exception as e:
        try:
            logger.error(f"Failed to save timeline data: {e}")
        except:
            pass  # Logger may be closed during shutdown

def load_timeline_data():
    """Load timeline data from disk."""
    try:
        if not os.path.exists(TIMELINE_DATA_FILE):
            logger.info("No timeline data file found, starting with empty timeline")
            return deque(maxlen=168)
        
        with open(TIMELINE_DATA_FILE, 'r') as f:
            timeline_list = json.load(f)
        
        # Filter out entries older than 7 days
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        timeline_deque = deque(maxlen=168)
        for entry in timeline_list:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time > seven_days_ago:
                # Convert tables back to defaultdict
                entry['tables'] = defaultdict(int, entry['tables'])
                timeline_deque.append(entry)
        
        logger.info(f"Timeline data loaded from {TIMELINE_DATA_FILE} ({len(timeline_deque)} entries)")
        return timeline_deque
        
    except Exception as e:
        logger.error(f"Failed to load timeline data: {e}")
        return deque(maxlen=168)

def periodic_save_timeline():
    """Periodically save timeline data to disk with enhanced error handling - DISABLED."""
    logger.info("⚠️ Periodic timeline save DISABLED to debug hanging issue")
    # TEMPORARILY DISABLED: Background thread with while True loop may be causing hanging
    
    # def save_worker():
    #     while True:
    #         try:
    #             time.sleep(3600)  # Save every hour
    #             db_stats = system_metrics['database_stats']
    #             save_timeline_data(db_stats['timeline'])
    #             logger.info("Periodic timeline data save completed successfully")
    #         except Exception as e:
    #             logger.error(f"Periodic timeline save failed: {e}")
    #             # Continue running even if save fails
    # 
    # try:
    #     # Start the periodic save thread with enhanced error handling
    #     save_thread = threading.Thread(target=save_worker, daemon=True)
    #     save_thread.start()
    #     logger.info("Periodic timeline data save thread started successfully")
    # except Exception as e:
    #     logger.error(f"Failed to start periodic save thread: {e}")

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
                               is_active, created_at, updated_at, last_login, display_name, avatar_class
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
                            'last_login': row[10].isoformat() if row[10] else None,
                            'display_name': row[11],
                            'avatar_class': row[12]
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
    """Get recent system activities with pagination and filtering"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action', type=str)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
            
        # Parse date parameters
        start_date_obj = None
        end_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid start_date format", 400)
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response("Invalid end_date format", 400)
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            # Return mock activities for development when no database
            mock_activities = [
                {
                    'id': 1,
                    'action': 'login',
                    'user_display': 'Development User',
                    'description': 'Development User logged in',
                    'created_at': datetime.now().isoformat(),
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser'
                },
                {
                    'id': 2,
                    'action': 'user_view',
                    'user_display': 'Development User',
                    'description': 'Development User viewed profile',
                    'created_at': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'ip_address': '127.0.0.1',
                    'user_agent': 'Development Browser'
                }
            ]
            return create_success_response({
                'activities': mock_activities,
                'total_count': len(mock_activities)
            })
        
        # Use ActivityLog to fetch activities
        activity_log = ActivityLog(conn)
        activities = activity_log.get_recent_activities(
            limit=limit,
            offset=offset,
            user_id=user_id,
            action=action,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        total_count = activity_log.get_activity_count(
            user_id=user_id,
            action=action,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        # Format activities with descriptions
        formatted_activities = []
        for activity in activities:
            formatted_activity = dict(activity)
            
            # Add formatted description
            user_display = activity.get('user_display', 'Unknown User')
            action_type = activity.get('action', 'unknown')
            
            if action_type == ActivityLog.ACTION_LOGIN:
                formatted_activity['description'] = f"{user_display} logged in"
            elif action_type == 'user_view':
                formatted_activity['description'] = f"{user_display} viewed profile"
            elif action_type == 'admin_action':
                formatted_activity['description'] = f"{user_display} performed admin action"
            else:
                formatted_activity['description'] = f"{user_display} performed {action_type}"
            
            # Ensure created_at is properly formatted
            if 'created_at' in formatted_activity and isinstance(formatted_activity['created_at'], datetime):
                formatted_activity['created_at'] = formatted_activity['created_at'].isoformat()
                
            formatted_activities.append(formatted_activity)
        
        return create_success_response({
            'activities': formatted_activities,
            'total_count': total_count
        })
        
    except Exception as e:
        logger.error(f"Failed to get activities: {e}")
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
    """Refresh all caches (admin only)"""
    try:
        from app import refresh_all_caches
        result = refresh_all_caches()
        return jsonify({
            'success': True,
            'message': 'All caches refreshed successfully',
            'result': result
        })
    except Exception as e:
        logger.error(f"Error refreshing caches: {e}")
        return create_error_response(f'Failed to refresh caches: {str(e)}', 500)


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
        from utils.persistent_config import get_persistent_config
        
        # Get diagnostic info about persistent storage with error handling
        try:
            persistent_config = get_persistent_config()
            storage_info = {
                'data_directory': str(persistent_config.data_dir) if persistent_config.data_dir else 'Not available',
                'config_file': str(persistent_config.config_file) if persistent_config.config_file else None,
                'storage_available': getattr(persistent_config, '_available', False),
                'directory_exists': persistent_config.data_dir.exists() if persistent_config.data_dir else False,
                'directory_writable': os.access(persistent_config.data_dir, os.W_OK) if persistent_config.data_dir and persistent_config.data_dir.exists() else False,
                'config_file_exists': persistent_config.config_file.exists() if persistent_config.config_file else False
            }
        except Exception as storage_error:
            logger.warning(f"Persistent storage diagnostic failed: {storage_error}")
            storage_info = {
                'storage_available': False,
                'error': str(storage_error)
            }
            persistent_config = None
        
        # Try persistent config first (for production) with error handling
        db_config = None
        if persistent_config:
            try:
                db_config = persistent_config.get_database_config()
            except Exception as config_error:
                logger.warning(f"Failed to get database config from persistent storage: {config_error}")
                db_config = None
        
        if db_config:
            current_db_url = db_config['production_database_url']
            config = db_config
            logger.info("Loaded database config from persistent storage")
            storage_info['config_source'] = 'persistent_storage'
        else:
            # Check environment variable
            env_db_url = os.environ.get('EQEMU_DATABASE_URL')
            if env_db_url:
                current_db_url = env_db_url
                config = {
                    'production_database_url': env_db_url,
                    'database_type': os.environ.get('EQEMU_DATABASE_TYPE', 'mysql'),
                    'database_ssl': os.environ.get('EQEMU_DATABASE_SSL', 'true').lower() == 'true'
                }
                logger.info("Loaded database config from environment variable")
                storage_info['config_source'] = 'environment_variable'
            else:
                # Fall back to config.json for local development
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
                config = {}
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    logger.info(f"Loaded config.json - production_database_url present: {bool(config.get('production_database_url'))}")
                else:
                    logger.warning(f"config.json not found at {config_path}")
                
                # Get production database URL from config only
                current_db_url = config.get('production_database_url', '')
                storage_info['config_source'] = 'config_json' if current_db_url else 'none'
        
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
                
                # Lightweight database connection test (no heavy queries)
                try:
                    # Import database connector utils
                    import sys
                    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if backend_path not in sys.path:
                        sys.path.append(backend_path)
                    from utils.database_connectors import get_database_connector
                    
                    # Create connection config from saved settings
                    test_config = {
                        'host': db_info['host'],
                        'port': db_info['port'],
                        'database': db_info['database'],
                        'username': db_info['username'],
                        'password': parsed.password,  # Include password for testing
                        'use_ssl': config.get('database_ssl', True)
                    }
                    
                    # LIGHTWEIGHT TEST: Just verify connection without table queries
                    test_conn = get_database_connector(db_type, test_config, track_queries=False)
                    
                    # Simple connection validation - no table queries to reduce load
                    cursor = test_conn.cursor()
                    cursor.execute("SELECT 1")  # Minimal query just to test connection
                    cursor.fetchone()
                    cursor.close()
                    test_conn.close()
                    
                    # Set basic connection success info without table details
                    test_result = {
                        'version': 'Connected',
                        'tables': {
                            'items_exists': None,  # Not tested to avoid unnecessary queries
                            'discovered_items_exists': None
                        }
                    }
                    
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
            'use_database_cache': config.get('use_production_database', False),
            'storage_info': storage_info
        }))
        
    except Exception as e:
        logger.error(f"Database config endpoint error: {str(e)}")
        import traceback
        logger.error(f"Database config traceback: {traceback.format_exc()}")
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
        
        # Save configuration
        import json
        import os
        from utils.persistent_config import get_persistent_config
        
        # Save to persistent storage (for production)
        persistent_config = get_persistent_config()
        saved_to_persistent = persistent_config.save_database_config(
            db_url=connection_url,
            db_type=db_type,
            use_ssl=use_ssl,
            db_name=database,
            db_password=password,
            db_port=str(port)
        )
        
        if saved_to_persistent:
            logger.info("Database config saved to persistent storage")
        
        # Also update config.json for local development
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
        config = {}
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        config['production_database_url'] = connection_url
        config['use_production_database'] = True
        config['database_read_only'] = True  # Mark as read-only
        config['database_type'] = db_type  # Save database type
        config['database_ssl'] = use_ssl  # Save SSL setting
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Database config saved to config.json")
        except Exception as e:
            logger.warning(f"Could not save to config.json: {e}")
        
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


@admin_bp.route('/admin/database/stored-config', methods=['GET'])
@require_admin
def get_stored_database_config():
    """
    Get the stored database configuration (for populating the config modal).
    This returns the configuration even if the database is disconnected.
    
    Returns:
        JSON response with stored configuration data
    """
    try:
        from utils.persistent_config import get_persistent_config
        from urllib.parse import urlparse
        
        # Get stored configuration from persistent storage
        persistent_config = get_persistent_config()
        db_config = persistent_config.get_database_config()
        
        if not db_config:
            return create_error_response("No database configuration found", 404)
        
        # Parse the database URL to extract components
        db_url = db_config.get('production_database_url')
        if not db_url:
            return create_error_response("No database URL found in configuration", 404)
        
        try:
            parsed = urlparse(db_url)
            config_data = {
                'database_type': db_config.get('database_type', 'mysql'),
                'host': parsed.hostname,
                'port': parsed.port,
                'database_name': parsed.path[1:] if parsed.path else '',
                'username': parsed.username,
                'database_ssl': db_config.get('database_ssl', True),
                'config_source': db_config.get('config_source', 'unknown')
            }
            
            return jsonify({
                'success': True,
                'data': config_data
            })
        except Exception as e:
            return create_error_response(f"Error parsing database configuration: {str(e)}", 500)
            
    except Exception as e:
        return create_error_response(f"Error loading stored database configuration: {str(e)}", 500)


@admin_bp.route('/admin/network/test', methods=['POST'])
@require_admin
def test_network_connectivity():
    """
    Test network connectivity to various hosts (admin only).
    
    Expected JSON payload:
    {
        "host": "string or IP",
        "port": 3306,
        "test_type": "ping|tcp|mysql"  # Optional, defaults to "tcp"
    }
    
    Returns:
        JSON response with connectivity test results
    """
    try:
        import socket
        import time
        import subprocess
        import platform
        
        data = request.get_json()
        if not data or not data.get('host'):
            return create_error_response("Missing host parameter", 400)
        
        host = data.get('host')
        port = data.get('port', 3306)
        test_type = data.get('test_type', 'tcp')
        
        results = {
            'host': host,
            'port': port,
            'test_type': test_type,
            'tests': {}
        }
        
        # Test 1: DNS Resolution
        try:
            start_time = time.time()
            addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            resolution_time = time.time() - start_time
            
            results['tests']['dns_resolution'] = {
                'success': True,
                'time_ms': round(resolution_time * 1000, 2),
                'resolved_addresses': [info[4][0] for info in addr_info],
                'message': f"Successfully resolved {host}"
            }
        except Exception as e:
            results['tests']['dns_resolution'] = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'message': f"DNS resolution failed: {str(e)}"
            }
        
        # Test 2: TCP Connection
        if test_type in ['tcp', 'mysql']:
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((host, port))
                sock.close()
                connection_time = time.time() - start_time
                
                if result == 0:
                    results['tests']['tcp_connection'] = {
                        'success': True,
                        'time_ms': round(connection_time * 1000, 2),
                        'message': f"TCP connection to {host}:{port} successful"
                    }
                else:
                    results['tests']['tcp_connection'] = {
                        'success': False,
                        'error_code': result,
                        'message': f"TCP connection failed with error code {result}"
                    }
            except Exception as e:
                results['tests']['tcp_connection'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'message': f"TCP connection failed: {str(e)}"
                }
        
        # Test 3: Ping (if requested and platform supports it)
        if test_type == 'ping':
            try:
                # Determine ping command based on platform
                system = platform.system().lower()
                if system == 'windows':
                    cmd = ['ping', '-n', '1', '-w', '3000', host]
                else:
                    cmd = ['ping', '-c', '1', '-W', '3', host]
                
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                ping_time = time.time() - start_time
                
                results['tests']['icmp_ping'] = {
                    'success': result.returncode == 0,
                    'time_ms': round(ping_time * 1000, 2),
                    'output': result.stdout if result.returncode == 0 else result.stderr,
                    'message': "Ping successful" if result.returncode == 0 else "Ping failed"
                }
            except subprocess.TimeoutExpired:
                results['tests']['icmp_ping'] = {
                    'success': False,
                    'error': 'Timeout',
                    'message': 'Ping command timed out after 5 seconds'
                }
            except Exception as e:
                results['tests']['icmp_ping'] = {
                    'success': False,
                    'error': str(e),
                    'message': f"Ping failed: {str(e)}"
                }
        
        # Test 4: MySQL Connection (if requested)
        if test_type == 'mysql' and results['tests'].get('tcp_connection', {}).get('success'):
            try:
                import pymysql
                
                # For MySQL test, we need credentials
                username = data.get('username', 'root')
                password = data.get('password', '')
                database = data.get('database', 'test')
                
                start_time = time.time()
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database,
                    connect_timeout=10
                )
                conn.close()
                mysql_time = time.time() - start_time
                
                results['tests']['mysql_connection'] = {
                    'success': True,
                    'time_ms': round(mysql_time * 1000, 2),
                    'message': f"MySQL connection to {host}:{port} successful"
                }
            except Exception as e:
                results['tests']['mysql_connection'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'message': f"MySQL connection failed: {str(e)}"
                }
        
        # Overall status
        all_success = all(test.get('success', False) for test in results['tests'].values())
        results['overall_success'] = all_success
        results['summary'] = "All tests passed" if all_success else "Some tests failed"
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return create_error_response(f"Network test failed: {str(e)}", 500)


@admin_bp.route('/admin/database/diagnostics', methods=['GET'])
@require_admin
def database_diagnostics():
    """
    Run comprehensive database diagnostics to identify connection issues.
    
    Returns:
        JSON response with diagnostic information
    """
    try:
        import os
        from utils.persistent_config import get_persistent_config
        from urllib.parse import urlparse
        
        diagnostics = {
            'environment': {
                'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'not set'),
                'EQEMU_DATABASE_URL': 'set' if os.environ.get('EQEMU_DATABASE_URL') else 'not set',
                'DATABASE_URL': 'set' if os.environ.get('DATABASE_URL') else 'not set',
                'EQEMU_DATABASE_TYPE': os.environ.get('EQEMU_DATABASE_TYPE', 'not set'),
                'EQEMU_DATABASE_SSL': os.environ.get('EQEMU_DATABASE_SSL', 'not set'),
                'EQEMU_DATABASE_HOST': os.environ.get('EQEMU_DATABASE_HOST', 'not set'),
                'EQEMU_DATABASE_PORT': os.environ.get('EQEMU_DATABASE_PORT', 'not set'),
                'EQEMU_DATABASE_NAME': os.environ.get('EQEMU_DATABASE_NAME', 'not set'),
                'ENABLE_USER_ACCOUNTS': os.environ.get('ENABLE_USER_ACCOUNTS', 'not set'),
                'PYTHON_VERSION': os.environ.get('PYTHON_VERSION', 'not set'),
                'NODE_ENV': os.environ.get('NODE_ENV', 'not set'),
            },
            'config_checks': {},
            'connection_test': {},
            'connection_pooling': {},
            'config_validation': {},
            'persistent_storage': {},
            'runtime_config': {},
            'config_sources': {}
        }
        
        # Check persistent config
        try:
            persistent_config = get_persistent_config()
            db_config = persistent_config.get_database_config()
            
            if db_config:
                diagnostics['config_checks']['persistent_config_found'] = True
                diagnostics['config_checks']['config_source'] = db_config.get('config_source', 'unknown')
                diagnostics['config_checks']['has_url'] = bool(db_config.get('production_database_url'))
                
                # Parse URL for display (hide password)
                if db_config.get('production_database_url'):
                    parsed = urlparse(db_config['production_database_url'])
                    diagnostics['config_checks']['host'] = parsed.hostname
                    diagnostics['config_checks']['port'] = parsed.port
                    diagnostics['config_checks']['database'] = parsed.path[1:] if parsed.path else ''
                    diagnostics['config_checks']['username'] = parsed.username
                    diagnostics['config_checks']['has_password'] = bool(parsed.password)
                    
                # Include all config values (excluding password)
                diagnostics['config_checks']['database_type'] = db_config.get('database_type', 'not set')
                diagnostics['config_checks']['use_production_database'] = db_config.get('use_production_database', False)
                diagnostics['config_checks']['database_read_only'] = db_config.get('database_read_only', True)
                diagnostics['config_checks']['database_ssl'] = db_config.get('database_ssl', False)
                diagnostics['config_checks']['config_timestamp'] = db_config.get('updated_at', 'not set')
            else:
                diagnostics['config_checks']['persistent_config_found'] = False
        except Exception as e:
            diagnostics['config_checks']['error'] = str(e)
        
        # Check database connection
        try:
            import time
            from app import get_eqemu_db_connection, db_config_manager
            
            # Force reload config
            logger.info("Diagnostics: About to force reload db_config_manager")
            reload_start = time.time()
            current_config = db_config_manager.force_reload()
            reload_time = time.time() - reload_start
            logger.info(f"Diagnostics: db_config_manager force reload returned: {type(current_config)}")
            diagnostics['config_checks']['config_reload_time_ms'] = round(reload_time * 1000, 2)
            
            diagnostics['config_checks']['db_config_manager_keys'] = list(current_config.keys()) if current_config else []
            diagnostics['config_checks']['db_config_manager_has_url'] = 'production_database_url' in current_config if current_config else False
            diagnostics['config_checks']['db_config_manager_type'] = str(type(current_config))
            
            # Get the actual connection parameters being used
            if hasattr(db_config_manager, '_parsed_config') and db_config_manager._parsed_config:
                parsed = db_config_manager._parsed_config
                diagnostics['config_checks']['active_connection'] = {
                    'host': parsed.get('host', 'not set'),
                    'port': parsed.get('port', 'not set'),
                    'database': parsed.get('database', 'not set'),
                    'username': parsed.get('username', 'not set'),
                    'has_password': bool(parsed.get('password')),
                    'use_ssl': parsed.get('use_ssl', False),
                    'db_type': parsed.get('db_type', 'not set')
                }
            else:
                diagnostics['config_checks']['active_connection'] = 'No parsed configuration available'
            
            connection_start = time.time()
            test_conn, db_type, error = get_eqemu_db_connection()
            connection_time = time.time() - connection_start
            diagnostics['connection_test']['connection_time_ms'] = round(connection_time * 1000, 2)
            
            if test_conn:
                diagnostics['connection_test']['success'] = True
                diagnostics['connection_test']['db_type'] = db_type
                
                # Try a simple query
                try:
                    cursor = test_conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    diagnostics['connection_test']['query_test'] = 'success'
                    
                    # Get database version
                    if db_type == 'mysql':
                        cursor.execute("SELECT VERSION()")
                        version_result = cursor.fetchone()
                        diagnostics['connection_test']['db_version'] = version_result.get('VERSION()') if isinstance(version_result, dict) else version_result[0]
                        
                        # Check if we have access to EQEmu tables
                        cursor.execute("SHOW TABLES LIKE 'items'")
                        items_table = cursor.fetchone()
                        diagnostics['connection_test']['items_table_exists'] = bool(items_table)
                        
                        cursor.execute("SHOW TABLES LIKE 'discovered_items'")
                        discovered_table = cursor.fetchone()
                        diagnostics['connection_test']['discovered_items_table_exists'] = bool(discovered_table)
                        
                        # Get current database name
                        cursor.execute("SELECT DATABASE()")
                        db_name_result = cursor.fetchone()
                        diagnostics['connection_test']['current_database'] = db_name_result.get('DATABASE()') if isinstance(db_name_result, dict) else db_name_result[0]
                        
                    cursor.close()
                except Exception as qe:
                    diagnostics['connection_test']['query_test'] = f'failed: {str(qe)}'
                
                test_conn.close()
            else:
                diagnostics['connection_test']['success'] = False
                diagnostics['connection_test']['error'] = error or 'Unknown error'
        except Exception as e:
            diagnostics['connection_test']['success'] = False
            diagnostics['connection_test']['error'] = str(e)
        
        # Check configuration validation
        try:
            from utils.db_config_validator import validate_database_config, get_validator
            
            validation_result = validate_database_config()
            diagnostics['config_validation'] = {
                'valid': validation_result['valid'],
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings'],
                'config_comparison': validation_result['config_comparison'],
                'recommendations': validation_result['recommendations'],
                'config_sources': validation_result['config_sources']
            }
            
            # If validation failed, try to construct URL from components
            if not validation_result['valid'] and not os.environ.get('EQEMU_DATABASE_URL'):
                validator = get_validator()
                suggested_url = validator.get_connection_string_from_components()
                if suggested_url:
                    diagnostics['config_validation']['suggested_fix'] = {
                        'action': 'Set EQEMU_DATABASE_URL',
                        'value': suggested_url,
                        'reason': 'Constructed from individual components'
                    }
                    
        except Exception as e:
            diagnostics['config_validation'] = {
                'valid': False,
                'error': str(e)
            }
        
        # Check connection pooling
        try:
            from utils.content_db_manager import get_content_db_manager
            
            manager = get_content_db_manager()
            pool_status = manager.get_connection_status()
            
            diagnostics['connection_pooling'] = {
                'manager_initialized': True,
                'pool_active': pool_status.get('pool_active', False),
                'connected': pool_status.get('connected', False),
                'retry_delay': pool_status.get('retry_delay', 0),
                'database_type': pool_status.get('database_type', 'unknown')
            }
            
            # Include pool statistics if available
            if pool_status.get('pool_stats'):
                stats = pool_status['pool_stats']
                diagnostics['connection_pooling']['pool_stats'] = {
                    'total_connections': stats.get('total_connections', 0),
                    'available_connections': stats.get('available_connections', 0),
                    'in_use_connections': stats.get('in_use_connections', 0),
                    'max_connections': stats.get('max_connections', 0),
                    'pool_closed': stats.get('is_closed', False)
                }
                
                # Test pool health
                if pool_status.get('pool_active') and not stats.get('is_closed'):
                    try:
                        # Test getting a connection from the pool
                        test_start = time.time()
                        with manager.get_connection() as pooled_conn:
                            pool_time = time.time() - test_start
                            diagnostics['connection_pooling']['pool_test'] = {
                                'success': True,
                                'connection_time_ms': round(pool_time * 1000, 2)
                            }
                            
                            # Test query through pooled connection
                            cursor = pooled_conn.cursor()
                            cursor.execute("SELECT 1")
                            cursor.fetchone()
                            cursor.close()
                            diagnostics['connection_pooling']['pool_query_test'] = 'success'
                    except Exception as pe:
                        diagnostics['connection_pooling']['pool_test'] = {
                            'success': False,
                            'error': str(pe)
                        }
                else:
                    diagnostics['connection_pooling']['pool_test'] = {
                        'success': False,
                        'error': 'Pool not active or closed'
                    }
            else:
                diagnostics['connection_pooling']['pool_stats'] = 'Not available'
                
        except Exception as e:
            diagnostics['connection_pooling'] = {
                'manager_initialized': False,
                'error': str(e)
            }
        
        # Check persistent storage
        try:
            diagnostics['persistent_storage'] = {
                'data_directory': str(persistent_config.data_dir),
                'directory_exists': persistent_config.data_dir.exists() if persistent_config.data_dir else False,
                'directory_writable': os.access(persistent_config.data_dir, os.W_OK) if persistent_config.data_dir and persistent_config.data_dir.exists() else False,
                'config_file': str(persistent_config.config_file) if persistent_config.config_file else None,
                'config_file_exists': persistent_config.config_file.exists() if persistent_config.config_file else False
            }
            
            # Get raw config content
            if persistent_config.config_file and persistent_config.config_file.exists():
                try:
                    raw_config = persistent_config.load()
                    # Remove sensitive data
                    safe_config = raw_config.copy()
                    if 'production_database_url' in safe_config:
                        # Mask password in URL
                        url = safe_config['production_database_url']
                        if '@' in url:
                            parts = url.split('@')
                            if ':' in parts[0]:
                                user_parts = parts[0].split(':')
                                masked_url = f"{user_parts[0]}:****@{parts[1]}"
                                safe_config['production_database_url'] = masked_url
                    diagnostics['persistent_storage']['config_content'] = safe_config
                    diagnostics['persistent_storage']['config_keys'] = list(raw_config.keys())
                except Exception as e:
                    diagnostics['persistent_storage']['config_read_error'] = str(e)
        except Exception as e:
            diagnostics['persistent_storage']['error'] = str(e)
            
        # Check runtime configuration state
        try:
            from config import config
            diagnostics['runtime_config'] = {
                'use_production_database': config.get('use_production_database', False),
                'database_read_only': config.get('database_read_only', True),
                'database_cache_timeout': config.get('database_cache_timeout', 300),
                'cache_expiry_hours': config.get('cache_expiry_hours', 24),
                'min_scrape_interval_minutes': config.get('min_scrape_interval_minutes', 5),
                'backend_port': config.get('backend_port', 5001),
                'frontend_port': config.get('frontend_port', 3000)
            }
        except Exception as e:
            diagnostics['runtime_config']['error'] = str(e)
            
        # Check config source priority
        diagnostics['config_sources'] = {
            'priority_order': [
                '1. Persistent storage (highest priority)',
                '2. Environment variables (EQEMU_*)',
                '3. config.json file (lowest priority)'
            ],
            'current_source': diagnostics['config_checks'].get('config_source', 'unknown'),
            'persistent_available': diagnostics['config_checks'].get('persistent_config_found', False),
            'env_vars_available': bool(os.environ.get('EQEMU_DATABASE_URL')),
            'config_json_exists': os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'config.json'))
        }
        
        # Recommendations
        recommendations = []
        if not diagnostics['config_checks'].get('persistent_config_found'):
            recommendations.append("No database configuration found. Please configure through the admin panel.")
        
        if not diagnostics['connection_test'].get('success'):
            recommendations.append("Database connection failed. Check configuration and network connectivity.")
            if 'SSL' in diagnostics['connection_test'].get('error', ''):
                recommendations.append("SSL connection error detected. Try disabling SSL in database configuration.")
        
        diagnostics['recommendations'] = recommendations
        
        return jsonify(create_success_response(diagnostics))
        
    except Exception as e:
        return create_error_response(f"Diagnostics failed: {str(e)}", 500)


@admin_bp.route('/admin/database/persist-check', methods=['GET'])
@require_admin
def check_persistence():
    """
    Check persistence capabilities and diagnose storage issues.
    
    Returns:
        JSON response with persistence diagnostics
    """
    try:
        import os
        from pathlib import Path
        from utils.persistent_config import get_persistent_config
        
        persistent_config = get_persistent_config()
        
        # Comprehensive persistence check
        diagnostics = {
            'environment': {
                'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'not set'),
                'IS_PRODUCTION': os.environ.get('RAILWAY_ENVIRONMENT') == 'production',
                'EQEMU_DATABASE_URL': 'set' if os.environ.get('EQEMU_DATABASE_URL') else 'not set',
                'HOME': os.environ.get('HOME', 'not set'),
                'PWD': os.environ.get('PWD', 'not set')
            },
            'persistent_storage': {
                'configured_directory': str(persistent_config.data_dir),
                'directory_exists': persistent_config.data_dir.exists() if persistent_config.data_dir else False,
                'directory_writable': False,
                'config_file_path': str(persistent_config.config_file) if persistent_config.config_file else None,
                'config_file_exists': False,
                'config_content': None
            },
            'tested_directories': []
        }
        
        # Test write permissions
        if persistent_config.data_dir and persistent_config.data_dir.exists():
            try:
                test_file = persistent_config.data_dir / '.write_test'
                test_file.write_text('test write')
                test_file.unlink()
                diagnostics['persistent_storage']['directory_writable'] = True
            except Exception as e:
                diagnostics['persistent_storage']['write_error'] = str(e)
        
        # Check config file
        if persistent_config.config_file and persistent_config.config_file.exists():
            diagnostics['persistent_storage']['config_file_exists'] = True
            try:
                diagnostics['persistent_storage']['config_content'] = persistent_config.load()
            except Exception as e:
                diagnostics['persistent_storage']['config_read_error'] = str(e)
        
        # Test various potential persistent directories
        test_dirs = [
            '/app/data',
            '/data',
            '/persist',
            '/tmp',
            str(Path.home()),
            str(Path.home() / '.eqdata'),
            '/var/lib/eqdata'
        ]
        
        for dir_path in test_dirs:
            dir_test = {
                'path': dir_path,
                'exists': False,
                'writable': False,
                'error': None
            }
            
            try:
                path = Path(dir_path)
                dir_test['exists'] = path.exists()
                
                if path.exists():
                    # Test write
                    test_file = path / '.eqdata_write_test'
                    test_file.write_text('test')
                    test_file.unlink()
                    dir_test['writable'] = True
            except Exception as e:
                dir_test['error'] = str(e)
            
            diagnostics['tested_directories'].append(dir_test)
        
        # Recommendations
        recommendations = []
        if not diagnostics['persistent_storage']['directory_writable']:
            recommendations.append("No writable persistent directory found. Consider setting EQEMU_DATABASE_URL environment variable.")
        
        if os.environ.get('RAILWAY_ENVIRONMENT') and not any(d['writable'] for d in diagnostics['tested_directories'] if d['path'].startswith('/app')):
            recommendations.append("Railway persistent volume may not be properly mounted. Check Railway volume configuration.")
        
        diagnostics['recommendations'] = recommendations
        
        return jsonify(create_success_response(diagnostics))
        
    except Exception as e:
        return create_error_response(f"Failed to check persistence: {str(e)}", 500)


@admin_bp.route('/admin/database/resolve-mismatch', methods=['POST'])
@require_admin
def resolve_config_mismatch():
    """
    Resolve configuration mismatches by setting the selected value in all locations.
    
    Expected JSON payload:
    {
        "field": "host",
        "selected_value": "76.251.85.36"
    }
    
    Returns:
        JSON response with resolution status
    """
    try:
        import os
        from utils.persistent_config import get_persistent_config
        from utils.db_config_validator import get_validator
        
        data = request.get_json()
        logger.info(f"Resolve mismatch request: {data}")
        
        if not data or not data.get('field') or 'selected_value' not in data:
            return create_error_response("Missing field or selected_value", 400)
        
        field = data['field']
        selected_value = data['selected_value']
        
        logger.info(f"Resolving mismatch for field '{field}' with value '{selected_value}'")
        
        # Map field names to environment variables
        field_to_env = {
            'host': 'EQEMU_DATABASE_HOST',
            'port': 'EQEMU_DATABASE_PORT',
            'database': 'EQEMU_DATABASE_NAME',
            'username': 'EQEMU_DATABASE_USER',
            'password': 'EQEMU_DATABASE_PW',
            'database_type': 'EQEMU_DATABASE_TYPE',
            'ssl': 'EQEMU_DATABASE_SSL'
        }
        
        env_var = field_to_env.get(field)
        if not env_var:
            return create_error_response(f"Unknown field: {field}", 400)
        
        # Update environment variable (for current process)
        # For empty string values, we need to handle them specially
        if selected_value == '':
            # Don't set empty values for required fields
            if field in ['host', 'database', 'username']:
                logger.warning(f"Cannot set {field} to empty value - it's a required field")
                return create_error_response(f"Cannot set {field} to empty - it's a required field for database connection", 400)
            os.environ[env_var] = ''
        else:
            os.environ[env_var] = str(selected_value)
        
        # Get current validator and construct new URL
        validator = get_validator()
        
        # Log current environment state for debugging
        logger.info(f"Current environment state before URL construction:")
        logger.info(f"  EQEMU_DATABASE_HOST: {os.environ.get('EQEMU_DATABASE_HOST', 'NOT SET')}")
        logger.info(f"  EQEMU_DATABASE_PORT: {os.environ.get('EQEMU_DATABASE_PORT', 'NOT SET')}")
        logger.info(f"  EQEMU_DATABASE_NAME: {os.environ.get('EQEMU_DATABASE_NAME', 'NOT SET')}")
        logger.info(f"  EQEMU_DATABASE_USER: {os.environ.get('EQEMU_DATABASE_USER', 'NOT SET')}")
        logger.info(f"  EQEMU_DATABASE_TYPE: {os.environ.get('EQEMU_DATABASE_TYPE', 'NOT SET')}")
        
        new_url = validator.get_connection_string_from_components()
        
        # Log for debugging
        logger.info(f"After setting {env_var} to '{selected_value}', new_url construction: {new_url}")
        
        # Update persistent storage regardless of whether we can construct a URL
        persistent_config = get_persistent_config()
        db_config = persistent_config.get_database_config() or {}
        
        # Update the URL if we have one
        if new_url:
            os.environ['EQEMU_DATABASE_URL'] = new_url
            db_config['production_database_url'] = new_url
        else:
            # Log why we couldn't construct URL
            logger.warning(f"Cannot construct URL - missing required components")
            logger.info(f"Required: host={bool(os.environ.get('EQEMU_DATABASE_HOST'))}, "
                       f"database={bool(os.environ.get('EQEMU_DATABASE_NAME'))}, "
                       f"username={bool(os.environ.get('EQEMU_DATABASE_USER'))}")
        
        # Update individual fields in persistent storage to match
        if field == 'host':
            db_config['database_host'] = selected_value
        elif field == 'port':
            db_config['database_port'] = int(selected_value) if selected_value else 3306
        elif field == 'database':
            db_config['database_name'] = selected_value
        elif field == 'username':
            db_config['database_username'] = selected_value
        elif field == 'password':
            db_config['database_password'] = selected_value
        elif field == 'database_type':
            db_config['database_type'] = selected_value
        elif field == 'ssl':
            db_config['database_ssl'] = selected_value.lower() == 'true'
        
        # Save to persistent storage
        # Extract the required parameters for save_database_config
        db_url = db_config.get('production_database_url', '')
        db_type = db_config.get('database_type', 'mysql')
        use_ssl = db_config.get('database_ssl', False)
        db_name = db_config.get('database_name', '')
        db_password = db_config.get('database_password', '')
        db_port = str(db_config.get('database_port', '3306'))
        
        persistent_config.save_database_config(
            db_url=db_url,
            db_type=db_type,
            use_ssl=use_ssl,
            db_name=db_name,
            db_password=db_password,
            db_port=db_port
        )
        
        # Force reload of database configuration
        from flask import current_app
        if hasattr(current_app, 'db_config_manager'):
            current_app.db_config_manager.invalidate()
            logger.info(f"Database configuration updated: {field} = {selected_value}")
        
        # Run validation again to confirm resolution
        new_validation = validator.validate_config()
        
        if new_url:
            return jsonify(create_success_response({
                'message': f'Configuration mismatch resolved for {field}',
                'field': field,
                'value': selected_value,
                'new_url': new_url,
                'validation_result': new_validation
            }))
        else:
            return jsonify(create_success_response({
                'message': f'Configuration value saved for {field}, but database URL could not be constructed due to missing required fields',
                'field': field,
                'value': selected_value,
                'new_url': None,
                'validation_result': new_validation,
                'warning': 'Database connection requires host, database name, and username to be set'
            }))
            
    except Exception as e:
        logger.error(f"Error resolving mismatch: {str(e)}")
        return create_error_response(f"Failed to resolve mismatch: {str(e)}", 500)


@admin_bp.route('/admin/database/reconnect', methods=['POST'])
@require_admin
def reconnect_database():
    """
    Force database reconnection by invalidating the connection pool.
    
    Returns:
        JSON response with reconnection status
    """
    try:
        from flask import current_app
        from utils.db_connection_pool import close_connection_pool
        from utils.persistent_config import get_persistent_config
        
        # Close existing connection pool to force reconnection
        close_connection_pool()
        
        # Force reload of database configuration from persistent storage
        if hasattr(current_app, 'db_config_manager'):
            current_app.db_config_manager.invalidate()
            logger.info("Database configuration cache invalidated for reconnection")
        
        # Also check persistent config for database settings
        persistent_config = get_persistent_config()
        db_config = persistent_config.get_database_config()
        
        if db_config:
            logger.info("Found database config in persistent storage, reloading...")
            # The config manager should pick this up on next access
        
        # Reset connection state without blocking operations
        from utils.content_db_manager import get_content_db_manager
        manager = get_content_db_manager()
        
        # Reset retry delay to allow immediate reconnection attempt
        with manager._lock:
            manager._connect_retry_delay = 1
            manager._connection_healthy = False
            manager._last_connect_attempt = 0
            logger.info("Database connection state reset for reconnection")
        
        return jsonify(create_success_response({
            'message': 'Database reconnection triggered (non-blocking)',
            'status': 'reset'
        }))
            
    except Exception as e:
        logger.error(f"Reconnection error: {str(e)}")
        return create_error_response(f"Reconnection failed: {str(e)}", 500)


# System monitoring data storage
# Initialize system metrics with loaded timeline data
# Load database stats from persistent storage
database_stats = query_persistence.load_metrics()
database_stats['timeline'] = query_persistence.load_timeline()

system_metrics = {
    'response_times': deque(maxlen=1000),  # Store last 1000 response times
    'endpoint_stats': defaultdict(lambda: {
        'total_calls': 0,
        'total_time': 0,
        'errors': 0,
        'last_called': None
    }),
    'server_start_time': time.time(),
    'error_log': deque(maxlen=100),  # Store last 100 errors
    'database_stats': database_stats
}

# Don't start periodic saves immediately - they will be started when app is fully initialized
# periodic_save_timeline()

# Periodic save for query tracking data
def periodic_save_query_tracking():
    """Save query tracking data periodically - DISABLED."""
    logger.info("⚠️ Periodic query tracking save DISABLED to debug hanging issue")
    # TEMPORARILY DISABLED: Background timers may be causing hanging
    
    # def save_data():
    #     try:
    #         # Save metrics (excluding timeline which is handled separately)
    #         metrics_to_save = {
    #             'total_queries': system_metrics['database_stats']['total_queries'],
    #             'query_times': system_metrics['database_stats']['query_times'],
    #             'slow_queries': system_metrics['database_stats']['slow_queries'],
    #             'query_types': system_metrics['database_stats']['query_types'],
    #             'tables_accessed': system_metrics['database_stats']['tables_accessed'],
    #             'table_sources': system_metrics['database_stats']['table_sources']
    #         }
    #         
    #         query_persistence.save_metrics(metrics_to_save)
    #         query_persistence.save_timeline(system_metrics['database_stats']['timeline'])
    #         
    #         # Schedule next save
    #         threading.Timer(300, save_data).start()  # Save every 5 minutes
    #     except Exception as e:
    #         logger.error(f"Error saving query tracking data: {e}")
    #         # Still schedule next save even if this one failed
    #         threading.Timer(300, save_data).start()
    # 
    # # Start the periodic save (delay initial save by 1 minute)
    # threading.Timer(60, save_data).start()

# Don't start periodic query tracking save immediately 
# periodic_save_query_tracking()

# Save query tracking data on shutdown
def save_query_tracking_on_shutdown():
    """Save query tracking data when the application shuts down."""
    try:
        metrics_to_save = {
            'total_queries': system_metrics['database_stats']['total_queries'],
            'query_times': system_metrics['database_stats']['query_times'],
            'slow_queries': system_metrics['database_stats']['slow_queries'],
            'query_types': system_metrics['database_stats']['query_types'],
            'tables_accessed': system_metrics['database_stats']['tables_accessed'],
            'table_sources': system_metrics['database_stats']['table_sources']
        }
        
        query_persistence.save_metrics(metrics_to_save)
        query_persistence.save_timeline(system_metrics['database_stats']['timeline'])
        try:
            logger.info("Query tracking data saved on shutdown")
        except:
            pass  # Logger may be closed during shutdown
    except Exception as e:
        try:
            logger.error(f"Error saving query tracking data on shutdown: {e}")
        except:
            pass  # Logger may be closed during shutdown

# Register shutdown handler
atexit.register(save_query_tracking_on_shutdown)

# Daily cleanup of old query tracking data
def periodic_cleanup_query_tracking():
    """Clean up old query tracking data periodically - DISABLED."""
    logger.info("⚠️ Periodic query tracking cleanup DISABLED to debug hanging issue")
    # TEMPORARILY DISABLED: Background timers may be causing hanging
    
    # def cleanup():
    #     try:
    #         query_persistence.cleanup_old_data()
    #         logger.info("Query tracking data cleanup completed")
    #         
    #         # Schedule next cleanup (24 hours)
    #         threading.Timer(86400, cleanup).start()
    #     except Exception as e:
    #         logger.error(f"Error during query tracking cleanup: {e}")
    #         # Still schedule next cleanup even if this one failed
    #         threading.Timer(86400, cleanup).start()
    # 
    # # Start the first cleanup after 30 minutes
    # threading.Timer(1800, cleanup).start()

# Don't start periodic cleanup immediately
# periodic_cleanup_query_tracking()

# Function to start all periodic tasks (should be called after app initialization)
def start_periodic_tasks():
    """Start all periodic tasks."""
    periodic_save_timeline()
    periodic_save_query_tracking()  
    periodic_cleanup_query_tracking()

# Save timeline data on shutdown
def save_timeline_on_shutdown():
    """Save timeline data when the application shuts down."""
    try:
        db_stats = system_metrics['database_stats']
        save_timeline_data(db_stats['timeline'])
        try:
            logger.info("Timeline data saved on shutdown")
        except:
            pass  # Logger may be closed during shutdown
    except Exception as e:
        try:
            logger.error(f"Failed to save timeline data on shutdown: {e}")
        except:
            pass  # Logger may be closed during shutdown

atexit.register(save_timeline_on_shutdown)


@admin_bp.route('/admin/system/metrics', methods=['GET'])
@require_admin
def get_system_metrics():
    """
    Get comprehensive system metrics including CPU, memory, and performance data.
    
    Returns:
        JSON response with system metrics
    """
    try:
        # Get system resource usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # System-wide metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate uptime
        uptime_seconds = time.time() - system_metrics['server_start_time']
        
        # Calculate average response time
        response_times = list(system_metrics['response_times'])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate error rate
        total_requests = sum(stats['total_calls'] for stats in system_metrics['endpoint_stats'].values())
        total_errors = sum(stats['errors'] for stats in system_metrics['endpoint_stats'].values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Get cache statistics from main app
        try:
            from app import spells_cache, spell_details_cache, cache_timestamp
            cache_stats = {
                'cached_classes': len(spells_cache),
                'cached_spell_details': len(spell_details_cache),
                'total_spells': sum(len(spells) for spells in spells_cache.values()),
                'cache_age_hours': {
                    class_name: (time.time() - timestamp) / 3600
                    for class_name, timestamp in cache_timestamp.items()
                }
            }
        except ImportError:
            cache_stats = {
                'cached_classes': 0,
                'cached_spell_details': 0,
                'total_spells': 0,
                'cache_age_hours': {}
            }
        
        return jsonify(create_success_response({
            'system': {
                'uptime_seconds': uptime_seconds,
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'percent': memory.percent,
                    'available': memory.available,
                    'process_rss': memory_info.rss,
                    'process_vms': memory_info.vms
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            'performance': {
                'avg_response_time': round(avg_response_time, 2),
                'total_requests': total_requests,
                'error_rate': round(error_rate, 2),
                'error_count': total_errors,
                'response_time_history': response_times[-20:] if response_times else []  # Last 20 values
            },
            'cache': cache_stats,
            'database': {
                'total_queries': system_metrics['database_stats']['total_queries'],
                'avg_query_time': sum(system_metrics['database_stats']['query_times']) / len(system_metrics['database_stats']['query_times']) if system_metrics['database_stats']['query_times'] else 0,
                'query_types': dict(system_metrics['database_stats']['query_types']),
                'tables_accessed': dict(system_metrics['database_stats']['tables_accessed']),
                'slow_queries_count': len(system_metrics['database_stats']['slow_queries']),
                'recent_slow_queries': list(system_metrics['database_stats']['slow_queries'])[-5:],  # Last 5 slow queries
                'timeline': format_query_timeline(system_metrics['database_stats']['timeline'])
            },
            'health_score': calculate_health_score(cpu_percent, memory.percent, error_rate, avg_response_time)
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to get system metrics: {str(e)}", 500)


@admin_bp.route('/admin/system/endpoints', methods=['GET'])
@require_admin
def get_endpoint_metrics():
    """
    Get detailed metrics for all API endpoints.
    
    Returns:
        JSON response with endpoint performance data
    """
    try:
        endpoints = []
        
        for endpoint, stats in system_metrics['endpoint_stats'].items():
            avg_time = (stats['total_time'] / stats['total_calls']) if stats['total_calls'] > 0 else 0
            success_rate = ((stats['total_calls'] - stats['errors']) / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 100
            
            # Determine endpoint status
            if stats['errors'] > 5 or success_rate < 90:
                status = 'critical'
            elif stats['errors'] > 2 or success_rate < 95:
                status = 'warning'
            else:
                status = 'healthy'
            
            # Calculate calls per hour
            if stats['last_called']:
                hours_since_start = (time.time() - system_metrics['server_start_time']) / 3600
                calls_per_hour = stats['total_calls'] / hours_since_start if hours_since_start > 0 else 0
            else:
                calls_per_hour = 0
            
            endpoints.append({
                'method': endpoint.split()[0],
                'path': endpoint.split()[1] if len(endpoint.split()) > 1 else endpoint,
                'avgTime': round(avg_time, 0),
                'callsPerHour': round(calls_per_hour, 0),
                'successRate': round(success_rate, 1),
                'status': status,
                'totalCalls': stats['total_calls'],
                'errors': stats['errors'],
                'lastCalled': stats['last_called']
            })
        
        # Sort by total calls descending
        endpoints.sort(key=lambda x: x['totalCalls'], reverse=True)
        
        # Add some default endpoints if none exist yet
        if not endpoints:
            endpoints = [
                {
                    'method': 'GET',
                    'path': '/api/classes',
                    'avgTime': 45,
                    'callsPerHour': 0,
                    'successRate': 100.0,
                    'status': 'healthy',
                    'totalCalls': 0,
                    'errors': 0,
                    'lastCalled': None
                },
                {
                    'method': 'GET',
                    'path': '/api/spells/:class',
                    'avgTime': 120,
                    'callsPerHour': 0,
                    'successRate': 100.0,
                    'status': 'healthy',
                    'totalCalls': 0,
                    'errors': 0,
                    'lastCalled': None
                }
            ]
        
        return jsonify(create_success_response({
            'endpoints': endpoints
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to get endpoint metrics: {str(e)}", 500)


@admin_bp.route('/admin/system/logs', methods=['GET'])
@require_admin
def get_system_logs():
    """
    Get system logs with filtering options.
    
    Query parameters:
        level: Filter by log level (all, error, warning, info)
        limit: Number of logs to return (default: 50, max: 500)
    
    Returns:
        JSON response with system logs
    """
    try:
        level = request.args.get('level', 'all')
        limit = min(int(request.args.get('limit', 50)), 500)
        
        logs = []
        
        # Read from actual log files if available
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'backend_run.log')
        
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as f:
                    # Read last N lines efficiently
                    lines = deque(f, maxlen=limit * 2)  # Read more to account for filtering
                    
                for line in lines:
                    try:
                        # Parse log line (assuming standard format: timestamp - level - message)
                        if ' - ' in line:
                            parts = line.strip().split(' - ', 2)
                            if len(parts) >= 3:
                                timestamp_str = parts[0]
                                log_level = parts[1].lower()
                                message = parts[2]
                                
                                # Filter by level if specified
                                if level != 'all' and log_level != level:
                                    continue
                                
                                # Determine context from message and extract endpoint details
                                context = None
                                endpoint = None
                                status_code = None
                                response_time = None
                                error_details = None
                                stack_trace = None
                                
                                # Parse endpoint failures
                                if 'failed endpoint attempt' in message.lower() or 'endpoint accessed' in message.lower():
                                    context = 'Endpoint monitoring'
                                    # Extract endpoint from message
                                    import re
                                    endpoint_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', message)
                                    if endpoint_match:
                                        endpoint = f"{endpoint_match.group(1)} {endpoint_match.group(2)}"
                                    
                                    # Extract status code
                                    status_match = re.search(r'(\d{3})\s+(status|error|response)', message.lower())
                                    if status_match:
                                        status_code = int(status_match.group(1))
                                    
                                    # Extract response time
                                    time_match = re.search(r'(\d+)ms', message)
                                    if time_match:
                                        response_time = int(time_match.group(1))
                                        
                                elif 'api request' in message.lower() or 'api response' in message.lower():
                                    context = 'API activity'
                                elif 'scraping' in message.lower():
                                    context = 'Scraping operation'
                                elif 'cache' in message.lower():
                                    context = 'Cache operation'
                                elif 'database' in message.lower() or 'db' in message.lower():
                                    context = 'Database operation'
                                elif 'oauth' in message.lower() or 'auth' in message.lower():
                                    context = 'Authentication'
                                elif 'disabled' in message.lower() and 'spell' in message.lower():
                                    context = 'Disabled endpoints'
                                
                                # For error level logs, try to extract additional details
                                if log_level == 'error':
                                    if 'traceback' in message.lower() or 'exception' in message.lower():
                                        # Extract error details for exceptions
                                        if ':' in message:
                                            error_details = message.split(':', 1)[1].strip()
                                
                                log_entry = {
                                    'id': len(logs) + 1,
                                    'timestamp': timestamp_str,
                                    'level': log_level,
                                    'message': message,
                                    'context': context
                                }
                                
                                # Add endpoint details if available
                                if endpoint:
                                    log_entry['endpoint'] = endpoint
                                if status_code:
                                    log_entry['statusCode'] = status_code
                                if response_time:
                                    log_entry['responseTime'] = response_time
                                if error_details:
                                    log_entry['errorDetails'] = error_details
                                if stack_trace:
                                    log_entry['stackTrace'] = stack_trace
                                    
                                logs.append(log_entry)
                    except Exception:
                        # Skip malformed log lines
                        continue
                        
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
        
        # If no logs from file, use in-memory error log
        if not logs and system_metrics['error_log']:
            for i, error in enumerate(system_metrics['error_log']):
                if level == 'all' or level == 'error':
                    log_entry = {
                        'id': i + 1,
                        'timestamp': error.get('timestamp', datetime.now().isoformat()),
                        'level': 'error',
                        'message': error.get('message', 'Unknown error'),
                        'context': error.get('context')
                    }
                    
                    # Add endpoint details if available
                    if error.get('endpoint'):
                        log_entry['endpoint'] = error.get('endpoint')
                    if error.get('status_code'):
                        log_entry['statusCode'] = error.get('status_code')
                    if error.get('response_time'):
                        log_entry['responseTime'] = error.get('response_time')
                    if error.get('error_details'):
                        log_entry['errorDetails'] = error.get('error_details')
                    if error.get('stack_trace'):
                        log_entry['stackTrace'] = error.get('stack_trace')
                        
                    logs.append(log_entry)
        
        # If still no logs, provide some sample logs
        if not logs:
            logs = [
                {
                    'id': 1,
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': 'System monitoring started',
                    'context': 'System startup'
                }
            ]
        
        # Sort by timestamp descending and limit
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        logs = logs[:limit]
        
        return jsonify(create_success_response({
            'logs': logs,
            'total': len(logs),
            'level_filter': level
        }))
        
    except Exception as e:
        return create_error_response(f"Failed to get system logs: {str(e)}", 500)


def calculate_health_score(cpu_percent, memory_percent, error_rate, avg_response_time):
    """Calculate overall system health score (0-100)."""
    score = 100
    
    # CPU penalty
    if cpu_percent > 80:
        score -= 20
    elif cpu_percent > 60:
        score -= 10
    
    # Memory penalty
    if memory_percent > 85:
        score -= 20
    elif memory_percent > 70:
        score -= 10
    
    # Error rate penalty
    if error_rate > 5:
        score -= 30
    elif error_rate > 1:
        score -= 15
    
    # Response time penalty
    if avg_response_time > 500:
        score -= 20
    elif avg_response_time > 200:
        score -= 10
    
    return max(0, score)


def track_endpoint_metric(endpoint, response_time, is_error=False, status_code=None, error_details=None, stack_trace=None):
    """Track metrics for an endpoint (called by middleware)."""
    try:
        # Initialize endpoint stats if not exists
        if endpoint not in system_metrics['endpoint_stats']:
            system_metrics['endpoint_stats'][endpoint] = {
                'total_calls': 0,
                'total_time': 0,
                'errors': 0,
                'last_called': None
            }
        
        stats = system_metrics['endpoint_stats'][endpoint]
        stats['total_calls'] += 1
        stats['total_time'] += response_time
        stats['last_called'] = time.time()
        
        if is_error:
            stats['errors'] += 1
            
            # Log detailed endpoint failure information
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': f'Endpoint failure: {endpoint} - Status: {status_code} - {response_time}ms',
                'context': 'Endpoint monitoring',
                'endpoint': endpoint,
                'status_code': status_code,
                'response_time': response_time,
                'error_details': error_details,
                'stack_trace': stack_trace
            }
            
            # Add to error log for system logs display
            system_metrics['error_log'].append(error_entry)
            
            # Keep only last 100 errors to prevent memory issues
            if len(system_metrics['error_log']) > 100:
                system_metrics['error_log'] = system_metrics['error_log'][-100:]
                
            # Log to application logger as well
            logger.error(f'Endpoint failure: {endpoint} - Status: {status_code} - Time: {response_time}ms - Error: {error_details}')
        
        # Add to response time history
        system_metrics['response_times'].append(response_time)
        
    except Exception as e:
        # Don't let metrics tracking break the app
        logger.error(f'Error tracking endpoint metric: {e}')
        pass


def log_system_error(message, context=None):
    """Log a system error for monitoring."""
    system_metrics['error_log'].append({
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'context': context
    })


def format_query_timeline(timeline_data, time_scale='1h'):
    """Format timeline data for the requested time scale."""
    if not timeline_data:
        return []
    
    # Convert deque to list for processing
    all_entries = list(timeline_data)
    
    # For now, return the raw hourly data
    # Frontend will aggregate as needed based on selected time scale
    formatted_data = []
    for entry in all_entries:
        formatted_entry = {
            'timestamp': entry['timestamp'],
            'total': entry['total_queries'],
            'tables': dict(entry['tables'])  # Convert defaultdict to regular dict
        }
        formatted_data.append(formatted_entry)
    
    return formatted_data[-168:]  # Return up to 7 days of hourly data


def update_query_timeline(table_name=None):
    """Update the timeline data for query tracking."""
    db_stats = system_metrics['database_stats']
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    # Get the latest timeline entry or create a new one
    timeline_updated = False
    if not db_stats['timeline'] or db_stats['timeline'][-1]['timestamp'] != current_hour.isoformat():
        # Create new hourly entry
        new_entry = {
            'timestamp': current_hour.isoformat(),
            'total_queries': 0,
            'tables': defaultdict(int)
        }
        db_stats['timeline'].append(new_entry)
        timeline_updated = True
    
    # Update the current hour's data
    current_entry = db_stats['timeline'][-1]
    current_entry['total_queries'] += 1
    
    if table_name:
        current_entry['tables'][table_name.lower()] += 1
    
    # Only save when a new hour starts (reduces disk I/O)
    if timeline_updated:
        save_timeline_data(db_stats['timeline'])


def track_database_query(query, execution_time, query_type=None, table_name=None, source_endpoint=None):
    """Track database query metrics."""
    db_stats = system_metrics['database_stats']
    
    # Track total queries
    db_stats['total_queries'] += 1
    
    # Track query time
    db_stats['query_times'].append(execution_time)
    
    # Track slow queries (> 100ms)
    if execution_time > 100:
        db_stats['slow_queries'].append({
            'query': query[:200] if len(query) > 200 else query,  # Truncate long queries
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'type': query_type,
            'table': table_name,
            'source_endpoint': source_endpoint
        })
    
    # Detect query type if not provided
    if not query_type:
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            query_type = 'SELECT'
        elif query_upper.startswith('INSERT'):
            query_type = 'INSERT'
        elif query_upper.startswith('UPDATE'):
            query_type = 'UPDATE'
        elif query_upper.startswith('DELETE'):
            query_type = 'DELETE'
        else:
            query_type = 'OTHER'
    
    # Track query type
    db_stats['query_types'][query_type] += 1
    
    # Detect table name if not provided
    if not table_name and query_type in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']:
        # Simple table name extraction (works for basic queries)
        query_upper = query.upper()
        if 'FROM' in query_upper:
            # Extract table name after FROM
            parts = query_upper.split('FROM')
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                table_name = table_part.strip('`"\' ')
        elif 'INTO' in query_upper:
            # Extract table name after INTO
            parts = query_upper.split('INTO')
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                table_name = table_part.strip('`"\' ')
        elif 'UPDATE' in query_upper:
            # Extract table name after UPDATE
            parts = query_upper.split('UPDATE')
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0]
                table_name = table_part.strip('`"\' ')
    
    # Detect source endpoint if not provided
    if not source_endpoint:
        # Try to get the current request context
        try:
            from flask import request
            if request:
                source_endpoint = f"{request.method} {request.path}"
        except:
            source_endpoint = "Unknown"
    
    # Track table access
    if table_name:
        table_key = table_name.lower()
        db_stats['tables_accessed'][table_key] += 1
        
        # Track which endpoint accessed this table
        if source_endpoint:
            db_stats['table_sources'][table_key][source_endpoint] += 1
    
    # Update timeline data
    update_query_timeline(table_name)
    
    # Save query tracking data every 100 queries to avoid too much I/O
    if db_stats['total_queries'] % 100 == 0:
        try:
            metrics_to_save = {
                'total_queries': db_stats['total_queries'],
                'query_times': db_stats['query_times'],
                'slow_queries': db_stats['slow_queries'],
                'query_types': db_stats['query_types'],
                'tables_accessed': db_stats['tables_accessed'],
                'table_sources': db_stats['table_sources']
            }
            query_persistence.save_metrics(metrics_to_save)
        except Exception as e:
            logger.error(f"Error saving query tracking data: {e}")


@admin_bp.route('/admin/database/table-sources/<table_name>', methods=['GET'])
@require_admin
def get_table_sources(table_name):
    """
    Get the breakdown of which endpoints/sources are accessing a specific table.
    
    Args:
        table_name: The name of the table to get sources for
        
    Returns:
        JSON response with source breakdown
    """
    try:
        db_stats = system_metrics['database_stats']
        table_key = table_name.lower()
        
        # Get the source breakdown for this table
        sources = dict(db_stats['table_sources'].get(table_key, {}))
        total_queries = db_stats['tables_accessed'].get(table_key, 0)
        
        # Sort sources by query count (descending)
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        
        # Format the response
        source_breakdown = []
        for endpoint, count in sorted_sources:
            percentage = (count / total_queries * 100) if total_queries > 0 else 0
            source_breakdown.append({
                'endpoint': endpoint,
                'query_count': count,
                'percentage': round(percentage, 1)
            })
        
        return jsonify(create_success_response({
            'table_name': table_name,
            'total_queries': total_queries,
            'sources': source_breakdown
        }, f"Source breakdown for table '{table_name}' retrieved successfully"))
        
    except Exception as e:
        return create_error_response(f"Failed to get table sources: {str(e)}", 500)


@admin_bp.route('/admin/debug/avatars', methods=['GET'])
@require_admin
def debug_avatars():
    """Debug endpoint to check avatar URLs."""
    try:
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, email, avatar_url, avatar_class 
                FROM users 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            users = []
            for row in cursor.fetchall():
                user_data = {
                    'id': row[0],
                    'email': row[1],
                    'avatar_url': row[2],
                    'avatar_class': row[3],
                    'has_google_avatar': bool(row[2] and not row[3]),
                    'has_class_avatar': bool(row[3])
                }
                users.append(user_data)
            
            return create_success_response({
                'users': users,
                'total': len(users)
            })
            
    except Exception as e:
        logger.error(f"Error in debug avatars endpoint: {str(e)}")
        return create_error_response(f"Failed to get avatar debug info: {str(e)}", 500)


@admin_bp.route('/api/avatar-proxy/<int:user_id>', methods=['GET'])
@require_auth
def proxy_avatar(user_id):
    """Proxy Google avatars to avoid CORS issues."""
    try:
        conn = get_db_connection()
        if not conn:
            return create_error_response("Database connection failed", 500)
        
        # Get the user's avatar URL
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT avatar_url, avatar_class 
                FROM users 
                WHERE id = %s AND is_active = TRUE
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return create_error_response("User not found", 404)
            
            avatar_url = result[0]
            avatar_class = result[1]
            
            # If user has a class avatar, they shouldn't be using this endpoint
            if avatar_class:
                return create_error_response("User has class avatar", 400)
            
            # If no avatar URL, return 404
            if not avatar_url:
                return create_error_response("No avatar URL", 404)
            
            # Fetch the avatar from Google
            import requests
            response = requests.get(avatar_url, headers={'User-Agent': 'EQDataScraper/1.0'})
            
            if response.status_code == 200:
                from flask import Response
                return Response(
                    response.content,
                    mimetype=response.headers.get('content-type', 'image/jpeg'),
                    headers={
                        'Cache-Control': 'public, max-age=86400',  # Cache for 1 day
                        'Access-Control-Allow-Origin': '*'
                    }
                )
            else:
                return create_error_response(f"Failed to fetch avatar: {response.status_code}", 500)
                
    except Exception as e:
        logger.error(f"Error in avatar proxy: {str(e)}")
        return create_error_response(f"Failed to proxy avatar: {str(e)}", 500)