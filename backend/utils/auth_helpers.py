"""
Authentication helper functions for protecting database operations.
"""

def is_dev_user(user_id):
    """
    Check if a user ID is from dev authentication.
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if this is a dev user, False otherwise
    """
    return str(user_id).startswith('dev_')


def block_dev_user_db_operations(func):
    """
    Decorator to prevent dev users from performing database operations.
    
    Usage:
        @block_dev_user_db_operations
        def create_user_preference(user_id, preference_data):
            # This will throw an error if user_id starts with 'dev_'
            ...
    """
    def wrapper(*args, **kwargs):
        # Check if first argument is a user_id
        if args and is_dev_user(args[0]):
            raise ValueError("Dev users cannot perform database operations")
        
        # Check kwargs for user_id
        if 'user_id' in kwargs and is_dev_user(kwargs['user_id']):
            raise ValueError("Dev users cannot perform database operations")
            
        return func(*args, **kwargs)
    
    return wrapper