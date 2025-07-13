"""
Activity logging model for tracking user actions and system events.
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

class ActivityLog:
    """Activity log model for tracking user actions and system events."""
    
    # Common action types
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_TOKEN_REFRESH = 'token_refresh'
    ACTION_CACHE_REFRESH = 'cache_refresh'
    ACTION_CACHE_CLEAR = 'cache_clear'
    ACTION_SCRAPE_START = 'scrape_start'
    ACTION_SCRAPE_COMPLETE = 'scrape_complete'
    ACTION_SCRAPE_ERROR = 'scrape_error'
    ACTION_SPELL_VIEW = 'spell_view'
    ACTION_SPELL_SEARCH = 'spell_search'
    ACTION_USER_UPDATE = 'user_update'
    ACTION_USER_CREATE = 'user_create'
    ACTION_ADMIN_ACTION = 'admin_action'
    ACTION_SYSTEM_ERROR = 'system_error'
    ACTION_API_ERROR = 'api_error'
    
    # Resource types
    RESOURCE_USER = 'user'
    RESOURCE_CACHE = 'cache'
    RESOURCE_SPELL = 'spell'
    RESOURCE_CLASS = 'class'
    RESOURCE_SESSION = 'session'
    RESOURCE_SYSTEM = 'system'
    
    def __init__(self, connection):
        # Use raw connection for auth database (no query tracking)
        self.conn = connection
    
    def _get_cursor(self):
        """Get a cursor, trying RealDictCursor first, falling back to regular cursor."""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            return cursor, True  # True indicates dict cursor
        except TypeError:
            # Connection doesn't support cursor_factory
            cursor = self.conn.cursor()
            return cursor, False  # False indicates regular cursor
    
    def _row_to_dict(self, row, columns, use_dict_cursor):
        """Convert row to dict, handling both cursor types."""
        if not row:
            return None
        if use_dict_cursor:
            return dict(row)
        else:
            return dict(zip(columns, row))
    
    def log_activity(self, action: str, user_id: Optional[int] = None,
                    resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Log a user activity or system event."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    INSERT INTO activity_logs 
                    (user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, action, resource_type, resource_id, 
                             details, ip_address, user_agent, created_at
                """, (
                    user_id, action, resource_type, resource_id,
                    Json(details) if details else None,
                    ip_address, user_agent
                ))
                
                row = cursor.fetchone()
                columns = ['id', 'user_id', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'user_agent', 'created_at']
                activity = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return activity
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to log activity: {str(e)}")
    
    def get_recent_activities(self, limit: int = 50, offset: int = 0,
                            user_id: Optional[int] = None, action: Optional[str] = None,
                            resource_type: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get recent activities with optional filtering."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                # Build query with filters
                query = """
                    SELECT 
                        a.id, a.user_id, a.action, a.resource_type, a.resource_id,
                        a.details, a.ip_address, a.user_agent, a.created_at,
                        u.email as user_email, u.first_name, u.last_name,
                        u.display_name, u.anonymous_mode
                    FROM activity_logs a
                    LEFT JOIN users u ON a.user_id = u.id
                    WHERE 1=1
                """
                params = []
                
                if user_id is not None:
                    query += " AND a.user_id = %s"
                    params.append(user_id)
                
                if action:
                    query += " AND a.action = %s"
                    params.append(action)
                
                if resource_type:
                    query += " AND a.resource_type = %s"
                    params.append(resource_type)
                
                if start_date:
                    query += " AND a.created_at >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND a.created_at <= %s"
                    params.append(end_date)
                
                query += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                activities = []
                columns = ['id', 'user_id', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'user_agent', 'created_at', 'user_email', 'first_name', 'last_name', 'display_name', 'anonymous_mode']
                
                for row in cursor.fetchall():
                    activity = self._row_to_dict(row, columns, use_dict_cursor)
                    # Format user info based on anonymous mode
                    if activity.get('anonymous_mode'):
                        activity['user_display'] = activity.get('display_name', 'Anonymous User')
                    else:
                        if activity.get('first_name') or activity.get('last_name'):
                            activity['user_display'] = f"{activity.get('first_name', '')} {activity.get('last_name', '')}".strip()
                        else:
                            activity['user_display'] = activity.get('email', 'Unknown User')
                    
                    activities.append(activity)
                
                return activities
        except psycopg2.Error as e:
            raise Exception(f"Failed to get recent activities: {str(e)}")
    
    def get_activity_count(self, user_id: Optional[int] = None, action: Optional[str] = None,
                          resource_type: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> int:
        """Get count of activities with optional filtering."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                query = "SELECT COUNT(*) as count FROM activity_logs WHERE 1=1"
                params = []
                
                if user_id is not None:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                if action:
                    query += " AND action = %s"
                    params.append(action)
                
                if resource_type:
                    query += " AND resource_type = %s"
                    params.append(resource_type)
                
                if start_date:
                    query += " AND created_at >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND created_at <= %s"
                    params.append(end_date)
                
                cursor.execute(query, params)
                return cursor.fetchone()['count']
        except psycopg2.Error as e:
            raise Exception(f"Failed to get activity count: {str(e)}")
    
    def get_activity_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get activity statistics for the past N hours."""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                # Get action counts
                cursor.execute("""
                    SELECT action, COUNT(*) as count
                    FROM activity_logs
                    WHERE created_at >= %s
                    GROUP BY action
                    ORDER BY count DESC
                """, (start_time,))
                
                action_counts = {row['action']: row['count'] for row in cursor.fetchall()}
                
                # Get unique users
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as unique_users
                    FROM activity_logs
                    WHERE created_at >= %s AND user_id IS NOT NULL
                """, (start_time,))
                
                unique_users = cursor.fetchone()['unique_users']
                
                # Get total activities
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM activity_logs
                    WHERE created_at >= %s
                """, (start_time,))
                
                total_activities = cursor.fetchone()['total']
                
                # Get most active users
                cursor.execute("""
                    SELECT 
                        a.user_id, COUNT(*) as activity_count,
                        u.email, u.first_name, u.last_name, 
                        u.display_name, u.anonymous_mode
                    FROM activity_logs a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.created_at >= %s AND a.user_id IS NOT NULL
                    GROUP BY a.user_id, u.email, u.first_name, u.last_name, 
                             u.display_name, u.anonymous_mode
                    ORDER BY activity_count DESC
                    LIMIT 10
                """, (start_time,))
                
                most_active_users = []
                for row in cursor.fetchall():
                    user_data = dict(row)
                    if user_data.get('anonymous_mode'):
                        user_data['display_name'] = user_data.get('display_name', 'Anonymous User')
                    else:
                        if user_data.get('first_name') or user_data.get('last_name'):
                            user_data['display_name'] = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
                        else:
                            user_data['display_name'] = user_data.get('email', 'Unknown User')
                    most_active_users.append(user_data)
                
                return {
                    'time_period_hours': hours,
                    'total_activities': total_activities,
                    'unique_users': unique_users,
                    'action_counts': action_counts,
                    'most_active_users': most_active_users
                }
        except psycopg2.Error as e:
            raise Exception(f"Failed to get activity stats: {str(e)}")
    
    def cleanup_old_activities(self, days: int = 90) -> int:
        """Clean up activities older than N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM activity_logs
                    WHERE created_at < %s
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                self.conn.commit()
                return deleted_count
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to cleanup old activities: {str(e)}")