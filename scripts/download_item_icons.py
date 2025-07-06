#!/usr/bin/env python3
"""
Download item icons from the EQEmuAllaClone GitHub repository
"""
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Configuration
GITHUB_API_URL = "https://api.github.com/repos/Isaaru/EQEmuAllaClone/contents/images/icons"
RAW_BASE_URL = "https://raw.githubusercontent.com/Isaaru/EQEmuAllaClone/master/images/icons"
LOCAL_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "icons", "items")
MAX_WORKERS = 10
RATE_LIMIT_DELAY = 0.1  # Delay between downloads to avoid rate limiting

def ensure_dir_exists():
    """Ensure the local icons directory exists"""
    os.makedirs(LOCAL_ICONS_DIR, exist_ok=True)
    print(f"Icons will be saved to: {LOCAL_ICONS_DIR}")

def get_icon_list():
    """Get list of all icon files from GitHub API with pagination"""
    print("Fetching icon list from GitHub...")
    all_files = []
    page = 1
    per_page = 100
    
    while True:
        url = f"{GITHUB_API_URL}?page={page}&per_page={per_page}"
        print(f"Fetching page {page}...")
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch icon list: {response.status_code}")
        
        files = response.json()
        if not files:  # No more files
            break
            
        all_files.extend(files)
        page += 1
        
        # GitHub API has a limit, check if we got less than per_page
        if len(files) < per_page:
            break
    
    icon_files = [f for f in all_files if f['name'].endswith('.gif')]
    print(f"Found {len(icon_files)} icon files across {page-1} pages")
    return icon_files

def download_icon(file_info):
    """Download a single icon file"""
    filename = file_info['name']
    local_path = os.path.join(LOCAL_ICONS_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(local_path):
        return f"Skipped {filename} (already exists)"
    
    # Download the file
    url = f"{RAW_BASE_URL}/{filename}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return f"Downloaded {filename}"
        else:
            return f"Failed to download {filename}: {response.status_code}"
    except Exception as e:
        return f"Error downloading {filename}: {str(e)}"

def download_all_icons(icon_files):
    """Download all icons using thread pool"""
    print(f"\nStarting download of {len(icon_files)} icons...")
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all download tasks
        future_to_file = {executor.submit(download_icon, file_info): file_info for file_info in icon_files}
        
        # Process completed downloads
        for future in as_completed(future_to_file):
            result = future.result()
            print(result)
            
            if "Downloaded" in result:
                downloaded += 1
            elif "Skipped" in result:
                skipped += 1
            else:
                failed += 1
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nDownload complete!")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Total: {downloaded + skipped + failed}")

def create_icon_mapping():
    """Create a JSON mapping of icon numbers to filenames"""
    print("\nCreating icon mapping...")
    mapping = {}
    
    for filename in os.listdir(LOCAL_ICONS_DIR):
        if filename.endswith('.gif'):
            # Extract icon number from filename (e.g., 500.gif -> 500)
            try:
                icon_num = int(filename[:-4])  # Remove '.gif' suffix
                mapping[icon_num] = filename
            except ValueError:
                continue
    
    # Save mapping to JSON file
    mapping_path = os.path.join(LOCAL_ICONS_DIR, "icon_mapping.json")
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Created icon mapping with {len(mapping)} entries")
    print(f"Mapping saved to: {mapping_path}")

def main():
    """Main function"""
    print("EverQuest Item Icon Downloader")
    print("=" * 50)
    
    try:
        # Ensure directory exists
        ensure_dir_exists()
        
        # Get list of icons
        icon_files = get_icon_list()
        
        # Download all icons
        download_all_icons(icon_files)
        
        # Create icon mapping
        create_icon_mapping()
        
        print("\nAll done! Icons are ready to use.")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())