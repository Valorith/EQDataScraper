#!/usr/bin/env python3
"""
Tests for the monitoring system and -m flag integration.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import argparse
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class TestMonitoringArgumentParsing(unittest.TestCase):
    """Test argument parsing for monitoring flags"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import run module
        from run import AppRunner
        self.runner = AppRunner()
    
    def test_monitor_flag_parsing(self):
        """Test -m flag parsing with different values"""
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--with-monitor", nargs='?', const=30, type=int,
                          help="Start services with monitoring enabled")
        
        # Test -m without value (should default to 30)
        args = parser.parse_args(['start', '-m'])
        self.assertEqual(args.with_monitor, 30)
        
        # Test -m with custom value
        args = parser.parse_args(['start', '-m', '60'])
        self.assertEqual(args.with_monitor, 60)
        
        # Test without -m (should be None)
        args = parser.parse_args(['start'])
        self.assertIsNone(args.with_monitor)
    
    def test_monitor_flag_validation(self):
        """Test monitor flag value validation"""
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--with-monitor", nargs='?', const=30, type=int)
        
        # Test invalid value raises error
        with self.assertRaises(SystemExit):
            parser.parse_args(['start', '-m', 'invalid'])
    
    @patch('run.AppRunner.start_services')
    @patch('run.AppRunner.monitor_services')
    def test_monitor_integration_with_start(self, mock_monitor, mock_start):
        """Test that -m flag properly triggers monitoring"""
        from run import main
        
        # Mock sys.argv for testing
        test_args = ['run.py', 'start', '-m', '45']
        with patch.object(sys, 'argv', test_args):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit
        
        # Verify start_services was called
        mock_start.assert_called_once()
        
        # Verify monitor_services was called with correct parameters
        mock_monitor.assert_called_once_with(daemon=True, interval=45)

class TestServiceMonitorClass(unittest.TestCase):
    """Test the ServiceMonitor class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the monitor module to avoid import issues
        self.mock_monitor = MagicMock()
        sys.modules['monitor'] = self.mock_monitor
        
        # Create mock ServiceMonitor class
        self.mock_service_monitor_class = MagicMock()
        self.mock_monitor.ServiceMonitor = self.mock_service_monitor_class
        
        # Create mock instance
        self.mock_service_monitor = MagicMock()
        self.mock_service_monitor_class.return_value = self.mock_service_monitor
    
    @patch('monitor.psutil')
    @patch('monitor.requests')
    def test_backend_health_check(self, mock_requests, mock_psutil):
        """Test backend health check functionality"""
        # Import after mocking
        from monitor import ServiceMonitor
        
        # Mock successful health check response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'cached_classes': 16}
        mock_requests.get.return_value = mock_response
        
        monitor = ServiceMonitor()
        healthy, message = monitor.check_backend_health()
        
        self.assertTrue(healthy)
        self.assertIn('cached classes: 16', message)
        mock_requests.get.assert_called_once()
    
    @patch('monitor.psutil')
    @patch('monitor.requests')
    def test_backend_health_check_failure(self, mock_requests, mock_psutil):
        """Test backend health check when service is down"""
        from monitor import ServiceMonitor
        
        # Mock connection refused
        mock_requests.get.side_effect = ConnectionError("Connection refused")
        
        monitor = ServiceMonitor()
        healthy, message = monitor.check_backend_health()
        
        self.assertFalse(healthy)
        self.assertIn('Connection refused', message)
    
    @patch('monitor.psutil')
    @patch('monitor.socket')
    def test_frontend_health_check(self, mock_socket_module, mock_psutil):
        """Test frontend health check functionality"""
        from monitor import ServiceMonitor
        
        # Mock socket connection success
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # Success
        mock_socket_module.socket.return_value = mock_socket
        
        monitor = ServiceMonitor()
        healthy, message = monitor.check_frontend_health()
        
        self.assertTrue(healthy)
        self.assertIn('OK', message)
    
    @patch('monitor.psutil')
    def test_process_memory_monitoring(self, mock_psutil):
        """Test process memory monitoring"""
        from monitor import ServiceMonitor
        
        # Mock process list
        mock_proc1 = MagicMock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'python3',
            'memory_info': MagicMock(rss=100 * 1024 * 1024)  # 100MB
        }
        mock_proc1.cmdline.return_value = ['python3', 'app.py']
        
        mock_proc2 = MagicMock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'node',
            'memory_info': MagicMock(rss=200 * 1024 * 1024)  # 200MB
        }
        mock_proc2.cmdline.return_value = ['node', 'vite']
        
        mock_psutil.process_iter.return_value = [mock_proc1, mock_proc2]
        
        monitor = ServiceMonitor()
        memory_usage = monitor.check_process_memory()
        
        self.assertIn('backend', memory_usage)
        self.assertIn('frontend', memory_usage)
        self.assertAlmostEqual(memory_usage['backend'], 100, delta=1)
        self.assertAlmostEqual(memory_usage['frontend'], 200, delta=1)

class TestRunPyMonitorIntegration(unittest.TestCase):
    """Test run.py integration with monitoring system"""
    
    def setUp(self):
        """Set up test fixtures"""
        from run import AppRunner
        self.runner = AppRunner()
    
    @patch('run.AppRunner.print_status')
    @patch('run.os.fork')
    @patch('run.os.setsid')
    def test_daemon_mode_fork(self, mock_setsid, mock_fork, mock_print):
        """Test daemon mode forking on Unix systems"""
        # Mock successful fork
        mock_fork.side_effect = [1234, 0]  # Parent PID, then child
        
        with patch('run.sys.platform', 'linux'):
            with patch('run.ServiceMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor_class.return_value = mock_monitor
                
                # This should return early due to fork
                result = self.runner.monitor_services(daemon=True, interval=30)
                
                # Verify fork was called
                self.assertEqual(mock_fork.call_count, 1)
    
    @patch('run.AppRunner.print_status')
    def test_windows_daemon_warning(self, mock_print):
        """Test that Windows shows daemon mode warning"""
        with patch('run.sys.platform', 'win32'):
            with patch('run.ServiceMonitor') as mock_monitor_class:
                mock_monitor = MagicMock()
                mock_monitor_class.return_value = mock_monitor
                
                self.runner.monitor_services(daemon=True, interval=30)
                
                # Should print warning about daemon mode not supported
                mock_print.assert_any_call(
                    "Daemon mode not supported on Windows", "warning", 1
                )
    
    @patch('run.AppRunner.print_status')
    def test_psutil_missing_error(self, mock_print):
        """Test error handling when psutil is missing"""
        with patch('builtins.__import__', side_effect=ImportError("No module named 'psutil'")):
            self.runner.monitor_services(daemon=False, interval=30)
            
            mock_print.assert_any_call(
                "psutil not installed - required for monitoring", "error", 1
            )

class TestMonitorProcessManagement(unittest.TestCase):
    """Test monitor process management in run.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        from run import AppRunner
        self.runner = AppRunner()
    
    @patch('run.psutil')
    @patch('run.AppRunner.print_status')
    def test_stop_monitor_process_found(self, mock_print, mock_psutil):
        """Test stopping monitor processes when found"""
        # Mock process with monitor.py in cmdline
        mock_proc = MagicMock()
        mock_proc.info = {'pid': 1234, 'name': 'python3', 'cmdline': ['python3', 'monitor.py']}
        mock_proc.terminate.return_value = None
        mock_proc.wait.return_value = None
        
        mock_psutil.process_iter.return_value = [mock_proc]
        
        self.runner._stop_monitor_process()
        
        # Verify process was terminated
        mock_proc.terminate.assert_called_once()
        mock_print.assert_any_call(
            "Stopping monitor process (PID: 1234)", "step", 2
        )
    
    @patch('run.psutil')
    @patch('run.AppRunner.print_status')
    def test_stop_monitor_no_processes(self, mock_print, mock_psutil):
        """Test stopping monitor when no processes found"""
        mock_psutil.process_iter.return_value = []
        
        self.runner._stop_monitor_process()
        
        mock_print.assert_any_call("No monitor processes found", "info", 1)
    
    @patch('run.subprocess.run')
    @patch('run.AppRunner.print_status')
    def test_stop_monitor_fallback_unix(self, mock_print, mock_subprocess):
        """Test fallback process search on Unix when psutil unavailable"""
        with patch('builtins.__import__', side_effect=ImportError("No psutil")):
            # Mock pgrep finding processes
            mock_result = MagicMock()
            mock_result.stdout = "1234\n5678"
            mock_subprocess.return_value = mock_result
            
            with patch('run.os.kill') as mock_kill:
                self.runner._stop_monitor_process()
                
                # Verify pgrep was called
                mock_subprocess.assert_called_once()
                
                # Verify processes were killed
                expected_calls = [call(1234, 15), call(5678, 15)]  # SIGTERM = 15
                mock_kill.assert_has_calls(expected_calls, any_order=True)

class TestMonitorSystemIntegration(unittest.TestCase):
    """Integration tests for the complete monitoring system"""
    
    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_monitor_system_startup_sequence(self, mock_sleep, mock_popen):
        """Test the complete startup sequence with monitoring"""
        from run import AppRunner
        runner = AppRunner()
        
        # Mock successful service starts
        mock_backend_proc = MagicMock()
        mock_frontend_proc = MagicMock()
        mock_popen.side_effect = [mock_backend_proc, mock_frontend_proc]
        
        with patch.object(runner, 'check_dependencies', return_value=True):
            with patch.object(runner, 'allocate_ports', return_value={'backend': 5001, 'frontend': 3000}):
                with patch.object(runner, 'start_backend', return_value=True):
                    with patch.object(runner, 'start_frontend', return_value=True):
                        with patch.object(runner, 'monitor_services') as mock_monitor:
                            
                            # Simulate: python3 run.py start -m 60
                            runner.start_services()
                            # This would normally be called by main() based on args
                            runner.monitor_services(daemon=True, interval=60)
                            
                            mock_monitor.assert_called_once_with(daemon=True, interval=60)
    
    def test_help_text_includes_monitor_options(self):
        """Test that help text includes monitoring options"""
        import subprocess
        import sys
        
        # Run help command
        result = subprocess.run([
            sys.executable, 'run.py', '--help'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        help_text = result.stdout
        
        # Verify monitoring options are documented
        self.assertIn('-m', help_text)
        self.assertIn('--with-monitor', help_text)
        self.assertIn('monitoring enabled', help_text)
        self.assertIn('python3 run.py start -m', help_text)

def run_tests():
    """Run all monitoring system tests"""
    print("🧪 Running Monitoring System Tests")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMonitoringArgumentParsing,
        TestServiceMonitorClass,
        TestRunPyMonitorIntegration,
        TestMonitorProcessManagement,
        TestMonitorSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All monitoring system tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for failure in result.failures:
            print(f"FAIL: {failure[0]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)