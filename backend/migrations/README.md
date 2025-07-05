# Database Migrations for User Authentication

This directory contains SQL migrations for adding user authentication to EQDataScraper.

## Files

- `001_add_user_tables.sql` - Creates user authentication tables
- `001_rollback_user_tables.sql` - Removes user authentication tables
- `../run_migration.py` - Safe migration runner script

## Usage

### Check current state
```bash
cd backend
python run_migration.py --check
```

### Run migration (create user tables)
```bash
cd backend
python run_migration.py
```

### Rollback migration (remove user tables)
```bash
cd backend
python run_migration.py --rollback
```

## Safety Features

1. **No existing data affected** - Only creates new tables
2. **Verification checks** - Confirms spell tables unchanged
3. **Rollback protection** - Prevents accidental data loss
4. **Transaction safety** - Rolls back on any error

## Tables Created

- `users` - Google OAuth user accounts
- `oauth_sessions` - Session management
- `user_preferences` - User settings

## Complete Rollback

If you want to completely remove all user authentication:

```bash
cd backend
python run_migration.py --rollback
cd ..
git checkout master
git branch -D feature/oauth-user-accounts
```

This will restore the database to its original state and remove all authentication code.