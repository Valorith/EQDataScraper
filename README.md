# EQDataScraper

![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white)

A modern Vue.js application for browsing EverQuest spell data with an interactive, user-friendly interface.

## ✨ What This App Does

Browse spell data for all 16 EverQuest classes with:
- **Interactive level matrix** (1-60) for quick navigation
- **Enhanced spell cards** with copy-to-clipboard functionality  
- **Class-specific color themes** for each EverQuest class
- **Real-time spell data** scraped from [Clumsy's World](https://alla.clumsysworld.com/)
- **Responsive design** that works on desktop and mobile

## 🚀 Quick Setup

### Prerequisites
- ![Python](https://img.shields.io/badge/Python_3.8+-3776AB?style=flat-square&logo=python&logoColor=white) ([Download here](https://www.python.org/downloads/))
- ![Node.js](https://img.shields.io/badge/Node.js_16+-339933?style=flat-square&logo=node.js&logoColor=white) ([Download here](https://nodejs.org/))
- 🌐 **Internet connection** for spell data

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

## 🎮 Usage

1. **Select a Class**: Choose from 16 EverQuest classes on the home page
2. **Browse Spells**: Use the level matrix (1-60) to jump to specific spell levels
3. **View Details**: Click spell cards to see detailed information
4. **Copy Spell IDs**: Click any spell to copy its ID to clipboard
5. **Navigate**: Use "Top" buttons or smooth scrolling to move around

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `python3 run.py install` | Install all dependencies |
| `python3 run.py start` | Start both frontend and backend |
| `python3 run.py stop` | Stop all services |
| `python3 run.py status` | Check if services are running |
| `python3 run.py --help` | Show all available options |

## ⚙️ Configuration

The app automatically creates a `config.json` file with sensible defaults:

```json
{
  "backend_port": 5001,
  "frontend_port": 3000,
  "cache_expiry_hours": 24,
  "min_scrape_interval_minutes": 5
}
```

**Environment Variables** (optional):
- `BACKEND_PORT` - Override backend port
- `FRONTEND_PORT` - Override frontend port

**Port Conflicts**: The app automatically detects and resolves port conflicts, updating the configuration as needed.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Vue.js SPA    │───▶│   Flask API      │───▶│ Spell Scraper   │
│   Port: 3000    │    │   Port: 5001     │    │ (alla.clumsy    │
│                 │    │                  │    │  sworld.com)    │
│ • Vue Router    │    │ • REST Endpoints │    │                 │
│ • Pinia Store   │    │ • Data Caching   │    │ • BeautifulSoup │
│ • Axios Client  │    │ • Error Handling │    │ • Pandas        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

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

Validate cross-platform compatibility:
```bash
# Test platform compatibility
python3 validate_platform.py

# Test core functionality
python3 test_functional.py
```

See [TESTING.md](TESTING.md) for comprehensive testing information.

## 🎭 EverQuest Classes Supported

All 16 original EverQuest classes with unique color themes:
- Warrior, Cleric, Paladin, Ranger
- Shadow Knight, Druid, Monk, Bard  
- Rogue, Shaman, Necromancer, Wizard
- Magician, Enchanter, Beastlord, Berserker

## 🤝 Contributing

![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test with `python3 validate_platform.py`
4. Commit with descriptive messages
5. Push and create a pull request

## 📄 License

This project is provided as-is for personal use and education.

---

**Data Source**: Spell data is sourced from [Clumsy's World](https://alla.clumsysworld.com/), an Allakhazam clone for EverQuest.