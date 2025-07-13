#!/usr/bin/env python3
"""
Simple test to isolate backend hanging issues.
"""
import os
import sys
import signal
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_import_timeout():
    """Test that imports don't hang."""
    print("Testing basic imports...")
    
    def timeout_handler(signum, frame):
        print("❌ Import timed out!")
        sys.exit(1)
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        print("Importing utils.db_connection_pool...")
        from utils.db_connection_pool import DatabaseConnectionPool
        print("✅ db_connection_pool imported")
        
        print("Importing utils.database_connectors...")
        from utils.database_connectors import get_database_connector
        print("✅ database_connectors imported")
        
        print("Importing utils.content_db_manager...")
        from utils.content_db_manager import ContentDatabaseManager
        print("✅ content_db_manager imported")
        
        # Cancel timeout
        signal.alarm(0)
        print("✅ All imports successful")
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Import error: {e}")
        sys.exit(1)

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    print("Testing basic functionality...")
    
    try:
        # Test connection pool creation with dummy function
        from utils.db_connection_pool import DatabaseConnectionPool
        
        def dummy_conn():
            return "test_connection"
        
        pool = DatabaseConnectionPool(dummy_conn, max_connections=2, timeout=1)
        print("✅ Connection pool created")
        
        # Test getting connection
        with pool.get_connection() as conn:
            assert conn == "test_connection"
        print("✅ Connection retrieved from pool")
        
        # Test pool stats
        stats = pool.get_pool_stats()
        print(f"✅ Pool stats: {stats}")
        
        # Clean up
        pool.close_all()
        print("✅ Pool closed")
        
    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        sys.exit(1)

def test_app_creation():
    """Test that app can be created without hanging."""
    print("Testing Flask app creation...")
    
    def timeout_handler(signum, frame):
        print("❌ App creation timed out!")
        sys.exit(1)
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        # Set environment variables to avoid database connections
        os.environ['ENABLE_USER_ACCOUNTS'] = 'false'
        os.environ['ENABLE_DEV_AUTH'] = 'true'
        os.environ['TESTING'] = '1'
        
        print("Creating Flask app...")
        from app import app
        print("✅ Flask app created")
        
        # Test basic route
        with app.test_client() as client:
            response = client.get('/api/health')
            print(f"✅ Health check: {response.status_code}")
        
        # Cancel timeout
        signal.alarm(0)
        print("✅ App creation successful")
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ App creation error: {e}")
        sys.exit(1)

def main():
    """Run simple tests."""
    print("🧪 Simple Backend Hanging Tests")
    print("=" * 40)
    
    test_import_timeout()
    test_basic_functionality()
    test_app_creation()
    
    print("\n✅ All simple tests passed!")

if __name__ == "__main__":
    main()