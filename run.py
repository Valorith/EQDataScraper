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
        self.npm_command = None
        
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
        
    def find_npm_command(self) -> Optional[str]:
        """Find the npm command that works on this system"""
        import platform
        import os
        
        # Check if we're in WSL (Linux subsystem but accessing Windows files)
        is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
        
        # Different commands to try based on platform
        if platform.system() == "Windows" and not is_wsl:
            npm_commands = ["npm.cmd", "npm", "npx.cmd", "npx"]
            use_shell = True
        else:
            npm_commands = ["npm", "npx"]
            use_shell = False
        
        for cmd in npm_commands:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10,
                                      shell=use_shell)
                if result.returncode == 0:
                    return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # Try using 'where' on Windows or 'which' on Unix to find npm
        try:
            search_cmd = "where" if platform.system() == "Windows" and not is_wsl else "which"
            result = subprocess.run([search_cmd, "npm"], capture_output=True, text=True, shell=True)
            if result.returncode == 0 and result.stdout.strip():
                npm_path = result.stdout.strip().split('\n')[0]  # Take first result
                return npm_path
        except:
            pass
            
        return None

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
        
        # Find npm command
        npm_cmd = self.find_npm_command()
        if not npm_cmd:
            self.print_status("npm not found", "error")
            self.print_status("Please ensure npm is installed and in your PATH", "info")
            return False
        else:
            self.npm_command = npm_cmd
            # Debug: Show what we detected
            import os
            import platform
            is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
            self.print_status(f"npm command: {npm_cmd} (WSL: {is_wsl})", "success")
            
        # Check if node_modules exists and has required packages
        if not (self.frontend_dir / "node_modules").exists():
            self.print_status("Node modules not installed", "warning")
            self.print_status(f"Run: {npm_cmd} install", "info")
            return False
        
        # Check for critical packages
        critical_packages = ["vite", "vue", "@vitejs/plugin-vue"]
        missing_packages = []
        
        for package in critical_packages:
            if not (self.frontend_dir / "node_modules" / package).exists():
                missing_packages.append(package)
        
        if missing_packages:
            self.print_status(f"Missing critical packages: {', '.join(missing_packages)}", "warning")
            self.print_status(f"Run: {npm_cmd} install", "info")
            return False
        
        # Check for Rollup dependency issues (Windows and WSL)
        import platform
        import os
        is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
        
        if platform.system() == "Windows" and not is_wsl:
            rollup_native = self.frontend_dir / "node_modules" / "@rollup" / "rollup-win32-x64-msvc"
            if not rollup_native.exists():
                self.print_status("Windows Rollup dependency issue detected", "warning")
                self.print_status("This is a known npm bug. Attempting to fix...", "info")
                return self._fix_windows_dependencies(npm_cmd)
        elif is_wsl:
            rollup_native = self.frontend_dir / "node_modules" / "@rollup" / "rollup-linux-x64-gnu"
            if not rollup_native.exists():
                self.print_status("WSL Rollup dependency issue detected", "warning")
                self.print_status("This is a known npm bug. Attempting to fix...", "info")
                return self._fix_windows_dependencies(npm_cmd)
        
        self.print_status("Node modules: OK", "success")
            
        return True
        
    def _fix_windows_dependencies(self, npm_cmd: str) -> bool:
        """Fix Windows npm dependency issues by removing and reinstalling"""
        try:
            # Remove package-lock.json if it exists
            package_lock = self.frontend_dir / "package-lock.json"
            if package_lock.exists():
                self.print_status("Removing package-lock.json...", "info")
                package_lock.unlink()
            
            # Remove node_modules directory
            node_modules = self.frontend_dir / "node_modules"
            if node_modules.exists():
                self.print_status("Removing node_modules directory...", "info")
                import shutil
                shutil.rmtree(node_modules)
            
            # Reinstall dependencies
            self.print_status("Reinstalling dependencies...", "info")
            result = subprocess.run([npm_cmd, "install"], 
                                  cwd=self.frontend_dir, 
                                  capture_output=True, 
                                  text=True,
                                  shell=False)
            
            if result.returncode == 0:
                self.print_status("Dependencies reinstalled successfully", "success")
                return True
            else:
                self.print_status(f"Failed to reinstall dependencies: {result.stderr}", "error")
                return False
                
        except Exception as e:
            self.print_status(f"Error fixing dependencies: {e}", "error")
            return False
    
    def save_pids(self):
        """Save process IDs to file"""
        pids = {}
        for name, proc in self.processes.items():
            if proc and proc.poll() is None:  # Only save if process is still running
                pids[name] = proc.pid
        
        if pids:  # Only write file if we have running processes
            try:
                with open(self.pids_file, 'w') as f:
                    json.dump(pids, f)
                self.print_status(f"Saved PIDs: {pids}", "info")
            except Exception as e:
                self.print_status(f"Failed to save PIDs: {e}", "warning")
        else:
            # No running processes, remove PID file if it exists
            if self.pids_file.exists():
                self.pids_file.unlink()
            
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
        import platform
        try:
            if platform.system() == "Windows":
                # On Windows, use tasklist to check if process exists
                result = subprocess.run(['tasklist', '/fi', f'PID eq {pid}'], 
                                      capture_output=True, text=True, shell=True)
                return str(pid) in result.stdout
            else:
                # On Unix systems, use os.kill
                os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
                return True
        except (OSError, ProcessLookupError, subprocess.CalledProcessError):
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
            time.sleep(3)
            if process.poll() is None:
                self.print_status("Backend server started on http://localhost:5000", "success")
                return True
            else:
                stdout, stderr = process.communicate()
                self.print_status(f"Backend failed to start: {stderr.strip()}", "error")
                return False
                
        except Exception as e:
            self.print_status(f"Error starting backend: {e}", "error")
            return False
            
    def start_frontend(self) -> bool:
        """Start the Vite frontend development server"""
        import platform
        self.print_status("Starting frontend development server...", "info")
        
        # Ensure we have npm command available
        if not self.npm_command:
            self.npm_command = self.find_npm_command()
            if not self.npm_command:
                self.print_status("npm command not found", "error")
                return False
        
        try:
            # Simple approach: always use npm run dev first, then fallback to node execution
            import os
            is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
            vite_js_path = self.frontend_dir / "node_modules" / "vite" / "bin" / "vite.js"
            
            # Always use list format for better cross-platform compatibility
            commands_to_try = [
                [self.npm_command, "run", "dev"],
                ["npx", "vite"],
                ["node", str(vite_js_path)] if vite_js_path.exists() else ["npx", "vite"]
            ]
            
            use_shell = False  # Use shell=False for better compatibility
            
            for cmd in commands_to_try:
                try:
                    cmd_str = ' '.join(cmd)
                    self.print_status(f"Trying command: {cmd_str}", "info")
                    
                    process = subprocess.Popen(
                        cmd,
                        cwd=self.frontend_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=use_shell
                    )
                    
                    # Wait for Vite to start
                    time.sleep(5)  # Give more time for Vite to start
                    if process.poll() is None:
                        self.processes["frontend"] = process
                        self.print_status("Frontend server started on port 3000 (or next available)", "success")
                        return True
                    else:
                        # Process failed - get error output
                        stdout, stderr = process.communicate()
                        error_msg = stderr.strip() if stderr and stderr.strip() else stdout.strip()
                        self.print_status(f"Command {cmd_str} failed: {error_msg}", "warning")
                        continue
                        
                except Exception as e:
                    self.print_status(f"Error with command {cmd_str}: {e}", "warning")
                    continue
            
            self.print_status("All frontend start commands failed", "error")
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
                    dead_processes = []
                    for name, proc in self.processes.items():
                        if proc and proc.poll() is not None:
                            dead_processes.append(name)
                    
                    if dead_processes:
                        self.print_status(f"Services stopped unexpectedly: {', '.join(dead_processes)}", "error")
                        # Remove dead processes from tracking
                        for name in dead_processes:
                            if name in self.processes:
                                del self.processes[name]
                        # Update PID file
                        self.save_pids()
                        
                        # If all processes are dead, exit
                        if not self.processes:
                            break
                    
                    time.sleep(2)  # Check every 2 seconds
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
                    if process and process.poll() is None:  # Process is still running
                        self.print_status(f"Stopping {name}...", "info")
                        process.terminate()
                        
                        # Wait for graceful shutdown
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.print_status(f"Force killing {name}...", "warning")
                            process.kill()
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pass  # Process might be forcefully killed
                        
                        self.print_status(f"Stopped {name}", "success")
                    else:
                        self.print_status(f"{name} was already stopped", "info")
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
        npm_cmd = self.find_npm_command()
        if not npm_cmd:
            self.print_status("npm command not found", "error")
            return
        try:
            subprocess.run([npm_cmd, "install"], check=True, cwd=self.frontend_dir)
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