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

# Debug: Print environment immediately
print(f"[BACKEND STARTUP] ENABLE_DEV_AUTH = {os.environ.get('ENABLE_DEV_AUTH', 'NOT SET')}")
print(f"[BACKEND STARTUP] Python: {sys.executable}")
print(f"[BACKEND STARTUP] CWD: {os.getcwd()}")

# Import psycopg2 only when needed
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("⚠️ psycopg2 not available - PostgreSQL features disabled")

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

# Configure request timeout to prevent hanging connections
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No caching in development
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

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
    print(f"   - DEV_MODE_AUTH_BYPASS: {DEV_MODE_AUTH_BYPASS}")
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
    
    CORS(app, 
         origins=allowed_origins, 
         supports_credentials=True, 
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         automatic_options=True)
else:
    # Standard CORS for existing functionality
    CORS(app, 
         origins='*',
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         automatic_options=True)

# Decorator to conditionally apply rate limiting
def exempt_when_limiting(f):
    """Decorator to exempt endpoints from rate limiting when limiter is active"""
    if limiter:
        return limiter.exempt(f)
    return f

# Import search logging function regardless of OAuth status
try:
    from routes.admin import log_search_event
    SEARCH_LOGGING_AVAILABLE = True
except ImportError:
    SEARCH_LOGGING_AVAILABLE = False
    app.logger.warning("Search event logging not available - admin module not found")

# Import OAuth components only if enabled
if ENABLE_USER_ACCOUNTS:
    try:
        from routes.auth import auth_bp
        from routes.users import users_bp
        from routes.admin import admin_bp, initialize_test_data
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
                # Skip auth endpoints in dev mode, but allow admin and users endpoints
                if DEV_MODE_AUTH_BYPASS and request.endpoint.startswith('auth.'):
                    g.db_connection = None
                    return
                
                # Connect to database if DB_CONFIG is available (for OAuth)
                if DB_CONFIG:
                    try:
                        if DB_TYPE == 'postgresql':
                            if HAS_PSYCOPG2:
                                # Override with shorter timeout to prevent hanging
                                db_config_with_timeout = DB_CONFIG.copy()
                                db_config_with_timeout['connect_timeout'] = 2  # 2 second timeout
                                g.db_connection = psycopg2.connect(**db_config_with_timeout)
                            else:
                                raise Exception("psycopg2 not available")
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
                    track_endpoint_metric(endpoint_key, response_time, is_error, status_code)
                    error_details = None
                    
                    # Add error details for failed requests
                    if is_error and hasattr(response, 'get_data'):
                        try:
                            response_data = response.get_data(as_text=True)
                            if response_data and len(response_data) < 500:  # Limit size
                                error_details = response_data
                        except:
                            pass
                    
                    # Wrap in try-except to prevent metric tracking from breaking requests
                    try:
                        track_endpoint_metric(
                            endpoint_key, 
                            response_time, 
                            is_error, 
                            status_code=status_code,
                            error_details=error_details
                        )
                    except Exception as metric_error:
                        # Log but don't fail the request
                        app.logger.debug(f"Metric tracking error: {metric_error}")
                except ImportError:
                    pass  # Admin routes not loaded
                except Exception as e:
                    app.logger.error(f"Error tracking metrics: {e}")
            
            return response
        
        # Register OAuth blueprints
        app.register_blueprint(auth_bp, url_prefix='/api')
        app.register_blueprint(users_bp, url_prefix='/api')
        app.register_blueprint(admin_bp, url_prefix='/api')
        
        # Initialize test data for dev mode after blueprints are registered
        initialize_test_data()
        
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
    # Register minimal admin routes when OAuth is disabled
    try:
        from routes.admin_minimal import admin_minimal_bp
        app.register_blueprint(admin_minimal_bp, url_prefix='/api')
        app.logger.info("✅ Minimal admin routes registered (OAuth disabled)")
    except ImportError as e:
        app.logger.warning(f"⚠️ Could not load minimal admin routes: {e}")

# Load configuration
def load_config():
    """Load configuration from config.json and environment variables"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
    default_config = {
        'backend_port': 5001,
        'frontend_port': 3000,
        'cache_expiry_hours': 24,
        'pricing_cache_expiry_hours': 168,  # 1 week
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

# File handler with rotation - TEMPORARILY DISABLED FOR DEBUGGING
# TODO: Re-enable after fixing hanging issue
if False:  # Disabled to debug hanging
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path, maxBytes=10*1024*1024, backupCount=5  # 10MB max, 5 backup files
        )
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
        print(f"✅ Logging configured to write to: {log_file_path}")
    except Exception as e:
        print(f"⚠️ Could not set up file logging: {e}")
else:
    print("⚠️ File logging temporarily disabled for debugging")


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
    logger.info(f"DATABASE_URL starts with: {DATABASE_URL[:30]}...")
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
    logger.info(f"DB_CONFIG set with host: {DB_CONFIG['host']}, database: {DB_CONFIG['database']}")
else:
    logger.info(f"DB_CONFIG not set: DATABASE_URL={bool(DATABASE_URL)}, ENABLE_USER_ACCOUNTS={ENABLE_USER_ACCOUNTS}")
        
if DATABASE_URL and not ENABLE_USER_ACCOUNTS:
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
            if HAS_PSYCOPG2:
                conn = psycopg2.connect(**DB_CONFIG)
            else:
                raise Exception("psycopg2 not available")
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
    
    # Skip database status check for basic health endpoint to prevent timeouts
    # Database status can be checked via /api/health/database if needed
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'startup_complete': server_startup_progress['startup_complete'],
        'dev_mode': os.environ.get('ENABLE_DEV_AUTH') == 'true'
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
            app.logger.info(f"Executing item search query")
            start_time = time.time()
            cursor.execute(items_query, items_params)
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            app.logger.info(f"Item search query completed in {query_time:.2f}ms")
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
        
        # Log search event for monitoring
        try:
            # Gather user information including username when available
            user_info = {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            
            # Try to get authenticated user information
            current_user = None
            try:
                from utils.jwt_utils import get_current_user
                current_user = get_current_user()
                if current_user:
                    user_info['user_id'] = current_user.get('id')
                    user_info['user_email'] = current_user.get('email')
                    
                    # Get full user details for display name
                    if current_user.get('id') and ENABLE_USER_ACCOUNTS:
                        try:
                            from models.user import User
                            from utils.oauth import get_oauth_db_connection
                            oauth_conn = get_oauth_db_connection()
                            if oauth_conn:
                                user_model = User(oauth_conn)
                                user_details = user_model.get_user_by_id(current_user['id'])
                                if user_details:
                                    # Use display_name if available, otherwise first_name + last_name
                                    display_name = user_details.get('display_name')
                                    if not display_name:
                                        first_name = user_details.get('first_name', '')
                                        last_name = user_details.get('last_name', '')
                                        if first_name or last_name:
                                            display_name = f"{first_name} {last_name}".strip()
                                    
                                    if display_name:
                                        user_info['username'] = display_name
                                    else:
                                        user_info['username'] = current_user.get('email', 'Unknown User')
                        except Exception as e:
                            # Don't let user lookup break logging
                            pass
            except Exception as e:
                # Don't let auth check break logging
                pass
            
            # Gather filter information (handle both dict and list formats)
            applied_filters = {}
            if isinstance(filters, dict):
                applied_filters = {k: v for k, v in filters.items() if v is not None and v != ''}
            elif isinstance(filters, list):
                # Convert list of filters to a dict representation
                applied_filters = {'filter_count': len(filters), 'filters': filters} if filters else {}
            
            # Log the search event (always log search events for monitoring)
            if SEARCH_LOGGING_AVAILABLE:
                try:
                    log_search_event(
                        search_type='item',
                        query=search_query,
                        results_count=len(items_list),
                        execution_time_ms=round(query_time, 2),
                        filters=applied_filters if applied_filters else None,
                        user_info=user_info
                    )
                except Exception as log_error:
                    app.logger.error(f"Failed to log item search event: {log_error}")
        except Exception as e:
            # Don't let logging break the search
            app.logger.error(f"Error gathering search event data: {e}")
        
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
def search_spells():
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
            where_conditions.append("name LIKE %s")
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
        
        # Detect if a specific class level filter is being used for sorting
        class_field_for_sorting = None
        class_to_column_map = {
            'warrior_level': 'classes1',
            'cleric_level': 'classes2', 
            'paladin_level': 'classes3',
            'ranger_level': 'classes4',
            'shadowknight_level': 'classes5',
            'druid_level': 'classes6',
            'monk_level': 'classes7',
            'bard_level': 'classes8',
            'rogue_level': 'classes9',
            'shaman_level': 'classes10',
            'necromancer_level': 'classes11',
            'wizard_level': 'classes12',
            'magician_level': 'classes13',
            'enchanter_level': 'classes14',
            'beastlord_level': 'classes15',
            'berserker_level': 'classes16'
        }
        
        # Look for class level filters to determine sorting column
        for filter_item in filters:
            field = filter_item['field']
            if field in class_to_column_map:
                class_field_for_sorting = class_to_column_map[field]
                app.logger.info(f"Using {field} ({class_field_for_sorting}) for sorting")
                break
        
        # Combine all WHERE conditions
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build queries with dynamic WHERE clause
        # First get count - with a reasonable limit to prevent full table scans
        count_query = f"""
            SELECT COUNT(*) AS total_count
            FROM (
                SELECT 1 FROM spells_new
                WHERE {where_clause}
                LIMIT 10000
            ) AS limited_count
        """
        app.logger.info(f"Executing spell count query")
        count_start = time.time()
        try:
            cursor.execute(count_query, query_params)
            count_time = (time.time() - count_start) * 1000
            app.logger.info(f"Spell count query completed in {count_time:.2f}ms")
            result = cursor.fetchone()
            total_count = result['total_count'] if isinstance(result, dict) else result[0]
            app.logger.info(f"Found {total_count} spells matching criteria")
        except Exception as e:
            app.logger.error(f"Count query failed: {e}")
            # If count fails, just set a high number and continue
            total_count = 9999
        
        # Determine sorting column - use specific class if filtered, otherwise minimum level
        if class_field_for_sorting:
            sort_column = f"CASE WHEN {class_field_for_sorting} = 255 THEN 999 ELSE {class_field_for_sorting} END"
        else:
            sort_column = """LEAST(
                CASE WHEN classes1 = 255 THEN 999 ELSE classes1 END,
                CASE WHEN classes2 = 255 THEN 999 ELSE classes2 END,
                CASE WHEN classes3 = 255 THEN 999 ELSE classes3 END,
                CASE WHEN classes4 = 255 THEN 999 ELSE classes4 END,
                CASE WHEN classes5 = 255 THEN 999 ELSE classes5 END,
                CASE WHEN classes6 = 255 THEN 999 ELSE classes6 END,
                CASE WHEN classes7 = 255 THEN 999 ELSE classes7 END,
                CASE WHEN classes8 = 255 THEN 999 ELSE classes8 END,
                CASE WHEN classes9 = 255 THEN 999 ELSE classes9 END,
                CASE WHEN classes10 = 255 THEN 999 ELSE classes10 END,
                CASE WHEN classes11 = 255 THEN 999 ELSE classes11 END,
                CASE WHEN classes12 = 255 THEN 999 ELSE classes12 END,
                CASE WHEN classes13 = 255 THEN 999 ELSE classes13 END,
                CASE WHEN classes14 = 255 THEN 999 ELSE classes14 END,
                CASE WHEN classes15 = 255 THEN 999 ELSE classes15 END,
                CASE WHEN classes16 = 255 THEN 999 ELSE classes16 END
            )"""
        
        # Then get spells - reduce columns for better performance
        spells_query = f"""
            SELECT 
                id,
                name,
                mana,
                cast_time,
                `range`,
                targettype,
                skill,
                classes1, classes2, classes3, classes4, classes5, classes6,
                classes7, classes8, classes9, classes10, classes11, classes12,
                classes13, classes14, classes15, classes16,
                icon, new_icon,
                {sort_column} AS sort_level
            FROM spells_new
            WHERE {where_clause}
            ORDER BY sort_level ASC, name ASC
            LIMIT %s OFFSET %s
        """
        # Add limit and offset to params
        spells_params = query_params + [limit, offset]
        
        # Execute spell search query with timeout protection
        try:
            app.logger.info(f"Executing spell search query")
            start_time = time.time()
            cursor.execute(spells_query, spells_params)
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            app.logger.info(f"Spell search query completed in {query_time:.2f}ms")
        except Exception as e:
            app.logger.error(f"Database query failed: {e}")
            app.logger.error(f"Query: {spells_query}")
            app.logger.error(f"Params: {spells_params}")
            raise Exception("Database query failed - connection may have timed out")
            
        spells = cursor.fetchall()
        
        # Convert to response format with reduced columns
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
                    'resisttype': 0,  # Not retrieved for performance
                    'spell_category': 0,  # Not retrieved for performance
                    'buffduration': 0,  # Not retrieved for performance
                    'deities': 0,  # Not retrieved for performance
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
                    'effects': [0] * 12,  # Not retrieved for performance
                    'components': [0] * 4,  # Not retrieved for performance
                    'icon': _safe_int(spell['icon']),
                    'new_icon': _safe_int(spell['new_icon'])
                }
            else:
                # Handle tuple results
                idx = 0
                spell_dict = {
                    'spell_id': str(spell[idx]),
                    'name': spell[idx + 1],
                    'mana': _safe_int(spell[idx + 2]),
                    'cast_time': _safe_int(spell[idx + 3]),
                    'range': _safe_int(spell[idx + 4]),
                    'targettype': _safe_int(spell[idx + 5]),
                    'skill': _safe_int(spell[idx + 6]),
                    'resisttype': 0,  # Not retrieved for performance
                    'spell_category': 0,  # Not retrieved for performance
                    'buffduration': 0,  # Not retrieved for performance
                    'deities': 0,  # Not retrieved for performance
                    'class_levels': {
                        'warrior': _safe_int(spell[idx + 7]),
                        'cleric': _safe_int(spell[idx + 8]),
                        'paladin': _safe_int(spell[idx + 9]),
                        'ranger': _safe_int(spell[idx + 10]),
                        'shadowknight': _safe_int(spell[idx + 11]),
                        'druid': _safe_int(spell[idx + 12]),
                        'monk': _safe_int(spell[idx + 13]),
                        'bard': _safe_int(spell[idx + 14]),
                        'rogue': _safe_int(spell[idx + 15]),
                        'shaman': _safe_int(spell[idx + 16]),
                        'necromancer': _safe_int(spell[idx + 17]),
                        'wizard': _safe_int(spell[idx + 18]),
                        'magician': _safe_int(spell[idx + 19]),
                        'enchanter': _safe_int(spell[idx + 20]),
                        'beastlord': _safe_int(spell[idx + 21]),
                        'berserker': _safe_int(spell[idx + 22])
                    },
                    'effects': [0] * 12,  # Not retrieved for performance
                    'components': [0] * 4,  # Not retrieved for performance
                    'icon': _safe_int(spell[idx + 23]),
                    'new_icon': _safe_int(spell[idx + 24])
                }
            spells_list.append(spell_dict)
        
        # Log search event for monitoring
        try:
            # Gather user information including username when available
            user_info = {
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            
            # Try to get authenticated user information
            current_user = None
            try:
                from utils.jwt_utils import get_current_user
                current_user = get_current_user()
                if current_user:
                    user_info['user_id'] = current_user.get('id')
                    user_info['user_email'] = current_user.get('email')
                    
                    # Get full user details for display name
                    if current_user.get('id') and ENABLE_USER_ACCOUNTS:
                        try:
                            from models.user import User
                            from utils.oauth import get_oauth_db_connection
                            oauth_conn = get_oauth_db_connection()
                            if oauth_conn:
                                user_model = User(oauth_conn)
                                user_details = user_model.get_user_by_id(current_user['id'])
                                if user_details:
                                    # Use display_name if available, otherwise first_name + last_name
                                    display_name = user_details.get('display_name')
                                    if not display_name:
                                        first_name = user_details.get('first_name', '')
                                        last_name = user_details.get('last_name', '')
                                        if first_name or last_name:
                                            display_name = f"{first_name} {last_name}".strip()
                                    
                                    if display_name:
                                        user_info['username'] = display_name
                                    else:
                                        user_info['username'] = current_user.get('email', 'Unknown User')
                        except Exception as e:
                            # Don't let user lookup break logging
                            pass
            except Exception as e:
                # Don't let auth check break logging
                pass
            
            # Gather filter information (handle both dict and list formats)
            applied_filters = {}
            if isinstance(filters, dict):
                applied_filters = {k: v for k, v in filters.items() if v is not None and v != ''}
            elif isinstance(filters, list):
                # Convert list of filters to a dict representation
                applied_filters = {'filter_count': len(filters), 'filters': filters} if filters else {}
            
            # Log the search event (always log search events for monitoring)
            try:
                from routes.admin import log_search_event
                log_search_event(
                    search_type='spell',
                    query=search_query,
                    results_count=len(spells_list),
                    execution_time_ms=round(query_time, 2),
                    filters=applied_filters if applied_filters else None,
                    user_info=user_info
                )
            except Exception as log_error:
                app.logger.error(f"Failed to log spell search event: {log_error}")
        except Exception as e:
            # Don't let logging break the search
            app.logger.error(f"Error gathering search event data: {e}")
        
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


@app.route('/api/spells/<spell_id>/details', methods=['GET'])
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=120, requests_per_hour=1200)  # Higher limits for single spell lookup
def get_spell_details(spell_id):
    """
    Get detailed information for a specific spell by ID.
    Returns all available spell data from the spells_new table.
    """
    app.logger.info(f"=== SPELL DETAILS START for ID: {spell_id} ===")
    conn = None
    cursor = None
    
    try:
        # Validate spell_id
        try:
            spell_id_int = int(spell_id)
        except ValueError:
            return jsonify({'error': 'Invalid spell ID'}), 400
        
        # Get database connection
        app.logger.info("Getting database connection...")
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"No connection available: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        app.logger.info(f"Got connection, db_type: {db_type}")
        cursor = conn.cursor()
        
        # Query for detailed spell information
        spell_query = """
            SELECT 
                id,
                name,
                player_1,
                teleport_zone,
                you_cast,
                other_casts,
                cast_on_you,
                cast_on_other,
                spell_fades,
                `range`,
                aoerange,
                pushback,
                pushup,
                cast_time,
                recovery_time,
                recast_time,
                buffdurationformula,
                buffduration,
                AEDuration,
                mana,
                effect_base_value1, effect_base_value2, effect_base_value3, effect_base_value4,
                effect_base_value5, effect_base_value6, effect_base_value7, effect_base_value8,
                effect_base_value9, effect_base_value10, effect_base_value11, effect_base_value12,
                effect_limit_value1, effect_limit_value2, effect_limit_value3, effect_limit_value4,
                effect_limit_value5, effect_limit_value6, effect_limit_value7, effect_limit_value8,
                effect_limit_value9, effect_limit_value10, effect_limit_value11, effect_limit_value12,
                max1, max2, max3, max4, max5, max6, max7, max8, max9, max10, max11, max12,
                icon,
                new_icon,
                spell_icon,
                memicon,
                components1, components2, components3, components4,
                component_counts1, component_counts2, component_counts3, component_counts4,
                NoexpendReagent1, NoexpendReagent2, NoexpendReagent3, NoexpendReagent4,
                formula1, formula2, formula3, formula4, formula5, formula6,
                formula7, formula8, formula9, formula10, formula11, formula12,
                LightType,
                goodEffect,
                Activated,
                resisttype,
                effectid1, effectid2, effectid3, effectid4, effectid5, effectid6,
                effectid7, effectid8, effectid9, effectid10, effectid11, effectid12,
                targettype,
                basediff,
                skill,
                zonetype,
                EnvironmentType,
                TimeOfDay,
                classes1, classes2, classes3, classes4, classes5, classes6,
                classes7, classes8, classes9, classes10, classes11, classes12,
                classes13, classes14, classes15, classes16,
                CastingAnim,
                TargetAnim,
                TravelType,
                SpellAffectIndex,
                disallow_sit,
                deities,
                field142,
                field143,
                new_icon,
                spellanim,
                uninterruptable,
                ResistDiff,
                dot_stacking_exempt,
                deleteable,
                RecourseLink,
                no_partial_resist,
                field152,
                field153,
                short_buff_box,
                descnum,
                typedescnum,
                effectdescnum,
                effectdescnum2,
                npc_no_los,
                field160,
                reflectable,
                bonushate,
                field163,
                field164,
                ldon_trap,
                EndurCost,
                EndurTimerID,
                IsDiscipline,
                field169,
                field170,
                field171,
                HateAdded,
                EndurUpkeep,
                numhits,
                pvpresistbase,
                pvpresistcalc,
                pvpresistcap,
                spell_category,
                pvp_duration,
                pvp_duration_cap,
                pcnpc_only_flag,
                cast_not_standing,
                can_mgb,
                nodispell,
                npc_category,
                npc_usefulness,
                MinResist,
                MaxResist,
                viral_targets,
                viral_timer,
                nimbuseffect,
                ConeStartAngle,
                ConeStopAngle,
                sneaking,
                not_extendable,
                field198,
                field199,
                suspendable,
                viral_range,
                songcap,
                field203,
                field204,
                no_block,
                field206,
                spellgroup,
                rank,
                field209,
                field210,
                CastRestriction,
                allowrest,
                InCombat,
                OutofCombat,
                field215,
                field216,
                field217,
                aemaxtargets,
                maxtargets,
                field220,
                field221,
                field222,
                field223,
                persistdeath,
                field225,
                field226,
                min_dist,
                min_dist_mod,
                max_dist,
                max_dist_mod,
                min_range,
                field232,
                field233,
                field234,
                field235,
                field236
            FROM spells_new
            WHERE id = %s
        """
        
        app.logger.info(f"Executing spell details query for ID: {spell_id_int}")
        cursor.execute(spell_query, (spell_id_int,))
        
        spell = cursor.fetchone()
        if not spell:
            return jsonify({'error': 'Spell not found'}), 404
        
        # Convert to dict if it's a tuple
        if isinstance(spell, dict):
            spell_dict = spell
        else:
            # Handle tuple results - map to expected field names
            fields = [
                'id', 'name', 'player_1', 'teleport_zone', 'you_cast', 'other_casts',
                'cast_on_you', 'cast_on_other', 'spell_fades', 'range', 'aoerange',
                'pushback', 'pushup', 'cast_time', 'recovery_time', 'recast_time',
                'buffdurationformula', 'buffduration', 'AEDuration', 'mana',
                'effect_base_value1', 'effect_base_value2', 'effect_base_value3', 'effect_base_value4',
                'effect_base_value5', 'effect_base_value6', 'effect_base_value7', 'effect_base_value8',
                'effect_base_value9', 'effect_base_value10', 'effect_base_value11', 'effect_base_value12',
                'effect_limit_value1', 'effect_limit_value2', 'effect_limit_value3', 'effect_limit_value4',
                'effect_limit_value5', 'effect_limit_value6', 'effect_limit_value7', 'effect_limit_value8',
                'effect_limit_value9', 'effect_limit_value10', 'effect_limit_value11', 'effect_limit_value12',
                'max1', 'max2', 'max3', 'max4', 'max5', 'max6', 'max7', 'max8', 'max9', 'max10', 'max11', 'max12',
                'icon', 'new_icon', 'spell_icon', 'memicon',
                'components1', 'components2', 'components3', 'components4',
                'component_counts1', 'component_counts2', 'component_counts3', 'component_counts4',
                'NoexpendReagent1', 'NoexpendReagent2', 'NoexpendReagent3', 'NoexpendReagent4',
                'formula1', 'formula2', 'formula3', 'formula4', 'formula5', 'formula6',
                'formula7', 'formula8', 'formula9', 'formula10', 'formula11', 'formula12',
                'LightType', 'goodEffect', 'Activated', 'resisttype',
                'effectid1', 'effectid2', 'effectid3', 'effectid4', 'effectid5', 'effectid6',
                'effectid7', 'effectid8', 'effectid9', 'effectid10', 'effectid11', 'effectid12',
                'targettype', 'basediff', 'skill', 'zonetype', 'EnvironmentType', 'TimeOfDay',
                'classes1', 'classes2', 'classes3', 'classes4', 'classes5', 'classes6',
                'classes7', 'classes8', 'classes9', 'classes10', 'classes11', 'classes12',
                'classes13', 'classes14', 'classes15', 'classes16'
            ] + ['field' + str(i) for i in range(142, 237)]  # Add remaining fields
            
            spell_dict = {field: spell[i] if i < len(spell) else None for i, field in enumerate(fields)}
        
        # Build detailed response
        detailed_spell = {
            'spell_id': str(spell_dict['id']),
            'name': spell_dict['name'],
            'mana': _safe_int(spell_dict['mana']),
            'cast_time': _safe_int(spell_dict['cast_time']),
            'recovery_time': _safe_int(spell_dict['recovery_time']),
            'recast_time': _safe_int(spell_dict['recast_time']),
            'range': _safe_int(spell_dict['range']),
            'aoerange': _safe_int(spell_dict['aoerange']),
            'buffduration': _safe_int(spell_dict['buffduration']),
            'targettype': _safe_int(spell_dict['targettype']),
            'skill': _safe_int(spell_dict['skill']),
            'resisttype': _safe_int(spell_dict['resisttype']),
            'spell_category': _safe_int(spell_dict.get('spell_category', 0)),
            'class_levels': {
                'warrior': _safe_int(spell_dict['classes1']),
                'cleric': _safe_int(spell_dict['classes2']),
                'paladin': _safe_int(spell_dict['classes3']),
                'ranger': _safe_int(spell_dict['classes4']),
                'shadowknight': _safe_int(spell_dict['classes5']),
                'druid': _safe_int(spell_dict['classes6']),
                'monk': _safe_int(spell_dict['classes7']),
                'bard': _safe_int(spell_dict['classes8']),
                'rogue': _safe_int(spell_dict['classes9']),
                'shaman': _safe_int(spell_dict['classes10']),
                'necromancer': _safe_int(spell_dict['classes11']),
                'wizard': _safe_int(spell_dict['classes12']),
                'magician': _safe_int(spell_dict['classes13']),
                'enchanter': _safe_int(spell_dict['classes14']),
                'beastlord': _safe_int(spell_dict['classes15']),
                'berserker': _safe_int(spell_dict['classes16'])
            },
            'effects': [
                _safe_int(spell_dict.get('effectid1', 0)),
                _safe_int(spell_dict.get('effectid2', 0)),
                _safe_int(spell_dict.get('effectid3', 0)),
                _safe_int(spell_dict.get('effectid4', 0)),
                _safe_int(spell_dict.get('effectid5', 0)),
                _safe_int(spell_dict.get('effectid6', 0)),
                _safe_int(spell_dict.get('effectid7', 0)),
                _safe_int(spell_dict.get('effectid8', 0)),
                _safe_int(spell_dict.get('effectid9', 0)),
                _safe_int(spell_dict.get('effectid10', 0)),
                _safe_int(spell_dict.get('effectid11', 0)),
                _safe_int(spell_dict.get('effectid12', 0))
            ],
            'components': [
                _safe_int(spell_dict.get('components1', 0)),
                _safe_int(spell_dict.get('components2', 0)),
                _safe_int(spell_dict.get('components3', 0)),
                _safe_int(spell_dict.get('components4', 0))
            ],
            'icon': _safe_int(spell_dict['icon']),
            'new_icon': _safe_int(spell_dict['new_icon']),
            'spell_icon': _safe_int(spell_dict.get('spell_icon', 0)),
            'you_cast': spell_dict.get('you_cast', ''),
            'other_casts': spell_dict.get('other_casts', ''),
            'cast_on_you': spell_dict.get('cast_on_you', ''),
            'cast_on_other': spell_dict.get('cast_on_other', ''),
            'spell_fades': spell_dict.get('spell_fades', ''),
            'pushback': _safe_int(spell_dict.get('pushback', 0)),
            'pushup': _safe_int(spell_dict.get('pushup', 0)),
            'goodEffect': _safe_int(spell_dict.get('goodEffect', 0)),
            'deities': _safe_int(spell_dict.get('deities', 0))
        }
        
        app.logger.info(f"Spell details retrieved successfully for ID: {spell_id_int}")
        
        return jsonify(detailed_spell)
        
    except Exception as e:
        app.logger.error(f"Error getting spell details: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to get spell details: {str(e)}'}), 500
        
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


def load_cache_from_storage():
    """DISABLED - spell system disabled"""
    logger.info("Cache loading disabled - spell system disabled")
    pass




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

def clear_expired_cache():
    """DISABLED - spell system disabled"""
    logger.info("Cache clearing disabled - spell system disabled")
    pass


















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

# Configure connection pooling limits to prevent resource exhaustion
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,  # Limit number of connection pools
    pool_maxsize=20,      # Limit connections per pool
    pool_block=False      # Don't block when pool is full, create new connection
)

# Apply to both HTTP and HTTPS
session.mount("http://", adapter)
session.mount("https://", adapter)

# Set reasonable timeouts for all requests
session.timeout = (5, 30)  # (connect timeout, read timeout)

# Pricing cache is already declared at the top with other global storage variables



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



def update_startup_progress(step_name, step_number):
    """Update server startup progress"""
    global server_startup_progress
    
    server_startup_progress['current_step'] = step_name
    server_startup_progress['steps_completed'] = step_number
    server_startup_progress['progress_percent'] = int((step_number / server_startup_progress['total_steps']) * 100)
    
    logger.info(f"📈 Startup Progress: {server_startup_progress['progress_percent']}% - {step_name}")







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
                'connect_timeout': 10,   # 10 second connection timeout
                'read_timeout': 60,      # 60 second read timeout for spell searches
                'write_timeout': 30,     # 30 second write timeout
                'autocommit': True       # Enable autocommit to avoid transaction hangs
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
    logger.info(f"[MAIN BLOCK] ENABLE_DEV_AUTH = {os.environ.get('ENABLE_DEV_AUTH', 'NOT SET')}")
    if os.environ.get('ENABLE_DEV_AUTH') == 'true' or os.environ.get('TESTING') == '1':
        if os.environ.get('TESTING') == '1':
            logger.info("⚡ Testing mode: Skipping database initialization for fast startup")
        else:
            logger.info("⚡ Dev mode: Skipping database initialization for fast startup")
        logger.info("⚡ Databases will be initialized on first request")
    else:
        initialize_database_connection()  # Auth database
        
        # Initialize content database only if configured
        if config.get('production_database_url') or os.environ.get('EQEMU_DATABASE_URL'):
            try:
                from utils.content_db_manager import initialize_content_database
                logger.info("Initializing content database...")
                if initialize_content_database():
                    logger.info("✅ Content database initialized successfully")
                else:
                    logger.warning("⚠️ Content database initialization failed - will retry on first request")
            except Exception as e:
                logger.error(f"Error initializing content database: {e}")
        else:
            logger.info("⚠️ No content database configured - skipping initialization")
    
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
        'spell', 'cache', 'classes'
    ])
    
    # Log with appropriate level and context
    if is_spell_endpoint:
        logger.info(f"🚫 Disabled spell endpoint accessed: {method} {endpoint} (404 Not Found) | IP: {ip} | User-Agent: {user_agent[:100]}")
    else:
        logger.warning(f"❌ Failed endpoint attempt: {method} {endpoint} (404 Not Found) | IP: {ip} | User-Agent: {user_agent[:100]}")
    
    # Track endpoint failure metrics only if OAuth is enabled
    if ENABLE_USER_ACCOUNTS:
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
    
    # Track endpoint failure metrics with full error details only if OAuth is enabled
    if ENABLE_USER_ACCOUNTS:
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
    """Log all incoming requests and set request timeout"""
    # Store request start time for timeout handling
    g.request_start_time = time.time()
    
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
    """Log response information for failed requests and ensure connection cleanup"""
    # Check request duration
    if hasattr(g, 'request_start_time'):
        duration = time.time() - g.request_start_time
        if duration > 30:  # Log slow requests over 30 seconds
            logger.warning(f"⏱️ Slow request: {request.method} {request.path} took {duration:.2f}s")
    
    # Force connection cleanup for any lingering connections
    if hasattr(g, 'db_connection') and g.db_connection:
        try:
            g.db_connection.close()
            g.db_connection = None
        except:
            pass
    
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
    
    # Add connection close headers to prevent keep-alive issues
    response.headers['Connection'] = 'close'
    
    return response

if __name__ == '__main__':
    # Use threaded Flask server to prevent hanging with multiple requests
    # Add signal handlers for graceful shutdown
    import signal
    import atexit
    
    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        cleanup_resources()
        sys.exit(0)
    
    # Register signal handlers (skip on Windows as it can cause issues)
    if sys.platform != 'win32':
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup on exit (but avoid duplicate registration)
    # Note: Already registered above, so commenting out to prevent double registration
    # atexit.register(cleanup_resources)
    
    # Run Flask app with explicit threading configuration
    logger.info(f"Starting Flask server on port {config['backend_port']} with threading enabled")
    app.run(
        debug=True,  # Enable debug mode for proper module reloading
        host='0.0.0.0', 
        port=config['backend_port'],
        threaded=True,  # Enable threading to handle multiple requests
        use_reloader=True,  # Enable reloader for development
        processes=1  # Ensure single process with multiple threads
    ) 