-- Rollback Migration: Remove activity tracking table
-- Date: 2025-01-05
-- Description: Removes the activity tracking table and associated indexes

-- Drop indexes first
DROP INDEX IF EXISTS idx_activity_logs_user_id;
DROP INDEX IF EXISTS idx_activity_logs_action;
DROP INDEX IF EXISTS idx_activity_logs_created_at;
DROP INDEX IF EXISTS idx_activity_logs_resource;
DROP INDEX IF EXISTS idx_activity_logs_user_action_time;

-- Drop the table
DROP TABLE IF EXISTS activity_logs;

-- Verification query
SELECT 
    table_name
FROM information_schema.tables
WHERE table_schema = 'public' 
    AND table_name = 'activity_logs';