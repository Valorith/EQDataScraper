# Testing Guide for EQDataScraper

This document provides comprehensive information about the testing suite for EQDataScraper.

## ⚠️ Important CI/CD Notes

**Frontend Tests**: Due to rollup native dependency issues, frontend tests are **skipped in CI** but work locally. This is a known limitation that doesn't affect deployment or functionality.

**GitHub Actions**: We use a single streamlined CI/CD pipeline (`ci.yml`) that focuses on what works reliably in CI environments.

## Overview

The testing suite includes:
- **Backend Tests**: Python/pytest for API endpoints, caching, and data processing
- **Frontend Tests**: JavaScript/Vitest for Vue components and stores
- **Integration Tests**: End-to-end testing of API and UI interactions
- **CI/CD**: Automated testing on GitHub Actions

## Quick Start

### Run All Tests Locally
```bash
# Recommended: Run local test suite
npm run test:local

# This runs both backend and frontend tests
# Frontend tests may show warnings (expected)
```

### Backend Tests Only
```bash
# Using npm script
npm run test:backend

# Using pytest directly
cd backend && python -m pytest

# With coverage
npm run test:backend:coverage

# Run specific test
cd backend && python -m pytest tests/test_api_endpoints.py -v
```

### Frontend Tests Only
```bash
# Run tests
npm run test

# Run tests once (CI mode)
npm run test:run

# With coverage
npm run test:coverage

# Interactive UI
npm run test:ui
```

## Test Structure

### Backend Tests (`backend/tests/`)

#### `test_pricing_system.py`
Tests the critical pricing system that was recently refactored:
- Pricing cache functionality
- Cache refresh operations
- Data consistency across storage systems
- Error handling and edge cases

#### `test_cache_management.py`
Tests cache storage and expiry logic:
- File vs database cache storage
- Cache expiry detection
- Rate limiting
- Cache validation and integrity

#### `test_api_endpoints.py`
Tests all API endpoints:
- Spell data endpoints
- Search functionality
- Cache status endpoints
- Error handling and validation

### Frontend Tests (`tests/`)

#### `tests/stores/spells.test.js`
Tests the Pinia store:
- State management
- API integration
- Computed properties
- Data validation

#### `tests/components/ClassSpells.test.js`
Tests the main spell display component:
- Data status section
- Cache expiry logic
- Refresh functionality
- Accessibility features

#### `tests/components/Home.test.js`
Tests the home page component:
- Class grid display
- Global search functionality
- Search pagination and navigation
- Performance optimizations

## Test Configuration

### Backend Configuration (`backend/pytest.ini`)
- Uses file-based cache for isolation
- Reduced cache expiry times for faster testing
- Coverage reporting with HTML output
- Test environment variables

### Frontend Configuration (`vitest.config.js`)
- Happy DOM environment for faster testing
- Vue Test Utils integration
- Coverage reporting with v8 provider
- Mock environment variables

## Testing Best Practices

### Writing Backend Tests
```python
def test_pricing_system_functionality(mock_app, sample_data):
    """Test pricing system with descriptive name and fixtures."""
    # Arrange
    setup_test_data(sample_data)
    
    # Act
    result = perform_operation()
    
    # Assert
    assert result == expected_value
    assert side_effects_occurred()
```

### Writing Frontend Tests
```javascript
describe('Component Feature', () => {
  it('should handle user interaction correctly', async () => {
    // Arrange
    const wrapper = mount(Component, { props: testProps })
    
    // Act
    await wrapper.find('.button').trigger('click')
    
    // Assert
    expect(wrapper.emitted('event')).toBeTruthy()
  })
})
```

## Critical Test Areas

Based on recent bugs found during pricing system deprecation, these areas receive special attention:

### 1. Cache Consistency
- Data storage across multiple cache systems
- Timestamp tracking and expiry logic
- Cache refresh and cleanup operations

### 2. API Data Flow
- Request/response data integrity
- Error handling and fallbacks
- Data transformation and validation

### 3. State Management
- Store mutations and getters
- Computed property reactivity
- Component state synchronization

### 4. User Interactions
- Search functionality and pagination
- Cache refresh operations
- Navigation and routing

## Running Tests in Different Environments

### Local Development
```bash
# Quick test run
npm run test:all

# Development with watch mode
npm run test  # Frontend watch mode
cd backend && python -m pytest -f  # Backend watch mode
```

### CI/CD Environment
```bash
# Automated testing (GitHub Actions)
# - Installs all dependencies
# - Runs backend tests with coverage
# - Runs frontend tests with coverage
# - Runs integration tests
# - Uploads coverage reports
```

### Production-like Testing
```bash
# Test with production build
npm run build
npm run test:all

# Test with database cache (if available)
export DATABASE_URL="your-db-url"
npm run test:backend
```

## Coverage Reports

### Backend Coverage
- Generated in `backend/htmlcov/`
- Includes line, branch, and function coverage
- Excludes test files and configuration

### Frontend Coverage
- Generated in `coverage/`
- Includes component, store, and utility coverage
- Interactive HTML reports with source maps

## Troubleshooting

### Common Issues

#### Backend Tests Failing
```bash
# Check Python environment
python --version  # Should be 3.9+

# Install missing dependencies
cd backend && pip install -r requirements-test.txt

# Clear cache and retry
rm -rf backend/htmlcov backend/.pytest_cache
```

#### Frontend Tests Failing
```bash
# Check Node version
node --version  # Should be 18+

# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vitest cache
npx vitest --clearCache
```

#### Test Environment Issues
```bash
# Ensure test environment variables are set
export TESTING=1
export DATABASE_URL=""
export PORT=5999

# Check for port conflicts
lsof -i :5999
```

## Performance Considerations

### Test Speed Optimization
- Uses Happy DOM instead of JSDOM for frontend tests
- File-based cache for backend tests (faster than database)
- Parallel test execution where possible
- Selective test running with patterns

### Memory Management
- Clears cache between tests
- Mocks external dependencies
- Uses temporary directories for file tests

## Continuous Integration

### GitHub Actions Workflow
- **Backend Tests**: Python 3.9, pytest with coverage
- **Frontend Tests**: Node 18, Vitest with coverage
- **Integration Tests**: Full stack smoke tests
- **Deployment Check**: Build verification

### Coverage Reporting
- Uploaded to Codecov
- Separate reports for backend/frontend
- Coverage badges in README
- Pull request coverage comments

## Future Enhancements

### Planned Improvements
- Visual regression testing for UI components
- Performance benchmarking tests
- End-to-end tests with Playwright
- Database integration tests with test containers
- Load testing for API endpoints

### Test Data Management
- Shared test fixtures and factories
- Test data generation utilities
- Snapshot testing for complex data structures