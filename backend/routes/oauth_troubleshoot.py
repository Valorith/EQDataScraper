"""
OAuth Troubleshooting and Enhanced Error Handling
This module provides improved OAuth error handling and diagnostics for production issues.
"""

from flask import Blueprint, request, jsonify, g
from utils.oauth import GoogleOAuth, oauth_storage
from utils.jwt_utils import create_error_response, create_success_response
import os
import logging
import traceback

logger = logging.getLogger(__name__)

oauth_troubleshoot_bp = Blueprint('oauth_troubleshoot', __name__)

def safe_log(message):
    """Safely log messages without causing errors in production."""
    try:
        print(message)
        logger.info(message)
    except:
        pass

@oauth_troubleshoot_bp.route('/auth/google/callback-enhanced', methods=['POST'])
def google_callback_enhanced():
    """
    Enhanced OAuth callback with better error handling and diagnostics.
    This temporarily replaces the main callback for troubleshooting.
    """
    try:
        safe_log("[Enhanced OAuth] Starting callback processing")
        
        # Log all request details for debugging
        safe_log(f"[Enhanced OAuth] Request headers: {dict(request.headers)}")
        safe_log(f"[Enhanced OAuth] Request method: {request.method}")
        safe_log(f"[Enhanced OAuth] Request URL: {request.url}")
        safe_log(f"[Enhanced OAuth] Request args: {dict(request.args)}")
        
        # Get request data with better error handling
        try:
            data = request.get_json()
            if not data:
                safe_log("[Enhanced OAuth] No JSON data in request")
                return create_error_response("Missing request data", 400)
            
            safe_log(f"[Enhanced OAuth] JSON data received: {list(data.keys())}")
        except Exception as e:
            safe_log(f"[Enhanced OAuth] Failed to parse JSON: {str(e)}")
            return create_error_response(f"Invalid JSON data: {str(e)}", 400)
        
        # Extract and validate parameters
        code = data.get('code')
        state = data.get('state')
        
        safe_log(f"[Enhanced OAuth] Code present: {bool(code)}")
        safe_log(f"[Enhanced OAuth] State present: {bool(state)}")
        safe_log(f"[Enhanced OAuth] State value: {state}")
        
        if not code:
            return create_error_response("Missing authorization code", 400)
        
        if not state:
            return create_error_response("Missing state parameter", 400)
        
        # Check OAuth storage with detailed logging
        safe_log(f"[Enhanced OAuth] Checking stored state for: {state}")
        
        try:
            stored_state = oauth_storage.get_oauth_state(state)
            safe_log(f"[Enhanced OAuth] Stored state found: {bool(stored_state)}")
            
            if stored_state:
                safe_log(f"[Enhanced OAuth] Stored state keys: {list(stored_state.keys())}")
                safe_log(f"[Enhanced OAuth] Code verifier present: {bool(stored_state.get('code_verifier'))}")
            
            # Get current storage keys for debugging
            if hasattr(oauth_storage, '_storage'):
                storage_keys = list(oauth_storage._storage.keys())
                safe_log(f"[Enhanced OAuth] Current storage keys: {storage_keys}")
                safe_log(f"[Enhanced OAuth] Storage size: {len(storage_keys)}")
            
        except Exception as e:
            safe_log(f"[Enhanced OAuth] Error accessing stored state: {str(e)}")
            return create_error_response(f"State storage error: {str(e)}", 500)
        
        if not stored_state:
            # Provide more helpful error message
            error_msg = (
                "Invalid or expired state parameter. This usually happens when:\n"
                "1. The login process took too long (state expires)\n"
                "2. Browser cookies are disabled\n"
                "3. The page was refreshed during OAuth flow\n"
                "4. Server was restarted during login\n\n"
                "Please try signing in again."
            )
            return create_error_response(error_msg, 400)
        
        # Clean up used state
        oauth_storage.remove_oauth_state(state)
        safe_log(f"[Enhanced OAuth] Cleaned up state: {state}")
        
        # Initialize Google OAuth with environment variable logging
        try:
            safe_log("[Enhanced OAuth] Initializing GoogleOAuth")
            safe_log(f"[Enhanced OAuth] OAUTH_REDIRECT_URI: {os.environ.get('OAUTH_REDIRECT_URI', 'NOT_SET')}")
            safe_log(f"[Enhanced OAuth] FRONTEND_URL: {os.environ.get('FRONTEND_URL', 'NOT_SET')}")
            safe_log(f"[Enhanced OAuth] RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT', 'NOT_SET')}")
            
            google_oauth = GoogleOAuth()
            safe_log(f"[Enhanced OAuth] GoogleOAuth initialized with redirect_uri: {google_oauth.redirect_uri}")
            
        except Exception as e:
            safe_log(f"[Enhanced OAuth] Failed to initialize GoogleOAuth: {str(e)}")
            return create_error_response(f"OAuth configuration error: {str(e)}", 500)
        
        # Override redirect URI for production if needed
        origin = request.headers.get('Origin', '')
        safe_log(f"[Enhanced OAuth] Request origin: {origin}")
        
        if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
            frontend_url = os.environ.get('FRONTEND_URL', 'https://eqdatascraper-frontend-production.up.railway.app')
            frontend_url = frontend_url.rstrip('/')
            google_oauth.redirect_uri = f"{frontend_url}/auth/callback"
            safe_log(f"[Enhanced OAuth] Production redirect override: {google_oauth.redirect_uri}")
        
        # Exchange code for tokens with enhanced error handling
        try:
            safe_log("[Enhanced OAuth] Starting token exchange")
            
            code_verifier = stored_state.get('code_verifier')
            if not code_verifier:
                return create_error_response("Missing code verifier in stored state", 400)
            
            # Call the token exchange
            token_data = google_oauth.exchange_code_for_tokens(code, code_verifier)
            safe_log("[Enhanced OAuth] Token exchange successful")
            
            # The rest of the callback logic would go here...
            # For now, return success with diagnostic info
            return create_success_response({
                'message': 'Enhanced OAuth callback successful',
                'token_exchange': 'success',
                'redirect_uri_used': google_oauth.redirect_uri,
                'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')
            })
            
        except Exception as e:
            safe_log(f"[Enhanced OAuth] Token exchange failed: {str(e)}")
            safe_log(f"[Enhanced OAuth] Token exchange traceback: {traceback.format_exc()}")
            return create_error_response(f"Token exchange failed: {str(e)}", 500)
            
    except Exception as e:
        safe_log(f"[Enhanced OAuth] Unexpected error: {str(e)}")
        safe_log(f"[Enhanced OAuth] Full traceback: {traceback.format_exc()}")
        return create_error_response(f"OAuth callback failed: {str(e)}", 500)