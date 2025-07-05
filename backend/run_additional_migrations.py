#!/usr/bin/env python3
"""
Run additional migrations for display_name, anonymous_mode, and avatar_class fields.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_db_connection():
    """Get database connection using existing app configuration."""
    # Try production database first
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # Fall back to config.json if no env var
        import json
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                database_url = config.get('production_database_url')
    
    if not database_url:
        print("ERROR: No database URL found. Set DATABASE_URL environment variable.")
        sys.exit(1)
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def run_migrations():
    """Run the additional migrations."""
    conn = None
    try:
        print("Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check what columns need to be added
        columns_to_check = [
            ('display_name', 'VARCHAR(50)'),
            ('anonymous_mode', 'BOOLEAN DEFAULT FALSE'),
            ('avatar_class', 'VARCHAR(20)')
        ]
        
        migrations_needed = []
        for column_name, column_def in columns_to_check:
            if not check_column_exists(cursor, 'users', column_name):
                migrations_needed.append((column_name, column_def))
                print(f"Column '{column_name}' needs to be added")
            else:
                print(f"Column '{column_name}' already exists")
        
        if not migrations_needed:
            print("✓ All columns already exist. No migrations needed.")
            return True
        
        # Run migrations for missing columns
        for column_name, column_def in migrations_needed:
            print(f"Adding column '{column_name}'...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_def}")
        
        # Commit all changes
        conn.commit()
        print("✓ All additional migrations completed successfully")
        
        # Verify columns were added
        print("\nVerifying columns:")
        for column_name, _ in columns_to_check:
            if check_column_exists(cursor, 'users', column_name):
                print(f"  ✓ {column_name}")
            else:
                print(f"  ✗ {column_name}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    if run_migrations():
        print("\n✓ Migration completed. User table updated with new columns.")
    else:
        print("\n✗ Migration failed.")
        sys.exit(1)