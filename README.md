# 🎰 AXL GAME BOT - Advanced Telegram Gaming Bot

A powerful Telegram gaming bot with slots game, balance management, leaderboard, and more! Perfect for gaming communities.

## ✨ Features

- 🎰 **Slots Game** - Play with dynamic jackpots and multipliers
- 💰 **Balance Management** - Earn, win, and transfer currency
- 🏆 **Leaderboard** - Compete with other players globally
- 🎁 **Daily Bonus** - Claim 100∆ every 12 hours
- 🤝 **Send Currency** - Transfer ∆ to other players
- 📊 **Game Statistics** - Track your wins, losses, and performance
- 💾 **SQLite Database** - Reliable local storage

## 🎮 Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot |
| `/balance` | Check balance |
| `/leaderboard` | Top 10 players |
| `/slots [amount]` | Play slots |
| `/bonus` | Daily bonus (100∆ every 12h) |
| `/send [amount]` | Send currency (reply to message) |
| `/help` | Help menu |

## 💵 Currency

- **Symbol**: ∆ (AXL)
- **Starting**: 500∆
- **Daily Bonus**: 100∆
- **Bet Range**: 10∆ - 10,000∆

## 🎯 Slots Game

- **Loss** = 0x (lose bet)
- **Win** = 1.5x (1 line match)
- **Big Win** = 3x (2+ lines)
- **Jackpot** = 10x (all 3 lines) 🎊

## 📦 Installation

```bash
# Clone repo
git clone https://github.com/sunitasharma04446-hue/Crosga.git
cd Crosga

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your TELEGRAM_TOKEN

# Run bot
python bot.py
```

## 🚀 Deployment Options

### Render
1. Push to GitHub
2. Connect repo on render.com
3. Add TELEGRAM_TOKEN env var
4. Command: `python bot.py`

### Koyeb
1. Go to koyeb.com
2. Connect GitHub repo
3. Add TELEGRAM_TOKEN
4. Command: `python bot.py`

### Railway
1. Go to railway.app
2. Create new project from GitHub
3. Add TELEGRAM_TOKEN env
4. Deploy!

## 📊 Database Info

Uses SQLite with tables:
- **users** - Balance, stats, bonus timer
- **game_history** - All game results
- **transactions** - Money transfers

## 🔧 Quick Customization

Edit `config.py`:
```python
BOT_NAME = "AXL GAME BOT"
CURRENCY_SYMBOL = "∆"
DAILY_BONUS = 100
JACKPOT_MULTIPLIER = 10.0
```

## 📱 Group

Join: `@vfriendschat`

## 🐛 Troubleshooting

- **Bot not responding**: Check TELEGRAM_TOKEN in .env
- **Database error**: Delete axl_game_bot.db and restart
- **Import error**: `pip install -r requirements.txt`

---

**🎮 Ready to play! Get your token from @BotFather on Telegram and start gaming!**
