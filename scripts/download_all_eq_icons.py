#!/usr/bin/env python3
"""
Download ALL EverQuest item icons from Lucy (Allakhazam)
Icons are available at: http://lucy.allakhazam.com/images/icons/item_####.gif
where #### is the icon number (e.g., item_500.gif)
"""
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configuration
LUCY_BASE_URL = "http://lucy.allakhazam.com/images/icons"
LOCAL_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "icons", "items")
MAX_WORKERS = 20
RATE_LIMIT_DELAY = 0.05  # Delay between downloads
MAX_ICON_NUMBER = 10000  # We'll try up to this number

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
        return f"Skipped {filename} (already exists)", True
    
    # Download the file
    url = f"{LUCY_BASE_URL}/item_{icon_num}.gif"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Check if it's actually an image (not an error page)
            if response.headers.get('content-type', '').startswith('image'):
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return f"Downloaded {filename}", True
            else:
                return f"Not an image: {filename}", False
        else:
            return f"Not found: {filename} (status {response.status_code})", False
    except Exception as e:
        return f"Error downloading {filename}: {str(e)}", False

def download_icon_range(start, end):
    """Download icons in a specific range"""
    print(f"\nDownloading icons from {start} to {end}...")
    
    downloaded = 0
    skipped = 0
    failed = 0
    not_found = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all download tasks
        future_to_num = {executor.submit(download_icon, num): num for num in range(start, end + 1)}
        
        # Process completed downloads
        for future in as_completed(future_to_num):
            result, success = future.result()
            
            if "Downloaded" in result:
                downloaded += 1
                if downloaded % 100 == 0:
                    print(f"Progress: Downloaded {downloaded} new icons...")
            elif "Skipped" in result:
                skipped += 1
            elif "Not found" in result or "Not an image" in result:
                not_found += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nRange {start}-{end} complete!")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Not found: {not_found}")
    print(f"Failed: {failed}")
    
    return downloaded, skipped, not_found, failed

def find_icon_ranges():
    """Find which icon number ranges actually exist"""
    print("Scanning for valid icon ranges...")
    ranges = []
    current_start = None
    last_valid = None
    
    # Quick scan to find ranges (checking every 100)
    for i in range(0, MAX_ICON_NUMBER, 100):
        url = f"{LUCY_BASE_URL}/item_{i}.gif"
        try:
            response = requests.head(url, timeout=2)
            if response.status_code == 200:
                if current_start is None:
                    current_start = i
                last_valid = i
            else:
                if current_start is not None and last_valid is not None:
                    # End of a range
                    ranges.append((current_start, min(last_valid + 100, MAX_ICON_NUMBER)))
                    current_start = None
                    last_valid = None
        except:
            pass
    
    # Don't forget the last range
    if current_start is not None:
        ranges.append((current_start, min(last_valid + 100, MAX_ICON_NUMBER)))
    
    print(f"Found {len(ranges)} icon ranges: {ranges}")
    return ranges

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
    print("EverQuest Complete Icon Downloader")
    print("=" * 50)
    
    try:
        # Ensure directory exists
        ensure_dir_exists()
        
        # Option 1: Download specific ranges (faster, recommended)
        # Common icon ranges in EverQuest
        icon_ranges = [
            (0, 2000),      # Most common item icons
            (2000, 4000),   # Extended item icons
            (4000, 6000),   # More items
            (6000, 8000),   # Even more items
            (8000, 10000)   # Latest expansions
        ]
        
        total_downloaded = 0
        total_skipped = 0
        total_not_found = 0
        total_failed = 0
        
        for start, end in icon_ranges:
            d, s, n, f = download_icon_range(start, end)
            total_downloaded += d
            total_skipped += s
            total_not_found += n
            total_failed += f
            
            # Stop if we're getting mostly not found
            if n > (end - start) * 0.9:  # 90% not found
                print(f"Stopping - most icons in range {start}-{end} don't exist")
                break
        
        print("\n" + "=" * 50)
        print("FINAL SUMMARY")
        print(f"Total downloaded: {total_downloaded}")
        print(f"Total skipped: {total_skipped}")
        print(f"Total not found: {total_not_found}")
        print(f"Total failed: {total_failed}")
        
        # Create icon mapping
        mapping = create_icon_mapping()
        
        print(f"\nAll done! {len(mapping)} icons are ready to use.")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())