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
        
        # Try different URL patterns to get spell data
        search_urls = [
            f"{base_url}?a=spells&class={class_name.lower()}",
            f"{base_url}?a=spells&iclass={type_id}",
            f"{base_url}?a=spells&classid={type_id}",
            f"{base_url}?a=spells&search=&iclass={type_id}&level_min=1&level_max=65",
            f"{base_url}?a=spell_list&class={type_id}",
            f"{base_url}spells/?class={type_id}",
            f"{base_url}spells.php?class={type_id}"
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
                            # Look for spell-related content in tables with multiple rows
                            if any(keyword in header_text for keyword in ['name', 'level', 'spell', 'mana', 'cast']) and len(rows) > 5:
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
        
        # Find the spell table - look for table with spell-related headers
        spell_table = None
        for table in tables:
            # Check if this table has spell-related headers
            header_row = table.find('tr')
            if header_row:
                headers_text = header_row.get_text().lower()
                if any(keyword in headers_text for keyword in ['name', 'level', 'spell', 'mana', 'cast']):
                    spell_table = table
                    break
        
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
        
        # Extract headers
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Extract data
        data = []
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                row_data = []
                for cell in cells[:len(headers)]:
                    text = cell.get_text(strip=True)
                    row_data.append(text)
                data.append(row_data)
        
        if not data:
            logger.warning(f"No spell data extracted for {class_name}")
            return None
        
        df = pd.DataFrame(data, columns=headers)
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