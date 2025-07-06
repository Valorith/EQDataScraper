#!/usr/bin/env python3
"""
Download EverQuest item icons from Project 1999 Wiki
Icons are available at: https://wiki.project1999.com/images/icons/####.gif
where #### is the icon number
"""
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configuration
P99_BASE_URL = "https://wiki.project1999.com/images/icons"
LOCAL_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "icons", "items")
MAX_WORKERS = 10
RATE_LIMIT_DELAY = 0.1  # Be respectful to P99 wiki
ICON_RANGES = [
    (500, 600),    # Test range first
    (600, 700),
    (700, 800),
    (800, 900),
    (900, 1000),
    (1000, 1100),
    (1100, 1200),
    (1200, 1300),
    (1300, 1400),
    (1400, 1500),
    (1500, 1600),
    (1600, 1700),
    (1700, 1800),
    (1800, 1900),
    (1900, 2000),
    (2000, 2500),
    (2500, 3000),
    (3000, 3500),
    (3500, 4000),
    (4000, 4500),
    (4500, 5000),
    (5000, 5500),
    (5500, 6000),
    (6000, 6500),
    (6500, 7000)
]

def ensure_dir_exists():
    """Ensure the local icons directory exists"""
    os.makedirs(LOCAL_ICONS_DIR, exist_ok=True)
    print(f"Icons will be saved to: {LOCAL_ICONS_DIR}")

def download_icon(icon_num):
    """Download a single icon file"""
    filename = f"{icon_num}.gif"
    local_path = os.path.join(LOCAL_ICONS_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(local_path):
        return f"Skipped {filename} (already exists)", True, 'skipped'
    
    # Try the P99 wiki URL
    url = f"{P99_BASE_URL}/{icon_num}.gif"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return f"Downloaded {filename}", True, 'downloaded'
            else:
                return f"Not an image: {filename}", False, 'not_image'
        elif response.status_code == 404:
            return f"Not found: {filename}", False, 'not_found'
        else:
            return f"Error {response.status_code}: {filename}", False, 'error'
    except Exception as e:
        return f"Error downloading {filename}: {str(e)}", False, 'error'

def download_icon_range(start, end):
    """Download icons in a specific range"""
    print(f"\nDownloading icons from {start} to {end}...")
    
    stats = {
        'downloaded': 0,
        'skipped': 0,
        'not_found': 0,
        'error': 0,
        'not_image': 0
    }
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all download tasks
        future_to_num = {executor.submit(download_icon, num): num for num in range(start, end + 1)}
        
        # Process completed downloads
        for future in as_completed(future_to_num):
            result, success, status = future.result()
            stats[status] = stats.get(status, 0) + 1
            
            if stats['downloaded'] % 50 == 0 and stats['downloaded'] > 0:
                print(f"Progress: Downloaded {stats['downloaded']} new icons...")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"Range {start}-{end} complete: Downloaded={stats['downloaded']}, Skipped={stats['skipped']}, Not Found={stats['not_found']}")
    
    return stats

def create_icon_mapping():
    """Create a JSON mapping of icon numbers to filenames"""
    print("\nCreating icon mapping...")
    mapping = {}
    
    for filename in os.listdir(LOCAL_ICONS_DIR):
        if filename.endswith('.gif') and not filename.startswith('icon_mapping'):
            try:
                icon_num = int(filename[:-4])
                mapping[icon_num] = filename
            except ValueError:
                continue
    
    # Save mapping to JSON file
    mapping_path = os.path.join(LOCAL_ICONS_DIR, "icon_mapping.json")
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Created icon mapping with {len(mapping)} entries")
    return mapping

def main():
    """Main function"""
    print("EverQuest P99 Icon Downloader")
    print("=" * 50)
    
    try:
        # Ensure directory exists
        ensure_dir_exists()
        
        total_stats = {
            'downloaded': 0,
            'skipped': 0,
            'not_found': 0,
            'error': 0,
            'not_image': 0
        }
        
        for start, end in ICON_RANGES:
            stats = download_icon_range(start, end)
            
            # Add to totals
            for key, value in stats.items():
                total_stats[key] = total_stats.get(key, 0) + value
            
            # Stop if we're getting mostly not found
            if stats['not_found'] > (end - start) * 0.8:  # 80% not found
                print(f"Stopping - most icons in range {start}-{end} don't exist")
                break
            
            # Small break between ranges
            time.sleep(1)
        
        print("\n" + "=" * 50)
        print("FINAL SUMMARY")
        for key, value in total_stats.items():
            print(f"{key.capitalize()}: {value}")
        
        # Create icon mapping
        mapping = create_icon_mapping()
        
        print(f"\nAll done! {len(mapping)} icons are ready to use.")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())