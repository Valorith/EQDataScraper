"""
Minimal admin routes that work without OAuth authentication.
These provide basic functionality when OAuth is disabled.
"""

from flask import Blueprint, jsonify
import logging
from datetime import datetime

admin_minimal_bp = Blueprint('admin_minimal', __name__)
logger = logging.getLogger(__name__)

@admin_minimal_bp.route('/admin/stats', methods=['GET', 'OPTIONS'])
def admin_stats():
    """Return minimal admin stats when OAuth is disabled."""
    return jsonify({
        'success': True,
        'data': {
            'users': {
                'total': 0,
                'active_today': 0,
                'admins': 0
            },
            'totalUsers': 0,
            'activeToday': 0,
            'adminUsers': 0,
            'message': 'OAuth is disabled - no user data available'
        }
    })

@admin_minimal_bp.route('/admin/activities', methods=['GET', 'OPTIONS'])
def admin_activities():
    """Return empty activities when OAuth is disabled."""
    return jsonify({
        'success': True,
        'data': {
            'activities': [],
            'total': 0,
            'page': 1,
            'per_page': 10,
            'message': 'OAuth is disabled - no activity data available'
        }
    })

@admin_minimal_bp.route('/admin/database/config', methods=['GET', 'OPTIONS'])
def database_config():
    """Return database configuration status."""
    return jsonify({
        'success': True,
        'data': {
            'database': {
                'connected': False,
                'host': None,
                'port': None,
                'database': None,
                'username': None,
                'db_type': None,
                'use_ssl': True,
                'status': 'not_configured',
                'connection_type': 'none'
            },
            'storage_info': {
                'config_source': 'none',
                'storage_available': False,
                'directory_writable': False,
                'data_directory': None
            },
            'message': 'Database configuration requires OAuth to be enabled'
        }
    })

@admin_minimal_bp.route('/admin/system/metrics', methods=['GET', 'OPTIONS'])
def system_metrics():
    """Return minimal system metrics when OAuth is disabled."""
    print("DEBUG: admin_minimal system_metrics endpoint called")
    import psutil
    import time
    
    # Get actual system metrics
    try:
        print("DEBUG: Getting CPU percent...")
        cpu_percent = psutil.cpu_percent(interval=0.1)
        print(f"DEBUG: CPU percent = {cpu_percent}")
        memory = psutil.virtual_memory()
        print(f"DEBUG: Memory percent = {memory.percent}")
        process = psutil.Process()
        uptime = time.time() - process.create_time()
        print(f"DEBUG: Uptime = {uptime}")
    except Exception as e:
        print(f"DEBUG: Error getting metrics: {e}")
        cpu_percent = 0
        memory = type('obj', (object,), {'percent': 0, 'used': 0, 'total': 0})
        uptime = 0
    
    print("DEBUG: Creating response...")
    response_data = {
        'success': True,
        'data': {
            'performance': {
                'avg_response_time': 50,  # Default 50ms
                'error_rate': 0,
                'total_requests': 0
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_total': memory.total,
                'uptime_seconds': int(uptime)
            },
            'message': 'OAuth is disabled - limited metrics available'
        }
    }
    print(f"DEBUG: Response data created: {response_data}")
    
    try:
        result = jsonify(response_data)
        print("DEBUG: jsonify successful")
        return result
    except Exception as e:
        print(f"DEBUG: jsonify failed: {e}")
        raise

@admin_minimal_bp.route('/admin/database/test', methods=['POST', 'OPTIONS'])
def test_database():
    """Database testing requires OAuth."""
    return jsonify({
        'success': False,
        'message': 'Database configuration requires OAuth to be enabled',
        'error': {
            'error_type': 'auth_required',
            'error_message': 'Enable OAuth to configure database connections'
        }
    }), 403

@admin_minimal_bp.route('/admin/database/stored-config', methods=['GET', 'OPTIONS'])
def stored_config():
    """Stored config requires OAuth."""
    return jsonify({
        'success': False,
        'message': 'Database configuration requires OAuth to be enabled'
    }), 403

@admin_minimal_bp.route('/admin/network/test', methods=['POST', 'OPTIONS'])
def network_test():
    """Network testing requires OAuth."""
    return jsonify({
        'success': False,
        'message': 'Network testing requires OAuth to be enabled'
    }), 403

@admin_minimal_bp.route('/admin/database/diagnostics', methods=['GET', 'OPTIONS'])
def database_diagnostics():
    """Database diagnostics requires OAuth."""
    return jsonify({
        'success': False,
        'message': 'Database diagnostics requires OAuth to be enabled'
    }), 403

@admin_minimal_bp.route('/admin/system/endpoints', methods=['GET', 'OPTIONS'])
def system_endpoints():
    """Return minimal endpoint metrics when OAuth is disabled."""
    return jsonify({
        'success': True,
        'data': {
            'endpoints': [
                {
                    'endpoint': 'GET /api/health',
                    'total_calls': 100,
                    'avg_response_time': 50,
                    'success_rate': 100,
                    'last_called': datetime.now().isoformat(),
                    'status': 'healthy'
                },
                {
                    'endpoint': 'GET /api/items/search',
                    'total_calls': 50,
                    'avg_response_time': 200,
                    'success_rate': 100,
                    'last_called': datetime.now().isoformat(),
                    'status': 'healthy'
                }
            ],
            'message': 'OAuth is disabled - showing sample data only'
        }
    })

@admin_minimal_bp.route('/admin/system/logs', methods=['GET', 'OPTIONS'])
def system_logs():
    """Return minimal logs when OAuth is disabled."""
    return jsonify({
        'success': True,
        'data': {
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'OAuth is disabled - system logs not available',
                    'source': 'admin_minimal'
                }
            ],
            'total': 1,
            'message': 'OAuth is disabled - system logs not available'
        }
    })