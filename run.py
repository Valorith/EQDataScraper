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
import socket
import threading
from pathlib import Path
from typing import Optional, List, Dict

# Import platform-specific modules conditionally
try:
    import termios
    import tty
    import select
    HAS_UNIX_TERMINAL = True
except ImportError:
    HAS_UNIX_TERMINAL = False

try:
    import msvcrt
    HAS_WINDOWS_TERMINAL = True
except ImportError:
    HAS_WINDOWS_TERMINAL = False

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
        self.config_file = self.root_dir / "config.json"
        self.port_map_file = self.root_dir / ".port_mapping.json"
        self.processes = {}
        self.skip_dependency_check = False
        self.npm_command = None
        self.config = self.load_config()
        self.running = False
        self.restart_requested = False
        self.old_termios = None
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}\n")
        
    def print_status(self, message: str, status: str = "info", indent: int = 0):
        """Print a status message with color coding and optional indentation"""
        color = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "step": Colors.CYAN,
            "detail": Colors.WHITE
        }.get(status, Colors.WHITE)
        
        prefix = {
            "info": "ℹ",
            "success": "✅",
            "warning": "⚠",
            "error": "❌",
            "step": "🔧",
            "detail": "  •"
        }.get(status, "•")
        
        indent_str = "  " * indent
        print(f"{indent_str}{color}{prefix} {message}{Colors.END}")
    
    def print_section(self, title: str):
        """Print a section separator"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}─── {title} ───{Colors.END}")
    
    def load_config(self) -> Dict:
        """Load configuration from config.json"""
        default_config = {
            'backend_port': 5001,
            'frontend_port': 3000,
            'cache_expiry_hours': 24,
            'min_scrape_interval_minutes': 5
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = {**default_config, **json.load(f)}
            else:
                config = default_config
                self.save_config(config)
        except (json.JSONDecodeError, IOError) as e:
            self.print_status(f"Error loading config.json: {e}. Using defaults.", "warning")
            config = default_config
            
        return config
    
    def save_config(self, config: Dict):
        """Save configuration to config.json"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            self.print_status(f"Error saving config.json: {e}", "error")
    
    def load_port_mapping(self) -> Dict[str, int]:
        """Load port mapping that tracks actual ports in use"""
        if self.port_map_file.exists():
            try:
                with open(self.port_map_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_port_mapping(self, mapping: Dict[str, int]):
        """Save actual port mapping"""
        try:
            with open(self.port_map_file, 'w') as f:
                json.dump(mapping, f, indent=2)
        except IOError:
            pass
    
    def smart_port_allocation(self) -> Dict[str, int]:
        """Smart port allocation with conflict detection and resolution"""
        self.print_section("Port Management")
        
        # Check if we're in a deployment environment (Railway, etc.)
        if self._is_deployment_environment():
            self.print_status("Deployment environment detected - using environment variables", "info", 1)
            return {
                'backend': int(os.environ.get('BACKEND_PORT', self.config['backend_port'])),
                'frontend': int(os.environ.get('PORT', os.environ.get('FRONTEND_PORT', self.config['frontend_port'])))
            }
        
        self.print_status("Checking for port conflicts...", "step", 1)
        
        # Define default ports to prevent drift
        DEFAULT_BACKEND_PORT = 5001
        DEFAULT_FRONTEND_PORT = 3000
        
        # Try to use defaults first, then fall back to configured ports
        backend_port = DEFAULT_BACKEND_PORT
        frontend_port = DEFAULT_FRONTEND_PORT
        
        # Check if we can use default ports
        default_backend_available = not self.is_port_in_use(DEFAULT_BACKEND_PORT)
        default_frontend_available = not self.is_port_in_use(DEFAULT_FRONTEND_PORT)
        
        # Track allocated ports
        allocated_ports = {}
        ports_changed = False
        
        # Backend port allocation
        if default_backend_available:
            # Prefer default port
            backend_port = DEFAULT_BACKEND_PORT
            if self.config['backend_port'] != DEFAULT_BACKEND_PORT:
                self.print_status(f"Using default backend port: {DEFAULT_BACKEND_PORT}", "success", 2)
                ports_changed = True
        else:
            # Default is not available, check configured port
            backend_port = self.config['backend_port']
            if self.is_port_in_use(backend_port):
                process_info = self.get_port_conflict_process(backend_port)
                self.print_status(f"Port {backend_port} in use by: {process_info or 'unknown'}", "warning", 2)
                
                # Find alternative
                new_backend_port = self.find_available_port(backend_port + 1, max_attempts=20)
                if new_backend_port != backend_port:
                    self.print_status(f"Allocated backend port: {new_backend_port}", "success", 2)
                    backend_port = new_backend_port
                    ports_changed = True
        
        allocated_ports['backend'] = backend_port
        
        # Frontend port allocation
        if default_frontend_available and frontend_port != backend_port:
            # Prefer default port
            frontend_port = DEFAULT_FRONTEND_PORT
            if self.config['frontend_port'] != DEFAULT_FRONTEND_PORT:
                self.print_status(f"Using default frontend port: {DEFAULT_FRONTEND_PORT}", "success", 2)
                ports_changed = True
        else:
            # Default is not available or conflicts with backend
            frontend_port = self.config['frontend_port']
            if self.is_port_in_use(frontend_port) or frontend_port == backend_port:
                if frontend_port == backend_port:
                    self.print_status(f"Frontend port conflicts with backend", "warning", 2)
                else:
                    process_info = self.get_port_conflict_process(frontend_port)
                    self.print_status(f"Port {frontend_port} in use by: {process_info or 'unknown'}", "warning", 2)
                
                # Find alternative (avoid backend port)
                new_frontend_port = frontend_port + 1
                while new_frontend_port == backend_port or self.is_port_in_use(new_frontend_port):
                    new_frontend_port += 1
                    if new_frontend_port > frontend_port + 20:  # Safety limit
                        break
                
                if new_frontend_port != frontend_port:
                    self.print_status(f"Allocated frontend port: {new_frontend_port}", "success", 2)
                    frontend_port = new_frontend_port
                    ports_changed = True
        
        allocated_ports['frontend'] = frontend_port
        
        # Update config if ports changed
        if ports_changed:
            self.config['backend_port'] = backend_port
            self.config['frontend_port'] = frontend_port
            self.save_config(self.config)
            
            if backend_port == DEFAULT_BACKEND_PORT and frontend_port == DEFAULT_FRONTEND_PORT:
                self.print_status("Reverted to default ports configuration", "success", 2)
            else:
                self.print_status("Updated config.json with new port allocations", "success", 2)
            
            # Update all frontend files that reference the backend port
            self.sync_frontend_config(backend_port)
            
            # Update OAuth redirect URIs if frontend port changed
            self.sync_oauth_config(frontend_port)
        else:
            if backend_port == DEFAULT_BACKEND_PORT and frontend_port == DEFAULT_FRONTEND_PORT:
                self.print_status("Using default ports (no conflicts detected)", "success", 2)
            else:
                self.print_status("Using previously configured ports", "info", 2)
        
        # Save port mapping
        self.save_port_mapping(allocated_ports)
        self.print_status(f"Backend: {backend_port}, Frontend: {frontend_port}", "info", 2)
        
        return allocated_ports
    
    def sync_frontend_config(self, backend_port: int):
        """Synchronize backend port across all frontend configuration files"""
        # Skip file syncing in deployment environments
        if self._is_deployment_environment():
            self.print_status("Deployment environment - skipping file sync", "info", 2)
            return
            
        self.print_status(f"Syncing backend port {backend_port} to frontend files...", "step", 2)
        
        # Files that need updating (only localhost references - don't touch production URLs)
        files_to_update = [
            (self.frontend_dir / "src" / "stores" / "spells.js", 
             r"'http://localhost:\d+'", f"'http://localhost:{backend_port}'"),
            (self.frontend_dir / "src" / "App.vue",
             r"'http://localhost:\d+'", f"'http://localhost:{backend_port}'"),
            (self.frontend_dir / "vite.config.js",
             r"target:\s*['\"]http://localhost:\d+['\"]", f"target: 'http://localhost:{backend_port}'"),
            (self.frontend_dir / ".env.development",
             r"VITE_BACKEND_URL=http://localhost:\d+", f"VITE_BACKEND_URL=http://localhost:{backend_port}")
        ]
        
        for file_path, pattern, replacement in files_to_update:
            if file_path.exists():
                try:
                    import re
                    content = file_path.read_text()
                    updated_content = re.sub(pattern, replacement, content)
                    if content != updated_content:
                        file_path.write_text(updated_content)
                        self.print_status(f"Updated {file_path.name}", "success", 3)
                except Exception as e:
                    self.print_status(f"Failed to update {file_path.name}: {e}", "warning", 3)
        
        # Create .env.development if it doesn't exist
        env_file = self.frontend_dir / ".env.development"
        if not env_file.exists():
            try:
                env_file.write_text(f"VITE_BACKEND_URL=http://localhost:{backend_port}\n")
                self.print_status("Created .env.development", "success", 3)
            except Exception as e:
                self.print_status(f"Failed to create .env.development: {e}", "warning", 3)
    
    def sync_oauth_config(self, frontend_port: int):
        """Synchronize OAuth redirect URIs when frontend port changes"""
        # Skip file syncing in deployment environments
        if self._is_deployment_environment():
            self.print_status("Deployment environment - skipping OAuth sync", "info", 2)
            return
            
        redirect_uri = f"http://localhost:{frontend_port}/auth/callback"
        self.print_status("Syncing OAuth redirect URI...", "step", 2)
        
        # Files that need OAuth redirect URI updates
        oauth_files_to_update = [
            (self.frontend_dir / ".env", 
             r"VITE_OAUTH_REDIRECT_URI=http://localhost:\d+/auth/callback", 
             f"VITE_OAUTH_REDIRECT_URI={redirect_uri}"),
            (self.backend_dir / ".env",
             r"OAUTH_REDIRECT_URI=http://localhost:\d+/auth/callback",
             f"OAUTH_REDIRECT_URI={redirect_uri}")
        ]
        
        oauth_updated = False
        for file_path, pattern, replacement in oauth_files_to_update:
            if file_path.exists():
                try:
                    import re
                    content = file_path.read_text()
                    updated_content = re.sub(pattern, replacement, content)
                    if content != updated_content:
                        file_path.write_text(updated_content)
                        self.print_status(f"Updated {file_path.name}", "success", 3)
                        oauth_updated = True
                except Exception as e:
                    self.print_status(f"Failed to update OAuth redirect in {file_path.name}: {e}", "warning", 3)
            else:
                self.print_status(f"OAuth config file not found: {file_path.name}", "warning", 3)
        
        if oauth_updated:
            self.print_status("OAuth configuration synchronized", "success", 2)
            self.print_status("Remember to update Google Cloud Console redirect URIs", "warning", 2)
        else:
            self.print_status("OAuth configuration up to date", "info", 2)
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    def find_available_port(self, start_port: int, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port"""
        # First, check if the preferred default ports are available
        DEFAULT_BACKEND_PORT = 5001
        DEFAULT_FRONTEND_PORT = 3000
        
        # If we're looking for a backend port and default is free, prefer it
        if start_port > DEFAULT_BACKEND_PORT and not self.is_port_in_use(DEFAULT_BACKEND_PORT):
            return DEFAULT_BACKEND_PORT
            
        # If we're looking for a frontend port and default is free, prefer it
        if start_port > DEFAULT_FRONTEND_PORT and start_port < 5000 and not self.is_port_in_use(DEFAULT_FRONTEND_PORT):
            return DEFAULT_FRONTEND_PORT
        
        # Otherwise, find next available port
        for port in range(start_port, start_port + max_attempts):
            if not self.is_port_in_use(port):
                return port
        return start_port  # Fallback to original port
    
    def get_port_conflict_process(self, port: int) -> Optional[str]:
        """Get information about the process using a port"""
        try:
            import platform
            
            if platform.system() == "Windows":
                # Use netstat on Windows to find process using port
                result = subprocess.run(['netstat', '-ano'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                # Get process name from PID
                                proc_result = subprocess.run(['tasklist', '/fi', f'PID eq {pid}', '/fo', 'csv'], 
                                                           capture_output=True, text=True, shell=True)
                                if proc_result.returncode == 0 and proc_result.stdout:
                                    lines = proc_result.stdout.strip().split('\n')
                                    if len(lines) > 1:
                                        # Parse CSV output (Image Name is first column)
                                        process_name = lines[1].split(',')[0].strip('"')
                                        return process_name
                return "unknown process"
                
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    pid = result.stdout.strip().split('\n')[0]
                    proc_result = subprocess.run(['ps', '-p', pid, '-o', 'comm='], 
                                               capture_output=True, text=True)
                    if proc_result.returncode == 0:
                        return proc_result.stdout.strip()
                        
            elif platform.system() == "Linux":
                # Try multiple methods for Linux
                # Method 1: ss command (preferred)
                try:
                    result = subprocess.run(['ss', '-tlnp', f'sport = :{port}'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:  # Skip header
                            if f':{port}' in line:
                                # Parse ss output to extract process info
                                parts = line.split()
                                if len(parts) >= 6 and 'users:' in parts[-1]:
                                    return "process found via ss"
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pass
                
                # Method 2: netstat fallback
                try:
                    result = subprocess.run(['netstat', '-tlnp'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if f':{port}' in line and 'LISTEN' in line:
                                return "process found via netstat"
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pass
                    
                return "unknown process"
                
        except Exception as e:
            # Fallback: just indicate something is using the port
            pass
        return None
    
    def handle_port_conflict(self, service: str, port: int) -> int:
        """Handle port conflicts by suggesting alternatives and updating config"""
        process_info = self.get_port_conflict_process(port)
        
        if process_info:
            if "ControlCenter" in process_info or port == 5000:
                self.print_status(f"Port {port} is used by AirPlay Receiver (ControlCenter)", "warning")
                self.print_status("Tip: You can disable AirPlay Receiver in System Settings -> General -> AirDrop & Handoff", "info")
            else:
                self.print_status(f"Port {port} is in use by: {process_info}", "warning")
        else:
            self.print_status(f"Port {port} is already in use", "warning")
        
        # Find alternative port
        new_port = self.find_available_port(port + 1)
        if new_port != port:
            self.print_status(f"Suggesting alternative port {new_port} for {service}", "info")
            
            # Update config
            if service == "backend":
                self.config['backend_port'] = new_port
            elif service == "frontend":
                self.config['frontend_port'] = new_port
            
            self.save_config(self.config)
            self.print_status(f"Updated config.json with new {service} port: {new_port}", "success")
            
            # Sync OAuth config if frontend port changed
            if service == "frontend":
                self.sync_oauth_config(new_port)
            
            return new_port
        else:
            self.print_status(f"Could not find alternative port for {service}", "error")
            return port
        
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
            self.print_status("Core Python dependencies: OK", "success")
        except ImportError as e:
            self.print_status(f"Missing Python dependency: {e}", "error")
            self.print_status("", "info")  # Blank line
            self.print_status("🔧 To fix this issue:", "info")
            self.print_status("   1. pip install -r backend/requirements.txt", "info")
            self.print_status("   2. Or run: python3 run.py install", "info")
            return False
            
        # Check OAuth dependencies (optional but recommended)
        oauth_deps_missing = []
        try:
            import psycopg2
        except ImportError:
            oauth_deps_missing.append("psycopg2-binary")
            
        try:
            import jwt
        except ImportError:
            oauth_deps_missing.append("PyJWT")
            
        try:
            from google.auth import default
        except ImportError:
            oauth_deps_missing.append("google-auth")
            
        try:
            from flask_limiter import Limiter
        except ImportError:
            oauth_deps_missing.append("Flask-Limiter")
            
        try:
            import dotenv
        except ImportError:
            oauth_deps_missing.append("python-dotenv")
        
        if oauth_deps_missing:
            self.print_status(f"Optional OAuth dependencies missing: {', '.join(oauth_deps_missing)}", "warning")
            self.print_status("OAuth user accounts will be disabled", "detail", 1)
            self.print_status("To enable OAuth: pip install -r backend/requirements.txt", "detail", 1)
        else:
            self.print_status("OAuth dependencies: OK", "success")
            
        # Check Node.js and npm
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.print_status(f"Node.js: {result.stdout.strip()}", "success")
            else:
                raise subprocess.CalledProcessError(1, "node")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_status("Node.js not found", "error")
            self.print_status("", "info")  # Blank line
            self.print_status("🔧 To fix this issue:", "info")
            self.print_status("   1. Install Node.js from https://nodejs.org/", "info")
            self.print_status("   2. Choose the LTS version (recommended)", "info")
            self.print_status("   3. Restart your terminal after installation", "info")
            return False
        
        # Find npm command
        npm_cmd = self.find_npm_command()
        if not npm_cmd:
            self.print_status("npm not found", "error")
            self.print_status("", "info")  # Blank line
            self.print_status("🔧 To fix this issue:", "info")
            self.print_status("   1. npm should come with Node.js installation", "info")
            self.print_status("   2. Try restarting your terminal", "info")
            self.print_status("   3. Verify Node.js installation: node --version", "info")
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
            self.print_status("", "info")  # Blank line
            self.print_status("🔧 To fix this issue:", "info")
            self.print_status(f"   1. {npm_cmd} install", "info")
            self.print_status("   2. Or run: python3 run.py install", "info")
            return False
        
        # Check for Rollup dependency issues (Windows and WSL)
        import platform
        import os
        is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
        
        if platform.system() == "Windows" and not is_wsl:
            rollup_native = self.frontend_dir / "node_modules" / "@rollup" / "rollup-win32-x64-msvc"
            if not rollup_native.exists():
                self.print_status("Windows Rollup dependency issue detected", "warning", 1)
                self.print_status("This is a known npm bug. Attempting to fix...", "info", 2)
                return self._fix_windows_dependencies(npm_cmd)
        elif is_wsl:
            rollup_native = self.frontend_dir / "node_modules" / "@rollup" / "rollup-linux-x64-gnu"
            if not rollup_native.exists():
                self.print_status("WSL Rollup dependency issue detected", "warning", 1)
                self.print_status("This is a known npm bug. Attempting to fix...", "info", 2)
                return self._fix_windows_dependencies(npm_cmd)
        
        self.print_status("Node modules installed", "success", 1)
        
        # Check network connectivity for web scraping
        if not self._check_network_connectivity():
            self.print_status("Network connectivity issue detected", "warning", 1)
            self.print_status("App will start but may have issues scraping spell data", "detail", 2)
        
        # Check OAuth configuration status
        self._check_oauth_configuration()
            
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
    
    def _check_network_connectivity(self) -> bool:
        """Check if we can reach the spell data source"""
        try:
            import urllib.request
            import urllib.error
            
            # Test connectivity to the spell data source
            test_url = "https://alla.clumsysworld.com/"
            request = urllib.request.Request(test_url)
            request.add_header('User-Agent', 'EQDataScraper/1.0')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return False
        except Exception:
            # Any other error, assume connectivity is fine
            return True
    
    def _check_oauth_configuration(self):
        """Check OAuth configuration and provide status information"""
        try:
            from dotenv import load_dotenv
            
            # Load environment files to check OAuth settings
            backend_env_file = self.backend_dir / ".env"
            if backend_env_file.exists():
                load_dotenv(backend_env_file)
            
            root_env_file = self.root_dir / ".env"
            if root_env_file.exists():
                load_dotenv(root_env_file, override=False)
            
            # Check if OAuth is enabled
            oauth_enabled = os.environ.get('ENABLE_USER_ACCOUNTS', '').lower() == 'true'
            
            if oauth_enabled:
                # Check required OAuth environment variables
                oauth_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'JWT_SECRET_KEY', 'OAUTH_REDIRECT_URI']
                configured_vars = sum(1 for var in oauth_vars if os.environ.get(var))
                
                if configured_vars == len(oauth_vars):
                    self.print_status("OAuth system: READY", "success", 1)
                elif configured_vars > 0:
                    self.print_status(f"OAuth system: INCOMPLETE ({configured_vars}/{len(oauth_vars)} configured)", "warning", 1)
                else:
                    self.print_status("OAuth system: NOT CONFIGURED", "warning", 1)
                
                # Check database configuration
                if os.environ.get('DATABASE_URL'):
                    self.print_status("Database: configured", "success", 2)
                else:
                    self.print_status("Database: using local fallback", "info", 2)
                
                # Check OAuth redirect URI consistency (without showing actual values)
                redirect_uri = os.environ.get('OAUTH_REDIRECT_URI', '')
                frontend_port = self.config.get('frontend_port', 3000)
                expected_redirect = f"http://localhost:{frontend_port}/auth/callback"
                
                if redirect_uri == expected_redirect:
                    self.print_status("OAuth redirect URI: synchronized", "success", 2)
                elif redirect_uri and 'localhost' in redirect_uri:
                    self.print_status("OAuth redirect URI: port mismatch detected", "warning", 2)
                    
            else:
                self.print_status("OAuth system: DISABLED", "info", 1)
                
        except ImportError:
            # python-dotenv not available
            pass
        except Exception:
            # Any other error during OAuth check, don't fail startup
            pass
    
    def _verify_services_health(self):
        """Verify that services are actually responding"""
        self.print_status("Verifying service health...", "info")
        
        # Check backend health
        try:
            import urllib.request
            import urllib.error
            
            backend_url = f"http://localhost:{self.config['backend_port']}/api/health"
            request = urllib.request.Request(backend_url)
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    self.print_status("✓ Backend API is responding", "success")
                else:
                    self.print_status(f"⚠ Backend API returned status {response.status}", "warning")
        except urllib.error.URLError:
            self.print_status("⚠ Backend API not yet responding (may still be starting up)", "warning")
        except Exception as e:
            self.print_status(f"⚠ Could not verify backend health: {e}", "warning")
        
        # Check frontend health (basic connectivity)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('localhost', self.config['frontend_port']))
                if result == 0:
                    self.print_status("✓ Frontend server is accepting connections", "success")
                else:
                    self.print_status("⚠ Frontend server not yet accepting connections", "warning")
        except Exception as e:
            self.print_status(f"⚠ Could not verify frontend connectivity: {e}", "warning")
    
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
    
    def _terminate_process_by_pid(self, pid: int):
        """Terminate a process by PID in a cross-platform way"""
        import platform
        
        if platform.system() == "Windows":
            # On Windows, use taskkill
            try:
                subprocess.run(['taskkill', '/PID', str(pid), '/F'], 
                             capture_output=True, text=True, shell=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Fallback to direct process termination if available
                try:
                    import psutil
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    pass
        else:
            # On Unix systems, use os.kill with signals
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                if self.is_process_running(pid):
                    os.kill(pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
            
    def start_backend(self, allocated_ports: Dict[str, int]) -> bool:
        """Start the Flask backend server"""
        self.print_status("Starting backend server...", "step", 1)
        
        backend_port = allocated_ports.get('backend', self.config['backend_port'])
        
        try:
            # Change to backend directory and start Flask app
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.root_dir)
            env['BACKEND_PORT'] = str(backend_port)
            
            # Load environment variables from .env files for OAuth support
            # Check if python-dotenv is available and load .env files
            try:
                from dotenv import load_dotenv
                # Load backend .env file first (higher priority)
                backend_env_file = self.backend_dir / ".env"
                if backend_env_file.exists():
                    load_dotenv(backend_env_file)
                    self.print_status("Loaded backend OAuth configuration", "detail", 2)
                    
                # Load root .env file for any additional variables
                root_env_file = self.root_dir / ".env"
                if root_env_file.exists():
                    load_dotenv(root_env_file, override=False)  # Don't override backend settings
                    
                # Copy loaded environment variables to subprocess environment
                oauth_vars = [
                    'ENABLE_USER_ACCOUNTS', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
                    'JWT_SECRET_KEY', 'ENCRYPTION_KEY', 'OAUTH_REDIRECT_URI', 'DATABASE_URL'
                ]
                for var in oauth_vars:
                    if var in os.environ:
                        env[var] = os.environ[var]
                        
            except ImportError:
                # python-dotenv not available, OAuth will use system environment variables only
                self.print_status("python-dotenv not available, using system environment only", "detail", 2)
            
            # Platform-specific subprocess creation
            import platform
            creation_flags = 0
            if platform.system() == "Windows":
                # On Windows, prevent console window popup
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creation_flags if platform.system() == "Windows" else 0
            )
            
            self.processes["backend"] = process
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            if process.poll() is None:
                self.print_status(f"Backend ready on port {backend_port}", "success", 2)
                return True
            else:
                stdout, stderr = process.communicate()
                error_msg = stderr.strip()
                self.print_status(f"Backend failed to start: {error_msg}", "error", 2)
                return False
                
        except Exception as e:
            self.print_status(f"Error starting backend: {e}", "error", 2)
            return False
            
    def start_frontend(self, allocated_ports: Dict[str, int]) -> bool:
        """Start the Vite frontend development server"""
        import platform
        self.print_status("Starting frontend development server...", "step", 1)
        
        frontend_port = allocated_ports.get('frontend', self.config['frontend_port'])
        
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
            
            # Set environment variable for Vite port
            env = os.environ.copy()
            env['PORT'] = str(frontend_port)
            env['VITE_PORT'] = str(frontend_port)
            
            # Always use list format for better cross-platform compatibility
            commands_to_try = [
                [self.npm_command, "run", "dev", "--", "--port", str(frontend_port)],
                ["npx", "vite", "--port", str(frontend_port)],
                ["node", str(vite_js_path), "--port", str(frontend_port)] if vite_js_path.exists() else ["npx", "vite", "--port", str(frontend_port)]
            ]
            
            use_shell = False  # Use shell=False for better compatibility
            
            for cmd in commands_to_try:
                try:
                    cmd_str = ' '.join(cmd)
                    self.print_status(f"Trying: {cmd_str}", "detail", 2)
                    
                    # Platform-specific subprocess creation
                    creation_flags = 0
                    if platform.system() == "Windows":
                        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
                        use_shell = True  # npm.cmd requires shell on Windows
                    
                    process = subprocess.Popen(
                        cmd,
                        cwd=self.frontend_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=use_shell,
                        env=env,
                        creationflags=creation_flags if platform.system() == "Windows" else 0
                    )
                    
                    # Wait for Vite to start
                    time.sleep(5)  # Give more time for Vite to start
                    if process.poll() is None:
                        self.processes["frontend"] = process
                        self.print_status(f"Frontend ready on port {frontend_port}", "success", 2)
                        return True
                    else:
                        # Process failed - get error output
                        stdout, stderr = process.communicate()
                        error_msg = stderr.strip() if stderr and stderr.strip() else stdout.strip()
                        self.print_status(f"Command failed: {error_msg}", "warning", 3)
                        continue
                        
                except Exception as e:
                    self.print_status(f"Error: {e}", "warning", 3)
                    continue
            
            self.print_status("All frontend start commands failed", "error", 2)
            return False
                
        except Exception as e:
            self.print_status(f"Error starting frontend: {e}", "error", 2)
            return False
            
    def start_services(self):
        """Start both frontend and backend services"""
        self.print_header("Starting EQDataScraper Application")
        
        if self.skip_dependency_check:
            self.print_status("Skipping dependency check as requested", "warning")
        elif not self.check_dependencies():
            print()
            self.print_status("Dependency check failed. Please resolve issues and try again.", "error")
            self.print_status("Use --skip-deps to bypass this check (not recommended)", "detail")
            return
        
        # Smart port allocation
        allocated_ports = self.smart_port_allocation()
        
        success = True
        self.running = True
        
        # Start backend first
        if not self.start_backend(allocated_ports):
            success = False
            
        # Start frontend
        if success and not self.start_frontend(allocated_ports):
            success = False
            
        if success:
            self.save_pids()
            print()
            self.print_section("Application Ready")
            self.print_status(f"Frontend: http://localhost:{allocated_ports['frontend']}", "success", 1)
            self.print_status(f"Backend API: http://localhost:{allocated_ports['backend']}", "success", 1)
            print()
            self.print_status("Press Ctrl+C to stop all services", "info")
            self.print_status("Press Ctrl+R to restart all services", "info")
            
            # Verify services are actually responding
            print()
            self._verify_services_health()
            
            # Start keyboard listener
            self.setup_keyboard_handler()
            
            try:
                # Wait for processes and handle Ctrl+C
                while self.running:
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
                    
                    # Check if restart was requested
                    if self.restart_requested:
                        self.print_status("\n🔄 Restart requested...", "info")
                        self.restart_services()
                        self.restart_requested = False
                    
                    time.sleep(0.5)  # Check more frequently for keyboard input
            except KeyboardInterrupt:
                self.print_status("\nShutting down services...", "info")
                self.stop_services()
            finally:
                self.cleanup_keyboard_handler()
                self.running = False
        else:
            self.stop_services()
            self.cleanup_keyboard_handler()
            self.running = False
            
    def stop_services(self):
        """Stop all running services"""
        self.print_header("Stopping EQDataScraper Application")
        
        # Load PIDs from file if processes dict is empty
        if not self.processes:
            pids = self.load_pids()
            for name, pid in pids.items():
                if self.is_process_running(pid):
                    self.print_status(f"Found running {name} service (PID: {pid})", "info", 1)
                    try:
                        self._terminate_process_by_pid(pid)
                        self.print_status(f"Stopped {name} service", "success", 1)
                    except (OSError, ProcessLookupError):
                        self.print_status(f"Could not stop {name} service", "warning", 1)
        else:
            # Stop processes from current session
            for name, process in self.processes.items():
                try:
                    if process and process.poll() is None:  # Process is still running
                        self.print_status(f"Stopping {name}...", "step", 1)
                        process.terminate()
                        
                        # Wait for graceful shutdown
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.print_status(f"Force killing {name}...", "warning", 2)
                            process.kill()
                            try:
                                process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pass  # Process might be forcefully killed
                        
                        self.print_status(f"Stopped {name}", "success", 1)
                    else:
                        self.print_status(f"{name} was already stopped", "info", 1)
                except Exception as e:
                    self.print_status(f"Error stopping {name}: {e}", "error", 1)
                    
        # Clean up PID file
        if self.pids_file.exists():
            self.pids_file.unlink()
            
        self.print_status("All services stopped", "success", 1)
        
    def status(self):
        """Check status of services"""
        self.print_header("EQDataScraper Service Status")
        
        pids = self.load_pids()
        
        if not pids:
            self.print_status("No services are currently tracked", "info", 1)
            # Check if services might be running without tracking
            self._check_untracked_services()
            return
            
        services_running = False
        for name, pid in pids.items():
            if self.is_process_running(pid):
                self.print_status(f"{name.capitalize()}: Running (PID: {pid})", "success", 1)
                services_running = True
            else:
                self.print_status(f"{name.capitalize()}: Not running", "error", 1)
        
        if services_running:
            print()
            self._verify_services_health()
    
    def _check_untracked_services(self):
        """Check if services are running but not tracked"""
        self.print_status("Checking for untracked services...", "step", 1)
        
        # Check if ports are in use
        backend_port = self.config['backend_port']
        frontend_port = self.config['frontend_port']
        
        if self.is_port_in_use(backend_port):
            process_info = self.get_port_conflict_process(backend_port)
            if process_info and "Python" in process_info:
                self.print_status(f"Backend may be running on port {backend_port} (untracked)", "warning", 2)
        
        if self.is_port_in_use(frontend_port):
            process_info = self.get_port_conflict_process(frontend_port)
            if process_info and ("node" in process_info or "vite" in process_info):
                self.print_status(f"Frontend may be running on port {frontend_port} (untracked)", "warning", 2)
        
        if self.is_port_in_use(backend_port) or self.is_port_in_use(frontend_port):
            self.print_status("Use 'python3 run.py stop' to clean up untracked services", "detail", 2)
    
    def _is_deployment_environment(self) -> bool:
        """Check if we're running in a deployment environment"""
        # Railway provides these environment variables
        railway_indicators = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID']
        
        # Common deployment environment indicators
        deployment_indicators = ['DYNO', 'HEROKU_APP_NAME', 'RENDER', 'VERCEL', 'NETLIFY']
        
        # Check for Railway
        if any(os.environ.get(var) for var in railway_indicators):
            return True
            
        # Check for other deployment platforms
        if any(os.environ.get(var) for var in deployment_indicators):
            return True
            
        # Check if PORT is set (common in deployments)
        if os.environ.get('PORT') and os.environ.get('NODE_ENV') == 'production':
            return True
            
        return False
    
    def setup_keyboard_handler(self):
        """Setup keyboard handler for Ctrl+R restart functionality"""
        # Skip keyboard handlers in deployment environments
        if self._is_deployment_environment():
            return
            
        try:
            import platform
            if platform.system() == "Windows":
                # Windows-specific keyboard handling
                self._setup_windows_keyboard_handler()
            else:
                # Unix-like systems
                self._setup_unix_keyboard_handler()
        except Exception as e:
            # Silently fail keyboard handler setup
            pass
    
    def _setup_unix_keyboard_handler(self):
        """Setup keyboard handler for Unix-like systems"""
        if not HAS_UNIX_TERMINAL:
            return
        
        try:
            # Save current terminal settings
            self.old_termios = termios.tcgetattr(sys.stdin)
            
            # Set terminal to raw mode for capturing key presses
            new_settings = termios.tcgetattr(sys.stdin)
            new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)
            
            # Start keyboard listener thread
            keyboard_thread = threading.Thread(target=self._keyboard_listener_unix, daemon=True)
            keyboard_thread.start()
        except Exception:
            # Fallback if terminal manipulation fails
            pass
    
    def _setup_windows_keyboard_handler(self):
        """Setup keyboard handler for Windows"""
        if not HAS_WINDOWS_TERMINAL:
            return
            
        try:
            keyboard_thread = threading.Thread(target=self._keyboard_listener_windows, daemon=True)
            keyboard_thread.start()
        except Exception:
            pass
    
    def _keyboard_listener_unix(self):
        """Keyboard listener for Unix-like systems"""
        try:
            while self.running:
                # Check if input is available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char == '\x12':  # Ctrl+R
                        self.restart_requested = True
        except Exception:
            pass
    
    def _keyboard_listener_windows(self):
        """Keyboard listener for Windows"""
        if not HAS_WINDOWS_TERMINAL:
            return
            
        try:
            while self.running:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\x12':  # Ctrl+R
                        self.restart_requested = True
                time.sleep(0.1)
        except Exception:
            pass
    
    def cleanup_keyboard_handler(self):
        """Cleanup keyboard handler"""
        if HAS_UNIX_TERMINAL:
            try:
                if self.old_termios and sys.stdin.isatty():
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_termios)
            except Exception:
                pass
    
    def restart_services(self):
        """Restart all services"""
        self.print_status("Stopping services for restart...", "info")
        
        # Stop current services
        for name, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=2)
            except Exception:
                pass
        
        # Clear processes
        self.processes.clear()
        
        # Clean up PID file
        if self.pids_file.exists():
            self.pids_file.unlink()
        
        time.sleep(2)  # Brief pause before restart
        
        # Restart with smart port allocation
        self.print_status("Starting services...", "info")
        allocated_ports = self.smart_port_allocation()
        
        # Start backend
        if self.start_backend(allocated_ports):
            # Start frontend
            if self.start_frontend(allocated_ports):
                self.save_pids()
                self.print_status("\n🎉 Services restarted successfully!", "success")
                self.print_status(f"Frontend: http://localhost:{allocated_ports['frontend']}", "info")
                self.print_status(f"Backend API: http://localhost:{allocated_ports['backend']}", "info")
                self.print_status("\nPress Ctrl+C to stop all services", "info")
                self.print_status("Press Ctrl+R to restart all services", "info")
                self._verify_services_health()
            else:
                self.print_status("Failed to restart frontend", "error")
                self.stop_services()
                self.running = False
        else:
            self.print_status("Failed to restart backend", "error")
            self.stop_services()
            self.running = False
    
    def restart_command(self):
        """Restart services from command line"""
        self.print_header("Restarting EQDataScraper Application")
        
        # First stop any running services
        self.stop_services()
        
        # Wait a moment
        time.sleep(2)
        
        # Start services again
        self.start_services()
                
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
        self.print_status("", "info")  # Blank line
        
        # Show platform-appropriate start command
        import platform
        if platform.system() == "Windows":
            self.print_status("🚀 Ready to start! Run: run.bat start", "success")
            self.print_status("   Or: python run.py start", "info")
        else:
            self.print_status("🚀 Ready to start! Run: python3 run.py start", "success")
            self.print_status("   Or: ./run.sh start", "info")
    
    def _is_setup_complete(self) -> bool:
        """Check if the application appears to be set up"""
        # Check for key indicators that setup is complete
        node_modules_exists = (self.frontend_dir / "node_modules").exists()
        critical_packages = ["vite", "vue", "@vitejs/plugin-vue"]
        packages_exist = all((self.frontend_dir / "node_modules" / pkg).exists() for pkg in critical_packages)
        
        try:
            # Try importing Python dependencies
            import flask, requests, pandas
            from bs4 import BeautifulSoup
            python_deps_ok = True
        except ImportError:
            python_deps_ok = False
        
        return node_modules_exists and packages_exist and python_deps_ok
    
    def _show_first_time_setup_message(self):
        """Show helpful first-time setup message"""
        import platform
        
        self.print_header("First-Time Setup Required")
        self.print_status("🚨 It looks like this is your first time running EQDataScraper!", "warning")
        self.print_status("", "info")
        self.print_status("📋 Quick Setup Steps:", "info")
        
        if platform.system() == "Windows":
            self.print_status("   1. run.bat install       # Install dependencies", "info")
            self.print_status("   2. run.bat start         # Start the application", "info")
            self.print_status("   3. Open http://localhost:3000 in your browser", "info")
            self.print_status("", "info")
            self.print_status("⚡ Or run 'run.bat install' now to get started!", "success")
        else:
            self.print_status("   1. python3 run.py install  # Install dependencies", "info")
            self.print_status("   2. python3 run.py start    # Start the application", "info")
            self.print_status("   3. Open http://localhost:3000 in your browser", "info")
            self.print_status("", "info")
            self.print_status("⚡ Or run 'python3 run.py install' now to get started!", "success")
        self.print_status("", "info")

def main():
    # Check if we're in a deployment environment and warn about usage
    runner = AppRunner()
    if runner._is_deployment_environment() and len(sys.argv) > 1 and sys.argv[1] == "start":
        print("⚠️  Deployment environment detected")
        print("   Smart port management will use environment variables only")
        print("   For production, consider starting services directly:")
        print("   Backend: python backend/app.py")
        print("   Frontend: npm run build && npm run preview")
    
    parser = argparse.ArgumentParser(description="EQDataScraper Application Runner",
                                   formatter_class=argparse.RawDescriptionHelpFormatter,
                                   epilog="""
Examples:
  python3 run.py install    # First-time setup: install all dependencies
  python3 run.py start      # Start both frontend and backend services
  python3 run.py status     # Check if services are running
  python3 run.py stop       # Stop all services
  python3 run.py restart    # Restart all services

Platform-specific shortcuts:
  Windows: run.bat [command]
  Unix/Linux/macOS: ./run.sh [command]

First-time setup:
  1. python3 run.py install (or run.bat install on Windows)
  2. python3 run.py start (or run.bat start on Windows)
  3. Open http://localhost:3000 in your browser

For help with common issues, see the README.md file.
""")
    parser.add_argument("command", choices=["start", "stop", "status", "install", "restart"], 
                       help="Command to execute")
    parser.add_argument("--skip-deps", "--ignore-deps", action="store_true",
                       help="Skip dependency checking (use with caution)")
    
    args = parser.parse_args()
    runner = AppRunner()
    runner.skip_dependency_check = args.skip_deps
    
    # Check for first-time setup
    if not runner._is_setup_complete() and args.command != "install":
        runner._show_first_time_setup_message()
    
    if args.command == "start":
        runner.start_services()
    elif args.command == "stop":
        runner.stop_services()
    elif args.command == "status":
        runner.status()
    elif args.command == "install":
        runner.install_deps()
    elif args.command == "restart":
        runner.restart_command()

if __name__ == "__main__":
    main()