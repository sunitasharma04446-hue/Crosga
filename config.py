"""
Configuration for AXL GAME BOT
"""

# Bot Information
BOT_NAME = "AXL GAME BOT"
BOT_USERNAME = "@AXLGameBot"
GROUP_NAME = "@vfriendschat"

# Owner & Admin
OWNER_ID = 0  # SET THIS! Your Telegram User ID (get from @userinfobot)
# Owner: Unlimited bets, can add admins, grant balance, ban users
# Admin: Unlimited bets, can grant balance to users
# User: Normal play with bet limits

# Currency
CURRENCY_SYMBOL = "∆"
CURRENCY_NAME = "AXL"

# Game Settings
SLOTS_EMOJI = ["🍎", "🍌", "🍒", "🍷", "⭐", "💎", "🎯"]
JACKPOT_EMOJI = "🎰"
WINNING_COMBO = "777"  # Using emoji positions

# Rewards
SLOTS_MIN_BET = 10
SLOTS_MAX_BET = 10000
DAILY_BONUS = 100
BONUS_COOLDOWN = 12 * 3600  # 12 hours in seconds

# Game Multipliers
WIN_MULTIPLIER = 1.5  # 150% return
BIG_WIN_MULTIPLIER = 3.0  # 300% return
JACKPOT_MULTIPLIER = 10.0  # 1000% return

# XP System
SLOTS_WIN_XP = 50
SLOTS_LOSS_XP = 10
COIN_FLIP_WIN_XP = 30
COIN_FLIP_LOSS_XP = 5

# Coin Flip Settings
COIN_FLIP_MIN_BET = 10
COIN_FLIP_MAX_BET = 10000
COIN_FLIP_MULTIPLIER = 2.0  # 2x on win

# Messages
WELCOME_MESSAGE = f"""
🎮 **Welcome to {BOT_NAME}!** 🎮

I'm your ultimate casino gaming bot! 

🎰 **Commands:**
• `/balance` - Check your {CURRENCY_SYMBOL} balance
• `/leaderboard` - See the top players  
• `/slots [amount]` - Play slots!
• `/bonus` - Get daily bonus (every 12 hours)
• `/send [amount]` - Send {CURRENCY_SYMBOL} to others

📱 **Join our group:** {GROUP_NAME}
"""

# Slot Results
RESULT_MESSAGES = {
    "jackpot": "🎊 **JACKPOT!** 🎊\nYou won big! {amount}{symbol}",
    "big_win": "💰 **BIG WIN!** 💰\nAwesome! You won {amount}{symbol}",
    "win": "✨ **WIN!** ✨\nGreat! You won {amount}{symbol}",
    "loss": "😢 **LOSS** 😢\nYou lost {amount}{symbol}\nTry again!",
}

# Database
DB_CONNECTION_STRING = "mongodb://localhost:27017/"  # Change to your MongoDB connection
DB_NAME = "axl_game_bot"
DB_COLLECTION_USERS = "users"
