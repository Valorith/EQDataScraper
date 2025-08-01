"""
Character management routes for EQDataScraper.

This module provides API endpoints for:
- Character search by name
- Character data retrieval from EQEmu database
- User main character preferences (Primary/Secondary)
- Character inventory, currency, and calculated stats

All endpoints integrate with the EQEmu database schema as documented in
CHARACTER_DATA_STRUCTURE.md and USER_CHARACTER_SCHEMA.md.
"""

from flask import Blueprint, request, jsonify, g
from utils.security import sanitize_search_input, rate_limit_by_ip
import logging
import os
import pymysql
import psycopg2
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint for character routes
character_bp = Blueprint('character', __name__, url_prefix='/api')

@character_bp.route('/characters/test', methods=['GET'])
def test_characters():
    """Simple test endpoint to verify character routes are working."""
    return jsonify({'status': 'Character routes are working!', 'test': True}), 200

# Environment configuration
ENABLE_USER_ACCOUNTS = os.environ.get('ENABLE_USER_ACCOUNTS', 'false').lower() == 'true'
DEV_MODE_AUTH_BYPASS = (
    os.environ.get('ENABLE_DEV_AUTH') == 'true' and 
    os.environ.get('FLASK_ENV') != 'production'
)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')  # PostgreSQL for user accounts
EQEMU_DATABASE_URL = None  # MySQL for EQEmu character data

# Load EQEmu database configuration from config.json or environment
try:
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
        EQEMU_DATABASE_URL = config.get('production_database_url', '')
        logger.info("Loaded EQEmu database URL from config.json")
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.info(f"No config.json found or invalid: {e}")
    # Fallback to environment variable for EQEmu database
    EQEMU_DATABASE_URL = os.environ.get('EQEMU_DATABASE_URL', '')

if EQEMU_DATABASE_URL:
    logger.info("EQEmu database configured for character data")
else:
    logger.warning("No EQEmu database configured - character endpoints will use mock data")

# EQEmu class ID to name mapping
CLASS_NAMES = {
    1: 'Warrior', 2: 'Cleric', 3: 'Paladin', 4: 'Ranger', 5: 'Shadow Knight',
    6: 'Druid', 7: 'Monk', 8: 'Bard', 9: 'Rogue', 10: 'Shaman',
    11: 'Necromancer', 12: 'Wizard', 13: 'Magician', 14: 'Enchanter',
    15: 'Beastlord', 16: 'Berserker'
}

# EQEmu race ID to name mapping
RACE_NAMES = {
    1: 'Human', 2: 'Barbarian', 3: 'Erudite', 4: 'Wood Elf', 5: 'High Elf',
    6: 'Dark Elf', 7: 'Half Elf', 8: 'Dwarf', 9: 'Troll', 10: 'Ogre',
    11: 'Halfling', 12: 'Gnome', 128: 'Iksar', 130: 'Vah Shir', 330: 'Froglok',
    522: 'Drakkin'
}

def _format_timestamp(timestamp):
    """Helper function to format timestamp/datetime to ISO format string."""
    if timestamp is None:
        return None
    
    # Handle Unix timestamp (integer)
    if isinstance(timestamp, (int, float)):
        try:
            return datetime.fromtimestamp(timestamp).isoformat()
        except (ValueError, OSError):
            return None
    
    # Handle datetime object
    if hasattr(timestamp, 'isoformat'):
        return timestamp.isoformat()
    
    # Handle string
    if isinstance(timestamp, str):
        return timestamp
    
    return None

# Note: get_eqemu_connection() function removed - now using get_eqemu_db_connection() from app.py
# This ensures all routes use the same proven database connection method

def get_user_db_connection():
    """Get connection to user accounts PostgreSQL database with enhanced error handling."""
    # Check if user accounts are enabled
    if not ENABLE_USER_ACCOUNTS:
        logger.info("User accounts disabled - ENABLE_USER_ACCOUNTS not set to true")
        return None
        
    # Check if DATABASE_URL is configured
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured for user accounts")
        logger.error("Production environment variables may not be properly set")
        return None
        
    try:
        # Log connection attempt for debugging
        logger.info(f"Attempting PostgreSQL connection for user accounts...")
        logger.debug(f"DATABASE_URL starts with: {DATABASE_URL[:20]}...")
        
        connection = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        connection.autocommit = True
        
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
        logger.info("✅ User database connection successful")
        return connection
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        logger.error("This usually means:")
        logger.error("1. DATABASE_URL is incorrect")
        logger.error("2. PostgreSQL server is not accessible")
        logger.error("3. Network connectivity issues")
        return None
        
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to user database: {type(e).__name__}: {e}")
        logger.error("Check production environment configuration")
        return None

def require_auth():
    """Check if user is authenticated (unless in dev mode)."""
    if DEV_MODE_AUTH_BYPASS:
        return True
    
    # Check for valid JWT token or session
    # This would integrate with the existing auth system
    # For now, return True in dev mode
    return True

def get_current_user_id():
    """Get current user ID from session/token."""
    if DEV_MODE_AUTH_BYPASS:
        return "dev_user"
    
    # Extract user ID from JWT token or session
    # This would integrate with the existing auth system
    return "dev_user"

@character_bp.route('/database/status', methods=['GET'])
def check_database_status():
    """
    Check the status of the EQEmu database connection.
    
    Returns:
    - Database connection status and configuration info
    """
    try:
        from app import get_eqemu_db_connection
        from utils.db_config_manager import db_config_manager
        
        # Get configuration status
        config = db_config_manager.get_config()
        config_status = {
            'configured': config is not None and config.get('production_database_url') is not None,
            'database_type': config.get('database_type', 'unknown') if config else 'not_set',
            'database_host': config.get('database_host', 'not_set') if config else 'not_set',
            'database_name': config.get('database_name', 'not_set') if config else 'not_set',
            'ssl_enabled': config.get('database_ssl', False) if config else False,
            'config_source': config.get('config_source', 'unknown') if config else 'unknown'
        }
        
        # Test connection
        connection, db_type, error = get_eqemu_db_connection()
        if connection:
            connection.close()
            connection_status = {
                'connected': True,
                'database_type': db_type,
                'error': None
            }
        else:
            connection_status = {
                'connected': False,
                'database_type': None,
                'error': str(error) if error else 'Unknown connection error'
            }
        
        return jsonify({
            'config': config_status,
            'connection': connection_status,
            'status': 'ok' if connection_status['connected'] else 'error'
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return jsonify({
            'error': 'Failed to check database status',
            'message': str(e)
        }), 500

@character_bp.route('/characters/search', methods=['GET'])
def search_characters():
    """
    Search for characters by name in the EQEmu database.
    
    Query Parameters:
    - name: Character name to search for (partial matches supported)
    - limit: Maximum number of results (default: 10, max: 50)
    
    Returns:
    - List of characters with basic information (id, name, level, class, race)
    """
    try:
        # Get and validate parameters
        name = request.args.get('name', '').strip()
        limit = min(int(request.args.get('limit', 5)), 50)  # Allow up to 50 matches for pagination
        
        if not name or len(name) < 2:
            return jsonify({'error': 'Name parameter must be at least 2 characters'}), 400
        
        # Sanitize search input
        name = sanitize_search_input(name)
        
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for character search: {error}")
            logger.error("This usually means the content database is not configured properly")
            
            # Provide helpful error message for users
            if "Database not configured" in str(error):
                return jsonify({
                    'error': 'Content database not configured',
                    'message': 'The EverQuest content database connection has not been set up. Please contact an administrator to configure the database connection through the admin panel.',
                    'code': 'DB_NOT_CONFIGURED'
                }), 503
            else:
                return jsonify({
                    'error': 'Database connection unavailable',
                    'message': 'Unable to connect to the EverQuest database. Please try again later.',
                    'code': 'DB_CONNECTION_FAILED'
                }), 503
        
        # Search characters in database
        with connection.cursor() as cursor:
            query = """
                SELECT id, name, level, class, race, last_login
                FROM character_data 
                WHERE name LIKE %s 
                AND name NOT LIKE '%%-deleted-%%'
                ORDER BY last_login DESC, level DESC
                LIMIT %s
            """
            cursor.execute(query, (f"%{name}%", limit))
            results = cursor.fetchall()
            
            characters = []
            for row in results:
                # Handle both dictionary and tuple cursor results
                if isinstance(row, dict):
                    characters.append({
                        'id': row['id'],
                        'name': row['name'],
                        'level': row['level'],
                        'class': CLASS_NAMES.get(row['class'], 'Unknown'),
                        'race': RACE_NAMES.get(row['race'], 'Unknown'),
                        'lastLogin': _format_timestamp(row['last_login']) if row['last_login'] else None
                    })
                else:
                    characters.append({
                        'id': row[0],
                        'name': row[1],
                        'level': row[2],
                        'class': CLASS_NAMES.get(row[3], 'Unknown'),
                        'race': RACE_NAMES.get(row[4], 'Unknown'),
                        'lastLogin': _format_timestamp(row[5]) if row[5] else None
                    })
        
        connection.close()
        return jsonify(characters), 200
        
    except Exception as e:
        logger.error(f"Error searching characters: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/characters/<int:character_id>', methods=['GET'])
def get_character(character_id):
    """
    Get detailed character information by ID.
    
    Returns:
    - Complete character data from character_data table
    """
    try:
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for character details: {error}")
            logger.error("This usually means the content database is not configured properly")
            return jsonify({'error': 'Database connection unavailable'}), 503
        
        # Get character data from database
        with connection.cursor() as cursor:
            query = """
                SELECT id, name, level, class, race, gender, deity, cur_hp, mana, endurance,
                       `str`, sta, agi, dex, wis, `int`, cha, zone_id, x, y, z, heading,
                       exp, aa_exp, aa_points, birthday, last_login, time_played, pvp_status,
                       face, hair_color, hair_style, beard, beard_color, eye_color_1, eye_color_2
                FROM character_data 
                WHERE id = %s
            """
            cursor.execute(query, (character_id,))
            result = cursor.fetchone()
            
            if not result:
                connection.close()
                return jsonify({'error': 'Character not found'}), 404
            
            # Handle both dictionary and tuple cursor results
            if isinstance(result, dict):
                character = {
                    'id': result['id'],
                    'name': result['name'],
                    'level': result['level'],
                    'class': CLASS_NAMES.get(result['class'], 'Unknown'),
                    'race': RACE_NAMES.get(result['race'], 'Unknown'),
                    'gender': result['gender'],
                    'deity': result['deity'],
                    'cur_hp': result['cur_hp'],
                    'mana': result['mana'],
                    'endurance': result['endurance'],
                    'str': result['str'],
                    'sta': result['sta'],
                    'agi': result['agi'],
                    'dex': result['dex'],
                    'wis': result['wis'],
                    'int': result['int'],
                    'cha': result['cha'],
                    'zone_id': result['zone_id'],
                    'x': result['x'],
                    'y': result['y'],
                    'z': result['z'],
                    'heading': result['heading'],
                    'exp': result['exp'],
                    'aa_exp': result['aa_exp'],
                    'aa_points': result['aa_points'],
                    'birthday': _format_timestamp(result['birthday']) if result['birthday'] else None,
                    'last_login': _format_timestamp(result['last_login']) if result['last_login'] else None,
                    'time_played': result['time_played'],
                    'pvp_status': result['pvp_status'],
                    'appearance': {
                        'face': result['face'],
                        'hair_color': result['hair_color'],
                        'hair_style': result['hair_style'],
                        'beard': result['beard'],
                        'beard_color': result['beard_color'],
                        'eye_color_1': result['eye_color_1'],
                        'eye_color_2': result['eye_color_2']
                    }
                }
            else:
                character = {
                    'id': result[0],
                    'name': result[1],
                    'level': result[2],
                    'class': CLASS_NAMES.get(result[3], 'Unknown'),
                    'race': RACE_NAMES.get(result[4], 'Unknown'),
                    'gender': result[5],
                    'deity': result[6],
                    'cur_hp': result[7],
                    'mana': result[8],
                    'endurance': result[9],
                    'str': result[10],
                    'sta': result[11],
                    'agi': result[12],
                    'dex': result[13],
                    'wis': result[14],
                    'int': result[15],
                    'cha': result[16],
                    'zone_id': result[17],
                    'x': result[18],
                    'y': result[19],
                    'z': result[20],
                    'heading': result[21],
                    'exp': result[22],
                    'aa_exp': result[23],
                    'aa_points': result[24],
                    'birthday': _format_timestamp(result[25]) if result[25] else None,
                    'last_login': _format_timestamp(result[26]) if result[26] else None,
                    'time_played': result[27],
                    'pvp_status': result[28],
                    'appearance': {
                        'face': result[29],
                        'hair_color': result[30],
                        'hair_style': result[31],
                        'beard': result[32],
                        'beard_color': result[33],
                        'eye_color_1': result[34],
                        'eye_color_2': result[35]
                    }
                }
        
        connection.close()
        return jsonify(character), 200
        
    except Exception as e:
        logger.error(f"Error getting character {character_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/characters/<int:character_id>/inventory', methods=['GET'])
def get_character_inventory(character_id):
    """
    Get character's inventory items.
    
    Returns:
    - Character inventory with item details
    """
    connection = None
    cursor = None
    
    # Add basic validation
    if not character_id or character_id <= 0:
        return jsonify({'error': 'Invalid character ID'}), 400
        
    try:
        logger.info(f"Starting inventory request for character {character_id}")
        
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for character {character_id}: {error}")
            return jsonify({'error': 'Database connection unavailable - please try again later'}), 503
            
        logger.info(f"Connection obtained for character {character_id}, proceeding with queries")
        
        # Get equipped items data with timeout and error handling
        cursor = connection.cursor()
        equipment = {}
        inventory = []
        
        try:
            # Get equipped items (slots 0-22 are equipment slots) - optimized query
            equipment_query = """
                SELECT inv.slotid, inv.itemid, inv.charges, inv.color, inv.instnodrop,
                       inv.augslot1, inv.augslot2, inv.augslot3, inv.augslot4, inv.augslot5, inv.augslot6,
                       inv.ornamenticon, inv.ornamentidfile, inv.ornament_hero_model,
                       items.Name, items.icon, items.ac, items.hp, items.mana, items.endur, items.attack,
                       items.astr, items.asta, items.aagi, items.adex, items.awis, items.aint, items.acha,
                       items.pr, items.mr, items.fr, items.cr, items.dr, items.svcorruption,
                       items.weight, items.itemtype, items.slots
                FROM inventory inv
                LEFT JOIN items ON inv.itemid = items.id
                WHERE inv.charid = %s AND inv.slotid BETWEEN 0 AND 22
                ORDER BY inv.slotid
                LIMIT 23
            """
            
            logger.info(f"Executing equipment query for character {character_id}")
            cursor.execute(equipment_query, (character_id,))
            equipment_results = cursor.fetchall()
            logger.info(f"Equipment query returned {len(equipment_results)} results")
            
            # Map slot IDs to slot names (EQEmu standard)
            slot_mapping = {
                0: 'charm', 1: 'ear1', 2: 'head', 3: 'face', 4: 'ear2',
                5: 'neck', 6: 'shoulder', 7: 'arms', 8: 'back', 9: 'wrist1',
                10: 'wrist2', 11: 'range', 12: 'hands', 13: 'primary',
                14: 'secondary', 15: 'ring1', 16: 'ring2', 17: 'chest',
                18: 'legs', 19: 'feet', 20: 'waist', 21: 'power_source', 22: 'ammo'
            }
            
            equipment = {}
            for row in equipment_results:
                # Handle both dictionary (DictCursor) and tuple cursor results
                if isinstance(row, dict):
                    itemid = row.get('itemid')
                    if itemid:
                        slot_name = slot_mapping.get(row.get('slotid'))
                        if slot_name:
                            equipment[slot_name] = {
                                'id': row.get('itemid'),
                                'name': row.get('Name') or f'Item {itemid}',
                                'icon': row.get('icon') or 500,
                                'charges': row.get('charges') or 0,
                                'color': row.get('color') or 0,
                                'isNoDrop': not bool(row.get('instnodrop')),
                                'stats': {
                                    'ac': row.get('ac') or 0,
                                    'hp': row.get('hp') or 0,
                                    'mana': row.get('mana') or 0,
                                    'endur': row.get('endur') or 0,
                                    'attack': row.get('attack') or 0
                                },
                                'attributes': {
                                    'str': row.get('astr') or 0,
                                    'sta': row.get('asta') or 0,
                                    'agi': row.get('aagi') or 0,
                                    'dex': row.get('adex') or 0,
                                    'wis': row.get('awis') or 0,
                                    'int': row.get('aint') or 0,
                                    'cha': row.get('acha') or 0
                                },
                                'resistances': {
                                    'poison': row.get('pr') or 0,
                                    'magic': row.get('mr') or 0,
                                    'fire': row.get('fr') or 0,
                                    'cold': row.get('cr') or 0,
                                    'disease': row.get('dr') or 0,
                                    'corruption': row.get('svcorruption') or 0
                                },
                                'weight': row.get('weight') or 0,
                                'augments': [
                                    row.get('augslot1'), row.get('augslot2'), row.get('augslot3'),
                                    row.get('augslot4'), row.get('augslot5'), row.get('augslot6')
                                ],
                                'ornament': {
                                    'icon': row.get('ornamenticon') or 0,
                                    'idfile': row.get('ornamentidfile') or 0,
                                    'hero_model': row.get('ornament_hero_model') or 0
                                }
                            }
                else:
                    # Fallback for tuple cursor results
                    if row[1]:  # itemid exists
                        slot_name = slot_mapping.get(row[0])
                        if slot_name:
                            equipment[slot_name] = {
                                'id': row[1],
                                'name': row[14] or f'Item {row[1]}',
                                'icon': row[15] or 500,
                                'charges': row[2] or 0,
                                'color': row[3] or 0,
                                'isNoDrop': not bool(row[4]),
                                'stats': {
                                    'ac': row[16] or 0,
                                    'hp': row[17] or 0,
                                    'mana': row[18] or 0,
                                    'endur': row[19] or 0,
                                    'attack': row[20] or 0
                                },
                                'attributes': {
                                    'str': row[21] or 0,
                                    'sta': row[22] or 0,
                                    'agi': row[23] or 0,
                                    'dex': row[24] or 0,
                                    'wis': row[25] or 0,
                                    'int': row[26] or 0,
                                    'cha': row[27] or 0
                                },
                                'resistances': {
                                    'poison': row[28] or 0,
                                    'magic': row[29] or 0,
                                    'fire': row[30] or 0,
                                    'cold': row[31] or 0,
                                    'disease': row[32] or 0,
                                    'corruption': row[33] or 0
                                },
                                'weight': row[34] or 0,
                                'augments': [
                                    row[5], row[6], row[7], row[8], row[9], row[10]
                                ],
                                'ornament': {
                                    'icon': row[11] or 0,
                                    'idfile': row[12] or 0,
                                    'hero_model': row[13] or 0
                                }
                            }
        
            # Get inventory data (main bag slots 23-32 + ALL bag contents 251-361) 
            inventory_query = """
                SELECT inv.slotid, inv.itemid, inv.charges, inv.color, inv.instnodrop,
                       inv.augslot1, inv.augslot2, inv.augslot3, inv.augslot4, inv.augslot5, inv.augslot6,
                       items.Name, items.icon, items.stackable, items.size, items.itemtype, items.bagslots, items.bagtype
                FROM inventory inv
                LEFT JOIN items ON inv.itemid = items.id
                WHERE inv.charid = %s AND (inv.slotid BETWEEN 23 AND 32 OR inv.slotid BETWEEN 251 AND 361)
                ORDER BY inv.slotid
            """
            
            logger.info(f"Executing inventory query for character {character_id}")
            cursor.execute(inventory_query, (character_id,))
            inventory_results = cursor.fetchall()
            logger.info(f"Inventory query returned {len(inventory_results)} results")
            
            inventory = []
            for row in inventory_results:
                # Handle both dictionary (DictCursor) and tuple cursor results
                if isinstance(row, dict):
                    inventory.append({
                        'slotid': row.get('slotid'),
                        'itemid': row.get('itemid'),
                        'charges': row.get('charges'),
                        'color': row.get('color'),
                        'instnodrop': row.get('instnodrop'),
                        'augslots': [
                            row.get('augslot1'), row.get('augslot2'), row.get('augslot3'),
                            row.get('augslot4'), row.get('augslot5'), row.get('augslot6')
                        ],
                        'item_name': row.get('Name'),
                        'item_icon': row.get('icon'),
                        'stackable': row.get('stackable'),
                        'container_size': row.get('bagslots'),
                        'item_type': row.get('itemtype')
                    })
                else:
                    # Fallback for tuple cursor results
                    inventory.append({
                        'slotid': row[0],
                        'itemid': row[1],
                        'charges': row[2],
                        'color': row[3],
                        'instnodrop': row[4],
                        'augslots': [row[5], row[6], row[7], row[8], row[9], row[10]],
                        'item_name': row[11],
                        'item_icon': row[12],
                        'stackable': row[13],
                        'container_size': row[16],  # bagslots is now at index 16
                        'item_type': row[15]
                    })
        
            return jsonify({'equipment': equipment, 'inventory': inventory}), 200
            
        except Exception as query_error:
            logger.error(f"Database query error for character {character_id}: {query_error}")
            # Return partial data if equipment loaded but inventory failed
            if equipment:
                return jsonify({'equipment': equipment, 'inventory': [], 'warning': 'Inventory data partially unavailable'}), 200
            else:
                return jsonify({'error': 'Failed to load character inventory'}), 500
        finally:
            if cursor:
                cursor.close()
        
    except Exception as e:
        logger.error(f"Connection error getting inventory for character {character_id}: {e}")
        return jsonify({'error': 'Database connection failed'}), 503
    finally:
        if connection:
            try:
                connection.close()
            except Exception as close_error:
                logger.error(f"Error closing connection: {close_error}")

@character_bp.route('/characters/<int:character_id>/currency', methods=['GET'])
def get_character_currency(character_id):
    """
    Get character's currency amounts.
    
    Note: Currency storage varies by EQEmu server implementation.
    This endpoint may need server-specific customization.
    
    Returns:
    - Character currency amounts (platinum, gold, silver, copper)
    """
    try:
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for currency: {error}")
            return jsonify({'error': 'Database connection unavailable'}), 503
        
        logger.info(f"Currency request for character {character_id}")
        
        # Note: Currency implementation varies by server
        # Some servers use character_currency table, others use items, others use character_data fields
        # This is a basic implementation that should be customized per server
        
        # Try character_currency table first (if it exists)
        with connection.cursor() as cursor:
            try:
                query = """
                    SELECT platinum, gold, silver, copper
                    FROM character_currency
                    WHERE id = %s
                """
                cursor.execute(query, (character_id,))
                result = cursor.fetchone()
                
                if result:
                    # Handle both dictionary and tuple cursor results
                    if isinstance(result, dict):
                        currency = {
                            'platinum': result.get('platinum') or 0,
                            'gold': result.get('gold') or 0,
                            'silver': result.get('silver') or 0,
                            'copper': result.get('copper') or 0
                        }
                    else:
                        currency = {
                            'platinum': result[0] or 0,
                            'gold': result[1] or 0,
                            'silver': result[2] or 0,
                            'copper': result[3] or 0
                        }
                else:
                    # No currency record found
                    currency = {
                        'platinum': 0,
                        'gold': 0,
                        'silver': 0,
                        'copper': 0
                    }
                    
            except Exception:
                # character_currency table doesn't exist, return zeros
                logger.info("character_currency table not found - returning zero currency")
                currency = {
                    'platinum': 0,
                    'gold': 0,
                    'silver': 0,
                    'copper': 0
                }
        
        connection.close()
        return jsonify(currency), 200
        
    except Exception as e:
        logger.error(f"Error getting currency for character {character_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/characters/<int:character_id>/stats', methods=['GET'])
def get_character_stats(character_id):
    """
    Get character's calculated stats (AC, ATK, resistances, max HP/MP, weight).
    
    Calculates stats by summing base character stats plus equipment bonuses.
    
    Returns:
    - Calculated character statistics
    """
    try:
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for stats: {error}")
            return jsonify({'error': 'Database connection unavailable'}), 503
            
        logger.info(f"Stats request for character {character_id}")
        
        # Get base character data including any pre-calculated stats
        with connection.cursor() as cursor:
            # Following Char Browser approach - base stats only (resistances calculated from equipment)
            char_query = """
                SELECT cur_hp, mana, endurance, str, sta, agi, dex, wis, `int`, cha, level, class
                FROM character_data 
                WHERE id = %s
            """
            cursor.execute(char_query, (character_id,))
            char_result = cursor.fetchone()
            
            if not char_result:
                connection.close()
                return jsonify({'error': 'Character not found'}), 404
            
            # Handle both dictionary and tuple cursor results - following Char Browser pattern
            if isinstance(char_result, dict):
                base_hp = char_result['cur_hp'] or 0
                base_mp = char_result['mana'] or 0
                base_endurance = char_result['endurance'] or 0
                base_ac = 0  # AC calculated from equipment only
                base_resistances = {
                    'magic': 0, 'poison': 0, 'fire': 0, 'disease': 0, 'cold': 0, 'corrupt': 0
                }
                # Base stats for HP/MP calculations
                base_str = char_result['str'] or 0
                base_sta = char_result['sta'] or 0
                base_agi = char_result['agi'] or 0
                base_dex = char_result['dex'] or 0
                base_wis = char_result['wis'] or 0
                base_intel = char_result['int'] or 0
                base_cha = char_result['cha'] or 0
                char_level = char_result['level'] or 1
                char_class = char_result['class'] or 1
            else:
                base_hp = char_result[0] or 0
                base_mp = char_result[1] or 0
                base_endurance = char_result[2] or 0
                base_ac = 0  # AC calculated from equipment only
                # Following Char Browser column order
                base_str = char_result[3] or 0
                base_sta = char_result[4] or 0  
                base_agi = char_result[5] or 0
                base_dex = char_result[6] or 0
                base_wis = char_result[7] or 0
                base_intel = char_result[8] or 0
                base_cha = char_result[9] or 0
                char_level = char_result[10] or 1
                char_class = char_result[11] or 1
                base_resistances = {
                    'magic': 0, 'poison': 0, 'fire': 0, 'disease': 0, 'cold': 0, 'corrupt': 0
                }
        
            # Get equipped items and calculate bonuses (start with basic stats)
            equipment_query = """
                SELECT items.ac, items.hp, items.mana, items.endur, items.attack,
                       items.pr, items.mr, items.fr, items.cr, items.dr, items.svcorruption,
                       items.weight, items.astr, items.asta, items.aagi, items.adex, 
                       items.awis, items.aint, items.acha
                FROM inventory inv
                LEFT JOIN items ON inv.itemid = items.id
                WHERE inv.charid = %s AND inv.slotid BETWEEN 0 AND 22
                AND inv.itemid IS NOT NULL
            """
            cursor.execute(equipment_query, (character_id,))
            equipment_results = cursor.fetchall()
            
            # Initialize calculated stats (following Char Browser pattern)
            equipment_ac = 0
            equipment_atk = 0
            equipment_weight = 0
            equipment_hp_bonus = 0
            equipment_mp_bonus = 0
            equipment_endur_bonus = 0
            equipment_resistances = {
                'poison': 0,
                'magic': 0,
                'disease': 0,
                'fire': 0,
                'cold': 0,
                'corrupt': 0
            }
            # Track stat bonuses from equipment 
            equipment_stats = {
                'str': 0, 'sta': 0, 'agi': 0, 'dex': 0, 'wis': 0, 'int': 0, 'cha': 0
            }
            # Track heroic stats separately (Char Browser approach)
            heroic_stats = {
                'str': 0, 'sta': 0, 'agi': 0, 'dex': 0, 'wis': 0, 'int': 0, 'cha': 0
            }
            heroic_resistances = {
                'poison': 0, 'magic': 0, 'fire': 0, 'cold': 0, 'disease': 0, 'corrupt': 0
            }
            
            # Sum up equipment bonuses (Char Browser additem approach)
            for item in equipment_results:
                if isinstance(item, dict):
                    # Basic stats
                    equipment_ac += item.get('ac') or 0
                    equipment_atk += item.get('attack') or 0
                    equipment_weight += item.get('weight') or 0
                    equipment_hp_bonus += item.get('hp') or 0
                    equipment_mp_bonus += item.get('mana') or 0
                    equipment_endur_bonus += item.get('endur') or 0
                    
                    # Resistances
                    equipment_resistances['poison'] += item.get('pr') or 0
                    equipment_resistances['magic'] += item.get('mr') or 0
                    equipment_resistances['fire'] += item.get('fr') or 0
                    equipment_resistances['cold'] += item.get('cr') or 0
                    equipment_resistances['disease'] += item.get('dr') or 0
                    equipment_resistances['corrupt'] += item.get('svcorruption') or 0
                    
                    # Stat bonuses
                    equipment_stats['str'] += item.get('astr') or 0
                    equipment_stats['sta'] += item.get('asta') or 0
                    equipment_stats['agi'] += item.get('aagi') or 0
                    equipment_stats['dex'] += item.get('adex') or 0
                    equipment_stats['wis'] += item.get('awis') or 0
                    equipment_stats['int'] += item.get('aint') or 0
                    equipment_stats['cha'] += item.get('acha') or 0
                    
                    # Heroic stats (not available in this database version)
                    # heroic_stats placeholder for future expansion
                else:
                    # Tuple cursor results (maintain compatibility)
                    equipment_ac += item[0] or 0           # ac
                    equipment_hp_bonus += item[1] or 0     # hp
                    equipment_mp_bonus += item[2] or 0     # mana
                    equipment_endur_bonus += item[3] or 0  # endur
                    equipment_atk += item[4] or 0          # attack
                    equipment_resistances['poison'] += item[5] or 0    # pr
                    equipment_resistances['magic'] += item[6] or 0     # mr
                    equipment_resistances['fire'] += item[7] or 0      # fr
                    equipment_resistances['cold'] += item[8] or 0      # cr
                    equipment_resistances['disease'] += item[9] or 0   # dr
                    equipment_resistances['corrupt'] += item[10] or 0  # svcorruption
                    equipment_weight += item[11] or 0      # weight
                    
                    # Additional stats (if query includes them)
                    if len(item) > 12:
                        equipment_stats['str'] += item[12] or 0  # astr
                        equipment_stats['sta'] += item[13] or 0  # asta
                        equipment_stats['agi'] += item[14] or 0  # aagi
                        equipment_stats['dex'] += item[15] or 0  # adex
                        equipment_stats['wis'] += item[16] or 0  # awis
                        equipment_stats['int'] += item[17] or 0  # aint
                        equipment_stats['cha'] += item[18] or 0  # acha
            
            # Calculate final stats (Char Browser approach)
            # Total resistances = base + equipment + heroic
            final_resistances = {}
            for resist_type in equipment_resistances:
                final_resistances[resist_type] = (
                    base_resistances[resist_type] +
                    equipment_resistances[resist_type] +
                    heroic_resistances[resist_type]
                )
            
            # Calculate effective stats with equipment bonuses
            effective_sta = base_sta + equipment_stats['sta'] + heroic_stats['sta']
            effective_wis = base_wis + equipment_stats['wis'] + heroic_stats['wis'] 
            effective_intel = base_intel + equipment_stats['int'] + heroic_stats['int']
            
            calculated_stats = {
                'maxHp': base_hp + equipment_hp_bonus,     # Base + equipment HP
                'maxMp': base_mp + equipment_mp_bonus,     # Base + equipment MP  
                'maxEndurance': base_endurance + equipment_endur_bonus, # Base + equipment Endurance
                'ac': base_ac + equipment_ac,              # Base + equipment AC
                'atk': equipment_atk,                      # Equipment attack bonuses
                'weight': equipment_weight,                # Total equipment weight
                'resistances': final_resistances,          # Combined resistances
                
                # Additional comprehensive stats (Char Browser style)
                'totalStats': {
                    'str': base_str + equipment_stats['str'] + heroic_stats['str'],
                    'sta': effective_sta,
                    'agi': base_agi + equipment_stats['agi'] + heroic_stats['agi'],
                    'dex': base_dex + equipment_stats['dex'] + heroic_stats['dex'],
                    'wis': effective_wis,
                    'int': effective_intel,
                    'cha': base_cha + equipment_stats['cha'] + heroic_stats['cha']
                },
                
                # Equipment bonuses breakdown for debugging
                'equipmentBonuses': {
                    'hp': equipment_hp_bonus,
                    'mp': equipment_mp_bonus,
                    'endurance': equipment_endur_bonus,
                    'ac': equipment_ac,
                    'attack': equipment_atk,
                    'weight': equipment_weight,
                    'stats': equipment_stats,
                    'resistances': equipment_resistances
                }
            }
            
            logger.info(f"Enhanced stats for character {character_id}: AC={base_ac + equipment_ac}, ATK={equipment_atk}, Weight={equipment_weight}, HP={base_hp}+{equipment_hp_bonus}, MP={base_mp}+{equipment_mp_bonus}, Resistances={final_resistances}")
        
        connection.close()
        return jsonify(calculated_stats), 200
        
    except Exception as e:
        logger.error(f"Error getting stats for character {character_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/item/<int:item_id>', methods=['GET'])
@rate_limit_by_ip(120, 500)
def get_item_details(item_id):
    """
    Get detailed item information by ID.
    
    Returns:
    - Complete item data from items table
    """
    try:
        # Get EQEmu database connection using the same method as other working routes
        from app import get_eqemu_db_connection
        connection, db_type, error = get_eqemu_db_connection()
        if error or not connection:
            logger.error(f"No EQEmu database connection available for item details: {error}")
            return jsonify({'error': 'Database connection unavailable'}), 503
        
        # Get item data
        with connection.cursor() as cursor:
            query = """
                SELECT id, Name, icon, ac, hp, mana, endur, attack, damage, delay, weight,
                       astr, asta, aagi, adex, awis, aint, acha,
                       pr, mr, fr, cr, dr, svcorruption,
                       classes, races, deity, slots, itemtype, price
                FROM items
                WHERE id = %s
            """
            cursor.execute(query, (item_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Item not found'}), 404
            
            item = {
                'id': result[0],
                'name': result[1],
                'icon': result[2],
                'stats': {
                    'ac': result[3] or 0,
                    'hp': result[4] or 0,
                    'mana': result[5] or 0,
                    'endur': result[6] or 0,
                    'attack': result[7] or 0,
                    'damage': result[8] or 0,
                    'delay': result[9] or 0,
                    'weight': result[10] or 0
                },
                'attributes': {
                    'str': result[11] or 0,
                    'sta': result[12] or 0,
                    'agi': result[13] or 0,
                    'dex': result[14] or 0,
                    'wis': result[15] or 0,
                    'int': result[16] or 0,
                    'cha': result[17] or 0
                },
                'resistances': {
                    'poison': result[18] or 0,
                    'magic': result[19] or 0,
                    'fire': result[20] or 0,
                    'cold': result[21] or 0,
                    'disease': result[22] or 0,
                    'corruption': result[23] or 0
                },
                'restrictions': {
                    'classes': result[24] or 0,
                    'races': result[25] or 0,
                    'deity': result[26] or 0,
                    'slots': result[27] or 0,
                    'itemtype': result[28] or 0
                },
                'price': result[29] or 0
            }
        
        connection.close()
        return jsonify(item), 200
        
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# User main character management endpoints (requires authentication)
def create_user_character_preferences_table(connection):
    """
    Create the user_character_preferences table if it doesn't exist.
    Based on migration 006_add_character_preferences.sql
    """
    try:
        with connection.cursor() as cursor:
            # Create the table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_character_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    primary_character_id INTEGER,
                    primary_character_name VARCHAR(64),
                    secondary_character_id INTEGER, 
                    secondary_character_name VARCHAR(64),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Ensure one record per user
                    CONSTRAINT unique_user_id UNIQUE (user_id)
                );
            """)
            
            # Create the trigger function
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_user_character_preferences_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create the trigger
            cursor.execute("""
                DROP TRIGGER IF EXISTS trigger_update_user_character_preferences_updated_at ON user_character_preferences;
                CREATE TRIGGER trigger_update_user_character_preferences_updated_at
                    BEFORE UPDATE ON user_character_preferences
                    FOR EACH ROW EXECUTE FUNCTION update_user_character_preferences_updated_at();
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_character_prefs ON user_character_preferences (user_id);
            """)
            
            connection.commit()
            
    except Exception as e:
        connection.rollback()
        raise e

@character_bp.route('/user/characters/mains', methods=['GET'])
@rate_limit_by_ip(30, 150)
def get_user_main_characters():
    """
    Get user's selected main characters (Primary and Secondary).
    
    Requires authentication.
    
    Returns:
    - User's main character selections
    """
    try:
        if not require_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = get_current_user_id()
        
        if not ENABLE_USER_ACCOUNTS:
            # Return empty when user accounts disabled
            logger.info("User accounts disabled - returning empty main characters")
            return jsonify({
                'success': True,
                'data': {
                    'primaryMain': None,
                    'secondaryMain': None
                },
                'message': 'User accounts disabled'
            }), 200
        
        # Get user database connection
        connection = get_user_db_connection()
        if not connection:
            logger.warning("No user database connection - returning empty main characters")
            logger.warning("This usually means DATABASE_URL is not configured properly in production")
            return jsonify({
                'success': True,
                'data': {
                    'primaryMain': None,
                    'secondaryMain': None
                },
                'message': 'User database not available'
            }), 200
        
        # Get user's main characters with enhanced error handling
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT primary_character_id, primary_character_name,
                           secondary_character_id, secondary_character_name,
                           updated_at
                    FROM user_character_preferences
                    WHERE user_id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                
                data = {
                    'primaryMain': None,
                    'secondaryMain': None
                }
                
                # Helper function to get complete character data from EQEmu database
                def get_complete_character_data(character_id, character_name, set_at):
                    try:
                        from app import get_eqemu_db_connection
                        eqemu_connection, db_type, error = get_eqemu_db_connection()
                        if error or not eqemu_connection:
                            # Fallback to basic data if EQEmu DB unavailable
                            return {
                                'id': character_id,
                                'name': character_name,
                                'level': 0,
                                'class': 'Unknown',
                                'race': 'Unknown',
                                'setAt': set_at
                            }
                        
                        with eqemu_connection.cursor() as eqemu_cursor:
                            eqemu_cursor.execute("""
                                SELECT id, name, level, class, race, last_login
                                FROM character_data 
                                WHERE id = %s
                            """, (character_id,))
                            
                            char_result = eqemu_cursor.fetchone()
                            if char_result:
                                # Handle both dict and tuple result formats
                                if isinstance(char_result, dict):
                                    # DictCursor result
                                    char_id = char_result['id']
                                    char_name = char_result['name']
                                    char_level = char_result['level']
                                    char_class = char_result['class']
                                    char_race = char_result['race']
                                    char_last_login = char_result['last_login']
                                else:
                                    # Tuple result
                                    char_id = char_result[0]
                                    char_name = char_result[1]
                                    char_level = char_result[2]
                                    char_class = char_result[3]
                                    char_race = char_result[4]
                                    char_last_login = char_result[5]
                                
                                class_name = CLASS_NAMES.get(char_class, 'Unknown')
                                race_name = RACE_NAMES.get(char_race, 'Unknown')
                                
                                # Handle timestamp conversion safely
                                last_login_iso = None
                                if char_last_login:
                                    try:
                                        if hasattr(char_last_login, 'isoformat'):
                                            last_login_iso = char_last_login.isoformat()
                                        else:
                                            # Handle Unix timestamp
                                            import datetime
                                            last_login_iso = datetime.datetime.fromtimestamp(char_last_login).isoformat()
                                    except Exception:
                                        last_login_iso = str(char_last_login)
                                
                                return {
                                    'id': char_id,
                                    'name': char_name,
                                    'level': char_level,
                                    'class': class_name,
                                    'race': race_name,
                                    'lastLogin': last_login_iso,
                                    'setAt': set_at
                                }
                        
                        eqemu_connection.close()
                    except Exception as e:
                        logger.error(f"Error fetching complete character data for {character_id}: {e}")
                    
                    # Fallback to basic data
                    return {
                        'id': character_id,
                        'name': character_name,
                        'level': 0,
                        'class': 'Unknown',
                        'race': 'Unknown',
                        'setAt': set_at
                    }
                
                if result:
                    if result[0]:  # primary_character_id
                        set_at = result[4].isoformat() if result[4] else None
                        data['primaryMain'] = get_complete_character_data(result[0], result[1], set_at)
                    
                    if result[2]:  # secondary_character_id
                        set_at = result[4].isoformat() if result[4] else None
                        data['secondaryMain'] = get_complete_character_data(result[2], result[3], set_at)
            
            connection.close()
            return jsonify({
                'success': True,
                'data': data,
                'message': 'Main characters loaded successfully'
            }), 200
            
        except psycopg2.Error as db_error:
            logger.error(f"Database error loading main characters: {db_error}")
            
            # Check if this is a missing table error
            if "user_character_preferences" in str(db_error) and "does not exist" in str(db_error):
                logger.info("user_character_preferences table does not exist, creating it...")
                try:
                    # Create the table
                    create_user_character_preferences_table(connection)
                    logger.info("Successfully created user_character_preferences table")
                    
                    # Retry the query
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT primary_character_id, primary_character_name,
                                   secondary_character_id, secondary_character_name,
                                   updated_at
                            FROM user_character_preferences
                            WHERE user_id = %s
                        """, (user_id,))
                        
                        result = cursor.fetchone()
                        
                        data = {
                            'primaryMain': None,
                            'secondaryMain': None
                        }
                        
                        # Since the table was just created, result will be None
                        # Return empty data successfully
                        connection.close()
                        return jsonify({
                            'success': True,
                            'data': data,
                            'message': 'Main characters loaded successfully (table created)'
                        }), 200
                        
                except Exception as create_error:
                    logger.error(f"Failed to create user_character_preferences table: {create_error}")
                    connection.close()
                    return jsonify({
                        'success': True,
                        'data': {
                            'primaryMain': None,
                            'secondaryMain': None
                        },
                        'message': 'Database schema initialization failed - returning empty results'
                    }), 200
            else:
                logger.error("Database error is not related to missing table")
                connection.close()
                return jsonify({
                    'success': True,
                    'data': {
                        'primaryMain': None,
                        'secondaryMain': None
                    },
                    'message': 'Database error - returning empty results'
                }), 200
        
    except Exception as e:
        logger.error(f"Error getting user main characters: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/user/characters/primary', methods=['POST'])
@rate_limit_by_ip(10, 50)
def set_primary_main():
    """
    Set user's primary main character.
    
    Requires authentication.
    
    Body:
    - characterId: ID of the character
    - characterName: Name of the character
    
    Returns:
    - Success confirmation
    """
    try:
        if not require_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or 'characterId' not in data or 'characterName' not in data:
            return jsonify({'error': 'characterId and characterName required'}), 400
        
        character_id = int(data['characterId'])
        character_name = str(data['characterName']).strip()
        
        if not character_name:
            return jsonify({'error': 'Character name cannot be empty'}), 400
        
        if not ENABLE_USER_ACCOUNTS:
            # Mock success when user accounts disabled
            return jsonify({
                'success': True,
                'message': 'Primary main character set successfully (mock)',
                'character': {
                    'characterId': character_id,
                    'characterName': character_name
                }
            }), 200
        
        # Get user database connection
        connection = get_user_db_connection()
        if not connection:
            # In development mode with auth bypass, provide mock success
            if DEV_MODE_AUTH_BYPASS:
                logger.warning("No user database connection - returning mock success in dev mode")
                return jsonify({
                    'success': True,
                    'message': 'Primary main character set successfully (mock - no database)',
                    'character': {
                        'characterId': character_id,
                        'characterName': character_name
                    }
                }), 200
            else:
                return jsonify({'error': 'Database unavailable'}), 503
        
        # Set primary main character with table creation fallback
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_character_preferences (user_id, primary_character_id, primary_character_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        primary_character_id = EXCLUDED.primary_character_id,
                        primary_character_name = EXCLUDED.primary_character_name,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, character_id, character_name))
            
            connection.close()
            
        except psycopg2.Error as db_error:
            # Check if this is a missing table error
            if "user_character_preferences" in str(db_error) and "does not exist" in str(db_error):
                logger.info("user_character_preferences table does not exist, creating it for primary main...")
                try:
                    # Create the table
                    create_user_character_preferences_table(connection)
                    logger.info("Successfully created user_character_preferences table")
                    
                    # Retry the operation
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO user_character_preferences (user_id, primary_character_id, primary_character_name)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (user_id)
                            DO UPDATE SET 
                                primary_character_id = EXCLUDED.primary_character_id,
                                primary_character_name = EXCLUDED.primary_character_name,
                                updated_at = CURRENT_TIMESTAMP
                        """, (user_id, character_id, character_name))
                    
                    connection.close()
                    
                except Exception as create_error:
                    logger.error(f"Failed to create user_character_preferences table: {create_error}")
                    connection.close()
                    return jsonify({'error': 'Database schema initialization failed'}), 503
            else:
                logger.error(f"Database error setting primary main: {db_error}")
                connection.close()
                return jsonify({'error': 'Database error'}), 503
        
        return jsonify({
            'success': True,
            'message': 'Primary main character set successfully',
            'character': {
                'characterId': character_id,
                'characterName': character_name
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting primary main character: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/user/characters/secondary', methods=['POST'])
@rate_limit_by_ip(10, 50)
def set_secondary_main():
    """
    Set user's secondary main character.
    
    Requires authentication.
    
    Body:
    - characterId: ID of the character
    - characterName: Name of the character
    
    Returns:
    - Success confirmation
    """
    try:
        if not require_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or 'characterId' not in data or 'characterName' not in data:
            return jsonify({'error': 'characterId and characterName required'}), 400
        
        character_id = int(data['characterId'])
        character_name = str(data['characterName']).strip()
        
        if not character_name:
            return jsonify({'error': 'Character name cannot be empty'}), 400
        
        if not ENABLE_USER_ACCOUNTS:
            # Mock success when user accounts disabled
            return jsonify({
                'success': True,
                'message': 'Secondary main character set successfully (mock)',
                'character': {
                    'characterId': character_id,
                    'characterName': character_name
                }
            }), 200
        
        # Get user database connection
        connection = get_user_db_connection()
        if not connection:
            # In development mode with auth bypass, provide mock success
            if DEV_MODE_AUTH_BYPASS:
                logger.warning("No user database connection - returning mock success in dev mode")
                return jsonify({
                    'success': True,
                    'message': 'Secondary main character set successfully (mock - no database)',
                    'character': {
                        'characterId': character_id,
                        'characterName': character_name
                    }
                }), 200
            else:
                return jsonify({'error': 'Database unavailable'}), 503
        
        # Set secondary main character with table creation fallback
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_character_preferences (user_id, secondary_character_id, secondary_character_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET 
                        secondary_character_id = EXCLUDED.secondary_character_id,
                        secondary_character_name = EXCLUDED.secondary_character_name,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, character_id, character_name))
            
            connection.close()
            
        except psycopg2.Error as db_error:
            # Check if this is a missing table error
            if "user_character_preferences" in str(db_error) and "does not exist" in str(db_error):
                logger.info("user_character_preferences table does not exist, creating it for secondary main...")
                try:
                    # Create the table
                    create_user_character_preferences_table(connection)
                    logger.info("Successfully created user_character_preferences table")
                    
                    # Retry the operation
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO user_character_preferences (user_id, secondary_character_id, secondary_character_name)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (user_id)
                            DO UPDATE SET 
                                secondary_character_id = EXCLUDED.secondary_character_id,
                                secondary_character_name = EXCLUDED.secondary_character_name,
                                updated_at = CURRENT_TIMESTAMP
                        """, (user_id, character_id, character_name))
                    
                    connection.close()
                    
                except Exception as create_error:
                    logger.error(f"Failed to create user_character_preferences table: {create_error}")
                    connection.close()
                    return jsonify({'error': 'Database schema initialization failed'}), 503
            else:
                logger.error(f"Database error setting secondary main: {db_error}")
                connection.close()
                return jsonify({'error': 'Database error'}), 503
        
        return jsonify({
            'success': True,
            'message': 'Secondary main character set successfully',
            'character': {
                'characterId': character_id,
                'characterName': character_name
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error setting secondary main character: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/user/characters/primary', methods=['DELETE'])
@rate_limit_by_ip(10, 50)
def remove_primary_main():
    """
    Remove user's primary main character selection.
    
    Requires authentication.
    
    Returns:
    - Success confirmation
    """
    try:
        if not require_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = get_current_user_id()
        
        if not ENABLE_USER_ACCOUNTS:
            # Mock success when user accounts disabled
            return jsonify({
                'success': True,
                'message': 'Primary main character removed successfully (mock)'
            }), 200
        
        # Get user database connection
        connection = get_user_db_connection()
        if not connection:
            # In development mode with auth bypass, provide mock success
            if DEV_MODE_AUTH_BYPASS:
                logger.warning("No user database connection - returning mock success in dev mode")
                return jsonify({
                    'success': True,
                    'message': 'Primary main character removed successfully (mock - no database)'
                }), 200
            else:
                return jsonify({'error': 'Database unavailable'}), 503
        
        # Remove primary main character
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_character_preferences 
                SET primary_character_id = NULL,
                    primary_character_name = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
        
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Primary main character removed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error removing primary main character: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@character_bp.route('/user/characters/secondary', methods=['DELETE'])
@rate_limit_by_ip(10, 50)
def remove_secondary_main():
    """
    Remove user's secondary main character selection.
    
    Requires authentication.
    
    Returns:
    - Success confirmation
    """
    try:
        if not require_auth():
            return jsonify({'error': 'Authentication required'}), 401
        
        user_id = get_current_user_id()
        
        if not ENABLE_USER_ACCOUNTS:
            # Mock success when user accounts disabled
            return jsonify({
                'success': True,
                'message': 'Secondary main character removed successfully (mock)'
            }), 200
        
        # Get user database connection
        connection = get_user_db_connection()
        if not connection:
            # In development mode with auth bypass, provide mock success
            if DEV_MODE_AUTH_BYPASS:
                logger.warning("No user database connection - returning mock success in dev mode")
                return jsonify({
                    'success': True,
                    'message': 'Secondary main character removed successfully (mock - no database)'
                }), 200
            else:
                return jsonify({'error': 'Database unavailable'}), 503
        
        # Remove secondary main character
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_character_preferences 
                SET secondary_character_id = NULL,
                    secondary_character_name = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
        
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Secondary main character removed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error removing secondary main character: {e}")
        return jsonify({'error': 'Internal server error'}), 500