-- Migration 006: Add user character preferences table
-- Description: Add table to store user's Primary/Secondary main character selections
-- Author: Claude Code
-- Created: 2024-12-19

-- Create user character preferences table
CREATE TABLE IF NOT EXISTS user_character_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    primary_character_id INTEGER,
    primary_character_name VARCHAR(64),
    secondary_character_id INTEGER, 
    secondary_character_name VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one record per user
    CONSTRAINT unique_user_id UNIQUE (user_id),
    
    -- Add index for efficient lookups
    INDEX idx_user_character_prefs (user_id)
);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_character_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_character_preferences_updated_at
    BEFORE UPDATE ON user_character_preferences
    FOR EACH ROW EXECUTE FUNCTION update_user_character_preferences_updated_at();

-- Add comments for documentation
COMMENT ON TABLE user_character_preferences IS 'Stores user character preferences for Primary/Secondary main character selections';
COMMENT ON COLUMN user_character_preferences.user_id IS 'User identifier from OAuth system (email or sub claim)';
COMMENT ON COLUMN user_character_preferences.primary_character_id IS 'EQEmu character_data.id for primary main character';
COMMENT ON COLUMN user_character_preferences.primary_character_name IS 'Character name for display (denormalized for performance)';
COMMENT ON COLUMN user_character_preferences.secondary_character_id IS 'EQEmu character_data.id for secondary main character';
COMMENT ON COLUMN user_character_preferences.secondary_character_name IS 'Character name for display (denormalized for performance)';

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 006_add_character_preferences.sql completed successfully';
END $$;