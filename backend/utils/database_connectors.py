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
    
    conn_params = {
        'host': config['host'],
        'port': int(config['port']),  # Ensure port is an integer
        'database': config['database'],
        'user': config['username'],
        'password': config['password'],
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    if config.get('use_ssl', True):
        # MySQL SSL configuration
        conn_params['ssl'] = {'ssl': True}
        
    return pymysql.connect(**conn_params)


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