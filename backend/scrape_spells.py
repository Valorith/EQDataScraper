#!/usr/bin/env python3
import os
import time
import argparse
import logging
import tempfile
from typing import Dict, Optional, List

import requests
import pandas as pd
from bs4 import BeautifulSoup
from jinja2 import Template

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 🎯 Full list of classes with their type IDs
CLASSES: Dict[str, int] = {
    'Warrior': 1,
    'Cleric': 2,
    'Paladin': 3,
    'Ranger': 4,
    'ShadowKnight': 5,
    'Druid': 6,
    'Monk': 7,
    'Bard': 8,
    'Rogue': 9,
    'Shaman': 10,
    'Necromancer': 11,
    'Wizard': 12,
    'Magician': 13,
    'Enchanter': 14,
    'Beastlord': 15,
    'Berserker': 16,
}

# Basic colour theme for each class used in the generated HTML. This is far from
# accurate to the game's palette but provides a quick way to differentiate the
# pages when rendered.
CLASS_COLORS: Dict[str, str] = {
    'Warrior': '#8e2d2d',
    'Cleric': '#ccccff',
    'Paladin': '#ffd700',
    'Ranger': '#228b22',
    'ShadowKnight': '#551a8b',
    'Druid': '#a0522d',
    'Monk': '#556b2f',
    'Bard': '#ff69b4',
    'Rogue': '#708090',
    'Shaman': '#20b2aa',
    'Necromancer': '#8b008b',
    'Wizard': '#4169e1',
    'Magician': '#ff4500',
    'Enchanter': '#9370db',
    'Beastlord': '#b8860b',
    'Berserker': '#dc143c',
}

def scrape_class(class_name: str, base_url: str, output_file: Optional[str]) -> Optional[pd.DataFrame]:
    """Scrape spells for a specific class"""
    if class_name not in CLASSES:
        logger.error(f"Unknown class: {class_name}")
        return None
    
    type_id = CLASSES[class_name]
    url = f"{base_url}?a=spells&type={type_id}"
    
    logger.info(f"Scraping {class_name} spells from {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # First, get the search form page
        form_response = requests.get(url, headers=headers, timeout=30)
        form_response.raise_for_status()
        
        logger.info(f"Form page HTTP Status: {form_response.status_code}")
        
        # Parse the form to get any hidden fields or required parameters
        form_soup = BeautifulSoup(form_response.content, 'html.parser')
        
        # Use the correct URL format for alla.clumsysworld.com spell search
        search_urls = [
            f"{base_url}?a=spells&name=&type={type_id}&level=1&opt=2",
            f"{base_url}?a=spells&type={type_id}&level=1&opt=2",
            f"{base_url}?a=spells&type={type_id}&opt=2"
        ]
        
        response = None
        for search_url in search_urls:
            try:
                logger.info(f"Trying URL: {search_url}")
                response = requests.get(search_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    tables = soup.find_all('table')
                    
                    # Check if this URL returns spell data
                    spell_found = False
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:  # Has header + data rows
                            header_text = rows[0].get_text().lower()
                            # Look for spell-related content - table 3 has "Level: X" header and many rows
                            if (any(keyword in header_text for keyword in ['name', 'level', 'spell', 'mana', 'cast']) and len(rows) > 5) or \
                               ('level:' in header_text and len(rows) > 50):
                                spell_found = True
                                logger.info(f"Found spell data with URL: {search_url}")
                                break
                    
                    if spell_found:
                        break
                        
            except Exception as e:
                logger.warning(f"Failed to fetch {search_url}: {e}")
                continue
        
        if response is None:
            logger.error(f"All URL attempts failed for {class_name}")
            return None
        response.raise_for_status()
        
        logger.info(f"Search results HTTP Status: {response.status_code}")
        logger.info(f"Response length: {len(response.content)} bytes")
        logger.info(f"Content type: {response.headers.get('content-type', 'unknown')}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        
        logger.info(f"Found {len(tables)} tables")
        if tables:
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                logger.info(f"Table {i}: {len(rows)} rows")
                if rows:
                    header_text = rows[0].get_text(strip=True)[:100]
                    logger.info(f"Table {i} header: {header_text}")
        
        if not tables:
            logger.warning(f"No tables found for {class_name}")
            return None
        
        # Find the spell table - prioritize tables with "Level: X" pattern and many rows
        spell_table = None
        best_table_score = 0
        
        for table in tables:
            header_row = table.find('tr')
            if header_row:
                headers_text = header_row.get_text().lower()
                rows = table.find_all('tr')
                
                # Score tables: Level: X pattern with many rows gets highest score
                score = 0
                if 'level:' in headers_text and len(rows) > 50:
                    score = 100 + len(rows)  # High priority for Level: X tables
                elif any(keyword in headers_text for keyword in ['name', 'level', 'spell', 'mana', 'cast']) and len(rows) > 5:
                    score = 50 + len(rows)   # Medium priority for traditional headers
                
                if score > best_table_score:
                    best_table_score = score
                    spell_table = table
                    logger.info(f"New best table (score {score}): {headers_text[:50]}... ({len(rows)} rows)")
        
        if spell_table is not None:
            rows = spell_table.find_all('tr')
            logger.info(f"Final selected table: {len(rows)} rows")
        
        # Fallback to largest table if no spell table found
        if spell_table is None:
            if tables:
                spell_table = max(tables, key=lambda t: len(t.find_all('tr')))
            else:
                logger.warning(f"No tables found for {class_name}")
                return None
        
        rows = spell_table.find_all('tr')
        if len(rows) < 2:
            logger.warning(f"No spell data found for {class_name}")
            return None
        
        # Skip the header row and extract spell data
        # Actual columns: Icon, Name, Class-Level, Effects, Mana, Skill, Target, Spell ID
        data = []
        spell_count = 0
        
        for i, row in enumerate(rows[1:]):  # Skip header row
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 7:  # Ensure we have minimum expected columns
                try:
                    # Extract spell icon URL
                    icon_cell = cells[0]
                    icon_img = icon_cell.find('img')
                    icon_url = ''
                    if icon_img and icon_img.get('src'):
                        icon_src = icon_img.get('src')
                        if icon_src.startswith('/'):
                            icon_url = f"https://alla.clumsysworld.com{icon_src}"
                        elif not icon_src.startswith('http'):
                            icon_url = f"https://alla.clumsysworld.com/{icon_src}"
                        else:
                            icon_url = icon_src
                    
                    # Extract spell name and ID from link
                    name_cell = cells[1]
                    name_link = name_cell.find('a')
                    spell_name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)
                    
                    # Extract spell ID from the link href
                    spell_id = ''
                    if name_link and name_link.get('href'):
                        href = name_link.get('href')
                        # Extract ID from URL like "?a=spell&id=123"
                        import re
                        id_match = re.search(r'[?&]id=(\d+)', href)
                        if id_match:
                            spell_id = id_match.group(1)
                    
                    # Extract class and level from "Class Level" field (e.g., "Cleric 1")
                    class_level_text = cells[2].get_text(strip=True)
                    level = 0
                    import re
                    level_match = re.search(r'(\d+)$', class_level_text)
                    if level_match:
                        level = int(level_match.group(1))
                    
                    # Extract other fields - handling both 7 and 8 column layouts
                    if len(cells) == 8:
                        effects = cells[3].get_text(strip=True)
                        mana = cells[4].get_text(strip=True)
                        skill = cells[5].get_text(strip=True)
                        target_type = cells[6].get_text(strip=True)
                        spell_id_cell = cells[7].get_text(strip=True)
                        if not spell_id and spell_id_cell.isdigit():
                            spell_id = spell_id_cell
                    else:  # 7 columns
                        effects = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                        mana = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                        skill = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                        target_type = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                        spell_id_cell = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                        if not spell_id and spell_id_cell.isdigit():
                            spell_id = spell_id_cell
                    
                    # Only add valid spells (with name and level)
                    if spell_name and level > 0:
                        spell_data = {
                            'name': spell_name,
                            'level': level,
                            'mana': mana,
                            'spell_id': spell_id,
                            'icon': icon_url,
                            'skill': skill,
                            'target_type': target_type,
                            'effects': effects,
                        }
                        data.append(spell_data)
                        spell_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error parsing spell row: {e}")
                    continue
        
        if not data:
            logger.warning(f"No valid spell data extracted for {class_name}")
            return None
        
        # Convert to DataFrame with proper column names
        df = pd.DataFrame(data)
        logger.info(f"Successfully scraped {len(df)} spells for {class_name}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error scraping {class_name}: {e}")
        return None

def scrape_all(base_url: str, output_dir: Optional[str]):
    """Scrape all classes"""
    for class_name in CLASSES.keys():
        output_file = os.path.join(output_dir, f"{class_name}.html") if output_dir else None
        scrape_class(class_name, base_url, output_file)
        time.sleep(1)  # Be nice to the server