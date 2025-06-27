from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime, timedelta
import logging
import time

# Add the parent directory to the path so we can import scrape_spells
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape_spells import scrape_class, CLASSES, CLASS_COLORS

app = Flask(__name__)
CORS(app)

# Data storage
spells_cache = {}
cache_timestamp = {}
CACHE_EXPIRY_HOURS = 24

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/api/spells/<class_name>', methods=['GET'])
def get_spells(class_name):
    """Get spells for a specific class"""
    try:
        # Normalize class name
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
        
        logger.info(f"Scraping fresh data for {class_name}")
        
        # Scrape the data with timeout
        start_time = time.time()
        df = scrape_class(class_name, 'https://alla.clumsysworld.com/', None)
        scrape_time = time.time() - start_time
        
        if df is None or df.empty:
            logger.error(f"No spells found for {class_name}")
            return jsonify({
                'error': f'No spells found for {class_name}',
                'suggestion': 'Try scraping all classes first'
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
        spells_cache[class_name] = spells
        cache_timestamp[class_name] = datetime.now().isoformat()
        
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cached_classes': len(spells_cache)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 