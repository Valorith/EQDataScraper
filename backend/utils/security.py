"""
Security utilities for input validation and sanitization
"""

import re
from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
from datetime import datetime, timedelta

# Rate limiting storage
rate_limit_storage = defaultdict(list)

def sanitize_search_input(text, max_length=100):
    """
    Sanitize search input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # Trim to max length
    text = str(text)[:max_length]
    
    # Remove any HTML/script tags (simple regex-based approach)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove potentially dangerous SQL characters while preserving legitimate search chars
    # Allow alphanumeric, spaces, hyphens, apostrophes (for item names like "Ghoul's Heart")
    text = re.sub(r'[^\w\s\-\']', '', text)
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def validate_numeric_input(value, min_val=0, max_val=999999, default=None):
    """
    Validate and sanitize numeric input.
    
    Args:
        value: Input value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value if validation fails
        
    Returns:
        Validated integer or default value
    """
    if value is None or value == '':
        return default
    
    try:
        # Handle string inputs
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ['nan', 'null', 'undefined', '']:
                return default
        
        # Convert to integer
        num_value = int(value)
        
        # Validate range
        if num_value < min_val or num_value > max_val:
            return default
            
        return num_value
    except (ValueError, TypeError):
        return default

def validate_json_filters(filters_json, max_filters=10):
    """
    Validate and sanitize JSON filter data.
    
    Args:
        filters_json: JSON string of filters
        max_filters: Maximum number of filters allowed
        
    Returns:
        Dictionary with keys:
            - is_valid (bool): Whether validation succeeded
            - filters (list): List of validated filter dictionaries (if valid)
            - error (str): Error message (if invalid)
    """
    if not filters_json:
        return {"is_valid": True, "filters": []}
    
    try:
        import json
        filters = json.loads(filters_json)
        
        # Ensure it's a list
        if not isinstance(filters, list):
            return {
                "is_valid": False,
                "error": "Filters must be a JSON array"
            }
        
        # Check max filters limit
        if len(filters) > max_filters:
            return {
                "is_valid": False,
                "error": f"Maximum {max_filters} filters allowed"
            }
        
        # Define field categories for validation
        text_fields = {'loretext'}
        numeric_fields = {'price', 'weight', 'size', 'damage', 'delay', 'ac', 'hp', 'mana', 
                         'str', 'sta', 'agi', 'dex', 'wis', 'int', 'cha', 
                         'mr', 'fr', 'cr', 'dr', 'pr', 'reqlevel', 'reclevel'}
        boolean_fields = {'magic', 'lore', 'lore_flag', 'nodrop', 'norent', 'artifact'}
        effect_fields = {'clickeffect', 'proceffect', 'worneffect', 'focuseffect'}
        
        # All allowed fields
        allowed_fields = text_fields | numeric_fields | boolean_fields | effect_fields | {'slots'}
        
        # Operators by field type
        text_operators = {'contains', 'equals', 'not equals', 'starts with', 'ends with'}
        numeric_operators = {'equals', 'not equals', 'greater than', 'less than', 'between'}
        boolean_operators = {'is'}
        effect_operators = {'exists'}
        slot_operators = {'includes'}
        
        # Validate each filter
        validated_filters = []
        
        for i, filter_item in enumerate(filters):
            if not isinstance(filter_item, dict):
                return {
                    "is_valid": False,
                    "error": f"Filter at index {i} must be an object"
                }
                
            field = filter_item.get('field', '')
            operator = filter_item.get('operator', '')
            
            # Check for missing required fields
            if not field or not operator:
                return {
                    "is_valid": False,
                    "error": f"Missing required filter fields at index {i}"
                }
            
            # Validate field
            if field not in allowed_fields:
                return {
                    "is_valid": False,
                    "error": f"Invalid field '{field}' at index {i}"
                }
            
            # Validate operator based on field type
            valid_operator = False
            if field in text_fields and operator in text_operators:
                valid_operator = True
            elif field in numeric_fields and operator in numeric_operators:
                valid_operator = True
            elif field in boolean_fields and operator in boolean_operators:
                valid_operator = True
            elif field in effect_fields and operator in effect_operators:
                valid_operator = True
            elif field == 'slots' and operator in slot_operators:
                valid_operator = True
                
            if not valid_operator:
                return {
                    "is_valid": False,
                    "error": f"Invalid operator '{operator}' for field '{field}'"
                }
            
            # Check for required value
            if operator != 'exists' and 'value' not in filter_item:
                return {
                    "is_valid": False,
                    "error": f"Missing required filter fields at index {i}"
                }
            
            # Special validation for 'between' operator
            if operator == 'between':
                value = filter_item.get('value')
                if not isinstance(value, list) or len(value) != 2:
                    return {
                        "is_valid": False,
                        "error": f"Between operator requires 2 numeric values"
                    }
                # Check if both values are numeric
                try:
                    float(value[0])
                    float(value[1])
                except (TypeError, ValueError):
                    return {
                        "is_valid": False,
                        "error": f"Between operator requires 2 numeric values"
                    }
            
            # Build validated filter
            validated_filter = {
                'field': field,
                'operator': operator
            }
            
            # Handle different value types
            if 'value' in filter_item:
                value = filter_item['value']
                
                # For between operator, keep as list
                if operator == 'between':
                    validated_filter['value'] = value
                elif field in numeric_fields and operator in numeric_operators:
                    # Numeric fields must have numeric values
                    if not isinstance(value, (int, float)):
                        try:
                            # Try to convert string numbers
                            validated_filter['value'] = float(value)
                        except (TypeError, ValueError):
                            return {
                                "is_valid": False,
                                "error": f"Field '{field}' must be numeric"
                            }
                    else:
                        validated_filter['value'] = value
                elif isinstance(value, (int, float, bool)):
                    validated_filter['value'] = value
                else:
                    # Sanitize string values
                    validated_filter['value'] = sanitize_search_input(
                        str(value), max_length=50
                    )
            
            # Handle 'value2' for backward compatibility
            if operator == 'between' and 'value2' in filter_item:
                validated_filter['value2'] = filter_item['value2']
            
            validated_filters.append(validated_filter)
        
        return {"is_valid": True, "filters": validated_filters}
        
    except json.JSONDecodeError as e:
        return {
            "is_valid": False,
            "error": f"Invalid JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Validation error: {str(e)}"
        }

def rate_limit_by_ip(requests_per_minute=30, requests_per_hour=300):
    """
    Rate limiting decorator for Flask routes.
    
    Args:
        requests_per_minute: Maximum requests allowed per minute
        requests_per_hour: Maximum requests allowed per hour
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            current_time = time.time()
            
            # Clean old entries
            rate_limit_storage[client_ip] = [
                timestamp for timestamp in rate_limit_storage[client_ip]
                if current_time - timestamp < 3600  # Keep last hour
            ]
            
            # Check rate limits
            timestamps = rate_limit_storage[client_ip]
            
            # Count requests in last minute
            minute_ago = current_time - 60
            recent_requests = sum(1 for ts in timestamps if ts > minute_ago)
            
            if recent_requests >= requests_per_minute:
                return jsonify({
                    'error': 'Rate limit exceeded. Please wait a moment before trying again.',
                    'retry_after': 60
                }), 429
            
            # Count requests in last hour
            hour_ago = current_time - 3600
            hourly_requests = sum(1 for ts in timestamps if ts > hour_ago)
            
            if hourly_requests >= requests_per_hour:
                return jsonify({
                    'error': 'Hourly rate limit exceeded. Please try again later.',
                    'retry_after': 3600
                }), 429
            
            # Add current request
            rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator

def validate_item_search_params(params):
    """
    Validate all item search parameters.
    
    Args:
        params: Dictionary of search parameters
        
    Returns:
        Dictionary of validated parameters
    """
    validated = {}
    
    # Sanitize text search query
    if 'q' in params:
        validated['q'] = sanitize_search_input(params.get('q', ''), max_length=100)
    
    # Validate numeric inputs
    validated['limit'] = validate_numeric_input(
        params.get('limit'), min_val=1, max_val=100, default=20
    )
    validated['offset'] = validate_numeric_input(
        params.get('offset'), min_val=0, max_val=10000, default=0
    )
    
    # Validate item type
    if 'type' in params:
        validated['type'] = validate_numeric_input(
            params.get('type'), min_val=0, max_val=100
        )
    
    # Validate class filter
    if 'class' in params:
        validated['class'] = validate_numeric_input(
            params.get('class'), min_val=0, max_val=999999
        )
    
    # Validate level filters
    if 'min_level' in params:
        validated['min_level'] = validate_numeric_input(
            params.get('min_level'), min_val=0, max_val=255
        )
    
    if 'max_level' in params:
        validated['max_level'] = validate_numeric_input(
            params.get('max_level'), min_val=0, max_val=255
        )
    
    # Validate JSON filters
    if 'filters' in params:
        filter_result = validate_json_filters(params.get('filters'))
        if filter_result['is_valid']:
            validated['filters'] = filter_result['filters']
        else:
            # Include empty filters list if validation fails
            validated['filters'] = []
    
    return validated