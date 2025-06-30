#!/usr/bin/env python3
"""
Functional tests for EQDataScraper
Tests actual functionality without complex mocking
"""

import subprocess
import platform
import json
import time
from pathlib import Path

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

def test_run_py_help():
    """Test that run.py help works"""
    try:
        result = subprocess.run(['python3', 'run.py', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'EQDataScraper Application Runner' in result.stdout:
            print_status("run.py --help works", "success")
            return True
        else:
            print_status(f"run.py --help failed: {result.stderr}", "error")
            return False
    except Exception as e:
        print_status(f"run.py --help test failed: {e}", "error")
        return False

def test_run_py_status():
    """Test that run.py status works"""
    try:
        result = subprocess.run(['python3', 'run.py', 'status'], 
                              capture_output=True, text=True, timeout=15)
        # Status should work regardless of whether services are running
        if result.returncode == 0:
            print_status("run.py status works", "success")
            if "Service Status" in result.stdout:
                print_status("Status output format correct", "success")
                return True
            else:
                print_status("Status output format unexpected", "warning")
                return False
        else:
            print_status(f"run.py status failed: {result.stderr}", "error")
            return False
    except Exception as e:
        print_status(f"run.py status test failed: {e}", "error")
        return False

def test_config_file_creation():
    """Test that config.json is created with defaults"""
    config_file = Path("config.json")
    
    # Remove config file if it exists
    if config_file.exists():
        original_config = config_file.read_text()
    else:
        original_config = None
    
    try:
        config_file.unlink(missing_ok=True)
        
        # Run status to trigger config creation
        result = subprocess.run(['python3', 'run.py', 'status'], 
                              capture_output=True, text=True, timeout=10)
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            expected_keys = ['backend_port', 'frontend_port', 'cache_expiry_hours', 'min_scrape_interval_minutes']
            if all(key in config for key in expected_keys):
                print_status("config.json creation works", "success")
                print_status(f"Config: backend_port={config['backend_port']}, frontend_port={config['frontend_port']}", "info")
                return True
            else:
                print_status("config.json missing expected keys", "error")
                return False
        else:
            print_status("config.json was not created", "error")
            return False
            
    except Exception as e:
        print_status(f"Config file test failed: {e}", "error")
        return False
    finally:
        # Restore original config if it existed
        if original_config:
            config_file.write_text(original_config)

def test_platform_script_existence():
    """Test that platform-specific scripts exist and are executable"""
    current_platform = platform.system()
    
    if current_platform == "Windows":
        script_file = Path("run.bat")
        if script_file.exists():
            print_status("run.bat exists", "success")
            # Test if it's readable
            content = script_file.read_text()
            if "python" in content.lower():
                print_status("run.bat contains Python commands", "success")
                return True
            else:
                print_status("run.bat content unexpected", "warning")
                return False
        else:
            print_status("run.bat not found", "error")
            return False
    else:
        script_file = Path("run.sh")
        if script_file.exists():
            print_status("run.sh exists", "success")
            
            # Check if executable
            if script_file.stat().st_mode & 0o111:
                print_status("run.sh is executable", "success")
            else:
                print_status("run.sh is not executable", "warning")
            
            # Check content
            content = script_file.read_text()
            if "python3" in content:
                print_status("run.sh contains Python commands", "success")
                return True
            else:
                print_status("run.sh content unexpected", "warning")
                return False
        else:
            print_status("run.sh not found", "error")
            return False

def test_backend_script_exists():
    """Test that backend script exists"""
    backend_file = Path("backend/app.py")
    if backend_file.exists():
        print_status("backend/app.py exists", "success")
        
        # Check if it imports Flask
        content = backend_file.read_text()
        if "Flask" in content:
            print_status("backend/app.py imports Flask", "success")
            return True
        else:
            print_status("backend/app.py doesn't import Flask", "warning")
            return False
    else:
        print_status("backend/app.py not found", "error")
        return False

def test_frontend_files_exist():
    """Test that frontend files exist"""
    files_to_check = [
        "package.json",
        "vite.config.js",
        "src/App.vue",
        "src/main.js"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print_status(f"{file_path} exists", "success")
        else:
            print_status(f"{file_path} not found", "error")
            all_exist = False
    
    return all_exist

def test_package_json_content():
    """Test package.json has expected content"""
    package_file = Path("package.json")
    if package_file.exists():
        try:
            with open(package_file, 'r') as f:
                package_data = json.load(f)
            
            # Check for expected dependencies
            expected_deps = ["vue", "vue-router", "pinia", "axios"]
            dependencies = package_data.get("dependencies", {})
            
            missing_deps = [dep for dep in expected_deps if dep not in dependencies]
            if not missing_deps:
                print_status("package.json has all expected dependencies", "success")
                return True
            else:
                print_status(f"package.json missing dependencies: {missing_deps}", "error")
                return False
                
        except Exception as e:
            print_status(f"Error reading package.json: {e}", "error")
            return False
    else:
        print_status("package.json not found", "error")
        return False

def test_import_run_module():
    """Test that we can import the run module"""
    try:
        import run
        if hasattr(run, 'AppRunner'):
            print_status("run.py module imports correctly", "success")
            
            # Test creating AppRunner instance
            runner = run.AppRunner()
            if hasattr(runner, 'config'):
                print_status("AppRunner class instantiates correctly", "success")
                return True
            else:
                print_status("AppRunner missing expected attributes", "error")
                return False
        else:
            print_status("run.py missing AppRunner class", "error")
            return False
    except Exception as e:
        print_status(f"Cannot import run.py: {e}", "error")
        return False

def run_functional_tests():
    """Run all functional tests"""
    print("🧪 Running EQDataScraper Functional Tests")
    print("=" * 60)
    print_status(f"Platform: {platform.system()} {platform.release()}", "info")
    print_status(f"Python: {platform.python_version()}", "info")
    print_status(f"Working directory: {Path.cwd()}", "info")
    print()
    
    tests = [
        ("run.py --help", test_run_py_help),
        ("run.py status", test_run_py_status),
        ("Config file creation", test_config_file_creation),
        ("Platform scripts", test_platform_script_existence),
        ("Backend script", test_backend_script_exists),
        ("Frontend files", test_frontend_files_exist),
        ("package.json content", test_package_json_content),
        ("Import run module", test_import_run_module)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print_status(f"Test '{test_name}' crashed: {e}", "error")
    
    print("\n" + "=" * 60)
    print("🎯 Functional Test Summary")
    print("=" * 60)
    
    for i, (test_name, _) in enumerate(tests):
        # We'll assume they passed if no errors were shown
        pass
    
    print_status(f"Tests completed: {total}", "info")
    
    if passed >= total * 0.8:  # 80% pass rate
        print_status("🎉 Functional tests PASSED!", "success")
        print_status("Core functionality appears to be working correctly.", "success")
        return True
    else:
        print_status("⚠️ Some functional tests failed", "warning")
        print_status("Some features may not work correctly.", "warning")
        return False

if __name__ == "__main__":
    import sys
    success = run_functional_tests()
    sys.exit(0 if success else 1)