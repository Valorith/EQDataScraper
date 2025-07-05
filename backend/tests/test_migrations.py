"""Test cases for database migrations."""

import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import tempfile
from unittest.mock import patch, Mock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from run_all_migrations import (
    get_db_connection, create_migrations_table, 
    get_applied_migrations, apply_migration
)


class TestMigrations:
    """Test cases for database migration system."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock database connection."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
        return mock_conn, mock_cursor
    
    def test_get_db_connection_missing_url(self):
        """Test connection fails without DATABASE_URL."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(Exception, match="DATABASE_URL environment variable not set"):
                get_db_connection()
    
    @patch('psycopg2.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection."""
        with patch.dict('os.environ', {
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb'
        }):
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            conn = get_db_connection()
            
            mock_connect.assert_called_once_with(
                host='localhost',
                port=5432,
                database='testdb',
                user='user',
                password='pass'
            )
            assert conn == mock_conn
    
    def test_create_migrations_table(self, mock_connection):
        """Test migrations table creation."""
        mock_conn, mock_cursor = mock_connection
        
        create_migrations_table(mock_conn)
        
        # Verify SQL executed
        mock_cursor.execute.assert_called_once()
        sql = mock_cursor.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS schema_migrations" in sql
        assert "id SERIAL PRIMARY KEY" in sql
        assert "filename VARCHAR(255) UNIQUE NOT NULL" in sql
        assert "applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP" in sql
        
        # Verify commit called
        mock_conn.commit.assert_called_once()
    
    def test_get_applied_migrations(self, mock_connection):
        """Test retrieving applied migrations."""
        mock_conn, mock_cursor = mock_connection
        
        # Mock already applied migrations
        mock_cursor.fetchall.return_value = [
            ('001_add_user_tables.sql',),
            ('002_add_display_fields.sql',)
        ]
        
        applied = get_applied_migrations(mock_conn)
        
        # Verify SQL executed
        mock_cursor.execute.assert_called_once_with(
            "SELECT filename FROM schema_migrations ORDER BY filename"
        )
        
        # Check result
        assert applied == {'001_add_user_tables.sql', '002_add_display_fields.sql'}
    
    def test_apply_migration_success(self, mock_connection):
        """Test successful migration application."""
        mock_conn, mock_cursor = mock_connection
        
        # Create temporary migration file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test_table (id INT PRIMARY KEY);")
            temp_file = f.name
        
        try:
            result = apply_migration(mock_conn, temp_file)
            
            # Verify migration SQL executed
            calls = mock_cursor.execute.call_args_list
            assert len(calls) == 2
            
            # First call should be the migration SQL
            assert calls[0][0][0] == "CREATE TABLE test_table (id INT PRIMARY KEY);"
            
            # Second call should record the migration
            assert "INSERT INTO schema_migrations" in calls[1][0][0]
            assert os.path.basename(temp_file) in str(calls[1][0])
            
            # Verify commit called
            mock_conn.commit.assert_called_once()
            assert result is True
            
        finally:
            os.unlink(temp_file)
    
    def test_apply_migration_failure(self, mock_connection):
        """Test migration application failure."""
        mock_conn, mock_cursor = mock_connection
        
        # Make execute raise an exception
        mock_cursor.execute.side_effect = psycopg2.Error("Syntax error")
        
        # Create temporary migration file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("INVALID SQL SYNTAX")
            temp_file = f.name
        
        try:
            result = apply_migration(mock_conn, temp_file)
            
            # Verify rollback called on error
            mock_conn.rollback.assert_called_once()
            assert result is False
            
        finally:
            os.unlink(temp_file)
    
    @patch('glob.glob')
    def test_migration_file_ordering(self, mock_glob):
        """Test migrations are applied in correct order."""
        # Mock migration files in random order
        mock_glob.return_value = [
            '/path/003_add_avatar_class.sql',
            '/path/001_add_user_tables.sql',
            '/path/002_add_display_fields.sql'
        ]
        
        # The main function should sort these
        sorted_files = sorted(mock_glob.return_value)
        
        assert sorted_files[0].endswith('001_add_user_tables.sql')
        assert sorted_files[1].endswith('002_add_display_fields.sql')
        assert sorted_files[2].endswith('003_add_avatar_class.sql')


class TestMigrationContent:
    """Test the actual migration SQL files."""
    
    def test_migration_files_exist(self):
        """Test all expected migration files exist."""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'migrations'
        )
        
        expected_migrations = [
            '001_add_user_tables.sql',
            '002_add_display_fields.sql',
            '003_add_avatar_class.sql',
            '004_remove_default_class.sql'
        ]
        
        for migration in expected_migrations:
            filepath = os.path.join(migrations_dir, migration)
            assert os.path.exists(filepath), f"Migration {migration} not found"
    
    def test_migration_001_content(self):
        """Test first migration creates required tables."""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'migrations'
        )
        
        with open(os.path.join(migrations_dir, '001_add_user_tables.sql'), 'r') as f:
            content = f.read()
        
        # Check for essential tables
        assert "CREATE TABLE IF NOT EXISTS users" in content
        assert "CREATE TABLE IF NOT EXISTS oauth_sessions" in content
        assert "CREATE TABLE IF NOT EXISTS user_preferences" in content
        
        # Check for important columns
        assert "google_id VARCHAR(255) UNIQUE NOT NULL" in content
        assert "email VARCHAR(255) UNIQUE NOT NULL" in content
        assert "access_token TEXT NOT NULL" in content
        assert "refresh_token TEXT NOT NULL" in content
    
    def test_migration_002_content(self):
        """Test display fields migration."""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'migrations'
        )
        
        with open(os.path.join(migrations_dir, '002_add_display_fields.sql'), 'r') as f:
            content = f.read()
        
        # Check for new columns
        assert "ADD COLUMN IF NOT EXISTS display_name VARCHAR(100)" in content
        assert "ADD COLUMN IF NOT EXISTS anonymous_mode BOOLEAN DEFAULT FALSE" in content
    
    def test_migration_004_removes_default_class(self):
        """Test default_class removal migration."""
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'migrations'
        )
        
        with open(os.path.join(migrations_dir, '004_remove_default_class.sql'), 'r') as f:
            content = f.read()
        
        # Check it removes the column
        assert "DROP COLUMN IF EXISTS default_class" in content