#!/usr/bin/env python3
"""
EQDataScraper Application Runner
Unified script to start/stop both frontend and backend services
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import json
from pathlib import Path
from typing import Optional, List

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class AppRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir
        self.pids_file = self.root_dir / ".app_pids.json"
        self.processes = {}
        self.skip_dependency_check = False
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}\n")
        
    def print_status(self, message: str, status: str = "info"):
        """Print a status message with color coding"""
        color = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED
        }.get(status, Colors.WHITE)
        
        prefix = {
            "info": "ℹ",
            "success": "✅",
            "warning": "⚠",
            "error": "❌"
        }.get(status, "•")
        
        print(f"{color}{prefix} {message}{Colors.END}")
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        self.print_status("Checking dependencies...", "info")
        
        # Check Python dependencies
        try:
            import flask
            import requests
            import pandas
            from bs4 import BeautifulSoup  # beautifulsoup4 package imports as bs4
            import jinja2
            self.print_status("Python dependencies: OK", "success")
        except ImportError as e:
            self.print_status(f"Missing Python dependency: {e}", "error")
            self.print_status("Run: pip install -r backend/requirements.txt", "info")
            return False
            
        # Check Node.js and npm
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_status(f"Node.js: {result.stdout.strip()}", "success")
            else:
                raise subprocess.CalledProcessError(1, "node")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("Node.js not found", "error")
            self.print_status("Please install Node.js from https://nodejs.org/", "info")
            return False
            
        # Check if node_modules exists
        if not (self.frontend_dir / "node_modules").exists():
            self.print_status("Node modules not installed", "warning")
            self.print_status("Run: npm install", "info")
            return False
        else:
            self.print_status("Node modules: OK", "success")
            
        return True
        
    def save_pids(self):
        """Save process IDs to file"""
        pids = {name: proc.pid for name, proc in self.processes.items()}
        with open(self.pids_file, 'w') as f:
            json.dump(pids, f)
            
    def load_pids(self) -> dict:
        """Load process IDs from file"""
        if self.pids_file.exists():
            try:
                with open(self.pids_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
        
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is still running"""
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False
            
    def start_backend(self) -> bool:
        """Start the Flask backend server"""
        self.print_status("Starting backend server...", "info")
        
        try:
            # Change to backend directory and start Flask app
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.root_dir)
            
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes["backend"] = process
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            if process.poll() is None:
                self.print_status("Backend server started on http://localhost:5000", "success")
                return True
            else:
                stdout, stderr = process.communicate()
                self.print_status(f"Backend failed to start: {stderr}", "error")
                return False
                
        except Exception as e:
            self.print_status(f"Error starting backend: {e}", "error")
            return False
            
    def start_frontend(self) -> bool:
        """Start the Vite frontend development server"""
        self.print_status("Starting frontend development server...", "info")
        
        try:
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes["frontend"] = process
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            if process.poll() is None:
                self.print_status("Frontend server started on http://localhost:3000", "success")
                return True
            else:
                stdout, stderr = process.communicate()
                self.print_status(f"Frontend failed to start: {stderr}", "error")
                return False
                
        except Exception as e:
            self.print_status(f"Error starting frontend: {e}", "error")
            return False
            
    def start_services(self):
        """Start both frontend and backend services"""
        self.print_header("Starting EQDataScraper Application")
        
        if self.skip_dependency_check:
            self.print_status("⚠️  Skipping dependency check as requested", "warning")
        elif not self.check_dependencies():
            self.print_status("Dependency check failed. Please resolve issues and try again.", "error")
            self.print_status("Use --skip-deps to bypass this check (not recommended)", "info")
            return
            
        success = True
        
        # Start backend first
        if not self.start_backend():
            success = False
            
        # Start frontend
        if success and not self.start_frontend():
            success = False
            
        if success:
            self.save_pids()
            self.print_status("\n🎉 Application started successfully!", "success")
            self.print_status("Frontend: http://localhost:3000", "info")
            self.print_status("Backend API: http://localhost:5000", "info")
            self.print_status("\nPress Ctrl+C to stop all services", "info")
            
            try:
                # Wait for processes and handle Ctrl+C
                while True:
                    # Check if processes are still running
                    if any(proc.poll() is not None for proc in self.processes.values()):
                        self.print_status("One or more services stopped unexpectedly", "error")
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                self.print_status("\nShutting down services...", "info")
                self.stop_services()
        else:
            self.stop_services()
            
    def stop_services(self):
        """Stop all running services"""
        self.print_header("Stopping EQDataScraper Application")
        
        # Load PIDs from file if processes dict is empty
        if not self.processes:
            pids = self.load_pids()
            for name, pid in pids.items():
                if self.is_process_running(pid):
                    self.print_status(f"Found running {name} service (PID: {pid})", "info")
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(2)
                        if self.is_process_running(pid):
                            os.kill(pid, signal.SIGKILL)
                        self.print_status(f"Stopped {name} service", "success")
                    except (OSError, ProcessLookupError):
                        self.print_status(f"Could not stop {name} service", "warning")
        else:
            # Stop processes from current session
            for name, process in self.processes.items():
                try:
                    self.print_status(f"Stopping {name}...", "info")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.print_status(f"Force killing {name}...", "warning")
                        process.kill()
                        process.wait()
                        
                    self.print_status(f"Stopped {name}", "success")
                except Exception as e:
                    self.print_status(f"Error stopping {name}: {e}", "error")
                    
        # Clean up PID file
        if self.pids_file.exists():
            self.pids_file.unlink()
            
        self.print_status("All services stopped", "success")
        
    def status(self):
        """Check status of services"""
        self.print_header("EQDataScraper Service Status")
        
        pids = self.load_pids()
        
        if not pids:
            self.print_status("No services are currently tracked", "info")
            return
            
        for name, pid in pids.items():
            if self.is_process_running(pid):
                self.print_status(f"{name.capitalize()} service: Running (PID: {pid})", "success")
            else:
                self.print_status(f"{name.capitalize()} service: Not running", "error")
                
    def install_deps(self):
        """Install all dependencies"""
        self.print_header("Installing Dependencies")
        
        # Install Python dependencies
        self.print_status("Installing Python dependencies...", "info")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], 
                         check=True, cwd=self.root_dir)
            self.print_status("Python dependencies installed", "success")
        except subprocess.CalledProcessError as e:
            self.print_status(f"Failed to install Python dependencies: {e}", "error")
            return
            
        # Install Node.js dependencies
        self.print_status("Installing Node.js dependencies...", "info")
        try:
            subprocess.run(["npm", "install"], check=True, cwd=self.frontend_dir)
            self.print_status("Node.js dependencies installed", "success")
        except subprocess.CalledProcessError as e:
            self.print_status(f"Failed to install Node.js dependencies: {e}", "error")
            return
            
        self.print_status("All dependencies installed successfully!", "success")

def main():
    parser = argparse.ArgumentParser(description="EQDataScraper Application Runner")
    parser.add_argument("command", choices=["start", "stop", "status", "install"], 
                       help="Command to execute")
    parser.add_argument("--skip-deps", "--ignore-deps", action="store_true",
                       help="Skip dependency checking (use with caution)")
    
    args = parser.parse_args()
    runner = AppRunner()
    runner.skip_dependency_check = args.skip_deps
    
    if args.command == "start":
        runner.start_services()
    elif args.command == "stop":
        runner.stop_services()
    elif args.command == "status":
        runner.status()
    elif args.command == "install":
        runner.install_deps()

if __name__ == "__main__":
    main()