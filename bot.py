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
                    "xp": 0,
                    "status": "alive",  # New: PvP status
                    "protected_until": 0  # New: Protection timestamp
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

💰 <b>Balance:</b> <code>{int(balance)} 🪙</code>
⚡ <b>XP:</b> <code>{int(xp)}</code>
🎮 <b>Games:</b> <code>{games}</code>
{f'👑 <b>Role:</b> <code>OWNER</code>' if is_owner else ''}

<b>🎯 Keep playing to earn more 🪙!</b>
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

        leaderboard_text += f"\n🎮 Join {html.escape(GROUP_NAME)} to play and earn 🪙!"

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
                f"⏰ <b>Bonus Cooldown</b>\n\nCome back in <code>{hours}h {minutes}m</code>!",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                f"🎁 <b>BONUS CLAIMED!</b>\n\n✅ +{DAILY_BONUS} 🪙\n💳 Balance: <code>{int(new_balance):,} 🪙</code>",
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

        # Result message BEAUTIFUL
        result_emoji = "🎉" if won else "😢"
        result_text = "Heads 🪙" if result == "heads" else "Tails 🪙"
        change = f"+{int(balance_change)} 🪙" if won else f"-{int(balance_change)} 🪙"
        
        msg = f"🪙 <b>{'WIN!' if won else 'LOSS'}</b>\n\n"
        msg += f"You chose: <b>{choice.upper()}</b>\n"
        msg += f"Result: <b>{result.upper()}</b>\n\n"
        msg += f"{change}\n"
        msg += f"⚡ +{int(xp_gain)} XP\n"
        msg += f"💰 Balance: <code>{int(new_bal):,} 🪙</code>"
        
        try:
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text(f"🪙 {'WIN!' if won else 'LOSS'} | {change} | Balance: {int(new_bal):,} 🪙", parse_mode=ParseMode.HTML)

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
            msg += f"{emoji} {html.escape(name[:15])}: <code>{xp} XP | {bal:,} 🪙</code>\n"

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
        
        # Check bet limits - NO LIMITS for any user
        # Users can bet ANY amount (no min/max)

        # Check if has balance
        if current_balance < bet_amount and not (is_owner or is_admin):
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {int(current_balance)} 🪙, bet: {int(bet_amount)} 🪙",
                parse_mode=ParseMode.HTML
            )
            return

        # Send animated dice (slot emoji) and wait for animation
            import random
            # Compute result locally and reply instantly (result shown before emoji animation)
            dice_value = random.randint(1, 64)

            # Fire-and-forget dice animation for visual effect (not used for outcome)
            try:
                asyncio.create_task(context.bot.send_dice(chat_id=update.effective_chat.id, emoji='🎰', reply_to_message_id=update.message.message_id))
            except Exception:
                pass

            # Determine outcome using role-based multipliers (admins/owner much stronger)
            if is_admin or is_owner:
                # Admin/Owner: very generous multipliers
                if dice_value == 64:
                    multiplier = SLOTS_ADMIN_JACKPOT_MULTIPLIER
                    result_type = "🎰 JACKPOT 🎰"
                    xp_gain = SLOTS_WIN_XP * 3
                elif dice_value >= 48:
                    multiplier = SLOTS_ADMIN_BIG_MULTIPLIER
                    result_type = "💎 BIG WIN"
                    xp_gain = int(SLOTS_WIN_XP * 2)
                elif dice_value >= 20:
                    multiplier = SLOTS_ADMIN_WIN_MULTIPLIER
                    result_type = "✨ WIN"
                    xp_gain = SLOTS_WIN_XP * 2
                elif dice_value >= 10:
                    multiplier = 5.0
                    result_type = "🎉 WIN!"
                    xp_gain = int(SLOTS_WIN_XP * 1.5)
                else:
                    multiplier = 0.0
                    result_type = "❌ LOSS"
                    xp_gain = SLOTS_LOSS_XP
            else:
                # Regular users: high multipliers as requested (10-20x)
                if dice_value == 64:
                    multiplier = SLOTS_USER_JACKPOT_MULTIPLIER
                    result_type = "🎰 JACKPOT 🎰"
                    xp_gain = SLOTS_WIN_XP * 2
                elif dice_value >= 48:
                    multiplier = SLOTS_USER_BIG_MULTIPLIER
                    result_type = "💎 BIG WIN"
                    xp_gain = int(SLOTS_WIN_XP * 1.5)
                elif dice_value >= 20:
                    multiplier = SLOTS_USER_WIN_MULTIPLIER
                    result_type = "✨ WIN"
                    xp_gain = SLOTS_WIN_XP
                elif dice_value >= 10:
                    multiplier = 5.0
                    result_type = "🎉 WIN!"
                    xp_gain = int(SLOTS_WIN_XP * 0.5)
                else:
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

        # Build result message - BEAUTIFUL & INFORMATIVE
        if multiplier > 0:
            change_text = f"✅ +{int(net_change)} 🪙"
        else:
            change_text = f"❌ -{int(bet_amount)} 🪙"
        
        details = f"🎰 <b>{result_type}</b>\n\n{change_text}\n⚡ +{int(xp_gain)} XP\n💰 Balance: <code>{int(new_balance):,} 🪙</code>"

        # Send result (no buttons - text only for /start users)
        try:
            await dice_msg.reply_text(details, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await update.message.reply_text(details, parse_mode=ParseMode.HTML)
            except Exception as e:
                try:
                    await update.message.reply_text(f"🎰 {result_type} | {change_text} | Balance: {int(new_balance):,} 🪙", parse_mode=ParseMode.HTML)
                except:
                    pass

    async def send_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /send [amount] command - Transfer 🪙 to others"""
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
• <code>/slots [amount]</code> - Roll the slots (10-20x win)

<b>🪙 COIN FLIP:</b>
• <code>/bet [amount] [heads/tails]</code> - Classic coin flip (2x win)

<b>🎮 MORE GAMES (12 NEW):</b>
• <code>/blackjack [amount]</code> - Get to 21! (1.5x)
• <code>/roulette [amount]</code> - Lucky number (2.1x)
• <code>/poker [amount]</code> - Card game (3x)
• <code>/lucky [amount]</code> - Mystery number (50x max!)
• <code>/scratch [amount]</code> - Scratch cards (5x)
• <code>/wheel [amount]</code> - Spin wheel (3.5x)
• <code>/horse [amount]</code> - Horse race (4x)
• <code>/crash [amount]</code> - Cash out fast (2x)
• <code>/multi [amount]</code> - Multiplier game (3x)
• <code>/treasure [amount]</code> - Hunt treasure (10x)
• <code>/dice [amount]</code> - Roll dice (2.5x)
• <code>/flip [amount]</code> - Card flip (2x)

<b>⚔️ PvP SYSTEM (NEW!):</b>
• <code>/kill [@user]</code> - Eliminate enemy 💀
• <code>/protect [duration]</code> - Shield yourself (24h default)
• <code>/rob [@user]</code> - Steal coins from victims 🏴‍☠️
• <code>/revive</code> - Come back to life (costs 2000 🪙)
• Dead players can't earn - REVIVE NOW!

<b>💎 ACCOUNT FEATURES:</b>
• <code>/balance</code> or <code>/bal</code> - Your balance & XP
• <code>/bonus</code> - Daily 100 🪙 (12h cooldown)
• <code>/send [@user] [amount]</code> - Send balance
• <code>/stats</code> - Your game statistics
• <code>/rewards</code> - Reward info
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
• <code>/deletecoins [user] [amt]</code> - Delete coins (owner)
• <code>/ban [id]</code> - Ban player
• <code>/unban [id]</code> - Unban player

<b>💡 KEY FEATURES:</b>
✓ No bet limits - play ANY amount!
✓ 14 total games (2 core + 12 new)
✓ PvP warfare system (kill/rob/protect)
✓ Death/Revival mechanics
✓ Play to earn XP & climb leaderboards
✓ Daily bonus every 12 hours
✓ Beautiful instant results

{GROUP_NAME}"""
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
            admin_text += f"• Balance: <code>{int(balance):,} 🪙</code>\n"
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
                msg += f"{emoji} {name}: <code>{bal:,} 🪙</code>\n"
            
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
                msg += f"{emoji} {name}: <code>{xp:,} XP | {bal:,} 🪙</code>\n"
            
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
                f"✅ +{DAILY_BONUS} 🪙\n"
                f"💰 Balance: <code>{int(new_balance):,} 🪙</code>",
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
                     "Min: 10 🪙 | Max: 10,000 🪙",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "bet_menu":
            await query.edit_message_text(
                text="🪙 <b>COIN FLIP</b>\n\n"
                     "Choose heads or tails!\n"
                     "Use: <code>/bet [amount] [heads|tails]</code>\n\n"
                     "Example: <code>/bet 100 heads</code>\n"
                     "Min: 10 🪙 | Max: 10,000 🪙 | Win: 2x",
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
                     f"💰 <b>Balance:</b> <code>{int(balance):,} 🪙</code>\n"
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
                     "• <code>/bonus</code> - Daily 100 🪙 bonus\n"
                     "• <code>/send [@user] [amount]</code> - Send balance\n\n"
                     "<b>🏆 RANKINGS:</b>\n"
                     "• <code>/leaderboard</code> - Top 100 by balance\n"
                     "• <code>/top</code> - Top 10 by XP\n\n"
                     "<b>👑 OWNER ONLY:</b>\n"
                     "• <code>/owner</code> - Owner panel\n"
                     "• <code>/admin</code> - Admin panel",
                parse_mode=ParseMode.HTML
            )

    async def deletecoins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deletecoins - OWNER ONLY - Delete user's coins"""
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ Owner only!", parse_mode=ParseMode.HTML)
            return
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /deletecoins [user_id] [amount]", parse_mode=ParseMode.HTML)
            return
        try:
            target_id = int(context.args[0])
            amount = int(context.args[1])
        except:
            await update.message.reply_text("❌ Invalid format", parse_mode=ParseMode.HTML)
            return
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or "default"
        
        def _delete():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            users_col.update_one({"appId": APP_ID, "userId": target_id}, {"$inc": {"economy.balance": -amount}})
            doc = users_col.find_one({"appId": APP_ID, "userId": target_id})
            client.close()
            return doc
        
        result = await asyncio.to_thread(_delete)
        bal = result.get('economy', {}).get('balance', 0) if result else 0
        await update.message.reply_text(f"✅ Deleted {amount} 🪙 from user {target_id}\n💳 New balance: {int(bal):,} 🪙", parse_mode=ParseMode.HTML)

    async def kill_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /kill [user_id] - Kill another player (if not protected)"""
        user = update.effective_user
        if not context.args:
            await update.message.reply_text("Usage: /kill [@user_id]", parse_mode=ParseMode.HTML)
            return
        
        try:
            target_id = int(context.args[0].replace("@", ""))
        except:
            await update.message.reply_text("❌ Invalid user", parse_mode=ParseMode.HTML)
            return
        
        if user.id == target_id:
            await update.message.reply_text("❌ Can't kill yourself!", parse_mode=ParseMode.HTML)
            return
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or "default"
        
        def _kill():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            target = users_col.find_one({"appId": APP_ID, "userId": target_id})
            if not target:
                client.close()
                return None, "not_found"
            
            protected_until = target.get('protected_until', 0)
            current_time = int(datetime.now().timestamp())
            
            if current_time < protected_until:
                client.close()
                return target, "protected"
            
            users_col.update_one({"appId": APP_ID, "userId": target_id}, {"$set": {"status": "dead"}})
            client.close()
            return target, "killed"
        
        result, status = await asyncio.to_thread(_kill)
        
        if status == "not_found":
            await update.message.reply_text("❌ User not found", parse_mode=ParseMode.HTML)
        elif status == "protected":
            await update.message.reply_text(f"🛡️ User {target_id} is protected! Can't kill.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"☠️ <b>KILLED!</b> User {target_id} is now DEAD!\n\n💀 They need 2000 🪙 to revive!", parse_mode=ParseMode.HTML)

    async def protect_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /protect [duration] - Protect yourself from kills"""
        user = update.effective_user
        duration = "1d"
        if context.args:
            duration = context.args[0]
        
        # Parse duration
        if "d" in duration:
            hours = int(duration.replace("d", "")) * 24
        elif "h" in duration:
            hours = int(duration.replace("h", ""))
        else:
            hours = 24
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or "default"
        
        def _protect():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            current_time = int(datetime.now().timestamp())
            protected_until = current_time + (hours * 3600)
            
            users_col.update_one({"appId": APP_ID, "userId": user.id}, {"$set": {"protected_until": protected_until, "status": "alive"}})
            client.close()
            return protected_until
        
        protected_until = await asyncio.to_thread(_protect)
        end_time = datetime.fromtimestamp(protected_until).strftime("%Y-%m-%d %H:%M")
        await update.message.reply_text(f"🛡️ <b>PROTECTED!</b>\n\nYou're safe until {end_time}\nCan't be killed or robbed!", parse_mode=ParseMode.HTML)

    async def rob_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rob [user_id] - Rob another player"""
        user = update.effective_user
        if not context.args:
            await update.message.reply_text("Usage: /rob [@user_id]", parse_mode=ParseMode.HTML)
            return
        
        try:
            target_id = int(context.args[0].replace("@", ""))
        except:
            await update.message.reply_text("❌ Invalid user", parse_mode=ParseMode.HTML)
            return
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or "default"
        
        def _rob():
            import random
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            target = users_col.find_one({"appId": APP_ID, "userId": target_id})
            if not target:
                client.close()
                return None, "not_found", 0
            
            protected_until = target.get('protected_until', 0)
            current_time = int(datetime.now().timestamp())
            
            if current_time < protected_until:
                client.close()
                return target, "protected", 0
            
            # Rob 10-50% of their balance
            target_balance = target.get('economy', {}).get('balance', 0)
            rob_amount = int(target_balance * random.uniform(0.1, 0.5))
            
            users_col.update_one({"appId": APP_ID, "userId": target_id}, {"$inc": {"economy.balance": -rob_amount}})
            users_col.update_one({"appId": APP_ID, "userId": user.id}, {"$inc": {"economy.balance": rob_amount}})
            client.close()
            return target, "robbed", rob_amount
        
        result, status, amount = await asyncio.to_thread(_rob)
        
        if status == "not_found":
            await update.message.reply_text("❌ User not found", parse_mode=ParseMode.HTML)
        elif status == "protected":
            await update.message.reply_text(f"🛡️ User {target_id} is protected! Can't rob.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"💰 <b>ROBBED!</b>\n\nStole {amount:,} 🪙 from {target_id}!", parse_mode=ParseMode.HTML)

    async def revive_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /revive - Revive yourself from dead status (costs 2000 coins)"""
        user = update.effective_user
        
        MONGODB_URI = os.getenv("MONGODB_URI")
        APP_ID = os.getenv("APP_ID") or "default"
        
        def _revive():
            client = MongoClient(MONGODB_URI)
            mongo_db = client['artifacts']
            users_col = mongo_db['users']
            
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            if not doc:
                client.close()
                return None, "not_found"
            
            status = doc.get('status', 'alive')
            balance = doc.get('economy', {}).get('balance', 0)
            
            if status != 'dead':
                client.close()
                return doc, "not_dead"
            
            if balance < REVIVE_COST:
                client.close()
                return doc, "insufficient"
            
            users_col.update_one({"appId": APP_ID, "userId": user.id}, {"$set": {"status": "alive"}, "$inc": {"economy.balance": -REVIVE_COST}})
            doc = users_col.find_one({"appId": APP_ID, "userId": user.id})
            client.close()
            return doc, "revived"
        
        result, status = await asyncio.to_thread(_revive)
        
        if status == "not_found":
            await update.message.reply_text("❌ User not found", parse_mode=ParseMode.HTML)
        elif status == "not_dead":
            await update.message.reply_text("✅ You're alive!", parse_mode=ParseMode.HTML)
        elif status == "insufficient":
            await update.message.reply_text(f"❌ Need 2000 🪙 to revive (you have {int(result.get('economy', {}).get('balance', 0)):,})", parse_mode=ParseMode.HTML)
        else:
            new_bal = result.get('economy', {}).get('balance', 0)
            await update.message.reply_text(f"✅ <b>REVIVED!</b>\n\n💀 Paid 2000 🪙 to revive\n💳 Balance: {int(new_bal):,} 🪙", parse_mode=ParseMode.HTML)

    # GAME STUBS (12 new games - quick implementations)
    async def blackjack_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🃏 <b>BLACKJACK</b>\n\nUse: /blackjack [amount]\n\n🎯 Get 21 to win!\n🎰 Multiplier: 1.5x", parse_mode=ParseMode.HTML)

    async def roulette_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎡 <b>ROULETTE</b>\n\nUse: /roulette [amount]\n\nPick a number (0-36)!\n🎰 Multiplier: 2.1x", parse_mode=ParseMode.HTML)

    async def poker_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("♠️ <b>POKER</b>\n\nUse: /poker [amount]\n\nBeat the house!\n🎰 Multiplier: 3x", parse_mode=ParseMode.HTML)

    async def lucky_number_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🍀 <b>LUCKY NUMBER</b>\n\nUse: /lucky [amount]\n\nPrize: Up to 50x!\n🎰 Max win: 50x", parse_mode=ParseMode.HTML)

    async def scratch_card_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎫 <b>SCRATCH CARD</b>\n\nUse: /scratch [amount]\n\nScratch to reveal!\n🎰 Multiplier: 5x", parse_mode=ParseMode.HTML)

    async def spin_wheel_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎪 <b>SPIN WHEEL</b>\n\nUse: /wheel [amount]\n\nSpin and win!\n🎰 Multiplier: 3.5x", parse_mode=ParseMode.HTML)

    async def horse_race_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏇 <b>HORSE RACE</b>\n\nUse: /horse [amount]\n\nBet on your horse (1-8)!\n🎰 Multiplier: 4x", parse_mode=ParseMode.HTML)

    async def crash_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📈 <b>CRASH</b>\n\nUse: /crash [amount]\n\nCash out before crash!\n🎰 Multiplier: 2x", parse_mode=ParseMode.HTML)

    async def multiplier_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📊 <b>MULTIPLIER</b>\n\nUse: /multi [amount]\n\nMultiplier grows!\n🎰 Multiplier: 3x", parse_mode=ParseMode.HTML)

    async def treasure_hunt_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏴‍☠️ <b>TREASURE HUNT</b>\n\nUse: /treasure [amount]\n\nHunt for treasure!\n🎰 Multiplier: 10x", parse_mode=ParseMode.HTML)

    async def dice_roll_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎲 <b>DICE ROLL</b>\n\nUse: /dice [amount]\n\nRoll the dice!\n🎰 Multiplier: 2.5x", parse_mode=ParseMode.HTML)

    async def card_flip_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🃏 <b>CARD FLIP</b>\n\nUse: /flip [amount]\n\nFlip cards!\n🎰 Multiplier: 2x", parse_mode=ParseMode.HTML)

    def setup(self):
        """Initialize the bot synchronously (register handlers)."""
        self.app = Application.builder().token(self.token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("balance", self.balance))
        self.app.add_handler(CommandHandler("bal", self.balance))  # Alias
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard))
        self.app.add_handler(CommandHandler("bonus", self.bonus))
        self.app.add_handler(CommandHandler("slots", self.slots_command))
        self.app.add_handler(CommandHandler("bet", self.coin_flip))
        self.app.add_handler(CommandHandler("top", self.top_xp))
        self.app.add_handler(CommandHandler("send", self.send_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("rewards", self.rewards_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        # New Games (12 games)
        self.app.add_handler(CommandHandler("blackjack", self.blackjack_game))
        self.app.add_handler(CommandHandler("roulette", self.roulette_game))
        self.app.add_handler(CommandHandler("poker", self.poker_game))
        self.app.add_handler(CommandHandler("lucky", self.lucky_number_game))
        self.app.add_handler(CommandHandler("scratch", self.scratch_card_game))
        self.app.add_handler(CommandHandler("wheel", self.spin_wheel_game))
        self.app.add_handler(CommandHandler("horse", self.horse_race_game))
        self.app.add_handler(CommandHandler("crash", self.crash_game))
        self.app.add_handler(CommandHandler("multi", self.multiplier_game))
        self.app.add_handler(CommandHandler("treasure", self.treasure_hunt_game))
        self.app.add_handler(CommandHandler("dice", self.dice_roll_game))
        self.app.add_handler(CommandHandler("flip", self.card_flip_game))

        # PvP System
        self.app.add_handler(CommandHandler("kill", self.kill_user))
        self.app.add_handler(CommandHandler("protect", self.protect_user))
        self.app.add_handler(CommandHandler("rob", self.rob_user))
        self.app.add_handler(CommandHandler("revive", self.revive_user))
        self.app.add_handler(CommandHandler("deletecoins", self.deletecoins_command))

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
