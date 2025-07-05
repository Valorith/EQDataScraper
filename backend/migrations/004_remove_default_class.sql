-- Remove default_class column from user_preferences table
-- This column is no longer needed as the feature has been removed

ALTER TABLE user_preferences 
DROP COLUMN IF EXISTS default_class;