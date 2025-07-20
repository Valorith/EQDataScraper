#!/usr/bin/env python3
"""
Enhanced EQDataScraper Service Monitor
Comprehensive monitoring with detailed diagnostics for backend unresponsiveness
"""

import os
import sys
import time
import json
import socket
import psutil
import subprocess
import argparse
import logging
import requests
import threading
import signal
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from collections import defaultdict, deque

class EnhancedServiceMonitor:
    def __init__(self, config_path: str = "config.json"):
        self.root_dir = Path(__file__).parent
        self.config_path = self.root_dir / config_path
        self.config = self._load_config()
        self.backend_port = self.config.get('backend_port', 5001)
        self.frontend_port = self.config.get('frontend_port', 3000)
        self.running = True
        self.recovery_attempts = {}
        self.last_check = {}
        
        # Enhanced monitoring data
        self.response_times = deque(maxlen=100)  # Last 100 response times
        self.error_history = deque(maxlen=50)    # Last 50 errors
        self.memory_history = deque(maxlen=60)   # Last 60 memory readings
        self.cpu_history = deque(maxlen=60)      # Last 60 CPU readings
        self.connection_history = deque(maxlen=50)  # Connection info
        self.restart_history = []                # All restart events
        
        # Thresholds for alerting
        self.max_response_time = 5.0  # seconds
        self.max_memory_percent = 80  # percent of system RAM
        self.max_cpu_percent = 90     # percent CPU usage
        self.max_consecutive_failures = 3
        self.consecutive_failures = 0
        
        # Setup enhanced logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup comprehensive logging with rotation"""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Main monitor log
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Separate loggers for different aspects
        self.perf_logger = logging.getLogger('performance')
        perf_handler = logging.FileHandler(log_dir / 'performance.log')
        perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.setLevel(logging.INFO)
        
        self.error_logger = logging.getLogger('errors')
        error_handler = logging.FileHandler(log_dir / 'errors.log')
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.error_logger.addHandler(error_handler)
        self.error_logger.setLevel(logging.WARNING)
        
        self.restart_logger = logging.getLogger('restarts')
        restart_handler = logging.FileHandler(log_dir / 'restarts.log')
        restart_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.restart_logger.addHandler(restart_handler)
        self.restart_logger.setLevel(logging.INFO)
        
    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def check_backend_health_detailed(self) -> Dict:
        """Comprehensive backend health check with detailed diagnostics"""
        start_time = time.time()
        result = {
            'healthy': False,
            'response_time': None,
            'status_code': None,
            'error': None,
            'process_info': None,
            'memory_usage': None,
            'cpu_usage': None,
            'connections': None,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # HTTP health check
            url = f"http://127.0.0.1:{self.backend_port}/api/health"
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            result['response_time'] = response_time
            result['status_code'] = response.status_code
            result['healthy'] = response.status_code == 200
            
            # Log slow responses
            if response_time > self.max_response_time:
                self.error_logger.warning(f"Slow backend response: {response_time:.2f}s (threshold: {self.max_response_time}s)")
            
            # Get process information
            result['process_info'] = self._get_backend_process_info()
            
            if result['process_info']:
                result['memory_usage'] = result['process_info']['memory_percent']
                result['cpu_usage'] = result['process_info']['cpu_percent']
                result['connections'] = len(result['process_info']['connections'])
                
                # Check resource usage
                if result['memory_usage'] > self.max_memory_percent:
                    self.error_logger.warning(f"High backend memory usage: {result['memory_usage']:.1f}% (threshold: {self.max_memory_percent}%)")
                
                if result['cpu_usage'] > self.max_cpu_percent:
                    self.error_logger.warning(f"High backend CPU usage: {result['cpu_usage']:.1f}% (threshold: {self.max_cpu_percent}%)")
            
        except requests.exceptions.Timeout:
            result['error'] = 'Request timeout'
            self.error_logger.error("Backend health check timed out")
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection refused'
            self.error_logger.error("Backend connection refused")
        except Exception as e:
            result['error'] = str(e)
            self.error_logger.error(f"Backend health check failed: {e}")
        
        # Store historical data
        self.response_times.append(result['response_time'])
        if result['memory_usage']:
            self.memory_history.append(result['memory_usage'])
        if result['cpu_usage']:
            self.cpu_history.append(result['cpu_usage'])
        if result['connections']:
            self.connection_history.append(result['connections'])
        
        # Log performance data
        self.perf_logger.info(
            f"Backend: healthy={result['healthy']}, "
            f"response_time={result['response_time']:.3f}s, "
            f"memory={result['memory_usage']:.1f}%, "
            f"cpu={result['cpu_usage']:.1f}%, "
            f"connections={result['connections']}"
        )
        
        return result
    
    def _get_backend_process_info(self) -> Optional[Dict]:
        """Get detailed information about the backend process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent', 'cpu_percent', 'connections']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'app.py' in cmdline and 'python' in proc.info['name'].lower():
                        # Get additional process info
                        process = psutil.Process(proc.info['pid'])
                        
                        return {
                            'pid': proc.info['pid'],
                            'memory_percent': proc.info['memory_percent'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'connections': proc.info['connections'] or [],
                            'num_threads': process.num_threads(),
                            'create_time': process.create_time(),
                            'status': process.status(),
                            'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
                        }
        except Exception as e:
            self.error_logger.error(f"Error getting backend process info: {e}")
        return None
    
    def detect_unresponsive_patterns(self) -> List[str]:
        """Analyze historical data to detect patterns that lead to unresponsiveness"""
        issues = []
        
        # Check for increasing response times
        if len(self.response_times) >= 10:
            recent_times = list(self.response_times)[-10:]
            valid_times = [t for t in recent_times if t is not None]
            if len(valid_times) >= 5:
                avg_recent = sum(valid_times) / len(valid_times)
                if avg_recent > self.max_response_time * 0.8:
                    issues.append(f"Response times trending high: {avg_recent:.2f}s average")
        
        # Check for memory growth
        if len(self.memory_history) >= 20:
            recent_memory = list(self.memory_history)[-20:]
            early_avg = sum(recent_memory[:10]) / 10
            late_avg = sum(recent_memory[-10:]) / 10
            if late_avg > early_avg * 1.2:  # 20% increase
                issues.append(f"Memory usage growing: {early_avg:.1f}% → {late_avg:.1f}%")
        
        # Check for connection buildup
        if len(self.connection_history) >= 10:
            recent_connections = list(self.connection_history)[-10:]
            if recent_connections and max(recent_connections) > 50:
                issues.append(f"High connection count: {max(recent_connections)} connections")
        
        # Check for consecutive failures
        if self.consecutive_failures >= 2:
            issues.append(f"Consecutive health check failures: {self.consecutive_failures}")
        
        return issues
    
    def diagnose_unresponsiveness(self) -> Dict:
        """Comprehensive diagnosis when backend becomes unresponsive"""
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'system_resources': self._get_system_resources(),
            'process_info': self._get_backend_process_info(),
            'network_info': self._check_network_status(),
            'recent_errors': list(self.error_history)[-10:],
            'patterns': self.detect_unresponsive_patterns(),
            'database_connections': self._check_database_connections()
        }
        
        # Log comprehensive diagnosis
        self.error_logger.error("BACKEND UNRESPONSIVE - DIAGNOSIS:")
        self.error_logger.error(f"System CPU: {diagnosis['system_resources']['cpu_percent']:.1f}%")
        self.error_logger.error(f"System Memory: {diagnosis['system_resources']['memory_percent']:.1f}%")
        self.error_logger.error(f"System Load: {diagnosis['system_resources']['load_average']}")
        
        if diagnosis['process_info']:
            self.error_logger.error(f"Backend PID: {diagnosis['process_info']['pid']}")
            self.error_logger.error(f"Backend Memory: {diagnosis['process_info']['memory_percent']:.1f}%")
            self.error_logger.error(f"Backend CPU: {diagnosis['process_info']['cpu_percent']:.1f}%")
            self.error_logger.error(f"Backend Threads: {diagnosis['process_info']['num_threads']}")
            self.error_logger.error(f"Backend Status: {diagnosis['process_info']['status']}")
        
        if diagnosis['patterns']:
            self.error_logger.error("Detected patterns:")
            for pattern in diagnosis['patterns']:
                self.error_logger.error(f"  - {pattern}")
        
        return diagnosis
    
    def _get_system_resources(self) -> Dict:
        """Get overall system resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'boot_time': psutil.boot_time()
        }
    
    def _check_network_status(self) -> Dict:
        """Check network connectivity and port status"""
        result = {
            'backend_port_listening': False,
            'can_connect_localhost': False,
            'active_connections': 0
        }
        
        try:
            # Check if backend port is listening
            for conn in psutil.net_connections():
                if conn.laddr.port == self.backend_port and conn.status == 'LISTEN':
                    result['backend_port_listening'] = True
                    break
            
            # Test socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result['can_connect_localhost'] = sock.connect_ex(('127.0.0.1', self.backend_port)) == 0
            sock.close()
            
            # Count active connections to backend port
            for conn in psutil.net_connections():
                if conn.laddr.port == self.backend_port:
                    result['active_connections'] += 1
                    
        except Exception as e:
            self.error_logger.error(f"Network status check failed: {e}")
        
        return result
    
    def _check_database_connections(self) -> Dict:
        """Check database connection status"""
        # This would need to be implemented based on your database setup
        # For now, return placeholder
        return {
            'status': 'unknown',
            'note': 'Database connection check not implemented'
        }
    
    def restart_backend_with_diagnosis(self) -> bool:
        """Restart backend with comprehensive logging and diagnosis"""
        restart_event = {
            'timestamp': datetime.now().isoformat(),
            'reason': 'unresponsive',
            'diagnosis': None,
            'success': False
        }
        
        # Perform diagnosis before restart
        restart_event['diagnosis'] = self.diagnose_unresponsiveness()
        
        self.restart_logger.info(f"RESTART INITIATED: {restart_event['timestamp']}")
        self.restart_logger.info(f"Reason: Backend unresponsive")
        
        try:
            # Kill existing backend processes
            killed_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'app.py' in cmdline and 'python' in proc.info['name'].lower():
                            self.restart_logger.info(f"Killing backend process PID: {proc.info['pid']}")
                            proc.kill()
                            killed_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if killed_processes:
                time.sleep(3)  # Wait for processes to die
                self.restart_logger.info(f"Killed {len(killed_processes)} backend processes")
            
            # Start new backend process
            backend_script = self.root_dir / "backend" / "app.py"
            env = os.environ.copy()
            env['PORT'] = str(self.backend_port)
            
            self.restart_logger.info("Starting new backend process...")
            process = subprocess.Popen(
                [sys.executable, str(backend_script)],
                cwd=str(self.root_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait and verify restart
            time.sleep(5)
            health_result = self.check_backend_health_detailed()
            restart_event['success'] = health_result['healthy']
            
            if restart_event['success']:
                self.restart_logger.info("Backend restart SUCCESSFUL")
                self.consecutive_failures = 0
            else:
                self.restart_logger.error("Backend restart FAILED - service still unhealthy")
            
        except Exception as e:
            restart_event['success'] = False
            self.restart_logger.error(f"Backend restart ERROR: {e}")
            self.restart_logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Store restart event
        self.restart_history.append(restart_event)
        
        return restart_event['success']
    
    def monitor_loop(self, interval: int = 30):
        """Enhanced monitoring loop with detailed diagnostics"""
        self.logger.info("Starting enhanced service monitoring...")
        self.logger.info(f"Backend port: {self.backend_port}")
        self.logger.info(f"Check interval: {interval} seconds")
        self.logger.info(f"Logs directory: {Path('logs').absolute()}")
        
        while self.running:
            try:
                # Comprehensive backend check
                health_result = self.check_backend_health_detailed()
                
                if health_result['healthy']:
                    self.consecutive_failures = 0
                    self.logger.info(f"Backend healthy - Response: {health_result['response_time']:.3f}s")
                else:
                    self.consecutive_failures += 1
                    self.error_history.append({
                        'timestamp': health_result['timestamp'],
                        'error': health_result['error'],
                        'status_code': health_result['status_code']
                    })
                    
                    self.logger.warning(f"Backend unhealthy (attempt {self.consecutive_failures}): {health_result['error']}")
                    
                    # Auto-restart if too many consecutive failures
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        self.logger.error(f"Backend failed {self.consecutive_failures} consecutive times - initiating restart")
                        if self.restart_backend_with_diagnosis():
                            self.logger.info("Backend restart successful")
                        else:
                            self.logger.error("Backend restart failed")
                
                # Sleep until next check
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitor stopped by user")
                break
            except Exception as e:
                self.error_logger.error(f"Monitor loop error: {e}")
                self.error_logger.error(f"Traceback: {traceback.format_exc()}")
                time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='Enhanced EQDataScraper Service Monitor')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    parser.add_argument('--config', default='config.json', help='Config file path')
    
    args = parser.parse_args()
    
    monitor = EnhancedServiceMonitor(args.config)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        monitor.logger.info("Received shutdown signal")
        monitor.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        monitor.monitor_loop(args.interval)
    except Exception as e:
        monitor.error_logger.error(f"Monitor crashed: {e}")
        monitor.error_logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()