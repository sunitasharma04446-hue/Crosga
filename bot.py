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
                # Auto-set owner/admin
                is_admin = user_id == OWNER_ID
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": user_id,
                    "username": username,
                    "first_name": first_name,
                    "economy": {"balance": 500.0},
                    "is_admin": is_admin,  # Auto-admin if owner
                    "is_banned": False,
                    "last_bonus_time": 0,
                    "total_winnings": 0,
                    "total_losses": 0,
                    "games_played": 0,
                    "xp": 0
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
            [InlineKeyboardButton("🎰 Slots", callback_data='slots_menu'),
             InlineKeyboardButton("🪙 Coin Flip", callback_data='bet_menu'),
             InlineKeyboardButton("💰 Balance", callback_data='balance')],
            [InlineKeyboardButton("🏆 Top Balance", callback_data='leaderboard'),
             InlineKeyboardButton("🏅 Top XP", callback_data='top'),
             InlineKeyboardButton("🎁 Bonus", callback_data='bonus')],
            [InlineKeyboardButton("ℹ️ Help", callback_data='help_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome = f"""
╔══════════════════════════════╗
║    🎮 AXL GAME BOT 🎮        ║
║      Casino Gaming Fun       ║
╚══════════════════════════════╝

👋 Welcome <b>{html.escape(user.first_name or user.username or 'Player')}</b>!

<b>💎 Your Gateway to Riches 💎</b>
Play slots • Flip coins • Earn XP • Climb ranks

<b>🚀 Quick Start:</b>
• Tap a button below
• Or use /slots, /bet, /balance, /help

<b>🎯 Ready to play?</b>
"""
        await update.message.reply_text(
            welcome,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user = update.effective_user
        user_data = await self._create_or_get_user(user.id, user.username, user.first_name)

        balance = user_data.get('economy', {}).get('balance', 0)
        xp = user_data.get('xp', 0)
        games = user_data.get('games_played', 0)
        
        is_owner = user.id == OWNER_ID

        balance_text = f"""
╔═══════════════════════════╗
║   💳 YOUR ACCOUNT 💳      ║
╚═══════════════════════════╝

💰 <b>Balance:</b> <code>{int(balance)} ∆</code>
⚡ <b>XP:</b> <code>{int(xp)}</code>
🎮 <b>Games:</b> <code>{games}</code>
{f'👑 <b>Role:</b> <code>OWNER</code>' if is_owner else ''}

<b>🎯 Keep playing to earn more ∆!</b>
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

    async def coin_flip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /bet [amount] [heads/tails] command - Coin Flip"""
        import random
        user = update.effective_user

        if not context.args or len(context.args) < 2:
            await update.message.reply_text("🪙 Usage: /bet <amount> <heads|tails>\nExample: /bet 100 heads", parse_mode=ParseMode.HTML)
            return

        try:
            bet_amount = float(context.args[0])
            choice = context.args[1].lower()
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid format!", parse_mode=ParseMode.HTML)
            return

        if bet_amount <= 0 or choice not in ["heads", "tails"]:
            await update.message.reply_text("❌ Invalid amount or choice!", parse_mode=ParseMode.HTML)
            return

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ DB error", parse_mode=ParseMode.HTML)
            return

        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        is_owner = user.id == OWNER_ID

        # Check user & balance FAST
        def _check():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            client.close()
            return doc if doc else {"economy": {"balance": 500.0}, "is_banned": False}

        user_doc = await asyncio.to_thread(_check)
        balance = float(user_doc.get("economy", {}).get("balance", 0))
        
        if user_doc.get("is_banned", False) and not is_owner:
            await update.message.reply_text("🚫 Banned!", parse_mode=ParseMode.HTML)
            return

        if not (is_owner or balance >= bet_amount):
            await update.message.reply_text(f"❌ Balance: {int(balance)}{html.escape(CURRENCY_SYMBOL)}", parse_mode=ParseMode.HTML)
            return

        # Flip coin
        result = random.choice(["heads", "tails"])
        won = result == choice
        
        # Update balance & XP FAST
        xp_gain = COIN_FLIP_WIN_XP if won else COIN_FLIP_LOSS_XP
        balance_change = bet_amount * COIN_FLIP_MULTIPLIER if won else -bet_amount

        def _update():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": user.id}
            
            result = users_col.update_one(query, {"$inc": {"economy.balance": balance_change, "xp": xp_gain, "games_played": 1}}, upsert=False)
            if result.matched_count == 0:
                users_col.insert_one({"appId": APP_ID, "userId": user.id, "username": user.username, "first_name": user.first_name, "economy": {"balance": 500.0 + balance_change}, "xp": xp_gain, "games_played": 1, "is_admin": False, "is_banned": False})
            
            doc = users_col.find_one(query)
            return float(doc.get("economy", {}).get("balance", 0)) if doc else 500.0

        new_bal = await asyncio.to_thread(_update)

        # Result message - ULTRA DETAILED & BEAUTIFUL (matching slots format)
        result_emoji = "🎉" if won else "😢"
        
        if won:
            change_text = f"✅ +{int(balance_change):,} 🪙"
        else:
            change_text = f"❌ -{int(bet_amount):,} 🪙"
        
        msg = f"""<b>{result_emoji} {'WIN!' if won else 'LOSS'}</b>

🪙 <b>Your Choice:</b> <code>{choice.upper()}</code>
🎲 <b>Flip Result:</b> <code>{result.upper()}</code>
💰 <b>Won:</b> {change_text}
📈 <b>+{int(xp_gain)} XP</b>
💳 <b>New Balance:</b> <code>{int(new_bal):,} 🪙</code>"""
        
        try:
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        except Exception:
            await update.message.reply_text(f"{result_emoji} {'WIN!' if won else 'LOSS'} | {change_text} | Balance: {int(new_bal):,} 🪙", parse_mode=ParseMode.HTML)

    async def top_xp(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /top command - Show top XP players"""
        await update.message.chat.send_action(ChatAction.TYPING)

        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ DB error", parse_mode=ParseMode.HTML)
            return

        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"

        def _get_top():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            cursor = users_col.find({"appId": APP_ID}).sort([("xp", -1)]).limit(10)
            results = list(cursor)
            client.close()
            return results

        top_players = await asyncio.to_thread(_get_top)

        msg = "<b>🏆 TOP 10 XP PLAYERS</b>\n\n"
        for idx, player in enumerate(top_players, 1):
            emoji = ["🥇", "🥈", "🥉"][idx-1] if idx <= 3 else f"{idx}️⃣"
            name = player.get('username') or player.get('first_name') or "User"
            xp = int(player.get('xp', 0))
            bal = int(player.get('economy', {}).get('balance', 0))
            msg += f"{emoji} {html.escape(name[:15])}: <code>{xp} XP | {bal}{html.escape(CURRENCY_SYMBOL)}</code>\n"

        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

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

        # Send animated dice (slot emoji) - INSTANT RESULT (NO WAIT)
        try:
            dice_msg = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎰', reply_to_message_id=update.message.message_id)
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to send slot: {str(e)}", parse_mode=ParseMode.HTML)
            return

        # Mini delay for dice animation completion (telegram requirement - minimal)
        await asyncio.sleep(0.5)

        # Get the dice value
        try:
            dice_value = dice_msg.dice.value
        except Exception as e:
            await update.message.reply_text("❌ Failed to read spin result.", parse_mode=ParseMode.HTML)
            return

        # Determine result based on dice emoji value (1-64) - WITH ADMIN/OWNER BOOST
        # ADMIN/OWNER get 3x better odds!
        boost = 3 if (is_admin or is_owner) else 1
        boosted_value = min(64, dice_value * boost)  # Cap at 64 for fairness
        
        if boosted_value == 64 or dice_value == 64:
            multiplier = 10.0
            result_type = "🎰 JACKPOT 🎰"
            xp_gain = SLOTS_WIN_XP * 2
        elif boosted_value >= 48:  # 48-64 = BIG WINS
            multiplier = 5.0
            result_type = "💎 BIG WIN"
            xp_gain = int(SLOTS_WIN_XP * 1.5)
        elif boosted_value >= 20:  # 20-47 = REGULAR WINS
            multiplier = 2.5
            result_type = "✨ WIN"
            xp_gain = SLOTS_WIN_XP
        elif boosted_value >= 10:  # 10-19 = SMALL WINS for admin/owner
            multiplier = 1.5
            result_type = "🎉 WIN!"
            xp_gain = int(SLOTS_WIN_XP * 0.5)
        else:  # LOSS extremely rare for admin/owner
            multiplier = 0.0
            result_type = "❌ LOSS"
            xp_gain = SLOTS_LOSS_XP

        # Calculate net change
        if multiplier > 0:
            profit = bet_amount * (multiplier - 1)
            net_change = profit
        else:
            net_change = -bet_amount

        # Update balance in MongoDB (with XP)
        def _update_balance():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query = {"appId": APP_ID, "userId": user.id}
            
            # Try to increment balance AND xp
            result = users_col.update_one(query, {"$inc": {"economy.balance": net_change, "xp": xp_gain, "games_played": 1}}, upsert=False)
            
            # If no match, create user
            if result.matched_count == 0:
                new_balance = 500.0 + net_change
                users_col.insert_one({
                    "appId": APP_ID,
                    "userId": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "economy": {"balance": new_balance},
                    "xp": xp_gain,
                    "games_played": 1,
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

        # Build result message - ULTRA DETAILED & BEAUTIFUL
        if multiplier > 0:
            result_emoji = "🎉"
            change_text = f"✅ +{int(net_change):,} 🪙"
            won_text = "YES"
        else:
            result_emoji = "😢"
            change_text = f"❌ -{int(bet_amount):,} 🪙"
            won_text = "NO"
        
        # DETAILED MESSAGE WITH ALL INFO
        details = f"""<b>{result_emoji} {result_type}</b>

🎰 <b>Slot Value:</b> <code>{dice_value}</code>
🎯 <b>Multiplier:</b> <code>{multiplier}x</code>
💰 <b>Won:</b> {change_text}
📈 <b>+{int(xp_gain)} XP</b>
💳 <b>New Balance:</b> <code>{int(new_balance):,} 🪙</code>"""

        # Add admin boost indicator
        if is_admin or is_owner:
            details += f"\n\n👑 <b>ADMIN BOOST ACTIVE</b> (+3x odds)"

        # Send result with instant reply
        try:
            await dice_msg.reply_text(details, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await update.message.reply_text(details, parse_mode=ParseMode.HTML)
            except Exception as e:
                await update.message.reply_text(f"{result_emoji} {result_type}\n{change_text}\nBalance: {int(new_balance):,} 🪙", parse_mode=ParseMode.HTML)

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
        """Handle /help command - Beautiful help"""
        help_text = f"""<b>🎮 {BOT_NAME} - COMPLETE GUIDE</b>

<b>╔════════════════════════════╗</b>
<b>║   🎯 MAIN GAMES & FEATURES  ║</b>
<b>╚════════════════════════════╝</b>

<b>🎰 SLOTS GAME:</b>
• Command: <code>/slots [amount]</code>
• Min: 10 ∆ | Max: 10,000 ∆
• Wins: 2.5x - 10x multipliers
• Example: <code>/slots 100</code>

<b>🪙 COIN FLIP:</b>
• Command: <code>/bet [amount] [heads/tails]</code>
• Min: 10 ∆ | Max: 10,000 ∆
• Win: 2x multiplier
• Example: <code>/bet 100 heads</code>

<b>💎 ACCOUNT FEATURES:</b>
• <code>/balance</code> - Your balance & XP
• <code>/bonus</code> - Daily 100 ∆ (12h cooldown)
• <code>/send [@user] [amount]</code> - Send balance
• <code>/top</code> - Top 10 XP players
• <code>/leaderboard</code> - Top 100 by balance

<b>⚡ XP SYSTEM:</b>
• Slots Win: +100 XP
• Slots Loss: +20 XP
• Coin Flip Win: +60 XP
• Coin Flip Loss: +10 XP

<b>👑 OWNER/ADMIN:</b>
• <code>/owner</code> - Owner panel
• <code>/admin</code> - Admin panel
• <code>/setadmin [id]</code> - Make admin
• <code>/grant [id] [amt]</code> - Give balance
• <code>/ban [id]</code> - Ban player
• <code>/unban [id]</code> - Unban player

<b>💡 TIPS:</b>
✓ Play games to earn XP & climb /top
✓ Buttons on /start for quick access
✓ Use /balance to check status anytime
✓ Daily bonus every 12 hours!

{GROUP_NAME}
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

    async def owner_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /owner command - Show owner-only panel"""
        user = update.effective_user
        
        # Check if user is owner
        if user.id != OWNER_ID:
            await update.message.reply_text(
                "❌ <b>Not authorized!</b>\n\n"
                "This command is reserved for the bot owner only.",
                parse_mode=ParseMode.HTML
            )
            return
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        if not MONGODB_URI:
            await update.message.reply_text("❌ Server not configured.", parse_mode=ParseMode.HTML)
            return
        
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_stats():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            total_users = users_col.count_documents({"appId": APP_ID})
            admins = users_col.count_documents({"appId": APP_ID, "is_admin": True})
            banned = users_col.count_documents({"appId": APP_ID, "is_banned": True})
            
            # Get total economy
            pipeline = [
                {"$match": {"appId": APP_ID}},
                {"$group": {
                    "_id": None,
                    "total_balance": {"$sum": "$economy.balance"},
                    "total_xp": {"$sum": "$xp"}
                }}
            ]
            stats = list(users_col.aggregate(pipeline))
            total_balance = stats[0]["total_balance"] if stats else 0
            total_xp = stats[0]["total_xp"] if stats else 0
            
            owner_doc = users_col.find_one({"appId": APP_ID, "userId": OWNER_ID})
            owner_balance = owner_doc.get('economy', {}).get('balance', 0) if owner_doc else 0
            
            client.close()
            return total_users, admins, banned, total_balance, total_xp, owner_balance
        
        stats = await asyncio.to_thread(_get_stats)
        total_users, admins, banned, total_balance, total_xp, owner_balance = stats
        
        owner_text = f"""╔═══════════════════════════════╗
║      👑 OWNER PANEL 👑       ║
║   Bot Owner Control Center   ║
╚═══════════════════════════════╝

<b>📊 BOT STATISTICS:</b>
👥 Total Players: <code>{total_users}</code>
🛡️  Admins: <code>{admins}</code>
🚫 Banned: <code>{banned}</code>
💰 Total Economy: <code>{int(total_balance):,} {html.escape(CURRENCY_SYMBOL)}</code>
⚡ Total XP: <code>{int(total_xp):,}</code>

<b>🏆 YOUR ACCOUNT:</b>
💳 Balance: <code>{int(owner_balance):,} {html.escape(CURRENCY_SYMBOL)}</code>
🎯 Status: <b>OWNER - Unlimited Bets</b>

<b>🔑 OWNER COMMANDS:</b>
• <code>/setadmin [user_id]</code> - Promote admin
• <code>/ban [user_id]</code> - Ban player
• <code>/unban [user_id]</code> - Unban player
• <code>/grant [user_id] [amount]</code> - Give balance
• Full control, no restrictions

<b>💡 TIPS:</b>
✓ You have unlimited daily bets
✓ Use /grant to add balance to players
✓ Admins get unlimited bets too
✓ All commands work instantly
"""
        
        await update.message.reply_text(owner_text, parse_mode=ParseMode.HTML)

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

    async def _show_leaderboard(self, update: Update, query):
        """Show leaderboard from button callback"""
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_leaderboard():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            players = list(users_col.find({"appId": APP_ID}).sort("economy.balance", -1).limit(100))
            client.close()
            return players
        
        try:
            players = await asyncio.to_thread(_get_leaderboard)
            msg = "🏆 <b>TOP 100 BALANCE</b>\n\n"
            for i, player in enumerate(players[:100], 1):
                name = html.escape(player.get('username', f"User{player['userId']}")[:15])
                bal = int(player.get('economy', {}).get('balance', 0))
                emoji = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
                msg += f"{emoji} {name}: <code>{bal:,} ∆</code>\n"
            
            await query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.edit_message_text(f"❌ Error loading leaderboard: {str(e)}", parse_mode=ParseMode.HTML)
    
    async def _show_top_xp(self, update: Update, query):
        """Show top XP leaderboard from button callback"""
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_top():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            players = list(users_col.find({"appId": APP_ID}).sort("xp", -1).limit(10))
            client.close()
            return players
        
        try:
            players = await asyncio.to_thread(_get_top)
            msg = "🏅 <b>TOP 10 BY XP</b>\n\n"
            for i, player in enumerate(players, 1):
                name = html.escape(player.get('username', f"User{player['userId']}")[:15])
                xp = int(player.get('xp', 0))
                bal = int(player.get('economy', {}).get('balance', 0))
                emoji = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
                msg += f"{emoji} {name}: <code>{xp:,} XP | {bal:,} ∆</code>\n"
            
            await query.edit_message_text(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.edit_message_text(f"❌ Error loading top XP: {str(e)}", parse_mode=ParseMode.HTML)
    
    async def _claim_bonus(self, update: Update, query):
        """Claim bonus from button callback"""
        user = update.effective_user
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _check_and_grant():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            query_doc = {"appId": APP_ID, "userId": user.id}
            doc = users_col.find_one(query_doc)
            
            current_time = int(datetime.now().timestamp())
            last_bonus = doc.get('last_bonus_time', 0) if doc else 0
            time_remaining = BONUS_COOLDOWN - (current_time - last_bonus)
            
            if time_remaining > 0:
                client.close()
                return None, time_remaining
            
            # Grant bonus
            update_result = users_col.find_one_and_update(
                query_doc,
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
            await query.edit_message_text(
                f"⏰ <b>Bonus Cooldown</b>\n\n"
                f"Come back in <code>{hours}h {minutes}m</code>!",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.edit_message_text(
                f"🎁 <b>BONUS CLAIMED!</b>\n\n"
                f"✅ +{DAILY_BONUS} ∆\n"
                f"💰 Balance: <code>{int(new_balance):,} ∆</code>",
                parse_mode=ParseMode.HTML
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks from /start command only"""
        query = update.callback_query
        await query.answer()
        
        # /start buttons
        if query.data == "slots_menu":
            await query.edit_message_text(
                text="🎰 <b>SLOTS GAME</b>\n\n"
                     "💎 <b>Win Big!</b>\n"
                     "Use: <code>/slots [amount]</code>\n\n"
                     "Example: <code>/slots 100</code>\n"
                     "Min: 10 ∆ | Max: 10,000 ∆",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "bet_menu":
            await query.edit_message_text(
                text="🪙 <b>COIN FLIP</b>\n\n"
                     "Choose heads or tails!\n"
                     "Use: <code>/bet [amount] [heads|tails]</code>\n\n"
                     "Example: <code>/bet 100 heads</code>\n"
                     "Min: 10 ∆ | Max: 10,000 ∆ | Win: 2x",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "balance":
            # Call balance command
            user = update.effective_user
            user_data = await self._create_or_get_user(user.id, user.username, user.first_name)
            balance = user_data.get('economy', {}).get('balance', 0)
            xp = user_data.get('xp', 0)
            games = user_data.get('games_played', 0)
            is_owner = user.id == OWNER_ID
            is_admin = user_data.get('is_admin', False)
            
            role = "👑 OWNER" if is_owner else ("🛡️ ADMIN" if is_admin else "👤 User")
            
            await query.edit_message_text(
                text=f"╔═══════════════════════════╗\n"
                     f"║   💳 YOUR ACCOUNT 💳      ║\n"
                     f"╚═══════════════════════════╝\n\n"
                     f"💰 <b>Balance:</b> <code>{int(balance):,} ∆</code>\n"
                     f"⚡ <b>XP:</b> <code>{int(xp):,}</code>\n"
                     f"🎮 <b>Games:</b> <code>{games}</code>\n"
                     f"👑 <b>Status:</b> <b>{role}</b>",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "leaderboard":
            # Call leaderboard
            await self._show_leaderboard(update, query)
        elif query.data == "top":
            # Call top XP
            await self._show_top_xp(update, query)
        elif query.data == "bonus":
            # Call bonus
            await self._claim_bonus(update, query)
        elif query.data == "help_menu":
            await query.edit_message_text(
                text="<b>📚 COMMAND HELP</b>\n\n"
                     "<b>🎮 GAMES:</b>\n"
                     "• <code>/slots [amount]</code> - Play slots\n"
                     "• <code>/bet [amt] [heads|tails]</code> - Coin flip\n\n"
                     "<b>💎 ACCOUNT:</b>\n"
                     "• <code>/balance</code> - Check balance & XP\n"
                     "• <code>/bonus</code> - Daily 100 ∆ bonus\n"
                     "• <code>/send [@user] [amount]</code> - Send balance\n\n"
                     "<b>🏆 RANKINGS:</b>\n"
                     "• <code>/leaderboard</code> - Top 100 by balance\n"
                     "• <code>/top</code> - Top 10 by XP\n\n"
                     "<b>👑 OWNER ONLY:</b>\n"
                     "• <code>/owner</code> - Owner panel\n"
                     "• <code>/admin</code> - Admin panel",
                parse_mode=ParseMode.HTML
            )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - Show user detailed statistics"""
        user = update.effective_user
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or os.getenv("KOYEB_APPLICATION_ID") or os.getenv("KOYEB_APP_ID") or "default"
        
        def _get_stats():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            if not doc:
                return None
            # Get rank by balance
            rank = users_col.count_documents({"appId": APP_ID, "economy.balance": {"$gt": doc.get('economy', {}).get('balance', 0)}}) + 1
            client.close()
            return doc, rank
        
        result = await asyncio.to_thread(_get_stats)
        if not result:
            await update.message.reply_text("❌ User not found", parse_mode=ParseMode.HTML)
            return
        
        doc, rank = result
        balance = doc.get('economy', {}).get('balance', 0)
        xp = doc.get('xp', 0)
        games = doc.get('games_played', 0)
        is_owner = user.id == OWNER_ID
        is_admin = doc.get('is_admin', False)
        
        stats_msg = f"""<b>📊 YOUR STATISTICS</b>

╔════════════════════════════╗
║   <b>ACCOUNT OVERVIEW</b>        ║
╚════════════════════════════╝

💳 <b>Balance:</b> <code>{int(balance):,} 🪙</code>
⚡ <b>XP Level:</b> <code>{int(xp):,}</code>
🎮 <b>Games Played:</b> <code>{games}</code>
🏆 <b>Global Rank:</b> <code>#{rank}</code>

👑 <b>Status:</b> <b>{'OWNER 👑' if is_owner else ('ADMIN 🛡️' if is_admin else 'User 👤')}</b>

<b>🎯 Quick Stats:</b>
• Avg Balance/Game: <code>{int(balance/max(games, 1)):,}</code> 🪙
• XP/Game: <code>{int(xp/max(games, 1))}</code>

💡 <i>Keep playing to climb the ranks!</i>
"""
        await update.message.reply_text(stats_msg, parse_mode=ParseMode.HTML)

    async def rewards_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rewards command - Show reward system info"""
        rewards_msg = f"""<b>🎁 REWARD SYSTEM</b>

╔════════════════════════════╗
║   <b>EARNING REWARDS</b>      ║
╚════════════════════════════╝

<b>🎰 SLOTS GAMES:</b>
🎉 WIN: +100 XP + Multiplier rewards
   • Regular: 2.5x bet
   • Big Win: 5x bet
   • JACKPOT: 10x bet
😢 LOSS: +20 XP (still earn!)

<b>🪙 COIN FLIP:</b>
🎉 WIN: +60 XP + 2x bet
😢 LOSS: +10 XP

<b>💎 DAILY REWARDS:</b>
🎁 /bonus - 100 🪙 every 12 hours
⚡ Bonus Streak: Keep claiming!

<b>👑 ADMIN/OWNER BENEFITS:</b>
✨ 3x BETTER WIN ODDS on slots!
💰 Unlimited bets (no restrictions)
🌟 Double/Extra XP rewards
🎕 Early access to new features

<b>🏆 RANKING REWARDS:</b>
Use /top to see top 10 players
Use /leaderboard to see top 100
Climb ranks = More prestige!

💡 <b>Pro Tip:</b> Play both games for balanced XP growth!
"""
        await update.message.reply_text(rewards_msg, parse_mode=ParseMode.HTML)

    def setup(self):
        """Initialize the bot synchronously (register handlers)."""
        self.app = Application.builder().token(self.token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("balance", self.balance))
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard))
        self.app.add_handler(CommandHandler("bonus", self.bonus))
        self.app.add_handler(CommandHandler("slots", self.slots_command))
        self.app.add_handler(CommandHandler("bet", self.coin_flip))
        self.app.add_handler(CommandHandler("top", self.top_xp))
        self.app.add_handler(CommandHandler("send", self.send_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Advanced features 🎯
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("rewards", self.rewards_command))

        # Owner & Admin commands
        self.app.add_handler(CommandHandler("owner", self.owner_panel))
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
