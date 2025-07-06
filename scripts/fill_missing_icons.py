#!/usr/bin/env python3
"""
Fill in missing icon files from the GitHub repository
"""
import os
import requests
import time

# Configuration
GITHUB_RAW_URL = "https://raw.githubusercontent.com/Isaaru/EQEmuAllaClone/master/images/icons"
LOCAL_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "icons", "items")

def download_missing_icons():
    """Download any missing icons between 0 and 1521"""
    downloaded = 0
    already_exists = 0
    failed = 0
    
    print("Checking for missing icons between 0 and 1521...")
    
    for i in range(0, 1522):  # 0 to 1521 inclusive
        filename = f"{i}.gif"
        local_path = os.path.join(LOCAL_ICONS_DIR, filename)
        
        if os.path.exists(local_path):
            already_exists += 1
            continue
        
        # Try to download
        url = f"{GITHUB_RAW_URL}/{filename}"
        try:
            print(f"Downloading missing icon: {filename}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
            else:
                failed += 1
                print(f"  Failed to download {filename}: status {response.status_code}")
        except Exception as e:
            failed += 1
            print(f"  Error downloading {filename}: {e}")
        
        # Small delay to be respectful
        if downloaded % 10 == 0 and downloaded > 0:
            time.sleep(0.5)
    
    print(f"\nSummary:")
    print(f"Already existed: {already_exists}")
    print(f"Downloaded: {downloaded}")
    print(f"Failed: {failed}")
    print(f"Total icons now: {already_exists + downloaded}")

if __name__ == "__main__":
    download_missing_icons()