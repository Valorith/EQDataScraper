# EQDataScraper

![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white)

A full-stack Vue.js application for browsing EverQuest game data with an interactive, user-friendly interface. Connect to EQEmu databases to explore items, spells, NPCs, zones, and manage your characters.

🚀 **Live Demo**: [https://eqdatascraper-frontend-production.up.railway.app](https://eqdatascraper-frontend-production.up.railway.app)

## ✨ Features

### 🔮 Spell Browser
- **Interactive level matrix** (1-60) for quick navigation
- **Class-specific spell lists** for all 16 EverQuest classes
- **Enhanced spell cards** with copy-to-clipboard functionality  
- **Class-specific color themes** for authentic EverQuest feel
- **Global spell search** across all classes
- **Detailed spell information** including pricing and availability

### 🗡️ Item Database
- **Comprehensive item search** connected to EQEmu databases
- **Detailed item statistics** and descriptions
- **Item availability** tracking (drops, merchants, ground spawns, forage)
- **Drop sources** with NPC and zone information
- **Tradeskill recipe** integration
- **Item type filtering** and categorization

### 🗺️ Zone Explorer
- **Interactive zone maps** with pan and zoom functionality
- **Zone NPC listings** with spawn locations
- **Zone item drops** and availability
- **Zone search** with autocomplete
- **Visual zone representations** using EQEmu map data

### 👥 NPC Database
- **NPC search** with detailed statistics
- **Loot tables** and drop information
- **Spawn location** tracking
- **Merchant inventory** for vendor NPCs

### 🎭 Character Management
- **Primary and Secondary main** character slots
- **Character search** across EQEmu database
- **Character inventory** viewer with search and filtering
- **Equipment display** with stat tracking
- **Platinum and bank information**
- **Visual class icons** and character portraits

### 🔐 User Accounts & Authentication
- **Google OAuth integration** for secure login
- **User profiles** with personalized settings
- **Activity tracking** and search history
- **Session management** with JWT tokens
- **Secure encryption** for sensitive data

### 👑 Admin Dashboard
- **User management** with role assignment
- **System monitoring** and health checks
- **Activity logs** and user tracking
- **Database configuration** for EQEmu connections
- **Cache management** and status monitoring

### 🎨 User Experience
- **Responsive design** that works on desktop and mobile
- **Glassmorphism UI** with modern aesthetics
- **Loading animations** with EverQuest class icons
- **Toast notifications** for user feedback
- **Thread monitoring** for development/debugging
- **Backend status indicator** for connection health

## 🚀 Quick Setup

### Prerequisites
- ![Python](https://img.shields.io/badge/Python_3.8+-3776AB?style=flat-square&logo=python&logoColor=white) ([Download here](https://www.python.org/downloads/))
- ![Node.js](https://img.shields.io/badge/Node.js_16+-339933?style=flat-square&logo=node.js&logoColor=white) ([Download here](https://nodejs.org/))
- **Optional:** PostgreSQL database for user accounts and OAuth (can be disabled)
- **Optional:** MySQL database connection to EQEmu server for item/character data

### Installation & Start

**Option 1: Automated Setup (Recommended)**
```bash
# Clone the repository
git clone https://github.com/your-username/EQDataScraper.git
cd EQDataScraper

# Install all dependencies and start
python3 run.py install
python3 run.py start
```

**Option 2: Platform-Specific Scripts**
```bash
# 🪟 Windows
run.bat install
run.bat start

# 🍎 macOS / 🐧 Linux  
./run.sh install
./run.sh start
```

**Option 3: Manual Setup**
```bash
# Install dependencies
pip install -r backend/requirements.txt
npm install

# Start services
npm run start
```

### Access the Application
- 🌐 **Frontend**: http://localhost:3000
- ⚡ **Backend API**: http://localhost:5001

*Ports are automatically configured and conflicts are resolved automatically.*

### Optional: Configure OAuth and Database

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Enable user accounts** (optional):
   - Set `ENABLE_USER_ACCOUNTS=true` in `.env`
   - Configure Google OAuth credentials from [Google Console](https://console.cloud.google.com)
   - Set up PostgreSQL database for user data

3. **Connect to EQEmu database** (optional):
   - Configure production database in Admin Dashboard
   - Or set `production_database_url` in `config.json`
   - Enables items, NPCs, zones, and character features

See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for detailed configuration instructions.

## 🎮 Usage

### Spell Browser
1. **Select a Class**: Choose from 16 EverQuest classes
2. **Browse Spells**: Use the level matrix (1-60) to jump to specific spell levels
3. **Search Globally**: Use the search bar to find spells across all classes
4. **View Details**: Click spell cards to see detailed information and pricing
5. **Copy Spell IDs**: Click any spell to copy its ID to clipboard

### Item Database (requires database connection)
1. **Search Items**: Use the search bar to find items by name
2. **Filter by Type**: Browse items by equipment slot or category
3. **View Drop Sources**: See which NPCs drop the item and in which zones
4. **Check Merchants**: Find vendors that sell the item
5. **View Recipes**: See tradeskill recipes that use or create the item

### Zone Explorer (requires database connection)
1. **Browse Zones**: Search or select from zone list
2. **View Maps**: Interactive zone maps with pan/zoom
3. **See NPCs**: View all NPCs that spawn in the zone
4. **Check Loot**: See what items drop in the zone

### Character Management (requires database connection and login)
1. **Login**: Sign in with Google OAuth
2. **Search Characters**: Find your characters from EQEmu database
3. **Set Mains**: Assign primary and secondary main characters
4. **View Inventory**: Browse character items with search and filters
5. **Track Equipment**: See equipped items and stats

## 🛠️ Commands

### Main Commands

| Command | Description |
|---------|-------------|
| `python3 run.py install` | Install all dependencies |
| `python3 run.py start` | Start both frontend and backend |
| `python3 run.py stop` | Stop all services |
| `python3 run.py status` | Check if services are running |
| `python3 run.py --help` | Show all available options |

### NPM Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server (frontend only) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run test` | Run frontend tests with Vitest |
| `npm run test:backend` | Run backend tests with pytest |
| `npm run test:all` | Run all tests |

## ⚙️ Configuration

### Application Settings (config.json)

The app automatically creates a `config.json` file with sensible defaults:

```json
{
  "backend_port": 5001,
  "frontend_port": 3000,
  "cache_expiry_hours": 24,
  "pricing_cache_expiry_hours": 168,
  "min_scrape_interval_minutes": 5,
  "use_production_database": false,
  "production_database_url": ""
}
```

### Environment Variables (.env)

**Core Settings:**
- `BACKEND_PORT` - Override backend port (default: 5001)
- `FRONTEND_PORT` - Override frontend port (default: 3000)
- `CACHE_EXPIRY_HOURS` - Spell cache expiry time
- `MIN_SCRAPE_INTERVAL_MINUTES` - Minimum time between scrapes

**User Accounts (Optional):**
- `ENABLE_USER_ACCOUNTS` - Enable OAuth authentication (default: false)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `OAUTH_REDIRECT_URI` - OAuth callback URL
- `JWT_SECRET_KEY` - JWT token signing key
- `ENCRYPTION_KEY` - Data encryption key

**Database Connections:**
- `DATABASE_URL` - PostgreSQL URL for user accounts (when OAuth enabled)
- Production database URL can be set via Admin Dashboard or `config.json`

**Important Notes:**
- **Port Conflicts**: Automatically detected and resolved
- **Database Types**: PostgreSQL for auth, MySQL for EQEmu game data
- **Security**: Never commit `.env` file with real credentials

## 🏗️ Architecture

```
┌─────────────────────────┐
│   Vue.js 3 Frontend     │
│   (Port: 3000)          │
│                         │
│ • Vue Router            │
│ • Pinia State Mgmt      │
│ • Axios HTTP Client     │
│ • Component Library     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐     ┌──────────────────┐
│   Flask Backend API     │────▶│ Spell Data Cache │
│   (Port: 5001)          │     │ (JSON + Memory)  │
│                         │     └──────────────────┘
│ • REST API Endpoints    │
│ • OAuth Authentication  │     ┌──────────────────┐
│ • JWT Session Mgmt      │────▶│  PostgreSQL DB   │
│ • Database Pooling      │     │ (User Accounts)  │
│ • Cache Management      │     └──────────────────┘
│ • Rate Limiting         │
└────────┬────────────────┘     ┌──────────────────┐
         │                      │   MySQL DB       │
         └─────────────────────▶│ (EQEmu Server)   │
                                │ • Items          │
                                │ • NPCs           │
                                │ • Zones          │
                                │ • Characters     │
                                └──────────────────┘
```

### Key Components

**Frontend Stack:**
- Vue 3 with Composition API
- Vite for build tooling
- Pinia for state management with persistence
- Vue Router for navigation
- Axios for API communication

**Backend Stack:**
- Flask REST API with CORS
- SQLAlchemy for database ORM
- PyMySQL for MySQL connections
- psycopg2 for PostgreSQL connections
- Google OAuth for authentication
- BeautifulSoup for web scraping
- Gunicorn for production server

**Data Sources:**
- Spell data scraped from [Clumsy's World](https://alla.clumsysworld.com/)
- Item/NPC/Zone data from EQEmu MySQL database
- User data stored in PostgreSQL database

## 🐛 Troubleshooting

**App Won't Start?**
```bash
# Check what's running
python3 run.py status

# Stop everything and restart
python3 run.py stop
python3 run.py start
```

**Dependencies Missing?**
```bash
# Reinstall everything
python3 run.py install
```

**Port Conflicts?**
- The app automatically detects and resolves port conflicts
- On macOS, port 5000 conflicts with AirPlay Receiver (this is handled automatically)

**Permission Issues on macOS/Linux?**
```bash
chmod +x run.sh
```

**Need Help?**
```bash
python3 run.py --help
```

## 🧪 Testing

![Cross Platform](https://img.shields.io/badge/Cross_Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)

### Frontend Tests (Vitest)
```bash
npm run test              # Run tests in watch mode
npm run test:ui           # Run tests with UI
npm run test:run          # Run tests once
npm run test:coverage     # Run with coverage report
```

### Backend Tests (pytest)
```bash
npm run test:backend              # Run all backend tests
npm run test:backend:coverage     # Run with coverage
cd backend && pytest              # Run pytest directly
```

### Platform Validation
```bash
python3 validate_platform.py     # Test platform compatibility
```

### Railway Pre-Deploy Tests
```bash
npm run test:railway             # Run critical tests for Railway deployment
```

The application includes automated testing that runs before Railway deployments to ensure stability. See [TESTING_STRATEGY.md](TESTING_STRATEGY.md) and [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for comprehensive testing information.

## 📡 API Endpoints

### Spell Endpoints
- `GET /api/classes` - List all EverQuest classes
- `GET /api/spells/<className>` - Get spells for specific class
- `GET /api/spells/search?q=<query>` - Search spells across all classes
- `GET /api/spells/<spellId>/details` - Get detailed spell information
- `GET /api/spells/<spellId>/items` - Get items related to spell
- `POST /api/scrape-all` - Trigger scraping for all classes

### Item Endpoints
- `GET /api/items/search?q=<query>` - Search items
- `GET /api/items/<itemId>` - Get item details
- `GET /api/items/types` - List item types
- `GET /api/items/<itemId>/drop-sources` - Get NPC drop sources
- `GET /api/items/<itemId>/merchant-sources` - Get merchant vendors
- `GET /api/items/<itemId>/ground-spawns` - Get ground spawn locations
- `GET /api/items/<itemId>/forage-sources` - Get forage zones
- `GET /api/items/<itemId>/tradeskill-recipes` - Get recipes using item
- `GET /api/items/<itemId>/created-by-recipes` - Get recipes creating item
- `GET /api/items/<itemId>/availability` - Get all availability data

### NPC Endpoints
- `GET /api/npcs/search?q=<query>` - Search NPCs
- `GET /api/npcs/<npcId>/details` - Get NPC details and loot table

### Zone Endpoints
- `GET /api/zone-map/<zoneShortName>` - Get zone map data
- `GET /api/zone-npcs/<zoneShortName>` - Get NPCs in zone
- `GET /api/zone-items/<zoneShortName>` - Get items available in zone

### Character Endpoints (requires auth)
- `GET /api/characters/search?name=<name>` - Search characters
- `GET /api/characters/<characterId>` - Get character details
- `GET /api/characters/<characterId>/inventory` - Get character inventory
- `POST /api/characters/set-main` - Set primary/secondary main
- `DELETE /api/characters/clear-main` - Clear main slot

### Auth Endpoints
- `GET /api/auth/login` - Initiate OAuth login
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/logout` - Logout user
- `GET /api/auth/user` - Get current user info

### Admin Endpoints (requires admin role)
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/<userId>/role` - Update user role
- `GET /api/admin/logs` - Get activity logs
- `GET /api/admin/system/stats` - Get system statistics
- `POST /api/admin/database/config` - Configure database connection

### System Endpoints
- `GET /api/health` - Health check
- `GET /api/health/database` - Database health check
- `GET /api/cache/status` - Get cache status
- `POST /api/cache/save` - Save cache to disk
- `POST /api/cache/clear` - Clear all caches
- `GET /api/startup-status` - Get application startup status

## 🎭 EverQuest Classes Supported

All 16 original EverQuest classes with unique color themes:
- Warrior, Cleric, Paladin, Ranger
- Shadow Knight, Druid, Monk, Bard  
- Rogue, Shaman, Necromancer, Wizard
- Magician, Enchanter, Beastlord, Berserker

## 🚀 Deployment

### Railway Deployment

This application is designed for easy deployment to Railway:

1. **Connect Repository**: Link your GitHub repo to Railway
2. **Configure Environment Variables**: Set OAuth credentials and database URLs
3. **Deploy**: Railway automatically builds and deploys
4. **Automated Testing**: Pre-deploy tests ensure stability

The application uses Docker for consistent deployments and includes automated health checks. See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for detailed deployment instructions.

### Local Production Build

```bash
# Build frontend
npm run build

# Serve production build
npm run serve

# Or use Docker
docker build -t eqdatascraper .
docker run -p 3000:3000 eqdatascraper
```

## 🤝 Contributing

![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test thoroughly:
   - Run `npm run test:all` for comprehensive testing
   - Run `python3 validate_platform.py` for platform compatibility
   - Test locally with `python3 run.py start`
4. Commit with descriptive messages (follow conventional commits)
5. Push and create a pull request

See [CLAUDE.md](CLAUDE.md) for development guidelines and architecture details.

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Development guide and architecture overview
- **[RAILWAY_SETUP.md](RAILWAY_SETUP.md)** - Railway deployment instructions
- **[TESTING_STRATEGY.md](TESTING_STRATEGY.md)** - Testing approach and coverage
- **[DEPLOYMENT_NOTES.md](DEPLOYMENT_NOTES.md)** - Production deployment notes
- **[.env.example](.env.example)** - Environment variable template

## 🗄️ Database Configuration

### Two-Database System

EQDataScraper uses **two separate database systems**:

1. **Auth Database (PostgreSQL)** - Optional
   - User accounts and OAuth sessions
   - Activity logs and search history
   - Spell data cache
   - Set via `DATABASE_URL` environment variable

2. **Content Database (MySQL)** - Optional, Read-Only
   - EQEmu game data (items, NPCs, zones, characters)
   - Connected via Admin Dashboard or config.json
   - Read-only to protect game data integrity

**Note**: Both databases are optional. The spell browser works without any database connection. Items, NPCs, zones, and characters require the MySQL content database. User accounts require the PostgreSQL auth database.

## 🔒 Security Features

- **OAuth 2.0** authentication with Google
- **JWT tokens** for session management
- **Encrypted storage** for sensitive data
- **Rate limiting** on API endpoints
- **CORS protection** with configurable origins
- **Input sanitization** to prevent injection attacks
- **Role-based access control** (user/admin roles)
- **Secure password handling** (no passwords stored)

## 📄 License

This project is provided as-is for personal use and education.

---

**Data Sources**: 
- Spell data scraped from [Clumsy's World](https://alla.clumsysworld.com/), an Allakhazam clone for EverQuest
- Item, NPC, zone, and character data from EQEmu database servers
- EverQuest® is a registered trademark of Daybreak Game Company LLC