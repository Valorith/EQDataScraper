# OAuth User Account System - Comprehensive Testing Strategy

## Overview

This document outlines a complete testing strategy for the newly implemented OAuth user account system. The tests are organized by layer and priority to ensure comprehensive coverage while maintaining development velocity.

## 1. Backend Testing (Python/pytest)

### 1.1 Database Models (`backend/models/user.py`)

#### User Model Tests
```python
# test_user_model.py
class TestUserModel:
    def test_create_user_success(self, mock_db):
        """Test successful user creation with valid Google OAuth data"""
        
    def test_create_user_duplicate_google_id(self, mock_db):
        """Test handling of duplicate Google ID (should fail gracefully)"""
        
    def test_get_user_by_google_id(self, mock_db):
        """Test user retrieval by Google ID"""
        
    def test_update_user_profile_partial(self, mock_db):
        """Test updating user profile with partial data"""
        
    def test_user_preferences_crud(self, mock_db):
        """Test complete user preferences lifecycle"""
```

#### OAuth Session Model Tests
```python
class TestOAuthSessionModel:
    def test_create_session_with_tokens(self, mock_db):
        """Test session creation with access/refresh tokens"""
        
    def test_session_expiry_cleanup(self, mock_db):
        """Test automatic cleanup of expired sessions"""
        
    def test_get_user_sessions(self, mock_db):
        """Test retrieving all sessions for a user"""
```

### 1.2 OAuth Flow (`backend/routes/auth.py`)

#### Authentication Endpoint Tests
```python
# test_auth_routes.py
class TestAuthRoutes:
    def test_google_login_url_generation(self, client):
        """Test OAuth URL generation with PKCE parameters"""
        
    def test_oauth_callback_success(self, client, mock_google_api):
        """Test successful OAuth callback with valid code"""
        
    def test_oauth_callback_invalid_state(self, client):
        """Test CSRF protection via state parameter validation"""
        
    def test_token_refresh_success(self, client, mock_jwt):
        """Test access token refresh with valid refresh token"""
        
    def test_logout_cleanup(self, client, authenticated_user):
        """Test session cleanup on logout"""
```

### 1.3 JWT Security (`backend/utils/jwt_utils.py`)

#### Token Management Tests
```python
# test_jwt_utils.py
class TestJWTSecurity:
    def test_create_access_token(self, mock_user):
        """Test JWT access token creation"""
        
    def test_verify_valid_token(self, valid_token):
        """Test JWT token verification"""
        
    def test_reject_expired_token(self, expired_token):
        """Test rejection of expired tokens"""
        
    def test_require_auth_decorator(self, client):
        """Test authentication decorator functionality"""
        
    def test_require_admin_decorator(self, client, regular_user):
        """Test admin-only access enforcement"""
```

### 1.4 Rate Limiting

#### Security Tests
```python
# test_rate_limiting.py
class TestRateLimiting:
    def test_oauth_endpoint_rate_limit(self, client):
        """Test 10 requests per minute limit on auth endpoints"""
        
    def test_user_endpoint_rate_limit(self, client, authenticated_user):
        """Test 60 requests per hour limit on user endpoints"""
        
    def test_admin_endpoint_rate_limit(self, client, admin_user):
        """Test 30 requests per hour limit on admin endpoints"""
```

### 1.5 Input Validation & Security

#### Security Tests
```python
# test_security.py
class TestInputSecurity:
    def test_sql_injection_prevention(self, client):
        """Test SQL injection protection in user queries"""
        
    def test_xss_prevention_profile_update(self, client, authenticated_user):
        """Test XSS payload rejection in profile fields"""
        
    def test_csrf_protection_oauth_flow(self, client):
        """Test CSRF protection in OAuth state parameter"""
```

## 2. Frontend Testing (Vitest/Vue Test Utils)

### 2.1 User Store (`src/stores/userStore.js`)

#### Pinia Store Tests
```javascript
// userStore.test.js
describe('User Store', () => {
  test('initializes auth state from localStorage', () => {
    // Test state restoration on app load
  })
  
  test('handles OAuth login flow initiation', () => {
    // Test loginWithGoogle action
  })
  
  test('processes OAuth callback successfully', () => {
    // Test handleOAuthCallback with valid state
  })
  
  test('handles OAuth callback with invalid state', () => {
    // Test CSRF protection on frontend
  })
  
  test('refreshes access token automatically', () => {
    // Test automatic token refresh logic
  })
  
  test('clears auth state on logout', () => {
    // Test complete state cleanup
  })
  
  test('persists user preferences', () => {
    // Test preference synchronization
  })
})
```

### 2.2 OAuth Components

#### GoogleAuthButton Tests
```javascript
// GoogleAuthButton.test.js
describe('GoogleAuthButton', () => {
  test('renders sign in button when not authenticated', () => {
    // Test initial render state
  })
  
  test('shows loading state during OAuth initiation', () => {
    // Test loading spinner and disabled state
  })
  
  test('displays error message on OAuth failure', () => {
    // Test error state rendering
  })
  
  test('initiates OAuth flow on click', () => {
    // Test click handler and store interaction
  })
  
  test('meets accessibility requirements', () => {
    // Test ARIA labels and keyboard navigation
  })
})
```

#### UserMenu Tests
```javascript
// UserMenu.test.js
describe('UserMenu', () => {
  test('displays user avatar and name', () => {
    // Test user data display
  })
  
  test('shows admin badge for admin users', () => {
    // Test role-based UI elements
  })
  
  test('opens dropdown menu on avatar click', () => {
    // Test menu interaction
  })
  
  test('handles logout action', () => {
    // Test logout button functionality
  })
  
  test('generates proper avatar initials fallback', () => {
    // Test fallback for missing avatars
  })
})
```

#### AuthCallback Tests
```javascript
// AuthCallback.test.js
describe('AuthCallback', () => {
  test('processes successful OAuth callback', () => {
    // Test success state with valid parameters
  })
  
  test('handles OAuth error responses', () => {
    // Test error state with invalid parameters
  })
  
  test('redirects to home after successful login', () => {
    // Test post-login navigation
  })
  
  test('shows retry option on failure', () => {
    // Test error recovery UI
  })
})
```

### 2.3 Route Guards & Navigation

#### Router Tests
```javascript
// router.test.js
describe('Router Guards', () => {
  test('allows authenticated users to access protected routes', () => {
    // Test successful route access
  })
  
  test('redirects unauthenticated users to login', () => {
    // Test route protection
  })
  
  test('blocks non-admin users from admin routes', () => {
    // Test admin route protection
  })
  
  test('preserves intended route after login', () => {
    // Test redirect after authentication
  })
})
```

### 2.4 State Persistence

#### localStorage Tests
```javascript
// persistence.test.js
describe('State Persistence', () => {
  test('saves authentication state to localStorage', () => {
    // Test state saving
  })
  
  test('restores authentication state on app reload', () => {
    // Test state restoration
  })
  
  test('handles corrupted localStorage data', () => {
    // Test error recovery
  })
  
  test('clears localStorage on logout', () => {
    // Test cleanup
  })
})
```

## 3. Integration Testing

### 3.1 End-to-End OAuth Flow

#### Playwright/Cypress Tests
```javascript
// e2e/oauth-flow.spec.js
describe('OAuth Integration', () => {
  test('complete login flow from start to finish', () => {
    // Test full OAuth cycle
  })
  
  test('maintains session across page reloads', () => {
    // Test session persistence
  })
  
  test('handles multiple browser tabs', () => {
    // Test concurrent sessions
  })
  
  test('recovers from network interruptions', () => {
    // Test error recovery
  })
})
```

### 3.2 API Integration

#### Backend Integration Tests
```python
# test_api_integration.py
class TestAPIIntegration:
    def test_complete_user_registration_flow(self, client):
        """Test full user creation and preference setup"""
        
    def test_concurrent_user_operations(self, client):
        """Test database consistency under load"""
        
    def test_session_management_across_requests(self, client):
        """Test session lifecycle management"""
```

## 4. Security Testing

### 4.1 Penetration Testing

#### Security Validation
```python
# test_security_penetration.py
class TestSecurityPenetration:
    def test_brute_force_login_protection(self, client):
        """Test rate limiting against brute force attacks"""
        
    def test_jwt_token_manipulation(self, client):
        """Test JWT tampering detection"""
        
    def test_cors_configuration(self, client):
        """Test CORS policy enforcement"""
        
    def test_input_sanitization(self, client):
        """Test malicious input handling"""
```

## 5. Testing Infrastructure

### 5.1 Test Database Setup

```python
# conftest.py
@pytest.fixture
def test_db():
    """Create isolated test database"""
    # Setup test PostgreSQL instance
    # Run migrations
    # Yield connection
    # Cleanup after tests

@pytest.fixture
def mock_google_oauth():
    """Mock Google OAuth API responses"""
    # Mock successful OAuth flow
    # Mock error responses
    # Mock token validation
```

### 5.2 Frontend Test Utilities

```javascript
// test-utils.js
export function createTestUserStore(initialState = {}) {
  // Create Pinia store for testing
}

export function mockAuthenticatedUser() {
  // Mock authenticated user state
}

export function mockOAuthCallback(success = true) {
  // Mock OAuth callback scenarios
}
```

## 6. Continuous Integration

### 6.1 GitHub Actions Workflow

```yaml
# .github/workflows/oauth-tests.yml
name: OAuth System Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run backend tests
        run: pytest backend/tests/ -v
        
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run frontend tests
        run: npm run test:run
        
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup test environment
        run: |
          # Start backend and frontend
          # Setup test database
      - name: Run E2E tests
        run: npm run test:e2e
```

## 7. Implementation Priority

### Phase 1: Core Functionality (Week 1)
- [ ] User model database tests
- [ ] Basic OAuth flow tests
- [ ] JWT token management tests
- [ ] User store action tests

### Phase 2: Integration & Components (Week 2)
- [ ] OAuth component tests
- [ ] Route guard tests
- [ ] API integration tests
- [ ] Error handling tests

### Phase 3: Security & Performance (Week 3)
- [ ] Rate limiting tests
- [ ] Security penetration tests
- [ ] End-to-end flow tests
- [ ] Performance/load tests

### Phase 4: Advanced & Edge Cases (Week 4)
- [ ] Cross-browser compatibility
- [ ] Accessibility compliance
- [ ] Mobile responsiveness
- [ ] Stress testing

## Test Coverage Goals

- **Backend**: 90%+ coverage on new OAuth code
- **Frontend**: 85%+ coverage on new components and stores
- **Integration**: 100% coverage of critical user flows
- **Security**: 100% coverage of security-critical functions

## Monitoring & Metrics

- Test execution time tracking
- Coverage reporting with trends
- Security test results dashboard
- Performance regression detection
- Accessibility compliance scoring

This comprehensive testing strategy ensures the OAuth user account system is robust, secure, and maintainable while protecting against regressions in the existing spell functionality.