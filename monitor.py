#!/usr/bin/env python3
"""
EQDataScraper Service Monitor
Monitors frontend and backend services and attempts automatic recovery
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import threading
import signal

class ServiceMonitor:
    def __init__(self, config_path: str = "config.json"):
        self.root_dir = Path(__file__).parent
        self.config_path = self.root_dir / config_path
        self.config = self._load_config()
        self.backend_port = self.config.get('backend_port', 5001)
        self.frontend_port = self.config.get('frontend_port', 3000)
        self.running = True
        self.recovery_attempts = {}
        self.last_check = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def check_backend_health(self) -> Tuple[bool, str]:
        """Check if backend is healthy"""
        try:
            response = requests.get(
                f"http://localhost:{self.backend_port}/api/health",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                cached_classes = data.get('cached_classes', 0)
                return True, f"OK (cached classes: {cached_classes})"
            else:
                return False, f"Unhealthy (status: {response.status_code})"
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - service not running"
        except requests.exceptions.Timeout:
            return False, "Timeout - service not responding"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_frontend_health(self) -> Tuple[bool, str]:
        """Check if frontend is healthy"""
        try:
            # For Vite dev server, check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.frontend_port))
            sock.close()
            
            if result == 0:
                # Try to fetch the index page
                try:
                    response = requests.get(
                        f"http://localhost:{self.frontend_port}/",
                        timeout=5
                    )
                    if response.status_code == 200:
                        return True, "OK"
                    else:
                        return True, f"Running (status: {response.status_code})"
                except:
                    return True, "Running (port open)"
            else:
                return False, "Port not accessible - service not running"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_process_memory(self) -> Dict[str, float]:
        """Check memory usage of services"""
        memory_usage = {}
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                pinfo = proc.info
                name = pinfo['name']
                
                # Check for Python backend
                if 'python' in name.lower():
                    cmdline = proc.cmdline()
                    if any('app.py' in cmd for cmd in cmdline):
                        memory_mb = pinfo['memory_info'].rss / 1024 / 1024
                        memory_usage['backend'] = memory_mb
                
                # Check for Node frontend
                elif 'node' in name.lower():
                    cmdline = proc.cmdline()
                    if any('vite' in cmd for cmd in cmdline):
                        memory_mb = pinfo['memory_info'].rss / 1024 / 1024
                        memory_usage['frontend'] = memory_mb
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return memory_usage
    
    def restart_backend(self) -> bool:
        """Attempt to restart the backend service"""
        self.logger.warning("Attempting to restart backend service...")
        
        try:
            # Kill existing backend process
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = proc.cmdline()
                        if any('app.py' in cmd for cmd in cmdline):
                            self.logger.info(f"Killing backend process (PID: {proc.info['pid']})")
                            proc.kill()
                            time.sleep(2)
                except:
                    continue
            
            # Start backend
            backend_cmd = [sys.executable, "app.py"]
            subprocess.Popen(
                backend_cmd,
                cwd=self.root_dir / "backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait for startup
            time.sleep(5)
            
            # Check if it started successfully
            healthy, _ = self.check_backend_health()
            if healthy:
                self.logger.info("Backend restarted successfully")
                return True
            else:
                self.logger.error("Backend restart failed - service not healthy")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting backend: {e}")
            return False
    
    def restart_frontend(self) -> bool:
        """Attempt to restart the frontend service"""
        self.logger.warning("Attempting to restart frontend service...")
        
        try:
            # Kill existing frontend process
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'node' in proc.info['name'].lower():
                        cmdline = proc.cmdline()
                        if any('vite' in cmd for cmd in cmdline):
                            self.logger.info(f"Killing frontend process (PID: {proc.info['pid']})")
                            proc.kill()
                            time.sleep(2)
                except:
                    continue
            
            # Start frontend
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            frontend_cmd = [npm_cmd, "run", "dev"]
            subprocess.Popen(
                frontend_cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait for startup
            time.sleep(8)
            
            # Check if it started successfully
            healthy, _ = self.check_frontend_health()
            if healthy:
                self.logger.info("Frontend restarted successfully")
                return True
            else:
                self.logger.error("Frontend restart failed - service not healthy")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting frontend: {e}")
            return False
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting service monitoring...")
        self.logger.info(f"Backend port: {self.backend_port}")
        self.logger.info(f"Frontend port: {self.frontend_port}")
        
        check_interval = 30  # seconds
        max_recovery_attempts = 3
        recovery_cooldown = 300  # 5 minutes
        memory_threshold_mb = 1000  # Restart if memory exceeds 1GB
        
        while self.running:
            try:
                # Check backend
                backend_healthy, backend_status = self.check_backend_health()
                self.logger.debug(f"Backend status: {backend_status}")
                
                if not backend_healthy:
                    self.logger.error(f"Backend unhealthy: {backend_status}")
                    
                    # Check recovery attempts
                    last_attempt = self.recovery_attempts.get('backend', 0)
                    if time.time() - last_attempt > recovery_cooldown:
                        if self.restart_backend():
                            self.recovery_attempts['backend'] = time.time()
                        else:
                            self.logger.error("Failed to recover backend service")
                    else:
                        self.logger.info("Skipping recovery - cooldown period active")
                
                # Check frontend
                frontend_healthy, frontend_status = self.check_frontend_health()
                self.logger.debug(f"Frontend status: {frontend_status}")
                
                if not frontend_healthy:
                    self.logger.error(f"Frontend unhealthy: {frontend_status}")
                    
                    # Check recovery attempts
                    last_attempt = self.recovery_attempts.get('frontend', 0)
                    if time.time() - last_attempt > recovery_cooldown:
                        if self.restart_frontend():
                            self.recovery_attempts['frontend'] = time.time()
                        else:
                            self.logger.error("Failed to recover frontend service")
                    else:
                        self.logger.info("Skipping recovery - cooldown period active")
                
                # Check memory usage
                memory_usage = self.check_process_memory()
                for service, memory_mb in memory_usage.items():
                    self.logger.debug(f"{service} memory: {memory_mb:.1f} MB")
                    
                    if memory_mb > memory_threshold_mb:
                        self.logger.warning(f"{service} memory usage high: {memory_mb:.1f} MB")
                        
                        # Consider restarting if memory is too high
                        last_attempt = self.recovery_attempts.get(f'{service}_memory', 0)
                        if time.time() - last_attempt > recovery_cooldown:
                            self.logger.warning(f"Restarting {service} due to high memory usage")
                            if service == 'backend':
                                self.restart_backend()
                            elif service == 'frontend':
                                self.restart_frontend()
                            self.recovery_attempts[f'{service}_memory'] = time.time()
                
                # Log periodic status
                if time.time() - self.last_check.get('status_log', 0) > 300:  # Every 5 minutes
                    self.logger.info(f"Status - Backend: {backend_status}, Frontend: {frontend_status}")
                    self.last_check['status_log'] = time.time()
                
                # Sleep before next check
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(check_interval)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        self.logger.info("Stopping service monitor")


def main():
    parser = argparse.ArgumentParser(description='Monitor EQDataScraper services')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--config', default='config.json', help='Config file path')
    args = parser.parse_args()
    
    monitor = ServiceMonitor(args.config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.daemon:
            # Fork to background
            if os.fork() > 0:
                sys.exit(0)
            os.setsid()
            if os.fork() > 0:
                sys.exit(0)
        
        monitor.monitor_loop()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()