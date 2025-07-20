#!/usr/bin/env python3
"""
Development Database Setup Helper
Helps configure PostgreSQL for local development or Railway connection
"""

import os
import sys
from urllib.parse import urlparse

def load_env_file(env_path='.env'):
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars

def update_env_file(env_path='.env', updates={}):
    """Update environment variables in .env file"""
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update existing variables
    for i, line in enumerate(lines):
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0]
            if key in updates:
                lines[i] = f"{key}={updates[key]}\n"
                del updates[key]
    
    # Add new variables
    for key, value in updates.items():
        lines.append(f"{key}={value}\n")
    
    with open(env_path, 'w') as f:
        f.writelines(lines)

def validate_database_url(db_url):
    """Validate and parse DATABASE_URL"""
    try:
        parsed = urlparse(db_url)
        return {
            'scheme': parsed.scheme,
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:] if parsed.path else '',
            'username': parsed.username,
            'password': parsed.password
        }
    except Exception as e:
        return None

def main():
    print("🗄️  EQDataScraper Development Database Setup")
    print("=" * 50)
    
    # Load current environment
    env_vars = load_env_file()
    current_db_url = env_vars.get('DATABASE_URL', '')
    
    if current_db_url:
        print(f"📍 Current DATABASE_URL: {current_db_url[:50]}...")
        parsed = validate_database_url(current_db_url)
        if parsed:
            print(f"   Host: {parsed['host']}")
            print(f"   Database: {parsed['database']}")
            print(f"   Port: {parsed['port']}")
            if 'railway.internal' in current_db_url:
                print("   Type: Railway PostgreSQL")
            else:
                print("   Type: Local PostgreSQL")
    else:
        print("❌ No DATABASE_URL configured")
    
    print("\n🎯 Database Configuration Options:")
    print("1. Use Railway PostgreSQL (same as production)")
    print("2. Use Local PostgreSQL")
    print("3. Keep current configuration")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        print("\n🚀 Railway PostgreSQL Setup:")
        print("1. Go to your Railway project dashboard")
        print("2. Click on 'Variables' tab")
        print("3. Find DATABASE_URL variable")
        print("4. Copy the full PostgreSQL URL")
        print("   Example: postgresql://postgres:xxx@postgres.railway.internal:5432/railway")
        
        railway_url = input("\nPaste Railway DATABASE_URL: ").strip()
        if railway_url:
            parsed = validate_database_url(railway_url)
            if parsed and 'railway.internal' in railway_url:
                update_env_file(updates={'DATABASE_URL': railway_url})
                print("✅ Railway PostgreSQL configured successfully!")
                print("   You can now run: python3 run.py start dev")
            else:
                print("❌ Invalid Railway PostgreSQL URL")
        else:
            print("❌ No URL provided")
    
    elif choice == '2':
        print("\n🏠 Local PostgreSQL Setup:")
        print("Make sure you have PostgreSQL installed and running locally")
        
        host = input("Host (localhost): ").strip() or "localhost"
        port = input("Port (5432): ").strip() or "5432"
        database = input("Database name (eqdatascraper): ").strip() or "eqdatascraper"
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        if username and password:
            local_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            update_env_file(updates={'DATABASE_URL': local_url})
            print("✅ Local PostgreSQL configured successfully!")
            print(f"   Database: {database}")
            print(f"   Host: {host}:{port}")
            print("   You can now run: python3 run.py start dev")
        else:
            print("❌ Username and password are required")
    
    elif choice == '3':
        print("✅ Keeping current configuration")
    
    elif choice == '4':
        print("👋 Goodbye!")
        sys.exit(0)
    
    else:
        print("❌ Invalid option selected")

if __name__ == "__main__":
    main()