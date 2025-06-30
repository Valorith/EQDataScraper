#!/usr/bin/env python3
"""
Manual Platform Validation Script
Performs real-world tests of platform-specific functionality
"""

import platform
import subprocess
import socket
import time
import sys
import json
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(message, status="info"):
    colors = {
        "info": '\033[94m',
        "success": '\033[92m', 
        "warning": '\033[93m',
        "error": '\033[91m'
    }
    prefixes = {
        "info": "ℹ",
        "success": "✅",
        "warning": "⚠",
        "error": "❌"
    }
    
    color = colors.get(status, '\033[0m')
    prefix = prefixes.get(status, "•")
    reset = '\033[0m'
    
    print(f"{color}{prefix} {message}{reset}")

def test_platform_detection():
    """Test platform detection capabilities"""
    print_header("Platform Detection Tests")
    
    detected_platform = platform.system()
    print_status(f"Detected platform: {detected_platform}", "success")
    print_status(f"Platform release: {platform.release()}", "info")
    print_status(f"Python version: {platform.python_version()}", "info")
    print_status(f"Architecture: {platform.machine()}", "info")
    
    # Test WSL detection
    if detected_platform == "Linux":
        is_wsl = Path('/mnt/c').exists()
        if is_wsl:
            print_status("WSL environment detected", "warning")
        else:
            print_status("Native Linux environment", "success")
    
    return True

def test_command_availability():
    """Test availability of platform-specific commands"""
    print_header("Command Availability Tests")
    
    commands_to_test = {
        "Windows": ["tasklist", "taskkill", "netstat", "where"],
        "Darwin": ["lsof", "ps", "which"],
        "Linux": ["ss", "netstat", "ps", "which", "pkill"]
    }
    
    current_platform = platform.system()
    commands = commands_to_test.get(current_platform, [])
    
    available_commands = []
    missing_commands = []
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--help'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0 or 'usage' in result.stderr.lower():
                available_commands.append(cmd)
                print_status(f"Command '{cmd}' is available", "success")
            else:
                missing_commands.append(cmd)
                print_status(f"Command '{cmd}' returned error", "warning")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            missing_commands.append(cmd)
            print_status(f"Command '{cmd}' not found", "error")
    
    return len(missing_commands) == 0

def test_python_command_detection():
    """Test Python command detection"""
    print_header("Python Command Detection")
    
    python_commands = ["python3", "python", "py"]
    
    working_commands = []
    for cmd in python_commands:
        try:
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                working_commands.append(cmd)
                print_status(f"'{cmd}' works: {version}", "success")
            else:
                print_status(f"'{cmd}' returned error", "warning")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print_status(f"'{cmd}' not found", "error")
    
    return len(working_commands) > 0

def test_npm_command_detection():
    """Test npm command detection"""
    print_header("npm Command Detection")
    
    npm_commands = ["npm", "npm.cmd"] if platform.system() == "Windows" else ["npm"]
    
    working_commands = []
    for cmd in npm_commands:
        try:
            shell_required = platform.system() == "Windows" and cmd.endswith('.cmd')
            result = subprocess.run([cmd, "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10,
                                  shell=shell_required)
            if result.returncode == 0:
                version = result.stdout.strip()
                working_commands.append(cmd)
                print_status(f"'{cmd}' works: {version}", "success")
            else:
                print_status(f"'{cmd}' returned error", "warning")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print_status(f"'{cmd}' not found", "error")
    
    if working_commands:
        print_status(f"Best npm command: {working_commands[0]}", "success")
        return True
    else:
        print_status("No working npm command found", "error")
        return False

def test_port_operations():
    """Test port-related operations"""
    print_header("Port Operations Tests")
    
    # Test port availability check
    test_port = 19876  # Unlikely to be in use
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', test_port))
            if result != 0:
                print_status(f"Port {test_port} is available (good)", "success")
            else:
                print_status(f"Port {test_port} is in use (unexpected)", "warning")
    except Exception as e:
        print_status(f"Port check failed: {e}", "error")
        return False
    
    # Test creating a temporary server
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(('localhost', 0))  # Bind to any available port
            actual_port = server.getsockname()[1]
            server.listen(1)
            
            print_status(f"Created test server on port {actual_port}", "success")
            
            # Test that we can detect this port is in use
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_client:
                test_client.settimeout(1)
                result = test_client.connect_ex(('localhost', actual_port))
                if result == 0:
                    print_status("Port conflict detection works", "success")
                else:
                    print_status("Port conflict detection failed", "error")
                    return False
                    
    except Exception as e:
        print_status(f"Server test failed: {e}", "error")
        return False
    
    return True

def test_process_management():
    """Test process management capabilities"""
    print_header("Process Management Tests")
    
    current_platform = platform.system()
    
    if current_platform == "Windows":
        # Test tasklist
        try:
            result = subprocess.run(['tasklist', '/fi', 'PID eq 1'], 
                                  capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                print_status("tasklist command works", "success")
            else:
                print_status("tasklist command failed", "error")
                return False
        except Exception as e:
            print_status(f"tasklist test failed: {e}", "error")
            return False
            
        # Test netstat
        try:
            result = subprocess.run(['netstat', '-an'], 
                                  capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0 and 'TCP' in result.stdout:
                print_status("netstat command works", "success")
            else:
                print_status("netstat command failed", "error")
                return False
        except Exception as e:
            print_status(f"netstat test failed: {e}", "error")
            return False
            
    else:
        # Test Unix commands
        if current_platform == "Darwin":
            # Test lsof
            try:
                result = subprocess.run(['lsof', '-i', ':22'], 
                                      capture_output=True, text=True, timeout=10)
                # lsof returns 1 if no processes found, which is normal
                if result.returncode in [0, 1]:
                    print_status("lsof command works", "success")
                else:
                    print_status("lsof command failed", "error")
                    return False
            except Exception as e:
                print_status(f"lsof test failed: {e}", "error")
                return False
        
        elif current_platform == "Linux":
            # Test ss command
            try:
                result = subprocess.run(['ss', '-tlnp'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print_status("ss command works", "success")
                else:
                    print_status("ss command failed, trying netstat", "warning")
                    
                    # Fallback to netstat
                    result = subprocess.run(['netstat', '-tlnp'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print_status("netstat fallback works", "success")
                    else:
                        print_status("Both ss and netstat failed", "error")
                        return False
            except Exception as e:
                print_status(f"Linux network commands test failed: {e}", "error")
                return False
    
    return True

def test_file_operations():
    """Test file system operations"""
    print_header("File System Operations Tests")
    
    # Test pathlib operations
    try:
        test_dir = Path.cwd() / "test_temp_dir"
        test_file = test_dir / "test_file.json"
        
        # Create directory
        test_dir.mkdir(exist_ok=True)
        print_status("Directory creation works", "success")
        
        # Create file
        test_data = {"test": "data", "platform": platform.system()}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        print_status("File creation works", "success")
        
        # Read file
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        if loaded_data == test_data:
            print_status("File read/write works", "success")
        else:
            print_status("File read/write failed", "error")
            return False
        
        # Cleanup
        test_file.unlink()
        test_dir.rmdir()
        print_status("File cleanup works", "success")
        
    except Exception as e:
        print_status(f"File operations test failed: {e}", "error")
        return False
    
    return True

def test_network_connectivity():
    """Test network connectivity"""
    print_header("Network Connectivity Tests")
    
    try:
        import urllib.request
        import urllib.error
        
        # Test connectivity to a reliable server
        test_urls = [
            "https://www.google.com",
            "https://github.com",
            "https://alla.clumsysworld.com"  # The actual data source
        ]
        
        successful_connections = 0
        
        for url in test_urls:
            try:
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'EQDataScraper-Test/1.0')
                
                with urllib.request.urlopen(request, timeout=10) as response:
                    if response.status == 200:
                        print_status(f"Connection to {url}: OK", "success")
                        successful_connections += 1
                    else:
                        print_status(f"Connection to {url}: Status {response.status}", "warning")
            except urllib.error.URLError as e:
                print_status(f"Connection to {url}: Failed ({e})", "error")
            except Exception as e:
                print_status(f"Connection to {url}: Error ({e})", "error")
        
        if successful_connections > 0:
            print_status(f"Network connectivity: {successful_connections}/{len(test_urls)} successful", "success")
            return True
        else:
            print_status("No successful network connections", "error")
            return False
            
    except Exception as e:
        print_status(f"Network test failed: {e}", "error")
        return False

def run_comprehensive_validation():
    """Run all validation tests"""
    print_header("EQDataScraper Cross-Platform Validation")
    print_status(f"Running on: {platform.system()} {platform.release()}", "info")
    print_status(f"Python version: {platform.python_version()}", "info")
    
    tests = [
        ("Platform Detection", test_platform_detection),
        ("Command Availability", test_command_availability),
        ("Python Command Detection", test_python_command_detection),
        ("npm Command Detection", test_npm_command_detection),
        ("Port Operations", test_port_operations),
        ("Process Management", test_process_management),
        ("File Operations", test_file_operations),
        ("Network Connectivity", test_network_connectivity)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print_status(f"Test '{test_name}' crashed: {e}", "error")
            results[test_name] = False
    
    # Summary
    print_header("Validation Summary")
    
    for test_name, result in results.items():
        status = "success" if result else "error"
        print_status(f"{test_name}: {'PASS' if result else 'FAIL'}", status)
    
    print_status(f"Overall: {passed}/{total} tests passed", 
                "success" if passed == total else "warning")
    
    if passed == total:
        print_status("🎉 All platform compatibility tests PASSED!", "success")
        print_status("The app should work correctly on this platform.", "success")
    else:
        print_status("⚠️  Some tests failed - check platform compatibility", "warning")
        print_status("The app may have issues on this platform.", "warning")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_validation()
    sys.exit(0 if success else 1)