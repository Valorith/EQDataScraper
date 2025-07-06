#!/usr/bin/env python3
"""
Generate test activities for the Recent Activity dashboard.
This script simulates user interactions to populate the activity feed.
"""

import requests
import time
import random
from datetime import datetime

BASE_URL = "http://localhost:5001"

def get_admin_token():
    """Get admin access token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/dev-login", 
                           json={"email": "testadmin@localhost.dev", "is_admin": True})
    if response.status_code == 200:
        return response.json()['data']['access_token']
    return None

def get_user_token(email="testuser@localhost.dev"):
    """Get regular user access token"""
    response = requests.post(f"{BASE_URL}/api/auth/dev-login", 
                           json={"email": email, "is_admin": False})
    if response.status_code == 200:
        return response.json()['data']['access_token']
    return None

def simulate_user_activities():
    """Simulate various user activities"""
    activities = []
    
    # Create different test users
    users = [
        "alice@localhost.dev",
        "bob@localhost.dev", 
        "charlie@localhost.dev"
    ]
    
    # Different search terms to try
    search_terms = ["heal", "damage", "buff", "teleport", "summon", "illusion"]
    
    print("🎭 Generating test activities...")
    
    for i, user_email in enumerate(users):
        print(f"  👤 Simulating activities for {user_email}")
        
        # Get token for this user
        token = get_user_token(user_email)
        if not token:
            print(f"    ❌ Failed to get token for {user_email}")
            continue
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. User "logs in" (already done by getting token, but could trigger login activity)
        
        # 2. Search for spells
        search_term = random.choice(search_terms)
        try:
            response = requests.get(f"{BASE_URL}/api/search-spells?q={search_term}", 
                                  headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"    ✅ Searched for '{search_term}'")
                activities.append(f"User searched for '{search_term}'")
            time.sleep(0.5)
        except:
            pass
        
        # 3. View cache status
        try:
            response = requests.get(f"{BASE_URL}/api/cache-status", headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"    ✅ Viewed cache status")
                activities.append("User viewed cache status")
            time.sleep(0.5)
        except:
            pass
        
        # 4. Check different class spells
        classes = ["paladin", "cleric", "wizard", "druid"]
        class_name = random.choice(classes)
        try:
            response = requests.get(f"{BASE_URL}/api/spells/{class_name}", 
                                  headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"    ✅ Viewed {class_name} spells")
                activities.append(f"User viewed {class_name} spells")
            time.sleep(0.5)
        except:
            pass
        
        time.sleep(1)  # Pause between users
    
    return activities

def simulate_admin_activities():
    """Simulate admin activities"""
    print("  🔒 Simulating admin activities...")
    
    token = get_admin_token()
    if not token:
        print("    ❌ Failed to get admin token")
        return []
    
    headers = {"Authorization": f"Bearer {token}"}
    activities = []
    
    # 1. Check admin stats
    try:
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            print("    ✅ Viewed admin statistics")
            activities.append("Admin viewed statistics")
        time.sleep(0.5)
    except:
        pass
    
    # 2. View system health
    try:
        response = requests.get(f"{BASE_URL}/api/health", headers=headers, timeout=5)
        if response.status_code == 200:
            print("    ✅ Checked system health")
            activities.append("Admin checked system health")
        time.sleep(0.5)
    except:
        pass
    
    # 3. Check cache details
    try:
        response = requests.get(f"{BASE_URL}/api/cache/status", headers=headers, timeout=5)
        if response.status_code == 200:
            print("    ✅ Checked detailed cache status")
            activities.append("Admin checked cache details")
        time.sleep(0.5)
    except:
        pass
    
    return activities

def main():
    """Main function to generate test activities"""
    print("🧪 EQDataScraper Activity Generator")
    print("=" * 40)
    print()
    
    # Test backend connection
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not responding. Make sure it's running:")
            print("   cd backend && python3 app.py")
            return False
    except:
        print("❌ Cannot connect to backend. Make sure it's running on port 5001")
        return False
    
    print("✅ Backend is running")
    print()
    
    # Generate activities
    user_activities = simulate_user_activities()
    admin_activities = simulate_admin_activities()
    
    total_activities = len(user_activities) + len(admin_activities)
    
    print()
    print("=" * 40)
    print(f"✅ Generated {total_activities} test activities!")
    print()
    print("🎯 What to do next:")
    print("1. Refresh the admin dashboard in your browser")
    print("2. Look at the Recent Activity section")
    print("3. You should see the activities that were just generated")
    print()
    print("📍 Admin Dashboard URL: http://localhost:3000/admin")
    print()
    print("💡 Note: Some activities may not appear immediately if activity")
    print("   logging is not fully configured, but the system is working!")
    
    return True

if __name__ == "__main__":
    main()