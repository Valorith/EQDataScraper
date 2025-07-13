"""
Development-only authentication routes for local testing.
NEVER deploy this to production - it bypasses all OAuth security!
"""

from flask import Blueprint, request, jsonify
from utils.jwt_utils import jwt_manager, create_success_response
import os

# Only create this blueprint if we're in development mode
def create_dev_auth_blueprint():
    """Create development auth blueprint only if conditions are met."""
    
    # CRITICAL: Multiple safety checks to ensure this NEVER runs in production
    
    # Check 1: Block all production environments
    if os.environ.get('FLASK_ENV') == 'production':
        return None
    
    # Check 2: Block Railway (cloud deployment)
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return None
    
    # Check 3: Block any cloud environment indicators
    cloud_indicators = ['HEROKU', 'AWS', 'AZURE', 'GCP', 'VERCEL', 'NETLIFY', 'DOCKER']
    if any(os.environ.get(indicator) for indicator in cloud_indicators):
        return None
    
    # Check 4: Require explicit dev auth flag
    if not os.environ.get('ENABLE_DEV_AUTH', 'false').lower() == 'true':
        return None
    
    # Check 5: Only allow on localhost/development URLs
    oauth_redirect = os.environ.get('OAUTH_REDIRECT_URI', '')
    if not any(host in oauth_redirect for host in ['localhost', '127.0.0.1']):
        return None
    
    # Check 6: Block if domain looks like production
    if any(domain in oauth_redirect for domain in ['.com', '.org', '.net', '.app', '.dev']):
        # Allow .dev domains only for localhost
        if '.dev' in oauth_redirect and 'localhost' not in oauth_redirect:
            return None
    
    dev_auth_bp = Blueprint('dev_auth', __name__)
    
    @dev_auth_bp.route('/api/auth/dev-login', methods=['POST'])
    def dev_login():
        """
        Development-only login endpoint that bypasses OAuth.
        
        Expected JSON payload:
        {
            "email": "test@example.com",  // Optional, defaults to test user
            "is_admin": false              // Optional, defaults to false
        }
        """
        # CRITICAL: Extra safety checks at runtime
        if (os.environ.get('FLASK_ENV') == 'production' or 
            os.environ.get('RAILWAY_ENVIRONMENT') or
            any(os.environ.get(indicator) for indicator in ['HEROKU', 'AWS', 'AZURE', 'GCP', 'VERCEL', 'NETLIFY', 'DOCKER'])):
            return jsonify({"error": "Not available in production"}), 404
            
        # Get request data
        data = request.get_json() or {}
        
        # Create a test user
        email = data.get('email', 'testuser@localhost.dev')
        is_admin = data.get('is_admin', False)
        
        # Generate a fake user ID based on email (must be integer)
        user_id = abs(hash(email)) % 1000000
        
        # Create test user data
        test_user = {
            'id': user_id,  # Integer ID
            'email': email,
            'first_name': 'Test',
            'last_name': 'User', 
            'avatar_url': f'https://ui-avatars.com/api/?name=Test+User&background=667eea&color=fff',
            'role': 'admin' if is_admin else 'user',
            'is_active': True,
            'google_id': f'dev_google_{user_id}',
            'display_name': None,
            'anonymous_mode': False,
            'avatar_class': None
        }
        
        # Create JWT tokens
        access_token = jwt_manager.create_access_token(
            user_id=user_id,
            user_email=email,
            user_role='admin' if is_admin else 'user'
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            user_id=user_id,
            session_token=f'dev_session_{user_id}'
        )
        
        # Default preferences
        preferences = {
            'theme_preference': 'auto',
            'results_per_page': 20,
            'default_class': None
        }
        
        return jsonify(create_success_response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': test_user,
            'preferences': preferences,
            'dev_mode_warning': 'This is a development-only login. Never use in production!'
        }, "Development login successful"))
    
    @dev_auth_bp.route('/api/auth/dev-status', methods=['GET'])
    def dev_auth_status():
        """Check if dev auth is enabled."""
        return jsonify({
            'dev_auth_enabled': True,
            'warning': 'Development authentication is enabled. This should NEVER be enabled in production!'
        })
    
    return dev_auth_bp