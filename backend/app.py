from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime, timedelta
import logging
import time

# Import scrape_spells from the same directory
from scrape_spells import scrape_class, CLASSES, CLASS_COLORS

app = Flask(__name__)
CORS(app)

# Load configuration
def load_config():
    """Load configuration from config.json and environment variables"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    default_config = {
        'backend_port': 5001,
        'frontend_port': 3000,
        'cache_expiry_hours': 24,
        'min_scrape_interval_minutes': 5
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = {**default_config, **json.load(f)}
        else:
            config = default_config
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading config.json: {e}. Using defaults.")
        config = default_config
    
    # Override with environment variables (Railway provides PORT)
    config['backend_port'] = int(os.getenv('PORT', os.getenv('BACKEND_PORT', config['backend_port'])))
    config['frontend_port'] = int(os.getenv('FRONTEND_PORT', config['frontend_port']))
    config['cache_expiry_hours'] = int(os.getenv('CACHE_EXPIRY_HOURS', config['cache_expiry_hours']))
    config['min_scrape_interval_minutes'] = int(os.getenv('MIN_SCRAPE_INTERVAL_MINUTES', config['min_scrape_interval_minutes']))
    
    return config

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Data storage
spells_cache = {}
cache_timestamp = {}
last_scrape_time = {}
CACHE_EXPIRY_HOURS = config['cache_expiry_hours']
MIN_SCRAPE_INTERVAL_MINUTES = config['min_scrape_interval_minutes']


def is_cache_expired(class_name):
    """Check if cache entry is expired"""
    if class_name not in cache_timestamp:
        return True
    
    cache_time = datetime.fromisoformat(cache_timestamp[class_name])
    expiry_time = cache_time + timedelta(hours=CACHE_EXPIRY_HOURS)
    return datetime.now() > expiry_time

def clear_expired_cache():
    """Remove expired cache entries"""
    expired_classes = []
    for class_name in list(cache_timestamp.keys()):
        if is_cache_expired(class_name):
            expired_classes.append(class_name)
    
    for class_name in expired_classes:
        spells_cache.pop(class_name, None)
        cache_timestamp.pop(class_name, None)
        logger.info(f"Cleared expired cache for {class_name}")

def can_scrape_class(class_name):
    """Check if enough time has passed since last scrape for rate limiting"""
    if class_name not in last_scrape_time:
        return True
    
    last_scrape = datetime.fromisoformat(last_scrape_time[class_name])
    min_interval = timedelta(minutes=MIN_SCRAPE_INTERVAL_MINUTES)
    return datetime.now() > last_scrape + min_interval

@app.route('/api/spells/<class_name>', methods=['GET'])
def get_spells(class_name):
    """Get spells for a specific class"""
    try:
        # Normalize class name - handle special cases
        class_name_lower = class_name.lower()
        
        # Map common variations to correct case
        class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
        
        if class_name_lower in class_name_map:
            class_name = class_name_map[class_name_lower]
        else:
            # Fallback to title case for unknown names
            class_name = class_name.title()
        
        if class_name not in CLASSES:
            logger.warning(f"Invalid class name requested: {class_name}")
            return jsonify({
                'error': f'Class {class_name} not found',
                'available_classes': list(CLASSES.keys())
            }), 404
        
        # Clear expired cache entries
        clear_expired_cache()
        
        # Check if we have valid cached data
        if class_name in spells_cache and not is_cache_expired(class_name):
            logger.info(f"Serving cached data for {class_name}")
            return jsonify({
                'spells': spells_cache[class_name],
                'cached': True,
                'last_updated': cache_timestamp[class_name]
            })
        
        # Check rate limiting before scraping
        if not can_scrape_class(class_name):
            time_since_last = datetime.now() - datetime.fromisoformat(last_scrape_time[class_name])
            wait_time = MIN_SCRAPE_INTERVAL_MINUTES - time_since_last.total_seconds() / 60
            logger.warning(f"Rate limited: {class_name} was scraped too recently. Wait {wait_time:.1f} minutes.")
            
            # Return stale cache if available, or error
            if class_name in spells_cache:
                return jsonify({
                    'spells': spells_cache[class_name],
                    'cached': True,
                    'stale': True,
                    'message': f'Using stale cache data. Please wait {wait_time:.1f} minutes before requesting fresh data.',
                    'last_updated': cache_timestamp[class_name]
                })
            else:
                return jsonify({
                    'error': f'Rate limited. Please wait {wait_time:.1f} minutes before trying again.',
                    'retry_after_minutes': wait_time
                }), 429
        
        logger.info(f"Scraping fresh data for {class_name}")
        
        # Scrape the data with timeout
        start_time = time.time()
        df = scrape_class(class_name, 'https://alla.clumsysworld.com/', None)
        scrape_time = time.time() - start_time
        
        if df is None or df.empty:
            logger.error(f"No spells found for {class_name} after trying all scraping methods")
            return jsonify({
                'error': f'No spells found for {class_name}',
                'suggestion': 'Check backend logs for scraping details',
                'message': 'Scraping unsuccessful - check alla.clumsysworld.com availability'
            }), 404
        
        # Convert DataFrame to list of dictionaries
        spells = []
        for _, row in df.iterrows():
            spell = {
                'name': row.get('Name', ''),
                'level': int(row.get('Level', 0)) if row.get('Level', '') else 0,
                'mana': row.get('Mana', ''),
                'skill': row.get('Skill', ''),
                'target_type': row.get('Target Type', ''),
                'spell_id': row.get('Spell ID', ''),
                'effects': row.get('Effect(s)', ''),
                'icon': row.get('Icon', '')
            }
            spells.append(spell)
        
        # Cache the data
        current_time = datetime.now().isoformat()
        spells_cache[class_name] = spells
        cache_timestamp[class_name] = current_time
        last_scrape_time[class_name] = current_time
        
        logger.info(f"Successfully scraped {len(spells)} spells for {class_name} in {scrape_time:.2f}s")
        
        return jsonify({
            'spells': spells,
            'cached': False,
            'last_updated': cache_timestamp[class_name],
            'scrape_time': round(scrape_time, 2),
            'spell_count': len(spells)
        })
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return jsonify({
            'error': 'Server configuration error',
            'details': 'Required modules not available'
        }), 500
    except ConnectionError as e:
        logger.error(f"Network error: {e}")
        return jsonify({
            'error': 'Unable to connect to data source',
            'details': 'Check network connection and try again'
        }), 503
    except Exception as e:
        logger.error(f"Unexpected error for {class_name}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e) if app.debug else 'An unexpected error occurred'
        }), 500

@app.route('/api/scrape-all', methods=['POST'])
def scrape_all_classes():
    """Scrape spells for all classes"""
    try:
        from scrape_spells import scrape_all
        
        # Clear cache
        spells_cache.clear()
        cache_timestamp.clear()
        
        # Scrape all classes
        scrape_all('https://alla.clumsysworld.com/', None)
        
        # Load the scraped data
        for class_name in CLASSES.keys():
            try:
                df = scrape_class(class_name, 'https://alla.clumsysworld.com/', None)
                if df is not None and not df.empty:
                    spells = []
                    for _, row in df.iterrows():
                        spell = {
                            'name': row.get('Name', ''),
                            'level': row.get('Level', ''),
                            'mana': row.get('Mana', ''),
                            'cast_time': row.get('Cast Time', ''),
                            'duration': row.get('Duration', ''),
                            'range': row.get('Range', ''),
                            'description': row.get('Description', '')
                        }
                        spells.append(spell)
                    
                    spells_cache[class_name] = spells
                    cache_timestamp[class_name] = datetime.now().isoformat()
            except Exception as e:
                print(f"Error scraping {class_name}: {e}")
        
        return jsonify({
            'message': 'All classes scraped successfully',
            'classes_scraped': list(spells_cache.keys()),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get list of all available classes"""
    classes = []
    for name, class_id in CLASSES.items():
        classes.append({
            'name': name,
            'id': class_id,
            'color': CLASS_COLORS.get(name, '#9370db')
        })
    
    return jsonify(classes)

@app.route('/api/cache-status', methods=['GET'])
def get_cache_status():
    """Get cache status for all classes"""
    status = {}
    for class_name in CLASSES.keys():
        status[class_name] = {
            'cached': class_name in spells_cache,
            'spell_count': len(spells_cache.get(class_name, [])),
            'last_updated': cache_timestamp.get(class_name)
        }
    
    return jsonify(status)

@app.route('/api/spell-details/<int:spell_id>', methods=['GET'])
def get_spell_details(spell_id):
    """Get detailed spell information from alla website"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        url = f'https://alla.clumsysworld.com/?a=spell&id={spell_id}'
        logger.info(f"Fetching spell details for ID {spell_id} from {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        details = parse_spell_details_from_html(soup)
        
        logger.info(f"Successfully parsed spell details for ID {spell_id}")
        return jsonify(details)
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching spell details for ID {spell_id}")
        return jsonify({'error': 'Request timed out'}), 504
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for spell ID {spell_id}: {e}")
        return jsonify({'error': 'Unable to connect to spell database'}), 503
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for spell ID {spell_id}")
        if e.response.status_code == 404:
            return jsonify({'error': 'Spell not found'}), 404
        return jsonify({'error': f'Server error ({e.response.status_code})'}), e.response.status_code
    except Exception as e:
        logger.error(f"Unexpected error fetching spell details for ID {spell_id}: {e}")
        return jsonify({'error': 'Failed to fetch spell details'}), 500

def enhance_reagents_with_icons(components):
    """Enhance reagent components with icons from their individual item pages"""
    import requests
    from bs4 import BeautifulSoup
    
    if not components:
        return components
    
    enhanced_components = []
    
    for reagent in components:
        try:
            # Skip if no item_id or if icon is already present
            if not reagent.get('item_id') or reagent.get('icon'):
                enhanced_components.append(reagent)
                continue
                
            item_id = reagent['item_id']
            
            # Fetch the item page to get the icon
            item_url = f'https://alla.clumsysworld.com/?a=item&id={item_id}'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            
            response = requests.get(item_url, headers=headers, timeout=10)
            if response.status_code == 200:
                item_soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for the item icon - typically the first image in the item details
                item_icon = None
                
                # Try to find icon in common locations
                for img in item_soup.find_all('img'):
                    src = img.get('src', '')
                    if ('icon' in src.lower() or 'item_' in src) and src.endswith('.png'):
                        if src.startswith('/'):
                            item_icon = f"https://alla.clumsysworld.com{src}"
                        elif not src.startswith('http'):
                            item_icon = f"https://alla.clumsysworld.com/{src}"
                        else:
                            item_icon = src
                        break
                
                # Add icon if found
                if item_icon:
                    reagent['icon'] = item_icon
                    logger.info(f"Found icon for reagent {reagent['name']}: {item_icon}")
                else:
                    logger.debug(f"No icon found for reagent {reagent['name']}")
            else:
                logger.warning(f"Failed to fetch item page for {reagent['name']} (status: {response.status_code})")
                
        except Exception as e:
            logger.warning(f"Error fetching icon for reagent {reagent.get('name', 'unknown')}: {e}")
        
        enhanced_components.append(reagent)
    
    return enhanced_components

def parse_spell_details_from_html(soup):
    """Parse spell details from the HTML soup object"""
    details = {}
    
    try:
        # Look for tables containing spell information
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if label and value and value != '-':
                        # Map common spell attributes
                        if 'cast time' in label or 'casting time' in label:
                            details['cast_time'] = value
                        elif 'duration' in label:
                            details['duration'] = value
                        elif 'range' in label:
                            details['range'] = value
                        elif 'resist' in label:
                            details['resist'] = value
                        elif 'description' in label:
                            details['description'] = value
                        elif 'recast' in label or 'recast time' in label:
                            details['recast_time'] = value
                        elif 'skill' in label:
                            details['skill'] = value
                        elif 'target' in label:
                            details['target_type'] = value
        
        # Look for spell effects in different possible locations
        effects = []
        
        # First, try to find the specific "Spell Effects" section
        spell_effects_header = None
        for header in soup.find_all('h2', class_='section_header'):
            if header.get_text(strip=True) == 'Spell Effects':
                spell_effects_header = header
                break
        
        if spell_effects_header:
            # Look for the parent table cell that contains the effects
            effects_container = spell_effects_header.find_parent('td')
            if effects_container:
                # Find all <ul> elements that contain effect information
                effect_lists = effects_container.find_all('ul')
                for ul in effect_lists:
                    effect_text = ul.get_text(strip=True)
                    if effect_text and 'Effect type' in effect_text:
                        # Clean up the effect text
                        cleaned_effect = effect_text.replace('Effect type :', '').replace('Effect type:', '').strip()
                        if cleaned_effect and len(cleaned_effect) > 5 and cleaned_effect not in effects:
                            effects.append(cleaned_effect)
        
        # Alternative approach: look for <ul> elements with effect information
        if not effects:
            for ul in soup.find_all('ul'):
                # Look for <b> tags containing effect numbers and types
                b_tags = ul.find_all('b')
                for b_tag in b_tags:
                    b_text = b_tag.get_text(strip=True)
                    if 'Effect type' in b_text and ':' in b_text:
                        # Get the parent <ul> element to extract the full effect text
                        ul_text = ul.get_text(strip=True)
                        # Extract everything after "Effect type :"
                        if 'Effect type :' in ul_text:
                            effect_desc = ul_text.split('Effect type :')[-1].strip()
                            if effect_desc and len(effect_desc) > 5 and effect_desc not in effects:
                                effects.append(effect_desc)
        
        # Fallback: Try to find effect text in various elements
        if not effects:
            for element in soup.find_all(['td', 'div', 'p']):
                text = element.get_text(strip=True)
                
                # Look for effect-like text patterns
                if (text and len(text) > 10 and 
                    any(keyword in text.lower() for keyword in [
                        'increase', 'decrease', 'damage', 'heal', 'restore', 
                        'drain', 'buff', 'debuff', 'summon', 'teleport',
                        'effect:', 'slot 1:', 'slot 2:', 'slot 3:'
                    ])):
                    # Clean up the text
                    cleaned_text = ' '.join(text.split())
                    if cleaned_text not in effects and len(cleaned_text) < 200:
                        effects.append(cleaned_text)
        
        if effects:
            details['effects'] = effects[:5]  # Limit to 5 effects to avoid clutter
        
        # Look for spell components/reagents
        components = []
        
        # Look for table rows with reagent information
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label_cell = cells[0]
                    value_cell = cells[1]
                    
                    label_text = label_cell.get_text(strip=True).lower()
                    
                    # Check if this row contains reagent information
                    if 'reagent' in label_text or 'component' in label_text:
                        # Extract reagent information from the value cell
                        reagent_info = {}
                        
                        # Look for links to items (reagent names)
                        links = value_cell.find_all('a')
                        if links:
                            for link in links:
                                href = link.get('href', '')
                                reagent_name = link.get_text(strip=True)
                                
                                if href and reagent_name:
                                    # Build full URL for the reagent
                                    if href.startswith('?'):
                                        reagent_url = f"https://alla.clumsysworld.com/{href}"
                                    else:
                                        reagent_url = href
                                    
                                    reagent_info['name'] = reagent_name
                                    reagent_info['url'] = reagent_url
                                    
                                    # Look for an icon in the same row/cell
                                    parent_cell = link.find_parent(['td', 'div'])
                                    if parent_cell:
                                        icon_img = parent_cell.find('img')
                                        if icon_img and icon_img.get('src'):
                                            icon_src = icon_img.get('src')
                                            if icon_src.startswith('/'):
                                                reagent_info['icon'] = f"https://alla.clumsysworld.com{icon_src}"
                                            elif not icon_src.startswith('http'):
                                                reagent_info['icon'] = f"https://alla.clumsysworld.com/{icon_src}"
                                            else:
                                                reagent_info['icon'] = icon_src
                                    
                                    # Extract item ID from href if possible
                                    import re
                                    reagent_id_match = re.search(r'id=(\d+)', href)
                                    if reagent_id_match:
                                        reagent_info['item_id'] = int(reagent_id_match.group(1))
                        
                        # Extract quantity from the cell text
                        cell_text = value_cell.get_text(strip=True)
                        # Look for quantity in parentheses like "(1)" or "(5)"
                        import re
                        quantity_match = re.search(r'\((\d+)\)', cell_text)
                        if quantity_match:
                            reagent_info['quantity'] = int(quantity_match.group(1))
                        
                        # If we have reagent information, add it to components
                        if reagent_info.get('name'):
                            components.append(reagent_info)
        
        if components:
            details['components'] = components
            
            # Enhance reagents with icons from their item pages (lightweight approach)
            details['components'] = enhance_reagents_with_icons(details['components'])
        
        # Look for "Items with spell" section
        items_with_spell = []
        
        # Find the "Items with spell" header or similar text
        items_header = None
        for element in soup.find_all(['h2', 'h3', 'th', 'td', 'b', 'strong']):
            element_text = element.get_text(strip=True).lower()
            if 'items with spell' in element_text or 'items with this spell' in element_text:
                items_header = element
                break
        
        if items_header:
            # Find the table or container that follows the header
            current = items_header
            while current:
                current = current.find_next()
                if not current:
                    break
                
                # Look for links that might be items
                if hasattr(current, 'find_all'):
                    item_links = current.find_all('a', href=True)
                    
                    for link in item_links:
                        href = link.get('href', '')
                        item_name = link.get_text(strip=True)
                        
                        # Check if this looks like an item link
                        if ('a=item' in href and item_name and 
                            len(item_name) > 2 and item_name != 'Items with spell'):
                            
                            item_info = {
                                'name': item_name,
                                'url': href if href.startswith('http') else f"https://alla.clumsysworld.com/{href.lstrip('/')}"
                            }
                            
                            # Look for an icon in the same row/cell
                            parent_cell = link.find_parent(['td', 'div'])
                            if parent_cell:
                                icon_img = parent_cell.find('img')
                                if icon_img and icon_img.get('src'):
                                    icon_src = icon_img.get('src')
                                    if icon_src.startswith('/'):
                                        item_info['icon'] = f"https://alla.clumsysworld.com{icon_src}"
                                    elif not icon_src.startswith('http'):
                                        item_info['icon'] = f"https://alla.clumsysworld.com/{icon_src}"
                                    else:
                                        item_info['icon'] = icon_src
                            
                            # Extract item ID from href if possible
                            import re
                            id_match = re.search(r'id=(\d+)', href)
                            if id_match:
                                item_info['item_id'] = int(id_match.group(1))
                            
                            items_with_spell.append(item_info)
                
                # Stop if we've found items or hit another major section
                if items_with_spell and len(items_with_spell) > 10:
                    break
                    
                # Stop if we hit another section header
                if (hasattr(current, 'get_text') and current.name in ['h2', 'h3'] and 
                    current != items_header and 'items with spell' not in current.get_text(strip=True).lower()):
                    break
        
        if items_with_spell:
            details['items_with_spell'] = items_with_spell[:20]  # Limit to 20 items to avoid clutter
            
        # If we didn't find much detail, try to get basic description from title or headers
        if not details.get('description'):
            title_element = soup.find('title')
            if title_element:
                title_text = title_element.get_text(strip=True)
                if 'spell' in title_text.lower():
                    details['description'] = title_text
                    
        logger.info(f"Parsed spell details: {list(details.keys())}")
        return details
        
    except Exception as e:
        logger.error(f"Error parsing spell details: {e}")
        return {'description': 'Spell information available on alla website'}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cached_classes': len(spells_cache)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=config['backend_port']) 