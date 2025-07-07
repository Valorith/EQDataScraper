# Railway Database Configuration Persistence

This document explains how to ensure your EQEmu database configuration persists across Railway deployments.

## The Problem

When deploying to Railway, the database configuration saved through the admin panel gets lost on each deployment because:
1. `config.json` is part of the git repository and gets reset on deployment
2. Railway's persistent volume at `/app/data` may not be properly configured
3. The application needs a reliable way to store configuration that survives deployments

## Solutions

### Solution 1: Environment Variables (Recommended)

The most reliable way to persist database configuration on Railway is using environment variables:

1. Go to your Railway project dashboard
2. Select your backend service
3. Go to the "Variables" tab
4. Add the following environment variables:

```
EQEMU_DATABASE_URL=mysql://username:password@host:port/database
EQEMU_DATABASE_TYPE=mysql
EQEMU_DATABASE_SSL=true
```

The application will automatically use these environment variables and save them to persistent storage when available.

### Solution 2: Railway Persistent Volume

If you prefer file-based persistence:

1. In Railway, go to your backend service
2. Go to the "Settings" tab
3. Under "Volumes", add a persistent volume:
   - Mount path: `/app/data`
   - Name: `eqdata-config`

The application will automatically detect and use this volume for storing configuration.

### Solution 3: Manual Configuration After Deployment

If the above solutions don't work:

1. After each deployment, go to the Admin Dashboard
2. Navigate to Database Configuration
3. Re-enter your database credentials
4. The application will attempt to save to any available persistent storage

## Diagnostics

To check if persistence is working correctly:

1. Go to Admin Dashboard → Database Configuration
2. Check the "storage_info" section in the response
3. Look for:
   - `config_source`: Shows where config was loaded from
   - `storage_available`: Whether persistent storage is available
   - `directory_writable`: Whether the app can write to persistent storage

You can also use the persistence check endpoint:
```
GET /api/admin/database/persist-check
```

This will show:
- Which directories are writable
- Current environment variables
- Recommendations for fixing persistence issues

## Best Practices

1. **Use Environment Variables**: This is the most reliable method for Railway
2. **Don't commit database URLs**: Never add database URLs to `config.json` in git
3. **Test after deployment**: Always verify database connection after deployment
4. **Monitor logs**: Check application logs for persistence warnings

## Troubleshooting

If configuration keeps getting lost:

1. Check if `EQEMU_DATABASE_URL` environment variable is set
2. Verify Railway volume is mounted at `/app/data`
3. Check application logs for write permission errors
4. Use the persist-check endpoint to diagnose issues

## Security Notes

- Database URLs contain passwords - handle with care
- Use Railway's encrypted environment variables
- The application enforces read-only access to the EQEmu database
- Never expose database credentials in logs or error messages