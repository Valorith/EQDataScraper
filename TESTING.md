# EQDataScraper Testing Guide

This document provides comprehensive testing strategies to validate the cross-platform improvements and overall functionality of EQDataScraper.

## 🧪 Testing Overview

The testing suite includes three levels of validation:

1. **Unit Tests** - Test individual components and platform-specific logic
2. **Integration Tests** - Test run.py functionality and component interaction  
3. **Platform Validation** - Test real-world platform compatibility
4. **Functional Tests** - Test core application functionality

## 🚀 Quick Testing

### Run All Tests
```bash
# Platform validation (recommended first)
python3 validate_platform.py

# Functional tests
python3 test_functional.py

# Unit tests (may have mock-related issues)
python3 test_platform_compatibility.py

# Integration tests
python3 test_run_py_integration.py
```

### Platform-Specific Testing
```bash
# Windows
run.bat status
python test_functional.py

# macOS/Linux
./run.sh status
python3 test_functional.py
```

## 📋 Test Categories

### 1. Platform Validation Tests (`validate_platform.py`)

**Purpose**: Validate real-world platform compatibility

**Tests Include**:
- ✅ Platform detection (Windows/macOS/Linux/WSL)
- ✅ Command availability (lsof, tasklist, netstat, etc.)
- ✅ Python command detection (python3, python, py)
- ✅ npm command detection (npm, npm.cmd)
- ✅ Port operations and conflict detection
- ✅ Process management capabilities
- ✅ File system operations
- ✅ Network connectivity to spell data source

**Expected Results**:
- **macOS**: All tests should pass
- **Linux**: All tests should pass
- **Windows**: All tests should pass (netstat, tasklist used)
- **WSL**: All tests should pass with hybrid commands

### 2. Functional Tests (`test_functional.py`)

**Purpose**: Test core application functionality without complex mocking

**Tests Include**:
- ✅ run.py --help command
- ✅ run.py status command
- ✅ Config file creation and defaults
- ✅ Platform script existence (run.bat/run.sh)
- ✅ Backend script availability
- ✅ Frontend file structure
- ✅ package.json dependencies
- ✅ Python module import

**Expected Results**: All tests should pass on any platform

### 3. Unit Tests (`test_platform_compatibility.py`)

**Purpose**: Test platform-specific logic with mocking

**Tests Include**:
- Platform detection logic
- Port conflict resolution
- Process management across platforms
- npm command detection variations
- Configuration management
- Network connectivity handling
- First-time setup detection

**Known Issues**: Some tests may fail due to mocking conflicts with real dependencies

### 4. Integration Tests (`test_run_py_integration.py`)

**Purpose**: Test run.py AppRunner class integration

**Tests Include**:
- Configuration loading/saving
- Port management
- Process detection methods
- npm command finding
- PID file management
- Network connectivity checks

## 🔧 Platform-Specific Testing

### Windows Testing Checklist

```cmd
# Test platform scripts
run.bat --help
run.bat status

# Test Python detection
python --version
python3 --version
py -3 --version

# Test Windows-specific commands
tasklist /?
taskkill /?
netstat /?

# Test npm detection
npm --version
npm.cmd --version

# Run validation
python validate_platform.py
```

**Expected Windows Behavior**:
- Uses `taskkill` for process termination
- Uses `netstat` + `tasklist` for port conflict detection  
- Handles `.cmd` extensions for npm commands
- Uses `CREATE_NEW_PROCESS_GROUP` flag for subprocess creation

### macOS Testing Checklist

```bash
# Test platform scripts
./run.sh --help
./run.sh status

# Test macOS-specific commands
lsof -h
ps --help

# Test Python detection
python3 --version

# Test npm detection
npm --version

# Run validation
python3 validate_platform.py
```

**Expected macOS Behavior**:
- Uses `lsof` + `ps` for port conflict detection
- Uses POSIX signals for process management
- Detects AirPlay Receiver conflicts on port 5000

### Linux Testing Checklist

```bash
# Test platform scripts
./run.sh --help
./run.sh status

# Test Linux-specific commands
ss --help
netstat --help
ps --help

# Test Python detection
python3 --version

# Run validation
python3 validate_platform.py
```

**Expected Linux Behavior**:
- Uses `ss` (preferred) or `netstat` (fallback) for port detection
- Uses POSIX signals for process management
- Handles various Linux distributions

### WSL Testing Checklist

```bash
# Verify WSL detection
ls /mnt/c  # Should exist in WSL

# Test hybrid behavior
./run.sh status
python3 validate_platform.py

# Test Windows file access
ls /mnt/c/Windows  # Should work in WSL
```

**Expected WSL Behavior**:
- Automatically detects WSL environment
- Uses Linux commands but handles Windows quirks
- Properly manages cross-platform file paths

## 🐛 Common Issues and Solutions

### Port Conflicts
**Issue**: Port 5000 already in use (AirPlay on macOS)
**Solution**: App automatically detects and switches to port 5001+
**Test**: Run `python3 run.py start` - should handle automatically

### npm Command Not Found
**Issue**: npm command detection fails
**Solutions**:
- Install Node.js from nodejs.org
- Restart terminal after installation
- On Windows, ensure npm.cmd is in PATH

### Process Management Issues
**Issue**: Cannot stop services
**Solutions**:
- Check PID file: `.app_pids.json`
- Use platform-appropriate stop commands
- Run `python3 run.py stop` to clean up

### Permission Issues
**Issue**: run.sh not executable
**Solution**: `chmod +x run.sh`

## 📊 Test Results Interpretation

### Success Indicators
- ✅ All platform validation tests pass
- ✅ Functional tests show 8/8 passing
- ✅ Services start and stop correctly
- ✅ Port conflicts are resolved automatically
- ✅ Configuration persists correctly

### Warning Indicators
- ⚠️ Some unit tests fail (acceptable if due to mocking issues)
- ⚠️ Network connectivity partial (3/3 or 2/3 acceptable)
- ⚠️ Non-critical commands missing (app will still work)

### Failure Indicators
- ❌ Platform validation shows 0% success
- ❌ Python/Node.js not found
- ❌ Core files missing (package.json, backend/app.py)
- ❌ Cannot create configuration files

## 🔄 Continuous Testing

### Before Each Release
1. Run platform validation on target platforms
2. Test with fresh dependency installation
3. Verify port conflict resolution
4. Test first-time user experience

### Platform Coverage
- **Primary**: macOS (development platform)
- **Secondary**: Linux (Ubuntu/Debian/RHEL)  
- **Tertiary**: Windows 10/11
- **Special**: WSL environments

### Automated Testing Integration
```bash
# Add to CI/CD pipeline
python3 validate_platform.py || exit 1
python3 test_functional.py || exit 1

# Optional (may have mocking issues)
python3 test_platform_compatibility.py
python3 test_run_py_integration.py
```

## 📝 Manual Testing Scenarios

### First-Time User Experience
1. Clone repository
2. Run `python3 run.py start` (should show setup message)
3. Run `python3 run.py install`
4. Run `python3 run.py start` (should work)
5. Verify app accessible at http://localhost:3000

### Port Conflict Scenario
1. Start app: `python3 run.py start`
2. Note backend port (e.g., 5001)
3. Start second instance in different terminal
4. Verify second instance uses different port (e.g., 5002)
5. Check config.json shows updated port

### Cross-Platform File Sharing
1. Set up app on one platform
2. Copy to another platform (via network share, USB, etc.)
3. Run platform validation
4. Verify app works without reconfiguration

## 🎯 Testing Success Criteria

**Minimum Requirements**:
- Platform validation: 80%+ pass rate
- Functional tests: 100% pass rate
- Core commands work: status, start, stop
- Configuration persists correctly

**Optimal Requirements**:
- Platform validation: 100% pass rate
- All test suites: 90%+ pass rate
- Automatic port conflict resolution
- Seamless cross-platform experience

The testing suite ensures EQDataScraper works reliably across Windows, macOS, and Linux with minimal user intervention and maximum compatibility.