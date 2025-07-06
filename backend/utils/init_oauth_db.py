"""
Initialize OAuth database tables.
This script checks if the required OAuth tables exist and creates them if needed.
"""

import os
import psycopg2
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def init_oauth_database(db_config):
    """
    Initialize OAuth database tables if they don't exist.
    
    Args:
        db_config: Database configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        users_exists = cursor.fetchone()[0]
        
        if not users_exists:
            logger.info("Creating OAuth database tables...")
            
            # Read and execute migration files
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
            migration_files = [
                '001_add_user_tables.sql',
                '002_add_display_fields.sql',
                '003_add_avatar_class.sql',
                '004_remove_default_class.sql',
                '005_add_activity_tracking.sql'
            ]
            
            for migration_file in migration_files:
                migration_path = os.path.join(migrations_dir, migration_file)
                if os.path.exists(migration_path):
                    logger.info(f"Running migration: {migration_file}")
                    with open(migration_path, 'r') as f:
                        sql = f.read()
                        # Execute the migration
                        cursor.execute(sql)
                        conn.commit()
                else:
                    logger.warning(f"Migration file not found: {migration_path}")
            
            logger.info("OAuth database tables created successfully")
        else:
            logger.info("OAuth database tables already exist")
        
        # Close connection
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize OAuth database: {e}")
        return False


def check_oauth_tables(db_config):
    """
    Check if all required OAuth tables exist.
    
    Args:
        db_config: Database configuration dictionary
        
    Returns:
        dict: Status of each table
    """
    required_tables = ['users', 'oauth_sessions', 'user_preferences', 'activity_logs']
    table_status = {}
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            table_status[table] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return table_status
        
    except Exception as e:
        logger.error(f"Failed to check OAuth tables: {e}")
        return {table: False for table in required_tables}


if __name__ == "__main__":
    # Test the initialization
    from dotenv import load_dotenv
    load_dotenv()
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        db_config = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password
        }
        
        print("Checking OAuth tables...")
        status = check_oauth_tables(db_config)
        for table, exists in status.items():
            print(f"  {table}: {'✓' if exists else '✗'}")
        
        if not all(status.values()):
            print("\nInitializing OAuth database...")
            if init_oauth_database(db_config):
                print("OAuth database initialized successfully")
            else:
                print("Failed to initialize OAuth database")
    else:
        print("No DATABASE_URL found")