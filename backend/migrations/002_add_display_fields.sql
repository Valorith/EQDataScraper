-- Migration: Add display name and anonymity fields to users table
-- Date: 2025-07-05
-- Description: Adds display_name and anonymous_mode columns to support user privacy preferences

-- Add display_name and anonymous_mode columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(50),
ADD COLUMN IF NOT EXISTS anonymous_mode BOOLEAN DEFAULT FALSE;

-- Create index on display_name for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_display_name ON users(display_name);

-- Verification query
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
    AND column_name IN ('display_name', 'anonymous_mode')
ORDER BY ordinal_position;