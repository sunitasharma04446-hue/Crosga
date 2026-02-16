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
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode, ChatAction
from pymongo import MongoClient, ReturnDocument

from config import *

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

    async def _create_or_get_user(self, user_id: int, username: str = None, first_name: str = None):
        """Create or get user from MongoDB"""
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _work():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": user_id}
            doc = users_col.find_one(query)
            if not doc:
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": user_id,
                    "username": username,
                    "first_name": first_name,
                    "economy": {"balance": 500.0},
                    "is_admin": False,
                    "is_banned": False,
                    "last_bonus_time": 0,
                    "total_winnings": 0,
                    "total_losses": 0,
                    "games_played": 0
                })
                doc = users_col.find_one(query)
            client.close()
            return doc
        
        return await asyncio.to_thread(_work)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        await self._create_or_get_user(user.id, user.username, user.first_name)

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
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user = update.effective_user
        user_data = await self._create_or_get_user(user.id, user.username, user.first_name)

        balance = user_data.get('economy', {}).get('balance', 0)
        winnings = user_data.get('total_winnings', 0)
        losses = user_data.get('total_losses', 0)
        games = user_data.get('games_played', 0)

        balance_text = f"""
<b>💳 YOUR BALANCE 💳</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Balance:</b> <code>{int(balance)}{html.escape(CURRENCY_SYMBOL)}</code>
<b>Total Wins:</b> <code>{int(winnings)}{html.escape(CURRENCY_SYMBOL)}</code>
<b>Total Losses:</b> <code>{int(losses)}{html.escape(CURRENCY_SYMBOL)}</code>
<b>Games Played:</b> <code>{games}</code>
"""
        await update.message.reply_text(balance_text, parse_mode=ParseMode.HTML)

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
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _check_and_grant():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": user.id}
            doc = users_col.find_one(query)
            if not doc:
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "economy": {"balance": 500.0},
                    "last_bonus_time": 0
                })
                doc = users_col.find_one(query)
            
            current_time = int(datetime.now().timestamp())
            last_bonus = doc.get('last_bonus_time', 0)
            time_remaining = BONUS_COOLDOWN - (current_time - last_bonus)
            
            if time_remaining > 0:
                client.close()
                return None, time_remaining
            
            # Grant bonus
            update_result = users_col.find_one_and_update(
                query,
                {"$inc": {"economy.balance": DAILY_BONUS}, "$set": {"last_bonus_time": current_time}},
                return_document=ReturnDocument.AFTER
            )
            new_balance = update_result.get('economy', {}).get('balance', 0)
            client.close()
            return new_balance, 0
        
        new_balance, time_remaining = await asyncio.to_thread(_check_and_grant)
        
        if time_remaining > 0:
            hours = time_remaining // 3600
            minutes = (time_remaining % 3600) // 60
            await update.message.reply_text(
                f"⏰ <b>Bonus Cooldown</b>\n\n"
                f"Come back in <code>{hours}h {minutes}m</code> for your next bonus!",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                f"🎁 <b>Daily Bonus Claimed!</b>\n\n"
                f"You received <code>{DAILY_BONUS}{html.escape(CURRENCY_SYMBOL)}</code>\n"
                f"New Balance: <b>{int(new_balance)}{html.escape(CURRENCY_SYMBOL)}</b>",
                parse_mode=ParseMode.HTML
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

        # Check admin/owner privileges & banned status (MongoDB check)
        is_owner = user.id == OWNER_ID
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured: MONGODB_URI is missing.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_user_status():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            client.close()
            return {
                "is_admin": doc and doc.get('is_admin', False),
                "is_banned": doc and doc.get('is_banned', False),
                "balance": doc and float(doc.get('economy', {}).get('balance', 0)) or 0.0
            } if doc else {"is_admin": False, "is_banned": False, "balance": 500.0}
        
        try:
            user_status = await asyncio.to_thread(_get_user_status)
        except Exception as e:
            await update.message.reply_text(f"❌ Database error: {str(e)}", parse_mode=ParseMode.HTML)
            return
        
        is_admin = user_status["is_admin"]
        is_banned = user_status["is_banned"]
        current_balance = user_status["balance"]
        
        # Check if banned
        if is_banned and not is_owner:
            await update.message.reply_text("🚫 <b>You are banned!</b> Contact the owner.", parse_mode=ParseMode.HTML)
            return
        
        # Check bet limits
        if not (is_owner or is_admin):
            if bet_amount < SLOTS_MIN_BET or bet_amount > SLOTS_MAX_BET:
                await update.message.reply_text(
                    f"❌ Bet must be between {SLOTS_MIN_BET}{html.escape(CURRENCY_SYMBOL)} and {SLOTS_MAX_BET}{html.escape(CURRENCY_SYMBOL)}",
                    parse_mode=ParseMode.HTML
                )
                return

        # Check if has balance
        if current_balance < bet_amount and not (is_owner or is_admin):
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {int(current_balance)}{html.escape(CURRENCY_SYMBOL)}, bet: {int(bet_amount)}{html.escape(CURRENCY_SYMBOL)}",
                parse_mode=ParseMode.HTML
            )
            return

        # Send animated dice (slot emoji) and wait for animation
        try:
            dice_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎰', reply_to_message_id=update.message.message_id)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send slot: {str(e)}", parse_mode=ParseMode.HTML)
            return

        # Wait exactly 4 seconds for animation
        await asyncio.sleep(4)

        # Get the dice value
        try:
            dice_value = dice_msg.dice.value
        except Exception as e:
            try:
                await dice_msg.reply_text("❌ Failed to read spin result.", parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text("❌ Failed to read spin result.", parse_mode=ParseMode.HTML)
            return

        # Determine result based on dice emoji value (1-64)
        if dice_value == 64:
            multiplier = 10.0
            result_type = "🎰🎰🎰 JACKPOT! 🎰🎰🎰"
        elif dice_value >= 55:
            multiplier = 5.0
            result_type = "💎 BIG WIN 💎"
        elif dice_value >= 30:
            multiplier = 3.0
            result_type = "✨ WIN ✨"
        else:
            multiplier = 0.0
            result_type = "❌ LOSS"

        # Calculate net change
        if multiplier > 0:
            profit = bet_amount * (multiplier - 1)
            net_change = profit
        else:
            net_change = -bet_amount

        # Update balance in MongoDB
        def _update_balance():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": user.id}
            
            # Try to increment
            result = users_col.update_one(query, {"$inc": {"economy.balance": net_change}}, upsert=False)
            
            # If no match, create user
            if result.matched_count == 0:
                new_balance = 500.0 + net_change
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "economy": {"balance": new_balance},
                    "is_admin": False,
                    "is_banned": False
                })
            
            # Fetch final balance
            doc = users_col.find_one(query)
            final_balance = float(doc.get("economy", {}).get("balance", 0)) if doc else 500.0
            client.close()
            return final_balance
        
        try:
            new_balance = await asyncio.to_thread(_update_balance)
        except Exception as e:
            try:
                await dice_msg.reply_text(f"❌ Balance update failed: {str(e)}", parse_mode=ParseMode.HTML)
            except:
                await update.message.reply_text(f"❌ Balance update failed: {str(e)}", parse_mode=ParseMode.HTML)
            return

        # Build result message
        user_name = html.escape(user.first_name or user.username or str(user.id))
        
        if multiplier > 0:
            profit_text = int(net_change) if net_change == int(net_change) else f"{net_change:.2f}"
            change_display = f"<code>+{profit_text}{html.escape(CURRENCY_SYMBOL)}</code>"
        else:
            change_display = f"<code>-{int(bet_amount)}{html.escape(CURRENCY_SYMBOL)}</code>"
        
        details = (
            f"<b>🎰 Slot Result</b>\n\n"
            f"Player: <b>{user_name}</b>\n"
            f"Status: <b>{result_type}</b>\n"
            f"Dice: {dice_value}/64\n"
            f"Change: {change_display}\n"
            f"New Balance: <b>{int(new_balance)}{html.escape(CURRENCY_SYMBOL)}</b>"
        )

        # Build keyboard
        keyboard = [
            [InlineKeyboardButton("Play Again 🎰", callback_data=f"slots_play_{int(bet_amount)}")],
            [InlineKeyboardButton("💳 Balance", callback_data="balance"), InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send result
        try:
            await dice_msg.reply_text(details, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            try:
                await update.message.reply_text(details, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            except Exception as e:
                try:
                    await update.message.reply_text(f"Result: {result_type} | Change: {change_display} | New Balance: {int(new_balance)}{html.escape(CURRENCY_SYMBOL)}", parse_mode=ParseMode.HTML)
                except:
                    pass

    async def send_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /send [amount] command"""
        user = update.effective_user

        if not update.message.reply_to_message:
            await update.message.reply_text(
                f"🤝 <b>Usage:</b> Reply to someone's message with <code>/send [amount]</code>\n\n"
                f"Example: Reply and type <code>/send 100</code>",
                parse_mode=ParseMode.HTML
            )
            return

        target_user = update.message.reply_to_message.from_user
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                f"❌ Please specify amount: <code>/send [amount]</code>",
                parse_mode=ParseMode.HTML
            )
            return

        try:
            amount = float(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!", parse_mode=ParseMode.HTML)
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0!", parse_mode=ParseMode.HTML)
            return

        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _transfer():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            sender_query = {"appId": APP_ID, "userId": user.id}
            sender_doc = users_col.find_one(sender_query)
            if not sender_doc:
                client.close()
                return None, None
            
            sender_balance = sender_doc.get('economy', {}).get('balance', 0)
            if sender_balance < amount:
                client.close()
                return sender_balance, None
            
            # Perform transfer - deduct from sender
            users_col.update_one(sender_query, {"$inc": {"economy.balance": -amount}})
            sender_updated = users_col.find_one(sender_query)
            new_sender_balance = sender_updated.get('economy', {}).get('balance', 0)
            
            # Add to target - try increment first
            target_query = {"appId": APP_ID, "userId": target_user.id}
            result = users_col.update_one(target_query, {"$inc": {"economy.balance": amount}}, upsert=False)
            
            # If target doesn't exist, create them
            if result.matched_count == 0:
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": target_user.id,
                    "username": target_user.username,
                    "first_name": target_user.first_name,
                    "economy": {"balance": amount},
                    "is_admin": False,
                    "is_banned": False
                })
            
            client.close()
            return new_sender_balance, True
        
        new_balance, success = await asyncio.to_thread(_transfer)
        
        if success is None:
            await update.message.reply_text("❌ Could not find your account.", parse_mode=ParseMode.HTML)
            return
        
        if success is None or (isinstance(success, bool) and not success):
            if new_balance is not None:
                await update.message.reply_text(
                    f"❌ <b>Insufficient balance!</b>\n\n"
                    f"You need: <code>{int(amount)}{html.escape(CURRENCY_SYMBOL)}</code>\n"
                    f"You have: <code>{int(new_balance)}{html.escape(CURRENCY_SYMBOL)}</code>",
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_text("❌ Transfer failed!", parse_mode=ParseMode.HTML)
            return

        target_name = target_user.username or target_user.first_name or f"User {target_user.id}"
        await update.message.reply_text(
            f"✅ <b>Transfer Successful!</b>\n\n"
            f"Sent: <code>{int(amount)}{html.escape(CURRENCY_SYMBOL)}</code> to <b>@{html.escape(target_name)}</b>\n"
            f"Your New Balance: <b>{int(new_balance)}{html.escape(CURRENCY_SYMBOL)}</b>",
            parse_mode=ParseMode.HTML
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = f"""
<b>📖 {BOT_NAME} - Help 📖</b>

<b>Available Commands:</b>

🎮 /start - Start the bot
💰 /balance - Check your balance
🏆 /leaderboard - View top players
🎰 /slots [amount] - Play slots game
🎁 /bonus - Get daily bonus (every 12 hours)
🤝 /send [amount] - Send {html.escape(CURRENCY_SYMBOL)} to others

<b>Game Rules:</b>
• Minimum bet: <code>{SLOTS_MIN_BET}{html.escape(CURRENCY_SYMBOL)}</code>
• Maximum bet: <code>{SLOTS_MAX_BET}{html.escape(CURRENCY_SYMBOL)}</code>
• 🎰 value 64 = <b>JACKPOT!</b> (×{int(JACKPOT_MULTIPLIER)})
• 🎰 value 1, 22, 43 = <b>WIN!</b> (×3)
• Other values = Loss
• Daily bonus: <code>{DAILY_BONUS}{html.escape(CURRENCY_SYMBOL)}</code> every 12 hours

<b>Currency:</b> {html.escape(CURRENCY_SYMBOL)} ({CURRENCY_NAME})

<b>Join our group:</b> {GROUP_NAME}
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

    async def set_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setadmin [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ <b>Only owner can use this command!</b>", parse_mode=ParseMode.HTML)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: <code>/setadmin [user_id]</code>", parse_mode=ParseMode.HTML)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.HTML)
            return

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _set_admin():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": target_id}
            users_col.update_one(query, {"$set": {"is_admin": True}}, upsert=True)
            client.close()
            return True
        
        await asyncio.to_thread(_set_admin)
        await update.message.reply_text(
            f"✅ <b>Admin Added!</b>\n\n"
            f"User <code>{target_id}</code> is now admin\n"
            f"• Unlimited bets\n"
            f"• Can grant balance",
            parse_mode=ParseMode.HTML
        )

    async def grant_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grant [user_id] [amount] command - OWNER & ADMIN"""
        user = update.effective_user
        
        # Check if owner or admin
        is_owner = user.id == OWNER_ID
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _is_admin():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            client.close()
            return doc and doc.get('is_admin', False) if doc else False
        
        is_admin = await asyncio.to_thread(_is_admin)
        
        if not (is_owner or is_admin):
            await update.message.reply_text("❌ <b>Only owner and admins can grant balance!</b>", parse_mode=ParseMode.HTML)
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: <code>/grant [user_id] [amount]</code>\n"
                "Example: <code>/grant 123456789 1000</code>",
                parse_mode=ParseMode.HTML
            )
            return

        try:
            target_id = int(context.args[0])
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid format! Use: <code>/grant [user_id] [amount]</code>", parse_mode=ParseMode.HTML)
            return

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0!", parse_mode=ParseMode.HTML)
            return

        # Grant balance
        def _grant():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": target_id}
            
            # Try to increment first
            result = users_col.update_one(query, {"$inc": {"economy.balance": amount}}, upsert=False)
            
            # If no document, create it
            if result.matched_count == 0:
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": target_id,
                    "economy": {"balance": amount},
                    "is_admin": False,
                    "is_banned": False
                })
            
            # Fetch and return final balance
            doc = users_col.find_one(query)
            new_balance = doc.get('economy', {}).get('balance', 0) if doc else 0
            client.close()
            return new_balance
        
        new_balance = await asyncio.to_thread(_grant)
        
        grant_type = "🔑 <b>Owner</b>" if is_owner else "🛡️ <b>Admin</b>"
        await update.message.reply_text(
            f"{grant_type} <b>Granted Balance</b>\n\n"
            f"To: User <code>{target_id}</code>\n"
            f"Amount: <code>{int(amount)}{html.escape(CURRENCY_SYMBOL)}</code>\n"
            f"New Balance: <code>{int(new_balance)}{html.escape(CURRENCY_SYMBOL)}</code>",
            parse_mode=ParseMode.HTML
        )

    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ <b>Only owner can ban users!</b>", parse_mode=ParseMode.HTML)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: <code>/ban [user_id]</code>", parse_mode=ParseMode.HTML)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.HTML)
            return

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _ban():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            users_col.update_one({"appId": APP_ID, "userId": target_id}, {"$set": {"is_banned": True}}, upsert=True)
            client.close()
        
        await asyncio.to_thread(_ban)
        await update.message.reply_text(
            f"🚫 <b>User Banned</b>\n\n"
            f"User <code>{target_id}</code> has been banned",
            parse_mode=ParseMode.HTML
        )

    async def unban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unban [user_id] command - OWNER ONLY"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ <b>Only owner can unban users!</b>", parse_mode=ParseMode.HTML)
            return

        if not context.args or len(context.args) == 0:
            await update.message.reply_text("❌ Usage: <code>/unban [user_id]</code>", parse_mode=ParseMode.HTML)
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!", parse_mode=ParseMode.HTML)
            return

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _unban():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            users_col.update_one({"appId": APP_ID, "userId": target_id}, {"$set": {"is_banned": False}}, upsert=True)
            client.close()
        
        await asyncio.to_thread(_unban)
        await update.message.reply_text(
            f"✅ <b>User Unbanned</b>\n\n"
            f"User <code>{target_id}</code> has been unbanned",
            parse_mode=ParseMode.HTML
        )

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - Show admin panel"""
        user = update.effective_user
        is_owner = user.id == OWNER_ID
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_user():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            client.close()
            return doc
        
        user_doc = await asyncio.to_thread(_get_user)
        is_admin = user_doc and user_doc.get('is_admin', False) if user_doc else False
        
        if not (is_owner or is_admin):
            await update.message.reply_text("❌ <b>Not authorized!</b>", parse_mode=ParseMode.HTML)
            return

        admin_text = f"<b>🛡️ ADMIN PANEL 🛡️</b>\n\n"
        
        if is_owner:
            admin_text += """<b>🔑 OWNER COMMANDS:</b>
• /setadmin [user_id] - Make user admin
• /ban [user_id] - Ban player
• /unban [user_id] - Unban player
• /grant [user_id] [amount] - Give balance
• Unlimited bets, no restrictions

"""

        admin_text += """<b>🛡️ ADMIN COMMANDS:</b>
• /grant [user_id] [amount] - Give balance
• Unlimited bets, no restrictions

<b>📊 YOUR STATS:</b>
"""
        if user_doc:
            balance = user_doc.get('economy', {}).get('balance', 0)
            wins = user_doc.get('total_winnings', 0)
            losses = user_doc.get('total_losses', 0)
            admin_text += f"• Balance: <code>{int(balance)}{html.escape(CURRENCY_SYMBOL)}</code>\n"
            admin_text += f"• Total Wins: <code>{int(wins)}{html.escape(CURRENCY_SYMBOL)}</code>\n"
            admin_text += f"• Total Losses: <code>{int(losses)}{html.escape(CURRENCY_SYMBOL)}</code>\n"

        await update.message.reply_text(admin_text, parse_mode=ParseMode.HTML)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button clicks"""
        query = update.callback_query
        await query.answer()  # Delete loading state immediately
        
        if query.data == "balance":
            await self.balance(update, context)
        elif query.data == "leaderboard":
            await self.leaderboard(update, context)
        elif query.data == "bonus":
            await self.bonus(update, context)
        elif query.data == "slots_menu":
            await query.edit_message_text(
                text="🎰 <b>Slots Game</b>\n\nUse: <code>/slots [amount]</code>\n\nExample: <code>/slots 100</code>",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "send_menu":
            await query.edit_message_text(
                text="🤝 <b>Send Balance</b>\n\nReply to someone's message with: <code>/send [amount]</code>",
                parse_mode=ParseMode.HTML
            )
        elif query.data.startswith("slots_play_"):
            try:
                amount = float(query.data.split("_")[2])
                # Create fake update to call slots_command
                context.args = [str(int(amount)) if amount == int(amount) else str(amount)]
                await self.slots_command(update, context)
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {str(e)}", parse_mode=ParseMode.HTML)

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

        # Button/Callback handlers (must be registered)
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

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
