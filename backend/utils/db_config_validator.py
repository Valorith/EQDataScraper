"""
Database Configuration Validator

Validates that the database URL matches individual environment variable components.
Helps identify configuration mismatches that could cause connection issues.
"""

import os
import logging
from urllib.parse import urlparse, unquote
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class DatabaseConfigValidator:
    """Validates database configuration consistency."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_errors = []
        self.validation_warnings = []
        self.config_sources = {}
        
    def _sanitize_value(self, value: Any) -> str:
        """Sanitize configuration value for comparison."""
        if value is None:
            return ''
        return str(value).strip()
        
    def _parse_database_url(self, url: str) -> Dict[str, str]:
        """Parse database URL into components."""
        try:
            parsed = urlparse(url)
            
            # Extract components
            scheme = parsed.scheme or ''
            username = unquote(parsed.username) if parsed.username else ''
            password = unquote(parsed.password) if parsed.password else ''
            hostname = parsed.hostname or ''
            port = str(parsed.port) if parsed.port else ''
            database = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else ''
            
            # Parse query parameters for SSL settings
            query_params = {}
            if parsed.query:
                for param in parsed.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        query_params[key] = value
                        
            return {
                'scheme': scheme,
                'username': username,
                'password': password,
                'host': hostname,
                'port': port,
                'database': database,
                'ssl': query_params.get('sslmode', ''),
                'query_params': query_params
            }
        except Exception as e:
            logger.error(f"Error parsing database URL: {e}")
            return {}
            
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate database configuration from all sources.
        
        Returns:
            Dict containing validation results and any errors/warnings
        """
        self.validation_errors = []
        self.validation_warnings = []
        self.config_sources = {}
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'config_comparison': {},
            'recommendations': []
        }
        
        # Get configuration from environment variables
        env_config = {
            'EQEMU_DATABASE_URL': os.environ.get('EQEMU_DATABASE_URL', ''),
            'EQEMU_DATABASE_TYPE': os.environ.get('EQEMU_DATABASE_TYPE', ''),
            'EQEMU_DATABASE_HOST': os.environ.get('EQEMU_DATABASE_HOST', ''),
            'EQEMU_DATABASE_PORT': os.environ.get('EQEMU_DATABASE_PORT', ''),
            'EQEMU_DATABASE_NAME': os.environ.get('EQEMU_DATABASE_NAME', ''),
            'EQEMU_DATABASE_USER': os.environ.get('EQEMU_DATABASE_USER', ''),
            'EQEMU_DATABASE_PW': os.environ.get('EQEMU_DATABASE_PW', ''),
            'EQEMU_DATABASE_SSL': os.environ.get('EQEMU_DATABASE_SSL', '')
        }
        
        # Check if we have a database URL
        db_url = env_config['EQEMU_DATABASE_URL']
        if not db_url:
            validation_result['warnings'].append({
                'field': 'EQEMU_DATABASE_URL',
                'message': 'No database URL configured',
                'severity': 'warning'
            })
            
            # Check if we have individual components
            if any([env_config['EQEMU_DATABASE_HOST'], 
                   env_config['EQEMU_DATABASE_NAME'],
                   env_config['EQEMU_DATABASE_USER']]):
                validation_result['recommendations'].append(
                    'Individual database components are set but no URL. Consider constructing URL from components.'
                )
        else:
            # Parse the URL
            url_components = self._parse_database_url(db_url)
            
            if not url_components:
                validation_result['errors'].append({
                    'field': 'EQEMU_DATABASE_URL',
                    'message': 'Failed to parse database URL',
                    'severity': 'error'
                })
                validation_result['valid'] = False
                return validation_result
                
            # Compare URL components with individual env vars
            comparisons = [
                ('host', url_components.get('host', ''), env_config['EQEMU_DATABASE_HOST'], 'EQEMU_DATABASE_HOST'),
                ('port', url_components.get('port', ''), env_config['EQEMU_DATABASE_PORT'], 'EQEMU_DATABASE_PORT'),
                ('database', url_components.get('database', ''), env_config['EQEMU_DATABASE_NAME'], 'EQEMU_DATABASE_NAME'),
                ('username', url_components.get('username', ''), env_config['EQEMU_DATABASE_USER'], 'EQEMU_DATABASE_USER'),
                ('password', url_components.get('password', ''), env_config['EQEMU_DATABASE_PW'], 'EQEMU_DATABASE_PW'),
            ]
            
            # Perform comparisons
            for field, url_value, env_value, env_name in comparisons:
                url_value_clean = self._sanitize_value(url_value)
                env_value_clean = self._sanitize_value(env_value)
                
                comparison = {
                    'field': field,
                    'url_value': url_value_clean,
                    'env_value': env_value_clean,
                    'env_name': env_name,
                    'match': url_value_clean == env_value_clean or (not url_value_clean and not env_value_clean)
                }
                
                validation_result['config_comparison'][field] = comparison
                
                # Check for mismatches
                if env_value_clean and url_value_clean and url_value_clean != env_value_clean:
                    validation_result['errors'].append({
                        'field': field,
                        'message': f'{env_name} mismatch: URL has "{url_value_clean}" but env has "{env_value_clean}"',
                        'severity': 'error',
                        'url_value': url_value_clean,
                        'env_value': env_value_clean
                    })
                    validation_result['valid'] = False
                elif env_value_clean and not url_value_clean:
                    validation_result['warnings'].append({
                        'field': field,
                        'message': f'{env_name} is set but not in URL',
                        'severity': 'warning',
                        'env_value': env_value_clean
                    })
                elif url_value_clean and not env_value_clean:
                    validation_result['warnings'].append({
                        'field': field,
                        'message': f'{field} in URL but {env_name} not set',
                        'severity': 'info',
                        'url_value': url_value_clean
                    })
                    
            # Check database type
            url_scheme = url_components.get('scheme', '')
            env_type = env_config['EQEMU_DATABASE_TYPE'].lower()
            
            if url_scheme and env_type:
                # Map URL schemes to database types
                scheme_to_type = {
                    'mysql': 'mysql',
                    'mysql+pymysql': 'mysql',
                    'postgresql': 'postgresql',
                    'postgres': 'postgresql'
                }
                
                url_type = scheme_to_type.get(url_scheme, url_scheme)
                
                if url_type != env_type:
                    validation_result['errors'].append({
                        'field': 'database_type',
                        'message': f'Database type mismatch: URL indicates {url_type} but EQEMU_DATABASE_TYPE is {env_type}',
                        'severity': 'error',
                        'url_value': url_type,
                        'env_value': env_type
                    })
                    validation_result['valid'] = False
                    
            # Check SSL settings
            env_ssl = env_config['EQEMU_DATABASE_SSL'].lower()
            url_ssl = url_components.get('ssl', '')
            
            if env_ssl and url_ssl:
                ssl_match = (env_ssl == 'true' and url_ssl in ['require', 'verify-full', 'verify-ca']) or \
                           (env_ssl == 'false' and url_ssl in ['disable', 'allow', ''])
                           
                if not ssl_match:
                    validation_result['warnings'].append({
                        'field': 'ssl',
                        'message': f'SSL configuration may differ: URL has {url_ssl or "not set"}, env has {env_ssl}',
                        'severity': 'warning'
                    })
                    
        # Add configuration source information
        validation_result['config_sources'] = {
            'url_configured': bool(db_url),
            'individual_components_configured': any([
                env_config['EQEMU_DATABASE_HOST'],
                env_config['EQEMU_DATABASE_NAME'],
                env_config['EQEMU_DATABASE_USER']
            ]),
            'from_persistent_storage': False  # Will be set by caller if applicable
        }
        
        # Add recommendations based on findings
        if validation_result['errors']:
            validation_result['recommendations'].append(
                'Fix configuration mismatches before attempting connection.'
            )
            
        if not db_url and validation_result['config_sources']['individual_components_configured']:
            # Construct URL from components
            host = env_config['EQEMU_DATABASE_HOST']
            port = env_config['EQEMU_DATABASE_PORT'] or '3306'
            database = env_config['EQEMU_DATABASE_NAME']
            username = env_config['EQEMU_DATABASE_USER']
            password = env_config['EQEMU_DATABASE_PW']
            db_type = env_config['EQEMU_DATABASE_TYPE'] or 'mysql'
            
            if host and database and username:
                suggested_url = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
                if env_config['EQEMU_DATABASE_SSL'].lower() == 'true':
                    suggested_url += "?sslmode=require"
                    
                validation_result['recommendations'].append(
                    f'Consider setting EQEMU_DATABASE_URL to: {suggested_url}'
                )
                
        return validation_result
        
    def validate_persistent_config(self, persistent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate persistent configuration against environment variables.
        
        Args:
            persistent_config: Configuration loaded from persistent storage
            
        Returns:
            Validation results
        """
        # First validate environment config
        result = self.validate_config()
        
        if not persistent_config:
            result['warnings'].append({
                'field': 'persistent_storage',
                'message': 'No persistent configuration found',
                'severity': 'info'
            })
            return result
            
        # Compare persistent config with environment
        persistent_url = persistent_config.get('production_database_url', '')
        env_url = os.environ.get('EQEMU_DATABASE_URL', '')
        
        if persistent_url and env_url and persistent_url != env_url:
            result['warnings'].append({
                'field': 'persistent_storage',
                'message': 'Persistent storage URL differs from environment URL',
                'severity': 'warning',
                'persistent_value': persistent_url[:50] + '...' if len(persistent_url) > 50 else persistent_url,
                'env_value': env_url[:50] + '...' if len(env_url) > 50 else env_url
            })
            
        result['config_sources']['from_persistent_storage'] = bool(persistent_url)
        
        return result
        
    def get_connection_string_from_components(self) -> Optional[str]:
        """
        Build a connection string from individual environment components.
        
        Returns:
            Connection string or None if components are missing
        """
        host = os.environ.get('EQEMU_DATABASE_HOST', '').strip()
        port = os.environ.get('EQEMU_DATABASE_PORT', '3306').strip()
        database = os.environ.get('EQEMU_DATABASE_NAME', '').strip()
        username = os.environ.get('EQEMU_DATABASE_USER', '').strip()
        password = os.environ.get('EQEMU_DATABASE_PW', '').strip()
        db_type = os.environ.get('EQEMU_DATABASE_TYPE', 'mysql').strip().lower()
        use_ssl = os.environ.get('EQEMU_DATABASE_SSL', 'false').strip().lower() == 'true'
        
        # Check required components
        if not all([host, database, username]):
            return None
            
        # Build connection string
        connection_string = f"{db_type}://{username}:{password}@{host}:{port}/{database}"
        
        if use_ssl:
            connection_string += "?sslmode=require"
            
        return connection_string


# Global validator instance
_validator = None


def get_validator() -> DatabaseConfigValidator:
    """Get the singleton validator instance."""
    global _validator
    if _validator is None:
        _validator = DatabaseConfigValidator()
    return _validator


def validate_database_config() -> Dict[str, Any]:
    """Validate current database configuration."""
    validator = get_validator()
    return validator.validate_config()


def validate_and_fix_config() -> Tuple[bool, Dict[str, Any]]:
    """
    Validate configuration and attempt to fix issues if possible.
    
    Returns:
        Tuple of (success, validation_result)
    """
    validator = get_validator()
    result = validator.validate_config()
    
    if not result['valid']:
        # Try to construct URL from components if missing
        if not os.environ.get('EQEMU_DATABASE_URL'):
            suggested_url = validator.get_connection_string_from_components()
            if suggested_url:
                logger.info(f"Constructed database URL from components: {suggested_url}")
                # Don't actually set it - just return the suggestion
                result['suggested_url'] = suggested_url
                result['fix_available'] = True
                
    return result['valid'], result