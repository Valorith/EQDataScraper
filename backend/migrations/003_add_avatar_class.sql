-- Add avatar_class field to users table
-- This allows users to select a class icon as their avatar

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS avatar_class VARCHAR(20);

-- Add comment to explain the field
COMMENT ON COLUMN users.avatar_class IS 'Selected class icon for user avatar (e.g., "wizard", "paladin", etc.)';