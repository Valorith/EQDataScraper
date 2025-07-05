-- Rollback Migration: Remove user account system tables
-- Date: 2025-01-04
-- Description: Safely removes user authentication tables without affecting spell data
-- 
-- WARNING: This will DELETE all user data! Make sure to backup if needed.

-- Drop triggers first
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;

-- Drop the trigger function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_user_preferences_user_id;
DROP INDEX IF EXISTS idx_oauth_sessions_expires;
DROP INDEX IF EXISTS idx_oauth_sessions_token;
DROP INDEX IF EXISTS idx_oauth_sessions_user_id;
DROP INDEX IF EXISTS idx_users_email;

-- Drop tables (order matters due to foreign keys)
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS oauth_sessions;
DROP TABLE IF EXISTS users;

-- Verification query to ensure tables were dropped
SELECT 
    table_name
FROM information_schema.tables
WHERE table_schema = 'public' 
    AND table_name IN ('users', 'oauth_sessions', 'user_preferences');