#!/usr/bin/env python3
"""
Run all database migrations in order for the OAuth user account system.
This script ensures migrations are applied in the correct sequence.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import glob
from datetime import datetime

def get_db_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    # Parse the database URL
    url = urlparse(database_url)
    
    return psycopg2.connect(
        host=url.hostname,
        port=url.port,
        database=url.path[1:],  # Remove leading '/'
        user=url.username,
        password=url.password
    )

def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist."""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✓ Migrations table ready")

def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        return {row[0] for row in cursor.fetchall()}

def apply_migration(conn, filepath):
    """Apply a single migration file."""
    filename = os.path.basename(filepath)
    
    try:
        # Read migration file
        with open(filepath, 'r') as f:
            migration_sql = f.read()
        
        # Apply migration
        with conn.cursor() as cursor:
            cursor.execute(migration_sql)
            
            # Record migration
            cursor.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (filename,)
            )
            
        conn.commit()
        print(f"✓ Applied migration: {filename}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to apply migration {filename}: {str(e)}")
        return False

def main():
    """Run all pending migrations."""
    print("OAuth User Account System - Database Migration Runner")
    print("=" * 50)
    
    # Check if OAuth is enabled
    if os.environ.get('ENABLE_USER_ACCOUNTS', '').lower() != 'true':
        print("ℹ️  OAuth user accounts not enabled (ENABLE_USER_ACCOUNTS != true)")
        print("   Skipping migrations.")
        return 0
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        print("✓ Connected to database")
        
        # Create migrations table
        create_migrations_table(conn)
        
        # Get list of migration files
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        migration_files = sorted(glob.glob(os.path.join(migrations_dir, '*.sql')))
        
        if not migration_files:
            print("No migration files found in", migrations_dir)
            return 1
        
        # Get already applied migrations
        applied = get_applied_migrations(conn)
        print(f"Found {len(applied)} previously applied migrations")
        
        # Apply pending migrations
        pending_count = 0
        failed_count = 0
        
        for filepath in migration_files:
            filename = os.path.basename(filepath)
            
            if filename in applied:
                print(f"⏭️  Skipping {filename} (already applied)")
            else:
                pending_count += 1
                if not apply_migration(conn, filepath):
                    failed_count += 1
                    # Stop on first failure
                    break
        
        # Summary
        print("\n" + "=" * 50)
        if failed_count > 0:
            print(f"❌ Migration failed! {failed_count} migration(s) could not be applied.")
            print("   Fix the issue and run migrations again.")
            return 1
        elif pending_count == 0:
            print("✅ All migrations already applied. Database is up to date!")
        else:
            print(f"✅ Successfully applied {pending_count} migration(s)!")
        
        # Close connection
        conn.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())