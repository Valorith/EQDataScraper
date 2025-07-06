from flask import Flask, jsonify, request, g
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime, timedelta
import logging
import time
import psycopg2
from urllib.parse import urlparse

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables only")

# Import scrape_spells from the same directory
from scrape_spells import scrape_class, CLASSES, CLASS_COLORS
from utils.security import sanitize_search_input, validate_item_search_params, rate_limit_by_ip

# Import activity logger if user accounts are enabled
if os.environ.get('ENABLE_USER_ACCOUNTS', 'false').lower() == 'true':
    from utils.activity_logger import log_scrape_activity, log_cache_activity, log_api_activity

app = Flask(__name__)

# Check if user accounts are enabled
ENABLE_USER_ACCOUNTS = os.environ.get('ENABLE_USER_ACCOUNTS', 'false').lower() == 'true'

# Log OAuth configuration at startup for debugging
if ENABLE_USER_ACCOUNTS:
    print("🔐 OAuth/User Accounts ENABLED")
    print(f"   - GOOGLE_CLIENT_ID: {'SET' if os.environ.get('GOOGLE_CLIENT_ID') else 'NOT SET'}")
    print(f"   - GOOGLE_CLIENT_SECRET: {'SET' if os.environ.get('GOOGLE_CLIENT_SECRET') else 'NOT SET'}")
    oauth_redirect = os.environ.get('OAUTH_REDIRECT_URI', 'NOT SET')
    print(f"   - OAUTH_REDIRECT_URI: {oauth_redirect}")
    if oauth_redirect != 'NOT SET' and ('backend' in oauth_redirect or '/api/' in oauth_redirect):
        print(f"   ⚠️  WARNING: OAUTH_REDIRECT_URI points to backend API, should point to frontend!")
    print(f"   - FRONTEND_URL: {os.environ.get('FRONTEND_URL', 'NOT SET')}")
    print(f"   - JWT_SECRET_KEY: {'SET' if os.environ.get('JWT_SECRET_KEY') else 'NOT SET'}")
    print(f"   - DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
    
    # Log production-specific environment detection
    is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
    print(f"   - Environment: {'Railway Production' if is_production else 'Railway Dev' if is_railway else 'Local Development'}")
else:
    print("🔓 OAuth/User Accounts DISABLED")

# Global limiter variable
limiter = None

# Configure CORS with OAuth support if enabled
if ENABLE_USER_ACCOUNTS:
    # Allow specific origins for OAuth callbacks
    allowed_origins = [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://localhost:3002',
        'https://eqdatascraper-frontend-production.up.railway.app'
    ]
    
    # Add frontend URL from environment if set
    frontend_url = os.environ.get('FRONTEND_URL')
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    
    CORS(app, origins=allowed_origins, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
else:
    # Standard CORS for existing functionality
    CORS(app)

# Decorator to conditionally apply rate limiting
def exempt_when_limiting(f):
    """Decorator to exempt endpoints from rate limiting when limiter is active"""
    if limiter:
        return limiter.exempt(f)
    return f

# Import OAuth components only if enabled
if ENABLE_USER_ACCOUNTS:
    try:
        from routes.auth import auth_bp
        from routes.users import users_bp
        from routes.admin import admin_bp
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        # Initialize rate limiter
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        
        # Apply rate limits to OAuth endpoints
        limiter.limit("10 per minute")(auth_bp)
        limiter.limit("60 per hour")(users_bp) 
        # Admin endpoints are exempt from rate limiting
        
        # Exempt health check, admin endpoints, and cache status from rate limiting
        @limiter.request_filter
        def exempt_endpoints():
            """Exempt health, admin, and cache status endpoints from rate limiting"""
            if request.endpoint in ['health_check', 'get_cache_status', 'cache_status_detailed']:
                return True
            # Exempt all admin endpoints from rate limiting
            if request.endpoint and request.endpoint.startswith('admin.'):
                return True
            # Also check by path for cache-related and health endpoints
            if request.path and any(path in request.path for path in ['/api/health', '/api/cache-status', '/api/cache/']):
                return True
            return False
        
        # Make limiter available globally for decorators
        app.limiter = limiter
        
        # Database connection injection for OAuth routes
        @app.before_request
        def inject_db_connection():
            """Inject database connection for OAuth routes."""
            if request.endpoint and any(request.endpoint.startswith(prefix) for prefix in ['auth.', 'users.', 'admin.']):
                # Connect to database if DB_CONFIG is available (for OAuth)
                if DB_CONFIG:
                    try:
                        if DB_TYPE == 'postgresql':
                            g.db_connection = psycopg2.connect(**DB_CONFIG)
                            app.logger.debug(f"Database connection established for endpoint: {request.endpoint}")
                        else:
                            # For other database types, we'd need to import and use appropriate drivers
                            app.logger.warning(f"Database type {DB_TYPE} not yet supported for OAuth")
                            g.db_connection = None
                    except Exception as e:
                        app.logger.error(f"Failed to connect to database for OAuth: {e}")
                        app.logger.error(f"DB_CONFIG: host={DB_CONFIG.get('host')}, port={DB_CONFIG.get('port')}, database={DB_CONFIG.get('database')}")
                        g.db_connection = None
                else:
                    app.logger.debug(f"No DB_CONFIG available for OAuth endpoint: {request.endpoint}")
                    g.db_connection = None
        
        @app.teardown_request
        def close_db_connection(error):
            """Close database connection after OAuth requests."""
            if hasattr(g, 'db_connection') and g.db_connection:
                g.db_connection.close()
        
        # Register OAuth blueprints
        app.register_blueprint(auth_bp, url_prefix='/api')
        app.register_blueprint(users_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api')
        
        # Import and register dev auth if conditions are met
        from routes.auth_dev import create_dev_auth_blueprint
        dev_auth_bp = create_dev_auth_blueprint()
        if dev_auth_bp:
            app.register_blueprint(dev_auth_bp, url_prefix='')
            app.logger.warning("⚠️  DEVELOPMENT AUTH ENABLED - Never use in production!")
        
        app.logger.info("✅ OAuth user accounts enabled")
    except ImportError as e:
        app.logger.warning(f"⚠️ OAuth components not available: {e}")
        ENABLE_USER_ACCOUNTS = False
else:
    app.logger.info("OAuth user accounts disabled")

# Load configuration
def load_config():
    """Load configuration from config.json and environment variables"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    default_config = {
        'backend_port': 5001,
        'frontend_port': 3000,
        'cache_expiry_hours': 24,
        'pricing_cache_expiry_hours': 168,  # 1 week
        'min_scrape_interval_minutes': 5,
        'use_production_database': False,
        'production_database_url': ''
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
    config['pricing_cache_expiry_hours'] = int(os.getenv('PRICING_CACHE_EXPIRY_HOURS', config['pricing_cache_expiry_hours']))
    config['min_scrape_interval_minutes'] = int(os.getenv('MIN_SCRAPE_INTERVAL_MINUTES', config['min_scrape_interval_minutes']))
    
    return config

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Environment detection
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT') == 'production' or os.environ.get('PORT') is not None
IS_LOCAL = not IS_PRODUCTION

# Database connection setup
DATABASE_URL = os.environ.get('DATABASE_URL')

# Only allow config.json database override in local environment
if IS_LOCAL and not DATABASE_URL and config.get('use_production_database', False):
    DATABASE_URL = config.get('production_database_url', '')
    if DATABASE_URL:
        logger.info("Using production database from config.json (local development)")
        logger.warning("⚠️  Connecting to PRODUCTION database from LOCAL environment")

# Log environment info
if IS_PRODUCTION:
    logger.info("Running in PRODUCTION environment")
else:
    logger.info("Running in LOCAL DEVELOPMENT environment")

# Disable database cache since it's configured for MySQL (EQEmu) not PostgreSQL
# The database URL is for the EQEmu database, not for cache storage
USE_DATABASE_CACHE = False

# Parse database configuration if OAuth is enabled
DB_CONFIG = None
DB_TYPE = None

if DATABASE_URL and ENABLE_USER_ACCOUNTS:
    logger.info(f"Configuring database for OAuth from DATABASE_URL")
    # Parse DATABASE_URL for OAuth user storage
    # Detect database type from URL
    if DATABASE_URL.startswith('mysql://'):
        DB_TYPE = 'mysql'
        logger.info("Using MySQL database for user accounts")
    elif DATABASE_URL.startswith('postgresql://') or DATABASE_URL.startswith('postgres://'):
        DB_TYPE = 'postgresql'
        logger.info("Using PostgreSQL database for user accounts")
    else:
        DB_TYPE = 'postgresql'  # Default to PostgreSQL
        logger.info("Using PostgreSQL database for user accounts (default)")
    
    # Parse DATABASE_URL for connection
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed.hostname,
        'port': parsed.port or (5432 if DB_TYPE == 'postgresql' else 3306),
        'database': parsed.path[1:],  # Remove leading slash
        'user': parsed.username,
        'password': parsed.password
    }
    logger.info(f"Database configured for OAuth: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info(f"DB_CONFIG is now set: {bool(DB_CONFIG)}")
        
elif DATABASE_URL and not ENABLE_USER_ACCOUNTS:
    logger.info("DATABASE_URL is set but OAuth is disabled")
elif not DATABASE_URL:
    logger.warning("No DATABASE_URL found - OAuth will work without persistence")
else:
    logger.info("OAuth is enabled but no DATABASE_URL is set")

if USE_DATABASE_CACHE:
    logger.info("Database cache is enabled")
else:
    logger.info("Using file system for cache storage")
    # Fallback to file cache for local development
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
    SPELLS_CACHE_FILE = os.path.join(CACHE_DIR, 'spells_cache.json')
    PRICING_CACHE_FILE = os.path.join(CACHE_DIR, 'pricing_cache.json')
    SPELL_DETAILS_CACHE_FILE = os.path.join(CACHE_DIR, 'spell_details_cache.json')
    METADATA_CACHE_FILE = os.path.join(CACHE_DIR, 'cache_metadata.json')

# Initialize cache storage
def init_cache_storage():
    """Initialize cache storage (database or file system)"""
    if USE_DATABASE_CACHE:
        init_database_cache()
    else:
        init_file_cache()

def init_database_cache():
    """Initialize database tables for cache storage"""
    try:
        if DB_TYPE == 'mysql':
            import pymysql
            conn = pymysql.connect(
                host=DB_CONFIG['host'],
                port=int(DB_CONFIG['port']) if DB_CONFIG['port'] else 3306,
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                charset='utf8mb4'
            )
        else:
            conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create cache tables
        if DB_TYPE == 'mysql':
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell_cache (
                    class_name VARCHAR(50) PRIMARY KEY,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spell_cache (
                    class_name VARCHAR(50) PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Create activity_logs table if user accounts are enabled
        if ENABLE_USER_ACCOUNTS:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(50),
                    resource_id VARCHAR(100),
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for activity_logs
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC)")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pricing_cache (
                spell_id VARCHAR(50) PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spell_details_cache (
                spell_id VARCHAR(50) PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pricing_fetch_attempts (
                spell_id VARCHAR(50) PRIMARY KEY,
                attempt_count INTEGER DEFAULT 1,
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key VARCHAR(100) PRIMARY KEY,
                value JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("✓ Database cache tables initialized successfully")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize database cache: {e}")

def init_file_cache():
    """Initialize file system cache (fallback for local development)"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        logger.info(f"Cache directory created/verified: {CACHE_DIR}")
        logger.info(f"Cache directory is writable: {os.access(CACHE_DIR, os.W_OK)}")
    except Exception as e:
        logger.error(f"Failed to create cache directory {CACHE_DIR}: {e}")

# Initialize cache storage
init_cache_storage()

# Data storage
spells_cache = {}
spell_details_cache = {}
cache_timestamp = {}
pricing_cache_timestamp = {}  # Track when each spell's pricing was cached
last_scrape_time = {}
pricing_lookup = {}  # Fast lookup index for pricing data from spell_details_cache

# Progress tracking for manual refresh operations
refresh_progress = {}  # Track progress for each class being refreshed
pricing_cache_loaded = False  # Track if we've loaded pricing from DB into memory

# Server startup progress tracking
server_startup_progress = {
    'is_starting': True,
    'current_step': 'Initializing server...',
    'progress_percent': 0,
    'steps_completed': 0,
    'total_steps': 5,
    'startup_complete': False,
    'startup_time': None
}

CACHE_EXPIRY_HOURS = config['cache_expiry_hours']
PRICING_CACHE_EXPIRY_HOURS = config['pricing_cache_expiry_hours']
MIN_SCRAPE_INTERVAL_MINUTES = config['min_scrape_interval_minutes']

def load_all_pricing_to_memory():
    """Load all pricing data from database to memory cache (one-time operation)"""
    global pricing_lookup, pricing_cache_loaded
    
    if pricing_cache_loaded:
        return
    
    # Skip if not using database cache
    if not USE_DATABASE_CACHE:
        return
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Load ALL pricing data in one query to minimize DB hits
        cursor.execute("""
            SELECT spell_id, data->'pricing' as pricing 
            FROM spell_details_cache 
            WHERE data->'pricing' IS NOT NULL
        """)
        
        pricing_lookup = {}
        for row in cursor.fetchall():
            spell_id, pricing = row
            if pricing:
                pricing_lookup[spell_id] = pricing
        
        cursor.close()
        conn.close()
        
        pricing_cache_loaded = True
        logger.info(f"Loaded {len(pricing_lookup)} pricing entries to memory cache")
        
    except Exception as e:
        logger.warning(f"Error loading pricing to memory: {e}")

def record_pricing_fetch_attempt(spell_id, success=False, error_message=None):
    """Record a pricing fetch attempt in the database"""
    if not USE_DATABASE_CACHE:
        return
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pricing_fetch_attempts (spell_id, success, error_message, last_attempt)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (spell_id) DO UPDATE SET
                attempt_count = pricing_fetch_attempts.attempt_count + 1,
                last_attempt = CURRENT_TIMESTAMP,
                success = EXCLUDED.success,
                error_message = EXCLUDED.error_message,
                updated_at = CURRENT_TIMESTAMP
        """, (spell_id, success, error_message))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Error recording pricing fetch attempt for {spell_id}: {e}")

def get_unfetched_spells(spell_ids):
    """Get spells that have never had pricing fetch attempted"""
    if not USE_DATABASE_CACHE or not spell_ids:
        return spell_ids  # Return all if no DB or no spells
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Find spells that have never been attempted
        cursor.execute("""
            SELECT unnest(%s::varchar[]) as spell_id
            EXCEPT
            SELECT spell_id FROM pricing_fetch_attempts
        """, (spell_ids,))
        
        unfetched_spells = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return unfetched_spells
        
    except Exception as e:
        logger.warning(f"Error checking unfetched spells: {e}")
        return spell_ids  # Return all on error

def get_failed_pricing_spells(spell_ids):
    """Get spells that have been attempted but failed to get pricing"""
    if not USE_DATABASE_CACHE or not spell_ids:
        return []
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Find spells that were attempted but failed
        cursor.execute("""
            SELECT spell_id FROM pricing_fetch_attempts 
            WHERE spell_id = ANY(%s) AND success = FALSE
        """, (spell_ids,))
        
        failed_spells = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return failed_spells
        
    except Exception as e:
        logger.warning(f"Error checking failed pricing spells: {e}")
        return []

def get_bulk_pricing_from_db(spell_ids):
    """Efficiently get pricing for multiple spells using in-memory cache"""
    if not spell_ids:
        return {}
    
    # Ensure pricing data is loaded to memory
    if not pricing_cache_loaded:
        load_all_pricing_to_memory()
    
    # Use in-memory lookup (much faster than DB queries)
    pricing_data = {}
    for spell_id in spell_ids:
        if spell_id in pricing_lookup:
            pricing_data[spell_id] = pricing_lookup[spell_id]
    
    return pricing_data

def rebuild_pricing_lookup():
    """Rebuild the fast pricing lookup index from spell_details_cache"""
    global pricing_lookup
    pricing_lookup = {}
    failed_count = 0
    success_count = 0
    
    for spell_id, details in spell_details_cache.items():
        if details.get('pricing'):
            pricing_lookup[spell_id] = details['pricing']
            if details['pricing'].get('unknown') == True:
                failed_count += 1
            else:
                success_count += 1
    
    logger.info(f"Rebuilt pricing lookup index with {len(pricing_lookup)} entries ({success_count} successful, {failed_count} failed)")

def load_cache_from_storage():
    """Load cached data from database or files"""
    if USE_DATABASE_CACHE:
        load_cache_from_database()
    else:
        load_cache_from_files()
    
    # Rebuild pricing lookup after loading cache
    rebuild_pricing_lookup()

def load_cache_from_database():
    """Load cached data from PostgreSQL database"""
    global spells_cache, cache_timestamp, last_scrape_time, spell_details_cache, pricing_cache_timestamp
    
    logger.info(f"=== DATABASE CACHE LOADING ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Load spells cache
        cursor.execute("SELECT class_name, data FROM spell_cache")
        spell_rows = cursor.fetchall()
        spells_cache = {row[0].lower(): row[1] for row in spell_rows}
        logger.info(f"✓ Loaded {len(spells_cache)} classes from database spell cache")
        
        # Load pricing cache
        cursor.execute("SELECT spell_id, data FROM pricing_cache")
        pricing_rows = cursor.fetchall()
        # pricing_cache table is deprecated - using spell_details_cache instead
        logger.info(f"✓ Loaded 0 spells from database pricing cache (deprecated)")
        
        # Load spell details cache
        cursor.execute("SELECT spell_id, data FROM spell_details_cache")
        details_rows = cursor.fetchall()
        spell_details_cache = {row[0]: row[1] for row in details_rows}
        logger.info(f"✓ Loaded {len(spell_details_cache)} spell details from database cache")
        
        # Load metadata
        cursor.execute("SELECT key, value FROM cache_metadata")
        metadata_rows = cursor.fetchall()
        for key, value in metadata_rows:
            if key == 'cache_timestamp':
                # Convert class names to lowercase for consistency
                cache_timestamp.update({k.lower(): v for k, v in value.items()})
            elif key == 'pricing_cache_timestamp':
                pricing_cache_timestamp.update(value)
            elif key == 'last_scrape_time':
                # Convert class names to lowercase for consistency
                last_scrape_time.update({k.lower(): v for k, v in value.items()})
        
        logger.info(f"✓ Loaded cache metadata for {len(cache_timestamp)} classes")
        
        cursor.close()
        conn.close()
        
        logger.info(f"=== DATABASE CACHE LOADING COMPLETE ===")
        logger.info(f"Final cache state - Spells: {len(spells_cache)} classes, Pricing: 0 spells (deprecated), Details: {len(spell_details_cache)} spells")
        
    except Exception as e:
        logger.error(f"✗ Error loading cache from database: {e}")
        # Initialize empty caches if loading fails
        spells_cache = {}
        spell_details_cache = {}
        cache_timestamp = {}
        last_scrape_time = {}

def load_cache_from_files():
    """Load cached data from JSON files (fallback for local development)"""
    global spells_cache, cache_timestamp, last_scrape_time, spell_details_cache, pricing_cache_timestamp
    
    logger.info(f"=== FILE CACHE LOADING ===")
    logger.info(f"Cache directory: {CACHE_DIR}")
    logger.info(f"Cache directory exists: {os.path.exists(CACHE_DIR)}")
    
    try:
        # Load spells cache
        if os.path.exists(SPELLS_CACHE_FILE):
            with open(SPELLS_CACHE_FILE, 'r') as f:
                spells_cache = json.load(f)
                logger.info(f"✓ Successfully loaded {len(spells_cache)} classes from spells cache")
        else:
            logger.warning(f"✗ Spells cache file not found: {SPELLS_CACHE_FILE}")
        
        # Skip loading pricing_cache - deprecated in favor of spell_details_cache
        logger.info(f"✓ Skipped loading pricing cache (deprecated)")
        
        # Load spell details cache
        if os.path.exists(SPELL_DETAILS_CACHE_FILE):
            with open(SPELL_DETAILS_CACHE_FILE, 'r') as f:
                spell_details_cache = json.load(f)
                logger.info(f"✓ Loaded {len(spell_details_cache)} spell details from cache")
        
        # Load metadata
        if os.path.exists(METADATA_CACHE_FILE):
            with open(METADATA_CACHE_FILE, 'r') as f:
                metadata = json.load(f)
                cache_timestamp.update(metadata.get('cache_timestamp', {}))
                pricing_cache_timestamp.update(metadata.get('pricing_cache_timestamp', {}))
                last_scrape_time.update(metadata.get('last_scrape_time', {}))
                logger.info(f"✓ Successfully loaded cache metadata for {len(cache_timestamp)} classes")
        else:
            logger.warning(f"✗ Metadata cache file not found: {METADATA_CACHE_FILE}")
        
        logger.info(f"=== FILE CACHE LOADING COMPLETE ===")
        logger.info(f"Final cache state - Spells: {len(spells_cache)} classes, Pricing: 0 spells (deprecated)")
                
    except Exception as e:
        logger.error(f"✗ Error loading cache from files: {e}")
        # Initialize empty caches if loading fails
        spells_cache = {}
        spell_details_cache = {}
        cache_timestamp = {}
        pricing_cache_timestamp = {}
        last_scrape_time = {}

def update_refresh_progress(class_name, stage, progress_percentage=None, message=None, estimated_time_remaining=None):
    """Update refresh progress for a specific class"""
    global refresh_progress
    
    if class_name not in refresh_progress:
        refresh_progress[class_name] = {
            'stage': 'initializing',
            'progress_percentage': 0,
            'message': 'Initializing refresh process...',
            'estimated_time_remaining': None,
            'start_time': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    refresh_progress[class_name]['stage'] = stage
    refresh_progress[class_name]['last_updated'] = datetime.now().isoformat()
    
    if progress_percentage is not None:
        refresh_progress[class_name]['progress_percentage'] = progress_percentage
    if message is not None:
        refresh_progress[class_name]['message'] = message
    if estimated_time_remaining is not None:
        refresh_progress[class_name]['estimated_time_remaining'] = estimated_time_remaining
    
    # Stage-specific defaults
    stage_defaults = {
        'initializing': {'progress': 5, 'message': '🔄 Initializing refresh process...'},
        'scraping': {'progress': 20, 'message': '🌐 Scraping fresh spell data...'},
        'processing': {'progress': 60, 'message': '⚙️ Processing spell information...'},
        'updating_cache': {'progress': 80, 'message': '💾 Updating cached data...'},
        'loading_memory': {'progress': 95, 'message': '📥 Loading into memory...'},
        'complete': {'progress': 100, 'message': '✅ Refresh completed successfully!'},
        'error': {'progress': 0, 'message': '❌ Error occurred during refresh'}
    }
    
    if stage in stage_defaults:
        if progress_percentage is None:
            refresh_progress[class_name]['progress_percentage'] = stage_defaults[stage]['progress']
        if message is None:
            refresh_progress[class_name]['message'] = stage_defaults[stage]['message']

def clear_refresh_progress(class_name):
    """Clear refresh progress for a specific class"""
    global refresh_progress
    if class_name in refresh_progress:
        del refresh_progress[class_name]

def save_cache_to_storage():
    """Save cached data to database or files"""
    if USE_DATABASE_CACHE:
        save_cache_to_database()
    else:
        save_cache_to_files()

def save_single_class_to_storage(class_name):
    """Save a single class to storage - much faster than saving everything"""
    if USE_DATABASE_CACHE:
        save_single_class_to_database(class_name)
    else:
        # For file storage, we still need to save everything
        save_cache_to_files()

def save_cache_to_database():
    """Save cached data to PostgreSQL database"""
    logger.info(f"=== SAVING CACHE TO DATABASE ===")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Save spells cache
        logger.info(f"Saving spells cache ({len(spells_cache)} classes) to database")
        # Make a copy to avoid "dictionary changed size during iteration" errors
        spells_cache_copy = dict(spells_cache)
        for class_name, data in spells_cache_copy.items():
            cursor.execute("""
                INSERT INTO spell_cache (class_name, data, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (class_name) 
                DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
            """, (class_name, json.dumps(data)))
        
        # Skip saving pricing_cache - deprecated in favor of spell_details_cache
        logger.info(f"Saving pricing cache (0 entries) to database")
        
        # Save spell details cache
        logger.info(f"Saving spell details cache ({len(spell_details_cache)} entries) to database")
        # Make a copy to avoid "dictionary changed size during iteration" errors
        spell_details_copy = dict(spell_details_cache)
        for spell_id, data in spell_details_copy.items():
            cursor.execute("""
                INSERT INTO spell_details_cache (spell_id, data, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (spell_id) 
                DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
            """, (spell_id, json.dumps(data)))
        
        # Save metadata
        metadata_items = [
            ('cache_timestamp', cache_timestamp),
            ('pricing_cache_timestamp', pricing_cache_timestamp),
            ('last_scrape_time', last_scrape_time),
            ('last_updated', datetime.now().isoformat())
        ]
        
        for key, value in metadata_items:
            cursor.execute("""
                INSERT INTO cache_metadata (key, value, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) 
                DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
            """, (key, json.dumps(value)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Successfully saved all cache data to database")
        logger.info(f"=== DATABASE CACHE SAVE COMPLETE ===")
        
    except Exception as e:
        logger.error(f"✗ Error saving cache to database: {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def save_single_class_to_database(class_name):
    """Save a single class to PostgreSQL database - optimized for single class updates"""
    logger.info(f"Saving single class '{class_name}' to database")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Save only the specific class
        if class_name in spells_cache:
            cursor.execute("""
                INSERT INTO spell_cache (class_name, data, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (class_name) 
                DO UPDATE SET data = EXCLUDED.data, updated_at = CURRENT_TIMESTAMP
            """, (class_name, json.dumps(spells_cache[class_name])))
        
        # Update metadata for this class only
        if class_name in cache_timestamp:
            cursor.execute("""
                INSERT INTO cache_metadata (key, value, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) 
                DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
            """, (f'cache_timestamp', json.dumps(cache_timestamp)))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Successfully saved class '{class_name}' to database")
        
    except Exception as e:
        logger.error(f"✗ Error saving single class to database: {e}")
        raise

def save_cache_to_files():
    """Save cached data to JSON files (fallback for local development)"""
    logger.info(f"=== SAVING CACHE TO FILES ===")
    logger.info(f"Cache directory exists: {os.path.exists(CACHE_DIR)}")
    logger.info(f"Cache directory writable: {os.access(CACHE_DIR, os.W_OK) if os.path.exists(CACHE_DIR) else 'Directory does not exist'}")
    
    try:
        # Save spells cache
        logger.info(f"Saving spells cache ({len(spells_cache)} classes) to {SPELLS_CACHE_FILE}")
        with open(SPELLS_CACHE_FILE, 'w') as f:
            json.dump(spells_cache, f, indent=2)
        logger.info(f"✓ Spells cache saved successfully")
        
        # Skip saving pricing_cache - deprecated in favor of spell_details_cache
        logger.info(f"Skipped saving pricing cache (deprecated)")
        logger.info(f"✓ Pricing cache saved successfully")
        
        # Save spell details cache
        logger.info(f"Saving spell details cache ({len(spell_details_cache)} entries) to {SPELL_DETAILS_CACHE_FILE}")
        with open(SPELL_DETAILS_CACHE_FILE, 'w') as f:
            json.dump(spell_details_cache, f, indent=2)
        logger.info(f"✓ Spell details cache saved successfully")
        
        # Save metadata
        metadata = {
            'cache_timestamp': cache_timestamp,
            'pricing_cache_timestamp': pricing_cache_timestamp,
            'last_scrape_time': last_scrape_time,
            'last_updated': datetime.now().isoformat()
        }
        logger.info(f"Saving metadata ({len(cache_timestamp)} classes) to {METADATA_CACHE_FILE}")
        with open(METADATA_CACHE_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Metadata cache saved successfully")
            
        logger.info(f"✓ Successfully saved all cache files")
        logger.info(f"=== FILE CACHE SAVE COMPLETE ===")
        
    except Exception as e:
        logger.error(f"✗ Error saving cache to files: {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

# Load existing cache on startup
load_cache_from_storage()



def is_cache_expired(class_name):
    """Check if spell cache entry is expired (24 hours)"""
    # Use lowercase class name for cache lookups since cache keys are stored in lowercase
    cache_key = class_name.lower()
    if cache_key not in cache_timestamp:
        return True
    
    cache_time = datetime.fromisoformat(cache_timestamp[cache_key])
    expiry_time = cache_time + timedelta(hours=CACHE_EXPIRY_HOURS)
    return datetime.now() > expiry_time

def is_pricing_cache_expired(spell_id):
    """Check if pricing cache entry is expired (1 week)"""
    spell_id = str(spell_id)
    if spell_id not in pricing_cache_timestamp:
        return True
    
    cache_time = datetime.fromisoformat(pricing_cache_timestamp[spell_id])
    expiry_time = cache_time + timedelta(hours=PRICING_CACHE_EXPIRY_HOURS)
    return datetime.now() > expiry_time

def clear_expired_cache():
    """Remove expired cache entries for both spells and pricing"""
    expired_classes = []
    expired_pricing = []
    
    # Check spell cache expiry (24 hours)
    for class_name in list(cache_timestamp.keys()):
        if is_cache_expired(class_name):
            expired_classes.append(class_name)
    
    # Check pricing cache expiry (1 week)
    for spell_id in list(pricing_cache_timestamp.keys()):
        if is_pricing_cache_expired(spell_id):
            expired_pricing.append(spell_id)
    
    # Clear expired spell cache entries
    for class_name in expired_classes:
        spells_cache.pop(class_name, None)
        cache_timestamp.pop(class_name, None)
        logger.info(f"Cleared expired spell cache for {class_name}")
    
    # Clear expired pricing cache entries
    for spell_id in expired_pricing:
        # Remove pricing from spell_details_cache but preserve other details
        if spell_id in spell_details_cache:
            spell_details_cache[spell_id].pop('pricing', None)
            # Remove entire entry if it only contained pricing
            if not spell_details_cache[spell_id]:
                spell_details_cache.pop(spell_id, None)
        pricing_lookup.pop(spell_id, None)
        pricing_cache_timestamp.pop(spell_id, None)
        logger.info(f"Cleared expired pricing cache for spell {spell_id}")
    
    # Save changes to storage if any entries were cleared
    if expired_classes or expired_pricing:
        save_cache_to_storage()

def can_scrape_class(class_name):
    """Check if enough time has passed since last scrape for rate limiting"""
    # Use lowercase class name for cache lookups since cache keys are stored in lowercase
    cache_key = class_name.lower()
    if cache_key not in last_scrape_time:
        return True
    
    last_scrape = datetime.fromisoformat(last_scrape_time[cache_key])
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
        
        # Check if we have cached data (don't auto-clear expired)
        # Use lowercase class name for cache lookups since cache keys are stored in lowercase
        cache_key = class_name_lower
        if cache_key in spells_cache:
            is_expired = is_cache_expired(cache_key)
            logger.info(f"Serving cached data for {class_name} (cache_key: {cache_key}, expired: {is_expired})")
            
            # Efficiently fetch pricing for this class's spells using PostgreSQL
            applied_pricing_count = 0
            applied_failed_count = 0
            
            if USE_DATABASE_CACHE:
                spell_ids = [str(spell.get('spell_id', '')) for spell in spells_cache[cache_key]]
                pricing_data = get_bulk_pricing_from_db(spell_ids)
                
                # Apply pricing to spells efficiently using dictionary lookup
                for spell in spells_cache[cache_key]:
                    spell_id = str(spell.get('spell_id', ''))
                    pricing = pricing_data.get(spell_id)
                    if pricing:
                        spell['pricing'] = pricing
                        applied_pricing_count += 1
                        if pricing.get('unknown') == True:
                            applied_failed_count += 1
            else:
                # Fallback to in-memory lookup for file-based cache
                if pricing_lookup:
                    for spell in spells_cache[cache_key]:
                        spell_id = str(spell.get('spell_id', ''))
                        pricing = pricing_lookup.get(spell_id)
                        if pricing:
                            spell['pricing'] = pricing
                            applied_pricing_count += 1
                            if pricing.get('unknown') == True:
                                applied_failed_count += 1
            
            logger.info(f"CACHED: Applied pricing to {applied_pricing_count} spells (including {applied_failed_count} failed attempts)")
            
            return jsonify({
                'spells': spells_cache[cache_key],
                'cached': True,
                'expired': is_expired,
                'last_updated': cache_timestamp[cache_key],
                'spell_count': len(spells_cache[cache_key])
            })
        
        # Check rate limiting before scraping
        if not can_scrape_class(class_name):
            time_since_last = datetime.now() - datetime.fromisoformat(last_scrape_time[cache_key])
            wait_time = MIN_SCRAPE_INTERVAL_MINUTES - time_since_last.total_seconds() / 60
            logger.warning(f"Rate limited: {class_name} was scraped too recently. Wait {wait_time:.1f} minutes.")
            
            # Return stale cache if available, or error
            if cache_key in spells_cache:
                is_expired = is_cache_expired(cache_key)
                
                # Efficiently fetch pricing for this class's spells using PostgreSQL
                if USE_DATABASE_CACHE:
                    spell_ids = [str(spell.get('spell_id', '')) for spell in spells_cache[cache_key]]
                    pricing_data = get_bulk_pricing_from_db(spell_ids)
                    
                    # Apply pricing to spells
                    for spell in spells_cache[cache_key]:
                        spell_id = str(spell.get('spell_id', ''))
                        if spell_id in pricing_data:
                            spell['pricing'] = pricing_data[spell_id]
                else:
                    # Fallback to in-memory lookup for file-based cache
                    if pricing_lookup:
                        for spell in spells_cache[cache_key]:
                            spell_id = str(spell.get('spell_id', ''))
                            if spell_id in pricing_lookup:
                                spell['pricing'] = pricing_lookup[spell_id]
                
                return jsonify({
                    'spells': spells_cache[cache_key],
                    'cached': True,
                    'expired': is_expired,
                    'stale': True,
                    'message': f'Using stale cache data. Please wait {wait_time:.1f} minutes before requesting fresh data.',
                    'last_updated': cache_timestamp[cache_key]
                })
            else:
                return jsonify({
                    'error': f'Rate limited. Please wait {wait_time:.1f} minutes before trying again.',
                    'retry_after_minutes': wait_time
                }), 429
        
        logger.info(f"Scraping fresh data for {class_name}")
        
        # Log scrape start activity
        if ENABLE_USER_ACCOUNTS:
            log_scrape_activity(
                action='scrape_start',
                class_name=class_name,
                details={'trigger': 'api_request'}
            )
        
        # Scrape the data with timeout
        start_time = time.time()
        df = scrape_class(class_name, 'https://alla.clumsysworld.com/', None)
        scrape_time = time.time() - start_time
        
        if df is None or df.empty:
            logger.error(f"No spells found for {class_name} after trying all scraping methods")
            
            # Log scrape error
            if ENABLE_USER_ACCOUNTS:
                log_scrape_activity(
                    action='scrape_error',
                    class_name=class_name,
                    details={'error': 'No spells found', 'scrape_time': scrape_time}
                )
            
            return jsonify({
                'error': f'No spells found for {class_name}',
                'suggestion': 'Check backend logs for scraping details',
                'message': 'Scraping unsuccessful - check alla.clumsysworld.com availability'
            }), 404
        
        # Convert DataFrame to list of dictionaries
        # The new scraper returns DataFrame with lowercase column names and proper data types
        spells = []
        for _, row in df.iterrows():
            spell = {
                'name': row.get('name', ''),
                'level': row.get('level', 0),  # Already an int from scraper
                'mana': row.get('mana', ''),
                'skill': row.get('skill', ''),
                'target_type': row.get('target_type', ''),
                'spell_id': row.get('spell_id', ''),
                'effects': row.get('effects', ''),
                'icon': row.get('icon', ''),
                'pricing': None  # Pricing will be populated on-demand from spell details
            }
            spells.append(spell)
        
        # Apply existing pricing data to newly scraped spells
        applied_pricing_count = 0
        applied_failed_count = 0
        
        if USE_DATABASE_CACHE:
            spell_ids = [str(spell.get('spell_id', '')) for spell in spells]
            pricing_data = get_bulk_pricing_from_db(spell_ids)
            
            logger.info(f"Found {len(pricing_data)} pricing entries for {len(spell_ids)} spells")
            
            # Apply pricing to spells (including unknown: true entries)
            for spell in spells:
                spell_id = str(spell.get('spell_id', ''))
                if spell_id in pricing_data:
                    spell['pricing'] = pricing_data[spell_id]
                    applied_pricing_count += 1
                    if pricing_data[spell_id].get('unknown') == True:
                        applied_failed_count += 1
        else:
            # Fallback to in-memory lookup for file-based cache
            if pricing_lookup:
                logger.info(f"Using in-memory pricing lookup with {len(pricing_lookup)} entries")
                for spell in spells:
                    spell_id = str(spell.get('spell_id', ''))
                    if spell_id in pricing_lookup:
                        spell['pricing'] = pricing_lookup[spell_id]
                        applied_pricing_count += 1
                        if pricing_lookup[spell_id].get('unknown') == True:
                            applied_failed_count += 1
        
        logger.info(f"Applied pricing to {applied_pricing_count} spells (including {applied_failed_count} failed attempts)")
        
        # Debug: Check a few sample spells
        sample_spells = spells[:3]
        for spell in sample_spells:
            spell_id = spell.get('spell_id', '')
            pricing = spell.get('pricing')
            logger.info(f"Sample spell {spell_id}: pricing = {pricing}")
        
        # Cache the data (with pricing applied)
        # Use lowercase class name for cache keys for consistency
        current_time = datetime.now().isoformat()
        spells_cache[cache_key] = spells
        cache_timestamp[cache_key] = current_time
        last_scrape_time[cache_key] = current_time
        
        # Save to disk after successful scrape
        save_cache_to_storage()
        
        logger.info(f"Successfully scraped {len(spells)} spells for {class_name} in {scrape_time:.2f}s")
        
        # Log successful scrape
        if ENABLE_USER_ACCOUNTS:
            log_scrape_activity(
                action='scrape_complete',
                class_name=class_name,
                details={
                    'spell_count': len(spells),
                    'scrape_time': round(scrape_time, 2),
                    'pricing_applied': applied_pricing_count
                }
            )
        
        return jsonify({
            'spells': spells,
            'cached': False,
            'last_updated': cache_timestamp[cache_key],
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
        
        # Log scrape start activity
        if ENABLE_USER_ACCOUNTS:
            log_scrape_activity(
                action='scrape_start',
                details={'classes': 'all', 'trigger': 'manual'}
            )
        
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
                            'name': row.get('name', ''),
                            'level': row.get('level', 0),
                            'mana': row.get('mana', ''),
                            'skill': row.get('skill', ''),
                            'target_type': row.get('target_type', ''),
                            'spell_id': row.get('spell_id', ''),
                            'effects': row.get('effects', ''),
                            'icon': row.get('icon', ''),
                            'pricing': None  # Will be populated when spell details are requested
                        }
                        spells.append(spell)
                    
                    # Apply existing pricing data to newly scraped spells
                    if USE_DATABASE_CACHE:
                        spell_ids = [str(spell.get('spell_id', '')) for spell in spells]
                        pricing_data = get_bulk_pricing_from_db(spell_ids)
                        
                        # Apply pricing to spells (including unknown: true entries)
                        for spell in spells:
                            spell_id = str(spell.get('spell_id', ''))
                            if spell_id in pricing_data:
                                spell['pricing'] = pricing_data[spell_id]
                    else:
                        # Fallback to in-memory lookup for file-based cache
                        if pricing_lookup:
                            for spell in spells:
                                spell_id = str(spell.get('spell_id', ''))
                                if spell_id in pricing_lookup:
                                    spell['pricing'] = pricing_lookup[spell_id]
                    
                    # Use lowercase class name for cache keys for consistency
                    cache_key = class_name.lower()
                    spells_cache[cache_key] = spells
                    cache_timestamp[cache_key] = datetime.now().isoformat()
            except Exception as e:
                print(f"Error scraping {class_name}: {e}")
        
        # Save to disk after scraping all classes
        save_cache_to_storage()
        
        # Log successful completion
        if ENABLE_USER_ACCOUNTS:
            total_spells = sum(len(spells) for spells in spells_cache.values())
            log_scrape_activity(
                action='scrape_complete',
                details={
                    'classes': 'all',
                    'classes_count': len(spells_cache),
                    'total_spells': total_spells
                }
            )
        
        return jsonify({
            'message': 'All classes scraped successfully',
            'classes_scraped': list(spells_cache.keys()),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        # Log scrape error
        if ENABLE_USER_ACCOUNTS:
            log_scrape_activity(
                action='scrape_error',
                details={'error': str(e), 'classes': 'all'}
            )
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

@app.route('/api/classes', methods=['GET'])
def get_classes_list():
    """Get list of all available classes"""
    classes_list = []
    for class_name, color in CLASSES.items():
        classes_list.append({
            'name': class_name,
            'color': color,
            'api_name': class_name.lower()
        })
    return jsonify(classes_list)

@app.route('/api/cache-status', methods=['GET'])
def get_cache_status():
    """Get cache status for all classes"""
    status = {}
    for class_name in CLASSES.keys():
        class_name_lower = class_name.lower()
        status[class_name] = {
            'cached': class_name_lower in spells_cache,
            'spell_count': len(spells_cache.get(class_name_lower, [])),
            'last_updated': cache_timestamp.get(class_name_lower)
        }
    
    # Add cache expiry configuration
    status['_config'] = {
        'spell_cache_expiry_hours': CACHE_EXPIRY_HOURS,
        'pricing_cache_expiry_hours': PRICING_CACHE_EXPIRY_HOURS,
        'min_scrape_interval_minutes': MIN_SCRAPE_INTERVAL_MINUTES
    }
    
    return jsonify(status)

@app.route('/api/cache-expiry-status/<class_name>', methods=['GET'])
def get_cache_expiry_status(class_name):
    """Get cache expiry status for a specific class"""
    # Normalize class name - handle special cases (same logic as /api/spells endpoint)
    class_name_lower = class_name.lower()
    
    # Map common variations to correct case
    class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
    
    if class_name_lower in class_name_map:
        normalized_class_name = class_name_map[class_name_lower]
    else:
        # Fallback to title case for unknown names
        normalized_class_name = class_name.title()
    
    if normalized_class_name not in CLASSES:
        return jsonify({'error': 'Invalid class name'}), 400
    
    class_name = class_name_lower  # Use lowercase for cache lookups
    
    # Check spell cache status
    spell_cached = class_name in spells_cache
    spell_expired = is_cache_expired(class_name) if spell_cached else True
    spell_timestamp = cache_timestamp.get(class_name)
    
    # Count pricing entries for this class from spell_details_cache
    class_spells = spells_cache.get(class_name, [])
    pricing_count = 0
    pricing_expired_count = 0
    most_recent_pricing_timestamp = None
    
    for spell in class_spells:
        spell_id = str(spell.get('spell_id', ''))
        if spell_id in spell_details_cache and spell_details_cache[spell_id].get('pricing'):
            pricing_data = spell_details_cache[spell_id]['pricing']
            # Only count spells that have actual pricing data (any coin > 0)
            if (pricing_data.get('platinum', 0) > 0 or 
                pricing_data.get('gold', 0) > 0 or 
                pricing_data.get('silver', 0) > 0 or 
                pricing_data.get('bronze', 0) > 0):
                pricing_count += 1
                if is_pricing_cache_expired(spell_id):
                    pricing_expired_count += 1
            
            # Track most recent pricing timestamp for this class
            pricing_timestamp = pricing_cache_timestamp.get(spell_id)
            if pricing_timestamp:
                if not most_recent_pricing_timestamp or pricing_timestamp > most_recent_pricing_timestamp:
                    most_recent_pricing_timestamp = pricing_timestamp
            else:
                # If pricing data exists but no timestamp, create one (migration scenario)
                if (pricing_data.get('platinum', 0) > 0 or pricing_data.get('gold', 0) > 0 or 
                    pricing_data.get('silver', 0) > 0 or pricing_data.get('bronze', 0) > 0):
                    current_time = datetime.now().isoformat()
                    pricing_cache_timestamp[spell_id] = current_time
                    if not most_recent_pricing_timestamp or current_time > most_recent_pricing_timestamp:
                        most_recent_pricing_timestamp = current_time
                    logger.info(f"Added missing timestamp for spell {spell_id} with existing pricing data")
    
    return jsonify({
        'class_name': class_name,
        'spells': {
            'cached': spell_cached,
            'expired': spell_expired,
            'timestamp': spell_timestamp,
            'count': len(class_spells)
        },
        'pricing': {
            'cached_count': pricing_count,
            'expired_count': pricing_expired_count,
            'total_spells': len(class_spells),
            'most_recent_timestamp': most_recent_pricing_timestamp
        },
        'expiry_config': {
            'spell_cache_hours': CACHE_EXPIRY_HOURS,
            'pricing_cache_hours': PRICING_CACHE_EXPIRY_HOURS
        }
    })

@app.route('/api/refresh-progress/<class_name>', methods=['GET'])
def get_refresh_progress(class_name):
    """Get current refresh progress for a specific class"""
    class_name = class_name.lower()
    
    if class_name not in refresh_progress:
        return jsonify({'error': 'No refresh in progress for this class'}), 404
    
    return jsonify(refresh_progress[class_name])

@app.route('/api/refresh-spell-cache/<class_name>', methods=['POST'])
def refresh_spell_cache(class_name):
    """Manually refresh spell cache for a specific class with progress tracking"""
    # Normalize class name - handle special cases (same logic as /api/spells endpoint)
    class_name_lower = class_name.lower()
    
    # Map common variations to correct case
    class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
    
    if class_name_lower in class_name_map:
        normalized_class_name = class_name_map[class_name_lower]
    else:
        # Fallback to title case for unknown names
        normalized_class_name = class_name.title()
    
    if normalized_class_name not in CLASSES:
        return jsonify({'error': 'Invalid class name'}), 400
    
    class_name = class_name_lower  # Use lowercase for cache lookups
    
    try:
        # Initialize progress tracking
        update_refresh_progress(class_name, 'initializing')
        
        # Return immediately with success response
        # Start the actual refresh operation asynchronously
        def perform_refresh():
            try:
                # Small delay to ensure tests can check initial state
                time.sleep(0.1)
                
                # Force refresh by removing from cache
                spells_cache.pop(class_name, None)
                cache_timestamp.pop(class_name, None)
                last_scrape_time[class_name] = datetime.now().isoformat()
                
                # Update progress to scraping stage
                update_refresh_progress(class_name, 'scraping', 
                                      estimated_time_remaining=30)
                
                # Trigger fresh scrape
                logger.info(f"Starting scrape for {normalized_class_name}")
                df = scrape_class(normalized_class_name, 'https://alla.clumsysworld.com/', None)
                
                if df is not None and not df.empty:
                    new_spells = df.to_dict('records')
                    update_refresh_progress(class_name, 'processing', progress_percentage=60, estimated_time_remaining=15)
                    
                    # Update cache
                    update_refresh_progress(class_name, 'updating_cache', progress_percentage=80, estimated_time_remaining=10)
                    spells_cache[class_name] = new_spells
                    cache_timestamp[class_name] = datetime.now().isoformat()
                    
                    # Save to storage with progress tracking
                    try:
                        update_refresh_progress(class_name, 'updating_cache', progress_percentage=85, message='💾 Saving to database...')
                        # Only save the specific class that was just scraped
                        save_single_class_to_storage(class_name)
                        update_refresh_progress(class_name, 'loading_memory', progress_percentage=95, estimated_time_remaining=2)
                    except Exception as e:
                        logger.error(f"Error saving cache to storage: {e}")
                        # Continue anyway, cache is in memory
                    
                    time.sleep(0.5)
                    update_refresh_progress(class_name, 'complete', progress_percentage=100)
                    
                    # Clear progress after a delay
                    def clear_progress_later():
                        time.sleep(5)
                        clear_refresh_progress(class_name)
                    
                    import threading
                    clear_thread = threading.Thread(target=clear_progress_later)
                    clear_thread.daemon = True
                    clear_thread.start()
                    
                    # Log activity if user accounts are enabled
                    if ENABLE_USER_ACCOUNTS:
                        user_id = getattr(g, 'user_id', None)
                        if user_id:
                            log_scrape_activity(user_id, normalized_class_name, len(new_spells), 'success')
                    
                else:
                    update_refresh_progress(class_name, 'error', message='❌ Failed to scrape new data')
                    
                    # Log failed activity if user accounts are enabled
                    if ENABLE_USER_ACCOUNTS:
                        user_id = getattr(g, 'user_id', None)
                        if user_id:
                            log_scrape_activity(user_id, normalized_class_name, 0, 'failed')
                    
            except Exception as e:
                logger.error(f"Error refreshing spell cache for {class_name}: {e}")
                # Update progress to error state
                update_refresh_progress(class_name, 'error', 
                                      message=f'❌ Error: {str(e)}')
        
        # Start the refresh operation in a background thread
        import threading
        refresh_thread = threading.Thread(target=perform_refresh)
        refresh_thread.daemon = True
        refresh_thread.start()
        
        # Return immediately with success response
        return jsonify({
            'success': True,
            'message': 'Refresh started',
            'class_name': class_name
        })
            
    except Exception as e:
        logger.error(f"Error starting refresh for {class_name}: {e}")
        # Update progress to error state
        update_refresh_progress(class_name, 'error', 
                              message=f'❌ Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh-pricing-cache/<class_name>', methods=['POST'])
def refresh_pricing_cache_for_class(class_name):
    """Manually refresh pricing cache for all spells in a class"""
    # Normalize class name - handle special cases (same logic as /api/spells endpoint)
    class_name_lower = class_name.lower()
    
    # Map common variations to correct case
    class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
    
    if class_name_lower in class_name_map:
        normalized_class_name = class_name_map[class_name_lower]
    else:
        # Fallback to title case for unknown names
        normalized_class_name = class_name.title()
    
    if normalized_class_name not in CLASSES:
        return jsonify({'error': 'Invalid class name'}), 400
    
    class_name = class_name_lower  # Use lowercase for cache lookups
    
    try:
        class_spells = spells_cache.get(class_name, [])
        if not class_spells:
            return jsonify({'error': 'No spells found for class. Refresh spell data first.'}), 400
        
        # Get spell IDs to refresh
        spell_ids = [spell.get('spell_id') for spell in class_spells if spell.get('spell_id')]
        
        if not spell_ids:
            return jsonify({'error': 'No valid spell IDs found'}), 400
        
        # Clear existing pricing data for these spells
        refreshed_count = 0
        for spell_id in spell_ids:
            spell_id_str = str(spell_id)
            cleared = False
            if spell_id_str in pricing_cache_timestamp:
                pricing_cache_timestamp.pop(spell_id_str, None)
                cleared = True
            if spell_id_str in pricing_lookup:
                pricing_lookup.pop(spell_id_str, None)
                cleared = True
            if spell_id_str in spell_details_cache:
                spell_details_cache[spell_id_str].pop('pricing', None)
                # Remove entire entry if it only contained pricing
                if not spell_details_cache[spell_id_str]:
                    spell_details_cache.pop(spell_id_str, None)
                cleared = True
            if cleared:
                refreshed_count += 1
        
        return jsonify({
            'success': True,
            'class_name': class_name,
            'cleared_count': refreshed_count,
            'total_spells': len(spell_ids),
            'message': f'Cleared pricing cache for {refreshed_count} spells. New pricing will be fetched on next request.'
        })
        
    except Exception as e:
        logger.error(f"Error refreshing pricing cache for {class_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/retry-failed-pricing/<class_name>', methods=['POST'])
def retry_failed_pricing_for_class(class_name):
    """Retry pricing fetch for all previously failed spells in a class"""
    # Normalize class name - handle special cases (same logic as /api/spells endpoint)
    class_name_lower = class_name.lower()
    
    # Map common variations to correct case
    class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
    
    if class_name_lower in class_name_map:
        normalized_class_name = class_name_map[class_name_lower]
    else:
        # Fallback to title case for unknown names
        normalized_class_name = class_name.title()
    
    if normalized_class_name not in CLASSES:
        return jsonify({'error': 'Invalid class name'}), 400
    
    class_name = class_name_lower  # Use lowercase for cache lookups
    
    try:
        class_spells = spells_cache.get(class_name, [])
        if not class_spells:
            return jsonify({'error': 'No spells found for class. Refresh spell data first.'}), 400
        
        # Get spell IDs for this class
        spell_ids = [str(spell.get('spell_id')) for spell in class_spells if spell.get('spell_id')]
        
        if not spell_ids:
            return jsonify({'error': 'No valid spell IDs found'}), 400
        
        # Get failed spells that need retry
        failed_spells = get_failed_pricing_spells(spell_ids)
        
        if not failed_spells:
            return jsonify({
                'success': True,
                'class_name': class_name,
                'retried_count': 0,
                'total_spells': len(spell_ids),
                'message': 'No failed pricing attempts found to retry.'
            })
        
        # Clear the failed attempts from the database so they can be retried
        if USE_DATABASE_CACHE:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Reset the failed attempts for these spells
                cursor.execute("""
                    DELETE FROM pricing_fetch_attempts 
                    WHERE spell_id = ANY(%s) AND success = FALSE
                """, (failed_spells,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"Reset {len(failed_spells)} failed pricing attempts for {class_name}")
                
            except Exception as e:
                logger.error(f"Error resetting failed pricing attempts: {e}")
                return jsonify({'error': 'Failed to reset pricing attempts'}), 500
        
        return jsonify({
            'success': True,
            'class_name': class_name,
            'retried_count': len(failed_spells),
            'total_spells': len(spell_ids),
            'failed_spells': failed_spells,
            'message': f'Reset {len(failed_spells)} failed pricing attempts. These spells will be automatically retried when the page loads.'
        })
        
    except Exception as e:
        logger.error(f"Error retrying failed pricing for {class_name}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge-pricing-cache', methods=['POST'])
def merge_pricing_cache():
    """Merge pricing data from UI into the cache"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        class_name = data.get('class_name', '').lower()
        pricing_data = data.get('pricing_data', [])
        
        if not class_name or not pricing_data:
            return jsonify({'error': 'Missing class_name or pricing_data'}), 400
        
        # Normalize class name for validation - handle special cases
        class_name_map = {cls.lower(): cls for cls in CLASSES.keys()}
        
        if class_name in class_name_map:
            normalized_class_name = class_name_map[class_name]
        else:
            # Fallback to title case for unknown names
            normalized_class_name = class_name.title()
        
        if normalized_class_name not in CLASSES:
            return jsonify({'error': 'Invalid class name'}), 400
        
        merged_count = 0
        current_time = datetime.now().isoformat()
        
        # Merge each pricing entry into the cache
        for entry in pricing_data:
            spell_id = str(entry.get('spell_id', ''))
            pricing = entry.get('pricing')
            
            if spell_id and pricing and isinstance(pricing, dict):
                # Add to pricing cache
                # pricing_cache deprecated - pricing stored in spell_details_cache
                pricing_cache_timestamp[spell_id] = current_time
                merged_count += 1
                logger.info(f"Merged pricing for spell {spell_id}: {pricing}")
        
        # Save to persistent storage
        save_cache_to_storage()
        
        logger.info(f"Successfully merged {merged_count} pricing entries for {class_name}")
        
        return jsonify({
            'success': True,
            'class_name': class_name,
            'merged_count': merged_count,
            'total_entries': len(pricing_data),
            'message': f'Successfully merged {merged_count} pricing entries into cache.'
        })
        
    except Exception as e:
        logger.error(f"Error merging pricing cache: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spell-states/<class_name>', methods=['GET'])
def get_spell_states(class_name):
    """Get pricing states for spells in a class (untried, failed, success)"""
    try:
        # Normalize class name
        class_name_lower = class_name.lower()
        
        if class_name_lower not in [cls.lower() for cls in CLASSES.keys()]:
            return jsonify({'error': 'Invalid class name'}), 400
        
        # Get spells for this class
        class_spells = spells_cache.get(class_name_lower, [])
        if not class_spells:
            return jsonify({'unfetched': [], 'failed': [], 'success': []})
        
        spell_ids = [str(spell.get('spell_id', '')) for spell in class_spells if spell.get('spell_id')]
        
        # Get different spell states
        unfetched_spells = get_unfetched_spells(spell_ids)
        failed_spells = get_failed_pricing_spells(spell_ids)
        success_spells = [sid for sid in spell_ids if sid in pricing_lookup]
        
        return jsonify({
            'unfetched': unfetched_spells,
            'failed': failed_spells, 
            'success': success_spells,
            'total': len(spell_ids)
        })
        
    except Exception as e:
        logger.error(f"Error getting spell states for {class_name}: {e}")
        return jsonify({'error': 'Failed to get spell states'}), 500

@app.route('/api/spell-details/<int:spell_id>', methods=['GET'])
def get_spell_details(spell_id):
    """Get detailed spell information from alla website"""
    try:
        spell_id_str = str(spell_id)
        
        # Check cache first
        if spell_id_str in spell_details_cache:
            logger.info(f"Serving cached spell details for ID {spell_id}")
            return jsonify(spell_details_cache[spell_id_str])
        
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
        logger.info(f"Fetching fresh spell details for ID {spell_id} from {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        details = parse_spell_details_from_html(soup)
        
        # Cache the result
        spell_details_cache[spell_id_str] = details
        
        # Update in-memory pricing cache when new pricing is found
        pricing_success = False
        if details.get('pricing'):
            logger.info(f"Found vendor pricing: {details['pricing']}")
            # Update the in-memory pricing lookup for immediate availability
            pricing_lookup[spell_id_str] = details['pricing']
            pricing_success = True
        else:
            # No pricing found - save as failed attempt so it's not retried
            logger.info(f"No pricing found for spell {spell_id} - marking as unknown")
            failed_pricing = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
            details['pricing'] = failed_pricing
            pricing_lookup[spell_id_str] = failed_pricing
        
        # Record the pricing fetch attempt
        record_pricing_fetch_attempt(spell_id_str, success=pricing_success)
        
        # Save cache immediately to ensure persistence
        save_cache_to_storage()
        
        logger.info(f"Successfully parsed and cached spell details for ID {spell_id}")
        
        # Log spell view activity
        if ENABLE_USER_ACCOUNTS:
            log_api_activity(
                action='spell_view',
                resource_type='spell',
                resource_id=spell_id_str,
                details={
                    'spell_name': details.get('name', 'Unknown'),
                    'has_pricing': pricing_success
                }
            )
        
        return jsonify(details)
        
    except requests.exceptions.Timeout:
        error_msg = 'Request timed out'
        logger.error(f"Timeout while fetching spell details for ID {spell_id}")
        record_pricing_fetch_attempt(spell_id_str, success=False, error_message=error_msg)
        
        # Save failed pricing attempt to cache so it's not retried
        failed_details = {'pricing': {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}}
        spell_details_cache[spell_id_str] = failed_details
        pricing_lookup[spell_id_str] = failed_details['pricing']
        save_cache_to_storage()
        
        return jsonify(failed_details), 504
    except requests.exceptions.ConnectionError as e:
        error_msg = 'Unable to connect to spell database'
        logger.error(f"Connection error for spell ID {spell_id}: {e}")
        record_pricing_fetch_attempt(spell_id_str, success=False, error_message=error_msg)
        
        # Save failed pricing attempt to cache so it's not retried
        failed_details = {'pricing': {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}}
        spell_details_cache[spell_id_str] = failed_details
        pricing_lookup[spell_id_str] = failed_details['pricing']
        save_cache_to_storage()
        
        return jsonify(failed_details), 503
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code} for spell ID {spell_id}")
        if e.response.status_code == 404:
            error_msg = 'Spell not found'
            record_pricing_fetch_attempt(spell_id_str, success=False, error_message=error_msg)
            
            # Save failed pricing attempt to cache so it's not retried
            failed_details = {'pricing': {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}}
            spell_details_cache[spell_id_str] = failed_details
            pricing_lookup[spell_id_str] = failed_details['pricing']
            save_cache_to_storage()
            
            return jsonify(failed_details), 404
        error_msg = f'Server error ({e.response.status_code})'
        record_pricing_fetch_attempt(spell_id_str, success=False, error_message=error_msg)
        
        # Save failed pricing attempt to cache so it's not retried
        failed_details = {'pricing': {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}}
        spell_details_cache[spell_id_str] = failed_details
        pricing_lookup[spell_id_str] = failed_details['pricing']
        save_cache_to_storage()
        
        return jsonify(failed_details), e.response.status_code
    except Exception as e:
        error_msg = 'Failed to fetch spell details'
        logger.error(f"Unexpected error fetching spell details for ID {spell_id}: {e}")
        record_pricing_fetch_attempt(spell_id_str, success=False, error_message=error_msg)
        
        # Save failed pricing attempt to cache so it's not retried
        failed_details = {'pricing': {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}}
        spell_details_cache[spell_id_str] = failed_details
        pricing_lookup[spell_id_str] = failed_details['pricing']
        save_cache_to_storage()
        
        return jsonify(failed_details), 500

def extract_scroll_pricing(items_with_spell):
    """Extract pricing from scroll/spell items"""
    import requests
    from bs4 import BeautifulSoup
    import re
    
    if not items_with_spell:
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    # Prioritize spell items first, then scrolls, then other items
    spell_items = [item for item in items_with_spell if item.get('name', '').lower().startswith('spell:')]
    scroll_items = [item for item in items_with_spell if 'scroll' in item.get('name', '').lower()]
    other_items = [item for item in items_with_spell if not item.get('name', '').lower().startswith('spell:') and 'scroll' not in item.get('name', '').lower()]
    
    # Check items in priority order: spell items first, then scrolls, then others
    items_to_check = spell_items + scroll_items + other_items[:3]
    
    logger.info(f"Found {len(spell_items)} spell items, {len(scroll_items)} scroll items, {len(other_items)} other items")
    if spell_items:
        logger.info(f"Prioritizing spell items: {[item.get('name') for item in spell_items]}")
    
    for item in items_to_check:
        try:
            if not item.get('item_id'):
                continue
                
            item_url = f"https://alla.clumsysworld.com/?a=item&id={item['item_id']}"
            logger.info(f"Fetching pricing from item: {item_url}")
            
            response = requests.get(item_url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            pricing = parse_item_pricing(soup)
            
            if pricing and any(pricing.values()):
                logger.info(f"Found pricing for {item.get('name')}: {pricing}")
                return pricing
                
        except Exception as e:
            logger.warning(f"Error extracting pricing from {item.get('name', 'unknown')}: {e}")
            continue
    
    return None

def parse_item_pricing(soup):
    """Parse pricing information from an item page"""
    import re
    
    pricing = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0}
    
    try:
        # Look for vendor pricing in format like "(4s)" or "(2g 5s)" - this is what players pay
        page_text = soup.get_text()
        
        # Pattern to match pricing like (4s), (2g), (1p 5g 10s), etc.
        price_patterns = [
            r'\((\d+)p\s+(\d+)g\s+(\d+)s\s+(\d+)c\)',  # full format
            r'\((\d+)p\s+(\d+)g\s+(\d+)s\)',  # plat gold silver
            r'\((\d+)g\s+(\d+)s\s+(\d+)c\)',  # gold silver copper
            r'\((\d+)p\s+(\d+)g\)',  # plat gold
            r'\((\d+)g\s+(\d+)s\)',  # gold silver  
            r'\((\d+)p\s+(\d+)s\)',  # plat silver
            r'\((\d+)s\s+(\d+)c\)',  # silver copper
            r'\((\d+)p\)',  # platinum only
            r'\((\d+)g\)',  # gold only
            r'\((\d+)s\)',  # silver only
            r'\((\d+)c\)',  # copper only
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                match = matches[0]  # Take the first match
                
                if pattern == r'\((\d+)p\s+(\d+)g\s+(\d+)s\s+(\d+)c\)':
                    pricing['platinum'] = int(match[0])
                    pricing['gold'] = int(match[1])
                    pricing['silver'] = int(match[2])
                    pricing['bronze'] = int(match[3])
                elif pattern == r'\((\d+)p\s+(\d+)g\s+(\d+)s\)':
                    pricing['platinum'] = int(match[0])
                    pricing['gold'] = int(match[1])
                    pricing['silver'] = int(match[2])
                elif pattern == r'\((\d+)g\s+(\d+)s\s+(\d+)c\)':
                    pricing['gold'] = int(match[0])
                    pricing['silver'] = int(match[1])
                    pricing['bronze'] = int(match[2])
                elif pattern == r'\((\d+)p\s+(\d+)g\)':
                    pricing['platinum'] = int(match[0])
                    pricing['gold'] = int(match[1])
                elif pattern == r'\((\d+)g\s+(\d+)s\)':
                    pricing['gold'] = int(match[0])
                    pricing['silver'] = int(match[1])
                elif pattern == r'\((\d+)p\s+(\d+)s\)':
                    pricing['platinum'] = int(match[0])
                    pricing['silver'] = int(match[1])
                elif pattern == r'\((\d+)s\s+(\d+)c\)':
                    pricing['silver'] = int(match[0])
                    pricing['bronze'] = int(match[1])
                elif pattern == r'\((\d+)p\)':
                    pricing['platinum'] = int(match)
                elif pattern == r'\((\d+)g\)':
                    pricing['gold'] = int(match)
                elif pattern == r'\((\d+)s\)':
                    pricing['silver'] = int(match)
                elif pattern == r'\((\d+)c\)':
                    pricing['bronze'] = int(match)
                
                # If we found any pricing, return it
                if any(pricing.values()):
                    logger.info(f"Found vendor pricing: {pricing}")
                    return pricing
        
        # Fallback: Look for price/value information in tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_cell = cells[1]
                    
                    # Look for price/value/cost labels
                    if any(keyword in label for keyword in ['price', 'value', 'cost', 'worth']):
                        # Look for coin images and associated values
                        coins_found = extract_coins_from_cell(value_cell)
                        if coins_found:
                            pricing.update(coins_found)
                            return pricing
                        
                        # Fallback: try to parse text for coin values
                        value_text = value_cell.get_text(strip=True)
                        text_coins = parse_coin_text(value_text)
                        if text_coins:
                            pricing.update(text_coins)
                            return pricing
        
        # Alternative approach: look for coin images anywhere on the page with associated numbers
        coin_images = soup.find_all('img')
        for img in coin_images:
            src = img.get('src', '').lower()
            if any(coin in src for coin in ['plat', 'gold', 'silver', 'bronze', 'copper']):
                # Look for numbers near this coin image
                parent = img.find_parent(['td', 'div', 'span'])
                if parent:
                    coins_found = extract_coins_from_cell(parent)
                    if coins_found and any(coins_found.values()):
                        pricing.update(coins_found)
                        return pricing
        
    except Exception as e:
        logger.warning(f"Error parsing item pricing: {e}")
    
    return pricing

def extract_coins_from_cell(cell):
    """Extract coin values from a table cell containing coin images and values"""
    import re
    
    coins = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0}
    
    try:
        # Look for images with coin-related src attributes
        images = cell.find_all('img')
        
        for img in images:
            src = img.get('src', '').lower()
            
            # Identify coin type from image source
            coin_type = None
            if 'plat' in src:
                coin_type = 'platinum'
            elif 'gold' in src:
                coin_type = 'gold'
            elif 'silver' in src:
                coin_type = 'silver'
            elif 'bronze' in src or 'copper' in src:
                coin_type = 'bronze'
            
            if coin_type:
                # Look for a number near this coin image
                # Check previous and next siblings
                current = img
                value = None
                
                # Look backwards for a number
                for _ in range(3):  # Check up to 3 elements back
                    prev = current.previous_sibling
                    if prev:
                        if hasattr(prev, 'get_text'):
                            text = prev.get_text(strip=True)
                        else:
                            text = str(prev).strip()
                        
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            value = int(numbers[-1])  # Take the last number found
                            break
                        current = prev
                    else:
                        break
                
                # If no number found backwards, try forwards
                if value is None:
                    current = img
                    for _ in range(3):  # Check up to 3 elements forward
                        next_elem = current.next_sibling
                        if next_elem:
                            if hasattr(next_elem, 'get_text'):
                                text = next_elem.get_text(strip=True)
                            else:
                                text = str(next_elem).strip()
                            
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                value = int(numbers[0])  # Take the first number found
                                break
                            current = next_elem
                        else:
                            break
                
                if value is not None:
                    coins[coin_type] = value
                    
    except Exception as e:
        logger.warning(f"Error extracting coins from cell: {e}")
    
    return coins

def parse_coin_text(text):
    """Parse coin values from text like '5 platinum, 10 gold, 20 silver'"""
    import re
    
    coins = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0}
    
    try:
        # Look for patterns like "5 platinum", "10pp", etc.
        patterns = [
            (r'(\d+)\s*(?:platinum|plat|pp)', 'platinum'),
            (r'(\d+)\s*(?:gold|gp)', 'gold'),
            (r'(\d+)\s*(?:silver|sp)', 'silver'),
            (r'(\d+)\s*(?:bronze|copper|cp)', 'bronze')
        ]
        
        for pattern, coin_type in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                coins[coin_type] = int(matches[0])
                
    except Exception as e:
        logger.warning(f"Error parsing coin text: {e}")
    
    return coins

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
            
            # Extract pricing from the first scroll/spell item
            scroll_pricing = extract_scroll_pricing(items_with_spell)
            if scroll_pricing:
                details['pricing'] = scroll_pricing
            
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

@app.route('/api/search-spells', methods=['GET'])
def search_spells():
    """Search for spells across all classes"""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({
                'error': 'Query must be at least 2 characters long',
                'results': []
            }), 400
        
        # Class abbreviations mapping
        class_abbreviations = {
            'Cleric': 'CLR',
            'Rogue': 'ROG', 
            'Monk': 'MNK',
            'Enchanter': 'ENC',
            'Magician': 'MAG',
            'Wizard': 'WIZ',
            'Shaman': 'SHM',
            'Bard': 'BRD',
            'Ranger': 'RNG',
            'Beastlord': 'BST',
            'Berserker': 'BER',
            'Shadowknight': 'DRK',
            'Paladin': 'PAL',
            'Necromancer': 'NEC'
        }
        
        results = []
        query_lower = query.lower()
        
        # Search through cached spells from all classes
        for class_name, spells in spells_cache.items():
            class_abbrev = class_abbreviations.get(class_name, class_name[:3].upper())
            
            for spell in spells:
                spell_name = spell.get('name', '').lower()
                if query_lower in spell_name:
                    # Check if this spell is already in results (same spell_id)
                    existing_spell = None
                    for result in results:
                        if result.get('spell_id') == spell.get('spell_id'):
                            existing_spell = result
                            break
                    
                    if existing_spell:
                        # Add this class to the existing spell entry
                        if class_abbrev not in existing_spell['classes']:
                            existing_spell['classes'].append(class_abbrev)
                            existing_spell['class_names'].append(class_name)
                    else:
                        # Create new spell entry
                        results.append({
                            'name': spell.get('name', ''),
                            'level': spell.get('level', 0),
                            'mana': spell.get('mana', ''),
                            'spell_id': spell.get('spell_id', ''),
                            'icon': spell.get('icon', ''),
                            'classes': [class_abbrev],
                            'class_names': [class_name]
                        })
        
        # Sort results by spell name and limit to 50
        results.sort(key=lambda x: x['name'].lower())
        results = results[:50]
        
        # Log search activity
        if ENABLE_USER_ACCOUNTS:
            log_api_activity(
                action='spell_search',
                resource_type='spell',
                details={
                    'query': query,
                    'results_count': len(results)
                }
            )
        
        return jsonify({
            'results': results,
            'query': query,
            'total_found': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching spells: {e}")
        return jsonify({
            'error': 'Internal server error',
            'results': []
        }), 500

# Global session for connection pooling
import requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
})

# Pricing cache is already declared at the top with other global storage variables

def fetch_single_spell_pricing(spell_id, max_retries=2):
    """Fetch pricing for a single spell with retry logic"""
    # Check cache first (return even if expired - let frontend decide)
    # Check spell_details_cache instead of deprecated pricing_cache
    details = spell_details_cache.get(str(spell_id), {})
    if details.get('pricing'):
        return details['pricing']
    
    for attempt in range(max_retries + 1):
        try:
            from bs4 import BeautifulSoup
            
            url = f'https://alla.clumsysworld.com/?a=spell&id={spell_id}'
            response = session.get(url, timeout=8)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                details = parse_spell_details_from_html(soup)
                
                if details.get('pricing'):
                    result = details['pricing']
                else:
                    result = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
                    details['pricing'] = result
                
                # Cache the result in spell_details_cache and timestamp
                spell_details_cache[str(spell_id)] = details
                pricing_lookup[str(spell_id)] = result
                pricing_cache_timestamp[str(spell_id)] = datetime.now().isoformat()
                # Save cache periodically (every 10 new entries)
                if len(pricing_cache_timestamp) % 10 == 0:
                    save_cache_to_storage()
                return result
            else:
                if attempt == max_retries:
                    result = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
                    # Store failed pricing attempt in spell_details_cache
                    spell_details_cache[str(spell_id)] = {'pricing': result}
                    pricing_lookup[str(spell_id)] = result
                    pricing_cache_timestamp[str(spell_id)] = datetime.now().isoformat()
                    # Save on failure too
                    if len(pricing_cache_timestamp) % 10 == 0:
                        save_cache_to_storage()
                    return result
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for spell {spell_id}: {e}")
            if attempt == max_retries:
                result = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
                # Store failed pricing attempt in spell_details_cache
                spell_details_cache[str(spell_id)] = {'pricing': result}
                pricing_lookup[str(spell_id)] = result
                pricing_cache_timestamp[str(spell_id)] = datetime.now().isoformat()
                # Save on failure too
                if len(pricing_cache_timestamp) % 10 == 0:
                    save_cache_to_storage()
                return result
            
            # Exponential backoff: 0.5s, 1s, 2s
            time.sleep(0.5 * (2 ** attempt))
    
    # Fallback
    result = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
    # Store failed pricing attempt in spell_details_cache
    spell_details_cache[str(spell_id)] = {'pricing': result}
    pricing_lookup[str(spell_id)] = result
    pricing_cache_timestamp[str(spell_id)] = datetime.now().isoformat()
    # Save fallback too
    if len(pricing_cache_timestamp) % 10 == 0:
        save_cache_to_storage()
    return result

@app.route('/api/spell-pricing', methods=['POST'])
def get_spell_pricing():
    """Get pricing for multiple spells with optimized fetching"""
    try:
        spell_ids = request.json.get('spell_ids', [])
        if not spell_ids:
            return jsonify({'error': 'No spell IDs provided'}), 400
        
        # Reduce batch size for better reliability
        if len(spell_ids) > 5:
            return jsonify({'error': 'Maximum 5 spell IDs allowed per request'}), 400
        
        pricing_results = {}
        
        # Use threading for concurrent requests (but still rate limited)
        import threading
        import queue
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Use single thread to avoid overwhelming the server
        with ThreadPoolExecutor(max_workers=1) as executor:
            # Submit all tasks
            future_to_spell = {executor.submit(fetch_single_spell_pricing, spell_id): spell_id for spell_id in spell_ids}
            
            # Collect results as they complete
            for future in as_completed(future_to_spell):
                spell_id = future_to_spell[future]
                try:
                    result = future.result(timeout=12)  # Individual timeout
                    pricing_results[str(spell_id)] = result
                except Exception as e:
                    logger.error(f"Failed to get pricing for spell {spell_id}: {e}")
                    pricing_results[str(spell_id)] = {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0, 'unknown': True}
                
                # Rate limiting between requests
                time.sleep(0.5)
        
        # Save cache after batch processing
        save_cache_to_storage()
        
        return jsonify({
            'pricing': pricing_results,
            'fetched_count': len(pricing_results),
            'cached_count': len([s for s in spell_ids if str(s) in spell_details_cache and spell_details_cache[str(s)].get('pricing')])
        })
        
    except Exception as e:
        logger.error(f"Error in spell pricing endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/startup-status', methods=['GET'])
def startup_status():
    """Get server startup progress status"""
    return jsonify(server_startup_progress)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with server memory status"""
    # This endpoint should not be rate limited
    pricing_count = len(pricing_lookup) if 'pricing_lookup' in globals() else 0
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'cached_classes': len(spells_cache),
        'cached_pricing': pricing_count,  # Now shows actual pricing count
        'cached_spell_details': len(spell_details_cache),
        'server_memory_loaded': len(spells_cache) > 0 or pricing_count > 0,
        'ready_for_instant_responses': len(spells_cache) > 0 and pricing_count > 0,
        'startup_complete': server_startup_progress['startup_complete']
    })

@app.route('/api/cache/save', methods=['POST'])
def save_cache():
    """Manually save cache to disk"""
    try:
        save_cache_to_storage()
        
        # Log cache save activity
        if ENABLE_USER_ACCOUNTS:
            log_cache_activity(
                action='cache_save',
                details={
                    'cached_classes': len(spells_cache),
                    'cached_spell_details': len(spell_details_cache),
                    'trigger': 'manual'
                }
            )
        
        return jsonify({
            'message': 'Cache saved successfully',
            'timestamp': datetime.now().isoformat(),
            'cached_classes': len(spells_cache),
            'cached_pricing': 0,  # pricing_cache deprecated
        'cached_spell_details': len(spell_details_cache)
        })
    except Exception as e:
        logger.error(f"Error saving cache: {e}")
        return jsonify({'error': 'Failed to save cache'}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached data"""
    global spells_cache, cache_timestamp, last_scrape_time, spell_details_cache
    
    try:
        spells_cache.clear()
        cache_timestamp.clear()
        last_scrape_time.clear()
        # pricing_cache.clear() - deprecated
        spell_details_cache.clear()
        
        # Clear database cache if using database storage
        if USE_DATABASE_CACHE:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Clear database tables
                cursor.execute("DELETE FROM spell_cache")
                cursor.execute("DELETE FROM pricing_cache") 
                cursor.execute("DELETE FROM spell_details_cache")
                cursor.execute("DELETE FROM cache_metadata")
                
                conn.commit()
                cursor.close()
                conn.close()
                logger.info("✓ Database cache tables cleared")
            except Exception as e:
                logger.error(f"Error clearing database cache: {e}")
        else:
            # Remove cache files (fallback for local development)
            for cache_file in [SPELLS_CACHE_FILE, PRICING_CACHE_FILE, SPELL_DETAILS_CACHE_FILE, METADATA_CACHE_FILE]:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
        
        # Log cache clear activity
        if ENABLE_USER_ACCOUNTS:
            log_cache_activity(
                action='cache_clear',
                details={
                    'storage_type': 'database' if USE_DATABASE_CACHE else 'file',
                    'trigger': 'manual'
                }
            )
        
        return jsonify({
            'message': 'Cache cleared successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """Get detailed cache status"""
    storage_info = {}
    
    if USE_DATABASE_CACHE:
        # Get database table info
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Get row counts for each table
            cursor.execute("SELECT COUNT(*) FROM spell_cache")
            spell_cache_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pricing_cache")  
            pricing_cache_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM spell_details_cache")
            details_cache_rows = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cache_metadata")
            metadata_rows = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            storage_info = {
                'type': 'database',
                'tables': {
                    'spell_cache_rows': spell_cache_rows,
                    'pricing_cache_rows': pricing_cache_rows,
                    'spell_details_cache_rows': details_cache_rows,
                    'metadata_rows': metadata_rows
                },
                'database_url_available': True
            }
        except Exception as e:
            storage_info = {
                'type': 'database',
                'error': str(e),
                'database_url_available': True
            }
    else:
        # Get file system info
        cache_files_exist = {
            'spells': os.path.exists(SPELLS_CACHE_FILE),
            'pricing': os.path.exists(PRICING_CACHE_FILE),
            'metadata': os.path.exists(METADATA_CACHE_FILE)
        }
        
        cache_sizes = {}
        for name, path in [('spells', SPELLS_CACHE_FILE), ('pricing', PRICING_CACHE_FILE), ('metadata', METADATA_CACHE_FILE)]:
            if os.path.exists(path):
                cache_sizes[name] = os.path.getsize(path)
            else:
                cache_sizes[name] = 0
        
        storage_info = {
            'type': 'files',
            'files_exist': cache_files_exist,
            'file_sizes_bytes': cache_sizes,
            'cache_directory': CACHE_DIR,
            'cache_directory_exists': os.path.exists(CACHE_DIR),
            'cache_directory_writable': os.access(CACHE_DIR, os.W_OK) if os.path.exists(CACHE_DIR) else False
        }
    
    return jsonify({
        'memory_cache': {
            'classes': len(spells_cache),
            'pricing_entries': 0,  # pricing_cache deprecated
            'spell_details': len(spell_details_cache),
            'timestamps': len(cache_timestamp),
            'pricing_timestamps': len(pricing_cache_timestamp),
            'last_scrape_times': len(last_scrape_time)
        },
        'storage': storage_info,
        'environment': {
            'working_directory': os.getcwd(),
            'python_path': os.path.dirname(os.path.abspath(__file__)),
            'database_url_available': DATABASE_URL is not None,
            'cache_storage_type': 'database' if USE_DATABASE_CACHE else 'files'
        },
        'config': {
            'spell_cache_expiry_hours': CACHE_EXPIRY_HOURS,
            'pricing_cache_expiry_hours': PRICING_CACHE_EXPIRY_HOURS,
            'min_scrape_interval_minutes': MIN_SCRAPE_INTERVAL_MINUTES
        }
    })

@app.route('/api/debug/pricing-lookup/<class_name>', methods=['GET'])
def debug_pricing_lookup(class_name):
    """Debug endpoint to check pricing lookup for a specific class"""
    try:
        if class_name not in spells_cache:
            return jsonify({'error': f'Class {class_name} not found in cache'}), 404
        
        spell_ids = [str(spell.get('spell_id', '')) for spell in spells_cache[class_name]]
        
        # Check what's in the pricing lookup
        found_in_lookup = {}
        failed_in_lookup = 0
        success_in_lookup = 0
        
        for spell_id in spell_ids:
            if spell_id in pricing_lookup:
                found_in_lookup[spell_id] = pricing_lookup[spell_id]
                if pricing_lookup[spell_id].get('unknown') == True:
                    failed_in_lookup += 1
                else:
                    success_in_lookup += 1
        
        # Get bulk pricing
        pricing_data = get_bulk_pricing_from_db(spell_ids)
        failed_in_bulk = 0
        success_in_bulk = 0
        
        for spell_id, pricing in pricing_data.items():
            if pricing.get('unknown') == True:
                failed_in_bulk += 1
            else:
                success_in_bulk += 1
        
        # Check database directly for missing failed entries
        db_failed_count = 0
        db_entries = {}
        if USE_DATABASE_CACHE:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT spell_id, data FROM spell_details WHERE spell_id = ANY(%s) AND data->>'pricing' IS NOT NULL", (spell_ids,))
                rows = cursor.fetchall()
                for spell_id, data in rows:
                    pricing = data.get('pricing')
                    if pricing and pricing.get('unknown') == True:
                        db_failed_count += 1
                    db_entries[spell_id] = pricing
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Database check failed: {e}")
        
        return jsonify({
            'class_name': class_name,
            'total_spells': len(spell_ids),
            'pricing_lookup_stats': {
                'total_found': len(found_in_lookup),
                'successful': success_in_lookup,
                'failed': failed_in_lookup
            },
            'bulk_pricing_stats': {
                'total_found': len(pricing_data),
                'successful': success_in_bulk,
                'failed': failed_in_bulk
            },
            'database_direct_check': {
                'total_with_pricing': len(db_entries),
                'failed_in_db': db_failed_count
            },
            'sample_spell_ids': spell_ids[:5],
            'sample_lookup_results': {spell_id: found_in_lookup.get(spell_id, 'NOT_FOUND') for spell_id in spell_ids[:5]},
            'sample_bulk_results': {spell_id: pricing_data.get(spell_id, 'NOT_FOUND') for spell_id in spell_ids[:5]},
            'sample_db_results': {spell_id: db_entries.get(spell_id, 'NOT_FOUND') for spell_id in spell_ids[:5]}
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/cache-keys', methods=['GET'])
def debug_cache_keys():
    """Debug endpoint to examine cache key formatting and contents"""
    try:
        # Get information about spells_cache keys
        spells_cache_info = {}
        for key in spells_cache.keys():
            spells_cache_info[key] = {
                'key_type': type(key).__name__,
                'key_repr': repr(key),
                'spell_count': len(spells_cache[key]) if isinstance(spells_cache[key], list) else 'not_a_list',
                'first_spell_id': spells_cache[key][0].get('spell_id', 'no_id') if isinstance(spells_cache[key], list) and len(spells_cache[key]) > 0 else 'no_spells'
            }
        
        # Get information about cache_timestamp keys
        cache_timestamp_info = {}
        for key in cache_timestamp.keys():
            cache_timestamp_info[key] = {
                'key_type': type(key).__name__,
                'key_repr': repr(key),
                'timestamp': cache_timestamp[key]
            }
        
        # Test specific lookups
        test_keys = ['Warrior', 'warrior', 'WARRIOR']
        test_results = {}
        for test_key in test_keys:
            test_results[test_key] = {
                'in_spells_cache': test_key in spells_cache,
                'in_cache_timestamp': test_key in cache_timestamp,
                'in_last_scrape_time': test_key in last_scrape_time
            }
        
        # Get CLASSES information
        classes_info = {}
        for key in CLASSES.keys():
            classes_info[key] = {
                'key_type': type(key).__name__,
                'key_repr': repr(key),
                'class_value': CLASSES[key]
            }
        
        return jsonify({
            'spells_cache_keys': list(spells_cache.keys()),
            'spells_cache_count': len(spells_cache),
            'spells_cache_info': spells_cache_info,
            'cache_timestamp_keys': list(cache_timestamp.keys()),
            'cache_timestamp_count': len(cache_timestamp),
            'cache_timestamp_info': cache_timestamp_info,
            'last_scrape_time_keys': list(last_scrape_time.keys()),
            'test_key_lookups': test_results,
            'classes_keys': list(CLASSES.keys()),
            'classes_info': classes_info,
            'debug_info': {
                'total_spell_cache_entries': len(spells_cache),
                'total_cache_timestamp_entries': len(cache_timestamp),
                'total_last_scrape_entries': len(last_scrape_time),
                'total_classes': len(CLASSES)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_startup_progress(step_name, step_number):
    """Update server startup progress"""
    global server_startup_progress
    
    server_startup_progress['current_step'] = step_name
    server_startup_progress['steps_completed'] = step_number
    server_startup_progress['progress_percent'] = int((step_number / server_startup_progress['total_steps']) * 100)
    
    logger.info(f"📈 Startup Progress: {server_startup_progress['progress_percent']}% - {step_name}")

def get_expired_spell_cache_classes():
    """Identify which spell cache classes have expired and need refresh"""
    expired_classes = []
    
    for class_name in CLASSES.keys():
        class_key = class_name.lower()
        if is_cache_expired(class_key):
            expired_classes.append(class_name)
    
    return expired_classes

def refresh_expired_spell_caches(expired_classes):
    """Refresh spell cache for expired classes only"""
    refreshed_classes = []
    failed_classes = []
    
    for class_name in expired_classes:
        class_key = class_name.lower()
        try:
            logger.info(f"🔄 Refreshing expired spell cache for {class_name}...")
            
            # Remove from cache to force fresh scrape
            spells_cache.pop(class_key, None)
            cache_timestamp.pop(class_key, None)
            
            # Trigger fresh scrape (use original class name, not lowercase)
            df = scrape_class(class_name, 'https://alla.clumsysworld.com/', None)
            
            if df is not None and not df.empty:
                new_spells = df.to_dict('records')
            else:
                new_spells = None
            
            if new_spells:
                spells_cache[class_key] = new_spells
                cache_timestamp[class_key] = datetime.now().isoformat()
                refreshed_classes.append(class_name)
                logger.info(f"✅ Successfully refreshed {class_name} cache with {len(new_spells)} spells")
            else:
                failed_classes.append(class_name)
                logger.warning(f"⚠️ Failed to refresh {class_name} cache - no data returned")
                
        except Exception as e:
            failed_classes.append(class_name)
            logger.error(f"❌ Error refreshing {class_name} cache: {e}")
    
    return refreshed_classes, failed_classes

def preload_spell_data_on_startup():
    """Load all spell data into server memory on startup for optimal performance"""
    global server_startup_progress
    import time
    
    startup_start_time = time.time()
    logger.info("🚀 Preloading spell data into server memory on startup...")
    
    try:
        # Step 1: Initialize cache storage
        update_startup_progress("Setting up cache storage...", 1)
        # (init_cache_storage already called earlier)
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 2: Load existing cache from storage (files or database)
        update_startup_progress("Loading existing cache from storage...", 2)
        load_cache_from_storage()
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 3: Check for expired spell caches and refresh them
        update_startup_progress("Checking and refreshing expired spell caches...", 3)
        expired_classes = get_expired_spell_cache_classes()
        
        if expired_classes:
            logger.info(f"📋 Found {len(expired_classes)} expired spell cache classes: {', '.join(expired_classes)}")
            refreshed_classes, failed_classes = refresh_expired_spell_caches(expired_classes)
            
            if refreshed_classes:
                logger.info(f"✅ Successfully refreshed {len(refreshed_classes)} classes: {', '.join(refreshed_classes)}")
                
            if failed_classes:
                logger.warning(f"⚠️ Failed to refresh {len(failed_classes)} classes: {', '.join(failed_classes)}")
                
            # Save updated cache to storage
            save_cache_to_storage()
        else:
            logger.info("✅ All spell caches are fresh - no refresh needed")
            
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 4: Load all pricing data into memory for instant lookups
        update_startup_progress("Loading pricing data into memory...", 4)
        load_all_pricing_to_memory()
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 5: Finalize and report
        update_startup_progress("Finalizing server startup...", 5)
        
        # Report what was loaded
        spell_classes_count = len(spells_cache)
        pricing_count = len(pricing_lookup) if 'pricing_lookup' in globals() else 0
        spell_details_count = len(spell_details_cache)
        
        # Mark startup as complete
        startup_time = round(time.time() - startup_start_time, 2)
        server_startup_progress.update({
            'is_starting': False,
            'current_step': 'Server ready for instant responses!',
            'progress_percent': 100,
            'startup_complete': True,
            'startup_time': startup_time
        })
        
        logger.info(f"✅ Server memory preloading complete in {startup_time}s!")
        logger.info(f"   📊 Spell classes cached: {spell_classes_count}")
        logger.info(f"   💎 Pricing entries cached: {pricing_count}")
        logger.info(f"   📋 Spell details cached: {spell_details_count}")
        logger.info(f"🎯 Server ready for instant spell data responses!")
        
        return True
        
    except Exception as e:
        # Mark startup as failed but still functional
        server_startup_progress.update({
            'is_starting': False,
            'current_step': 'Startup encountered issues - using on-demand loading',
            'progress_percent': 100,
            'startup_complete': True,
            'startup_time': round(time.time() - startup_start_time, 2)
        })
        
        logger.warning(f"⚠️ Server startup preloading encountered issues: {e}")
        logger.info("🔄 Server will still function with on-demand loading")
        return False

@app.route('/api/debug/cleanup-cache', methods=['POST'])
def cleanup_cache():
    """Debug endpoint to clean up invalid cache entries and report what was found"""
    cleanup_report = {
        'before_cleanup': {},
        'after_cleanup': {},
        'cleaned_entries': [],
        'errors': []
    }
    
    try:
        # Get official classes in lowercase
        official_classes_lower = [cls.lower() for cls in CLASSES.keys()]
        
        # Record state before cleanup
        cleanup_report['before_cleanup'] = {
            'spells_cache_count': len(spells_cache),
            'cache_timestamp_count': len(cache_timestamp),
            'last_scrape_time_count': len(last_scrape_time),
            'spells_cache_keys': list(spells_cache.keys()),
            'cache_timestamp_keys': list(cache_timestamp.keys()),
            'last_scrape_time_keys': list(last_scrape_time.keys())
        }
        
        # Clean up spells_cache
        invalid_spells_cache_keys = []
        for key in list(spells_cache.keys()):
            if key not in official_classes_lower:
                invalid_spells_cache_keys.append(key)
                del spells_cache[key]
                cleanup_report['cleaned_entries'].append(f"Removed invalid key '{key}' from spells_cache")
        
        # Clean up cache_timestamp
        invalid_cache_timestamp_keys = []
        for key in list(cache_timestamp.keys()):
            if key not in official_classes_lower:
                invalid_cache_timestamp_keys.append(key)
                del cache_timestamp[key]
                cleanup_report['cleaned_entries'].append(f"Removed invalid key '{key}' from cache_timestamp")
        
        # Clean up last_scrape_time
        invalid_last_scrape_keys = []
        for key in list(last_scrape_time.keys()):
            if key not in official_classes_lower:
                invalid_last_scrape_keys.append(key)
                del last_scrape_time[key]
                cleanup_report['cleaned_entries'].append(f"Removed invalid key '{key}' from last_scrape_time")
        
        # Clean up database if using database storage
        if USE_DATABASE_CACHE:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Check for invalid entries in database
                cursor.execute("SELECT class_name FROM spell_cache")
                db_classes = [row[0] for row in cursor.fetchall()]
                
                invalid_db_classes = [cls for cls in db_classes if cls not in official_classes_lower]
                
                if invalid_db_classes:
                    # Remove invalid entries from database
                    for invalid_class in invalid_db_classes:
                        cursor.execute("DELETE FROM spell_cache WHERE class_name = %s", (invalid_class,))
                        cursor.execute("DELETE FROM cache_metadata WHERE key = %s", (f"cache_timestamp.{invalid_class}",))
                        cleanup_report['cleaned_entries'].append(f"Removed invalid database entry '{invalid_class}' from spell_cache")
                
                conn.commit()
                cursor.close()
                conn.close()
                
                cleanup_report['database_cleanup'] = {
                    'invalid_entries_found': len(invalid_db_classes),
                    'invalid_entries': invalid_db_classes
                }
                
            except Exception as e:
                cleanup_report['errors'].append(f"Database cleanup error: {str(e)}")
        
        # Record state after cleanup
        cleanup_report['after_cleanup'] = {
            'spells_cache_count': len(spells_cache),
            'cache_timestamp_count': len(cache_timestamp),
            'last_scrape_time_count': len(last_scrape_time),
            'spells_cache_keys': list(spells_cache.keys()),
            'cache_timestamp_keys': list(cache_timestamp.keys()),
            'last_scrape_time_keys': list(last_scrape_time.keys())
        }
        
        # Summary
        cleanup_report['summary'] = {
            'total_entries_cleaned': len(cleanup_report['cleaned_entries']),
            'memory_cleaned': len(invalid_spells_cache_keys) + len(invalid_cache_timestamp_keys) + len(invalid_last_scrape_keys),
            'database_cleaned': len(invalid_db_classes) if USE_DATABASE_CACHE else 0,
            'all_classes_now_valid': len(spells_cache) == 16 and all(key in official_classes_lower for key in spells_cache.keys())
        }
        
        # Save cleaned cache if any changes were made
        if cleanup_report['summary']['total_entries_cleaned'] > 0:
            save_cache_to_storage()
            cleanup_report['cache_saved'] = True
        else:
            cleanup_report['cache_saved'] = False
        
        return jsonify(cleanup_report)
        
    except Exception as e:
        cleanup_report['errors'].append(f"Cleanup error: {str(e)}")
        return jsonify(cleanup_report), 500

@app.route('/api/debug/cache-integrity', methods=['GET'])
def cache_integrity():
    """Debug endpoint to verify cache integrity and consistency"""
    try:
        # Get official classes in lowercase
        official_classes_lower = [cls.lower() for cls in CLASSES.keys()]
        
        # Check memory cache consistency
        memory_stats = {
            'spells_cache_count': len(spells_cache),
            'cache_timestamp_count': len(cache_timestamp),
            'last_scrape_time_count': len(last_scrape_time),
            'all_keys_valid': True,
            'missing_classes': [],
            'extra_classes': []
        }
        
        # Find missing and extra classes in memory
        for official_class in official_classes_lower:
            if official_class not in spells_cache:
                memory_stats['missing_classes'].append(official_class)
        
        for cached_class in spells_cache.keys():
            if cached_class not in official_classes_lower:
                memory_stats['extra_classes'].append(cached_class)
                memory_stats['all_keys_valid'] = False
        
        # Check database consistency if using database
        db_stats = {'enabled': USE_DATABASE_CACHE}
        if USE_DATABASE_CACHE:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                cursor.execute("SELECT class_name FROM spell_cache")
                db_classes = [row[0] for row in cursor.fetchall()]
                
                db_stats.update({
                    'database_count': len(db_classes),
                    'database_classes': sorted(db_classes),
                    'database_keys_valid': all(cls in official_classes_lower for cls in db_classes),
                    'database_missing': [cls for cls in official_classes_lower if cls not in db_classes],
                    'database_extra': [cls for cls in db_classes if cls not in official_classes_lower]
                })
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                db_stats['error'] = str(e)
        
        # Overall health check
        integrity_check = {
            'overall_health': 'HEALTHY',
            'issues': [],
            'memory_cache_count': memory_stats['spells_cache_count'],
            'expected_class_count': len(official_classes_lower),
            'all_16_classes_present': len(spells_cache) == 16 and memory_stats['all_keys_valid'],
            'memory_cache_complete': len(memory_stats['missing_classes']) == 0,
            'database_cache_complete': db_stats.get('database_count', 0) == 16 if USE_DATABASE_CACHE else True
        }
        
        if not integrity_check['all_16_classes_present']:
            integrity_check['overall_health'] = 'ISSUES_FOUND'
            integrity_check['issues'].append('Memory cache has invalid or missing classes')
        
        if USE_DATABASE_CACHE and not integrity_check['database_cache_complete']:
            integrity_check['overall_health'] = 'ISSUES_FOUND'
            integrity_check['issues'].append('Database cache has invalid or missing classes')
        
        return jsonify({
            'integrity_check': integrity_check,
            'official_classes': sorted(official_classes_lower),
            'memory_stats': memory_stats,
            'database_stats': db_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Database configuration management
from utils.db_config_manager import DatabaseConfigManager
from utils.db_connection_pool import close_connection_pool

# Initialize config manager
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
db_config_manager = DatabaseConfigManager(config_path)

# Add callback to close pool when config changes
def on_db_config_change():
    """Close connection pool when database config changes."""
    logger.info("Database configuration changed, closing connection pool")
    close_connection_pool()

db_config_manager.add_reload_callback(on_db_config_change)

# Helper function for EQEmu database connection
def get_eqemu_db_connection():
    """Get connection to the configured EQEmu database using connection pooling."""
    # Get current config
    config = db_config_manager.get_config()
    
    # Get database URL from config
    database_url = config.get('production_database_url', '')
    if not database_url:
        return None, None, "Database not configured"
    
    # Import required modules
    from utils.database_connectors import get_database_connector
    from utils.db_connection_pool import get_connection_pool
    from urllib.parse import urlparse
    
    # Parse database URL
    parsed = urlparse(database_url)
    db_type = config.get('database_type', 'mysql')
    
    db_config = {
        'host': parsed.hostname,
        'port': int(parsed.port) if parsed.port else 3306,
        'database': parsed.path[1:] if parsed.path else '',
        'username': parsed.username,
        'password': parsed.password,
        'use_ssl': config.get('database_ssl', True)
    }
    
    try:
        # Create connection function for the pool
        def create_connection():
            return get_database_connector(db_type, db_config)
        
        # Get or create connection pool (will reuse existing pool if config hasn't changed)
        pool = get_connection_pool(create_connection, max_connections=10)
        
        # Return pool context manager, db_type, and no error
        return pool, db_type, None
    except Exception as e:
        app.logger.error(f"Database connection pool error: {e}")
        app.logger.error(f"Database config: host={db_config.get('host')}, port={db_config.get('port')}, db={db_config.get('database')}, user={db_config.get('username')}")
        return None, None, str(e)

# Helper function for safe numeric conversions
def _safe_float(value):
    """Safely convert a value to float, returning None if conversion fails"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def _safe_int(value):
    """Safely convert a value to int, returning None if conversion fails"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

# Item search endpoints (EQEmu schema with discovered items join)
@app.route('/api/items/search', methods=['GET'])
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)  # Liberal limits for normal users
def search_items():
    """
    Search discovered items in the EQEmu database.
    Only returns items that exist in both items and discovered_items tables.
    
    Query parameters:
        q: Search query
        limit: Number of results to return (default: 20, max: 100)
        offset: Offset for pagination (default: 0)
        type: Filter by item type (itemtype)
        class: Filter by usable classes
        min_level: Filter by minimum required level
        max_level: Filter by maximum required level
    """
    try:
        # Get EQEmu database connection pool
        pool, db_type, error = get_eqemu_db_connection()
        if not pool:
            return jsonify({'error': error or 'Database not configured'}), 503
        
        # Use connection from pool
        with pool.get_connection() as conn:
            # Validate and sanitize all input parameters
            validated_params = validate_item_search_params(request.args)
            
            search_query = validated_params.get('q', '')
            limit = validated_params.get('limit', 20)
            offset = validated_params.get('offset', 0)
            item_type = validated_params.get('type')
            item_class = validated_params.get('class')
            min_level = validated_params.get('min_level')
            max_level = validated_params.get('max_level')
            advanced_filters = validated_params.get('filters', [])
            
            # Security logging
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Log search activity
            app.logger.info(f"Item search request from {client_ip} - q: '{search_query}', type: '{item_type}', class: '{item_class}', min_level: '{min_level}', max_level: '{max_level}', filters: {len(advanced_filters)}")
            
            if not search_query and not item_type and not item_class and not min_level and not max_level and not advanced_filters:
                return jsonify({'error': 'Search query or filter required'}), 400
            
            # Build SQL query with JOIN to discovered_items
            conditions = []
            params = []
        
        if search_query:
            # Use LIKE for MySQL compatibility (ILIKE is PostgreSQL specific)
            if db_type == 'postgresql':
                conditions.append("(items.Name ILIKE %s OR items.lore ILIKE %s)")
            else:
                conditions.append("(items.Name LIKE %s OR items.lore LIKE %s)")
            params.extend([f'%{search_query}%', f'%{search_query}%'])
        
        if item_type is not None:
            conditions.append("items.itemtype = %s")
            params.append(item_type)
        
        if item_class:
            # EQEmu uses bitmask for classes - we'll do a simple search in the classes field
            if db_type == 'postgresql':
                conditions.append("items.classes::text LIKE %s")
            else:
                # For MySQL/MSSQL, use CAST function
                conditions.append("CAST(items.classes AS CHAR) LIKE %s")
            params.append(f'%{item_class}%')
        
        if min_level is not None:
            conditions.append("items.reqlevel >= %s")
            params.append(min_level)
        
        if max_level is not None:
            conditions.append("items.reqlevel <= %s")
            params.append(max_level)
        
        # Process advanced filters
        for filter_item in advanced_filters:
            field = filter_item.get('field')
            operator = filter_item.get('operator')
            value = filter_item.get('value')
            value2 = filter_item.get('value2')  # For 'between' operator
            
            # Map frontend field names to database column names
            field_mapping = {
                'lore': 'items.lore',
                'price': 'items.price',
                'weight': 'items.weight',
                'size': 'items.size',
                'damage': 'items.damage',
                'delay': 'items.delay',
                'ac': 'items.ac',
                'hp': 'items.hp',
                'mana': 'items.mana',
                'str': 'items.astr',
                'sta': 'items.asta',
                'agi': 'items.aagi',
                'dex': 'items.adex',
                'wis': 'items.awis',
                'int': 'items.aint',
                'cha': 'items.acha',
                'magic': 'items.magic',
                'lore': 'items.lore',
                'nodrop': 'items.nodrop',
                'norent': 'items.norent',
                'clickeffect': 'items.clickeffect',
                'proceffect': 'items.proceffect',
                'worneffect': 'items.worneffect',
                'focuseffect': 'items.focuseffect',
                'slots': 'items.slots'
            }
            
            db_field = field_mapping.get(field)
            if not db_field:
                continue
            
            # Handle different operators
            if operator == 'equals':
                conditions.append(f"{db_field} = %s")
                params.append(value)
            elif operator == 'not equals':
                conditions.append(f"{db_field} != %s")
                params.append(value)
            elif operator == 'contains':
                if db_type == 'postgresql':
                    conditions.append(f"{db_field} ILIKE %s")
                else:
                    conditions.append(f"{db_field} LIKE %s")
                params.append(f'%{value}%')
            elif operator == 'starts with':
                if db_type == 'postgresql':
                    conditions.append(f"{db_field} ILIKE %s")
                else:
                    conditions.append(f"{db_field} LIKE %s")
                params.append(f'{value}%')
            elif operator == 'ends with':
                if db_type == 'postgresql':
                    conditions.append(f"{db_field} ILIKE %s")
                else:
                    conditions.append(f"{db_field} LIKE %s")
                params.append(f'%{value}')
            elif operator == 'greater than':
                conditions.append(f"{db_field} > %s")
                params.append(value)
            elif operator == 'less than':
                conditions.append(f"{db_field} < %s")
                params.append(value)
            elif operator == 'between':
                conditions.append(f"{db_field} BETWEEN %s AND %s")
                params.extend([value, value2])
            elif operator == 'exists':
                conditions.append(f"{db_field} IS NOT NULL")
            elif operator == 'includes' and field == 'slots':
                # Special handling for slots (bitmask)
                conditions.append(f"(items.slots & %s) > 0")
                params.append(value)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Execute query with database connection (READ-ONLY)
        try:
            cursor = conn.cursor()
            # Set connection to read-only mode
            if db_type == 'mysql':
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
            elif db_type == 'postgresql':
                cursor.execute("SET TRANSACTION READ ONLY")
            elif db_type == 'mssql':
                # SQL Server doesn't have a direct equivalent, we rely on permissions
                pass
                
            
            # Get total count with JOIN
            count_query = f"""
                SELECT COUNT(DISTINCT items.id) AS total_count
                    FROM items 
                    INNER JOIN discovered_items ON items.id = discovered_items.item_id
                    WHERE {where_clause}
                """
            cursor.execute(count_query, params)
            result = cursor.fetchone()
            # Handle both dict and tuple results
            if result:
                if isinstance(result, dict):
                    total_count = result.get('total_count', 0)
                else:
                    total_count = result[0]
            else:
                total_count = 0
            
            # Get items with JOIN (only discovered items)
            items_query = f"""
                    SELECT DISTINCT 
                        items.id,
                        items.Name,
                        items.itemtype,
                        items.ac,
                        items.hp,
                        items.mana,
                        items.astr,
                        items.asta,
                        items.aagi,
                        items.adex,
                        items.awis,
                        items.aint,
                        items.acha,
                        items.weight,
                        items.damage,
                        items.delay,
                        items.magic,
                        items.nodrop,
                        items.norent,
                        items.classes,
                        items.races,
                        items.slots,
                        items.lore,
                        items.reqlevel,
                        items.stackable,
                        items.stacksize,
                        items.icon,
                        COUNT(discovered_items.item_id) as discovery_count
                    FROM items 
                    INNER JOIN discovered_items ON items.id = discovered_items.item_id
                    WHERE {where_clause}
                    GROUP BY items.id, items.Name, items.itemtype, items.ac, items.hp, items.mana,
                             items.astr, items.asta, items.aagi, items.adex, items.awis, items.aint, items.acha,
                             items.weight, items.damage, items.delay, items.magic, items.nodrop, items.norent,
                             items.classes, items.races, items.slots, items.lore, items.reqlevel,
                             items.stackable, items.stacksize, items.icon
                    ORDER BY items.Name
                    LIMIT %s OFFSET %s
                """
            cursor.execute(items_query, params + [limit, offset])
            items = cursor.fetchall()
            
            # Convert to list of dictionaries with proper field mapping
            items_list = []
            debug_logged = False  # Only log first item for debugging
            for item in items:
                # Handle both dict and tuple cursor results
                if isinstance(item, dict):
                    # MySQL DictCursor returns field names as they appear in query
                    item_dict = {
                        'id': item.get('id'),
                        'item_id': str(item.get('id')),  # Use id as item_id for consistency
                        'name': item.get('Name'),
                        'itemtype': item.get('itemtype'),
                        'ac': _safe_int(item.get('ac')),
                        'hp': _safe_int(item.get('hp')),
                        'mana': _safe_int(item.get('mana')),
                        'stats': {
                            'str': _safe_int(item.get('astr')),  # EQEmu uses astr for strength bonus
                            'sta': _safe_int(item.get('asta')),  # EQEmu uses asta for stamina bonus
                            'agi': _safe_int(item.get('aagi')),  # EQEmu uses aagi for agility bonus
                            'dex': _safe_int(item.get('adex')),  # EQEmu uses adex for dexterity bonus
                            'wis': _safe_int(item.get('awis')),  # EQEmu uses awis for wisdom bonus
                            'int': _safe_int(item.get('aint')),  # EQEmu uses aint for intelligence bonus
                            'cha': _safe_int(item.get('acha'))   # EQEmu uses acha for charisma bonus
                        },
                        'weight': _safe_float(item.get('weight')),
                        'damage': _safe_int(item.get('damage')),
                        'delay': _safe_int(item.get('delay')),
                        'magic': bool(item.get('magic')),
                        'nodrop': bool(item.get('nodrop')),
                        'norent': bool(item.get('norent')),
                        'lore': item.get('lore') if item.get('lore') else None,  # lore is text in EQEmu
                        'classes': _safe_int(item.get('classes')),
                        'races': _safe_int(item.get('races')),
                        'slots': _safe_int(item.get('slots')),
                        'reqlevel': _safe_int(item.get('reqlevel')),
                        'stackable': bool(item.get('stackable')),
                        'stacksize': _safe_int(item.get('stacksize')),
                        'icon': _safe_int(item.get('icon')),
                        'discovery_count': _safe_int(item.get('discovery_count'))
                    }
                else:
                    # Handle tuple results (MySQL)
                    if not debug_logged:
                        logger.info(f"Debug item tuple - norent field (index 18): {item[18] if len(item) > 18 else 'NO INDEX 18'}")
                        logger.info(f"Debug item tuple - magic field (index 16): {item[16] if len(item) > 16 else 'NO INDEX 16'}")
                        logger.info(f"Debug item tuple - nodrop field (index 17): {item[17] if len(item) > 17 else 'NO INDEX 17'}")
                        debug_logged = True
                    item_dict = {
                        'id': item[0],
                        'item_id': str(item[0]),
                        'name': item[1],
                        'itemtype': item[2],
                        'ac': _safe_int(item[3]),
                        'hp': _safe_int(item[4]),
                        'mana': _safe_int(item[5]),
                        'stats': {
                            'str': _safe_int(item[6]),
                            'sta': _safe_int(item[7]),
                            'agi': _safe_int(item[8]),
                            'dex': _safe_int(item[9]),
                            'wis': _safe_int(item[10]),
                            'int': _safe_int(item[11]),
                            'cha': _safe_int(item[12])
                        },
                        'weight': _safe_float(item[13]),
                        'damage': _safe_int(item[14]),
                        'delay': _safe_int(item[15]),
                        'magic': bool(item[16]),
                        'nodrop': bool(item[17]),
                        'norent': bool(item[18]),
                        'classes': _safe_int(item[19]),
                        'races': _safe_int(item[20]),
                        'slots': _safe_int(item[21]),
                        'lore': item[22],
                        'reqlevel': _safe_int(item[23]),
                        'stackable': bool(item[24]),
                        'stacksize': _safe_int(item[25]),
                        'icon': _safe_int(item[26]),
                        'discovery_count': _safe_int(item[27])
                    }
                items_list.append(item_dict)
            
                cursor.close()
                return jsonify({
                        'items': items_list,
                        'total_count': total_count,
                        'limit': limit,
                        'offset': offset,
                        'search_query': search_query,
                        'discovered_only': True
                })
                
        finally:
            if cursor:
                cursor.close()
            # Connection is automatically returned to pool by context manager
            
    except Exception as e:
        import traceback
        app.logger.error(f"Error searching items: {e}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Provide more specific error messages
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return jsonify({'error': 'Database connection timeout. Please try again.'}), 503
        elif "connection pool" in error_msg.lower():
            return jsonify({'error': 'Database connection pool error. Please try again later.'}), 503
        elif "not configured" in error_msg.lower():
            return jsonify({'error': 'Database not configured. Please contact administrator.'}), 503
        else:
            return jsonify({'error': f'Search failed: {error_msg}'}), 500


@app.route('/api/items/<item_id>', methods=['GET'])
@exempt_when_limiting
def get_item_details(item_id):
    """
    Get detailed information about a specific discovered item using EQEmu schema.
    Only returns items that exist in both items and discovered_items tables.
    """
    try:
        # Get EQEmu database connection
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            return jsonify({'error': error or 'Database not configured'}), 503
        try:
            cursor = conn.cursor()
            # Set connection to read-only mode
            if db_type == 'mysql':
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
            elif db_type == 'postgresql':
                cursor.execute("SET TRANSACTION READ ONLY")
            elif db_type == 'mssql':
                # SQL Server doesn't have a direct equivalent, we rely on permissions
                pass
            
            # Query with JOIN to ensure item is discovered
            cursor.execute("""
                    SELECT DISTINCT
                        items.id,
                        items.Name,
                        items.itemtype,
                        items.ac,
                        items.hp,
                        items.mana,
                        items.astr,
                        items.asta,
                        items.aagi,
                        items.adex,
                        items.awis,
                        items.aint,
                        items.acha,
                        items.weight,
                        items.damage,
                        items.delay,
                        items.magic,
                        items.nodrop,
                        items.norent,
                        items.classes,
                        items.races,
                        items.slots,
                        items.lore,
                        items.reqlevel,
                        items.stackable,
                        items.stacksize,
                        items.clickeffect,
                        items.proceffect,
                        items.worneffect,
                        items.focuseffect,
                        items.scrolleffect,
                        items.bardeffect,
                        items.cr,
                        items.dr,
                        items.fr,
                        items.mr,
                        items.pr,
                        items.svcorruption,
                        items.skillmodtype,
                        items.skillmodvalue,
                        items.price,
                        items.favor,
                        items.icon,
                        COUNT(discovered_items.item_id) as discovery_count,
                        MIN(discovered_items.discovered_date) as first_discovered,
                        MAX(discovered_items.discovered_date) as last_discovered
                    FROM items 
                    INNER JOIN discovered_items ON items.id = discovered_items.item_id
                    WHERE items.id = %s
                    GROUP BY items.id, items.Name, items.itemtype, items.ac, items.hp, items.mana,
                             items.astr, items.asta, items.aagi, items.adex, items.awis, items.aint, items.acha,
                             items.weight, items.damage, items.delay, items.magic, items.nodrop, items.norent,
                             items.classes, items.races, items.slots, items.lore, items.reqlevel,
                             items.stackable, items.stacksize, items.clickeffect, items.proceffect,
                             items.worneffect, items.focuseffect, items.scrolleffect, items.bardeffect,
                             items.cr, items.dr, items.fr, items.mr, items.pr, items.svcorruption,
                             items.skillmodtype, items.skillmodvalue, items.price, items.favor, items.icon
            """, (item_id,))
            
            item = cursor.fetchone()
            if not item:
                return jsonify({'error': 'Item not found or not discovered'}), 404
            
            # Convert to dictionary with proper field mapping
            # Handle both dict and tuple cursor results
            if isinstance(item, dict):
                item_dict = {
                    'id': item['id'],
                    'item_id': str(item['id']),
                    'name': item['Name'] if 'Name' in item else item.get('name', ''),
                    'itemtype': item['itemtype'],
                    'ac': item['ac'],
                    'hp': item['hp'],
                    'mana': item['mana'],
                    'str': item['astr'],
                    'sta': item['asta'],
                    'agi': item['aagi'],
                    'dex': item['adex'],
                    'wis': item['awis'],
                    'int': item['aint'],
                    'cha': item['acha'],
                    'weight': float(item['weight']) if item['weight'] else None,
                    'damage': item['damage'],
                    'delay': item['delay'],
                    'magic': bool(item['magic']),
                    'nodrop': bool(item['nodrop']),
                    'norent': bool(item['norent']),
                    'lore': item['lore'] if item['lore'] else None,
                    'classes': item['classes'],
                    'races': item['races'],
                    'slots': item['slots'],
                    'reqlevel': item['reqlevel'],
                    'stackable': bool(item['stackable']),
                    'stacksize': item['stacksize'],
                    'effects': {
                        'click': item['clickeffect'],
                        'proc': item['proceffect'],
                        'worn': item['worneffect'],
                        'focus': item['focuseffect'],
                        'scroll': item['scrolleffect'],
                        'bard': item['bardeffect']
                    },
                    'resistances': {
                        'cold': item['cr'],
                        'disease': item['dr'],
                        'fire': item['fr'],
                        'magic': item['mr'],
                        'poison': item['pr'],
                        'corruption': item['svcorruption']
                    },
                    'skill_mod': {
                        'type': item['skillmodtype'],
                        'value': item['skillmodvalue']
                    },
                    'price': item['price'],
                    'favor': item['favor'],
                    'icon': item['icon'],
                    'discovery_info': {
                        'discovery_count': item['discovery_count'],
                        'first_discovered': item['first_discovered'],
                        'last_discovered': item['last_discovered']
                    }
                }
            else:
                # Handle tuple results - map all fields by position
                item_dict = {
                    'id': item[0],
                    'item_id': str(item[0]),
                    'name': item[1],
                    'itemtype': item[2],
                    'ac': item[3],
                    'hp': item[4],
                    'mana': item[5],
                    'str': item[6],
                    'sta': item[7],
                    'agi': item[8],
                    'dex': item[9],
                    'wis': item[10],
                    'int': item[11],
                    'cha': item[12],
                    'weight': float(item[13]) if item[13] else None,
                    'damage': item[14],
                    'delay': item[15],
                    'magic': bool(item[16]),
                    'nodrop': bool(item[17]),
                    'norent': bool(item[18]),
                    'classes': item[19],
                    'races': item[20],
                    'slots': item[21],
                    'lore': item[22] if item[22] else None,
                    'reqlevel': item[23],
                    'stackable': bool(item[24]),
                    'stacksize': item[25],
                    'effects': {
                        'click': item[26],
                        'proc': item[27],
                        'worn': item[28],
                        'focus': item[29],
                        'scroll': item[30],
                        'bard': item[31]
                    },
                    'resistances': {
                        'cold': item[32],
                        'disease': item[33],
                        'fire': item[34],
                        'magic': item[35],
                        'poison': item[36],
                        'corruption': item[37]
                    },
                    'skill_mod': {
                        'type': item[38],
                        'value': item[39]
                    },
                    'price': item[40],
                    'favor': item[41],
                    'icon': item[42],
                    'discovery_info': {
                        'discovery_count': item[43],
                        'first_discovered': item[44],
                        'last_discovered': item[45]
                    }
                }
            
            cursor.close()
            return jsonify({'item': item_dict})
            
        finally:
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item details: {e}")
        return jsonify({'error': f'Failed to get item: {str(e)}'}), 500


@app.route('/api/items/types', methods=['GET'])
@exempt_when_limiting
def get_item_types():
    """
    Get list of available item types for filtering (discovered items only).
    Uses EQEmu schema with read-only access.
    """
    try:
        # Get EQEmu database connection
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            return jsonify({'error': error or 'Database not configured'}), 503
        try:
            cursor = conn.cursor()
            # Set connection to read-only mode
            if db_type == 'mysql':
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
            elif db_type == 'postgresql':
                cursor.execute("SET TRANSACTION READ ONLY")
            elif db_type == 'mssql':
                # SQL Server doesn't have a direct equivalent, we rely on permissions
                pass
            
            # Query only discovered items using JOIN with discovered_items table
            # Use proper column aliases for MySQL DictCursor
            query = """
                SELECT DISTINCT items.itemtype AS itemtype, COUNT(*) AS count
                FROM items 
                INNER JOIN discovered_items ON items.id = discovered_items.item_id
                WHERE items.itemtype IS NOT NULL
                GROUP BY items.itemtype
                ORDER BY count DESC, items.itemtype
            """
            
            app.logger.info(f"Executing query on {db_type} database: {query}")
            cursor.execute(query)
            
            types = []
            results = cursor.fetchall()
            app.logger.info(f"Query returned {len(results) if isinstance(results, list) else type(results)} results")
            
            for row in results:
                # Handle both dictionary and tuple results
                if isinstance(row, dict):
                    types.append({
                        'type': row['itemtype'],
                        'count': row['count']
                    })
                else:
                    types.append({
                        'type': row[0],
                        'count': row[1]
                    })
            
            cursor.close()
            return jsonify({'types': types})
            
        finally:
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item types: {e}")
        return jsonify({'error': f'Failed to get item types: {str(e)}'}), 500


def cleanup_resources():
    """Clean up resources on shutdown."""
    logger.info("Cleaning up resources...")
    close_connection_pool()
    logger.info("Connection pool closed")

if __name__ == '__main__':
    import atexit
    
    # Register cleanup on exit
    atexit.register(cleanup_resources)
    
    # Preload spell data before starting server for optimal performance
    # Skip during CI testing to avoid long startup times
    if not os.environ.get('SKIP_STARTUP_CACHE_REFRESH'):
        preload_spell_data_on_startup()
    else:
        logger.info("⚠️ Skipping startup cache refresh (SKIP_STARTUP_CACHE_REFRESH=1)")
    app.run(debug=True, host='0.0.0.0', port=config['backend_port']) 