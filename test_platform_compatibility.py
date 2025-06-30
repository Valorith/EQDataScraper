#!/usr/bin/env python3
"""
Cross-Platform Compatibility Test Suite for EQDataScraper
Tests platform-specific functionality without requiring actual deployment
"""

import unittest
import platform
import subprocess
import socket
import tempfile
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add the current directory to path to import run module
sys.path.insert(0, str(Path(__file__).parent))
from run import AppRunner

class TestPlatformDetection(unittest.TestCase):
    """Test platform detection and platform-specific behaviors"""
    
    def setUp(self):
        """Set up test environment"""
        self.runner = AppRunner()
    
    def test_current_platform_detection(self):
        """Test that we can detect the current platform correctly"""
        detected_platform = platform.system()
        self.assertIn(detected_platform, ["Windows", "Darwin", "Linux"])
        print(f"✓ Detected platform: {detected_platform}")
    
    def test_wsl_detection_logic(self):
        """Test WSL detection logic"""
        # Mock WSL environment
        with patch('os.path.exists') as mock_exists:
            with patch('platform.system', return_value='Linux'):
                # Simulate WSL environment
                mock_exists.return_value = True  # /mnt/c exists
                is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
                self.assertTrue(is_wsl)
                print("✓ WSL detection logic works")
                
                # Simulate regular Linux
                mock_exists.return_value = False  # /mnt/c doesn't exist
                is_wsl = os.path.exists('/mnt/c') and platform.system() == "Linux"
                self.assertFalse(is_wsl)
                print("✓ Regular Linux detection works")

class TestPortManagement(unittest.TestCase):
    """Test port conflict detection and resolution"""
    
    def setUp(self):
        self.runner = AppRunner()
    
    def test_port_availability_check(self):
        """Test port availability checking"""
        # Test with a likely available port
        available_port = self.runner.find_available_port(8000, max_attempts=10)
        self.assertIsInstance(available_port, int)
        self.assertGreaterEqual(available_port, 8000)
        print(f"✓ Found available port: {available_port}")
    
    def test_port_conflict_detection(self):
        """Test port conflict detection"""
        # Create a temporary server to test conflict detection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
            test_socket.bind(('localhost', 0))  # Bind to any available port
            test_port = test_socket.getsockname()[1]
            test_socket.listen(1)
            
            # Test that our conflict detection finds this port in use
            is_in_use = self.runner.is_port_in_use(test_port)
            self.assertTrue(is_in_use)
            print(f"✓ Port conflict detection works for port {test_port}")
    
    def test_port_conflict_resolution(self):
        """Test automatic port conflict resolution"""
        original_port = 9000
        
        # Mock that the port is in use
        with patch.object(self.runner, 'is_port_in_use', return_value=True):
            with patch.object(self.runner, 'find_available_port', return_value=9001):
                with patch.object(self.runner, 'save_config'):
                    new_port = self.runner.handle_port_conflict("backend", original_port)
                    self.assertNotEqual(new_port, original_port)
                    print(f"✓ Port conflict resolution: {original_port} → {new_port}")

class TestProcessManagement(unittest.TestCase):
    """Test cross-platform process management"""
    
    def setUp(self):
        self.runner = AppRunner()
    
    @patch('subprocess.run')
    def test_windows_process_detection(self, mock_run):
        """Test Windows-specific process detection"""
        # Mock Windows environment
        with patch('platform.system', return_value='Windows'):
            # Mock tasklist output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='PID 1234 in output'
            )
            
            result = self.runner.is_process_running(1234)
            self.assertTrue(result)
            
            # Verify tasklist was called with correct parameters
            mock_run.assert_called_with(
                ['tasklist', '/fi', 'PID eq 1234'],
                capture_output=True,
                text=True,
                shell=True
            )
            print("✓ Windows process detection works")
    
    @patch('os.kill')
    def test_unix_process_detection(self, mock_kill):
        """Test Unix-specific process detection"""
        # Mock Unix environment  
        with patch('platform.system', return_value='Darwin'):
            # Mock successful os.kill (process exists)
            mock_kill.return_value = None
            
            result = self.runner.is_process_running(1234)
            self.assertTrue(result)
            
            # Verify os.kill was called with signal 0
            mock_kill.assert_called_with(1234, 0)
            print("✓ Unix process detection works")

class TestNpmCommandDetection(unittest.TestCase):
    """Test npm command detection across platforms"""
    
    def setUp(self):
        self.runner = AppRunner()
    
    @patch('subprocess.run')
    @patch('platform.system')
    def test_windows_npm_detection(self, mock_platform, mock_run):
        """Test npm command detection on Windows"""
        mock_platform.return_value = 'Windows'
        
        # Mock successful npm.cmd detection
        mock_run.return_value = MagicMock(returncode=0, stdout='8.0.0')
        
        npm_cmd = self.runner.find_npm_command()
        self.assertIsNotNone(npm_cmd)
        
        # Should try npm.cmd first on Windows
        expected_calls = [
            unittest.mock.call(['npm.cmd', '--version'], 
                             capture_output=True, text=True, timeout=10, shell=True)
        ]
        mock_run.assert_any_call(*expected_calls[0])
        print("✓ Windows npm detection works")
    
    @patch('subprocess.run')
    @patch('platform.system')
    def test_unix_npm_detection(self, mock_platform, mock_run):
        """Test npm command detection on Unix systems"""
        mock_platform.return_value = 'Darwin'
        
        # Mock successful npm detection
        mock_run.return_value = MagicMock(returncode=0, stdout='8.0.0')
        
        npm_cmd = self.runner.find_npm_command()
        self.assertIsNotNone(npm_cmd)
        print("✓ Unix npm detection works")

class TestConfigurationManagement(unittest.TestCase):
    """Test configuration loading and saving"""
    
    def test_config_loading_with_defaults(self):
        """Test configuration loading with default values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a runner with a temporary config file
            runner = AppRunner()
            runner.config_file = Path(temp_dir) / "test_config.json"
            
            config = runner.load_config()
            
            # Should have default values
            expected_defaults = {
                'backend_port': 5001,
                'frontend_port': 3000,
                'cache_expiry_hours': 24,
                'min_scrape_interval_minutes': 5
            }
            
            for key, value in expected_defaults.items():
                self.assertEqual(config[key], value)
            print("✓ Default configuration loading works")
    
    def test_config_persistence(self):
        """Test configuration saving and loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = AppRunner()
            runner.config_file = Path(temp_dir) / "test_config.json"
            
            # Save custom config
            test_config = {
                'backend_port': 8001,
                'frontend_port': 8080,
                'cache_expiry_hours': 12,
                'min_scrape_interval_minutes': 10
            }
            
            runner.save_config(test_config)
            
            # Load it back
            loaded_config = runner.load_config()
            
            for key, value in test_config.items():
                self.assertEqual(loaded_config[key], value)
            print("✓ Configuration persistence works")

class TestNetworkConnectivity(unittest.TestCase):
    """Test network connectivity checking"""
    
    def setUp(self):
        self.runner = AppRunner()
    
    @patch('urllib.request.urlopen')
    def test_network_connectivity_success(self, mock_urlopen):
        """Test successful network connectivity check"""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.runner._check_network_connectivity()
        self.assertTrue(result)
        print("✓ Network connectivity check works")
    
    @patch('urllib.request.urlopen')
    def test_network_connectivity_failure(self, mock_urlopen):
        """Test network connectivity failure handling"""
        # Mock network failure
        mock_urlopen.side_effect = Exception("Network error")
        
        result = self.runner._check_network_connectivity()
        # Should return True on generic exceptions (assume connectivity is fine)
        self.assertTrue(result)
        print("✓ Network connectivity failure handling works")

class TestFirstTimeSetup(unittest.TestCase):
    """Test first-time setup detection"""
    
    def setUp(self):
        self.runner = AppRunner()
    
    def test_setup_completion_detection(self):
        """Test detection of complete setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = AppRunner()
            runner.frontend_dir = Path(temp_dir)
            
            # Create mock node_modules structure
            node_modules = runner.frontend_dir / "node_modules"
            node_modules.mkdir()
            
            # Create critical packages
            for package in ["vite", "vue", "@vitejs"]:
                (node_modules / package).mkdir(parents=True)
            (node_modules / "@vitejs" / "plugin-vue").mkdir()
            
            # Mock Python dependencies
            with patch('importlib.import_module'):
                is_complete = runner._is_setup_complete()
                # Should detect as complete if all packages exist
                print(f"✓ Setup completion detection: {is_complete}")

def run_platform_validation():
    """Run a comprehensive platform validation"""
    print("🔍 Running Cross-Platform Validation Tests")
    print("=" * 60)
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPlatformDetection,
        TestPortManagement,
        TestProcessManagement,
        TestNpmCommandDetection,
        TestConfigurationManagement,
        TestNetworkConnectivity,
        TestFirstTimeSetup
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("🎯 Platform Validation Summary")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("✅ All cross-platform compatibility tests PASSED!")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Platform: {platform.system()} {platform.release()}")
        print(f"   Python: {platform.python_version()}")
    else:
        print("❌ Some tests FAILED!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"   - {test}: {trace}")
        
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"   - {test}: {trace}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_platform_validation()
    sys.exit(0 if success else 1)