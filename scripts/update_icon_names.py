#!/usr/bin/env python3
"""
Script to update icon file names by removing the "item_" prefix
and updating the icon_mapping.json file accordingly.
"""

import os
import json
import shutil
from pathlib import Path

def update_icon_files():
    """Rename icon files and update the mapping JSON."""
    
    # Paths
    icons_dir = Path("public/icons/items")
    mapping_file = icons_dir / "icon_mapping.json"
    
    # Read the current mapping
    with open(mapping_file, 'r') as f:
        icon_mapping = json.load(f)
    
    print(f"Found {len(icon_mapping)} entries in icon mapping")
    
    # Get all PNG files with "item_" prefix
    item_files = list(icons_dir.glob("item_*.png"))
    print(f"Found {len(item_files)} PNG files with 'item_' prefix")
    
    # Track changes for the mapping
    mapping_updates = {}
    
    # Rename files and update mapping
    for item_file in item_files:
        # Extract the number from the filename (e.g., "item_1539.png" -> "1539")
        item_number = item_file.stem.replace("item_", "")
        
        # Create new filename
        new_filename = f"{item_number}.png"
        new_file_path = item_file.parent / new_filename
        
        # Check if target file already exists
        if new_file_path.exists():
            print(f"Warning: {new_filename} already exists, skipping {item_file.name}")
            continue
        
        # Rename the file
        try:
            item_file.rename(new_file_path)
            print(f"Renamed: {item_file.name} -> {new_filename}")
            
            # Update mapping if this number exists in the mapping
            if item_number in icon_mapping:
                old_value = icon_mapping[item_number]
                new_value = f"{item_number}.png"
                icon_mapping[item_number] = new_value
                mapping_updates[item_number] = (old_value, new_value)
                print(f"  Updated mapping: {item_number}: {old_value} -> {new_value}")
            else:
                # Add new entry to mapping
                icon_mapping[item_number] = f"{item_number}.png"
                print(f"  Added new mapping: {item_number}: {item_number}.png")
                
        except Exception as e:
            print(f"Error renaming {item_file.name}: {e}")
    
    # Also check for any GIF files that might need renaming
    gif_files = list(icons_dir.glob("item_*.gif"))
    print(f"Found {len(gif_files)} GIF files with 'item_' prefix")
    
    for gif_file in gif_files:
        item_number = gif_file.stem.replace("item_", "")
        new_filename = f"{item_number}.gif"
        new_file_path = gif_file.parent / new_filename
        
        if new_file_path.exists():
            print(f"Warning: {new_filename} already exists, skipping {gif_file.name}")
            continue
        
        try:
            gif_file.rename(new_file_path)
            print(f"Renamed: {gif_file.name} -> {new_filename}")
            
            # Update mapping
            if item_number in icon_mapping:
                old_value = icon_mapping[item_number]
                new_value = f"{item_number}.gif"
                icon_mapping[item_number] = new_value
                mapping_updates[item_number] = (old_value, new_value)
                print(f"  Updated mapping: {item_number}: {old_value} -> {new_value}")
            else:
                icon_mapping[item_number] = f"{item_number}.gif"
                print(f"  Added new mapping: {item_number}: {item_number}.gif")
                
        except Exception as e:
            print(f"Error renaming {gif_file.name}: {e}")
    
    # Update any remaining "item_" references in the mapping
    for icon_id, filename in list(icon_mapping.items()):
        if filename.startswith("item_"):
            new_filename = filename.replace("item_", "")
            icon_mapping[icon_id] = new_filename
            mapping_updates[icon_id] = (filename, new_filename)
            print(f"Updated mapping reference: {icon_id}: {filename} -> {new_filename}")
    
    # Write the updated mapping back to file, sorted by key numerically
    def numeric_key(k):
        try:
            return int(k)
        except ValueError:
            return float('inf')  # Put non-numeric keys at the end
    sorted_mapping = dict(sorted(icon_mapping.items(), key=lambda x: numeric_key(x[0])))
    with open(mapping_file, 'w') as f:
        json.dump(sorted_mapping, f, indent=2)
    
    print(f"\nSummary:")
    print(f"- Renamed {len(item_files) + len(gif_files)} files")
    print(f"- Updated {len(mapping_updates)} mapping entries")
    print(f"- Total mapping entries: {len(icon_mapping)}")
    print(f"- Updated mapping file: {mapping_file}")

if __name__ == "__main__":
    update_icon_files() 