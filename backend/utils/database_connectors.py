"""
Multi-database support for EQDataScraper.
Supports PostgreSQL, MySQL, and Microsoft SQL Server connections.
"""

import os
from urllib.parse import quote_plus, urlparse
from .query_tracker import create_tracked_connection


def get_database_connector(db_type, config, track_queries=True):
    """
    Get the appropriate database connector based on database type.
    
    Args:
        db_type: Type of database ('postgresql', 'mysql', 'mssql')
        config: Database configuration dict
        track_queries: Whether to track query metrics (default: True)
        
    Returns:
        Database connection object (optionally with query tracking)
    """
    if db_type == 'postgresql':
        conn = get_postgresql_connection(config)
    elif db_type == 'mysql':
        conn = get_mysql_connection(config)
    elif db_type == 'mssql':
        conn = get_mssql_connection(config)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    # Wrap connection with query tracking if enabled
    if track_queries:
        try:
            return create_tracked_connection(conn, db_type)
        except ImportError:
            # If tracking not available, return raw connection
            return conn
    
    return conn


def get_postgresql_connection(config):
    """Get PostgreSQL connection."""
    import psycopg2
    
    conn_params = {
        'host': config['host'],
        'port': int(config['port']),  # Ensure port is an integer
        'database': config['database'],
        'user': config['username'],
        'password': config['password']
    }
    
    if config.get('use_ssl', True):
        conn_params['sslmode'] = 'require'
    else:
        conn_params['sslmode'] = 'prefer'
        
    return psycopg2.connect(**conn_params)


def get_mysql_connection(config):
    """Get MySQL connection."""
    import pymysql
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Log connection attempt details
    logger.info(f"Attempting MySQL connection to {config['host']}:{config['port']}")
    
    # Test if we can resolve the host at all
    import socket
    try:
        # Try to resolve the hostname/IP
        addr_info = socket.getaddrinfo(config['host'], config['port'], socket.AF_UNSPEC, socket.SOCK_STREAM)
        logger.info(f"Socket address resolution successful: {addr_info[0] if addr_info else 'No results'}")
    except Exception as e:
        logger.error(f"Socket address resolution failed: {type(e).__name__}: {str(e)}")
        logger.error("This indicates a network-level issue preventing connection to the MySQL server")
    
    # Force string conversion for host to avoid any type issues
    host = str(config['host']).strip()
    port = int(config['port'])
    
    # Debug: Check for any hidden characters
    logger.info(f"MySQL connection params - host type: {type(host)}, host value: '{host}'")
    logger.info(f"MySQL connection params - host length: {len(host)}, repr: {repr(host)}")
    logger.info(f"MySQL connection params - port type: {type(port)}, port value: {port}")
    
    # Additional check - see if host has any non-printable characters
    import re
    if re.search(r'[^\x20-\x7E]', host):
        logger.warning(f"Host contains non-printable characters!")
        # Clean it
        host = re.sub(r'[^\x20-\x7E]', '', host)
        logger.info(f"Cleaned host: '{host}'")
    
    conn_params = {
        'host': host,
        'port': port,
        'database': config['database'],
        'user': config['username'],
        'password': config['password'],
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': 30  # Increase timeout to 30 seconds
    }
    
    # Try without SSL first if we're getting connection errors
    if config.get('use_ssl', True):
        # For now, disable SSL to test if that's the issue
        logger.warning("SSL requested but temporarily disabled for debugging")
        # conn_params['ssl'] = {}  # Commenting out SSL for now
    
    # Test direct socket connection first
    try:
        import socket
        logger.info("Testing direct socket connection before PyMySQL...")
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(5)
        test_result = test_sock.connect_ex((host, port))
        test_sock.close()
        if test_result == 0:
            logger.info(f"Direct socket connection successful to {host}:{port}")
        else:
            logger.error(f"Direct socket connection failed with code {test_result}")
    except Exception as e:
        logger.error(f"Socket test failed: {type(e).__name__}: {str(e)}")
    
    try:
        logger.info("Attempting MySQL connection...")
        logger.info(f"PyMySQL version: {pymysql.__version__}")
        conn = pymysql.connect(**conn_params)
        logger.info("MySQL connection successful!")
        return conn
    except Exception as e:
        logger.error(f"MySQL connection failed: {type(e).__name__}: {str(e)}")
        # Log the exact error for debugging
        if hasattr(e, 'args'):
            logger.error(f"Error args: {e.args}")
        raise


def get_mssql_connection(config):
    """Get Microsoft SQL Server connection."""
    import pyodbc
    
    # Build connection string for SQL Server
    driver = '{ODBC Driver 17 for SQL Server}'
    
    # Check for available drivers
    available_drivers = pyodbc.drivers()
    if 'ODBC Driver 17 for SQL Server' not in available_drivers:
        if 'ODBC Driver 18 for SQL Server' in available_drivers:
            driver = '{ODBC Driver 18 for SQL Server}'
        elif 'SQL Server' in available_drivers:
            driver = '{SQL Server}'
        else:
            # Try FreeTDS on Unix-like systems
            if 'FreeTDS' in available_drivers:
                driver = '{FreeTDS}'
            else:
                raise Exception(f"No suitable SQL Server driver found. Available drivers: {available_drivers}")
    
    # Build connection string
    conn_str = f'DRIVER={driver};SERVER={config["host"]},{config["port"]};DATABASE={config["database"]};UID={config["username"]};PWD={config["password"]}'
    
    if config.get('use_ssl', True):
        conn_str += ';Encrypt=yes;TrustServerCertificate=yes'
    else:
        conn_str += ';Encrypt=no'
        
    return pyodbc.connect(conn_str)


def build_connection_url(db_type, config):
    """
    Build a connection URL for the database.
    
    Args:
        db_type: Type of database
        config: Database configuration
        
    Returns:
        Connection URL string
    """
    username = quote_plus(config['username'])
    password = quote_plus(config['password'])
    host = config['host']
    port = config['port']
    database = config['database']
    
    if db_type == 'postgresql':
        sslmode = 'require' if config.get('use_ssl', True) else 'prefer'
        return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}&default_transaction_read_only=on"
    elif db_type == 'mysql':
        ssl_suffix = '?ssl=true' if config.get('use_ssl', True) else ''
        return f"mysql://{username}:{password}@{host}:{port}/{database}{ssl_suffix}"
    elif db_type == 'mssql':
        # For SQL Server, we'll store the pyodbc connection string format
        driver = 'ODBC+Driver+17+for+SQL+Server'
        encrypt = 'yes' if config.get('use_ssl', True) else 'no'
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={driver}&Encrypt={encrypt}&TrustServerCertificate=yes"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def test_database_query(connection, db_type):
    """
    Run a test query appropriate for the database type.
    
    Args:
        connection: Database connection
        db_type: Type of database
        
    Returns:
        Dict with test results
    """
    cursor = connection.cursor()
    
    # Get version
    if db_type == 'postgresql':
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
    elif db_type == 'mysql':
        cursor.execute('SELECT VERSION();')
        version = cursor.fetchone()['VERSION()']
    elif db_type == 'mssql':
        cursor.execute('SELECT @@VERSION;')
        version = cursor.fetchone()[0]
    else:
        version = 'Unknown'
    
    # Get current time
    if db_type == 'mssql':
        cursor.execute('SELECT GETDATE();')
        current_time = cursor.fetchone()[0]
    elif db_type == 'mysql':
        cursor.execute('SELECT NOW();')
        result = cursor.fetchone()
        current_time = result['NOW()'] if isinstance(result, dict) else result[0]
    else:
        cursor.execute('SELECT NOW();')
        current_time = cursor.fetchone()[0]
    
    # Check for EQEmu tables
    tables_info = {}
    
    if db_type == 'postgresql':
        # Check items table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'items'
            );
        """)
        tables_info['items_exists'] = cursor.fetchone()[0]
        
        # Check discovered_items table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'discovered_items'
            );
        """)
        tables_info['discovered_items_exists'] = cursor.fetchone()[0]
        
    elif db_type == 'mysql':
        # Check items table
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'items';
        """)
        tables_info['items_exists'] = cursor.fetchone()['COUNT(*)'] > 0
        
        # Check discovered_items table
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'discovered_items';
        """)
        tables_info['discovered_items_exists'] = cursor.fetchone()['COUNT(*)'] > 0
        
    elif db_type == 'mssql':
        # Check items table
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'items';
        """)
        tables_info['items_exists'] = cursor.fetchone()[0] > 0
        
        # Check discovered_items table
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'discovered_items';
        """)
        tables_info['discovered_items_exists'] = cursor.fetchone()[0] > 0
    
    # Try to count items if tables exist
    tables_info['items_accessible'] = False
    tables_info['items_count'] = 0
    tables_info['discovered_items_accessible'] = False
    tables_info['discovered_items_count'] = 0
    
    if tables_info.get('items_exists', False):
        try:
            cursor.execute("SELECT COUNT(*) FROM items")
            count = cursor.fetchone()
            if isinstance(count, dict):
                tables_info['items_count'] = count.get('COUNT(*)', 0)
            else:
                tables_info['items_count'] = count[0]
            tables_info['items_accessible'] = True
        except Exception as e:
            print(f"Could not access items table: {e}")
    
    if tables_info.get('discovered_items_exists', False):
        try:
            cursor.execute("SELECT COUNT(*) FROM discovered_items")
            count = cursor.fetchone()
            if isinstance(count, dict):
                tables_info['discovered_items_count'] = count.get('COUNT(*)', 0)
            else:
                tables_info['discovered_items_count'] = count[0]
            tables_info['discovered_items_accessible'] = True
        except Exception as e:
            print(f"Could not access discovered_items table: {e}")
    
    cursor.close()
    
    return {
        'version': version,
        'current_time': str(current_time),
        'tables': tables_info
    }