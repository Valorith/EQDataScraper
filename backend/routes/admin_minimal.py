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
    """Return empty endpoint metrics when OAuth is disabled."""
    return jsonify({
        'success': True,
        'data': {
            'endpoints': [],
            'message': 'OAuth is disabled - endpoint metrics not available'
        }
    })

@admin_minimal_bp.route('/admin/system/logs', methods=['GET', 'OPTIONS'])
def system_logs():
    """Return real search logs even when OAuth is disabled."""
    print("DEBUG: admin_minimal.system_logs() called")
    try:
        # Access system_metrics from the Flask app context
        from flask import current_app
        
        # Get system_metrics from the app's globals or blueprint
        system_metrics = None
        try:
            # Try to get system_metrics from the main admin blueprint
            import sys
            if 'routes.admin' in sys.modules:
                admin_module = sys.modules['routes.admin']
                if hasattr(admin_module, 'system_metrics'):
                    system_metrics = admin_module.system_metrics
        except Exception as e:
            print(f"Could not access system_metrics from admin module: {e}")
        
        # Get real logs from system_metrics
        real_logs = []
        if system_metrics and 'error_log' in system_metrics and system_metrics['error_log']:
            for i, log_entry in enumerate(system_metrics['error_log']):
                real_logs.append({
                    'id': i + 1,
                    'timestamp': log_entry['timestamp'],
                    'level': log_entry['level'],
                    'message': log_entry['message'],
                    'source': log_entry['source'],
                    'details': log_entry.get('details', {})
                })
        
        # If no real logs, show a helpful message
        if not real_logs:
            real_logs = [
                {
                    'id': 1,
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': 'No search events logged yet - try searching for items or spells',
                    'source': 'system',
                    'details': {}
                }
            ]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': real_logs,
                'total': len(real_logs),
                'message': f'Search events available (OAuth disabled but monitoring active) - {len(real_logs)} events found'
            }
        })
        
    except Exception as e:
        # Fallback to minimal logs if there's an error
        return jsonify({
            'success': True,
            'data': {
                'logs': [
                    {
                        'id': 1,
                        'timestamp': datetime.now().isoformat(),
                        'level': 'error',
                        'message': f'Error accessing search logs: {str(e)}',
                        'source': 'admin_minimal',
                        'details': {}
                    }
                ],
                'total': 1,
                'message': 'OAuth is disabled - error accessing search logs'
            }
        })

@admin_minimal_bp.route('/admin/logs', methods=['GET', 'OPTIONS'])
def logs():
    """Return minimal logs when OAuth is disabled (alternative endpoint)."""
    return system_logs()

@admin_minimal_bp.route('/admin/logs/clear', methods=['POST', 'OPTIONS'])
def clear_logs():
    """Clear logs operation when OAuth is disabled."""
    return jsonify({
        'success': False,
        'message': 'Log clearing requires OAuth to be enabled',
        'error': 'OAuth is disabled - cannot clear system logs'
    }), 403