# 📁 Project Structure - AXL GAME BOT

Complete guide to all files and folders in this project.

## Directory Layout

```
Crosga/
├── bot.py                  # Main bot file - handles all Telegram commands
├── config.py              # Configuration settings and constants
├── database.py            # Database management - SQLite/MongoDB operations
├── slots.py               # Slots game logic and mechanics
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .env                  # Your actual environment (git ignored)
├── .gitignore            # Files to ignore in git
├── Dockerfile            # Docker configuration for deployment
├── setup.sh              # Linux/Mac setup script
├── setup.bat             # Windows setup script
├── README.md             # Main documentation
├── QUICKSTART.md         # Quick start guide
├── DEPLOYMENT.md         # Deployment instructions
├── KOYEB_DEPLOYMENT.md   # Complete Koyeb deployment guide
├── MONGODB_GUIDE.md      # MongoDB Atlas setup
├── OWNER_SETUP.md        # Owner functionality guide
├── PROJECT_STRUCTURE.md  # This file
├── axl_game_bot.db       # Database file (auto-created, git ignored)
└── venv/                 # Virtual environment (git ignored)
```

## 📄 File Descriptions

### Core Bot Files

#### `bot.py` ⭐ MAIN FILE
**Purpose:** Core Telegram bot application
**Main components:**
- `AXLGameBot` class - main bot controller
- `/start` command - welcome message
- `/balance` command - show user balance
- `/leaderboard` command - top 10 players
- `/slots [amount]` - play slots game
- `/bonus` - daily bonus (100∆, 12h cooldown)
- `/send [amount]` - transfer currency
- `/admin` - admin panel
- `/setadmin [id]` - promote admin (owner only)
- `/grant [id] [amount]` - give balance (owner/admin)
- `/ban [id]` - ban player (owner only)
- `/unban [id]` - unban player (owner only)

**Owner/Admin Features:**
- Unlimited bet amounts (no 10-10,000 limit)
- Can grant infinite balance
- Ban/unban players
- Promote other admins

#### `config.py` 🎮 SETTINGS
**Contains all configurable settings:**
- Bot name & group
- Currency: ∆ (AXL)
- Slot emojis
- Game rewards
- Bet limits
- Daily bonus
- Message templates
- OWNER_ID setting

**Modify to:**
- Change currency
- Adjust bet limits
- Change daily bonus
- Customize messages

#### `database.py` 💾 DATA STORAGE
**Database operations:**
- User data (balance, stats, admin flag, ban flag)
- Game history (all slots results)
- Transactions (money transfers)
- Admin/ban management

**Tables:**
1. `users` - Player info and balance
2. `game_history` - Every slot game played
3. `transactions` - All money transfers

**Supports both:**
- SQLite (default) - local database
- MongoDB (optional) - cloud database

#### `slots.py` 🎰 GAME LOGIC
**Slots game implementation:**
- Spins 3 paylines with 7 emojis
- Calculates wins/losses
- Returns formatted display

**Win types:**
- Loss (0x) - no matches
- Win (1.5x) - 1 line match
- Big Win (3x) - 2+ lines
- Jackpot (10x) - all 3 lines

### Setup & Configuration

#### `requirements.txt` 📦
**Python dependencies:**
```
python-telegram-bot==20.7
python-dotenv==1.0.0
pymongo==4.6.0
requests==2.31.0
```

#### `.env.example` 📋
**Template for environment:**
```
TELEGRAM_TOKEN=your_token
OWNER_ID=your_user_id
```

#### `.env` 🔐
**Your actual secrets (git ignored):**
- TELEGRAM_TOKEN
- OWNER_ID
- MONGODB_URI (optional)

#### `.gitignore` 🚫
**Prevents committing:**
- .env (secrets)
- __pycache__/ (Python cache)
- venv/ (virtual env)
- *.db (databases)

### Docker & Deployment

#### `Dockerfile` 🐳
**Container configuration:**
- Python 3.11 slim image
- Installs dependencies
- Runs: `python bot.py`

**Used for:** Koyeb, Render, any Docker hosting

### Setup Scripts

#### `setup.sh` 🔧 (Linux/Mac)
**Automated setup:**
```bash
chmod +x setup.sh
./setup.sh
```

**Does:**
- Checks Python version
- Creates virtual environment
- Installs dependencies
- Creates .env file

#### `setup.bat` 🪟 (Windows)
**Automated setup:**
```bash
setup.bat
```

**Same as setup.sh but for Windows**

### Documentation

#### `README.md` 📖
Quick overview of features, commands, and installation

#### `QUICKSTART.md` ⚡
5-minute setup and running guide

#### `DEPLOYMENT.md` 🚀
Deployment on Render, Railway, Koyeb (older guide)

#### `KOYEB_DEPLOYMENT.md` ☁️
**Complete Koyeb + MongoDB deployment guide**
- Step-by-step Koyeb setup
- MongoDB Atlas (free) setup
- Environment configuration
- Troubleshooting

#### `MONGODB_GUIDE.md` 🗄️
**Detailed MongoDB setup:**
- Create free cluster
- Get connection string
- Connect to bot
- Backup database

#### `OWNER_SETUP.md` 🔑
**Owner functionality:**
- Get your User ID
- Set OWNER_ID
- Use owner commands
- Admin hierarchy

#### `PROJECT_STRUCTURE.md` (this file) 📁
Explains all files in project

### Data Files (Auto-created)

#### `axl_game_bot.db` 💾
**SQLite database file:**
- Created automatically on first run
- Stores all user data, games, transfers
- Local file (can backup)

#### `venv/` 🐍
**Python virtual environment:**
- Isolated Python environment
- All packages installed here
- Auto-created by setup script

#### `__pycache__/` 🔄
**Python bytecode cache:**
- Auto-generated
- Can be deleted (regenerates)
- Git ignored

## 🔄 Dependencies

```
bot.py (Main)
├── config.py (Settings)
├── database.py (Data + SQLite/MongoDB)
├── slots.py (Game logic)
└── Telegram library
```

## 📊 File Statistics

| File | Type | Size | Purpose |
|------|------|------|---------|
| bot.py | Python | ~20KB | Main application |
| config.py | Python | ~2KB | Settings |
| database.py | Python | ~11KB | Database |
| slots.py | Python | ~4KB | Game logic |
| requirements.txt | Text | <1KB | Dependencies |
| Dockerfile | Docker | <1KB | Container |
| setup.sh | Bash | ~1KB | Setup script |
| setup.bat | Batch | ~1KB | Setup script |
| README.md | Markdown | ~2KB | Docs |
| QUICKSTART.md | Markdown | ~5KB | Docs |
| KOYEB_DEPLOYMENT.md | Markdown | ~10KB | Docs |
| MONGODB_GUIDE.md | Markdown | ~7KB | Docs |
| OWNER_SETUP.md | Markdown | ~5KB | Docs |

## 🎯 Quick Commands

### Local Setup
```bash
chmod +x setup.sh
./setup.sh
```

### Local Run
```bash
source venv/bin/activate
python bot.py
```

### Deploy to Koyeb
```bash
git add .
git commit -m "Your message"
git push origin main
# Koyeb auto-deploys
```

### Test Bot
Send `/start` to your bot on Telegram

### Admin Commands
```
/admin - Show admin panel
/grant [id] [amount] - Give balance
/setadmin [id] - Make admin
/ban [id] - Ban player
/unban [id] - Unban player
```

## 🔒 Security

**Secure files:**
- .env (never commit)
- Database backups
- Keep token private

**Public files:**
- All .py files
- All .md files
- config.py

## ✅ Deployment Checklist

- [ ] All files present
- [ ] .env created with bot token
- [ ] requirements.txt installed
- [ ] Bot works locally (`python bot.py`)
- [ ] Git repository up to date
- [ ] OWNER_ID set
- [ ] Deploy to Koyeb
- [ ] Test on live bot

## 📞 Getting Help

1. **Bot issues?** Check README.md
2. **Setup problems?** See QUICKSTART.md
3. **Deploying?** Read KOYEB_DEPLOYMENT.md
4. **MongoDB?** Check MONGODB_GUIDE.md
5. **Owner features?** See OWNER_SETUP.md

---

**Ready to build your gaming bot!** 🚀

Start with: QUICKSTART.md
