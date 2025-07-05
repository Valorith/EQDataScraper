#!/usr/bin/env python3
"""
Safe migration runner for user authentication tables.
This script runs SQL migrations without affecting existing spell data.

Usage:
    python run_migration.py                    # Run the migration
    python run_migration.py --rollback        # Rollback the migration
    python run_migration.py --check          # Check current state
"""

import os
import sys
import argparse
import psycopg2
from psycopg2 import sql
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

def check_existing_tables(cursor):
    """Check if user tables already exist."""
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'oauth_sessions', 'user_preferences')
    """)
    return [row[0] for row in cursor.fetchall()]

def check_spell_tables(cursor):
    """Verify spell tables are present (safety check)."""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%spell%'
    """)
    return cursor.fetchone()[0]

def run_migration(rollback=False):
    """Run the migration or rollback."""
    migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    if rollback:
        migration_file = os.path.join(migration_dir, '001_rollback_user_tables.sql')
        action = "rollback"
    else:
        migration_file = os.path.join(migration_dir, '001_add_user_tables.sql')
        action = "migration"
    
    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    conn = None
    try:
        print(f"Connecting to database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Safety check: verify spell tables exist
        spell_table_count = check_spell_tables(cursor)
        print(f"Found {spell_table_count} existing spell-related tables (will not be modified)")
        
        # Check current state
        existing_tables = check_existing_tables(cursor)
        if existing_tables and not rollback:
            print(f"WARNING: User tables already exist: {', '.join(existing_tables)}")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        elif not existing_tables and rollback:
            print("No user tables found. Nothing to rollback.")
            return True
        
        # Read and execute migration
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"Running {action}...")
        cursor.execute(migration_sql)
        
        # Verify results
        if rollback:
            remaining_tables = check_existing_tables(cursor)
            if remaining_tables:
                print(f"ERROR: Tables still exist after rollback: {', '.join(remaining_tables)}")
                conn.rollback()
                return False
            print("✓ User tables successfully removed")
        else:
            created_tables = check_existing_tables(cursor)
            expected_tables = {'users', 'oauth_sessions', 'user_preferences'}
            if set(created_tables) != expected_tables:
                print(f"ERROR: Expected tables not created. Found: {', '.join(created_tables)}")
                conn.rollback()
                return False
            print("✓ User tables successfully created")
        
        # Verify spell tables unchanged
        spell_table_count_after = check_spell_tables(cursor)
        if spell_table_count != spell_table_count_after:
            print("ERROR: Spell table count changed! Rolling back...")
            conn.rollback()
            return False
        
        conn.commit()
        print(f"✓ {action.capitalize()} completed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def check_state():
    """Check current state of user tables."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("Checking database state...")
        
        # Check user tables
        existing_tables = check_existing_tables(cursor)
        if existing_tables:
            print(f"\nUser tables found: {', '.join(existing_tables)}")
            
            # Check row counts
            for table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} rows")
        else:
            print("\nNo user tables found.")
        
        # Check spell tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%spell%'
            ORDER BY table_name
        """)
        spell_tables = [row[0] for row in cursor.fetchall()]
        print(f"\nSpell-related tables ({len(spell_tables)} found):")
        for table in spell_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='Run user authentication migrations')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    parser.add_argument('--check', action='store_true', help='Check current state only')
    
    args = parser.parse_args()
    
    if args.check:
        check_state()
    elif args.rollback:
        if run_migration(rollback=True):
            print("\n✓ Rollback completed. You can safely delete the feature branch if desired.")
        else:
            print("\n✗ Rollback failed.")
            sys.exit(1)
    else:
        if run_migration(rollback=False):
            print("\n✓ Migration completed. User tables are ready.")
        else:
            print("\n✗ Migration failed.")
            sys.exit(1)

if __name__ == '__main__':
    main()