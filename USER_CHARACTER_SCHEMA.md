# User Character Selection Database Schema

This document outlines the database schema for storing user account character preferences (Primary and Secondary Main characters).

## Database Schema

### Table: `user_character_preferences`

```sql
CREATE TABLE user_character_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    primary_character_id INTEGER,
    primary_character_name VARCHAR(64),
    secondary_character_id INTEGER, 
    secondary_character_name VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Ensure one record per user
    UNIQUE KEY unique_user (user_id),
    
    -- Foreign key constraints (optional, depends on your user system)
    -- FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Alternative Table Structure (Individual Records)

If you prefer separate records for each character selection:

```sql
CREATE TABLE user_main_characters (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    character_id INTEGER NOT NULL,
    character_name VARCHAR(64) NOT NULL,
    main_type ENUM('primary', 'secondary') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Ensure one primary and one secondary per user
    UNIQUE KEY unique_user_type (user_id, main_type),
    
    -- Index for efficient lookups
    INDEX idx_user_character (user_id, main_type)
);
```

## API Endpoints Specification

### Get User's Main Characters
```
GET /api/user/characters/mains
Authorization: Bearer <jwt_token>

Response:
{
  "primaryMain": {
    "characterId": 12345,
    "characterName": "Myselis", 
    "setAt": "2024-01-15T10:30:00Z"
  },
  "secondaryMain": {
    "characterId": 67890,
    "characterName": "Testchar",
    "setAt": "2024-01-15T11:45:00Z"
  }
}
```

### Set Primary Main Character
```
POST /api/user/characters/primary
Authorization: Bearer <jwt_token>
Content-Type: application/json

Body:
{
  "characterId": 12345,
  "characterName": "Myselis"
}

Response:
{
  "success": true,
  "message": "Primary main character set successfully",
  "character": {
    "characterId": 12345,
    "characterName": "Myselis"
  }
}
```

### Set Secondary Main Character
```
POST /api/user/characters/secondary
Authorization: Bearer <jwt_token>
Content-Type: application/json

Body:
{
  "characterId": 67890,
  "characterName": "Testchar"
}

Response:
{
  "success": true,
  "message": "Secondary main character set successfully", 
  "character": {
    "characterId": 67890,
    "characterName": "Testchar"
  }
}
```

### Remove Primary Main Character
```
DELETE /api/user/characters/primary
Authorization: Bearer <jwt_token>

Response:
{
  "success": true,
  "message": "Primary main character removed successfully"
}
```

### Remove Secondary Main Character
```
DELETE /api/user/characters/secondary
Authorization: Bearer <jwt_token>

Response:
{
  "success": true,
  "message": "Secondary main character removed successfully"
}
```

## Backend Implementation Notes

### 1. Authentication Integration

The system assumes you have an authentication mechanism that provides:
- User identification (user_id)
- JWT token validation
- Route protection middleware

Example middleware check:
```javascript
// Middleware to extract user ID from JWT
const requireAuth = (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '')
  
  if (!token) {
    return res.status(401).json({ error: 'Authentication required' })
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.userId = decoded.userId
    next()
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' })
  }
}
```

### 2. Data Validation

- Validate that character exists before setting as main
- Ensure character belongs to accessible realm/server
- Validate character name matches character ID
- Check for race conditions when updating

### 3. Business Logic

- A character can be either Primary or Secondary, not both
- Users can only have one Primary and one Secondary main
- Setting a new Primary/Secondary replaces the previous selection
- Character names are stored for display purposes (denormalization)

### 4. Database Queries

#### Get User Main Characters
```sql
-- Single table approach
SELECT primary_character_id, primary_character_name,
       secondary_character_id, secondary_character_name,
       updated_at
FROM user_character_preferences 
WHERE user_id = ?;

-- Separate records approach  
SELECT character_id, character_name, main_type, updated_at
FROM user_main_characters
WHERE user_id = ?;
```

#### Set Primary Main Character
```sql
-- Single table approach
INSERT INTO user_character_preferences (user_id, primary_character_id, primary_character_name)
VALUES (?, ?, ?)
ON DUPLICATE KEY UPDATE 
  primary_character_id = VALUES(primary_character_id),
  primary_character_name = VALUES(primary_character_name),
  updated_at = CURRENT_TIMESTAMP;

-- Separate records approach
INSERT INTO user_main_characters (user_id, character_id, character_name, main_type)
VALUES (?, ?, ?, 'primary')
ON DUPLICATE KEY UPDATE
  character_id = VALUES(character_id),
  character_name = VALUES(character_name),
  updated_at = CURRENT_TIMESTAMP;
```

#### Remove Main Character
```sql
-- Single table approach
UPDATE user_character_preferences 
SET primary_character_id = NULL, 
    primary_character_name = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = ?;

-- Separate records approach
DELETE FROM user_main_characters 
WHERE user_id = ? AND main_type = 'primary';
```

## Integration with Existing User System

### If using OAuth (Google, Discord, etc.)
```javascript
// Extract user ID from OAuth profile
const userId = req.user.id || req.user.sub || req.user.email;
```

### If using custom user accounts
```javascript
// Extract from your user session/token
const userId = req.session.userId || req.user.id;
```

### If using device-based identification
```javascript
// Generate persistent device ID (fallback)
const userId = req.headers['x-device-id'] || generateDeviceId();
```

## Security Considerations

1. **User Isolation**: Ensure users can only modify their own character preferences
2. **Input Validation**: Validate character IDs and names before storage
3. **Rate Limiting**: Prevent abuse of character selection endpoints
4. **Audit Trail**: Log character selection changes for debugging
5. **Data Privacy**: Don't expose other users' character selections

## Error Handling

### Common Error Responses

```javascript
// Character not found
{
  "error": "CHARACTER_NOT_FOUND",
  "message": "Character with ID 12345 does not exist"
}

// Character not accessible  
{
  "error": "CHARACTER_ACCESS_DENIED", 
  "message": "You do not have access to this character"
}

// Database error
{
  "error": "DATABASE_ERROR",
  "message": "Failed to update character preferences"
}

// Validation error
{
  "error": "VALIDATION_ERROR",
  "message": "Character name does not match character ID",
  "details": {
    "providedName": "WrongName",
    "actualName": "CorrectName"
  }
}
```

## Testing Strategy

1. **Unit Tests**: Test individual API endpoints
2. **Integration Tests**: Test with real database
3. **Authentication Tests**: Verify user isolation
4. **Edge Cases**: Handle missing characters, invalid data
5. **Performance Tests**: Ensure queries are efficient

This schema provides a robust foundation for storing user character preferences while maintaining data integrity and user privacy.