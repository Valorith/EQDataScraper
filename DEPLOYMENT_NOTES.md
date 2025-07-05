# OAuth Deployment Notes - Shared Database Environment

## Important: Shared Database Configuration

This application uses the **same production database** for both local development and production deployment. This means:

### Advantages:
- ✅ No database migration needed during deployment (already done locally)
- ✅ Database schema is always in sync
- ✅ Can test with real data locally
- ✅ Simpler deployment process

### Considerations:
- ⚠️ Be careful with test data - it persists in production
- ⚠️ User accounts created locally will exist in production
- ⚠️ Database changes affect production immediately

## Simplified Deployment Process

Since the database is shared, deployment only requires:

1. **Environment Variables Setup** in Railway:
   - Backend: OAuth credentials, JWT secrets
   - Frontend: Google Client ID, redirect URI

2. **Deploy Services**:
   - Deploy backend first
   - Deploy frontend second
   - No database migration step needed!

## Best Practices for Shared Database

### 1. Test User Management
Consider using email patterns to identify test users:
```sql
-- Find potential test users
SELECT email, created_at FROM users 
WHERE email LIKE '%test%' OR email LIKE '%example%';
```

### 2. Google OAuth Redirect URIs
Add both local and production URLs to Google Console:
- `http://localhost:3000/auth/callback` (local)
- `https://your-app.railway.app/auth/callback` (production)

### 3. Data Cleanup
Periodically clean up test data:
```sql
-- Clean up old test sessions
DELETE FROM oauth_sessions 
WHERE created_at < NOW() - INTERVAL '30 days'
AND user_id IN (
    SELECT id FROM users WHERE email LIKE '%test%'
);
```

### 4. Environment Differentiation
Consider adding environment tracking:
```sql
-- Add environment column (optional)
ALTER TABLE users ADD COLUMN IF NOT EXISTS 
    created_environment VARCHAR(20) DEFAULT 'production';
```

## OAuth Configuration Tips

### Local Development
- Can use the same Google OAuth app for local and production
- Just add both redirect URIs to Google Console
- JWT secrets can differ between environments

### Production Deployment
- Only need to set environment variables in Railway
- Database already has all required tables and schema
- Focus on security: strong JWT secrets, proper CORS settings

## Troubleshooting Shared Database Issues

### Issue: Test data appearing in production
**Solution**: Use email filtering in UI or clean up test accounts

### Issue: OAuth sessions from local appearing in production
**Solution**: Sessions are environment-specific due to different JWT secrets

### Issue: Database schema out of sync
**Solution**: This shouldn't happen with shared DB - check migration history

## Security Considerations

1. **Never commit production DATABASE_URL** to version control
2. **Use different JWT secrets** for local vs production
3. **Be careful with admin accounts** - they work in both environments
4. **Monitor user registrations** to catch any test accounts

## Migration Management

With a shared database, migrations should be:
1. Tested thoroughly locally first
2. Applied once (locally) and they're live everywhere
3. Reversible in case of issues

Always backup before major schema changes:
```bash
pg_dump $DATABASE_URL > backup_before_migration.sql
```