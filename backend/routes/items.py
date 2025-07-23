"""
Item management routes for EQDataScraper tooltip system.

This module provides API endpoints for:
- Individual item tooltip data
- Bulk item data fetching for inventory preloading
- Item formatting following Char Browser patterns
"""

from flask import Blueprint, request, jsonify
import pymysql
import logging
import sys
import os
import time
from collections import defaultdict

# Add the parent directory to Python path to import from app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import get_eqemu_db_connection

logger = logging.getLogger(__name__)

# Create blueprint for item routes
item_bp = Blueprint('items', __name__, url_prefix='/api')

# Simple rate limiting for tooltip requests
request_times = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 30
RATE_LIMIT_WINDOW = 60

# EQEmu item type mapping (following Char Browser pattern)
ITEM_TYPES = {
    0: 'Common Item',
    1: '1H Slashing',
    2: '2H Slashing', 
    3: '1H Piercing',
    4: '1H Blunt',
    5: '2H Blunt',
    7: 'Archery',
    8: 'Shield',
    10: 'Armor',
    11: 'Miscellaneous',
    14: 'Food',
    15: 'Drink',
    16: 'Light',
    17: 'Combinable',
    18: 'Bandage',
    19: 'Throwing',
    20: 'Spell',
    21: 'Potion',
    22: 'Wind Instrument',
    23: 'String Instrument',
    24: 'Brass Instrument',
    25: 'Drum',
    26: 'Arrow',
    27: 'Jewelry',
    29: 'Skill Tome',
    35: 'Note'
}

def format_item_tooltip(item_data):
    """Format raw database item data for tooltip display following Char Browser patterns."""
    if not item_data:
        return None
    
    # Calculate derived stats
    ratio = 0.0
    if item_data.get('damage') and item_data.get('delay'):
        ratio = round(item_data['damage'] / (item_data['delay'] / 10), 1)
    
    # Format weight (EQEmu stores as integer * 10)
    weight = (item_data.get('weight', 0) / 10) if item_data.get('weight') else 0
    
    return {
        'id': item_data.get('id'),
        'name': item_data.get('name') or item_data.get('Name', ''),
        'icon': item_data.get('icon', 500),
        
        # Combat stats
        'damage': item_data.get('damage', 0),
        'delay': item_data.get('delay', 0),
        'ratio': ratio,
        'ac': item_data.get('ac', 0),
        'attack': item_data.get('attack', 0),
        
        # Character stats
        'hp': item_data.get('hp', 0),
        'mana': item_data.get('mana', 0),
        'endur': item_data.get('endur', 0),
        
        # Attribute bonuses
        'astr': item_data.get('astr', 0),
        'asta': item_data.get('asta', 0),
        'aagi': item_data.get('aagi', 0),
        'adex': item_data.get('adex', 0),
        'awis': item_data.get('awis', 0),
        'aint': item_data.get('aint', 0),
        'acha': item_data.get('acha', 0),
        
        # Resistances
        'pr': item_data.get('pr', 0),       # Poison resist
        'mr': item_data.get('mr', 0),       # Magic resist
        'fr': item_data.get('fr', 0),       # Fire resist
        'cr': item_data.get('cr', 0),       # Cold resist
        'dr': item_data.get('dr', 0),       # Disease resist
        'svcorruption': item_data.get('svcorruption', 0),  # Corruption resist
        
        # Item properties
        'weight': weight,
        'itemtype': item_data.get('itemtype', 0),
        'itemtype_name': ITEM_TYPES.get(item_data.get('itemtype', 0), 'Unknown'),
        'stacksize': item_data.get('stacksize', 1),
        
        # Flags
        'magic': bool(item_data.get('magic', 0)),
        'lore': bool(item_data.get('lore', 0)),
        'nodrop': bool(item_data.get('nodrop', 0)),
        
        # Restrictions
        'classes': item_data.get('classes', 0),
        'races': item_data.get('races', 0),
        'deity': item_data.get('deity', 0),
        'slots': item_data.get('slots', 0),
        
        # Additional data
        'price': item_data.get('price', 0),
        'material': item_data.get('material', 0),
        'color': item_data.get('color', 0)
    }

def check_rate_limit():
    """Simple rate limiting by IP address"""
    client_ip = request.remote_addr or 'unknown'
    now = time.time()
    
    # Clean old requests (older than rate limit window)
    request_times[client_ip] = [req_time for req_time in request_times[client_ip] 
                               if now - req_time < RATE_LIMIT_WINDOW]
    
    # Check if rate limit exceeded
    if len(request_times[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        return True
    
    # Add current request time
    request_times[client_ip].append(now)
    return False

@item_bp.route('/items/<int:item_id>/tooltip', methods=['GET'])
def get_item_tooltip(item_id):
    """Get comprehensive item data for tooltips following Char Browser format."""
    
    # TEMPORARY: Disable tooltip API completely to prevent backend crashes
    # TODO: Re-enable once database connection pooling issues are resolved
    logger.info(f"Tooltip API temporarily disabled for item {item_id} to prevent crashes")
    return jsonify({
        'error': 'Tooltip API temporarily disabled to prevent server crashes',
        'message': 'Showing basic inventory data only',
        'item_id': item_id
    }), 503
    
    # Rate limiting check (disabled during maintenance)
    if check_rate_limit():
        logger.warning(f"Rate limit exceeded for IP {request.remote_addr} on item {item_id}")
        return jsonify({'error': 'Rate limit exceeded - too many requests'}), 429
    
    connection = None
    try:
        # Validate item_id
        if not item_id or item_id < 1:
            logger.warning(f"Invalid item ID: {item_id}")
            return jsonify({'error': 'Invalid item ID'}), 400
        
        conn, db_type, error = get_eqemu_db_connection()
        if error:
            logger.error(f"Database connection failed: {error}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        if not conn:
            logger.error("No database connection available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        connection = conn
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Following Char Browser column selection
            query = """
                SELECT id, Name, icon, ac, hp, mana, endur, attack, damage, delay,
                       weight, astr, asta, aagi, adex, awis, aint, acha,
                       pr, mr, fr, cr, dr, svcorruption,
                       classes, races, deity, slots, itemtype, price,
                       magic, nodrop, lore, stacksize, material, color
                FROM items 
                WHERE id = %s
            """
            cursor.execute(query, (item_id,))
            item = cursor.fetchone()
            
            if not item:
                return jsonify({'error': 'Item not found'}), 404
            
            # Format for tooltip display
            formatted_item = format_item_tooltip(item)
            logger.info(f"Retrieved tooltip data for item {item_id}: {item.get('Name', 'Unknown')}")
            
            return jsonify(formatted_item)
            
    except pymysql.Error as e:
        logger.error(f"Database error getting item tooltip {item_id}: {str(e)}")
        return jsonify({'error': 'Database query failed'}), 500
    except Exception as e:
        logger.error(f"Error getting item tooltip {item_id}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass  # Ignore connection close errors

@item_bp.route('/items/bulk', methods=['POST'])
def get_items_bulk():
    """Bulk fetch items for inventory tooltip preloading (Char Browser optimization)."""
    
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({'error': 'Item IDs required'}), 400
        
        item_ids = data['ids']
        
        if not item_ids or not isinstance(item_ids, list):
            return jsonify([])
        
        if len(item_ids) > 500:  # Prevent abuse
            return jsonify({'error': 'Too many items requested'}), 400
        
        conn, db_type, error = get_eqemu_db_connection()
        if error:
            logger.error(f"Database connection failed: {error}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        if not conn:
            logger.error("No database connection available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        connection = conn
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Single query for all items (Char Browser optimization pattern)
            placeholders = ','.join(['%s'] * len(item_ids))
            query = f"""
                SELECT id, Name, icon, ac, hp, mana, endur, attack, damage, delay,
                       weight, astr, asta, aagi, adex, awis, aint, acha,
                       pr, mr, fr, cr, dr, svcorruption,
                       classes, races, deity, slots, itemtype, price,
                       magic, nodrop, lore, stacksize, material, color
                FROM items 
                WHERE id IN ({placeholders})
            """
            
            cursor.execute(query, item_ids)
            items = cursor.fetchall()
            
            # Format all items for tooltips
            formatted_items = []
            for item in items:
                formatted_item = format_item_tooltip(item)
                if formatted_item:
                    formatted_items.append(formatted_item)
            
            logger.info(f"Retrieved bulk tooltip data for {len(formatted_items)} items")
            return jsonify(formatted_items)
            
    except Exception as e:
        logger.error(f"Error getting bulk items: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if connection:
            connection.close()

@item_bp.route('/items/<int:item_id>/details', methods=['GET'])
def get_item_details(item_id):
    """Get detailed item information (for item pages, not tooltips)."""
    
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if error:
            logger.error(f"Database connection failed: {error}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        if not conn:
            logger.error("No database connection available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        connection = conn
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # More comprehensive query for detail pages
            query = """
                SELECT * FROM items WHERE id = %s
            """
            cursor.execute(query, (item_id,))
            item = cursor.fetchone()
            
            if not item:
                return jsonify({'error': 'Item not found'}), 404
            
            # Convert to regular dict to ensure JSON serialization
            item_dict = dict(item)
            
            return jsonify(item_dict)
            
    except Exception as e:
        logger.error(f"Error getting item details {item_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if connection:
            connection.close()

@item_bp.route('/items/search', methods=['GET'])
def search_items():
    """Search items by name for tooltip system."""
    
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        limit = min(int(request.args.get('limit', 20)), 100)
        
        conn, db_type, error = get_eqemu_db_connection()
        if error:
            logger.error(f"Database connection failed: {error}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        if not conn:
            logger.error("No database connection available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        connection = conn
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            search_query = """
                SELECT id, Name, icon, itemtype
                FROM items 
                WHERE Name LIKE %s
                ORDER BY Name
                LIMIT %s
            """
            
            cursor.execute(search_query, (f'%{query}%', limit))
            items = cursor.fetchall()
            
            # Format for search results
            results = []
            for item in items:
                results.append({
                    'id': item['id'],
                    'name': item['Name'],
                    'icon': item['icon'],
                    'type': ITEM_TYPES.get(item['itemtype'], 'Unknown')
                })
            
            return jsonify(results)
            
    except Exception as e:
        logger.error(f"Error searching items: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if connection:
            connection.close()