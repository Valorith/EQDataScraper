#!/usr/bin/env python3
"""
Backend connection monitoring script.
This script monitors backend connections and helps identify hanging issues.
"""
import os
import time
import threading
import psutil
import signal
from datetime import datetime
from collections import defaultdict, deque

class ConnectionMonitor:
    """Monitor backend connections and detect potential hanging issues."""
    
    def __init__(self, check_interval=10, history_size=100):
        self.check_interval = check_interval
        self.history = deque(maxlen=history_size)
        self.running = False
        self.thread = None
        self.connection_stats = defaultdict(list)
        
    def start_monitoring(self):
        """Start monitoring in a background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"📊 Connection monitoring started (interval: {self.check_interval}s)")
        
    def stop_monitoring(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join()
        print("📊 Connection monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                stats = self._collect_stats()
                self.history.append(stats)
                self._analyze_stats(stats)
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(self.check_interval)
                
    def _collect_stats(self):
        """Collect current connection and process statistics."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'processes': {},
            'connections': {},
            'memory': {},
            'cpu': {}
        }
        
        # Process information
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
            try:
                info = proc.info
                if 'python' in info['name'].lower():
                    cmdline = ' '.join(info['cmdline']) if info['cmdline'] else ''
                    if 'app.py' in cmdline or 'backend' in cmdline:
                        stats['processes'][info['pid']] = {
                            'name': info['name'],
                            'cmdline': cmdline,
                            'memory_mb': info['memory_info'].rss / 1024 / 1024,
                            'cpu_percent': info['cpu_percent']
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Network connections
        try:
            connections = psutil.net_connections(kind='inet')
            connection_summary = defaultdict(int)
            
            for conn in connections:
                if conn.status:
                    connection_summary[conn.status] += 1
                    
            stats['connections'] = dict(connection_summary)
            
        except psutil.AccessDenied:
            stats['connections'] = {'error': 'Access denied'}
            
        # System resources
        stats['memory'] = {
            'total_mb': psutil.virtual_memory().total / 1024 / 1024,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'used_percent': psutil.virtual_memory().percent
        }
        
        stats['cpu'] = {
            'percent': psutil.cpu_percent(interval=None),
            'count': psutil.cpu_count()
        }
        
        return stats
        
    def _analyze_stats(self, stats):
        """Analyze statistics for potential hanging issues."""
        warnings = []
        
        # Check for high memory usage
        if stats['memory']['used_percent'] > 90:
            warnings.append(f"High memory usage: {stats['memory']['used_percent']:.1f}%")
            
        # Check for high CPU usage
        if stats['cpu']['percent'] > 80:
            warnings.append(f"High CPU usage: {stats['cpu']['percent']:.1f}%")
            
        # Check for suspicious connection states
        conn_stats = stats['connections']
        if isinstance(conn_stats, dict):
            # Look for too many connections in non-established states
            suspicious_states = ['CLOSE_WAIT', 'TIME_WAIT', 'FIN_WAIT1', 'FIN_WAIT2']
            for state in suspicious_states:
                if state in conn_stats and conn_stats[state] > 50:
                    warnings.append(f"High {state} connections: {conn_stats[state]}")
                    
        # Check for backend processes
        backend_processes = stats['processes']
        if len(backend_processes) > 10:
            warnings.append(f"Many backend processes: {len(backend_processes)}")
            
        for pid, proc_info in backend_processes.items():
            if proc_info['memory_mb'] > 500:  # 500MB threshold
                warnings.append(f"High memory process {pid}: {proc_info['memory_mb']:.1f}MB")
                
        # Print warnings if any
        if warnings:
            print(f"⚠️  {stats['timestamp']} - Warnings detected:")
            for warning in warnings:
                print(f"   - {warning}")
                
    def print_summary(self):
        """Print a summary of monitoring results."""
        if not self.history:
            print("📊 No monitoring data available")
            return
            
        print("\n📊 Connection Monitoring Summary")
        print("=" * 50)
        
        latest = self.history[-1]
        print(f"Last check: {latest['timestamp']}")
        print(f"Backend processes: {len(latest['processes'])}")
        print(f"Memory usage: {latest['memory']['used_percent']:.1f}%")
        print(f"CPU usage: {latest['cpu']['percent']:.1f}%")
        
        if latest['connections'] and isinstance(latest['connections'], dict):
            print("Network connections:")
            for state, count in latest['connections'].items():
                print(f"  {state}: {count}")
                
        # Show trends if we have enough data
        if len(self.history) >= 3:
            print("\n📈 Trends (last 3 checks):")
            
            memory_trend = [h['memory']['used_percent'] for h in list(self.history)[-3:]]
            cpu_trend = [h['cpu']['percent'] for h in list(self.history)[-3:]]
            
            print(f"Memory: {memory_trend[0]:.1f}% → {memory_trend[1]:.1f}% → {memory_trend[2]:.1f}%")
            print(f"CPU: {cpu_trend[0]:.1f}% → {cpu_trend[1]:.1f}% → {cpu_trend[2]:.1f}%")
            
def test_backend_response_time():
    """Test backend response time to detect hanging."""
    print("🔍 Testing backend response time...")
    
    try:
        import requests
        
        # Test health endpoint
        start_time = time.time()
        response = requests.get('http://localhost:5001/api/health', timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Health check OK ({response_time:.1f}ms)")
        else:
            print(f"❌ Health check failed: {response.status_code} ({response_time:.1f}ms)")
            
    except requests.exceptions.ConnectRefused:
        print("❌ Backend not running")
    except requests.exceptions.Timeout:
        print("❌ Backend hanging (timeout)")
    except Exception as e:
        print(f"❌ Backend error: {e}")
        
def main():
    """Main monitoring script."""
    print("🔍 Backend Connection Monitor")
    print("=" * 50)
    
    # Test immediate response
    test_backend_response_time()
    
    # Start monitoring
    monitor = ConnectionMonitor(check_interval=5)
    
    def signal_handler(signum, frame):
        print("\n📊 Stopping monitoring...")
        monitor.stop_monitoring()
        monitor.print_summary()
        exit(0)
        
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        monitor.start_monitoring()
        
        print("📊 Monitoring active. Press Ctrl+C to stop and view summary.")
        print("⚠️  Watching for:")
        print("   - High memory usage (>90%)")
        print("   - High CPU usage (>80%)")
        print("   - Suspicious connection states")
        print("   - Backend processes using >500MB memory")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        monitor.print_summary()
        
if __name__ == "__main__":
    main()