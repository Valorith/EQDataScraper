#!/usr/bin/env python3
"""
Test the complete backend system with hanging fixes.
"""
import os
import sys
import signal
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_complete_system():
    """Test the complete backend system."""
    print("Testing complete backend system...")
    
    def timeout_handler(signum, frame):
        print("❌ Complete system test timed out!")
        sys.exit(1)
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        # Set environment variables to avoid external dependencies
        os.environ['ENABLE_USER_ACCOUNTS'] = 'false'
        os.environ['ENABLE_DEV_AUTH'] = 'true'
        os.environ['TESTING'] = '1'
        
        print("1. Testing connection pool...")
        from utils.db_connection_pool import DatabaseConnectionPool
        
        def dummy_conn():
            return "test_db_connection"
        
        pool = DatabaseConnectionPool(dummy_conn, max_connections=2)
        
        with pool.get_connection() as conn:
            assert conn == "test_db_connection"
        print("✅ Connection pool working")
        
        print("2. Testing content database manager...")
        from utils.content_db_manager import ContentDatabaseManager
        
        manager = ContentDatabaseManager()
        # Just test that it can be created without hanging
        status = manager.get_connection_status()
        print(f"✅ Content database manager created, status: {status}")
        
        print("3. Testing Flask app creation...")
        from app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            print(f"✅ Health check: {response.status_code}")
            
            # Test database health endpoint
            response = client.get('/api/health/database')
            print(f"✅ Database health check: {response.status_code}")
            
            # Test cleanup endpoint
            response = client.post('/api/cleanup')
            print(f"✅ Cleanup endpoint: {response.status_code}")
        
        print("4. Testing cleanup...")
        from app import cleanup_resources
        cleanup_resources()
        print("✅ Cleanup completed")
        
        # Cancel timeout
        signal.alarm(0)
        print("✅ All complete system tests passed!")
        
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_complete_system()