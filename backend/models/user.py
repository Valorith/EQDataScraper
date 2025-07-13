"""
User models for Google OAuth authentication.
This module provides database operations for user-related tables.
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

class User:
    """User model for Google OAuth authentication."""
    
    def __init__(self, connection):
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
    
    def create_user(self, google_id: str, email: str, first_name: str = None, 
                   last_name: str = None, avatar_url: str = None, role: str = 'user') -> Dict[str, Any]:
        """Create a new user from Google OAuth data."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    INSERT INTO users (google_id, email, first_name, last_name, avatar_url, role, last_login, display_name, anonymous_mode, avatar_class)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, google_id, email, first_name, last_name, avatar_url, role, 
                             is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                """, (google_id, email, first_name, last_name, avatar_url, role, datetime.utcnow(), None, False, None))
                
                row = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role',
                          'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                user = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                
                # Create default preferences
                self.create_user_preferences(user['id'])
                
                return user
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to create user: {str(e)}")
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, google_id, email, first_name, last_name, avatar_url, role, 
                           is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                    FROM users 
                    WHERE google_id = %s AND is_active = TRUE
                """, (google_id,))
                
                result = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role',
                          'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                return self._row_to_dict(result, columns, use_dict_cursor)
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user by Google ID: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, google_id, email, first_name, last_name, avatar_url, role, 
                           is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                    FROM users 
                    WHERE email = %s AND is_active = TRUE
                """, (email,))
                
                result = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                return self._row_to_dict(result, columns, use_dict_cursor)
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user by email: {str(e)}")
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, google_id, email, first_name, last_name, avatar_url, role, 
                           is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                    FROM users 
                    WHERE id = %s AND is_active = TRUE
                """, (user_id,))
                
                result = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                return self._row_to_dict(result, columns, use_dict_cursor)
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user by ID: {str(e)}")
    
    def update_user_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET last_login = %s 
                    WHERE id = %s
                """, (datetime.utcnow(), user_id))
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to update user login: {str(e)}")
    
    def update_user_profile(self, user_id: int, first_name: str = None, 
                           last_name: str = None, avatar_url: str = None,
                           display_name: str = None, anonymous_mode: bool = None, avatar_class: str = None) -> Dict[str, Any]:
        """Update user profile information."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                # Build dynamic update query
                updates = []
                params = []
                
                if first_name is not None:
                    updates.append("first_name = %s")
                    params.append(first_name)
                
                if last_name is not None:
                    updates.append("last_name = %s")
                    params.append(last_name)
                
                if avatar_url is not None:
                    updates.append("avatar_url = %s")
                    params.append(avatar_url)
                
                if display_name is not None:
                    updates.append("display_name = %s")
                    params.append(display_name)
                
                if anonymous_mode is not None:
                    updates.append("anonymous_mode = %s")
                    params.append(anonymous_mode)
                
                if avatar_class is not None:
                    updates.append("avatar_class = %s")
                    params.append(avatar_class)
                
                if not updates:
                    return self.get_user_by_id(user_id)
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(user_id)
                
                cursor.execute(f"""
                    UPDATE users 
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id, google_id, email, first_name, last_name, avatar_url, role, 
                             is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                """, params)
                
                row = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                user = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return user
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to update user profile: {str(e)}")
    
    def get_all_users(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get all users with pagination (admin only)."""
        try:
            offset = (page - 1) * per_page
            
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                count_row = cursor.fetchone()
                if use_dict_cursor:
                    total_count = count_row['count']
                else:
                    total_count = count_row[0]
                
                # Get users
                cursor.execute("""
                    SELECT id, google_id, email, first_name, last_name, avatar_url, role, 
                           is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                    FROM users 
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                
                rows = cursor.fetchall()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                users = [self._row_to_dict(row, columns, use_dict_cursor) for row in rows]
                
                return {
                    'users': users,
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
        except psycopg2.Error as e:
            raise Exception(f"Failed to get all users: {str(e)}")
    
    def update_user_role(self, user_id: int, role: str) -> Dict[str, Any]:
        """Update user role (admin only)."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    UPDATE users 
                    SET role = %s, updated_at = %s
                    WHERE id = %s
                    RETURNING id, google_id, email, first_name, last_name, avatar_url, role, 
                             is_active, created_at, updated_at, last_login, display_name, anonymous_mode, avatar_class
                """, (role, datetime.utcnow(), user_id))
                
                row = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                user = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return user
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to update user role: {str(e)}")
    
    def create_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Create default user preferences."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    INSERT INTO user_preferences (user_id, theme_preference, results_per_page)
                    VALUES (%s, %s, %s)
                    RETURNING id, user_id, theme_preference, results_per_page, 
                             created_at, updated_at
                """, (user_id, 'auto', 20))
                
                row = cursor.fetchone()
                columns = ['id', 'user_id', 'theme_preference', 'results_per_page', 'created_at', 'updated_at']
                preferences = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return preferences
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to create user preferences: {str(e)}")
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, user_id, theme_preference, results_per_page, 
                           created_at, updated_at
                    FROM user_preferences 
                    WHERE user_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                columns = ['id', 'google_id', 'email', 'first_name', 'last_name', 'avatar_url', 'role', 'is_active', 'created_at', 'updated_at', 'last_login', 'display_name', 'anonymous_mode', 'avatar_class']
                return self._row_to_dict(result, columns, use_dict_cursor)
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user preferences: {str(e)}")
    
    def update_user_preferences(self, user_id: int, theme_preference: str = None, 
                               results_per_page: int = None) -> Dict[str, Any]:
        """Update user preferences."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                # Build dynamic update query
                updates = []
                params = []
                
                if theme_preference is not None:
                    updates.append("theme_preference = %s")
                    params.append(theme_preference)
                
                if results_per_page is not None:
                    updates.append("results_per_page = %s")
                    params.append(results_per_page)
                
                if not updates:
                    return self.get_user_preferences(user_id)
                
                updates.append("updated_at = %s")
                params.append(datetime.utcnow())
                params.append(user_id)
                
                cursor.execute(f"""
                    UPDATE user_preferences 
                    SET {', '.join(updates)}
                    WHERE user_id = %s
                    RETURNING id, user_id, theme_preference, results_per_page, 
                             created_at, updated_at
                """, params)
                
                row = cursor.fetchone()
                columns = ['id', 'user_id', 'theme_preference', 'results_per_page', 'created_at', 'updated_at']
                preferences = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return preferences
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to update user preferences: {str(e)}")


class OAuthSession:
    """OAuth session model for managing user sessions."""
    
    def __init__(self, connection):
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
        """Convert a database row to a dictionary."""
        if row is None:
            return None
        
        if use_dict_cursor:
            # RealDictCursor already returns dict-like objects
            return dict(row)
        else:
            # Regular cursor returns tuples, convert to dict
            return dict(zip(columns, row)) if row else None
    
    def create_session(self, user_id: int, google_access_token: str, 
                      google_refresh_token: str = None, expires_in: int = 3600, 
                      local_session_token: str = None, ip_address: str = None) -> Dict[str, Any]:
        """Create a new OAuth session."""
        try:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    INSERT INTO oauth_sessions (user_id, google_access_token, google_refresh_token, 
                                              token_expires_at, local_session_token, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, token_expires_at, local_session_token, 
                             ip_address, created_at, last_used
                """, (user_id, google_access_token, google_refresh_token, 
                      expires_at, local_session_token, ip_address))
                
                row = cursor.fetchone()
                columns = ['id', 'user_id', 'token_expires_at', 'local_session_token', 'ip_address', 'created_at', 'last_used']
                session = self._row_to_dict(row, columns, use_dict_cursor)
                self.conn.commit()
                return session
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to create session: {str(e)}")
    
    def get_session_by_token(self, local_session_token: str) -> Optional[Dict[str, Any]]:
        """Get session by local session token."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, user_id, google_access_token, google_refresh_token, 
                           token_expires_at, local_session_token, ip_address, 
                           created_at, last_used
                    FROM oauth_sessions 
                    WHERE local_session_token = %s
                """, (local_session_token,))
                
                result = cursor.fetchone()
                columns = ['id', 'user_id', 'google_access_token', 'google_refresh_token', 'token_expires_at', 'local_session_token', 'ip_address', 'created_at', 'last_used']
                return self._row_to_dict(result, columns, use_dict_cursor)
        except psycopg2.Error as e:
            raise Exception(f"Failed to get session by token: {str(e)}")
    
    def update_session_last_used(self, session_id: int) -> None:
        """Update session last used timestamp."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE oauth_sessions 
                    SET last_used = %s 
                    WHERE id = %s
                """, (datetime.utcnow(), session_id))
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to update session last used: {str(e)}")
    
    def delete_session(self, local_session_token: str) -> None:
        """Delete session (logout)."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM oauth_sessions 
                    WHERE local_session_token = %s
                """, (local_session_token,))
                self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to delete session: {str(e)}")
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM oauth_sessions 
                    WHERE token_expires_at < %s
                """, (datetime.utcnow(),))
                
                deleted_count = cursor.rowcount
                self.conn.commit()
                return deleted_count
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Failed to cleanup expired sessions: {str(e)}")
    
    def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            cursor, use_dict_cursor = self._get_cursor()
            with cursor:
                cursor.execute("""
                    SELECT id, user_id, token_expires_at, local_session_token, 
                           ip_address, created_at, last_used
                    FROM oauth_sessions 
                    WHERE user_id = %s
                    ORDER BY last_used DESC
                """, (user_id,))
                
                rows = cursor.fetchall()
                columns = ['id', 'user_id', 'token_expires_at', 'local_session_token', 'ip_address', 'created_at', 'last_used']
                return [self._row_to_dict(row, columns, use_dict_cursor) for row in rows]
        except psycopg2.Error as e:
            raise Exception(f"Failed to get user sessions: {str(e)}")