-- Migration: Add activity tracking table
-- Date: 2025-01-05
-- Description: Creates table for tracking user activities and system events

-- Create activity_logs table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_resource ON activity_logs(resource_type, resource_id);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_action_time ON activity_logs(user_id, action, created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE activity_logs IS 'Tracks all user activities and system events for auditing';
COMMENT ON COLUMN activity_logs.user_id IS 'User who performed the action (NULL for system actions)';
COMMENT ON COLUMN activity_logs.action IS 'Type of action performed (e.g., login, logout, cache_refresh, scrape_start)';
COMMENT ON COLUMN activity_logs.resource_type IS 'Type of resource affected (e.g., user, cache, spell, class)';
COMMENT ON COLUMN activity_logs.resource_id IS 'ID of the affected resource';
COMMENT ON COLUMN activity_logs.details IS 'Additional JSON data about the activity';
COMMENT ON COLUMN activity_logs.ip_address IS 'IP address from which the action was performed';
COMMENT ON COLUMN activity_logs.user_agent IS 'User agent string of the client';

-- Verification query
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'activity_logs'
ORDER BY ordinal_position;