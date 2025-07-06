# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EQDataScraper is a full-stack Vue.js application for browsing EverQuest spell data. It consists of:
- **Frontend**: Vue 3 SPA (configurable port, default 3000) with Vue Router, Pinia state management, and Vite
- **Backend**: Flask REST API (configurable port, default 5001) that scrapes spell data from alla.clumsysworld.com
- **Data Source**: Web scraping from Clumsy's World (Allakhazam clone)

## Development Commands

### Quick Start (Recommended)
```bash
# Install all dependencies and start both services
python3 run.py install
python3 run.py start

# Alternative with npm
npm run install:all
npm run start
```

### Individual Services
```bash
# Frontend only
npm run dev          # Development server (Vite)
npm run build        # Production build
npm run preview      # Preview production build

# Backend only
cd backend && python app.py

# Service management
python3 run.py status    # Check running services
python3 run.py stop      # Stop all services
```

### Legacy Scraper
```bash
# Standalone scraper (original)
python scrape_spells.py
python scrape_spells.py --loop --interval 3600
```

## Architecture

### Frontend Structure
- **src/App.vue**: Main application component
- **src/views/**: Page components (Home.vue, ClassSpells.vue)
- **src/stores/spells.js**: Pinia store with class data and API calls
- **src/router/index.js**: Vue Router configuration
- **vite.config.js**: Development server with proxy to backend API

### Backend Structure
- **backend/app.py**: Flask REST API with CORS enabled
- **scrape_spells.py**: Core scraping logic (imported by Flask app)
- Caching system with 24-hour expiry and rate limiting

### Key Files
- **run.py**: Unified application runner and dependency manager
- **package.json**: Frontend dependencies and npm scripts
- **backend/requirements.txt**: Python dependencies

## API Endpoints

- `GET /api/classes` - List all EverQuest classes
- `GET /api/spells/{className}` - Get spells for specific class
- `GET /api/search-spells?q={query}` - Search spells across all classes (returns class abbreviations)
- `GET /api/spell-details/{spellId}` - Get detailed spell information from alla website
- `POST /api/scrape-all` - Trigger scraping for all classes
- `GET /api/cache-status` - Check cache status
- `GET /api/health` - Health check

## Data Flow

1. Vue frontend requests spell data via Axios
2. Flask backend checks persistent cache (24-hour expiry)
3. If cache miss, scrapes alla.clumsysworld.com with BeautifulSoup
4. Data cached in memory and saved to JSON files on disk
5. Frontend stores in Pinia with class-specific theming

## Persistent Cache System

- **Location**: `cache/` directory (gitignored)
- **Files**: 
  - `spells_cache.json` - All scraped spell data by class
  - `pricing_cache.json` - Individual spell pricing data
  - `cache_metadata.json` - Timestamps and cache management data
- **Benefits**: 
  - Survives server restarts
  - Eliminates re-scraping on deployment
  - Faster startup times with existing data
- **Management Endpoints**:
  - `GET /api/cache/status` - View cache statistics
  - `POST /api/cache/save` - Manually save cache to disk
  - `POST /api/cache/clear` - Clear all cached data
- **Auto-Save**: Cache automatically saves after successful scrapes and every 10 pricing updates

## Class System

16 EverQuest classes with unique color themes stored in stores/spells.js. Class names are normalized to lowercase for consistent caching and API calls.

## Configuration

- **config.json**: Contains port settings and cache configuration
- **Environment Variables**: `BACKEND_PORT`, `FRONTEND_PORT`, `CACHE_EXPIRY_HOURS`, `MIN_SCRAPE_INTERVAL_MINUTES`
- **Port Conflict Resolution**: `run.py` automatically detects conflicts and suggests alternatives
- **macOS Note**: Port 5000 conflicts with AirPlay Receiver (ControlCenter)

## Cross-Platform Support

- **Windows**: Uses `run.bat`, `taskkill`, `netstat`, `tasklist` for process management
- **macOS**: Uses `lsof`, `ps`, POSIX signals for process management  
- **Linux**: Uses `ss`/`netstat`, POSIX signals for process management
- **WSL**: Automatically detected and handled appropriately
- **npm Commands**: Handles `.cmd` extensions and shell requirements per platform
- **Process Creation**: Platform-specific flags prevent console popup on Windows

## Development Notes

- Vite proxy forwards `/api` requests to Flask backend (port configured dynamically)
- Cache prevents excessive scraping (rate limited to 5-minute intervals)
- Error handling includes network timeouts, rate limiting, and server errors
- Port conflicts are automatically resolved with persistent config updates
- Cross-platform process management handles termination gracefully
- Responsive design with glassmorphism UI aesthetics

## Git Workflow and Contribution Guidelines

### Branching Strategy
- **ALWAYS create feature or bug fix branches instead of committing directly to master**
- **Use descriptive branch names**: `feature/spell-search`, `fix/cache-expiry`, `refactor/api-endpoints`
- **Create pull requests to master** for all changes, regardless of size
- Allow for code review and testing before merging to master

### Branch Naming Convention
```bash
feature/description-of-feature    # New functionality
fix/description-of-bug           # Bug fixes  
refactor/description-of-change   # Code improvements
docs/description-of-update       # Documentation updates
```

### Workflow Process
1. Create a new branch from master: `git checkout -b feature/feature-name`
2. Make changes and commit with descriptive messages
3. Push branch to origin: `git push -u origin feature/feature-name`
4. Create pull request to master via GitHub CLI: `gh pr create`
5. **IMPORTANT**: After creating a PR, automatically open the PR page in Chrome using: `open -a "Google Chrome" <PR_URL>`
6. Review, test, and merge via pull request

### Commit Guidelines
- **All commits and pull requests should be attributed solely to the repository owner**
- **Do not include Co-Authored-By tags or Claude attribution in commits**
- Keep commit messages concise and descriptive of the actual changes
- Use conventional commit format when appropriate (feat:, fix:, refactor:, etc.)
- Each commit should represent a logical unit of work

## Railway Deployment Lessons Learned

### Critical API Configuration Issues
**Problem**: Frontend using relative `/api/` URLs works in development (with Vite proxy) but fails in Railway production where frontend and backend are deployed separately.

**Solution**: Always use `API_BASE_URL` configuration in ALL components:
```javascript
// Required in every Vue component making API calls
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

// Use in API calls
const response = await axios.get(`${API_BASE_URL}/api/endpoint`)
```

**Symptoms of this issue**:
- API calls return HTML instead of JSON (404 pages from frontend)
- JavaScript errors: "Cannot create property 'ClassName' on string '<!DOCTYPE html>'"
- Fast-completing loading modals with no actual data

**Prevention**: 
- Check that ALL Vue components use `API_BASE_URL` for API calls
- Never rely on Vite proxy configuration for production API routing
- Test API calls directly in browser console during development

### Data Loading and Error Handling Best Practices

**Proper Response Processing**:
```javascript
// WRONG - not capturing response data
await axios.get(`${API_BASE_URL}/api/spells/${className}`)

// CORRECT - capturing and using response data
const response = await axios.get(`${API_BASE_URL}/api/spells/${className}`)
const actualCount = response.data.spell_count || 0
```

**HTML Response Detection**:
```javascript
// Check if API returned HTML instead of JSON (proxy routing issue)
if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
  throw new Error(`API returned HTML instead of JSON - possible proxy routing issue`)
}
```

**Console Logging for Debugging**:
- Always add comprehensive console logging for data loading operations
- Log both success and failure cases with actual data counts
- Include error details and response types in error logs

### Frontend State Management
- Use actual API response data instead of hardcoded values (e.g., `spell_count: response.data.spell_count` not `spell_count: 1`)
- Always refresh cache status after bulk operations to update UI
- Handle progress updates even on API errors to prevent stuck loading states

### Build Artifacts and Git Management
- **Always add `dist/` to `.gitignore`** - build artifacts should not be committed
- Railway automatically builds frontend during deployment, local build files are unnecessary
- Clean up any existing `dist/` directories from git history if accidentally committed

### Testing Railway Deployments
- Test API endpoints directly via curl to verify backend functionality
- Check that frontend JavaScript includes expected changes (search minified code for key strings)
- Force browser cache refresh (`Ctrl+Shift+R`) after deployments
- Monitor browser console for API routing errors during testing

### UI Component Design Patterns
- Use dynamic CSS classes for conditional styling (`has-pagination` vs `no-pagination`)
- Design fixed-height components that degrade gracefully with less content
- Implement proper flexbox layouts to prevent overflow issues
- Always consider mobile responsiveness from the start

### Global Search Implementation Notes
- Cross-class spell search requires proper data deduplication by `spell_id`
- Class abbreviations mapping should be consistent between frontend and backend
- Pagination should trigger at 10+ results with fixed dropdown height (520px)
- Hash navigation with query parameters enables deep linking to specific spells
- Modal auto-opening enhances UX but requires careful timing coordination

## Reusable Components

### LoadingModal Component (`src/components/LoadingModal.vue`)
A standardized loading overlay component that should be used throughout the app for all loading states (except within class cards).

**Features:**
- Displays random EverQuest class icons (warrior.gif, cleric.gif, etc.) from `/icons/`
- Semi-transparent overlay with blur effect matching the app's glassmorphism theme
- Pulsing animation with purple glow effect
- Supports both relative (within container) and full-screen positioning
- Pixelated rendering for authentic EverQuest aesthetic

**Usage:**
```vue
<LoadingModal :visible="isLoading" />
<LoadingModal :visible="isSaving" text="Saving changes..." />
<LoadingModal :visible="isProcessing" text="Processing..." :full-screen="true" />
```

**Props:**
- `visible` (Boolean) - Controls visibility
- `text` (String, default: 'Loading') - Loading message
- `fullScreen` (Boolean) - Full viewport coverage
- `showIcon` (Boolean) - Whether to show icon
- `customIcon` (String) - Custom icon URL
- `randomClassIcon` (Boolean) - Use random EQ class icons

**When to use:**
- API calls and data fetching
- Form submissions
- Pagination transitions
- Any async operation that takes noticeable time
- NOT for loading states within individual class cards on the spell selection page