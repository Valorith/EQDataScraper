"""
OAuth Debug Route - Temporary diagnostic endpoint to troubleshoot OAuth issues.
This should be removed in production after debugging is complete.
"""

from flask import Blueprint, jsonify, request
import os
import logging

logger = logging.getLogger(__name__)

debug_oauth_bp = Blueprint('debug_oauth', __name__)

@debug_oauth_bp.route('/debug/oauth-config', methods=['GET'])
def debug_oauth_config():
    """
    Debug endpoint to check OAuth configuration.
    WARNING: This exposes configuration details - remove in production!
    """
    
    # Check environment variables
    config = {
        'GOOGLE_CLIENT_ID': {
            'exists': bool(os.environ.get('GOOGLE_CLIENT_ID')),
            'length': len(os.environ.get('GOOGLE_CLIENT_ID', '')),
            'starts_with': os.environ.get('GOOGLE_CLIENT_ID', '')[:20] + '...' if os.environ.get('GOOGLE_CLIENT_ID') else 'None'
        },
        'GOOGLE_CLIENT_SECRET': {
            'exists': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
            'length': len(os.environ.get('GOOGLE_CLIENT_SECRET', '')),
            'starts_with': '***SECRET***' if os.environ.get('GOOGLE_CLIENT_SECRET') else 'None'
        },
        'OAUTH_REDIRECT_URI': {
            'exists': bool(os.environ.get('OAUTH_REDIRECT_URI')),
            'value': os.environ.get('OAUTH_REDIRECT_URI', 'None'),
            'length': len(os.environ.get('OAUTH_REDIRECT_URI', ''))
        },
        'FRONTEND_URL': {
            'exists': bool(os.environ.get('FRONTEND_URL')),
            'value': os.environ.get('FRONTEND_URL', 'None')
        },
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'None'),
        'request_headers': {
            'origin': request.headers.get('Origin'),
            'referer': request.headers.get('Referer'),
            'host': request.headers.get('Host')
        }
    }
    
    # Check if OAuth configuration looks correct
    issues = []
    
    if not config['GOOGLE_CLIENT_ID']['exists']:
        issues.append('Missing GOOGLE_CLIENT_ID environment variable')
    
    if not config['GOOGLE_CLIENT_SECRET']['exists']:
        issues.append('Missing GOOGLE_CLIENT_SECRET environment variable')
        
    if not config['OAUTH_REDIRECT_URI']['exists']:
        issues.append('Missing OAUTH_REDIRECT_URI environment variable')
    else:
        redirect_uri = config['OAUTH_REDIRECT_URI']['value']
        if '/api/' in redirect_uri:
            issues.append('OAUTH_REDIRECT_URI points to backend API instead of frontend')
        if redirect_uri.endswith('/auth/callba'):
            issues.append('OAUTH_REDIRECT_URI appears truncated (missing "ck")')
    
    return jsonify({
        'success': True,
        'config': config,
        'issues': issues,
        'status': 'healthy' if not issues else 'issues_detected'
    })


@debug_oauth_bp.route('/debug/oauth-test', methods=['POST'])
def debug_oauth_test():
    """
    Test OAuth flow without actually redirecting.
    """
    try:
        from utils.oauth import GoogleOAuth
        
        google_oauth = GoogleOAuth()
        
        # Generate auth URL (method generates its own state and code_challenge)
        auth_data = google_oauth.get_authorization_url()
        
        auth_url = auth_data.get('auth_url')
        
        return jsonify({
            'success': True,
            'message': 'OAuth configuration appears valid',
            'auth_url_generated': bool(auth_url),
            'redirect_uri_used': google_oauth.redirect_uri,
            'client_id_configured': bool(google_oauth.client_id)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500