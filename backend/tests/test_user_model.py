"""
Tests for user database models.
Tests the User and OAuthSession models for CRUD operations and data validation.
"""

import pytest
import psycopg2
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor

from models.user import User, OAuthSession
from tests.conftest import MockRealDictCursor, generate_test_user, generate_test_session


class TestUserModel:
    """Test User model database operations."""
    
    def test_create_user_success(self, mock_db_connection_with_context, sample_user_data):
        """Test successful user creation with valid Google OAuth data."""
        # Setup mock cursor to return the created user
        mock_cursor = MockRealDictCursor(sample_user_data)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        # Create user model instance
        user_model = User(mock_db_connection_with_context)
        
        # Test user creation
        result = user_model.create_user(
            google_id=sample_user_data['google_id'],
            email=sample_user_data['email'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
            avatar_url=sample_user_data['avatar_url']
        )
        
        # Verify result
        assert result['google_id'] == sample_user_data['google_id']
        assert result['email'] == sample_user_data['email']
        assert result['first_name'] == sample_user_data['first_name']
        assert result['role'] == 'user'  # Default role
        
        # Verify database operations (should be called twice: user creation + preferences creation)
        assert mock_db_connection_with_context.commit.call_count == 2
        assert len(mock_cursor.executed_queries) >= 1  # User creation + preferences creation
    
    def test_create_user_duplicate_google_id(self, mock_db_connection_with_context):
        """Test handling of duplicate Google ID (should raise exception)."""
        # Setup mock to simulate database constraint violation
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("UNIQUE constraint failed: users.google_id")
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        
        # Test that duplicate Google ID raises exception
        with pytest.raises(Exception) as exc_info:
            user_model.create_user(
                google_id="duplicate_google_id",
                email="test@example.com"
            )
        
        assert "UNIQUE constraint failed" in str(exc_info.value) or "Failed to create user" in str(exc_info.value)
        mock_db_connection_with_context.rollback.assert_called_once()
    
    def test_get_user_by_google_id_found(self, mock_db_connection_with_context, sample_user_data):
        """Test retrieving user by Google ID when user exists."""
        mock_cursor = MockRealDictCursor(sample_user_data)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.get_user_by_google_id(sample_user_data['google_id'])
        
        assert result is not None
        assert result['google_id'] == sample_user_data['google_id']
        assert result['email'] == sample_user_data['email']
    
    def test_get_user_by_google_id_not_found(self, mock_db_connection_with_context):
        """Test retrieving user by Google ID when user doesn't exist."""
        mock_cursor = MockRealDictCursor(None)  # No user found
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.get_user_by_google_id("nonexistent_google_id")
        
        assert result is None
    
    def test_get_user_by_email(self, mock_db_connection_with_context, sample_user_data):
        """Test retrieving user by email address."""
        mock_cursor = MockRealDictCursor(sample_user_data)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.get_user_by_email(sample_user_data['email'])
        
        assert result is not None
        assert result['email'] == sample_user_data['email']
        assert result['google_id'] == sample_user_data['google_id']
    
    def test_update_user_login(self, mock_db_connection_with_context):
        """Test updating user's last login timestamp."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        
        # Should not raise any exception
        user_model.update_user_login(user_id=1)
        
        # Verify database operations
        mock_cursor.execute.assert_called_once()
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_update_user_profile(self, mock_db_connection_with_context, sample_user_data):
        """Test updating user profile with partial data."""
        # Setup mock to return updated user data
        updated_data = sample_user_data.copy()
        updated_data['first_name'] = 'Updated'
        updated_data['last_name'] = 'Name'
        
        mock_cursor = MockRealDictCursor(updated_data)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.update_user_profile(
            user_id=1,
            first_name='Updated',
            last_name='Name'
        )
        
        assert result['first_name'] == 'Updated'
        assert result['last_name'] == 'Name'
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_get_all_users_with_pagination(self, mock_db_connection_with_context, sample_user_data):
        """Test getting all users with pagination."""
        # Mock count query and users query
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        
        # First call returns count, second call returns users
        mock_cursor.fetchone.side_effect = [{'count': 5}, None]
        mock_cursor.fetchall.return_value = [sample_user_data]
        
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.get_all_users(page=1, per_page=10)
        
        assert 'users' in result
        assert 'total_count' in result
        assert 'page' in result
        assert 'per_page' in result
        assert result['total_count'] == 5
        assert len(result['users']) == 1
    
    def test_update_user_role(self, mock_db_connection_with_context, sample_user_data):
        """Test updating user role (admin functionality)."""
        updated_data = sample_user_data.copy()
        updated_data['role'] = 'admin'
        
        mock_cursor = MockRealDictCursor(updated_data)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.update_user_role(user_id=1, role='admin')
        
        assert result['role'] == 'admin'
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_create_user_preferences(self, mock_db_connection_with_context, sample_user_preferences):
        """Test creating default user preferences."""
        mock_cursor = MockRealDictCursor(sample_user_preferences)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.create_user_preferences(user_id=1)
        
        assert result['user_id'] == 1
        assert result['theme_preference'] == 'dark'
        assert result['results_per_page'] == 25
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_get_user_preferences(self, mock_db_connection_with_context, sample_user_preferences):
        """Test retrieving user preferences."""
        mock_cursor = MockRealDictCursor(sample_user_preferences)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.get_user_preferences(user_id=1)
        
        assert result is not None
        assert result['user_id'] == 1
        assert result['theme_preference'] == 'dark'
    
    def test_update_user_preferences(self, mock_db_connection_with_context, sample_user_preferences):
        """Test updating user preferences."""
        updated_prefs = sample_user_preferences.copy()
        updated_prefs['theme_preference'] = 'dark'
        updated_prefs['results_per_page'] = 50
        
        mock_cursor = MockRealDictCursor(updated_prefs)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.update_user_preferences(
            user_id=1,
            theme_preference='dark',
            results_per_page=50
        )
        
        assert result['theme_preference'] == 'dark'
        assert result['results_per_page'] == 50
        mock_db_connection_with_context.commit.assert_called_once()


class TestOAuthSessionModel:
    """Test OAuthSession model database operations."""
    
    def test_create_session_success(self, mock_db_connection_with_context, sample_oauth_session):
        """Test successful OAuth session creation."""
        mock_cursor = MockRealDictCursor(sample_oauth_session)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        result = session_model.create_session(
            user_id=1,
            google_access_token='test_access_token',
            google_refresh_token='test_refresh_token',
            expires_in=3600,
            local_session_token='test_session_token',
            ip_address='127.0.0.1'
        )
        
        assert result['user_id'] == 1
        assert result['local_session_token'] == 'test_local_session_token'
        assert result['ip_address'] == '127.0.0.1'
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_get_session_by_token(self, mock_db_connection_with_context, sample_oauth_session):
        """Test retrieving session by local session token."""
        mock_cursor = MockRealDictCursor(sample_oauth_session)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        result = session_model.get_session_by_token('test_session_token')
        
        assert result is not None
        assert result['local_session_token'] == 'test_local_session_token'
        assert result['user_id'] == 1
    
    def test_get_session_by_token_not_found(self, mock_db_connection_with_context):
        """Test retrieving session when token doesn't exist."""
        mock_cursor = MockRealDictCursor(None)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        result = session_model.get_session_by_token('nonexistent_token')
        
        assert result is None
    
    def test_update_session_last_used(self, mock_db_connection_with_context):
        """Test updating session last used timestamp."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        
        # Should not raise any exception
        session_model.update_session_last_used(session_id=1)
        
        mock_cursor.execute.assert_called_once()
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_delete_session(self, mock_db_connection_with_context):
        """Test deleting session (logout)."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        
        # Should not raise any exception
        session_model.delete_session('test_session_token')
        
        mock_cursor.execute.assert_called_once()
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_cleanup_expired_sessions(self, mock_db_connection_with_context):
        """Test cleaning up expired sessions."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.rowcount = 5  # 5 sessions deleted
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        deleted_count = session_model.cleanup_expired_sessions()
        
        assert deleted_count == 5
        mock_cursor.execute.assert_called_once()
        mock_db_connection_with_context.commit.assert_called_once()
    
    def test_get_user_sessions(self, mock_db_connection_with_context, sample_oauth_session):
        """Test getting all sessions for a user."""
        mock_cursor = MockRealDictCursor([sample_oauth_session])
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        session_model = OAuthSession(mock_db_connection_with_context)
        result = session_model.get_user_sessions(user_id=1)
        
        assert len(result) == 1
        assert result[0]['user_id'] == 1
        assert result[0]['local_session_token'] == 'test_local_session_token'
    
    def test_database_error_handling(self, mock_db_connection_with_context):
        """Test that database errors are properly handled."""
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.execute.side_effect = psycopg2.OperationalError("Database connection failed")
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        
        with pytest.raises(Exception) as exc_info:
            user_model.create_user(
                google_id="test_id",
                email="test@example.com"
            )
        
        assert "Database connection failed" in str(exc_info.value) or "Failed to create user" in str(exc_info.value)
        mock_db_connection_with_context.rollback.assert_called_once()
    
    def test_user_preferences_validation(self, mock_db_connection_with_context):
        """Test user preferences with edge case values."""
        # Test with None values (should be allowed)
        preferences_with_none = {
            'id': 1,
            'user_id': 1,
            'theme_preference': 'auto',
            'results_per_page': 20,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        mock_cursor = MockRealDictCursor(preferences_with_none)
        mock_db_connection_with_context.cursor.return_value = mock_cursor
        
        user_model = User(mock_db_connection_with_context)
        result = user_model.update_user_preferences(
            user_id=1,
            theme_preference='auto'
        )
        
        assert result['theme_preference'] == 'auto'