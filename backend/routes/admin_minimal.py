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
    return jsonify({
        'success': True,
        'data': {
            'performance': {
                'avg_response_time': 0,
                'error_rate': 0,
                'total_requests': 0
            },
            'system': {
                'cpu_percent': 0,
                'memory_percent': 0,
                'uptime_seconds': 0
            },
            'message': 'OAuth is disabled - limited metrics available'
        }
    })

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