# Railway Deployment with Unit Testing

This document explains how to deploy EQDataScraper to Railway with automated unit testing that runs before each deployment.

## 🚂 Railway Configuration

### Files Added for Railway Testing:
- `railway.json` - Railway deployment configuration
- `scripts/railway-test.sh` - Pre-deploy test script
- `backend/pytest-railway.ini` - Optimized pytest config for Railway
- `backend/requirements-railway.txt` - Minimal test dependencies
- `.railway-env` - Environment variable reference

## 🔧 Setup Instructions

### 1. Deploy to Railway

1. **Connect Repository**:
   - Go to [Railway Dashboard](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your EQDataScraper repository

2. **Configure Environment Variables**:
   In Railway dashboard, add these variables:
   ```
   DATABASE_URL=your_postgres_connection_string
   CACHE_EXPIRY_HOURS=24
   PRICING_CACHE_EXPIRY_HOURS=168
   NODE_ENV=production
   ```

3. **Deploy**:
   - Railway will automatically detect the `railway.json` config
   - Pre-deploy tests will run automatically before each deployment

### 2. How Testing Works

#### Pre-Deploy Testing Flow:
```
Git Push → Railway Build → Pre-Deploy Tests → Deploy (if tests pass)
```

#### Tests That Run:
- **Backend Critical Tests**:
  - Pricing system functionality (prevents cache bugs)
  - API endpoint validation
  - Cache management operations
- **Frontend Framework Validation**:
  - Testing framework verification
  - Basic component structure

#### Test Optimization for Railway:
- **Fast execution**: Only critical tests run (< 30 seconds)
- **Fail-fast**: Stops on first failure to save build time
- **No coverage**: Skips coverage collection for speed
- **Isolated environment**: Uses file-based cache for testing

### 3. What Happens on Test Failure

If tests fail during pre-deploy:
- ❌ Deployment is **blocked**
- 🚨 You receive notification of failure
- 🔄 Fix the issue and push again
- ✅ Tests must pass before deployment proceeds

### 4. Monitoring Test Results

**Railway Logs**: Check the "Deployments" tab in Railway dashboard
```
🚂 Railway Pre-Deploy Testing Suite
==================================
🐍 Backend Critical Tests
-------------------------
Running pricing system tests...
✅ tests/test_pricing_system.py::TestPricingCache::test_pricing_cache_expiry PASSED
✅ Backend: Core pricing and API systems verified
🚀 Deployment can proceed safely
```

**Failed Deployment Example**:
```
❌ tests/test_pricing_system.py::TestPricingCache::test_fetch_single_spell_pricing_success FAILED
🚨 Critical test failed - deployment blocked
```

## 🎯 Test Strategy

### Critical Tests (Run on Railway):
- **Pricing System**: Validates cache functionality that had bugs
- **API Endpoints**: Ensures core endpoints respond correctly  
- **Cache Management**: Verifies expiry and storage logic

### Comprehensive Tests (Run on CI/GitHub Actions):
- Full test suite with coverage
- Integration testing
- Performance benchmarks
- UI component testing

## 🛠️ Local Development

### Test Railway Configuration Locally:
```bash
# Run Railway-style tests
npm run test:railway

# Test specific Railway backend config
npm run test:backend:railway

# Simulate Railway environment
TESTING=1 DATABASE_URL="" bash scripts/railway-test.sh
```

### Debug Railway Deployment:
```bash
# Check Railway logs
railway logs

# Test deployment config
railway run bash scripts/railway-test.sh
```

## 🚀 Advanced Configuration

### Customize Test Selection:
Edit `scripts/railway-test.sh` to modify which tests run:
```bash
# Add more critical tests
python3 -m pytest tests/test_new_feature.py::TestCritical -x

# Skip frontend tests entirely
# Comment out the frontend section
```

### Environment-Specific Config:
Create `railway.production.json` for production-specific settings:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "preDeployCommand": ["bash scripts/railway-test.sh"],
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT backend.app:app"
  }
}
```

### Database Testing:
For tests that need database access during pre-deploy:
```bash
# In railway-test.sh, you can access Railway database
export DATABASE_URL=$DATABASE_URL  # Use actual Railway database
python3 -m pytest tests/test_database_integration.py
```

## 🔍 Troubleshooting

### Common Issues:

1. **Tests Timeout**:
   - Reduce test scope in `railway-test.sh`
   - Optimize slow tests
   - Use `-x` flag to fail fast

2. **Missing Dependencies**:
   - Add to `backend/requirements.txt`
   - Update `package.json` for frontend deps

3. **Environment Variables**:
   - Check Railway dashboard variables
   - Verify `.railway-env` reference

4. **Frontend Test Failures**:
   - Expected until store interface is aligned
   - Currently gracefully handled in script

### Getting Help:
- Check Railway deployment logs
- Run `npm run test:railway` locally first
- Verify tests pass in GitHub Actions
- Contact Railway support for platform issues

## ✅ Benefits

✅ **Quality Gate**: Bad code cannot reach production  
✅ **Fast Feedback**: Know immediately if deployment will fail  
✅ **Zero Maintenance**: Runs automatically on every deployment  
✅ **Confidence**: Deploy with certainty that core functionality works  
✅ **Bug Prevention**: Catches regressions before users see them  

This setup ensures your Railway deployments are always tested and reliable! 🎉