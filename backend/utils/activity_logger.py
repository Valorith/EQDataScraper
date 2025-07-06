"""
Activity logging utilities for tracking actions in app.py endpoints.
This module provides helper functions to log activities without modifying the main app.py file extensively.
"""

from models.activity import ActivityLog
from flask import g, request
import psycopg2
from typing import Optional, Dict, Any

def log_scrape_activity(action: str, class_name: Optional[str] = None, 
                       details: Optional[Dict[str, Any]] = None,
                       user_id: Optional[int] = None) -> None:
    """
    Log scraping-related activities.
    
    Args:
        action: The action type (e.g., 'scrape_start', 'scrape_complete', 'scrape_error')
        class_name: The class name being scraped (optional)
        details: Additional details about the activity
        user_id: User ID if authenticated (optional)
    """
    try:
        # Get database connection from Flask g object
        conn = getattr(g, 'db_connection', None)
        if not conn:
            return  # No database connection available
        
        activity_log = ActivityLog(conn)
        
        # Prepare details
        activity_details = details or {}
        if class_name:
            activity_details['class_name'] = class_name
        
        # Get user ID from JWT if available and not provided
        if user_id is None and hasattr(g, 'current_user'):
            user_id = g.current_user.get('id')
        
        # Log the activity
        activity_log.log_activity(
            action=action,
            user_id=user_id,
            resource_type=ActivityLog.RESOURCE_CLASS if class_name else ActivityLog.RESOURCE_CACHE,
            resource_id=class_name.lower() if class_name else 'all',
            details=activity_details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
    except Exception as e:
        # Don't let activity logging errors break the main functionality
        print(f"Error logging activity: {e}")

def log_cache_activity(action: str, details: Optional[Dict[str, Any]] = None,
                      user_id: Optional[int] = None) -> None:
    """
    Log cache-related activities.
    
    Args:
        action: The action type (e.g., 'cache_refresh', 'cache_clear', 'cache_save')
        details: Additional details about the activity
        user_id: User ID if authenticated (optional)
    """
    try:
        # Get database connection from Flask g object
        conn = getattr(g, 'db_connection', None)
        if not conn:
            return  # No database connection available
        
        activity_log = ActivityLog(conn)
        
        # Get user ID from JWT if available and not provided
        if user_id is None and hasattr(g, 'current_user'):
            user_id = g.current_user.get('id')
        
        # Log the activity
        activity_log.log_activity(
            action=action,
            user_id=user_id,
            resource_type=ActivityLog.RESOURCE_CACHE,
            resource_id='cache',
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
    except Exception as e:
        # Don't let activity logging errors break the main functionality
        print(f"Error logging cache activity: {e}")

def log_api_activity(action: str, resource_type: str, resource_id: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None,
                    user_id: Optional[int] = None) -> None:
    """
    Log general API activities.
    
    Args:
        action: The action type
        resource_type: The resource type (e.g., 'spell', 'user', 'system')
        resource_id: The resource ID (optional)
        details: Additional details about the activity
        user_id: User ID if authenticated (optional)
    """
    try:
        # Get database connection from Flask g object
        conn = getattr(g, 'db_connection', None)
        if not conn:
            return  # No database connection available
        
        activity_log = ActivityLog(conn)
        
        # Get user ID from JWT if available and not provided
        if user_id is None and hasattr(g, 'current_user'):
            user_id = g.current_user.get('id')
        
        # Log the activity
        activity_log.log_activity(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
    except Exception as e:
        # Don't let activity logging errors break the main functionality
        print(f"Error logging API activity: {e}")