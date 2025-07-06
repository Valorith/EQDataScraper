#!/usr/bin/env python3
"""
Test script for the EQDataScraper Activity Tracking System
Tests both database functionality and API endpoints
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append('./backend')

class ActivitySystemTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({"test": test_name, "success": success, "message": message})
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        print()
    
    def test_backend_health(self):
        """Test that backend is responding"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Backend Health Check", True, 
                             f"Backend is healthy - {health_data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Backend Health Check", False, 
                             f"Backend returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Backend not responding: {e}")
            return False
    
    def test_activities_endpoint_auth(self):
        """Test that activities endpoint requires authentication"""
        try:
            response = requests.get(f"{self.base_url}/api/admin/activities", timeout=5)
            if response.status_code == 401:
                self.log_test("Activities Endpoint Authentication", True, 
                             "Correctly requires authentication")
                return True
            else:
                self.log_test("Activities Endpoint Authentication", False, 
                             f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Activities Endpoint Authentication", False, f"Request failed: {e}")
            return False
    
    def test_dev_login_and_activities(self):
        """Test dev login and activity logging"""
        try:
            # Try dev login with admin privileges
            login_response = requests.post(f"{self.base_url}/api/auth/dev-login", 
                                         json={"email": "testadmin@localhost.dev", "is_admin": True},
                                         timeout=5)
            
            if login_response.status_code != 200:
                self.log_test("Dev Login", False, 
                             f"Dev login failed with status {login_response.status_code}")
                return False
            
            login_data = login_response.json()
            if not login_data.get('success') or not login_data.get('data', {}).get('access_token'):
                self.log_test("Dev Login", False, "No access token in response")
                return False
            
            access_token = login_data['data']['access_token']
            self.log_test("Dev Login", True, "Successfully obtained access token")
            
            # Test accessing activities with token
            headers = {"Authorization": f"Bearer {access_token}"}
            activities_response = requests.get(f"{self.base_url}/api/admin/activities?limit=5", 
                                             headers=headers, timeout=5)
            
            if activities_response.status_code == 200:
                activities_data = activities_response.json()
                activities = activities_data.get('data', {}).get('activities', [])
                total_count = activities_data.get('data', {}).get('total_count', 0)
                
                self.log_test("Activities API Access", True, 
                             f"Retrieved {len(activities)} activities (total: {total_count})")
                
                # Log the first few activities for verification
                if activities:
                    print("    Recent activities:")
                    for i, activity in enumerate(activities[:3]):
                        desc = activity.get('description', 'No description')
                        timestamp = activity.get('created_at', 'No timestamp')
                        print(f"      {i+1}. {desc} ({timestamp})")
                else:
                    print("    No activities found in database yet")
                
                return True
            else:
                self.log_test("Activities API Access", False, 
                             f"Failed to access activities: {activities_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Dev Login and Activities", False, f"Test failed: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connection and table existence"""
        try:
            # Import backend modules
            import psycopg2
            from dotenv import load_dotenv
            
            # Load environment
            load_dotenv('./backend/.env')
            
            # Get database config from backend
            from backend.app import USE_DATABASE_CACHE, DB_CONFIG
            
            if not USE_DATABASE_CACHE:
                self.log_test("Database Connection", False, 
                             "Database cache not enabled - check DATABASE_URL")
                return False
            
            # Test connection
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check if activity_logs table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'activity_logs'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.log_test("Database Table Check", False, 
                             "activity_logs table does not exist - run migrations")
                conn.close()
                return False
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'activity_logs' 
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            expected_columns = ['id', 'user_id', 'action', 'resource_type', 'resource_id', 
                              'details', 'ip_address', 'user_agent', 'created_at']
            
            actual_columns = [col[0] for col in columns]
            missing_columns = set(expected_columns) - set(actual_columns)
            
            if missing_columns:
                self.log_test("Database Table Structure", False, 
                             f"Missing columns: {missing_columns}")
                conn.close()
                return False
            
            # Check record count
            cursor.execute("SELECT COUNT(*) FROM activity_logs;")
            record_count = cursor.fetchone()[0]
            
            self.log_test("Database Connection", True, 
                         f"Table exists with {record_count} records")
            
            conn.close()
            return True
            
        except ImportError as e:
            self.log_test("Database Connection", False, 
                         f"Missing dependencies: {e}")
            return False
        except Exception as e:
            self.log_test("Database Connection", False, f"Connection failed: {e}")
            return False
    
    def test_activity_logging_manual(self):
        """Manually test activity logging"""
        try:
            # Import backend modules  
            import psycopg2
            from backend.app import USE_DATABASE_CACHE, DB_CONFIG
            from backend.models.activity import ActivityLog
            
            if not USE_DATABASE_CACHE:
                self.log_test("Manual Activity Logging", False, 
                             "Database not available for testing")
                return False
            
            # Connect and create test activity
            conn = psycopg2.connect(**DB_CONFIG)
            activity_log = ActivityLog(conn)
            
            # Log a test activity
            test_activity = activity_log.log_activity(
                action=ActivityLog.ACTION_SYSTEM_ERROR,
                user_id=None,
                resource_type=ActivityLog.RESOURCE_SYSTEM,
                resource_id='test_system',
                details={'test': True, 'timestamp': datetime.now().isoformat()},
                ip_address='127.0.0.1',
                user_agent='Activity Test Script'
            )
            
            if test_activity and test_activity.get('id'):
                self.log_test("Manual Activity Logging", True, 
                             f"Successfully logged test activity with ID {test_activity['id']}")
                conn.close()
                return True
            else:
                self.log_test("Manual Activity Logging", False, 
                             "Failed to log test activity")
                conn.close()
                return False
                
        except Exception as e:
            self.log_test("Manual Activity Logging", False, f"Test failed: {e}")
            return False
    
    def generate_test_activities(self):
        """Generate some test activities for demonstration"""
        try:
            # Get access token first  
            login_response = requests.post(f"{self.base_url}/api/auth/dev-login", 
                                         json={"email": "test_activity_user@localhost.dev", "is_admin": True},
                                         timeout=5)
            
            if login_response.status_code != 200:
                self.log_test("Generate Test Activities", False, "Could not get access token")
                return False
            
            access_token = login_response.json()['data']['access_token']
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Perform some actions that should generate activities
            test_actions = [
                ("Search for spells", f"{self.base_url}/api/search-spells?q=heal"),
                ("Get cache status", f"{self.base_url}/api/cache-status"),
                ("Check system health", f"{self.base_url}/api/health"),
            ]
            
            success_count = 0
            for action_name, url in test_actions:
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        success_count += 1
                        print(f"    ✅ {action_name}")
                    else:
                        print(f"    ❌ {action_name} (status: {response.status_code})")
                except Exception as e:
                    print(f"    ❌ {action_name} (error: {e})")
                
                time.sleep(0.5)  # Small delay between requests
            
            self.log_test("Generate Test Activities", True, 
                         f"Performed {success_count}/{len(test_actions)} test actions")
            return True
            
        except Exception as e:
            self.log_test("Generate Test Activities", False, f"Failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 EQDataScraper Activity System Tests")
        print("=" * 50)
        print()
        
        # Run tests in order
        tests = [
            self.test_backend_health,
            self.test_database_connection,
            self.test_activities_endpoint_auth,
            self.test_dev_login_and_activities,
            self.test_activity_logging_manual,
            self.generate_test_activities,
        ]
        
        for test in tests:
            test()
        
        # Summary
        print("=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! Activity system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            print("\n🔧 Common fixes:")
            print("  - Ensure backend is running: python3 backend/app.py")
            print("  - Check DATABASE_URL is set in .env")
            print("  - Run migrations: python3 backend/run_all_migrations.py")
            print("  - Verify ENABLE_USER_ACCOUNTS=true in .env")
        
        return passed == total

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5001"
    
    print(f"Testing activity system at: {base_url}")
    print()
    
    tester = ActivitySystemTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()