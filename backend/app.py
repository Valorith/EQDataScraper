from flask import Flask, jsonify, request, g
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime, timedelta
import logging
import time
from urllib.parse import urlparse
import warnings

import psycopg2

# Suppress urllib3 OpenSSL warnings that spam the logs - MUST be done early
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')

# Suppress Flask-limiter warnings about in-memory storage - MUST be done early
warnings.filterwarnings('ignore', message='Using the in-memory storage for tracking rate limits')

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables only")

from utils.security import sanitize_search_input, validate_item_search_params, validate_spell_search_params, rate_limit_by_ip

# Import activity logger if user accounts are enabled
if os.environ.get('ENABLE_USER_ACCOUNTS', 'false').lower() == 'true':
    from utils.activity_logger import log_api_activity

app = Flask(__name__)

# Configure dev mode auth bypass for development
DEV_MODE_AUTH_BYPASS = (
    os.environ.get('ENABLE_DEV_AUTH') == 'true' and 
    os.environ.get('FLASK_ENV') != 'production'
)
app.config['DEV_MODE_AUTH_BYPASS'] = DEV_MODE_AUTH_BYPASS

if DEV_MODE_AUTH_BYPASS:
    print("🔧 DEV MODE AUTH BYPASS ENABLED - Authentication will be skipped")
else:
    print("🔐 Authentication required for protected routes")

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
        'http://localhost:3000',
        'http://localhost:3000',
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
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        limiter.init_app(app)
        
        # Apply rate limits to OAuth endpoints
        limiter.limit("10 per minute")(auth_bp)
        limiter.limit("60 per hour")(users_bp) 
        # Admin endpoints are exempt from rate limiting
        
        # Exempt health check, admin endpoints, and cache status from rate limiting
        @limiter.request_filter
        def exempt_endpoints():
            """Exempt health and admin endpoints from rate limiting"""
            if request.endpoint in ['health_check']:
                return True
            # Exempt all admin endpoints from rate limiting
            if request.endpoint and request.endpoint.startswith('admin.'):
                return True
            # Also check by path for health endpoints
            if request.path and any(path in request.path for path in ['/api/health']):
                return True
            return False
        
        # Make limiter available globally for decorators
        app.limiter = limiter
        
        # Database connection injection for OAuth routes
        @app.before_request
        def inject_db_connection():
            """Inject database connection for OAuth routes and track request start time."""
            # Track request start time for metrics
            g.request_start_time = time.time()
            
            if request.endpoint and any(request.endpoint.startswith(prefix) for prefix in ['auth.', 'users.', 'admin.']):
                # Connect to database if DB_CONFIG is available (for OAuth)
                if DB_CONFIG:
                    try:
                        if DB_TYPE == 'postgresql':
                            g.db_connection = psycopg2.connect(**DB_CONFIG)
                            app.logger.debug(f"Database connection established for endpoint: {request.endpoint}")
                        else:
                            app.logger.warning(f"Database type {DB_TYPE} not yet supported for OAuth")
                            g.db_connection = None
                    except Exception as e:
                        app.logger.error(f"Failed to connect to database for OAuth: {e}")
                        app.logger.error(f"DB_CONFIG: host={DB_CONFIG.get('host')}, port={DB_CONFIG.get('port')}, database={DB_CONFIG.get('database')}")
                        app.logger.error(f"DB_TYPE: {DB_TYPE}")
                        app.logger.error(f"Full error: {str(e)}")
                        g.db_connection = None
                else:
                    app.logger.debug(f"No DB_CONFIG available for OAuth endpoint: {request.endpoint}")
                    g.db_connection = None
        
        @app.teardown_request
        def close_db_connection(error):
            """Close database connection after OAuth requests."""
            if hasattr(g, 'db_connection') and g.db_connection:
                g.db_connection.close()
        
        @app.after_request
        def track_request_metrics(response):
            """Track metrics for each request."""
            if hasattr(g, 'request_start_time'):
                # Calculate response time
                response_time = (time.time() - g.request_start_time) * 1000  # Convert to milliseconds
                
                # Build endpoint identifier
                method = request.method
                path = request.path
                endpoint_key = f"{method} {path}"
                
                # Normalize paths with parameters
                if ':' in path or any(segment.isdigit() for segment in path.split('/')):
                    # Replace numeric IDs with placeholders
                    path_parts = path.split('/')
                    normalized_parts = []
                    for part in path_parts:
                        if part.isdigit():
                            normalized_parts.append(':id')
                        elif part and len(part) > 20 and not '.' in part:  # Likely a token or hash
                            normalized_parts.append(':token')
                        else:
                            normalized_parts.append(part)
                    normalized_path = '/'.join(normalized_parts)
                    endpoint_key = f"{method} {normalized_path}"
                
                # Track the metric
                try:
                    from routes.admin import track_endpoint_metric
                    is_error = response.status_code >= 400
                    status_code = response.status_code if is_error else None
                    error_details = None
                    
                    # Add error details for failed requests
                    if is_error and hasattr(response, 'get_data'):
                        try:
                            response_data = response.get_data(as_text=True)
                            if response_data and len(response_data) < 500:  # Limit size
                                error_details = response_data
                        except:
                            pass
                    
                    track_endpoint_metric(
                        endpoint_key, 
                        response_time, 
                        is_error, 
                        status_code=status_code,
                        error_details=error_details
                    )
                except ImportError:
                    pass  # Admin routes not loaded
                except Exception as e:
                    app.logger.error(f"Error tracking metrics: {e}")
            
            return response
        
        # Register OAuth blueprints
        app.register_blueprint(auth_bp, url_prefix='/api')
        app.register_blueprint(users_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api')
        
        # Temporarily register debug OAuth blueprint for troubleshooting
        try:
            from routes.debug_oauth import debug_oauth_bp
            app.register_blueprint(debug_oauth_bp, url_prefix='/api')
            app.logger.info("🔧 Debug OAuth endpoints enabled")
        except ImportError:
            pass
            
        # Register enhanced OAuth troubleshooting endpoint
        try:
            from routes.oauth_troubleshoot import oauth_troubleshoot_bp
            app.register_blueprint(oauth_troubleshoot_bp, url_prefix='/api')
            app.logger.info("🔧 Enhanced OAuth troubleshooting enabled")
        except ImportError:
            pass
            
        # Register OAuth production fix endpoint
        try:
            from routes.oauth_fix import oauth_fix_bp
            app.register_blueprint(oauth_fix_bp, url_prefix='/api')
            app.logger.info("🔧 OAuth production fix endpoints enabled")
        except ImportError:
            pass
        
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

# Configure logging first - write to both console and file
import logging.handlers

# Set up logging to write to both console and file
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend_run.log')
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

# File handler with rotation
try:
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5  # 10MB max, 5 backup files
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    print(f"✅ Logging configured to write to: {log_file_path}")
except Exception as e:
    print(f"⚠️ Could not set up file logging: {e}")


logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Global request tracking for non-OAuth routes
if not ENABLE_USER_ACCOUNTS:
    @app.before_request
    def track_request_start():
        """Track request start time for metrics."""
        g.request_start_time = time.time()
    
    @app.after_request
    def track_request_end(response):
        """Track metrics for each request."""
        if hasattr(g, 'request_start_time'):
            # Calculate response time
            response_time = (time.time() - g.request_start_time) * 1000  # Convert to milliseconds
            
            # Build endpoint identifier
            method = request.method
            path = request.path
            endpoint_key = f"{method} {path}"
            
            # Normalize paths with parameters
            if any(segment for segment in path.split('/') if segment.isdigit() or (segment and len(segment) > 30)):
                # Replace numeric IDs and long strings with placeholders
                path_parts = path.split('/')
                normalized_parts = []
                for part in path_parts:
                    if part.isdigit():
                        normalized_parts.append(':id')
                    elif part and len(part) > 30 and not '.' in part:  # Likely a spell ID or hash
                        normalized_parts.append(':id')
                    else:
                        normalized_parts.append(part)
                normalized_path = '/'.join(normalized_parts)
                endpoint_key = f"{method} {normalized_path}"
            
            # Track the metric if admin routes are available
            try:
                if ENABLE_USER_ACCOUNTS:
                    from routes.admin import track_endpoint_metric
                    is_error = response.status_code >= 400
                    track_endpoint_metric(endpoint_key, response_time, is_error)
            except ImportError:
                pass  # Admin routes not loaded
            except Exception as e:
                logger.error(f"Error tracking metrics: {e}")
        
        return response

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
        'password': parsed.password,
        'connect_timeout': 10  # Add 10 second connection timeout
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
    
    # Cache file paths (disabled but defined to prevent NameError)
    SPELLS_CACHE_FILE = os.path.join(CACHE_DIR, 'spells_cache.json')
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
        
        # SPELL CACHE TABLES REMOVED - spell system disabled
        
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
        
        # SPELL CACHE TABLES REMOVED - spell system disabled
        
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
# DISABLED: Spell cache initialization disabled
# init_cache_storage()


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

# Global scraping status tracking
scraping_status = {
    'is_scraping': False,
    'current_class': None,
    'progress_percent': 0,
    'classes_completed': 0,
    'total_classes': 0,
    'start_time': None,
    'last_update': None
}

# All spell system configuration and cache variables removed

# Spell system completely removed

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with server memory status"""
    # This endpoint should not be rate limited
    
    # Check content database status
    content_db_status = {'connected': False}
    try:
        from utils.content_db_manager import get_content_db_manager
        manager = get_content_db_manager()
        content_db_status = manager.get_connection_status()
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'startup_complete': server_startup_progress['startup_complete'],
        'content_database': content_db_status
    })

@app.route('/api/health/database', methods=['GET'])
@exempt_when_limiting
def database_health_check():
    """Health check specifically for database connections to diagnose hanging issues."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Test content database connection
    try:
        start_time = time.time()
        from utils.content_db_manager import get_content_db_manager
        manager = get_content_db_manager()
        
        # Get detailed connection status
        connection_status = manager.get_connection_status()
        response_time = time.time() - start_time
        
        health_status['checks']['content_database'] = {
            'status': 'healthy' if connection_status.get('connected') else 'unhealthy',
            'response_time_ms': round(response_time * 1000, 2),
            'details': connection_status
        }
        
        if not connection_status.get('connected'):
            overall_healthy = False
            
    except Exception as e:
        health_status['checks']['content_database'] = {
            'status': 'error',
            'error': str(e),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        overall_healthy = False
    
    # Set overall status
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
    health_status['overall_healthy'] = overall_healthy
    
    return jsonify(health_status), 200 if overall_healthy else 503

@app.route('/api/cleanup', methods=['POST'])
def cleanup_connections():
    """Force cleanup of database connections and resources to prevent hanging."""
    try:
        # Force cleanup of content database manager
        from utils.content_db_manager import get_content_db_manager
        manager = get_content_db_manager()
        if hasattr(manager, 'cleanup'):
            manager.cleanup()
        
        # Clear any cached connections
        import gc
        gc.collect()
        
        app.logger.info("Connection cleanup completed successfully")
        return jsonify({
            'status': 'success',
            'message': 'Connection cleanup completed',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Cleanup failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Cleanup failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/items/search', methods=['GET'])
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)  # Liberal limits for normal users
def search_items():
    """
    Search discovered items in the EQEmu database.
    Only returns items that exist in both items and discovered_items tables.
    """
    app.logger.info("=== ITEM SEARCH START ===")
    conn = None
    cursor = None
    
    try:
        # Get database connection using the helper function
        app.logger.info("Getting database connection...")
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"No connection available: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        app.logger.info(f"Got connection, db_type: {db_type}")
        
        # Validate parameters
        validated_params = validate_item_search_params(request.args)
        search_query = validated_params.get('q', '')
        limit = validated_params.get('limit', 20)
        offset = validated_params.get('offset', 0)
        filters = validated_params.get('filters', [])
        
        app.logger.info(f"Search params: q='{search_query}', limit={limit}, offset={offset}, filters={len(filters)}")
        
        if not search_query and not filters:
            return jsonify({'error': 'Search query or filters required'}), 400
        
        cursor = conn.cursor()
        
        # Build WHERE clause and parameters
        where_conditions = []
        query_params = []
        
        # Add search query condition if present
        if search_query:
            where_conditions.append("items.Name LIKE %s")
            query_params.append(f'%{search_query}%')
        
        # Add filter conditions
        for filter_item in filters:
            field = filter_item['field']
            operator = filter_item['operator']
            value = filter_item.get('value')
            
            # Map frontend field names to database column names
            field_mapping = {
                'name': 'items.Name',
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
                'weight': 'items.weight',
                'damage': 'items.damage',
                'delay': 'items.delay',
                'magic': 'items.magic',
                'nodrop': 'items.nodrop',
                'norent': 'items.norent',
                'classes': 'items.classes',
                'races': 'items.races',
                'reqlevel': 'items.reqlevel',
                'stackable': 'items.stackable',
                'stacksize': 'items.stacksize',
                'icon': 'items.icon',
                'price': 'items.price',
                'size': 'items.size',
                'mr': 'items.mr',
                'fr': 'items.fr',
                'cr': 'items.cr',
                'dr': 'items.dr',
                'pr': 'items.pr',
                'reclevel': 'items.reclevel',
                'lore_flag': 'items.loregroup',
                'lore': 'items.lore',
                'loretext': 'items.lore',  # Map loretext to lore column
                'clickeffect': 'items.clickeffect',
                'proceffect': 'items.proceffect',
                'worneffect': 'items.worneffect',
                'focuseffect': 'items.focuseffect',
                'slots': 'items.slots'
            }
            
            db_field = field_mapping.get(field, f'items.{field}')
            
            # Build condition based on operator
            if operator == 'contains':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}%')
            elif operator == 'equals':
                where_conditions.append(f"{db_field} = %s")
                query_params.append(value)
            elif operator == 'not equals':
                where_conditions.append(f"{db_field} != %s")
                query_params.append(value)
            elif operator == 'greater than':
                where_conditions.append(f"{db_field} > %s")
                query_params.append(value)
            elif operator == 'less than':
                where_conditions.append(f"{db_field} < %s")
                query_params.append(value)
            elif operator == 'between':
                if isinstance(value, list) and len(value) == 2:
                    where_conditions.append(f"{db_field} BETWEEN %s AND %s")
                    query_params.extend([value[0], value[1]])
            elif operator == 'is':
                # For boolean fields
                if field in ['magic', 'nodrop', 'norent']:
                    # Convert boolean to int (0 or 1)
                    bool_value = 1 if value else 0
                    # Note: nodrop and norent are inverted in the database (0=True, 1=False)
                    if field in ['nodrop', 'norent']:
                        bool_value = 0 if value else 1
                    where_conditions.append(f"{db_field} = %s")
                    query_params.append(bool_value)
                elif field == 'lore_flag':
                    # loregroup: 0 = not lore, non-zero = lore
                    if value:
                        where_conditions.append(f"{db_field} != 0")
                    else:
                        where_conditions.append(f"{db_field} = 0")
            elif operator == 'exists':
                # For effect fields
                if value:
                    where_conditions.append(f"{db_field} IS NOT NULL AND {db_field} != 0 AND {db_field} != -1")
                else:
                    where_conditions.append(f"({db_field} IS NULL OR {db_field} = 0 OR {db_field} = -1)")
            elif operator == 'includes' and field == 'slots':
                # Bitwise AND for slot checking
                where_conditions.append(f"({db_field} & %s) != 0")
                query_params.append(value)
            elif operator == 'starts with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'{value}%')
            elif operator == 'ends with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}')
        
        # Combine all WHERE conditions
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build queries with dynamic WHERE clause
        # First get count
        count_query = f"""
            SELECT COUNT(*) AS total_count
            FROM items 
            INNER JOIN discovered_items di ON items.id = di.item_id
            WHERE {where_clause}
        """
        cursor.execute(count_query, query_params)
        result = cursor.fetchone()
        total_count = result['total_count'] if isinstance(result, dict) else result[0]
        
        # Then get items
        items_query = f"""
            SELECT 
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
                items.loregroup,
                items.reqlevel,
                items.stackable,
                items.stacksize,
                items.icon,
                items.price,
                items.size,
                items.mr,
                items.fr,
                items.cr,
                items.dr,
                items.pr,
                items.reclevel,
                items.clickeffect,
                items.proceffect,
                items.worneffect,
                items.focuseffect
            FROM items 
            INNER JOIN discovered_items di ON items.id = di.item_id
            WHERE {where_clause}
            ORDER BY items.Name
            LIMIT %s OFFSET %s
        """
        # Add limit and offset to params
        items_params = query_params + [limit, offset]
        
        # Execute with timeout protection
        try:
            cursor.execute(items_query, items_params)
        except Exception as e:
            app.logger.error(f"Database query failed: {e}")
            app.logger.error(f"Query: {items_query}")
            app.logger.error(f"Params: {items_params}")
            raise Exception("Database query failed - connection may have timed out")
            
        items = cursor.fetchall()
        
        # Convert to response format
        items_list = []
        for item in items:
            if isinstance(item, dict):
                item_dict = {
                    'item_id': str(item['id']),
                    'name': item['Name'],
                    'itemtype': item['itemtype'],
                    'ac': _safe_int(item['ac']),
                    'hp': _safe_int(item['hp']),
                    'mana': _safe_int(item['mana']),
                    'str': _safe_int(item['astr']),
                    'sta': _safe_int(item['asta']),
                    'agi': _safe_int(item['aagi']),
                    'dex': _safe_int(item['adex']),
                    'wis': _safe_int(item['awis']),
                    'int': _safe_int(item['aint']),
                    'cha': _safe_int(item['acha']),
                    'weight': _safe_float(item['weight']),
                    'damage': _safe_int(item['damage']),
                    'delay': _safe_int(item['delay']),
                    'magic': bool(item['magic']),
                    'nodrop': not bool(item['nodrop']),  # Inverted: 0=True, 1=False
                    'norent': not bool(item['norent']),  # Inverted: 0=True, 1=False
                    'lore': item['lore'],
                    'lore_flag': bool(item['loregroup'] != 0),  # 0=not lore, non-zero=lore
                    'classes': _safe_int(item['classes']),
                    'races': _safe_int(item['races']),
                    'slots': _safe_int(item['slots']),
                    'reqlevel': _safe_int(item['reqlevel']),
                    'stackable': bool(item['stackable']),
                    'stacksize': _safe_int(item['stacksize']),
                    'icon': _safe_int(item['icon']),
                    'price': _safe_int(item['price']),
                    'size': _safe_int(item['size']),
                    'mr': _safe_int(item['mr']),
                    'fr': _safe_int(item['fr']),
                    'cr': _safe_int(item['cr']),
                    'dr': _safe_int(item['dr']),
                    'pr': _safe_int(item['pr']),
                    'reclevel': _safe_int(item['reclevel']),
                    'clickeffect': _safe_int(item['clickeffect']),
                    'proceffect': _safe_int(item['proceffect']),
                    'worneffect': _safe_int(item['worneffect']),
                    'focuseffect': _safe_int(item['focuseffect'])
                }
            else:
                # Handle tuple results
                item_dict = {
                    'item_id': str(item[0]),
                    'name': item[1],
                    'itemtype': item[2],
                    'ac': _safe_int(item[3]),
                    'hp': _safe_int(item[4]),
                    'mana': _safe_int(item[5]),
                    'str': _safe_int(item[6]),
                    'sta': _safe_int(item[7]),
                    'agi': _safe_int(item[8]),
                    'dex': _safe_int(item[9]),
                    'wis': _safe_int(item[10]),
                    'int': _safe_int(item[11]),
                    'cha': _safe_int(item[12]),
                    'weight': _safe_float(item[13]),
                    'damage': _safe_int(item[14]),
                    'delay': _safe_int(item[15]),
                    'magic': bool(item[16]),
                    'nodrop': not bool(item[17]),  # Inverted: 0=True, 1=False
                    'norent': not bool(item[18]),  # Inverted: 0=True, 1=False
                    'classes': _safe_int(item[19]),
                    'races': _safe_int(item[20]),
                    'slots': _safe_int(item[21]),
                    'lore': item[22],
                    'lore_flag': bool(item[23] != 0),  # 0=not lore, non-zero=lore
                    'reqlevel': _safe_int(item[24]),
                    'stackable': bool(item[25]),
                    'stacksize': _safe_int(item[26]),
                    'icon': _safe_int(item[27]),
                    'price': _safe_int(item[28]),
                    'size': _safe_int(item[29]),
                    'mr': _safe_int(item[30]),
                    'fr': _safe_int(item[31]),
                    'cr': _safe_int(item[32]),
                    'dr': _safe_int(item[33]),
                    'pr': _safe_int(item[34]),
                    'reclevel': _safe_int(item[35]),
                    'clickeffect': _safe_int(item[36]),
                    'proceffect': _safe_int(item[37]),
                    'worneffect': _safe_int(item[38]),
                    'focuseffect': _safe_int(item[39])
                }
            items_list.append(item_dict)
        
        return jsonify({
            'items': items_list,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'search_query': search_query,
            'filters': filters
        })
        
    except Exception as e:
        app.logger.error(f"Error searching items: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

@app.route('/api/spells/search', methods=['GET'])
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)  # Same limits as item search
def search_spells_new():
    """
    Search spells in the EQEmu database.
    Searches the spells_new table for spells matching the criteria.
    """
    app.logger.info("=== SPELL SEARCH START ===")
    conn = None
    cursor = None
    
    try:
        # Get database connection using the helper function
        app.logger.info("Getting database connection...")
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"No connection available: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        app.logger.info(f"Got connection, db_type: {db_type}")
        
        # Validate parameters
        validated_params = validate_spell_search_params(request.args)
        search_query = validated_params.get('q', '')
        limit = validated_params.get('limit', 20)
        offset = validated_params.get('offset', 0)
        filters = validated_params.get('filters', [])
        
        app.logger.info(f"Search params: q='{search_query}', limit={limit}, offset={offset}, filters={len(filters)}")
        
        if not search_query and not filters:
            return jsonify({'error': 'Search query or filters required'}), 400
        
        cursor = conn.cursor()
        
        # Build WHERE clause and parameters
        where_conditions = []
        query_params = []
        
        # Add search query condition if present
        if search_query:
            where_conditions.append("spells_new.name LIKE %s")
            query_params.append(f'%{search_query}%')
        
        # Add filter conditions
        for filter_item in filters:
            field = filter_item['field']
            operator = filter_item['operator']
            value = filter_item.get('value')
            
            # Map frontend field names to database column names
            field_mapping = {
                'name': 'spells_new.name',
                'mana': 'spells_new.mana',
                'cast_time': 'spells_new.cast_time',
                'range': 'spells_new.range',
                'targettype': 'spells_new.targettype',
                'skill': 'spells_new.skill',
                'resisttype': 'spells_new.resisttype',
                'spell_category': 'spells_new.spell_category',
                'buffduration': 'spells_new.buffduration',
                'deities': 'spells_new.deities',
                # Class level requirements
                'warrior_level': 'spells_new.classes1',
                'cleric_level': 'spells_new.classes2',
                'paladin_level': 'spells_new.classes3',
                'ranger_level': 'spells_new.classes4',
                'shadowknight_level': 'spells_new.classes5',
                'druid_level': 'spells_new.classes6',
                'monk_level': 'spells_new.classes7',
                'bard_level': 'spells_new.classes8',
                'rogue_level': 'spells_new.classes9',
                'shaman_level': 'spells_new.classes10',
                'necromancer_level': 'spells_new.classes11',
                'wizard_level': 'spells_new.classes12',
                'magician_level': 'spells_new.classes13',
                'enchanter_level': 'spells_new.classes14',
                'beastlord_level': 'spells_new.classes15',
                'berserker_level': 'spells_new.classes16',
                # Spell effects
                'effect1': 'spells_new.effectid1',
                'effect2': 'spells_new.effectid2',
                'effect3': 'spells_new.effectid3',
                'effect4': 'spells_new.effectid4',
                'effect5': 'spells_new.effectid5',
                'effect6': 'spells_new.effectid6',
                'effect7': 'spells_new.effectid7',
                'effect8': 'spells_new.effectid8',
                'effect9': 'spells_new.effectid9',
                'effect10': 'spells_new.effectid10',
                'effect11': 'spells_new.effectid11',
                'effect12': 'spells_new.effectid12',
                # Components
                'component1': 'spells_new.components1',
                'component2': 'spells_new.components2',
                'component3': 'spells_new.components3',
                'component4': 'spells_new.components4'
            }
            
            db_field = field_mapping.get(field, f'spells_new.{field}')
            
            # Build condition based on operator
            if operator == 'contains':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}%')
            elif operator == 'equals':
                where_conditions.append(f"{db_field} = %s")
                query_params.append(value)
            elif operator == 'not equals':
                where_conditions.append(f"{db_field} != %s")
                query_params.append(value)
            elif operator == 'greater than':
                where_conditions.append(f"{db_field} > %s")
                query_params.append(value)
            elif operator == 'less than':
                where_conditions.append(f"{db_field} < %s")
                query_params.append(value)
            elif operator == 'between':
                if isinstance(value, list) and len(value) == 2:
                    where_conditions.append(f"{db_field} BETWEEN %s AND %s")
                    query_params.extend([value[0], value[1]])
            elif operator == 'exists':
                # For effect fields and components
                if value:
                    where_conditions.append(f"{db_field} IS NOT NULL AND {db_field} != 0 AND {db_field} != -1")
                else:
                    where_conditions.append(f"({db_field} IS NULL OR {db_field} = 0 OR {db_field} = -1)")
            elif operator == 'class_can_use':
                # Special operator for class level requirements (255 = cannot use)
                if value:
                    where_conditions.append(f"{db_field} != 255")
                else:
                    where_conditions.append(f"{db_field} = 255")
            elif operator == 'starts with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'{value}%')
            elif operator == 'ends with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}')
        
        # Combine all WHERE conditions
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build queries with dynamic WHERE clause
        # First get count
        count_query = f"""
            SELECT COUNT(*) AS total_count
            FROM spells_new
            WHERE {where_clause}
        """
        cursor.execute(count_query, query_params)
        result = cursor.fetchone()
        total_count = result['total_count'] if isinstance(result, dict) else result[0]
        
        # Then get spells
        spells_query = f"""
            SELECT 
                spells_new.id,
                spells_new.name,
                spells_new.mana,
                spells_new.cast_time,
                spells_new.range,
                spells_new.targettype,
                spells_new.skill,
                spells_new.resisttype,
                spells_new.spell_category,
                spells_new.buffduration,
                spells_new.deities,
                spells_new.classes1,
                spells_new.classes2,
                spells_new.classes3,
                spells_new.classes4,
                spells_new.classes5,
                spells_new.classes6,
                spells_new.classes7,
                spells_new.classes8,
                spells_new.classes9,
                spells_new.classes10,
                spells_new.classes11,
                spells_new.classes12,
                spells_new.classes13,
                spells_new.classes14,
                spells_new.classes15,
                spells_new.classes16,
                spells_new.effectid1,
                spells_new.effectid2,
                spells_new.effectid3,
                spells_new.effectid4,
                spells_new.effectid5,
                spells_new.effectid6,
                spells_new.effectid7,
                spells_new.effectid8,
                spells_new.effectid9,
                spells_new.effectid10,
                spells_new.effectid11,
                spells_new.effectid12,
                spells_new.components1,
                spells_new.components2,
                spells_new.components3,
                spells_new.components4,
                spells_new.icon,
                spells_new.new_icon
            FROM spells_new
            WHERE {where_clause}
            ORDER BY spells_new.name
            LIMIT %s OFFSET %s
        """
        # Add limit and offset to params
        spells_params = query_params + [limit, offset]
        
        # Execute with timeout protection
        try:
            cursor.execute(spells_query, spells_params)
        except Exception as e:
            app.logger.error(f"Database query failed: {e}")
            app.logger.error(f"Query: {spells_query}")
            app.logger.error(f"Params: {spells_params}")
            raise Exception("Database query failed - connection may have timed out")
            
        spells = cursor.fetchall()
        
        # Convert to response format
        spells_list = []
        for spell in spells:
            if isinstance(spell, dict):
                spell_dict = {
                    'spell_id': str(spell['id']),
                    'name': spell['name'],
                    'mana': _safe_int(spell['mana']),
                    'cast_time': _safe_int(spell['cast_time']),
                    'range': _safe_int(spell['range']),
                    'targettype': _safe_int(spell['targettype']),
                    'skill': _safe_int(spell['skill']),
                    'resisttype': _safe_int(spell['resisttype']),
                    'spell_category': _safe_int(spell['spell_category']),
                    'buffduration': _safe_int(spell['buffduration']),
                    'deities': _safe_int(spell['deities']),
                    'class_levels': {
                        'warrior': _safe_int(spell['classes1']),
                        'cleric': _safe_int(spell['classes2']),
                        'paladin': _safe_int(spell['classes3']),
                        'ranger': _safe_int(spell['classes4']),
                        'shadowknight': _safe_int(spell['classes5']),
                        'druid': _safe_int(spell['classes6']),
                        'monk': _safe_int(spell['classes7']),
                        'bard': _safe_int(spell['classes8']),
                        'rogue': _safe_int(spell['classes9']),
                        'shaman': _safe_int(spell['classes10']),
                        'necromancer': _safe_int(spell['classes11']),
                        'wizard': _safe_int(spell['classes12']),
                        'magician': _safe_int(spell['classes13']),
                        'enchanter': _safe_int(spell['classes14']),
                        'beastlord': _safe_int(spell['classes15']),
                        'berserker': _safe_int(spell['classes16'])
                    },
                    'effects': [
                        _safe_int(spell['effectid1']),
                        _safe_int(spell['effectid2']),
                        _safe_int(spell['effectid3']),
                        _safe_int(spell['effectid4']),
                        _safe_int(spell['effectid5']),
                        _safe_int(spell['effectid6']),
                        _safe_int(spell['effectid7']),
                        _safe_int(spell['effectid8']),
                        _safe_int(spell['effectid9']),
                        _safe_int(spell['effectid10']),
                        _safe_int(spell['effectid11']),
                        _safe_int(spell['effectid12'])
                    ],
                    'components': [
                        _safe_int(spell['components1']),
                        _safe_int(spell['components2']),
                        _safe_int(spell['components3']),
                        _safe_int(spell['components4'])
                    ],
                    'icon': _safe_int(spell['icon']),
                    'new_icon': _safe_int(spell['new_icon'])
                }
            else:
                # Handle tuple results
                spell_dict = {
                    'spell_id': str(spell[0]),
                    'name': spell[1],
                    'mana': _safe_int(spell[2]),
                    'cast_time': _safe_int(spell[3]),
                    'range': _safe_int(spell[4]),
                    'targettype': _safe_int(spell[5]),
                    'skill': _safe_int(spell[6]),
                    'resisttype': _safe_int(spell[7]),
                    'spell_category': _safe_int(spell[8]),
                    'buffduration': _safe_int(spell[9]),
                    'deities': _safe_int(spell[10]),
                    'class_levels': {
                        'warrior': _safe_int(spell[11]),
                        'cleric': _safe_int(spell[12]),
                        'paladin': _safe_int(spell[13]),
                        'ranger': _safe_int(spell[14]),
                        'shadowknight': _safe_int(spell[15]),
                        'druid': _safe_int(spell[16]),
                        'monk': _safe_int(spell[17]),
                        'bard': _safe_int(spell[18]),
                        'rogue': _safe_int(spell[19]),
                        'shaman': _safe_int(spell[20]),
                        'necromancer': _safe_int(spell[21]),
                        'wizard': _safe_int(spell[22]),
                        'magician': _safe_int(spell[23]),
                        'enchanter': _safe_int(spell[24]),
                        'beastlord': _safe_int(spell[25]),
                        'berserker': _safe_int(spell[26])
                    },
                    'effects': [
                        _safe_int(spell[27]),
                        _safe_int(spell[28]),
                        _safe_int(spell[29]),
                        _safe_int(spell[30]),
                        _safe_int(spell[31]),
                        _safe_int(spell[32]),
                        _safe_int(spell[33]),
                        _safe_int(spell[34]),
                        _safe_int(spell[35]),
                        _safe_int(spell[36]),
                        _safe_int(spell[37]),
                        _safe_int(spell[38])
                    ],
                    'components': [
                        _safe_int(spell[39]),
                        _safe_int(spell[40]),
                        _safe_int(spell[41]),
                        _safe_int(spell[42])
                    ],
                    'icon': _safe_int(spell[43]),
                    'new_icon': _safe_int(spell[44])
                }
            spells_list.append(spell_dict)
        
        return jsonify({
            'spells': spells_list,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'search_query': search_query,
            'filters': filters
        })
        
    except Exception as e:
        app.logger.error(f"Error searching spells: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

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
    """DISABLED - spell system disabled"""
    logger.info("Cache loading disabled - spell system disabled")
    pass

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
    """DISABLED - spell system disabled"""
    logger.info("Cache saving disabled - spell system disabled")
    pass

def save_single_class_to_storage(class_name):
    """DISABLED - spell system disabled"""
    logger.info("Single class cache saving disabled - spell system disabled")
    pass

def save_cache_to_database():
    """DISABLED - spell system disabled"""
    logger.info("Database cache saving disabled - spell system disabled")
    pass
    
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
    """DISABLED - spell system disabled"""
    logger.info("File cache saving disabled - spell system disabled")
    pass
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
# Skip for gunicorn workers to prevent timeout
# DISABLED: Spell cache loading disabled
# if __name__ == '__main__' or os.environ.get('FORCE_CACHE_LOAD'):
#     load_cache_from_storage()
# else:
#     logger.info("Skipping initial cache load for gunicorn worker")



def is_cache_expired(class_name):
    """DISABLED - spell system disabled"""
    return True

def is_pricing_cache_expired(spell_id):
    """DISABLED - spell system disabled"""
    return True
    expiry_time = cache_time + timedelta(hours=PRICING_CACHE_EXPIRY_HOURS)
    return datetime.now() > expiry_time

def clear_expired_cache():
    """DISABLED - spell system disabled"""
    logger.info("Cache clearing disabled - spell system disabled")
    pass
    
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
    """Get spells for a specific class - SPELL SYSTEM DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/scrape-all', methods=['POST'])
def scrape_all_classes():
    """Scrape spells for all classes - SPELL SYSTEM DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get list of all available classes - SPELL SYSTEM DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503


@app.route('/api/cache-status', methods=['GET'])
def get_cache_status():
    """Get cache status for all classes - SPELL SYSTEM DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/cache-expiry-status/<class_name>', methods=['GET'])
def get_cache_expiry_status(class_name):
    """Get cache expiry status for a specific class - DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/refresh-progress/<class_name>', methods=['GET'])
def get_refresh_progress(class_name):
    """Get current refresh progress for a specific class - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/refresh-spell-cache/<class_name>', methods=['POST'])
def refresh_spell_cache(class_name):
    """Manually refresh spell cache for a specific class with progress tracking - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/refresh-pricing-cache/<class_name>', methods=['POST'])
def refresh_pricing_cache_for_class(class_name):
    """Manually refresh pricing cache for all spells in a class - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/retry-failed-pricing/<class_name>', methods=['POST'])
def retry_failed_pricing_for_class(class_name):
    """Retry pricing fetch for all previously failed spells in a class - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/merge-pricing-cache', methods=['POST'])
def merge_pricing_cache():
    """Merge pricing data from UI into the cache - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/spell-states/<class_name>', methods=['GET'])
def get_spell_states(class_name):
    """Get pricing states for spells in a class (untried, failed, success) - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/spell-details/<int:spell_id>', methods=['GET'])
def get_spell_details(spell_id):
    """Get detailed spell information from alla website - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

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
    """Search for spells across all classes - SPELL SYSTEM DISABLED"""
    return jsonify({
        'error': 'Spell system disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

# Global session for connection pooling with proper timeouts
import requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
})

# Configure session timeouts to prevent hanging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

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
    """Get pricing for multiple spells with optimized fetching - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/startup-status', methods=['GET'])
def startup_status():
    """Get current scraping status"""
    # Return scraping status if scraping is active, otherwise return server startup status
    if scraping_status['is_scraping']:
        return jsonify({
            'scraping_in_progress': True,
            'current_class': scraping_status['current_class'],
            'progress_percent': scraping_status['progress_percent'],
            'classes_completed': scraping_status['classes_completed'],
            'total_classes': scraping_status['total_classes'],
            'start_time': scraping_status['start_time'],
            'last_update': scraping_status['last_update']
        })
    else:
        # Return idle status when not scraping
        return jsonify({
            'scraping_in_progress': False,
            'current_class': None,
            'progress_percent': 0,
            'startup_complete': server_startup_progress['startup_complete']
        })


@app.route('/api/initialize', methods=['POST'])
def initialize_cache():
    """Initialize cache after server startup - DISABLED"""
    global server_startup_progress
    
    # Mark startup as complete
    server_startup_progress['startup_complete'] = True
    
    return jsonify({
        'message': 'Cache initialization disabled - spell system disabled',
        'cached_classes': 0,
        'cached_spell_details': 0,
        'storage_type': 'disabled'
    })

@app.route('/api/cache/save', methods=['POST'])
def save_cache():
    """Manually save cache to disk - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached data - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """Get detailed cache status - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/debug/pricing-lookup/<class_name>', methods=['GET'])
def debug_pricing_lookup(class_name):
    """Debug endpoint to check pricing lookup for a specific class - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/debug/cache-keys', methods=['GET'])
def debug_cache_keys():
    """Debug endpoint to examine cache key formatting and contents - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

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
        
        # Step 2: Skip cache loading - spell system disabled
        update_startup_progress("Cache loading skipped - spell system disabled", 2)
        logger.info("🚫 Skipping cache loading - spell system disabled")
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 3: Skip spell cache refresh - system disabled
        update_startup_progress("Spell cache refresh skipped - system disabled", 3)
        logger.info("🚫 Skipping spell cache refresh - spell system disabled")
        
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 4: Skip pricing data loading - system disabled
        update_startup_progress("Pricing data loading skipped - system disabled", 4)
        logger.info("🚫 Skipping pricing data loading - spell system disabled")
        time.sleep(0.5)  # Brief pause for UI feedback
        
        # Step 5: Finalize and report
        update_startup_progress("Finalizing server startup...", 5)
        
        # Mark startup as complete
        startup_time = round(time.time() - startup_start_time, 2)
        server_startup_progress.update({
            'is_starting': False,
            'current_step': 'Server ready! (Spell system disabled)',
            'progress_percent': 100,
            'startup_complete': True,
            'startup_time': startup_time
        })
        
        logger.info(f"✅ Server startup complete in {startup_time}s!")
        logger.info(f"🚫 Spell system disabled - no spell caching performed")
        logger.info(f"🎯 Server ready for items system and admin functionality!")
        
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
    """Debug endpoint to clean up invalid cache entries and report what was found - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503

@app.route('/api/debug/cache-integrity', methods=['GET'])
def cache_integrity():
    """Debug endpoint to verify cache integrity and consistency - DISABLED"""
    return jsonify({
        'error': 'Spell system temporarily disabled',
        'message': 'The spell system is being redesigned and is currently unavailable.',
        'status': 'disabled'
    }), 503


# Database configuration management
from utils.db_config_manager import DatabaseConfigManager
from utils.db_connection_pool import close_connection_pool

# Initialize config manager
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
db_config_manager = DatabaseConfigManager(config_path)

# Force initial load to ensure we get persistent config
db_config_manager.get_config()
logger.info("Database config manager initialized")

# Add callback to close pool when config changes
def on_db_config_change():
    """Close connection pool when database config changes."""
    logger.info("Database configuration changed, closing connection pool")
    close_connection_pool()

db_config_manager.add_reload_callback(on_db_config_change)

# Initialize database connection on startup
def initialize_database_connection(max_retries=3, initial_delay=2):
    """Initialize and test database connection on startup with retry logic."""
    import time
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing database connection on startup (attempt {attempt + 1}/{max_retries})...")
            
            # Get current config
            config = db_config_manager.get_config()
            
            # Check if we have a database URL configured
            database_url = config.get('production_database_url', '')
            if not database_url:
                logger.warning("No database URL configured. Checking environment variables...")
                # Force a config reload to pick up env vars
                db_config_manager.invalidate()
                config = db_config_manager.get_config()
                database_url = config.get('production_database_url', '')
                
            if database_url:
                logger.info(f"Found database configuration from: {config.get('config_source', 'unknown')}")
                # Test the connection
                conn, db_type, error = get_eqemu_db_connection()
                if conn:
                    try:
                        # Verify connection works
                        cursor = conn.cursor()
                        if db_type == 'mysql':
                            cursor.execute("SELECT VERSION()")
                        elif db_type == 'postgresql':
                            cursor.execute("SELECT version()")
                        elif db_type == 'mssql':
                            cursor.execute("SELECT @@VERSION")
                        
                        result = cursor.fetchone()
                        version = result[0] if result else "Unknown"
                        cursor.close()
                        conn.close()
                        
                        logger.info(f"✅ Database connection successful! Type: {db_type}, Version: {version.split()[0]}")
                        return True
                    except Exception as e:
                        logger.error(f"❌ Database connection test failed: {e}")
                        if conn:
                            try:
                                conn.close()
                            except:
                                pass
                else:
                    logger.error(f"❌ Failed to establish database connection: {error}")
                    
                # If we have more retries, wait with exponential backoff
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
            else:
                logger.warning("⚠️ No database configuration found. Database features will be unavailable.")
                logger.info("💡 Set EQEMU_DATABASE_URL environment variable or configure through admin panel")
                return False  # No point retrying if no config
            
        except Exception as e:
            logger.error(f"❌ Error during database initialization attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
    
    logger.error(f"❌ Failed to establish database connection after {max_retries} attempts")
    return False

# Helper function for EQEmu database connection
def get_eqemu_db_connection():
    """Get connection to the configured EQEmu database with automatic reconnection.
    
    WARNING: This function returns a raw connection for backward compatibility.
    Callers MUST close the connection when done to avoid connection leaks!
    
    Consider refactoring to use context managers instead.
    """
    from utils.content_db_manager import get_content_db_manager
    from utils.database_connectors import get_database_connector
    
    try:
        # Get the content database manager
        manager = get_content_db_manager()
        
        # Get connection status for logging
        status = manager.get_connection_status()
        app.logger.debug(f"Content DB status: connected={status['connected']}, "
                        f"pool_active={status['pool_active']}, "
                        f"db_type={status['database_type']}")
        
        # For backward compatibility, create a direct connection
        # This avoids the pooling complexity but ensures connections are closed
        config = db_config_manager.get_config()
        database_url = config.get('production_database_url', '')
        
        if not database_url:
            return None, None, "Database not configured"
            
        # Parse database URL
        from urllib.parse import urlparse
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
        
        # Add connection timeout settings to prevent hanging
        if db_type == 'mysql':
            db_config.update({
                'connect_timeout': 5,   # 5 second connection timeout (reduced from 10)
                'read_timeout': 15,     # 15 second read timeout (reduced from 30)
                'write_timeout': 15,    # 15 second write timeout (reduced from 30)
                'autocommit': True      # Enable autocommit to avoid transaction hangs
            })
        elif db_type == 'postgresql':
            db_config.update({
                'connect_timeout': 5    # 5 second connection timeout (reduced from 10)
            })
        elif db_type == 'mssql':
            db_config.update({
                'timeout': 5            # 5 second timeout for MSSQL
            })
        
        # Create direct connection with timeout
        conn = get_database_connector(db_type, db_config)
        return conn, db_type, None
        
    except Exception as e:
        app.logger.error(f"Failed to get database connection: {e}")
        return None, None, str(e)

# Context manager for safe database connections
from contextlib import contextmanager

@contextmanager
def safe_db_connection():
    """Context manager for safe database connections with automatic cleanup."""
    conn = None
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if error:
            raise Exception(f"Database connection failed: {error}")
        yield conn, db_type
    except Exception as e:
        app.logger.error(f"Database operation failed: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
                app.logger.debug("Database connection closed successfully")
            except Exception as e:
                app.logger.warning(f"Error closing database connection: {e}")

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
@app.route('/api/items/search-duplicate', methods=['GET'])  # TEMPORARY: renamed to avoid collision
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)  # Liberal limits for normal users
def search_items_duplicate():
    """
    Search discovered items in the EQEmu database.
    Only returns items that exist in both items and discovered_items tables.
    """
    app.logger.info("=== ITEM SEARCH START ===")
    conn = None
    cursor = None
    
    try:
        # Get database connection using the helper function
        app.logger.info("Getting database connection...")
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"No connection available: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        app.logger.info(f"Got connection, db_type: {db_type}")
        
        # Validate parameters
        validated_params = validate_item_search_params(request.args)
        search_query = validated_params.get('q', '')
        limit = validated_params.get('limit', 20)
        offset = validated_params.get('offset', 0)
        filters = validated_params.get('filters', [])
        
        app.logger.info(f"Search params: q='{search_query}', limit={limit}, offset={offset}, filters={len(filters)}")
        
        if not search_query and not filters:
            return jsonify({'error': 'Search query or filters required'}), 400
        
        cursor = conn.cursor()
        
        # Build WHERE clause and parameters
        where_conditions = []
        query_params = []
        
        # Add search query condition if present
        if search_query:
            where_conditions.append("items.Name LIKE %s")
            query_params.append(f'%{search_query}%')
        
        # Add filter conditions
        for filter_item in filters:
            field = filter_item['field']
            operator = filter_item['operator']
            value = filter_item.get('value')
            
            # Map frontend field names to database column names
            field_mapping = {
                'loretext': 'items.lore',
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
                'mr': 'items.mr',
                'fr': 'items.fr',
                'cr': 'items.cr',
                'dr': 'items.dr',
                'pr': 'items.pr',
                'reqlevel': 'items.reqlevel',
                'reclevel': 'items.reclevel',
                'magic': 'items.magic',
                'lore_flag': 'items.loregroup',
                'nodrop': 'items.nodrop',
                'norent': 'items.norent',
                'clickeffect': 'items.clickeffect',
                'proceffect': 'items.proceffect',
                'worneffect': 'items.worneffect',
                'focuseffect': 'items.focuseffect',
                'slots': 'items.slots'
            }
            
            db_field = field_mapping.get(field, f'items.{field}')
            
            # Build condition based on operator
            if operator == 'contains':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}%')
            elif operator == 'equals':
                where_conditions.append(f"{db_field} = %s")
                query_params.append(value)
            elif operator == 'not equals':
                where_conditions.append(f"{db_field} != %s")
                query_params.append(value)
            elif operator == 'greater than':
                where_conditions.append(f"{db_field} > %s")
                query_params.append(value)
            elif operator == 'less than':
                where_conditions.append(f"{db_field} < %s")
                query_params.append(value)
            elif operator == 'between':
                if isinstance(value, list) and len(value) == 2:
                    where_conditions.append(f"{db_field} BETWEEN %s AND %s")
                    query_params.extend([value[0], value[1]])
            elif operator == 'is':
                # For boolean fields
                if field in ['magic', 'nodrop', 'norent']:
                    # Convert boolean to int (0 or 1)
                    bool_value = 1 if value else 0
                    # Note: nodrop and norent are inverted in the database (0=True, 1=False)
                    if field in ['nodrop', 'norent']:
                        bool_value = 0 if value else 1
                    where_conditions.append(f"{db_field} = %s")
                    query_params.append(bool_value)
                elif field == 'lore_flag':
                    # loregroup: 0 = not lore, non-zero = lore
                    if value:
                        where_conditions.append(f"{db_field} != 0")
                    else:
                        where_conditions.append(f"{db_field} = 0")
            elif operator == 'exists':
                # For effect fields
                if value:
                    where_conditions.append(f"{db_field} IS NOT NULL AND {db_field} != 0 AND {db_field} != -1")
                else:
                    where_conditions.append(f"({db_field} IS NULL OR {db_field} = 0 OR {db_field} = -1)")
            elif operator == 'includes' and field == 'slots':
                # Bitwise AND for slot checking
                where_conditions.append(f"({db_field} & %s) != 0")
                query_params.append(value)
            elif operator == 'starts with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'{value}%')
            elif operator == 'ends with':
                where_conditions.append(f"{db_field} LIKE %s")
                query_params.append(f'%{value}')
        
        # Combine all WHERE conditions
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build queries with dynamic WHERE clause
        # First get count
        count_query = f"""
            SELECT COUNT(*) AS total_count
            FROM items 
            INNER JOIN discovered_items di ON items.id = di.item_id
            WHERE {where_clause}
        """
        cursor.execute(count_query, query_params)
        result = cursor.fetchone()
        total_count = result['total_count'] if isinstance(result, dict) else result[0]
        
        # Then get items
        items_query = f"""
            SELECT 
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
                items.loregroup,
                items.reqlevel,
                items.stackable,
                items.stacksize,
                items.icon,
                items.price,
                items.size,
                items.mr,
                items.fr,
                items.cr,
                items.dr,
                items.pr,
                items.reclevel,
                items.clickeffect,
                items.proceffect,
                items.worneffect,
                items.focuseffect
            FROM items 
            INNER JOIN discovered_items di ON items.id = di.item_id
            WHERE {where_clause}
            ORDER BY items.Name
            LIMIT %s OFFSET %s
        """
        # Add limit and offset to params
        items_params = query_params + [limit, offset]
        
        # Execute with timeout protection
        try:
            cursor.execute(items_query, items_params)
        except Exception as e:
            app.logger.error(f"Database query failed: {e}")
            app.logger.error(f"Query: {items_query}")
            app.logger.error(f"Params: {items_params}")
            raise Exception("Database query failed - connection may have timed out")
            
        items = cursor.fetchall()
        
        # Convert to response format
        items_list = []
        for item in items:
            if isinstance(item, dict):
                item_dict = {
                    'item_id': str(item['id']),
                    'name': item['Name'],
                    'itemtype': item['itemtype'],
                    'ac': _safe_int(item['ac']),
                    'hp': _safe_int(item['hp']),
                    'mana': _safe_int(item['mana']),
                    'str': _safe_int(item['astr']),
                    'sta': _safe_int(item['asta']),
                    'agi': _safe_int(item['aagi']),
                    'dex': _safe_int(item['adex']),
                    'wis': _safe_int(item['awis']),
                    'int': _safe_int(item['aint']),
                    'cha': _safe_int(item['acha']),
                    'weight': _safe_float(item['weight']),
                    'damage': _safe_int(item['damage']),
                    'delay': _safe_int(item['delay']),
                    'magic': bool(item['magic']),
                    'nodrop': not bool(item['nodrop']),  # Inverted: 0=True, 1=False
                    'norent': not bool(item['norent']),  # Inverted: 0=True, 1=False
                    'lore': item['lore'],
                    'lore_flag': bool(item['loregroup'] != 0),  # 0=not lore, non-zero=lore
                    'classes': _safe_int(item['classes']),
                    'races': _safe_int(item['races']),
                    'slots': _safe_int(item['slots']),
                    'reqlevel': _safe_int(item['reqlevel']),
                    'stackable': bool(item['stackable']),
                    'stacksize': _safe_int(item['stacksize']),
                    'icon': _safe_int(item['icon']),
                    'price': _safe_int(item['price']),
                    'size': _safe_int(item['size']),
                    'mr': _safe_int(item['mr']),
                    'fr': _safe_int(item['fr']),
                    'cr': _safe_int(item['cr']),
                    'dr': _safe_int(item['dr']),
                    'pr': _safe_int(item['pr']),
                    'reclevel': _safe_int(item['reclevel']),
                    'clickeffect': _safe_int(item['clickeffect']),
                    'proceffect': _safe_int(item['proceffect']),
                    'worneffect': _safe_int(item['worneffect']),
                    'focuseffect': _safe_int(item['focuseffect'])
                }
            else:
                # Handle tuple results
                item_dict = {
                    'item_id': str(item[0]),
                    'name': item[1],
                    'itemtype': item[2],
                    'ac': _safe_int(item[3]),
                    'hp': _safe_int(item[4]),
                    'mana': _safe_int(item[5]),
                    'str': _safe_int(item[6]),
                    'sta': _safe_int(item[7]),
                    'agi': _safe_int(item[8]),
                    'dex': _safe_int(item[9]),
                    'wis': _safe_int(item[10]),
                    'int': _safe_int(item[11]),
                    'cha': _safe_int(item[12]),
                    'weight': _safe_float(item[13]),
                    'damage': _safe_int(item[14]),
                    'delay': _safe_int(item[15]),
                    'magic': bool(item[16]),
                    'nodrop': not bool(item[17]),  # Inverted: 0=True, 1=False
                    'norent': not bool(item[18]),  # Inverted: 0=True, 1=False
                    'classes': _safe_int(item[19]),
                    'races': _safe_int(item[20]),
                    'slots': _safe_int(item[21]),
                    'lore': item[22],
                    'lore_flag': bool(item[23] != 0),  # 0=not lore, non-zero=lore
                    'reqlevel': _safe_int(item[24]),
                    'stackable': bool(item[25]),
                    'stacksize': _safe_int(item[26]),
                    'icon': _safe_int(item[27]),
                    'price': _safe_int(item[28]),
                    'size': _safe_int(item[29]),
                    'mr': _safe_int(item[30]),
                    'fr': _safe_int(item[31]),
                    'cr': _safe_int(item[32]),
                    'dr': _safe_int(item[33]),
                    'pr': _safe_int(item[34]),
                    'reclevel': _safe_int(item[35]),
                    'clickeffect': _safe_int(item[36]),
                    'proceffect': _safe_int(item[37]),
                    'worneffect': _safe_int(item[38]),
                    'focuseffect': _safe_int(item[39])
                }
            items_list.append(item_dict)
        
        return jsonify({
            'items': items_list,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'search_query': search_query,
            'filters': filters
        })
        
    except Exception as e:
        app.logger.error(f"Error searching items: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


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
                    'nodrop': not bool(item['nodrop']),  # Inverted: 0=True, 1=False
                    'norent': not bool(item['norent']),  # Inverted: 0=True, 1=False
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
    """Clean up resources on shutdown to prevent hanging."""
    logger.info("Cleaning up resources...")
    
    # Clean up HTTP session first
    try:
        if session:
            session.close()
            logger.info("HTTP session closed")
    except Exception as e:
        logger.error(f"Error closing HTTP session: {e}")
    
    # Close database connection pool
    try:
        close_connection_pool()
        logger.info("Connection pool closed")
    except Exception as e:
        logger.error(f"Error closing connection pool: {e}")
    
    # Close content database connections
    try:
        from utils.content_db_manager import get_content_db_manager
        manager = get_content_db_manager()
        manager.close()
        logger.info("Content database connections closed")
    except Exception as e:
        logger.error(f"Error closing content database: {e}")
    
    # Force garbage collection to clean up any remaining resources
    import gc
    gc.collect()
    logger.info("Garbage collection completed")

if __name__ == '__main__':
    import atexit
    
    # Register cleanup on exit
    atexit.register(cleanup_resources)
    
    # Initialize database connections on startup
    # Skip heavy database initialization in dev mode or testing for faster startup
    if os.environ.get('ENABLE_DEV_AUTH') == 'true' or os.environ.get('TESTING') == '1':
        if os.environ.get('TESTING') == '1':
            logger.info("⚡ Testing mode: Skipping database initialization for fast startup")
        else:
            logger.info("⚡ Dev mode: Skipping database initialization for fast startup")
        logger.info("⚡ Databases will be initialized on first request")
    else:
        initialize_database_connection()  # Auth database
        
        # Initialize content database with retry logic
        try:
            from utils.content_db_manager import initialize_content_database
            logger.info("Initializing content database...")
            if initialize_content_database():
                logger.info("✅ Content database initialized successfully")
            else:
                logger.warning("⚠️ Content database initialization failed - will retry on first request")
        except Exception as e:
            logger.error(f"Error initializing content database: {e}")
    
    # Spell system disabled - skipping spell data preloading
    logger.info("🚫 Spell system disabled - skipping startup spell data preload")
    
    # Mark server startup as complete
    server_startup_progress['is_starting'] = False
    server_startup_progress['startup_complete'] = True
    server_startup_progress['current_step'] = 'Server ready'
    server_startup_progress['progress_percent'] = 100
    server_startup_progress['startup_time'] = datetime.now().isoformat()
    logger.info("✅ Server startup complete")

# Error handlers for failed endpoint logging
@app.errorhandler(404)
def handle_404(error):
    """Log 404 errors for failed endpoint attempts"""
    endpoint = request.path
    method = request.method
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Create detailed error message with context
    error_msg = f"404 Not Found: {method} {endpoint}"
    
    # Determine if this looks like a disabled spell endpoint
    is_spell_endpoint = any(keyword in endpoint.lower() for keyword in [
        'spell', 'cache', 'classes', 'scrape'
    ])
    
    # Log with appropriate level and context
    if is_spell_endpoint:
        logger.info(f"🚫 Disabled spell endpoint accessed: {method} {endpoint} (404 Not Found) | IP: {ip} | User-Agent: {user_agent[:100]}")
    else:
        logger.warning(f"❌ Failed endpoint attempt: {method} {endpoint} (404 Not Found) | IP: {ip} | User-Agent: {user_agent[:100]}")
    
    # Track endpoint failure metrics
    try:
        from routes.admin import track_endpoint_metric
        track_endpoint_metric(
            f"{method} {endpoint}", 
            0,  # No response time for 404s
            is_error=True, 
            status_code=404,
            error_details=f"Endpoint not found: {error_msg} | IP: {ip}",
            stack_trace=None
        )
    except Exception:
        pass  # Don't let metrics tracking break error handling
    
    # Return JSON error for API endpoints
    if endpoint.startswith('/api/'):
        message = 'This endpoint is temporarily disabled' if is_spell_endpoint else f'The endpoint {method} {endpoint} does not exist'
        return jsonify({
            'error': 'Endpoint not found',
            'message': message,
            'status_code': 404
        }), 404
    
    # Return generic 404 for non-API endpoints
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(405)
def handle_405(error):
    """Log 405 errors for method not allowed"""
    endpoint = request.path
    method = request.method
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Create detailed error message
    error_msg = f"405 Method Not Allowed: {method} {endpoint}"
    
    # Log with details
    logger.warning(f"❌ Method not allowed: {method} {endpoint} (405 Method Not Allowed) | IP: {ip} | User-Agent: {user_agent[:100]}")
    
    return jsonify({
        'error': 'Method not allowed',
        'message': f'The method {method} is not allowed for endpoint {endpoint}',
        'status_code': 405
    }), 405

@app.errorhandler(500)
def handle_500(error):
    """Log 500 errors for internal server errors"""
    endpoint = request.path
    method = request.method
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Create detailed error message
    error_msg = f"500 Internal Server Error: {method} {endpoint}"
    
    # Log with details
    logger.error(f"💥 Server error: {method} {endpoint} (500 Internal Server Error) | IP: {ip} | User-Agent: {user_agent[:100]} | Error: {str(error)}")
    
    # Track endpoint failure metrics with full error details
    try:
        from routes.admin import track_endpoint_metric
        import traceback
        track_endpoint_metric(
            f"{method} {endpoint}", 
            0,  # No response time for server errors
            is_error=True, 
            status_code=500,
            error_details=f"Internal server error: {str(error)} | IP: {ip}",
            stack_trace=traceback.format_exc()
        )
    except Exception:
        pass  # Don't let metrics tracking break error handling
    
    return jsonify({
        'error': 'Internal server error',
        'message': 'An internal server error occurred',
        'status_code': 500
    }), 500

@app.errorhandler(503)
def handle_503(error):
    """Log 503 errors for service unavailable (disabled endpoints)"""
    endpoint = request.path
    method = request.method
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Create detailed error message
    error_msg = f"503 Service Unavailable: {method} {endpoint}"
    
    # Log with details (info level since these are expected for disabled spell endpoints)
    logger.info(f"🚫 Service unavailable: {method} {endpoint} (503 Service Unavailable) | IP: {ip} | User-Agent: {user_agent[:100]}")
    
    return jsonify({
        'error': 'Service temporarily unavailable',
        'message': 'This service is temporarily disabled',
        'status_code': 503
    }), 503

# Request logging middleware
@app.before_request
def log_request_info():
    """Log all incoming requests"""
    # Skip logging for admin system endpoints to prevent spam
    excluded_paths = ['/api/admin/system/', '/api/health']
    if request.path.startswith('/api/') and not any(request.path.startswith(path) for path in excluded_paths):
        method = request.method
        endpoint = request.path
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Log API requests at debug level
        logger.debug(f"📥 API Request: {method} {endpoint} | IP: {ip}")

@app.after_request
def log_response_info(response):
    """Log response information for failed requests"""
    # Skip logging for admin system endpoints to prevent spam
    excluded_paths = ['/api/admin/system/', '/api/health']
    if (request.path.startswith('/api/') and 
        response.status_code >= 400 and 
        not any(request.path.startswith(path) for path in excluded_paths)):
        
        method = request.method
        endpoint = request.path
        status = response.status_code
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Log failed API responses
        if status >= 500:
            logger.error(f"📤 API Response: {method} {endpoint} → {status} | IP: {ip}")
        elif status >= 400:
            logger.warning(f"📤 API Response: {method} {endpoint} → {status} | IP: {ip}")
    
    return response

if __name__ == '__main__':
    # Use threaded Flask server to prevent hanging with multiple requests
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=config['backend_port'],
        threaded=True,  # Enable threading to handle multiple requests
        use_reloader=False  # Disable reloader to prevent issues with database connections
    ) 