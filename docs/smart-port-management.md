# Smart Port Management System

## Overview

The EQDataScraper application now includes a smart port management system that automatically detects and resolves port conflicts, ensuring the application always starts successfully regardless of what other services are running on your system.

## Features

### 1. **Automatic Port Conflict Detection**
- Detects when configured ports (backend: 5001, frontend: 3000) are already in use
- Identifies which process is using the conflicting port
- Special handling for known conflicts (e.g., macOS AirPlay Receiver on port 5000)

### 2. **Port Drift Prevention**
- Always attempts to use default ports (5001 and 3000) first
- Automatically reverts to defaults when they become available
- Only uses alternative ports when absolutely necessary
- Prevents gradual drift to higher port numbers over time

### 3. **Intelligent Port Allocation**
- Automatically finds available alternative ports when conflicts are detected
- Ensures frontend and backend ports don't conflict with each other
- Updates configuration files persistently

### 4. **Configuration Synchronization**
- Automatically updates all frontend files that reference the backend port:
  - `src/stores/spells.js`
  - `src/App.vue`
  - `vite.config.js`
  - `.env.development` (created if doesn't exist)
- Ensures frontend always connects to the correct backend port

### 5. **Restart Functionality**
- **Command Line**: `python3 run.py restart`
- **Keyboard Shortcut**: Press `Ctrl+R` while services are running
- Gracefully stops and restarts all services with fresh port allocation

## Usage

### Starting with Smart Port Management

```bash
# The smart port management is automatic
python3 run.py start

# Example output when conflicts are detected:
# 🔍 Smart port management: Checking for conflicts...
# ⚠ Backend port 5001 is in use by: Python
# ✅ Allocating new backend port: 5002
# ⚠ Frontend port 3000 is in use by: node
# ✅ Allocating new frontend port: 3001
# ✅ Updated config.json with new port allocations
# 🔄 Syncing backend port 5002 to frontend files...
# ✅ Updated spells.js
# ✅ Updated App.vue
# ✅ Updated vite.config.js
# ✅ Created .env.development

# Example output when default ports become available again:
# 🔍 Smart port management: Checking for conflicts...
# ✅ Reverting to default backend port: 5001
# ✅ Reverting to default frontend port: 3000
# ✅ Reverted to default ports configuration
# 🔄 Syncing backend port 5001 to frontend files...
```

### Restarting Services

#### Method 1: Command Line
```bash
python3 run.py restart
```

#### Method 2: Keyboard Shortcut
While services are running, press `Ctrl+R` to restart them. The system will:
1. Stop current services
2. Re-run port conflict detection
3. Allocate new ports if needed
4. Start services on available ports

### Checking Status

```bash
python3 run.py status

# Shows which ports services are running on
# Detects untracked services that might be using expected ports
```

## Configuration

### Port Configuration
Ports are stored in `config.json`:
```json
{
  "backend_port": 5001,
  "frontend_port": 3000,
  "cache_expiry_hours": 24,
  "min_scrape_interval_minutes": 5
}
```

### Port Mapping
Active port allocations are tracked in `.port_mapping.json`:
```json
{
  "backend": 5002,
  "frontend": 3001
}
```

## How It Works

1. **Default Port Check**: Always checks if default ports (5001, 3000) are available first
2. **Port Reversion**: Automatically reverts to defaults when they become free
3. **Conflict Resolution**: If defaults are busy, finds the next available port
4. **Configuration Update**: Updates `config.json` with new ports for persistence
5. **Frontend Sync**: Updates all frontend files to use the new backend port
6. **Service Start**: Starts services on the allocated ports
7. **Runtime Monitoring**: Monitors for restart requests (Ctrl+R) and handles them gracefully

## Port Drift Prevention

The system actively prevents "port drift" - the gradual movement to higher port numbers over time:

1. **Default Preference**: Always tries to use ports 5001 (backend) and 3000 (frontend) first
2. **Automatic Reversion**: When default ports become available, the system automatically switches back
3. **Smart Allocation**: Only uses alternative ports when absolutely necessary
4. **Restart Benefits**: Each restart checks if defaults are available again

This ensures your application stays on familiar ports whenever possible, making it easier to remember URLs and maintain consistency.

## Troubleshooting

### Common Issues

1. **Port Still in Use After Stop**
   - The smart port management will detect this and allocate a new port
   - Use `python3 run.py status` to check for untracked services

2. **Frontend Can't Connect to Backend**
   - The sync process ensures all files are updated
   - Check `.env.development` exists with correct port
   - Force restart with `python3 run.py restart`

3. **Keyboard Shortcuts Not Working**
   - Windows: Requires proper terminal (not Git Bash)
   - Unix/Linux: Requires terminal with TTY support
   - Fallback: Use `python3 run.py restart` command

### Manual Port Override

If you need specific ports, edit `config.json` before starting:
```json
{
  "backend_port": 8080,
  "frontend_port": 8081
}
```

The smart port management will respect these but still check for conflicts.

## Testing

A test script is included to verify the smart port management:

```bash
python3 test_port_management.py

# This will:
# 1. Occupy the default ports (5001, 3000)
# 2. Start the application
# 3. Verify it starts on alternative ports
```

## Benefits

1. **Zero Configuration**: Works out of the box, no manual port management needed
2. **Deployment Ready**: Prevents port conflicts in production environments
3. **Developer Friendly**: No more "port already in use" errors
4. **Persistent**: Remembers port allocations between sessions
5. **Transparent**: Shows exactly what ports are allocated and why