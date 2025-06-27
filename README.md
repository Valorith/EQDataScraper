# EQDataScraper

A modern, full-stack Vue.js application for browsing EverQuest spell data with an interactive, user-friendly interface.

## 🌟 Features

- **Modern Vue.js Frontend**: Single Page Application with Vue Router and Pinia state management
- **Flask REST API Backend**: Serves spell data with caching and comprehensive error handling  
- **Interactive Navigation**: 6×10 level matrix for quick navigation to any spell level
- **Enhanced Spell Cards**: Display spell ID, school, target type, mana cost, and effects with copy functionality
- **Class-Specific Theming**: Dynamic color schemes for all 16 EverQuest classes
- **Responsive Design**: Mobile-friendly interface with glassmorphism aesthetics
- **Smart Features**: "Top" buttons, scroll blur effects, and smooth animations
- **Unified App Runner**: Single script to manage both frontend and backend services

## 🚀 Quick Start

### Option 1: Unified Runner (Recommended)
```bash
# Install all dependencies
python3 run.py install

# Start both frontend and backend
python3 run.py start
```

### Option 2: NPM Scripts
```bash
# Install dependencies
npm run install:all

# Start the application
npm run start
```

### Option 3: Platform-Specific Scripts
**Windows:**
```cmd
run.bat start
```

**Linux/macOS:**
```bash
./run.sh start
```

## 📋 Requirements

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Internet connection** for spell data scraping

## 🛠️ Manual Setup

If you prefer to set up each component manually:

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
npm install
npm run dev
```

## 🎮 Application URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## 📖 Unified Runner Commands

The `run.py` script provides comprehensive application management:

| Command | Description |
|---------|-------------|
| `python3 run.py start` | Start both frontend and backend services |
| `python3 run.py stop` | Stop all running services |
| `python3 run.py status` | Check service status |
| `python3 run.py install` | Install all dependencies |
| `python3 run.py start --skip-deps` | Start without dependency checking |

### Command Options
- `--skip-deps` / `--ignore-deps`: Skip dependency verification (use with caution)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vue.js SPA    │───▶│   Flask API      │───▶│ Spell Scraper   │
│   Port: 3000    │    │   Port: 5000     │    │ (alla.clumsy    │
│                 │    │                  │    │  sworld.com)    │
│ • Vue Router    │    │ • REST Endpoints │    │                 │
│ • Pinia Store   │    │ • Data Caching   │    │ • BeautifulSoup │
│ • Axios Client  │    │ • Error Handling │    │ • Pandas        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎨 User Interface Features

### Interactive Level Matrix
- 6×10 grid (levels 1-60) with visual indicators
- Available levels highlighted in class colors
- Click any level to instantly scroll to spells
- Current section highlighting while browsing

### Enhanced Spell Cards
- **Spell Information**: Name, level, mana cost, school, target type
- **Copy Functionality**: Click to copy spell IDs to clipboard
- **Visual Indicators**: Color-coded target types (self, single, group, AoE)
- **Detailed Effects**: Complete spell descriptions

### Smart Navigation
- "Top" buttons at each level header
- Smooth scroll animations with blur effects
- Responsive design for mobile and desktop
- Back to class selection from any page

## 🎭 Class Theming

Each of the 16 EverQuest classes has a unique color theme:

| Class | Color | Class | Color |
|-------|--------|-------|--------|
| Warrior | Red | Cleric | Light Blue |
| Paladin | Gold | Ranger | Green |
| Shadow Knight | Purple | Druid | Brown |
| Monk | Olive | Bard | Pink |
| Rogue | Gray | Shaman | Teal |
| Necromancer | Indigo | Wizard | Blue |
| Magician | Orange | Enchanter | Violet |
| Beastlord | Maroon | Berserker | Crimson |

## 🔧 Development

### Project Structure
```
EQDataScraper/
├── backend/           # Flask API server
│   ├── app.py        # Main Flask application
│   └── requirements.txt
├── src/              # Vue.js frontend source
│   ├── components/   
│   ├── views/        # Page components
│   ├── stores/       # Pinia state management
│   └── router/       # Vue Router configuration
├── public/           # Static assets
├── run.py           # Unified application runner
├── run.sh           # Unix shell script
├── run.bat          # Windows batch script
└── scrape_spells.py # Original spell scraper
```

### Build for Production
```bash
# Build frontend
npm run build

# Frontend files will be in dist/
# Backend runs the same (python backend/app.py)
```

## 🧪 Testing the Unified Runner

```bash
# Check service status
python3 run.py status

# Start with dependency bypass (if needed)
python3 run.py start --skip-deps

# Stop all services
python3 run.py stop

# Check help
python3 run.py --help
```

## 🔍 API Endpoints

The Flask backend provides these REST endpoints:

- `GET /api/classes` - List all available classes
- `GET /api/spells/{className}` - Get spells for a specific class
- `POST /api/scrape-all` - Trigger scraping for all classes
- `GET /api/cache-status` - Check cache status
- `GET /api/health` - Health check

## 🛠️ Legacy Usage (scrape_spells.py)

The original Python scraper can still be used independently:

```bash
# Scrape all classes once
python scrape_spells.py

# Run continuously (every hour)
python scrape_spells.py --loop --interval 3600

# Use local files instead of web scraping
python scrape_spells.py --local-dir samples
```

## 🐛 Troubleshooting

### Common Issues

**Dependencies Missing:**
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies  
npm install
```

**Port Conflicts:**
- Frontend uses port 3000
- Backend uses port 5000
- Stop conflicting services or change ports in config

**Permission Issues:**
```bash
chmod +x run.sh  # Make shell script executable
```

**Service Won't Start:**
```bash
# Check what's running
python3 run.py status

# Force stop everything
python3 run.py stop

# Start with verbose output
python3 run.py start --skip-deps
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test thoroughly
4. Commit with descriptive messages
5. Push and create a pull request

## 📄 License

This project is provided as-is for personal use and education.

## 🔗 Data Source

Spell data is sourced from [Clumsy's World](https://alla.clumsysworld.com/), an Allakhazam clone for EverQuest.