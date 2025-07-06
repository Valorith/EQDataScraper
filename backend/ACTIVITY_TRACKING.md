# Activity Tracking System Documentation

## Overview

The EQDataScraper activity tracking system provides comprehensive logging of user actions and system events. It's designed to track API usage, cache operations, scraping activities, and user authentication events.

## Components

### 1. Database Schema (`migrations/005_add_activity_tracking.sql`)
- **Table**: `activity_logs`
- **Columns**:
  - `id`: Primary key
  - `user_id`: User who performed the action (NULL for system actions)
  - `action`: Type of action performed
  - `resource_type`: Type of resource affected
  - `resource_id`: ID of the affected resource
  - `details`: Additional JSON data
  - `ip_address`: Client IP address
  - `user_agent`: Client user agent string
  - `created_at`: Timestamp

### 2. Activity Model (`models/activity.py`)
- **Class**: `ActivityLog`
- **Methods**:
  - `log_activity()`: Log a new activity
  - `get_recent_activities()`: Retrieve recent activities with filtering
  - `get_activity_count()`: Get count of activities
  - `get_activity_stats()`: Get statistics for a time period
  - `cleanup_old_activities()`: Remove old activity records

### 3. Activity Logger Utility (`utils/activity_logger.py`)
Helper functions for easy activity logging:
- `log_scrape_activity()`: Log scraping-related activities
- `log_cache_activity()`: Log cache operations
- `log_api_activity()`: Log general API activities

### 4. Activity Tracking Integration

#### Auth Routes (`routes/auth.py`)
- **Login**: Logs successful Google OAuth logins
- **User Creation**: Logs new user registrations
- **Logout**: Logs user logouts with session details

#### Admin Routes (`routes/admin.py`)
- **Activity Endpoints**:
  - `GET /admin/activities`: View recent activities
  - `POST /admin/activities`: Log custom activities
  - `GET /admin/activities/stats`: Get activity statistics
  - `POST /admin/activities/cleanup`: Clean up old activities

#### Main App (`app.py`)
Activity logging is integrated into:
- **Scraping Operations**:
  - Individual class scraping (start, complete, error)
  - All classes scraping
- **Cache Operations**:
  - Cache save
  - Cache clear
  - Cache refresh
- **Spell Operations**:
  - Spell search
  - Spell details viewing

## Activity Types

### Authentication Activities
- `login`: User logged in
- `logout`: User logged out
- `token_refresh`: Access token refreshed
- `user_create`: New user registered
- `user_update`: User profile updated

### Scraping Activities
- `scrape_start`: Scraping initiated
- `scrape_complete`: Scraping completed successfully
- `scrape_error`: Scraping failed

### Cache Activities
- `cache_refresh`: Cache refreshed
- `cache_clear`: Cache cleared
- `cache_save`: Cache saved to disk

### API Activities
- `spell_view`: Spell details viewed
- `spell_search`: Spell search performed

### Admin Activities
- `admin_action`: Administrative action performed
- `system_error`: System error occurred
- `api_error`: API error occurred

## Usage Examples

### Logging an Activity
```python
from utils.activity_logger import log_api_activity

# Log a spell search
log_api_activity(
    action='spell_search',
    resource_type='spell',
    details={
        'query': 'gate',
        'results_count': 5
    }
)
```

### Viewing Activities (Admin)
```bash
# Get recent activities
GET /api/admin/activities?limit=50

# Get activities for a specific user
GET /api/admin/activities?user_id=123

# Get activities for a specific action
GET /api/admin/activities?action=login

# Get activity statistics
GET /api/admin/activities/stats?hours=24
```

## Setup Requirements

1. **Environment Variables**:
   - `ENABLE_USER_ACCOUNTS=true` - Must be enabled
   - `DATABASE_URL` - PostgreSQL connection string

2. **Run Migration**:
   ```bash
   python run_migration.py 005_add_activity_tracking.sql
   ```

3. **Test the System**:
   ```bash
   python test_activity_tracking.py
   ```

## Privacy Considerations

- User display names respect `anonymous_mode` settings
- IP addresses are stored for security but should be handled per privacy policy
- Old activities can be cleaned up automatically using the cleanup endpoint

## Monitoring

The activity tracking system enables:
- User engagement metrics
- API usage patterns
- Performance monitoring (scrape times)
- Error tracking and debugging
- Security auditing

## Best Practices

1. **Don't Over-Log**: Only log significant actions
2. **Include Context**: Use the `details` field for relevant context
3. **Regular Cleanup**: Schedule periodic cleanup of old activities
4. **Monitor Performance**: Activity logging should not impact API performance
5. **Respect Privacy**: Follow data retention policies