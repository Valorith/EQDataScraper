#!/usr/bin/env python3
"""
Test script to verify the activity tracking system is properly implemented.
"""

import os
import sys
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_activity_tracking():
    """Test that activity tracking is properly set up"""
    
    # Check if user accounts are enabled
    if os.environ.get('ENABLE_USER_ACCOUNTS', 'false').lower() != 'true':
        print("❌ ENABLE_USER_ACCOUNTS is not set to 'true'")
        print("   Activity tracking requires user accounts to be enabled")
        return False
    
    print("✅ User accounts are enabled")
    
    # Check database connection
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print("✅ DATABASE_URL is configured")
    
    try:
        # Parse database URL
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        
        DB_CONFIG = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:] if parsed.path else None
        }
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Successfully connected to database")
        
        # Check if activity_logs table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'activity_logs'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        if not table_exists:
            print("❌ activity_logs table does not exist")
            print("   Run: python run_migration.py 005_add_activity_tracking.sql")
            return False
        
        print("✅ activity_logs table exists")
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'activity_logs'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        expected_columns = [
            'id', 'user_id', 'action', 'resource_type', 
            'resource_id', 'details', 'ip_address', 'user_agent', 'created_at'
        ]
        
        actual_columns = [col[0] for col in columns]
        missing_columns = set(expected_columns) - set(actual_columns)
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        
        print("✅ All required columns present")
        
        # Test activity logging
        from models.activity import ActivityLog
        activity_log = ActivityLog(conn)
        
        # Log a test activity
        test_activity = activity_log.log_activity(
            action='test_activity',
            user_id=None,  # System action
            resource_type='system',
            resource_id='test',
            details={'test': True, 'timestamp': datetime.now().isoformat()},
            ip_address='127.0.0.1',
            user_agent='Test Script'
        )
        
        print(f"✅ Successfully logged test activity with ID: {test_activity['id']}")
        
        # Get recent activities
        recent = activity_log.get_recent_activities(limit=5)
        print(f"✅ Retrieved {len(recent)} recent activities")
        
        # Get activity stats
        stats = activity_log.get_activity_stats(hours=24)
        print(f"✅ Activity stats - Total: {stats['total_activities']}, Unique users: {stats['unique_users']}")
        
        # Clean up test activity
        cursor.execute("DELETE FROM activity_logs WHERE id = %s", (test_activity['id'],))
        conn.commit()
        print("✅ Cleaned up test activity")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Activity tracking system is fully operational!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required modules are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Activity Tracking System...")
    print("=" * 50)
    
    success = test_activity_tracking()
    
    if not success:
        print("\n⚠️  Activity tracking system needs attention")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)