"""
AXL GAME BOT - Main Telegram Bot
Advanced casino gaming bot with slots, balance, leaderboard, and more!
"""

import os
import logging
import html
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode, ChatAction

from config import *
from database import db
from slots import slots_game

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class AXLGameBot:
    def __init__(self, token: str):
        self.token = token
        self.app = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        db.get_or_create_user(user.id, user.username, user.first_name)

        keyboard = [
            [InlineKeyboardButton("🎰 Play Slots", callback_data='slots_menu'),
             InlineKeyboardButton("💰 Balance", callback_data='balance')],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data='leaderboard'),
             InlineKeyboardButton("🎁 Daily Bonus", callback_data='bonus')],
            [InlineKeyboardButton("🤝 Send AXL", callback_data='send_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user = update.effective_user
        user_data = db.get_or_create_user(user.id, user.username, user.first_name)

        balance_text = f"""
╔━━━━━━━━━━━━━━━━━━━━━━━━━╗
║ 💳 **YOUR BALANCE** 💳
╠━━━━━━━━━━━━━━━━━━━━━━━━━╣
║ Balance: `{user_data['balance']}{CURRENCY_SYMBOL}`
║ Total Wins: `{user_data['total_winnings']}{CURRENCY_SYMBOL}`
║ Total Losses: `{user_data['total_losses']}{CURRENCY_SYMBOL}`
║ Games Played: `{user_data['games_played']}`
╚━━━━━━━━━━━━━━━━━━━━━━━━━╝
"""
        await update.message.reply_text(balance_text, parse_mode=ParseMode.MARKDOWN)

    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command"""
        await update.message.chat.send_action(ChatAction.TYPING)

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured: MONGODB_URI is missing.", parse_mode=ParseMode.HTML)
            return

        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"

        from pymongo import MongoClient

        def _get_top():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            cursor = users_col.find({"appId": APP_ID}).sort([("economy.balance", -1)]).limit(10)
            results = list(cursor)
            client.close()
            return results

        leaderboard_data = await asyncio.to_thread(_get_top)

        leaderboard_text = '<b>🏆 TOP 10 PLAYERS</b>\n\n'
        for idx, user in enumerate(leaderboard_data, 1):
            rank_emoji = ["🥇", "🥈", "🥉"][idx-1] if idx <= 3 else f"{idx}️⃣"
            username = user.get('username')
            user_id = user.get('userId')
            first_name = user.get('first_name')
            display = f"@{html.escape(username)}" if username else html.escape(first_name or f"User {user_id}")
            if username:
                link = f"https://t.me/{html.escape(username)}"
            else:
                link = f"tg://user?id={user_id}"

            balance_val = user.get('economy', {}).get('balance', 0)
            balance_html = html.escape(str(balance_val)) + html.escape(CURRENCY_SYMBOL)
            leaderboard_text += f"{rank_emoji} <a href=\"{link}\">{display}</a> → <code>{balance_html}</code>\n"

        leaderboard_text += f"\nJoin {html.escape(GROUP_NAME)} and start playing!"

        await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)

    async def bonus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bonus command"""
        user = update.effective_user
        user_data = db.get_or_create_user(user.id, user.username, user.first_name)

        # Check cooldown
        last_bonus_time = user_data['last_bonus_time']
        current_time = int(datetime.now().timestamp())
        time_remaining = BONUS_COOLDOWN - (current_time - last_bonus_time)

        if time_remaining > 0:
            hours = time_remaining // 3600
            minutes = (time_remaining % 3600) // 60
            await update.message.reply_text(
                f"⏰ **Bonus Cooldown**\n\n"
                f"Come back in `{hours}h {minutes}m` for your next bonus!",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Give bonus
        new_balance = db.update_balance(user.id, DAILY_BONUS)
        db.set_bonus_claimed(user.id)

        await update.message.reply_text(
            f"🎁 **Daily Bonus Claimed!**\n\n"
            f"You received `{DAILY_BONUS}{CURRENCY_SYMBOL}`\n"
            f"New Balance: `{new_balance}{CURRENCY_SYMBOL}`",
            parse_mode=ParseMode.MARKDOWN
        )

    async def slots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /slots [amount] command"""
        user = update.effective_user

        # Validate amount
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                f"🎰 Usage: /slots <amount>\nExample: /slots 100",
                parse_mode=ParseMode.HTML
            )
            return

        try:
            bet_amount = float(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount! Use numbers only.", parse_mode=ParseMode.HTML)
            return

        if bet_amount <= 0:
            await update.message.reply_text("❌ Bet must be greater than 0!", parse_mode=ParseMode.HTML)
            return

        # Check admin/owner privileges for limits
        is_owner = user.id == OWNER_ID
        is_admin = db.is_admin_user(user.id)
        if not (is_owner or is_admin):
            if bet_amount < SLOTS_MIN_BET or bet_amount > SLOTS_MAX_BET:
                await update.message.reply_text(
                    f"❌ Bet must be between {SLOTS_MIN_BET}{CURRENCY_SYMBOL} and {SLOTS_MAX_BET}{CURRENCY_SYMBOL}",
                    parse_mode=ParseMode.HTML
                )
                return

        # MongoDB only (no SQLite fallback)
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured: MONGODB_URI is missing. Please contact the owner.", parse_mode=ParseMode.HTML)
            return

        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"

        # Helper to fetch and update balance using pymongo (run in thread)
        async def get_balance_and_update(user_obj, change: float = 0, create_if_missing: bool = False):
            # user_obj can be user id or telegram User object
            uid = user_obj.id if hasattr(user_obj, 'id') else int(user_obj)

            from pymongo import MongoClient, ReturnDocument

            def _work():
                client = MongoClient(MONGODB_URI)
                mongo_db = client['artifacts']  # use short safe DB name
                users_col = mongo_db['users']

                query = {"appId": APP_ID, "userId": uid}

                if change != 0:
                    # Ensure document exists; use upsert and return AFTER
                    update = {"$setOnInsert": {"economy": {"balance": 500.0}, "userId": uid}, "$inc": {"economy.balance": change}}
                    doc_after = users_col.find_one_and_update(query, update, upsert=True, return_document=ReturnDocument.AFTER)
                    before_bal = float(doc_after.get("economy", {}).get("balance", 0)) - change
                    new_bal = float(doc_after.get("economy", {}).get("balance", 0))
                else:
                    doc = users_col.find_one(query)
                    if not doc:
                        if create_if_missing:
                            users_col.update_one(query, {"$setOnInsert": {"economy": {"balance": 500.0}, "userId": uid, "username": user.username if hasattr(user, 'username') else None, "first_name": user.first_name if hasattr(user, 'first_name') else None}}, upsert=True)
                            doc = users_col.find_one(query)
                        else:
                            client.close()
                            return None, None
                    before_bal = float(doc.get("economy", {}).get("balance", 0))
                    new_bal = before_bal

                client.close()
                return before_bal, new_bal

            before, new = await asyncio.to_thread(_work)
            return before, new

        # Fetch current balance
        before_balance, _ = await get_balance_and_update(user, 0, create_if_missing=True)
        if before_balance is None:
            await update.message.reply_text("❌ Could not fetch your balance. Try again later.", parse_mode=ParseMode.HTML)
            return

        if before_balance < bet_amount and not (is_owner or is_admin):
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {before_balance}{CURRENCY_SYMBOL}, bet: {bet_amount}{CURRENCY_SYMBOL}",
                parse_mode=ParseMode.HTML
            )
            return

        # Send animated dice (slot emoji) and wait for animation
        try:
            dice_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎰', reply_to_message_id=update.message.message_id)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send slot animation: {e}")
            return

        # Wait exactly 4 seconds for animation
        await asyncio.sleep(4)

        # Get the dice value
        try:
            dice_value = getattr(dice_msg, 'dice').value
        except Exception:
            await dice_msg.reply_text("❌ Failed to read spin result.", parse_mode=ParseMode.HTML)
            return

        # Determine result
        multiplier = 0.0
        result_type = "loss"
        if dice_value == 64:
            multiplier = 10.0
            result_type = "JACKPOT"
        elif dice_value in (1, 22, 43):
            multiplier = 2.0
            result_type = "WIN"
        else:
            multiplier = 0.0
            result_type = "LOSS"

        if result_type == "LOSS":
            net_change = -bet_amount
            amount_text = f"-{bet_amount}{CURRENCY_SYMBOL}"
        else:
            profit = bet_amount * (multiplier - 1)
            net_change = profit
            amount_text = f"+{int(profit)}{CURRENCY_SYMBOL}" if profit == int(profit) else f"+{profit:.2f}{CURRENCY_SYMBOL}"

        # Update DB with net_change
        before_bal_check, new_balance = await get_balance_and_update(user, net_change, create_if_missing=True)

        # Build result message (HTML)
        user_name = html.escape(user.first_name or user.username or str(user.id))
        result_title = f"🎰 <b>{result_type}</b>"
        details = (
            f"User: <b>{user_name}</b>\n"
            f"Result: <b>{result_type}</b> (dice value: {dice_value})\n"
            f"Amount: <code>{amount_text}</code>\n"
            f"Balance: <b>{new_balance}{html.escape(CURRENCY_SYMBOL)}</b>"
        )

        # Build inline keyboard
        keyboard = [
            [InlineKeyboardButton("Play Again 🎰", callback_data=f"slots_play_{int(bet_amount)}")],
            [InlineKeyboardButton("💳 Balance", callback_data="balance"), InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Reply to dice message with the result (HTML) and inline buttons
        try:
            await dice_msg.reply_text(f"{result_title}\n\n{details}", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            await update.message.reply_text(f"{result_title}\n\n{details}", parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    async def send_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /send [amount] command"""
        user = update.effective_user

        if not update.message.reply_to_message:
            await update.message.reply_text(
                f"🤝 **Usage:** Reply to someone's message with `/send [amount]`\n\n"
                f"Example: Reply to a message and type `/send 100`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        target_user = update.message.reply_to_message.from_user
        sender_data = db.get_or_create_user(user.id, user.username, user.first_name)

        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                f"❌ Please specify amount: `/send [amount]`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        try:
            amount = float(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!", parse_mode=ParseMode.MARKDOWN)
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0!", parse_mode=ParseMode.MARKDOWN)
            return

        if amount > sender_data['balance']:
            await update.message.reply_text(
                f"❌ **Insufficient balance!**\n"
                f"You need: `{amount}{CURRENCY_SYMBOL}`\n"
                f"You have: `{sender_data['balance']}{CURRENCY_SYMBOL}`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Perform transfer
        if db.transfer_balance(user.id, target_user.id, amount):
            target_name = target_user.username or target_user.first_name or f"User {target_user.id}"
            sender_new_balance = db.update_balance(user.id, -amount)  # Will fix
            db.update_balance(target_user.id, amount)

            await update.message.reply_text(
                f"✅ **Transfer Successful!**\n\n"
                f"Sent: `{amount}{CURRENCY_SYMBOL}` to **@{target_name}**\n"
                f"Your New Balance: `{sender_new_balance}{CURRENCY_SYMBOL}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Transfer failed!", parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = f"""
╔═══════════════════════════════════════╗
║ 📖 **{BOT_NAME} - Help** 📖
╚═══════════════════════════════════════╝

**Available Commands:**

🎮 `/start` - Start the bot
💰 `/balance` - Check your balance
🏆 `/leaderboard` - View top players
🎰 `/slots [amount]` - Play slots game
🎁 `/bonus` - Get daily bonus (every 12 hours)
🤝 `/send [amount]` - Send {CURRENCY_SYMBOL} to others

**Game Rules:**
• Minimum bet: `{SLOTS_MIN_BET}{CURRENCY_SYMBOL}`
• Maximum bet: `{SLOTS_MAX_BET}{CURRENCY_SYMBOL}`
• Match 3 of the same emoji to win
• 3 winning lines = JACKPOT! (x{JACKPOT_MULTIPLIER})
• Daily bonus: `{DAILY_BONUS}{CURRENCY_SYMBOL}` every 12 hours

**Currency:** {CURRENCY_SYMBOL} ({CURRENCY_NAME})

**Join our group:** {GROUP_NAME}
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def set_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setadmin [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ **Only owner can use this command!**", parse_mode=ParseMode.MARKDOWN)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: `/setadmin [user_id]`", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            return

        db.get_or_create_user(target_id)
        if db.set_admin(target_id, True):
            await update.message.reply_text(
                f"✅ **Admin Added!**\n\n"
                f"User `{target_id}` is now admin\n"
                f"• Unlimited bets\n"
                f"• Can grant balance",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Failed to add admin!", parse_mode=ParseMode.MARKDOWN)

    async def grant_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grant [user_id] [amount] command - OWNER & ADMIN"""
        user = update.effective_user
        user_data = db.get_or_create_user(user.id, user.username, user.first_name)

        # Check if owner or admin
        is_owner = user.id == OWNER_ID
        is_admin = db.is_admin_user(user.id)

        if not (is_owner or is_admin):
            await update.message.reply_text("❌ **Only owner and admins can grant balance!**", parse_mode=ParseMode.MARKDOWN)
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: `/grant [user_id] [amount]`\n"
                "Example: `/grant 123456789 1000`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        try:
            target_id = int(context.args[0])
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid format! Use: `/grant [user_id] [amount]`", parse_mode=ParseMode.MARKDOWN)
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0!", parse_mode=ParseMode.MARKDOWN)
            return

        # Grant balance
        db.get_or_create_user(target_id)
        new_balance = db.grant_balance(target_id, amount)

        grant_type = "🔑 **Owner**" if is_owner else "🛡️ **Admin**"
        await update.message.reply_text(
            f"{grant_type} **Granted Balance**\n\n"
            f"To: User `{target_id}`\n"
            f"Amount: `{amount}{CURRENCY_SYMBOL}`\n"
            f"New Balance: `{new_balance}{CURRENCY_SYMBOL}`",
            parse_mode=ParseMode.MARKDOWN
        )

    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ **Only owner can ban users!**", parse_mode=ParseMode.MARKDOWN)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: `/ban [user_id]`", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            return

        db.ban_user(target_id, True)
        await update.message.reply_text(
            f"🚫 **User Banned**\n\n"
            f"User `{target_id}` has been banned",
            parse_mode=ParseMode.MARKDOWN
        )

    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ **Only owner can unban users!**", parse_mode=ParseMode.MARKDOWN)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: `/unban [user_id]`", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.MARKDOWN)
            return

        db.ban_user(target_id, False)
        await update.message.reply_text(
            f"✅ **User Unbanned**\n\n"
            f"User `{target_id}` has been unbanned",
            parse_mode=ParseMode.MARKDOWN
        )

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - Show admin panel"""
        user = update.effective_user
        is_owner = user.id == OWNER_ID
        is_admin = db.is_admin_user(user.id)

        if not (is_owner or is_admin):
            await update.message.reply_text("❌ **Not authorized!**", parse_mode=ParseMode.MARKDOWN)
            return

        admin_text = f"""
╔══════════════════════════════════════╗
║ 🛡️ **ADMIN PANEL** 🛡️
╚══════════════════════════════════════╝

"""
        if is_owner:
            admin_text += """**🔑 OWNER COMMANDS:**
• `/setadmin [user_id]` - Make user admin
• `/ban [user_id]` - Ban player
• `/unban [user_id]` - Unban player
• `/grant [user_id] [amount]` - Give balance
• Unlimited bets, no restrictions

"""

        admin_text += """**🛡️ ADMIN COMMANDS:**
• `/grant [user_id] [amount]` - Give balance
• Unlimited bets, no restrictions

**📊 STATS:**
"""
        stats = db.get_stats(user.id)
        if stats:
            admin_text += f"• Balance: `{stats['balance']}{CURRENCY_SYMBOL}`\n"
            admin_text += f"• Total Wins: `{stats['total_winnings']}{CURRENCY_SYMBOL}`\n"
            admin_text += f"• Total Losses: `{stats['total_losses']}{CURRENCY_SYMBOL}`\n"

        await update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)

    def setup(self):
        """Initialize the bot synchronously (register handlers)."""
        self.app = Application.builder().token(self.token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("balance", self.balance))
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard))
        self.app.add_handler(CommandHandler("bonus", self.bonus))
        self.app.add_handler(CommandHandler("slots", self.slots_command))
        self.app.add_handler(CommandHandler("send", self.send_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        # Owner & Admin commands
        self.app.add_handler(CommandHandler("admin", self.admin_panel))
        self.app.add_handler(CommandHandler("setadmin", self.set_admin_command))
        self.app.add_handler(CommandHandler("grant", self.grant_command))
        self.app.add_handler(CommandHandler("ban", self.ban_command))
        self.app.add_handler(CommandHandler("unban", self.unban_command))

        logger.info("Bot setup complete!")

    def run(self):
        """Start the bot (synchronous run for Application.run_polling)

        Uses Application.run_polling() which manages lifecycle correctly
        for python-telegram-bot v20.x on hosting platforms like Koyeb.
        """
        # Ensure setup (handler registration) is completed
        self.setup()

        # Run polling (blocking) which handles initialize/start/stop lifecycle
        logger.info("🎮 AXL GAME BOT is starting (run_polling)...")
        self.app.run_polling()


if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not found in environment variables!")
        exit(1)

    bot = AXLGameBot(TELEGRAM_TOKEN)

    bot.run()
