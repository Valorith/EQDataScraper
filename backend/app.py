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
        'http://localhost:3001',
        'http://localhost:3002',
        'https://eqdatascraper-frontend-production.up.railway.app',
        'https://eqdatascraper-production.up.railway.app'
    ]
    
    
    # Add frontend URL from environment if set
    frontend_url = os.environ.get('FRONTEND_URL')
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    
    # Use permissive CORS for Railway production, strict for development
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'):
        print("🚀 Railway environment detected - using permissive CORS")
        cors_origins = '*'  # Allow all origins in Railway production
    else:
        # Use configured origins for development
        cors_origins = allowed_origins
    
    CORS(app, 
         origins=cors_origins, 
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
        
        # Register character management blueprints
        try:
            from routes.characters import character_bp
            app.register_blueprint(character_bp)
            app.logger.info("✅ Character routes registered")
        except ImportError as e:
            app.logger.warning(f"⚠️ Could not load character routes: {e}")
        
        # Register item tooltip blueprints
        try:
            from routes.items import item_bp
            app.register_blueprint(item_bp)
            app.logger.info("✅ Item tooltip routes registered")
        except ImportError as e:
            app.logger.warning(f"⚠️ Could not load item routes: {e}")
        
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
    
    # Register character management routes even when OAuth is disabled
    try:
        from routes.characters import character_bp
        app.register_blueprint(character_bp)
        app.logger.info("✅ Character routes registered (OAuth disabled)")
    except ImportError as e:
        app.logger.warning(f"⚠️ Could not load character routes: {e}")

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

@app.route('/api/database/manager/status', methods=['GET'])
@exempt_when_limiting
def get_database_manager_status():
    """Get database manager monitoring status - non-blocking and safe."""
    try:
        # Debug: Log that we're trying to get status
        app.logger.info("Database manager status endpoint called")
        
        from utils.database_manager import get_database_manager
        app.logger.info("Successfully imported get_database_manager")
        
        # Get manager instance without creating new connections
        manager = get_database_manager()
        app.logger.info(f"Got manager instance: {type(manager)}")
        
        # This call is fast and non-blocking - just returns cached status
        status = manager.get_monitoring_status()
        app.logger.info("Successfully got monitoring status")
        
        # Add basic server info
        status['server_timestamp'] = datetime.now().isoformat()
        status['success'] = True
        
        return jsonify(status), 200
        
    except Exception as e:
        # Ensure we never crash or block on this endpoint
        app.logger.error(f"Error getting database manager status: {e}", exc_info=True)
        error_response = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'monitoring_active': False,
            'server_timestamp': datetime.now().isoformat()
        }
        return jsonify(error_response), 200  # Return 200 to not break the UI


@app.route('/api/database/manager/logs', methods=['GET'])
@exempt_when_limiting
def get_database_manager_logs():
    """Get database manager logs for debugging purposes."""
    try:
        app.logger.info("Database manager logs endpoint called")
        from utils.database_manager import get_database_manager
        
        # Get limit parameter from query string
        limit = request.args.get('limit', type=int, default=25)
        
        # Get manager instance
        manager = get_database_manager()
        
        # Debug: Log current manager state
        app.logger.info(f"Database Manager logs request - Manager state: running={manager.is_running()}, "
                       f"inactive={manager._inactive_due_to_failures}, environment={manager._environment}, "
                       f"logs_count={len(manager._logs)}")
        
        # Get logs (this is fast and thread-safe)
        logs = manager.get_logs(limit=limit)
        
        # If no logs exist, force some debug entries to help identify the issue
        if not logs:
            app.logger.warning("No logs found in Database Manager - forcing debug entries")
            manager._add_log('debug', 'Logs endpoint called - no existing logs found')
            manager._add_log('info', f'Manager state: running={manager.is_running()}, environment={manager._environment}')
            manager._add_log('debug', f'Manager details: start_time={manager._start_time}, check_count={manager._check_count}')
            
            # Get logs again after adding debug entries
            logs = manager.get_logs(limit=limit)
        
        # Enhanced response with debugging information
        response_data = {
            'success': True,
            'logs': logs,
            'total_entries': len(logs),
            'limit': limit,
            'manager_debug': {
                'is_running': manager.is_running(),
                'inactive_due_to_failures': manager._inactive_due_to_failures,
                'environment': manager._environment,
                'start_time': manager._start_time.isoformat() if manager._start_time else None,
                'check_count': manager._check_count,
                'consecutive_failures': manager._consecutive_failures,
                'logs_buffer_size': len(manager._logs)
            },
            'server_timestamp': datetime.now().isoformat()
        }
        
        app.logger.info(f"Returning {len(logs)} log entries to client")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        app.logger.error(f"Error getting database manager logs: {e}")
        return jsonify({'error': 'Failed to get database manager logs', 'details': str(e)}), 500


@app.route('/api/database/manager/restart', methods=['POST'])
@exempt_when_limiting
def restart_database_manager_endpoint():
    """Restart database manager monitoring."""
    try:
        app.logger.info("Database manager restart endpoint called")
        from utils.database_manager import restart_database_manager, get_database_manager
        
        # Get current manager state for debugging
        manager = get_database_manager()
        current_state = {
            'running': manager.is_running(),
            'inactive_due_to_failures': manager._inactive_due_to_failures,
            'environment': manager._environment,
            'logs_count': len(manager._logs)
        }
        
        app.logger.info(f"Restart request - current state: {current_state}")
        
        # Get force parameter from request body
        force = False
        if request.is_json and request.get_json():
            force = request.get_json().get('force', False)
        
        # Add log entry to manager before restart attempt
        manager._add_log('info', f'Restart requested via API endpoint', {
            'force': force,
            'current_running': manager.is_running(),
            'current_inactive': manager._inactive_due_to_failures
        })
        
        # Restart the manager
        success = restart_database_manager(force=force)
        
        # Get new state after restart attempt
        new_state = {
            'running': manager.is_running(),
            'inactive_due_to_failures': manager._inactive_due_to_failures,
            'logs_count': len(manager._logs)
        }
        
        # Add result log entry to manager
        manager._add_log('info' if success else 'error', 
                        f'Restart {"successful" if success else "failed"}', {
            'success': success,
            'new_running': manager.is_running(),
            'new_inactive': manager._inactive_due_to_failures
        })
        
        app.logger.info(f"Restart result - success: {success}, new state: {new_state}")
        
        return jsonify({
            'success': success,
            'message': 'Database manager restarted successfully' if success else 'Failed to restart database manager',
            'debug_info': {
                'before_state': current_state,
                'after_state': new_state,
                'force': force
            },
            'server_timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error restarting database manager: {e}", exc_info=True)
        return jsonify({'error': 'Failed to restart database manager', 'details': str(e)}), 500


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
        
        # Query for detailed spell information - simplified to use common fields
        spell_query = """
            SELECT 
                id,
                name,
                mana,
                cast_time,
                `range`,
                targettype,
                buffduration,
                skill,
                resisttype,
                effect_base_value1, effect_base_value2, effect_base_value3, effect_base_value4,
                effect_base_value5, effect_base_value6, effect_base_value7, effect_base_value8,
                effect_base_value9, effect_base_value10, effect_base_value11, effect_base_value12,
                effect_limit_value1, effect_limit_value2, effect_limit_value3, effect_limit_value4,
                effect_limit_value5, effect_limit_value6, effect_limit_value7, effect_limit_value8,
                effect_limit_value9, effect_limit_value10, effect_limit_value11, effect_limit_value12,
                max1, max2, max3, max4, max5, max6, max7, max8, max9, max10, max11, max12,
                effectid1, effectid2, effectid3, effectid4, effectid5, effectid6,
                effectid7, effectid8, effectid9, effectid10, effectid11, effectid12,
                formula1, formula2, formula3, formula4, formula5, formula6,
                formula7, formula8, formula9, formula10, formula11, formula12,
                classes1, classes2, classes3, classes4, classes5, classes6,
                classes7, classes8, classes9, classes10, classes11, classes12,
                classes13, classes14, classes15, classes16,
                components1, components2, components3, components4,
                icon,
                new_icon
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
            # Handle tuple results - map to expected field names (simplified)
            fields = [
                'id', 'name', 'mana', 'cast_time', 'range', 'targettype', 'buffduration', 'skill', 'resisttype',
                'effect_base_value1', 'effect_base_value2', 'effect_base_value3', 'effect_base_value4',
                'effect_base_value5', 'effect_base_value6', 'effect_base_value7', 'effect_base_value8',
                'effect_base_value9', 'effect_base_value10', 'effect_base_value11', 'effect_base_value12',
                'effect_limit_value1', 'effect_limit_value2', 'effect_limit_value3', 'effect_limit_value4',
                'effect_limit_value5', 'effect_limit_value6', 'effect_limit_value7', 'effect_limit_value8',
                'effect_limit_value9', 'effect_limit_value10', 'effect_limit_value11', 'effect_limit_value12',
                'max1', 'max2', 'max3', 'max4', 'max5', 'max6', 'max7', 'max8', 'max9', 'max10', 'max11', 'max12',
                'effectid1', 'effectid2', 'effectid3', 'effectid4', 'effectid5', 'effectid6',
                'effectid7', 'effectid8', 'effectid9', 'effectid10', 'effectid11', 'effectid12',
                'formula1', 'formula2', 'formula3', 'formula4', 'formula5', 'formula6',
                'formula7', 'formula8', 'formula9', 'formula10', 'formula11', 'formula12',
                'classes1', 'classes2', 'classes3', 'classes4', 'classes5', 'classes6',
                'classes7', 'classes8', 'classes9', 'classes10', 'classes11', 'classes12',
                'classes13', 'classes14', 'classes15', 'classes16',
                'components1', 'components2', 'components3', 'components4',
                'icon', 'new_icon'
            ]
            
            spell_dict = {field: spell[i] if i < len(spell) else None for i, field in enumerate(fields)}
        
        # Build detailed response
        detailed_spell = {
            'spell_id': str(spell_dict['id']),
            'name': spell_dict['name'],
            'mana': _safe_int(spell_dict['mana']),
            'cast_time': _safe_int(spell_dict['cast_time']),
            'range': _safe_int(spell_dict['range']),
            'buffduration': _safe_int(spell_dict['buffduration']),
            'targettype': _safe_int(spell_dict['targettype']),
            'skill': _safe_int(spell_dict['skill']),
            'resisttype': _safe_int(spell_dict['resisttype']),
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
                {
                    'id': _safe_int(spell_dict.get('effectid1', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value1', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value1', 0)),
                    'max_value': _safe_int(spell_dict.get('max1', 0)),
                    'formula': _safe_int(spell_dict.get('formula1', 0))
                } if _safe_int(spell_dict.get('effectid1', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid2', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value2', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value2', 0)),
                    'max_value': _safe_int(spell_dict.get('max2', 0)),
                    'formula': _safe_int(spell_dict.get('formula2', 0))
                } if _safe_int(spell_dict.get('effectid2', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid3', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value3', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value3', 0)),
                    'max_value': _safe_int(spell_dict.get('max3', 0)),
                    'formula': _safe_int(spell_dict.get('formula3', 0))
                } if _safe_int(spell_dict.get('effectid3', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid4', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value4', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value4', 0)),
                    'max_value': _safe_int(spell_dict.get('max4', 0)),
                    'formula': _safe_int(spell_dict.get('formula4', 0))
                } if _safe_int(spell_dict.get('effectid4', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid5', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value5', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value5', 0)),
                    'max_value': _safe_int(spell_dict.get('max5', 0)),
                    'formula': _safe_int(spell_dict.get('formula5', 0))
                } if _safe_int(spell_dict.get('effectid5', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid6', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value6', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value6', 0)),
                    'max_value': _safe_int(spell_dict.get('max6', 0)),
                    'formula': _safe_int(spell_dict.get('formula6', 0))
                } if _safe_int(spell_dict.get('effectid6', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid7', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value7', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value7', 0)),
                    'max_value': _safe_int(spell_dict.get('max7', 0)),
                    'formula': _safe_int(spell_dict.get('formula7', 0))
                } if _safe_int(spell_dict.get('effectid7', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid8', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value8', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value8', 0)),
                    'max_value': _safe_int(spell_dict.get('max8', 0)),
                    'formula': _safe_int(spell_dict.get('formula8', 0))
                } if _safe_int(spell_dict.get('effectid8', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid9', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value9', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value9', 0)),
                    'max_value': _safe_int(spell_dict.get('max9', 0)),
                    'formula': _safe_int(spell_dict.get('formula9', 0))
                } if _safe_int(spell_dict.get('effectid9', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid10', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value10', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value10', 0)),
                    'max_value': _safe_int(spell_dict.get('max10', 0)),
                    'formula': _safe_int(spell_dict.get('formula10', 0))
                } if _safe_int(spell_dict.get('effectid10', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid11', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value11', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value11', 0)),
                    'max_value': _safe_int(spell_dict.get('max11', 0)),
                    'formula': _safe_int(spell_dict.get('formula11', 0))
                } if _safe_int(spell_dict.get('effectid11', 0)) != 0 else None,
                {
                    'id': _safe_int(spell_dict.get('effectid12', 0)),
                    'base_value': _safe_int(spell_dict.get('effect_base_value12', 0)),
                    'limit_value': _safe_int(spell_dict.get('effect_limit_value12', 0)),
                    'max_value': _safe_int(spell_dict.get('max12', 0)),
                    'formula': _safe_int(spell_dict.get('formula12', 0))
                } if _safe_int(spell_dict.get('effectid12', 0)) != 0 else None
            ],
            'components': [
                _safe_int(spell_dict.get('components1', 0)),
                _safe_int(spell_dict.get('components2', 0)),
                _safe_int(spell_dict.get('components3', 0)),
                _safe_int(spell_dict.get('components4', 0))
            ],
            'icon': _safe_int(spell_dict['icon']),
            'new_icon': _safe_int(spell_dict['new_icon'])
        }
        
        # Filter out None effects and keep only valid effect IDs with meaningful values
        detailed_spell['effects'] = [effect for effect in detailed_spell['effects'] 
                                    if effect is not None 
                                    and effect['id'] not in (0, 254)  # Exclude blank effects
                                    and effect['base_value'] != 0]    # Only show effects with values
        
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


@app.route('/api/spells/<spell_id>/items', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_items_with_spell(spell_id):
    """
    Get discovered items that contain the specified spell as a scroll effect, click effect, proc effect, 
    worn effect, focus effect, or bard effect.
    Only returns items that exist in both items and discovered_items tables.
    """
    try:
        spell_id_int = int(spell_id)
        app.logger.info(f"Getting items with spell ID: {spell_id_int}")
        
        # Get database connection
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # Check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'items'")
            if not cursor.fetchone():
                app.logger.warning("Items table not available in this database")
                return jsonify({'items': [], 'message': 'Item data not available in this database'})
            
            cursor.execute("SHOW TABLES LIKE 'discovered_items'")
            if not cursor.fetchone():
                app.logger.warning("Discovered_items table not available in this database")
                return jsonify({'items': [], 'message': 'Discovered items data not available in this database'})
            
            # Query for discovered items that have this spell in any spell effect field
            # Only include items that exist in both items and discovered_items tables
            query = """
                SELECT DISTINCT
                    items.id,
                    items.name,
                    items.icon,
                    items.scrolleffect,
                    items.clickeffect,
                    items.proceffect,
                    items.worneffect,
                    items.focuseffect,
                    items.bardeffect
                FROM items
                INNER JOIN discovered_items di ON items.id = di.item_id
                WHERE items.scrolleffect = %s
                   OR items.clickeffect = %s
                   OR items.proceffect = %s
                   OR items.worneffect = %s
                   OR items.focuseffect = %s
                   OR items.bardeffect = %s
                ORDER BY items.name ASC
                LIMIT 1000
            """
            
            cursor.execute(query, (spell_id_int, spell_id_int, spell_id_int, spell_id_int, spell_id_int, spell_id_int))
            results = cursor.fetchall()
            app.logger.debug(f"Discovered items with spell {spell_id_int} query returned {len(results)} results")
            
            if not results:
                return jsonify({'items': [], 'total_count': 0})
            
            # Format results
            items = []
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    item_id, name, icon, scrolleffect, clickeffect, proceffect, worneffect, focuseffect, bardeffect = (
                        row['id'], row['name'], row['icon'], row['scrolleffect'], 
                        row['clickeffect'], row['proceffect'], row['worneffect'], 
                        row['focuseffect'], row['bardeffect']
                    )
                else:
                    # Tuple format
                    item_id, name, icon, scrolleffect, clickeffect, proceffect, worneffect, focuseffect, bardeffect = row
                
                # Determine which effect type(s) match
                effect_types = []
                if scrolleffect == spell_id_int:
                    effect_types.append('scroll')
                if clickeffect == spell_id_int:
                    effect_types.append('click')
                if proceffect == spell_id_int:
                    effect_types.append('proc')
                if worneffect == spell_id_int:
                    effect_types.append('worn')
                if focuseffect == spell_id_int:
                    effect_types.append('focus')
                if bardeffect == spell_id_int:
                    effect_types.append('bard')
                
                items.append({
                    'id': item_id,
                    'name': name.replace('_', ' ') if name else 'Unknown Item',
                    'icon': icon or 0,
                    'effect_types': effect_types
                })
            
            app.logger.info(f"Found {len(items)} discovered items with spell ID: {spell_id_int}")
            
            return jsonify({
                'items': items,
                'total_count': len(items),
                'spell_id': spell_id_int
            })
            
        except Exception as e:
            app.logger.error(f"Error querying items with spell: {e}")
            import traceback
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Failed to query items with spell: {str(e)}'}), 500
            
        finally:
            cursor.close()
            
    except ValueError:
        app.logger.error(f"Invalid spell ID: {spell_id}")
        return jsonify({'error': 'Invalid spell ID'}), 400
    except Exception as e:
        app.logger.error(f"Error getting items with spell: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to get items with spell: {str(e)}'}), 500
        
    finally:
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


# Initialize the database manager for production (Gunicorn/Railway) deployment
# This runs at module level so it works with WSGI servers like Gunicorn
try:
    logger.info("🔄 Starting Database Manager initialization...")
    from utils.database_manager import initialize_database_manager
    logger.info("✅ Successfully imported initialize_database_manager")
    initialize_database_manager(delay_start=5.0)  # Start monitoring after 5 seconds
    logger.info("✅ Database manager initialized with 30-second monitoring (module level)")
except Exception as e:
    logger.error(f"❌ Failed to initialize database manager: {e}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")



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

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get EverQuest classes list - DISABLED"""
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
                    cursor = None
                    try:
                        # Verify connection works with a simple test query
                        cursor = conn.cursor()
                        
                        # Use a simpler test query that should always work
                        if db_type == 'mysql':
                            cursor.execute("SELECT 1 as test")
                        elif db_type == 'postgresql':
                            cursor.execute("SELECT 1 as test")
                        elif db_type == 'mssql':
                            cursor.execute("SELECT 1 as test")
                        else:
                            # Fallback for unknown database types
                            cursor.execute("SELECT 1")
                        
                        result = cursor.fetchone()
                        if result:
                            logger.info(f"✅ Database connection test successful! Type: {db_type}")
                            
                            # Now try to get version info (optional)
                            try:
                                if db_type == 'mysql':
                                    cursor.execute("SELECT VERSION()")
                                elif db_type == 'postgresql':
                                    cursor.execute("SELECT version()")
                                elif db_type == 'mssql':
                                    cursor.execute("SELECT @@VERSION")
                                    
                                version_result = cursor.fetchone()
                                version = version_result[0] if version_result else "Unknown"
                                logger.info(f"Database version: {version.split()[0] if version != 'Unknown' else 'Unknown'}")
                            except Exception as version_error:
                                logger.warning(f"Could not get database version: {version_error}")
                                
                            cursor.close()
                            conn.close()
                            return True
                        else:
                            raise Exception("Test query returned no result")
                            
                    except Exception as e:
                        logger.error(f"❌ Database connection test failed: {type(e).__name__}: {e}")
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


@app.route('/api/items/<item_id>/drop-sources', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_drop_sources(item_id):
    """
    Get NPCs and zones where an item is dropped.
    Optimized version of the legacy PHP query with proper JOINs and indexing.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'lootdrop_entries'")
            if not cursor.fetchone():
                app.logger.warning("Loot tables not available in this database")
                return jsonify({'zones': [], 'message': 'Drop source data not available in this database'})
            
            # Pre-check removed - availability endpoint now uses same filtering logic
            # Optimized query using explicit JOINs and proper indexing
            # Use standard EQEmu table names
            query = """
                SELECT DISTINCT
                    nt.id as npc_id,
                    nt.name as npc_name,
                    s2.zone,
                    z.long_name as zone_name,
                    lte.multiplier,
                    lte.probability,
                    lde.chance
                FROM npc_types nt
                INNER JOIN spawnentry se ON nt.id = se.npcID
                INNER JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
                INNER JOIN zone z ON s2.zone = z.short_name
                INNER JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
                INNER JOIN lootdrop_entries lde ON lte.lootdrop_id = lde.lootdrop_id
                LEFT JOIN spawn2_disabled s2d ON s2.id = s2d.spawn2_id
                WHERE lde.item_id = %s
                  AND z.min_status = 0
                  AND s2d.spawn2_id IS NULL
                  AND nt.merchant_id = 0
                  AND z.short_name NOT IN ('load', 'arena', 'nexus', 'arttest', 'ssratemple', 'tutorial')
                ORDER BY z.long_name, nt.name
                LIMIT 1000
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'zones': []})
            
            # Organize results by zone
            zones_data = {}
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    npc_id, npc_name, zone_short, zone_name, multiplier, probability, chance = (
                        row['npc_id'], row['npc_name'], row['zone'], row['zone_name'],
                        row['multiplier'], row['probability'], row['chance']
                    )
                else:
                    # Tuple format: npc_id, npc_name, zone, zone_name, multiplier, probability, chance
                    npc_id, npc_name, zone_short, zone_name, multiplier, probability, chance = row
                
                if zone_short not in zones_data:
                    zones_data[zone_short] = {
                        'zone_short': zone_short,
                        'zone_name': zone_name,
                        'npcs': []
                    }
                
                # Calculate drop chance (chance * probability / 100)
                drop_chance = round((chance * probability / 100), 2)
                
                zones_data[zone_short]['npcs'].append({
                    'npc_id': npc_id,
                    'npc_name': npc_name.replace('_', ' '),
                    'chance': chance,
                    'probability': probability,
                    'multiplier': multiplier,
                    'drop_chance': drop_chance
                })
            
            # Convert to list and sort by zone name
            zones_list = list(zones_data.values())
            zones_list.sort(key=lambda x: x['zone_name'])
            
            return jsonify({'zones': zones_list})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item drop sources for item {item_id}: {e}")
        return jsonify({'error': f'Failed to get drop sources: {str(e)}'}), 500


def calculate_merchant_price(base_price, sellrate, npc_class):
    """
    Calculate the actual price a merchant sells an item for.
    
    EverQuest pricing logic:
    - base_price: Item's base price in copper
    - sellrate: Merchant's pricing modifier (default 100 = 100%)
    - npc_class: Different classes may have different pricing rules
    
    Returns price in copper
    """
    if not base_price or base_price <= 0:
        return 0
    
    # Default sellrate if not set
    if not sellrate or sellrate <= 0:
        sellrate = 100
    
    # Calculate final price: (base_price * sellrate) / 100
    final_price = int((base_price * sellrate) / 100)
    
    # Ensure minimum price of 1 copper for sellable items
    return max(1, final_price)


def convert_copper_to_coins(copper_amount):
    """
    Convert copper amount to platinum, gold, silver, bronze coins.
    EverQuest currency: 1000 copper = 100 silver = 10 gold = 1 platinum
    """
    if not copper_amount or copper_amount <= 0:
        return {'platinum': 0, 'gold': 0, 'silver': 0, 'bronze': 0}
    
    platinum = copper_amount // 1000
    remaining = copper_amount % 1000
    
    gold = remaining // 100
    remaining = remaining % 100
    
    silver = remaining // 10
    bronze = remaining % 10
    
    return {
        'platinum': platinum,
        'gold': gold,
        'silver': silver,
        'bronze': bronze
    }


@app.route('/api/items/<item_id>/merchant-sources', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_merchant_sources(item_id):
    """
    Get NPCs and zones where an item is sold by merchants.
    Optimized version of the legacy PHP query with proper JOINs and pricing info.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'merchantlist'")
            if not cursor.fetchone():
                app.logger.warning("Merchant tables not available in this database")
                return jsonify({'zones': [], 'message': 'Merchant data not available in this database'})
            
            # Check if item is sold anywhere (optimized pre-check)
            cursor.execute("""
                SELECT 1 FROM merchantlist 
                WHERE item = %s LIMIT 1
            """, (item_id,))
            
            if not cursor.fetchone():
                return jsonify({'zones': []})
            
            # Optimized query using explicit JOINs and proper indexing
            # Include pricing information for shopkeepers and LDON merchants
            # Note: sellrate might not exist in all EQEmu schemas, so we'll use a default
            query = """
                SELECT DISTINCT
                    nt.id as npc_id,
                    nt.name as npc_name,
                    nt.class as npc_class,
                    s2.zone,
                    z.long_name as zone_name,
                    ml.slot as merchant_slot,
                    i.price as item_base_price,
                    100 as merchant_sellrate
                FROM npc_types nt
                INNER JOIN merchantlist ml ON nt.merchant_id = ml.merchantid
                INNER JOIN spawnentry se ON nt.id = se.npcID
                INNER JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
                INNER JOIN zone z ON s2.zone = z.short_name
                INNER JOIN items i ON ml.item = i.id
                LEFT JOIN spawn2_disabled s2d ON s2.id = s2d.spawn2_id
                WHERE ml.item = %s
                  AND z.min_status = 0
                  AND s2d.spawn2_id IS NULL
                  AND z.short_name NOT IN ('load', 'arena', 'nexus', 'arttest', 'ssratemple', 'tutorial')
                ORDER BY z.long_name, nt.name
                LIMIT 1000
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'zones': []})
            
            # Organize results by zone
            zones_data = {}
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    npc_id, npc_name, npc_class, zone_short, zone_name, merchant_slot, item_base_price, merchant_sellrate = (
                        row['npc_id'], row['npc_name'], row['npc_class'], row['zone'], 
                        row['zone_name'], row['merchant_slot'], row['item_base_price'], row['merchant_sellrate']
                    )
                else:
                    # Tuple format: npc_id, npc_name, npc_class, zone, zone_name, merchant_slot, item_base_price, merchant_sellrate
                    npc_id, npc_name, npc_class, zone_short, zone_name, merchant_slot, item_base_price, merchant_sellrate = row
                
                if zone_short not in zones_data:
                    zones_data[zone_short] = {
                        'zone_short': zone_short,
                        'zone_name': zone_name,
                        'merchants': []
                    }
                
                # Calculate actual selling price
                actual_price = calculate_merchant_price(item_base_price, merchant_sellrate, npc_class)
                
                # Convert to coin breakdown
                coins = convert_copper_to_coins(actual_price)
                
                # Determine merchant type and pricing info
                merchant_type = 'merchant'
                pricing_info = None
                
                if npc_class == 41:  # Shopkeeper
                    merchant_type = 'shopkeeper'
                    pricing_info = 'Sold for coins'
                elif npc_class == 61:  # LDON merchant
                    merchant_type = 'ldon_merchant'
                    pricing_info = 'Sold for adventure points'
                else:
                    pricing_info = 'Sold for coins'
                
                zones_data[zone_short]['merchants'].append({
                    'npc_id': npc_id,
                    'npc_name': npc_name.replace('_', ' '),
                    'npc_class': npc_class,
                    'merchant_type': merchant_type,
                    'pricing_info': pricing_info,
                    'merchant_slot': merchant_slot,
                    'price_copper': actual_price,
                    'price_coins': coins,
                    'base_price': item_base_price,
                    'sellrate': merchant_sellrate
                })
            
            # Convert to list and sort by zone name
            zones_list = list(zones_data.values())
            zones_list.sort(key=lambda x: x['zone_name'])
            
            return jsonify({'zones': zones_list})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item merchant sources for item {item_id}: {e}")
        return jsonify({'error': f'Failed to get merchant sources: {str(e)}'}), 500


@app.route('/api/items/<item_id>/ground-spawns', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_ground_spawns(item_id):
    """
    Get zones and coordinates where an item spawns on the ground.
    Optimized version of the legacy PHP query with proper JOINs.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'ground_spawns'")
            if not cursor.fetchone():
                app.logger.warning("Ground spawns table not available in this database")
                return jsonify({'zones': [], 'message': 'Ground spawn data not available in this database'})
            
            # Check if item has ground spawns (optimized pre-check) 
            cursor.execute("""
                SELECT 1 FROM ground_spawns 
                WHERE item = %s LIMIT 1
            """, (item_id,))
            
            if not cursor.fetchone():
                return jsonify({'zones': []})
            
            # Optimized query using explicit JOINs
            # Use basic coordinate fields that exist in EQEmu ground_spawns table
            query = """
                SELECT 
                    gs.id as spawn_id,
                    gs.max_x,
                    gs.max_y, 
                    gs.max_z,
                    gs.respawn_timer,
                    z.short_name as zone_short,
                    z.long_name as zone_name
                FROM ground_spawns gs
                INNER JOIN zone z ON gs.zoneid = z.zoneidnumber
                WHERE gs.item = %s
                  AND z.min_status = 0
                  AND z.short_name NOT IN ('load', 'arena', 'nexus', 'arttest', 'ssratemple', 'tutorial')
                ORDER BY z.long_name, gs.max_x, gs.max_y
                LIMIT 1000
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'zones': []})
            
            # Organize results by zone
            zones_data = {}
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    spawn_id, max_x, max_y, max_z, respawn_timer, zone_short, zone_name = (
                        row['spawn_id'], row['max_x'], row['max_y'], row['max_z'],
                        row['respawn_timer'], row['zone_short'], row['zone_name']
                    )
                else:
                    # Tuple format
                    spawn_id, max_x, max_y, max_z, respawn_timer, zone_short, zone_name = row
                
                if zone_short not in zones_data:
                    zones_data[zone_short] = {
                        'zone_short': zone_short,
                        'zone_name': zone_name,
                        'spawn_points': []
                    }
                
                # Format coordinates - simple X, Y, Z format
                coord_display = f"{max_x}, {max_y}, {max_z}"
                
                zones_data[zone_short]['spawn_points'].append({
                    'spawn_id': spawn_id,
                    'coordinates': coord_display,
                    'x': max_x,
                    'y': max_y,
                    'z': max_z,
                    'respawn_timer': respawn_timer
                })
            
            # Convert to list and sort by zone name
            zones_list = list(zones_data.values())
            zones_list.sort(key=lambda x: x['zone_name'])
            
            return jsonify({'zones': zones_list})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item ground spawns for item {item_id}: {e}")
        return jsonify({'error': f'Failed to get ground spawns: {str(e)}'}), 500


@app.route('/api/items/<item_id>/forage-sources', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_forage_sources(item_id):
    """
    Get zones where an item can be foraged.
    Optimized version of the legacy PHP query with proper JOINs.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'forage'")
            if not cursor.fetchone():
                app.logger.warning("Forage table not available in this database")
                return jsonify({'zones': [], 'message': 'Forage data not available in this database'})
            
            # Check if item can be foraged (optimized pre-check)
            cursor.execute("""
                SELECT 1 FROM forage 
                WHERE itemid = %s LIMIT 1
            """, (item_id,))
            
            if not cursor.fetchone():
                return jsonify({'zones': []})
            
            # Optimized query using explicit JOINs
            # Include chance and level information from the forage table
            query = """
                SELECT 
                    z.short_name as zone_short,
                    z.long_name as zone_name,
                    f.chance,
                    f.level
                FROM forage f
                INNER JOIN zone z ON f.zoneid = z.zoneidnumber
                WHERE f.itemid = %s
                  AND z.min_status = 0
                  AND z.short_name NOT IN ('load', 'arena', 'nexus', 'arttest', 'ssratemple', 'tutorial')
                GROUP BY z.zoneidnumber
                ORDER BY z.long_name
                LIMIT 1000
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'zones': []})
            
            # Organize results by zone
            zones_data = {}
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    zone_short, zone_name, chance, level = (
                        row['zone_short'], row['zone_name'], row['chance'], row['level']
                    )
                else:
                    # Tuple format
                    zone_short, zone_name, chance, level = row
                
                if zone_short not in zones_data:
                    zones_data[zone_short] = {
                        'zone_short': zone_short,
                        'zone_name': zone_name,
                        'forage_info': []
                    }
                
                zones_data[zone_short]['forage_info'].append({
                    'chance': chance,
                    'level': level
                })
            
            # Convert to list and sort by zone name
            zones_list = list(zones_data.values())
            zones_list.sort(key=lambda x: x['zone_name'])
            
            return jsonify({'zones': zones_list})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item forage sources for item {item_id}: {e}")
        return jsonify({'error': f'Failed to get forage sources: {str(e)}'}), 500


@app.route('/api/items/<item_id>/tradeskill-recipes', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_tradeskill_recipes(item_id):
    """
    Get tradeskill recipes that use this item as a component.
    Optimized version of the legacy PHP query with proper JOINs.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe'")
            if not cursor.fetchone():
                app.logger.warning("Tradeskill recipe tables not available in this database")
                return jsonify({'skills': [], 'message': 'Tradeskill recipe data not available in this database'})
            
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe_entries'")
            if not cursor.fetchone():
                app.logger.warning("Tradeskill recipe entries table not available in this database")
                return jsonify({'skills': [], 'message': 'Tradeskill recipe data not available in this database'})
            
            # Check if item is used in any recipes (optimized pre-check)
            cursor.execute("""
                SELECT 1 FROM tradeskill_recipe_entries 
                WHERE item_id = %s AND componentcount > 0 LIMIT 1
            """, (item_id,))
            
            if not cursor.fetchone():
                return jsonify({'skills': []})
            
            # Optimized query using explicit JOINs
            # Include recipe name, ID, tradeskill type, and resulting item icon
            query = """
                SELECT 
                    tsr.name as recipe_name,
                    tsr.id as recipe_id,
                    tsr.tradeskill,
                    tsre.componentcount,
                    result_items.icon as result_item_icon,
                    result_items.name as result_item_name
                FROM tradeskill_recipe tsr
                INNER JOIN tradeskill_recipe_entries tsre ON tsr.id = tsre.recipe_id
                LEFT JOIN (
                    SELECT 
                        tre_result.recipe_id,
                        MAX(CASE 
                            WHEN i.name NOT LIKE '%%Hammer%%' AND i.name NOT LIKE '%%hammer%%' 
                            AND i.name NOT LIKE '%%Tool%%' AND i.name NOT LIKE '%%tool%%'
                            AND i.name NOT LIKE '%%Kit%%' AND i.name NOT LIKE '%%kit%%'
                            AND i.name NOT LIKE '%%Needle%%' AND i.name NOT LIKE '%%needle%%'
                            AND i.name NOT LIKE '%%Awl%%' AND i.name NOT LIKE '%%awl%%'
                            AND i.name NOT LIKE '%%Chisel%%' AND i.name NOT LIKE '%%chisel%%'
                            AND i.name NOT LIKE '%%Tongs%%' AND i.name NOT LIKE '%%tongs%%'
                            AND i.name NOT LIKE '%%File%%' AND i.name NOT LIKE '%%file%%'
                            AND i.name NOT LIKE '%%Planer%%' AND i.name NOT LIKE '%%planer%%'
                            AND i.name NOT LIKE '%%Saw%%' AND i.name NOT LIKE '%%saw%%'
                            AND i.name NOT LIKE '%%Pottery Wheel%%' AND i.name NOT LIKE '%%pottery wheel%%'
                            AND i.name NOT LIKE '%%Kiln%%' AND i.name NOT LIKE '%%kiln%%'
                            THEN i.icon
                            ELSE NULL
                        END) as icon,
                        MAX(CASE 
                            WHEN i.name NOT LIKE '%%Hammer%%' AND i.name NOT LIKE '%%hammer%%' 
                            AND i.name NOT LIKE '%%Tool%%' AND i.name NOT LIKE '%%tool%%'
                            AND i.name NOT LIKE '%%Kit%%' AND i.name NOT LIKE '%%kit%%'
                            AND i.name NOT LIKE '%%Needle%%' AND i.name NOT LIKE '%%needle%%'
                            AND i.name NOT LIKE '%%Awl%%' AND i.name NOT LIKE '%%awl%%'
                            AND i.name NOT LIKE '%%Chisel%%' AND i.name NOT LIKE '%%chisel%%'
                            AND i.name NOT LIKE '%%Tongs%%' AND i.name NOT LIKE '%%tongs%%'
                            AND i.name NOT LIKE '%%File%%' AND i.name NOT LIKE '%%file%%'
                            AND i.name NOT LIKE '%%Planer%%' AND i.name NOT LIKE '%%planer%%'
                            AND i.name NOT LIKE '%%Saw%%' AND i.name NOT LIKE '%%saw%%'
                            AND i.name NOT LIKE '%%Pottery Wheel%%' AND i.name NOT LIKE '%%pottery wheel%%'
                            AND i.name NOT LIKE '%%Kiln%%' AND i.name NOT LIKE '%%kiln%%'
                            THEN i.name
                            ELSE NULL
                        END) as name
                    FROM tradeskill_recipe_entries tre_result
                    INNER JOIN items i ON tre_result.item_id = i.id
                    WHERE tre_result.successcount > 0
                    GROUP BY tre_result.recipe_id
                ) result_items ON tsr.id = result_items.recipe_id
                WHERE tsre.item_id = %s
                  AND tsre.componentcount > 0
                GROUP BY tsr.id
                ORDER BY tsr.tradeskill, tsr.name
                LIMIT 1000
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'skills': []})
            
            # EverQuest tradeskill mapping (based on EQEmu skills documentation)
            tradeskill_names = {
                # Legacy/custom mapping (preserved for compatibility)
                0: 'Baking',
                1: 'Tailoring', 
                2: 'Smithing',
                3: 'Brewing',
                4: 'Fletching',
                5: 'Alchemy',
                6: 'Pottery',
                7: 'Research',
                8: 'Tinkering',
                9: 'Jewelry Making',
                10: 'Make Poison',
                11: 'Unknown',
                # Standard EQEmu skill IDs (based on official skill table)
                56: 'Make Poison',
                57: 'Tinkering',
                58: 'Research',
                59: 'Alchemy',
                60: 'Baking',
                61: 'Tailoring',
                63: 'Blacksmithing',
                64: 'Fletching',
                65: 'Brewing',
                68: 'Jewelry Making',
                69: 'Pottery',
                # Extended/custom tradeskills
                62: 'Augmentation Distillation',
                66: 'Tradeskill 66',
                67: 'Tradeskill 67',
                70: 'Tradeskill 70'
            }
            
            # Organize results by tradeskill type
            recipes_by_skill = {}
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    recipe_name, recipe_id, tradeskill, componentcount, result_item_icon, result_item_name = (
                        row['recipe_name'], row['recipe_id'], row['tradeskill'], row['componentcount'],
                        row.get('result_item_icon'), row.get('result_item_name')
                    )
                else:
                    # Tuple format - now includes icon and name
                    if len(row) >= 6:
                        recipe_name, recipe_id, tradeskill, componentcount, result_item_icon, result_item_name = row
                    else:
                        # Fallback for old format
                        recipe_name, recipe_id, tradeskill, componentcount = row[:4]
                        result_item_icon, result_item_name = None, None
                
                # Get tradeskill name
                skill_name = tradeskill_names.get(tradeskill, f'Unknown Skill ({tradeskill})')
                
                if skill_name not in recipes_by_skill:
                    recipes_by_skill[skill_name] = {
                        'tradeskill_name': skill_name,
                        'tradeskill_id': tradeskill,
                        'recipes': []
                    }
                
                # Clean up recipe name (replace underscores with spaces)
                clean_recipe_name = recipe_name.replace('_', ' ') if recipe_name else f'Recipe {recipe_id}'
                
                recipes_by_skill[skill_name]['recipes'].append({
                    'recipe_id': recipe_id,
                    'recipe_name': clean_recipe_name,
                    'component_count': componentcount,
                    'result_item_icon': result_item_icon,
                    'result_item_name': result_item_name
                })
            
            # Convert to list and sort by skill name
            skills_list = list(recipes_by_skill.values())
            skills_list.sort(key=lambda x: x['tradeskill_name'])
            
            return jsonify({'skills': skills_list})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting item tradeskill recipes for item {item_id}: {e}")
        return jsonify({'error': f'Failed to get tradeskill recipes: {str(e)}'}), 500


@app.route('/api/recipes/<recipe_id>', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_recipe_details(recipe_id):
    """
    Get detailed information about a specific recipe including:
    - What item it creates (produces)
    - What components are required 
    - Tradeskill information
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # First check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe'")
            if not cursor.fetchone():
                app.logger.warning("Tradeskill_recipe table not available in this database")
                return jsonify({'error': 'Recipe data not available in this database'}), 503
            
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe_entries'")  
            if not cursor.fetchone():
                app.logger.warning("Tradeskill_recipe_entries table not available in this database")
                return jsonify({'error': 'Recipe entries data not available in this database'}), 503
            
            cursor.execute("SHOW TABLES LIKE 'items'")
            if not cursor.fetchone():
                app.logger.warning("Items table not available in this database")
                return jsonify({'error': 'Items data not available in this database'}), 503
            
            # Validate recipe_id
            try:
                recipe_id = int(recipe_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid recipe ID'}), 400
            
            # First, get the recipe basic information
            recipe_query = """
                SELECT 
                    tr.id as recipe_id,
                    tr.name as recipe_name,
                    tr.tradeskill as tradeskill_id,
                    tr.trivial as trivial_level,
                    tr.nofail as no_fail,
                    tr.replace_container as replace_container,
                    tr.notes as notes
                FROM tradeskill_recipe tr
                WHERE tr.id = %s
            """
            
            cursor.execute(recipe_query, (recipe_id,))
            recipe_info = cursor.fetchone()
            
            if not recipe_info:
                return jsonify({'error': 'Recipe not found'}), 404
            
            # Handle both dict and tuple results for recipe info
            if isinstance(recipe_info, dict):
                recipe_data = {
                    'recipe_id': recipe_info['recipe_id'],
                    'recipe_name': recipe_info['recipe_name'].replace('_', ' ') if recipe_info['recipe_name'] else 'Unknown Recipe',
                    'tradeskill_id': recipe_info['tradeskill_id'],
                    'trivial_level': recipe_info['trivial_level'],
                    'no_fail': bool(recipe_info['no_fail']),
                    'replace_container': bool(recipe_info['replace_container']),
                    'notes': recipe_info['notes']
                }
            else:
                # Tuple format
                recipe_data = {
                    'recipe_id': recipe_info[0],
                    'recipe_name': recipe_info[1].replace('_', ' ') if recipe_info[1] else 'Unknown Recipe',
                    'tradeskill_id': recipe_info[2],
                    'trivial_level': recipe_info[3],
                    'no_fail': bool(recipe_info[4]),
                    'replace_container': bool(recipe_info[5]),
                    'notes': recipe_info[6]
                }
            
            # Map tradeskill ID to name (based on EQEmu skills documentation)
            tradeskill_names = {
                # Legacy/custom mapping (preserved for compatibility)
                0: 'Baking',
                1: 'Tailoring',
                2: 'Smithing',
                3: 'Brewing',
                4: 'Fletching',
                5: 'Alchemy',
                6: 'Pottery',
                7: 'Research',
                8: 'Tinkering',
                9: 'Jewelry Making',
                10: 'Make Poison',
                11: 'Unknown',
                # Standard EQEmu skill IDs (based on official skill table)
                56: 'Make Poison',
                57: 'Tinkering',
                58: 'Research',
                59: 'Alchemy',
                60: 'Baking',
                61: 'Tailoring',
                63: 'Blacksmithing',
                64: 'Fletching',
                65: 'Brewing',
                68: 'Jewelry Making',
                69: 'Pottery',
                # Extended/custom tradeskills
                62: 'Augmentation Distillation',
                66: 'Tradeskill 66',
                67: 'Tradeskill 67',
                70: 'Tradeskill 70'
            }
            
            recipe_data['tradeskill_name'] = tradeskill_names.get(recipe_data['tradeskill_id'], 'Unknown')
            
            # Get all recipe entries, marking whether items are discovered or not
            # Undiscovered items will show as plain text only (not clickable)
            entries_query = """
                SELECT 
                    tre.item_id,
                    tre.successcount as success_count,
                    tre.failcount as fail_count,
                    tre.componentcount as component_count,
                    tre.iscontainer as is_container,
                    i.Name as item_name,
                    i.icon as item_icon,
                    i.nodrop as no_drop,
                    i.norent as no_rent,
                    i.stackable as is_stackable,
                    CASE WHEN di.item_id IS NOT NULL THEN 1 ELSE 0 END as is_discovered
                FROM tradeskill_recipe_entries tre
                INNER JOIN items i ON tre.item_id = i.id
                LEFT JOIN discovered_items di ON i.id = di.item_id
                WHERE tre.recipe_id = %s
                ORDER BY tre.successcount DESC, tre.componentcount DESC
            """
            
            cursor.execute(entries_query, (recipe_id,))
            entries = cursor.fetchall()
            
            creates_items = []  # Items produced (successcount > 0)
            requires_items = []  # Items needed as components (componentcount > 0)
            container_items = []  # Container items (is_container = 1)
            
            for entry in entries:
                # Handle both dict and tuple results
                if isinstance(entry, dict):
                    item_data = {
                        'item_id': entry['item_id'],
                        'item_name': entry['item_name'],
                        'item_icon': entry['item_icon'],
                        'success_count': entry['success_count'] or 0,
                        'fail_count': entry['fail_count'] or 0,
                        'component_count': entry['component_count'] or 0,
                        'is_container': bool(entry['is_container']),
                        'no_drop': bool(entry['no_drop']),
                        'no_rent': bool(entry['no_rent']),
                        'is_stackable': bool(entry['is_stackable']),
                        'is_discovered': bool(entry['is_discovered'])
                    }
                else:
                    # Tuple format: item_id, success_count, fail_count, component_count, is_container, item_name, item_icon, no_drop, no_rent, is_stackable, is_discovered
                    item_data = {
                        'item_id': entry[0],
                        'item_name': entry[5],
                        'item_icon': entry[6],
                        'success_count': entry[1] or 0,
                        'fail_count': entry[2] or 0,
                        'component_count': entry[3] or 0,
                        'is_container': bool(entry[4]),
                        'no_drop': bool(entry[7]),
                        'no_rent': bool(entry[8]),
                        'is_stackable': bool(entry[9]),
                        'is_discovered': bool(entry[10])
                    }
                
                # Categorize items based on their role in the recipe
                if item_data['success_count'] > 0:
                    creates_items.append(item_data)
                
                if item_data['component_count'] > 0:
                    requires_items.append(item_data)
                
                if item_data['is_container']:
                    container_items.append(item_data)
            
            # Build final response
            response_data = {
                'recipe': recipe_data,
                'creates': creates_items,
                'requires': requires_items,
                'containers': container_items
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting recipe details for recipe {recipe_id}: {e}")
        return jsonify({'error': f'Failed to get recipe details: {str(e)}'}), 500


@app.route('/api/items/<item_id>/created-by-recipes', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_item_created_by_recipes(item_id):
    """
    Get tradeskill recipes that create this item as a result.
    Equivalent to return_where_item_result_trade_skill() from the legacy system.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # Check if required tables exist
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe'")
            if not cursor.fetchone():
                return jsonify({'recipes': []})
            
            cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe_entries'")
            if not cursor.fetchone():
                return jsonify({'recipes': []})
            
            # Validate item_id
            try:
                item_id = int(item_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid item ID'}), 400
            
            # Query for recipes that create this item (successcount > 0)
            # Include the icon of the item being created
            query = """
                SELECT
                    tr.name as recipe_name,
                    tr.id as recipe_id,
                    tr.tradeskill as tradeskill_id,
                    tr.trivial as trivial_level,
                    i.icon as result_item_icon,
                    i.name as result_item_name
                FROM
                    tradeskill_recipe tr,
                    tradeskill_recipe_entries tre,
                    items i
                WHERE
                    tr.id = tre.recipe_id
                    AND tre.item_id = %s
                    AND tre.item_id = i.id
                    AND tre.successcount > 0
                GROUP BY
                    tr.id
                ORDER BY
                    tr.tradeskill, tr.trivial, tr.name
            """
            
            cursor.execute(query, (item_id,))
            results = cursor.fetchall()
            app.logger.debug(f"Drop sources query for item {item_id} returned {len(results)} results")
            
            if not results:
                return jsonify({'recipes': []})
            
            # Use the same tradeskill mapping as other endpoints
            tradeskill_names = {
                # Legacy/custom mapping (preserved for compatibility)
                0: 'Baking',
                1: 'Tailoring',
                2: 'Smithing',
                3: 'Brewing',
                4: 'Fletching',
                5: 'Alchemy',
                6: 'Pottery',
                7: 'Research',
                8: 'Tinkering',
                9: 'Jewelry Making',
                10: 'Make Poison',
                11: 'Unknown',
                # Standard EQEmu skill IDs (based on official skill table)
                56: 'Make Poison',
                57: 'Tinkering',
                58: 'Research',
                59: 'Alchemy',
                60: 'Baking',
                61: 'Tailoring',
                63: 'Blacksmithing',
                64: 'Fletching',
                65: 'Brewing',
                68: 'Jewelry Making',
                69: 'Pottery',
                # Extended/custom tradeskills
                62: 'Augmentation Distillation',
                66: 'Tradeskill 66',
                67: 'Tradeskill 67',
                70: 'Tradeskill 70'
            }
            
            recipes = []
            for row in results:
                # Handle both dict and tuple results
                if isinstance(row, dict):
                    recipe_name = row['recipe_name']
                    recipe_id = row['recipe_id']
                    tradeskill_id = row['tradeskill_id']
                    trivial_level = row['trivial_level']
                    result_item_icon = row.get('result_item_icon')
                    result_item_name = row.get('result_item_name')
                else:
                    if len(row) >= 6:
                        recipe_name, recipe_id, tradeskill_id, trivial_level, result_item_icon, result_item_name = row
                    else:
                        # Fallback for old format
                        recipe_name, recipe_id, tradeskill_id, trivial_level = row[:4]
                        result_item_icon, result_item_name = None, None
                
                tradeskill_name = tradeskill_names.get(tradeskill_id, 'Unknown')
                
                recipes.append({
                    'recipe_id': recipe_id,
                    'recipe_name': recipe_name.replace('_', ' ') if recipe_name else 'Unknown Recipe',
                    'tradeskill_id': tradeskill_id,
                    'tradeskill_name': tradeskill_name,
                    'trivial_level': trivial_level,
                    'result_item_icon': result_item_icon,
                    'result_item_name': result_item_name
                })
            
            return jsonify({'recipes': recipes})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error getting recipes that create item {item_id}: {e}")
        return jsonify({'error': f'Failed to get creation recipes: {str(e)}'}), 500


@app.route('/api/items/<item_id>/availability', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)
def get_item_data_availability(item_id):
    """
    Lightweight endpoint to check which data sources are available for an item.
    Returns counts/existence flags without fetching actual data for efficiency.
    """
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # Validate item_id
            try:
                item_id = int(item_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid item ID'}), 400
            
            availability = {
                'drop_sources': 0,
                'merchant_sources': 0,
                'ground_spawns': 0,
                'forage_sources': 0,
                'tradeskill_recipes': 0,
                'created_by_recipes': 0
            }
            
            app.logger.info(f"Checking availability for item {item_id}")
            
            # Check tradeskill recipes (where item is used as component) - Use simple existence check
            try:
                cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe'")
                if cursor.fetchone():
                    cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe_entries'")
                    if cursor.fetchone():
                        # Simple existence check - just see if any record exists
                        cursor.execute("""
                            SELECT 1 FROM tradeskill_recipe_entries 
                            WHERE item_id = %s AND componentcount > 0 LIMIT 1
                        """, (item_id,))
                        result = cursor.fetchone()
                        availability['tradeskill_recipes'] = 1 if result else 0
                        app.logger.info(f"Tradeskill recipes for item {item_id}: {'found' if result else 'none'}")
            except Exception as e:
                app.logger.error(f"Tradeskill recipes check failed: {e}")
            
            # Check created by recipes (where item is created as result) - Use simple existence check
            try:
                cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe'")
                if cursor.fetchone():
                    cursor.execute("SHOW TABLES LIKE 'tradeskill_recipe_entries'")
                    if cursor.fetchone():
                        # Simple existence check - just see if any record exists
                        cursor.execute("""
                            SELECT 1 FROM tradeskill_recipe_entries 
                            WHERE item_id = %s AND successcount > 0 LIMIT 1
                        """, (item_id,))
                        result = cursor.fetchone()
                        availability['created_by_recipes'] = 1 if result else 0
                        app.logger.info(f"Created by recipes for item {item_id}: {'found' if result else 'none'}")
            except Exception as e:
                app.logger.error(f"Created by recipes check failed: {e}")
            
            # Check drop sources - Use the same complex query as the actual drop sources endpoint
            try:
                cursor.execute("SHOW TABLES LIKE 'lootdrop_entries'")
                if cursor.fetchone():
                    # Use the same filtering logic as the drop sources endpoint to avoid false positives
                    cursor.execute("""
                        SELECT 1 FROM npc_types nt
                        INNER JOIN spawnentry se ON nt.id = se.npcID
                        INNER JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
                        INNER JOIN zone z ON s2.zone = z.short_name
                        INNER JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
                        INNER JOIN lootdrop_entries lde ON lte.lootdrop_id = lde.lootdrop_id
                        LEFT JOIN spawn2_disabled s2d ON s2.id = s2d.spawn2_id
                        WHERE lde.item_id = %s
                          AND z.min_status = 0
                          AND s2d.spawn2_id IS NULL
                          AND nt.merchant_id = 0
                          AND z.short_name NOT IN ('load', 'arena', 'nexus', 'arttest', 'ssratemple', 'tutorial')
                        LIMIT 1
                    """, (item_id,))
                    result = cursor.fetchone()
                    availability['drop_sources'] = 1 if result else 0
                    app.logger.debug(f"Drop sources availability for item {item_id}: {'found' if result else 'none'}")
            except Exception as e:
                app.logger.debug(f"Drop sources check failed: {e}")
            
            # Check merchant sources - Use existence check
            try:
                cursor.execute("SHOW TABLES LIKE 'merchantlist'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 1 FROM merchantlist 
                        WHERE item = %s LIMIT 1
                    """, (item_id,))
                    result = cursor.fetchone()
                    availability['merchant_sources'] = 1 if result else 0
            except Exception as e:
                app.logger.debug(f"Merchant sources check failed: {e}")
            
            # Check ground spawns - Use existence check
            try:
                cursor.execute("SHOW TABLES LIKE 'ground_spawns'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 1 FROM ground_spawns 
                        WHERE item = %s LIMIT 1
                    """, (item_id,))
                    result = cursor.fetchone()
                    availability['ground_spawns'] = 1 if result else 0
            except Exception as e:
                app.logger.debug(f"Ground spawns check failed: {e}")
            
            # Check forage sources - Use existence check
            try:
                cursor.execute("SHOW TABLES LIKE 'forage'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 1 FROM forage 
                        WHERE itemid = %s LIMIT 1
                    """, (item_id,))
                    result = cursor.fetchone()
                    availability['forage_sources'] = 1 if result else 0
            except Exception as e:
                app.logger.debug(f"Forage sources check failed: {e}")
            
            return jsonify(availability)
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        app.logger.error(f"Error checking item data availability for item {item_id}: {e}")
        return jsonify({'error': f'Failed to check data availability: {str(e)}'}), 500


@app.route('/api/debug/tables', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=10, requests_per_hour=60)
def debug_database_tables():
    """Debug endpoint to check which tables exist in the database."""
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # Get all tables
            cursor.execute("SHOW TABLES")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # Check specific tables we need
            required_tables = [
                'tradeskill_recipe',
                'tradeskill_recipe_entries',
                'lootdrop_entries',
                'loottable_entries',
                'npc_types',
                'merchantlist',
                'ground_spawns',
                'forage',
                'items'
            ]
            
            table_status = {}
            for table in required_tables:
                exists = table in all_tables
                table_status[table] = exists
                
                if exists:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table} LIMIT 1")
                        count = cursor.fetchone()[0]
                        table_status[f"{table}_count"] = count
                    except Exception as e:
                        table_status[f"{table}_error"] = str(e)
            
            return jsonify({
                'total_tables': len(all_tables),
                'all_tables': all_tables[:20],  # First 20 tables
                'required_tables': table_status
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({'error': f'Failed to debug tables: {str(e)}'}), 500


# Debug endpoints removed for security - they could leak information about undiscovered items


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
    
    # Shutdown database manager
    try:
        from utils.database_manager import shutdown_database_manager
        shutdown_database_manager()
        logger.info("Database manager shutdown")
    except Exception as e:
        logger.error(f"Error shutting down database manager: {e}")
    
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


@app.route('/api/npcs/search', methods=['GET'])
@exempt_when_limiting
@rate_limit_by_ip(requests_per_minute=60, requests_per_hour=600)
def search_npcs():
    """
    Search NPCs in the EQEmu database.
    Returns NPCs with basic information and spawn locations.
    """
    app.logger.info("=== NPC SEARCH START ===")
    conn = None
    cursor = None
    
    try:
        # Get database connection
        app.logger.info("Getting database connection...")
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        app.logger.info(f"Got connection, db_type: {db_type}")
        cursor = conn.cursor()
        
        # Get search parameters
        search_query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        min_level = request.args.get('min_level')
        max_level = request.args.get('max_level')
        zone_filter = request.args.get('zone')
        
        app.logger.info(f"Search params: q='{search_query}', limit={limit}, offset={offset}")
        
        if not search_query and not min_level and not max_level and not zone_filter:
            return jsonify({'error': 'Search query or filters required'}), 400
        
        # Build WHERE clause and parameters
        where_conditions = []
        query_params = []
        
        # Add search query condition with underscore/space/hash handling
        if search_query:
            # Convert spaces to underscores for database search, and use both patterns
            search_with_underscores = search_query.replace(' ', '_')
            search_with_spaces = search_query.replace('_', ' ')
            
            # Search for multiple variations to handle database format variations:
            # - Original query
            # - With underscores instead of spaces  
            # - With spaces instead of underscores
            # - With # prefix variations
            # - Using REPLACE to normalize both _ and # for comparison
            where_conditions.append("""(
                nt.name LIKE %s OR 
                nt.name LIKE %s OR 
                nt.name LIKE %s OR
                nt.name LIKE %s OR
                nt.name LIKE %s OR
                REPLACE(REPLACE(nt.name, '_', ' '), '#', '') LIKE %s
            )""")
            query_params.extend([
                f'%{search_query}%',                    # Original search
                f'%{search_with_underscores}%',         # Spaces -> underscores
                f'%{search_with_spaces}%',              # Underscores -> spaces 
                f'%#{search_query}%',                   # With # prefix
                f'%#{search_with_underscores}%',        # With # prefix and underscores
                f'%{search_query}%'                     # Normalized comparison
            ])
        
        # Add level filters
        if min_level:
            where_conditions.append("nt.level >= %s")
            query_params.append(int(min_level))
        
        if max_level:
            where_conditions.append("nt.level <= %s")
            query_params.append(int(max_level))
        
        # Add zone filter
        if zone_filter:
            where_conditions.append("z.short_name = %s")
            query_params.append(zone_filter)
        
        where_clause = " AND ".join(where_conditions)
        
        # Count query
        count_query = f"""
            SELECT COUNT(DISTINCT nt.id) as total_count
            FROM npc_types nt
            LEFT JOIN spawnentry se ON nt.id = se.npcID
            LEFT JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
            LEFT JOIN zone z ON s2.zone = z.short_name
            WHERE {where_clause}
        """
        
        cursor.execute(count_query, query_params)
        result = cursor.fetchone()
        total_count = result['total_count'] if isinstance(result, dict) else result[0]
        
        # Main search query with spawn location info
        search_query_sql = f"""
            SELECT DISTINCT
                nt.id,
                nt.name,
                nt.lastname,
                nt.level,
                nt.race,
                nt.class,
                nt.hp,
                nt.mindmg,
                nt.maxdmg,
                z.short_name as zone_short_name,
                z.long_name as zone_long_name
            FROM npc_types nt
            LEFT JOIN spawnentry se ON nt.id = se.npcID
            LEFT JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
            LEFT JOIN zone z ON s2.zone = z.short_name
            WHERE {where_clause}
            ORDER BY nt.name ASC
            LIMIT %s OFFSET %s
        """
        
        search_params = query_params + [limit, offset]
        cursor.execute(search_query_sql, search_params)
        results = cursor.fetchall()
        
        app.logger.debug(f"NPC search query returned {len(results)} results")
        
        # Format results
        npcs = []
        for row in results:
            if isinstance(row, dict):
                npc_data = dict(row)
            else:
                # Convert tuple to dict
                columns = [desc[0] for desc in cursor.description]
                npc_data = dict(zip(columns, row))
            
            # Clean up the data
            npc = {
                'id': npc_data['id'],
                'name': npc_data['name'].replace('_', ' ') if npc_data['name'] else 'Unknown NPC',
                'lastname': npc_data.get('lastname', ''),
                'level': npc_data.get('level', 1),
                'race': npc_data.get('race', 0),
                'class': npc_data.get('class', 0),
                'hp': npc_data.get('hp', 0),
                'mindmg': npc_data.get('mindmg', 0),
                'maxdmg': npc_data.get('maxdmg', 0),
                'zone_short_name': npc_data.get('zone_short_name', ''),
                'zone_long_name': npc_data.get('zone_long_name', '')
            }
            npcs.append(npc)
        
        app.logger.info(f"Formatted {len(npcs)} NPCs for response")
        
        return jsonify({
            'npcs': npcs,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'search_query': request.args.get('q', '')
        })
        
    except Exception as e:
        app.logger.error(f"Error searching NPCs: {e}")
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


def parse_special_abilities(special_abilities_str):
    """
    Parse EQEmu special_abilities field into a list of readable special attacks.
    
    EQEmu special_abilities format is typically comma-separated values with codes:
    Example: "1,1^2,1^3,1^35,1" 
    
    Common special ability codes:
    1 = Summon, 2 = Enrage, 3 = Rampage, 4 = Area Rampage, 5 = Flurry, 
    6 = Triple, 7 = Quad, 8 = Dual Wield, 9 = Bane Attack, 10 = Magical Attack,
    11 = Ranged Attack, 12 = Unslowable, 13 = Unmezzable, 14 = Uncharmable,
    15 = Unstunable, 16 = Unsnareable, 17 = Unfearable, 18 = Undispellable,
    19 = Immune to Fleeing, 20 = Destructible Object, 21 = No Harm from Players,
    22 = Always Flee, 23 = Flee Percent, 24 = Allow Beneficial, 25 = Disable Melee,
    26 = NPC Chase Distance, 27 = Allow Tank, 28 = Ignore Root Aggro,
    29 = Casting Resist Diff, 30 = Counter Avoid Damage, 31 = Prox Aggro,
    32 = Immune to Aggro, 33 = Resist Ranged Spells, 34 = See Invis,
    35 = See Invis vs Undead, 36 = See Hide, 37 = See Improved Hide,
    38 = Innate Dual Wield, 39 = Innate Berserk, 40 = Findable, 41 = Track
    """
    
    if not special_abilities_str or special_abilities_str.strip() == '':
        return []
    
    # Map of ability codes to readable names
    ability_names = {
        1: "Summon", 2: "Enrage", 3: "Rampage", 4: "Area Rampage", 5: "Flurry",
        6: "Triple Attack", 7: "Quad Attack", 8: "Dual Wield", 9: "Bane Attack", 
        10: "Magical Attack", 11: "Ranged Attack", 12: "Unslowable", 13: "Unmezzable",
        14: "Uncharmable", 15: "Unstunable", 16: "Unsnareable", 17: "Unfearable",
        18: "Undispellable", 19: "Immune to Fleeing", 20: "Destructible Object",
        21: "No Harm from Players", 22: "Always Flee", 23: "Flee Percent",
        24: "Allow Beneficial", 25: "Disable Melee", 26: "NPC Chase Distance",
        27: "Allow Tank", 28: "Ignore Root Aggro", 29: "Casting Resist Diff",
        30: "Counter Avoid Damage", 31: "Prox Aggro", 32: "Immune to Aggro",
        33: "Resist Ranged Spells", 34: "See Invisible", 35: "See Invisible vs Undead",
        36: "See Hide", 37: "See Improved Hide", 38: "Innate Dual Wield",
        39: "Innate Berserk", 40: "Findable", 41: "Track"
    }
    
    special_attacks = []
    
    try:
        # Parse the special_abilities string - typically format like "1,1^2,1^3,1"
        # Each ability is separated by ^ and has format "code,value"
        abilities = special_abilities_str.split('^')
        
        for ability in abilities:
            if ',' in ability:
                parts = ability.split(',')
                if len(parts) >= 2:
                    try:
                        ability_code = int(parts[0])
                        ability_value = int(parts[1])
                        
                        # Only include active abilities (value > 0)
                        if ability_value > 0 and ability_code in ability_names:
                            special_attacks.append(ability_names[ability_code])
                    except (ValueError, IndexError):
                        continue
        
        # Remove duplicates and sort
        special_attacks = sorted(list(set(special_attacks)))
        
    except Exception as e:
        app.logger.warning(f"Error parsing special abilities '{special_abilities_str}': {e}")
        return []
    
    return special_attacks


@app.route('/api/npcs/<npc_id>/details', methods=['GET'])
@rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300)
def get_npc_details(npc_id):
    """
    Get detailed information about a specific NPC including spawn locations and loot drops.
    Only shows discovered items in loot drops.
    """
    try:
        npc_id_int = int(npc_id)
        app.logger.info(f"Getting NPC details for ID: {npc_id_int}")
        
        # Get database connection
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        cursor = conn.cursor()
        
        try:
            # Get comprehensive NPC information matching EQ Alla clone
            npc_query = """
                SELECT 
                    nt.*
                FROM npc_types nt
                WHERE nt.id = %s
            """
            
            cursor.execute(npc_query, (npc_id_int,))
            npc_result = cursor.fetchone()
            
            if not npc_result:
                return jsonify({'error': 'NPC not found'}), 404
            
            # Convert to dict if it's a tuple
            if isinstance(npc_result, dict):
                npc_data = dict(npc_result)
            else:
                columns = [desc[0] for desc in cursor.description]
                npc_data = dict(zip(columns, npc_result))
            
            # Get spawn locations matching EQ Alla clone query structure
            spawn_query = """
                SELECT DISTINCT
                    z.note,
                    z.short_name,
                    z.long_name,
                    s2.x,
                    s2.y,
                    s2.z,
                    sg.name AS spawngroup
                FROM zone z
                INNER JOIN spawn2 s2 ON z.short_name = s2.zone
                INNER JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID
                LEFT JOIN spawngroup sg ON s2.spawngroupID = sg.id
                WHERE se.npcID = %s
                ORDER BY z.long_name
            """
            
            cursor.execute(spawn_query, (npc_id_int,))
            spawn_results = cursor.fetchall()
            
            spawn_locations = []
            for spawn in spawn_results:
                if isinstance(spawn, dict):
                    spawn_data = dict(spawn)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    spawn_data = dict(zip(columns, spawn))
                
                spawn_locations.append({
                    'zone_short_name': spawn_data['short_name'],
                    'zone_long_name': spawn_data['long_name'] or spawn_data['short_name'],
                    'zone_note': spawn_data.get('note', ''),
                    'spawngroup': spawn_data.get('spawngroup', ''),
                    'x': spawn_data.get('x', 0),
                    'y': spawn_data.get('y', 0),
                    'z': spawn_data.get('z', 0)
                })
            
            # Get NPC spells (matching EQ Alla clone query structure)
            npc_spells = []
            if npc_data.get('npc_spells_id'):
                spells_query = """
                    SELECT 
                        nse.spellid,
                        sn.name as spell_name,
                        sn.new_icon,
                        nse.minlevel,
                        nse.maxlevel,
                        nse.priority,
                        nse.recast_delay
                    FROM npc_spells_entries nse
                    INNER JOIN spells_new sn ON nse.spellid = sn.id
                    WHERE nse.npc_spells_id = %s
                    AND nse.minlevel <= %s
                    AND nse.maxlevel >= %s
                    ORDER BY nse.priority DESC, sn.name
                """
                
                cursor.execute(spells_query, (npc_data['npc_spells_id'], npc_data.get('level', 1), npc_data.get('level', 1)))
                spell_results = cursor.fetchall()
                
                for spell in spell_results:
                    if isinstance(spell, dict):
                        spell_data = dict(spell)
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        spell_data = dict(zip(columns, spell))
                    
                    npc_spells.append({
                        'spell_id': spell_data['spellid'],
                        'spell_name': spell_data['spell_name'].replace('_', ' ') if spell_data['spell_name'] else 'Unknown Spell',
                        'icon': spell_data.get('new_icon', 0),
                        'min_level': spell_data.get('minlevel', 1),
                        'max_level': spell_data.get('maxlevel', 255),
                        'priority': spell_data.get('priority', 0),
                        'recast_delay': spell_data.get('recast_delay', 0)
                    })

            # Get merchant items (only discovered items)
            merchant_items = []
            if npc_data.get('merchant_id'):
                merchant_query = """
                    SELECT DISTINCT
                        i.id as item_id,
                        i.name as item_name,
                        i.icon,
                        i.price
                    FROM merchantlist ml
                    INNER JOIN items i ON ml.item = i.id
                    INNER JOIN discovered_items di ON i.id = di.item_id
                    WHERE ml.merchantid = %s
                    AND ml.item > 0
                    ORDER BY ml.slot, i.name
                    LIMIT 100
                """
                
                cursor.execute(merchant_query, (npc_data['merchant_id'],))
                merchant_results = cursor.fetchall()
                
                for item in merchant_results:
                    if isinstance(item, dict):
                        item_data = dict(item)
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        item_data = dict(zip(columns, item))
                    
                    merchant_items.append({
                        'item_id': item_data['item_id'],
                        'item_name': item_data['item_name'].replace('_', ' ') if item_data['item_name'] else 'Unknown Item',
                        'icon': item_data.get('icon', 0),
                        'price': item_data.get('price', 0)
                    })

            # Get loot drops with hierarchical structure (loot drops containing items)
            loot_drops = []
            if npc_data.get('loottable_id'):
                # First, get all unique loot drops for this NPC's loot table
                loot_groups_query = """
                    SELECT DISTINCT
                        lte.lootdrop_id,
                        lte.probability as table_probability,
                        lte.multiplier,
                        lte.droplimit,
                        lte.mindrop
                    FROM loottable_entries lte
                    WHERE lte.loottable_id = %s
                    ORDER BY lte.probability DESC, lte.lootdrop_id
                """
                
                cursor.execute(loot_groups_query, (npc_data['loottable_id'],))
                loot_groups = cursor.fetchall()
                
                for group in loot_groups:
                    if isinstance(group, dict):
                        group_data = dict(group)
                    else:
                        columns = [desc[0] for desc in cursor.description]
                        group_data = dict(zip(columns, group))
                    
                    loot_drop_id = group_data['lootdrop_id']
                    table_probability = group_data.get('probability', 100)
                    multiplier = group_data.get('multiplier', 1)
                    droplimit = group_data.get('droplimit', 0)
                    mindrop = group_data.get('mindrop', 0)
                    
                    # Get items for this specific loot drop group
                    items_query = """
                        SELECT DISTINCT
                            i.id as item_id,
                            i.name as item_name,
                            i.icon,
                            i.itemtype,
                            lde.chance as item_chance
                        FROM lootdrop_entries lde
                        INNER JOIN items i ON lde.item_id = i.id
                        INNER JOIN discovered_items di ON i.id = di.item_id
                        WHERE lde.lootdrop_id = %s
                        AND lde.item_id > 0
                        ORDER BY lde.chance DESC, i.name
                        LIMIT 20
                    """
                    
                    cursor.execute(items_query, (loot_drop_id,))
                    item_results = cursor.fetchall()
                    
                    items = []
                    for item in item_results:
                        if isinstance(item, dict):
                            item_data = dict(item)
                        else:
                            columns = [desc[0] for desc in cursor.description]
                            item_data = dict(zip(columns, item))
                        
                        # Calculate overall probability (table_probability * item_chance)
                        item_chance = item_data.get('item_chance', 1)
                        overall_probability = round((table_probability / 100.0) * (item_chance / 100.0) * 100, 2)
                        
                        items.append({
                            'item_id': item_data['item_id'],
                            'item_name': item_data['item_name'].replace('_', ' ') if item_data['item_name'] else 'Unknown Item',
                            'icon': item_data.get('icon', 0),
                            'itemtype': item_data.get('itemtype', 0),
                            'item_chance': item_chance,
                            'overall_probability': max(0.01, overall_probability)
                        })
                    
                    # Only add loot drop groups that have items
                    if items:
                        loot_drops.append({
                            'loot_drop_id': loot_drop_id,
                            'table_probability': table_probability,
                            'multiplier': multiplier,
                            'droplimit': droplimit,
                            'mindrop': mindrop,
                            'items': items
                        })
            
            # Format response with comprehensive NPC data matching EQ Alla clone
            detailed_npc = {
                'id': npc_data['id'],
                'name': npc_data['name'].replace('_', ' ') if npc_data['name'] else 'Unknown NPC',
                'lastname': npc_data.get('lastname', ''),
                'level': npc_data.get('level', 1),
                'race': npc_data.get('race', 0),
                'class': npc_data.get('class', 0),
                'gender': npc_data.get('gender', 0),
                'size': npc_data.get('size', 6),
                'texture': npc_data.get('texture', 0),
                'helmtexture': npc_data.get('helmtexture', 0),
                
                # Combat stats
                'hp': npc_data.get('hp', 0),
                'mana': npc_data.get('mana', 0),
                'ac': npc_data.get('AC', 0),
                'mindmg': npc_data.get('mindmg', 0),
                'maxdmg': npc_data.get('maxdmg', 0),
                'attack_speed': npc_data.get('attack_speed', 0),
                'attack_delay': npc_data.get('attack_delay', 30),
                
                # Resistances
                'resistances': {
                    'magic': npc_data.get('MR', 0),
                    'cold': npc_data.get('CR', 0),
                    'disease': npc_data.get('DR', 0),
                    'fire': npc_data.get('FR', 0),
                    'poison': npc_data.get('PR', 0)
                },
                
                # System IDs
                'loottable_id': npc_data.get('loottable_id', 0),
                'merchant_id': npc_data.get('merchant_id', 0),
                'npc_spells_id': npc_data.get('npc_spells_id', 0),
                'npc_faction_id': npc_data.get('npc_faction_id', 0),
                
                # Special attacks
                'special_attacks': parse_special_abilities(npc_data.get('special_abilities', '')),
                
                # Associated data
                'spawn_locations': spawn_locations,
                'loot_drops': loot_drops,
                'spells': npc_spells,
                'merchant_items': merchant_items
            }
            
            app.logger.info(f"NPC details retrieved successfully for ID: {npc_id_int}")
            
            return jsonify(detailed_npc)
            
        except Exception as e:
            app.logger.error(f"Error querying NPC details: {e}")
            import traceback
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Failed to query NPC details: {str(e)}'}), 500
            
        finally:
            cursor.close()
            
    except ValueError:
        app.logger.error(f"Invalid NPC ID: {npc_id}")
        return jsonify({'error': 'Invalid NPC ID'}), 400
    except Exception as e:
        app.logger.error(f"Error getting NPC details: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to get NPC details: {str(e)}'}), 500
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


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
        # Check both persistent config and environment variables for database configuration
        try:
            from utils.persistent_config import get_persistent_config
            persistent_config = get_persistent_config()
            db_config = persistent_config.get_database_config()
            
            if db_config or os.environ.get('EQEMU_DATABASE_URL'):
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
        except Exception as e:
            logger.error(f"Error checking database configuration: {e}")
            logger.info("⚠️ Database initialization skipped due to configuration error")

    
    # Spell system disabled - skipping spell data preloading
    logger.info("🚫 Spell system disabled - skipping startup spell data preload")
    
    # Mark server startup as complete
    server_startup_progress['is_starting'] = False
    server_startup_progress['startup_complete'] = True
    server_startup_progress['current_step'] = 'Server ready'
    server_startup_progress['progress_percent'] = 100
    server_startup_progress['startup_time'] = datetime.now().isoformat()
    logger.info("✅ Server startup complete")


@app.route('/api/zone-map/<zone_short_name>', methods=['GET'])
def get_zone_map(zone_short_name):
    """
    Get zone map data (lines) for rendering an interactive map.
    Reads from the Maps folder and returns processed line data.
    """
    try:
        # Sanitize zone name to prevent directory traversal
        zone_short_name = zone_short_name.replace('..', '').replace('/', '').replace('\\', '').strip()
        
        if not zone_short_name:
            return jsonify({'error': 'Zone name is required'}), 400
        
        # Look for map file in Maps directory - try multiple possible locations
        # First try: relative to backend directory (Railway deployment with symlink)
        maps_dir = os.path.join(os.path.dirname(__file__), 'Maps')
        
        # Second try: relative to project root (local development)
        if not os.path.exists(maps_dir):
            maps_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Maps')
        
        # Third try: absolute path for Railway deployment
        if not os.path.exists(maps_dir):
            maps_dir = '/app/Maps'
        
        # Debug logging for production troubleshooting
        print(f"[DEBUG] zone-map endpoint: zone={zone_short_name}, maps_dir={maps_dir}, exists={os.path.exists(maps_dir)}")
        if os.path.exists(maps_dir):
            files = os.listdir(maps_dir)[:5]  # Show first 5 files for debugging
            print(f"[DEBUG] Maps directory contains {len(os.listdir(maps_dir))} files, sample: {files}")
        
        map_file_path = os.path.join(maps_dir, f"{zone_short_name}.txt")
        
        # Also try with _1 and _2 suffixes if base doesn't exist
        if not os.path.exists(map_file_path):
            for suffix in ['_1', '_2']:
                alt_path = os.path.join(maps_dir, f"{zone_short_name}{suffix}.txt")
                if os.path.exists(alt_path):
                    map_file_path = alt_path
                    break
        
        if not os.path.exists(map_file_path):
            return jsonify({'error': 'Zone map not found', 'zone': zone_short_name}), 404
        
        # Read and parse map file
        lines = []
        try:
            with open(map_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line.startswith('L '):
                        lines.append(line)
                    # Limit lines to prevent excessive memory usage
                    if len(lines) >= 10000:
                        app.logger.warning(f"Zone map {zone_short_name} has >10000 lines, truncating")
                        break
        except UnicodeDecodeError:
            # Try with latin-1 encoding if UTF-8 fails
            with open(map_file_path, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line.startswith('L '):
                        lines.append(line)
                    if len(lines) >= 10000:
                        break
        
        # Try to load label file (usually _1.txt suffix)
        labels = []
        label_file_path = os.path.join(maps_dir, f"{zone_short_name}_1.txt")
        
        if os.path.exists(label_file_path):
            try:
                with open(label_file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f):
                        line = line.strip()
                        if line.startswith('P '):
                            labels.append(line)
                        # Limit labels to prevent excessive memory usage
                        if len(labels) >= 1000:
                            app.logger.warning(f"Zone labels {zone_short_name} has >1000 labels, truncating")
                            break
            except UnicodeDecodeError:
                # Try with latin-1 encoding if UTF-8 fails
                with open(label_file_path, 'r', encoding='latin-1') as f:
                    for line_num, line in enumerate(f):
                        line = line.strip()
                        if line.startswith('P '):
                            labels.append(line)
                        if len(labels) >= 1000:
                            break
            except Exception as e:
                app.logger.warning(f"Could not read label file for {zone_short_name}: {str(e)}")
        
        app.logger.info(f"Loaded {len(lines)} map lines and {len(labels)} labels for zone: {zone_short_name}")
        
        return jsonify({
            'zone': zone_short_name,
            'lines': lines,
            'labels': labels,
            'line_count': len(lines),
            'label_count': len(labels)
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Zone map not found', 'zone': zone_short_name}), 404
    except Exception as e:
        app.logger.error(f"Error loading zone map {zone_short_name}: {str(e)}")
        return jsonify({'error': 'Failed to load zone map'}), 500


@app.route('/api/zone-npcs/<zone_short_name>', methods=['GET'])
def get_zone_npcs(zone_short_name):
    """
    Get all NPCs that spawn in a specific zone with their spawn locations.
    Returns detailed NPC information for the zone page NPC list.
    """
    try:
        zone_short_name = zone_short_name.lower().strip()
        app.logger.info(f"Getting NPCs for zone: {zone_short_name}")
        
        # Get database connection
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            app.logger.error(f"Database connection failed: {error}")
            return jsonify({'error': error or 'Database not configured'}), 503
        
        npcs = []
        
        cursor = conn.cursor()
        try:
            # Query to get all NPCs in the specified zone with spawn details
            # Based on EQEmu spawn2 schema: https://docs.eqemu.io/schema/spawns/spawn2/
            npc_query = """
                SELECT DISTINCT
                    nt.id,
                    nt.name,
                    nt.lastname,
                    nt.level,
                    nt.race,
                    nt.class,
                    nt.hp,
                    nt.mana,
                    nt.AC,
                    nt.mindmg,
                    nt.maxdmg,
                    s2.x,
                    s2.y,
                    s2.z,
                    s2.heading,
                    s2.respawntime,
                    s2.variance,
                    s2.pathgrid,
                    sg.name AS spawngroup_name,
                    se.chance AS spawn_chance
                FROM npc_types nt
                INNER JOIN spawnentry se ON nt.id = se.npcID
                INNER JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
                LEFT JOIN spawngroup sg ON s2.spawngroupID = sg.id
                WHERE s2.zone = %s
                ORDER BY nt.level DESC, nt.name ASC
                LIMIT 500
            """
            
            cursor.execute(npc_query, (zone_short_name,))
            results = cursor.fetchall()
            
            app.logger.debug(f"Found {len(results)} NPC spawns in zone: {zone_short_name}")
            
            # Process results
            for row in results:
                if isinstance(row, dict):
                    npc_data = dict(row)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    npc_data = dict(zip(columns, row))
                
                npc = {
                    'id': npc_data['id'],
                    'name': npc_data['name'].replace('_', ' ') if npc_data['name'] else 'Unknown NPC',
                    'lastname': npc_data.get('lastname', '') or '',
                    'full_name': (npc_data['name'].replace('_', ' ') + ' ' + (npc_data.get('lastname', '') or '')).strip(),
                    'level': npc_data.get('level', 1),
                    'race': npc_data.get('race', 0),
                    'class': npc_data.get('class', 0),
                    'hp': npc_data.get('hp', 0),
                    'mana': npc_data.get('mana', 0),
                    'ac': npc_data.get('AC', 0),
                    'mindmg': npc_data.get('mindmg', 0),
                    'maxdmg': npc_data.get('maxdmg', 0),
                    'location': {
                        'x': float(npc_data.get('x', 0)) if npc_data.get('x') is not None else 0,
                        'y': float(npc_data.get('y', 0)) if npc_data.get('y') is not None else 0,
                        'z': float(npc_data.get('z', 0)) if npc_data.get('z') is not None else 0,
                        'heading': float(npc_data.get('heading', 0)) if npc_data.get('heading') is not None else 0
                    },
                    'spawn_info': {
                        'respawn_time': npc_data.get('respawntime', 0),
                        'variance': npc_data.get('variance', 0),
                        'spawn_chance': npc_data.get('spawn_chance', 100),
                        'spawngroup': npc_data.get('spawngroup_name', '') or '',
                        'pathgrid': npc_data.get('pathgrid', 0)
                    }
                }
                npcs.append(npc)
            
            app.logger.info(f"Retrieved {len(npcs)} NPCs for zone: {zone_short_name}")
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        return jsonify({
            'zone': zone_short_name,
            'npcs': npcs,
            'count': len(npcs)
        })
        
    except Exception as e:
        app.logger.error(f"Error getting NPCs for zone {zone_short_name}: {e}")
        return jsonify({'error': f'Failed to get zone NPCs: {str(e)}'}), 500


def get_cursor_value(cursor_row, index=0):
    """Helper to extract values from cursor results regardless of format"""
    if cursor_row is None:
        return None
    if isinstance(cursor_row, dict):
        keys = list(cursor_row.keys())
        return cursor_row[keys[index]] if index < len(keys) else None
    elif isinstance(cursor_row, (list, tuple)):
        return cursor_row[index] if index < len(cursor_row) else None
    else:
        return cursor_row if index == 0 else None

@app.route('/api/zone-items-debug/<zone_short_name>', methods=['GET'])
def debug_zone_items(zone_short_name):
    """Simple debug to check each step of the zone items query"""
    if not zone_short_name:
        return jsonify({'error': 'Zone short name is required'}), 400
    
    cursor = None
    conn = None
    
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            return jsonify({'error': error or 'Database not connected'}), 503
            
        cursor = conn.cursor()
        
        # Just run each query step and show results as simple counts
        results = {}
        
        # Step 1: Test spawn2 directly with zone name (same as working NPC query)
        cursor.execute("SELECT COUNT(*) FROM spawn2 WHERE zone = %s", (zone_short_name,))
        spawn2_count = get_cursor_value(cursor.fetchone())
        results['spawn2_count'] = spawn2_count
        
        if spawn2_count == 0:
            results['message'] = 'No spawn2 entries found for this zone'
            return jsonify(results)
        
        # Step 2: Count spawnentry connections
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            WHERE s2.zone = %s
        """, (zone_short_name,))
        spawnentry_count = get_cursor_value(cursor.fetchone())
        results['spawnentry_count'] = spawnentry_count
        
        if spawnentry_count == 0:
            results['message'] = 'No spawnentry connections found'
            return jsonify(results)
        
        # Step 3: Count NPC connections
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            JOIN npc_types nt ON se.npcID = nt.id
            WHERE s2.zone = %s
        """, (zone_short_name,))
        npc_count = get_cursor_value(cursor.fetchone())
        results['npc_count'] = npc_count
        
        if npc_count == 0:
            results['message'] = 'No NPC connections found'
            return jsonify(results)
        
        # Step 4: Count NPCs with loot tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            JOIN npc_types nt ON se.npcID = nt.id
            WHERE s2.zone = %s AND nt.loottable_id > 0
        """, (zone_short_name,))
        loot_npc_count = get_cursor_value(cursor.fetchone())
        results['npcs_with_loot'] = loot_npc_count
        
        if loot_npc_count == 0:
            results['message'] = 'NPCs found but none have loot tables'
            return jsonify(results)
        
        # Step 5: Count loottable entries
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            JOIN npc_types nt ON se.npcID = nt.id
            JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
            WHERE s2.zone = %s AND nt.loottable_id > 0
        """, (zone_short_name,))
        loottable_count = get_cursor_value(cursor.fetchone())
        results['loottable_entries'] = loottable_count
        
        if loottable_count == 0:
            results['message'] = 'NPCs with loot tables found but no loottable_entries'
            return jsonify(results)
        
        # Step 6: Count lootdrop entries  
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            JOIN npc_types nt ON se.npcID = nt.id
            JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
            JOIN lootdrop_entries lde ON lte.lootdrop_id = lde.lootdrop_id
            WHERE s2.zone = %s AND nt.loottable_id > 0
        """, (zone_short_name,))
        lootdrop_count = get_cursor_value(cursor.fetchone())
        results['lootdrop_entries'] = lootdrop_count
        
        if lootdrop_count == 0:
            results['message'] = 'Loottable entries found but no lootdrop_entries'
            return jsonify(results)
        
        # Step 7: Count final items
        cursor.execute("""
            SELECT COUNT(*) 
            FROM spawn2 s2 
            JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID 
            JOIN npc_types nt ON se.npcID = nt.id
            JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
            JOIN lootdrop_entries lde ON lte.lootdrop_id = lde.lootdrop_id
            JOIN items ON lde.item_id = items.id
            WHERE s2.zone = %s AND nt.loottable_id > 0
            AND items.Name IS NOT NULL AND items.Name != ''
        """, (zone_short_name,))
        items_count = get_cursor_value(cursor.fetchone())
        results['final_items'] = items_count
        
        if items_count == 0:
            results['message'] = 'All joins successful but no valid items found'
        else:
            results['message'] = f'Success! Found {items_count} items'
        
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f"Debug failed for {zone_short_name}: {e}")
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/zone-items/<zone_short_name>', methods=['GET'])
def get_zone_items(zone_short_name):
    """
    Get all items that drop from NPCs in a specific zone.
    Returns unique items with drop information for the zone page items list.
    """
    if not zone_short_name:
        return jsonify({'error': 'Zone short name is required'}), 400
    
    cursor = None
    conn = None
    try:
        conn, db_type, error = get_eqemu_db_connection()
        if not conn:
            return jsonify({'error': error or 'Database not connected'}), 503
            
        cursor = conn.cursor()
        items = []
        
        # Debug: First check if zone exists
        cursor.execute("SELECT zoneidnumber, short_name, long_name FROM zone WHERE short_name = %s", (zone_short_name,))
        zone_info = cursor.fetchone()
        
        if not zone_info:
            app.logger.error(f"Zone '{zone_short_name}' not found in database")
            return jsonify({'error': f'Zone {zone_short_name} not found'}), 404
        
        app.logger.info(f"Found zone: {zone_info}")
        
        # Use optimized single query approach for maximum performance
        # This eliminates the N+1 query problem by joining all tables at once
        import time
        start_time = time.time()
        
        optimized_query = """
        SELECT DISTINCT 
            items.id, 
            items.Name, 
            items.icon, 
            items.itemtype
        FROM spawn2 s2
        JOIN spawnentry se ON s2.spawngroupID = se.spawngroupID  
        JOIN npc_types nt ON se.npcID = nt.id
        JOIN loottable_entries lte ON nt.loottable_id = lte.loottable_id
        JOIN lootdrop_entries lde ON lte.lootdrop_id = lde.lootdrop_id
        JOIN items ON lde.item_id = items.id
        WHERE s2.zone = %s
        AND nt.loottable_id > 0
        AND items.Name IS NOT NULL
        AND items.Name != ''
        ORDER BY items.Name
        """
        
        cursor.execute(optimized_query, (zone_short_name,))
        item_results = cursor.fetchall()
        query_time = time.time() - start_time
        
        # Format results
        items = []
        for item_row in item_results:
            items.append({
                'id': get_cursor_value(item_row, 0),
                'name': get_cursor_value(item_row, 1),
                'icon': get_cursor_value(item_row, 2) or 0,
                'item_type': get_cursor_value(item_row, 3) or 0
            })
        
        app.logger.info(f"Retrieved {len(items)} items for zone: {zone_short_name} in {query_time*1000:.1f}ms using optimized single query")
        
    except Exception as e:
        app.logger.error(f"Error getting items for zone {zone_short_name}: {e}")
        return jsonify({'error': f'Failed to get zone items: {str(e)}'}), 500
    
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
    
    return jsonify({
        'zone': zone_short_name,
        'items': items,
        'count': len(items)
    })


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