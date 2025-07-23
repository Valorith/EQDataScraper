-- Migration 006 Rollback: Remove user character preferences table
-- Description: Rollback migration that removes character preferences functionality
-- Author: Claude Code
-- Created: 2024-12-19

-- Drop trigger and function
DROP TRIGGER IF EXISTS trigger_update_user_character_preferences_updated_at ON user_character_preferences;
DROP FUNCTION IF EXISTS update_user_character_preferences_updated_at();

-- Drop table
DROP TABLE IF EXISTS user_character_preferences;

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 006_rollback_character_preferences.sql completed successfully';
END $$;