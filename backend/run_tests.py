#!/usr/bin/env python3
"""
Test runner script for backend tests.
Handles environment setup and provides test execution utilities.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def set_test_environment():
    """Set up test environment variables."""
    os.environ['TESTING'] = '1'
    os.environ['DATABASE_URL'] = ''  # Force file-based cache for tests
    os.environ['PORT'] = '5999'
    os.environ['CACHE_EXPIRY_HOURS'] = '1'
    os.environ['PRICING_CACHE_EXPIRY_HOURS'] = '1'

def run_tests(args):
    """Run pytest with appropriate configuration."""
    pytest_args = ['python', '-m', 'pytest']
    
    if args.verbose:
        pytest_args.append('-v')
    
    if args.coverage:
        pytest_args.extend(['--cov', '--cov-report=term-missing'])
        if args.html_coverage:
            pytest_args.append('--cov-report=html')
    
    if args.fast:
        pytest_args.extend(['-x', '--tb=short'])
    
    if args.pattern:
        pytest_args.extend(['-k', args.pattern])
    
    if args.file:
        pytest_args.append(args.file)
    
    # Run pytest
    return subprocess.run(pytest_args, cwd=Path(__file__).parent)

def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-r', 'requirements-test.txt'
    ], cwd=Path(__file__).parent)

def main():
    parser = argparse.ArgumentParser(description='Run backend tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose test output')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--html-coverage', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--fast', '-f', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--pattern', '-k', type=str,
                       help='Run tests matching pattern')
    parser.add_argument('--file', type=str,
                       help='Run specific test file')
    parser.add_argument('--install', action='store_true',
                       help='Install test dependencies first')
    
    args = parser.parse_args()
    
    if args.install:
        install_test_dependencies()
    
    set_test_environment()
    result = run_tests(args)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())