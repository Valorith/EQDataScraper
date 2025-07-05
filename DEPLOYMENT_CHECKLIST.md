# OAuth User Account System - Deployment Checklist

This checklist ensures smooth deployment of the OAuth user account system to production.

## Pre-Deployment Setup

### 1. Google OAuth Configuration
- [ ] Create a new project in [Google Cloud Console](https://console.cloud.google.com)
- [ ] Enable Google+ API for the project
- [ ] Create OAuth 2.0 credentials (Web application type)
- [ ] Add authorized redirect URIs:
  - Production frontend: `https://your-frontend-domain.com/auth/callback`
  - Production backend: `https://your-backend-domain.com/api/auth/google/callback`
- [ ] Copy Client ID and Client Secret

### 2. Generate Security Keys
```bash
# Generate JWT Secret (32 bytes, base64 encoded)
openssl rand -base64 32

# Generate Encryption Key (32 bytes, base64 encoded) - if needed
openssl rand -base64 32
```

### 3. Database Setup
- [ ] ✅ **Already Complete** - Database schema is shared between local and production
- [ ] Verify migrations have been run locally (tables already exist in production DB)
- [ ] No additional database setup needed for production deployment

## Railway Deployment Steps

### 1. Backend Environment Variables
Set these in Railway dashboard for the backend service:

```env
# OAuth System
ENABLE_USER_ACCOUNTS=true

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=https://your-frontend.railway.app/auth/callback

# Security Keys
JWT_SECRET_KEY=your-base64-encoded-jwt-secret
ENCRYPTION_KEY=your-base64-encoded-encryption-key  # Optional

# Database (usually auto-set by Railway)
DATABASE_URL=postgresql://user:password@host:5432/database

# CORS (if frontend is on different domain)
CORS_ORIGINS=https://your-frontend.railway.app
```

### 2. Frontend Environment Variables
Set these in Railway dashboard for the frontend service:

```env
# OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=https://your-frontend.railway.app/auth/callback

# Backend API URL (already configured in code as fallback)
VITE_API_BASE_URL=https://your-backend.railway.app
```

### 3. ✅ Database Migrations (Already Complete)

**Since local and production share the same database, migrations run locally are already applied!**

To verify:
```bash
# Check if OAuth tables exist in the shared database
psql $DATABASE_URL -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'oauth_sessions', 'user_preferences');"
```

If you haven't run migrations locally yet:
```bash
# Run locally before deployment
cd backend
python run_all_migrations.py
```

### 4. Deploy Services
1. [ ] Deploy backend service first
2. [ ] Verify backend is running: `https://your-backend.railway.app/api/health`
3. [ ] Deploy frontend service
4. [ ] Verify frontend loads correctly

## Post-Deployment Verification

### 1. Test OAuth Flow
- [ ] Click "Sign in with Google" button
- [ ] Verify redirect to Google
- [ ] Complete Google sign-in
- [ ] Verify redirect back to app
- [ ] Check user profile displays correctly
- [ ] Verify JWT tokens in browser DevTools

### 2. Test User Features
- [ ] Update display name in profile
- [ ] Toggle anonymous mode
- [ ] Select class avatar
- [ ] Change theme preference
- [ ] Verify logout works

### 3. Database Verification
```sql
-- Tables should already exist from local development
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'oauth_sessions', 'user_preferences');

-- Check for users (may include test users from local development)
SELECT email, created_at, 
       CASE WHEN google_id LIKE '%.local' THEN 'local' ELSE 'production' END as environment
FROM users 
ORDER BY created_at DESC 
LIMIT 5;
```

### 4. Security Checks
- [ ] Verify HTTPS is enforced
- [ ] Check no sensitive data in browser console
- [ ] Verify JWT tokens expire correctly
- [ ] Test with invalid/expired tokens

## Rollback Plan

If issues occur:

1. **Disable OAuth Temporarily**
   ```env
   ENABLE_USER_ACCOUNTS=false
   ```

2. **Rollback Database** (if needed)
   ```sql
   -- Remove OAuth tables
   DROP TABLE IF EXISTS user_preferences CASCADE;
   DROP TABLE IF EXISTS oauth_sessions CASCADE;
   DROP TABLE IF EXISTS users CASCADE;
   DROP TABLE IF EXISTS schema_migrations CASCADE;
   ```

3. **Clear Browser Storage**
   - Clear localStorage tokens
   - Clear any cached user data

## Common Issues and Solutions

### Issue: "Missing environment variables"
**Solution**: Ensure all required env vars are set in Railway dashboard

### Issue: OAuth redirect mismatch
**Solution**: Verify redirect URIs match exactly in Google Console and env vars

### Issue: Database connection failed
**Solution**: Check DATABASE_URL is correct and database is accessible

### Issue: CORS errors
**Solution**: Verify CORS_ORIGINS includes frontend URL

### Issue: Tokens not persisting
**Solution**: Check browser localStorage and JWT expiry settings

## Monitoring

After deployment, monitor:
- [ ] Application logs for OAuth errors
- [ ] Database connections and query performance  
- [ ] Failed login attempts
- [ ] Token refresh rates
- [ ] Google OAuth API quotas

## Support Contacts

- Google OAuth Issues: [Google OAuth Support](https://developers.google.com/identity/protocols/oauth2/support)
- Railway Issues: [Railway Discord](https://discord.gg/railway)
- Database Issues: Check Railway PostgreSQL addon status