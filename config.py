"""
Configuration for AXL GAME BOT
"""

# Bot Information
BOT_NAME = "AXL GAME BOT"
BOT_USERNAME = "@AXLGameBot"
GROUP_NAME = "@vfriendschat"

# Owner & Admin
OWNER_ID = 8430369957  # Owner: Unlimited bets, all permissions, admin access
ADMIN_IDS = [8430369957]  # List of admin user IDs - includes owner

# Currency
CURRENCY_SYMBOL = "🪙"
CURRENCY_NAME = "AXL Coins"

# Game Settings
SLOTS_EMOJI = ["🍎", "🍌", "🍒", "🍷", "⭐", "💎", "🎯"]
JACKPOT_EMOJI = "🎰"
WINNING_COMBO = "777"  # Using emoji positions

# Rewards
SLOTS_MIN_BET = 10
SLOTS_MAX_BET = 10000
DAILY_BONUS = 100
BONUS_COOLDOWN = 12 * 3600  # 12 hours in seconds

# Game Multipliers - USER and ADMIN tuned (very generous per request)
# User multipliers (regular players)
SLOTS_USER_WIN_MULTIPLIER = 10.0      # 10x return on regular win
SLOTS_USER_BIG_MULTIPLIER = 15.0      # 15x return on big win
SLOTS_USER_JACKPOT_MULTIPLIER = 20.0  # 20x return on jackpot

# Admin/Owner multipliers (special boosted rewards)
SLOTS_ADMIN_WIN_MULTIPLIER = 15.0     # 15x for admins
SLOTS_ADMIN_BIG_MULTIPLIER = 25.0     # 25x for big wins
SLOTS_ADMIN_JACKPOT_MULTIPLIER = 50.0 # 50x jackpot for owner/admin

# XP System - BOOSTED REWARDS
SLOTS_WIN_XP = 100  # Doubled
SLOTS_LOSS_XP = 20  # Boosted
COIN_FLIP_WIN_XP = 60  # Doubled
COIN_FLIP_LOSS_XP = 10  # Boosted

# Coin Flip Settings
COIN_FLIP_MIN_BET = 10
COIN_FLIP_MAX_BET = 10000
COIN_FLIP_MULTIPLIER = 2.0  # 2x on win

# Daily Bet Limits
DAILY_USER_BET_LIMIT = 50  # Regular users: 50 bets/day
ADMIN_DAILY_BET_LIMIT = 9999  # Admin: unlimited (9999 is practical max)
OWNER_DAILY_BET_LIMIT = 9999  # Owner: unlimited

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
