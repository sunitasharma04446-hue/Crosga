"""
Database module for AXL GAME BOT
Handles user data, balance, and game history
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List
import json

DB_PATH = "axl_game_bot.db"


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 500,
                total_winnings REAL DEFAULT 0,
                total_losses REAL DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                last_bonus_time INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Game history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                game_type TEXT,
                bet_amount REAL,
                result_amount REAL,
                result_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Transactions table (for /send command)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        return dict(user) if user else None

    def create_user(self, user_id: int, username: str = None, first_name: str = None, starting_balance: int = 500) -> Dict:
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, balance)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, starting_balance))
            conn.commit()

            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()
            return dict(user)
        except sqlite3.IntegrityError:
            conn.close()
            return self.get_user(user_id)

    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        """Get user or create if doesn't exist"""
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id, username, first_name)
        return user

    def update_balance(self, user_id: int, amount: float) -> float:
        """Update user balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users 
            SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (amount, user_id))
        conn.commit()

        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        new_balance = cursor.fetchone()[0]
        conn.close()

        return new_balance

    def add_game_result(self, user_id: int, bet_amount: float, result_amount: float, result_type: str, game_type: str = "slots"):
        """Record game result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO game_history (user_id, game_type, bet_amount, result_amount, result_type)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, game_type, bet_amount, result_amount, result_type))

        # Update user stats
        if result_amount > 0:
            cursor.execute("""
                UPDATE users 
                SET total_winnings = total_winnings + ?, games_played = games_played + 1, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (result_amount, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET total_losses = total_losses + ?, games_played = games_played + 1, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (abs(result_amount), user_id))

        conn.commit()
        conn.close()

    def set_bonus_claimed(self, user_id: int):
        """Set the last bonus claim time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = int(datetime.now().timestamp())
        cursor.execute("""
            UPDATE users 
            SET last_bonus_time = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (current_time, user_id))
        conn.commit()
        conn.close()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top players by balance"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, first_name, balance, total_winnings, games_played
            FROM users
            ORDER BY balance DESC
            LIMIT ?
        """, (limit,))

        users = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return users

    def transfer_balance(self, sender_id: int, receiver_id: int, amount: float) -> bool:
        """Transfer balance from one user to another"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if sender has enough balance
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
            sender = cursor.fetchone()
            if not sender or sender[0] < amount:
                conn.close()
                return False

            # Check if receiver exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (receiver_id,))
            if not cursor.fetchone():
                conn.close()
                return False

            # Perform transfer
            cursor.execute("""
                UPDATE users SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (amount, sender_id))

            cursor.execute("""
                UPDATE users SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (amount, receiver_id))

            # Record transaction
            cursor.execute("""
                INSERT INTO transactions (sender_id, receiver_id, amount)
                VALUES (?, ?, ?)
            """, (sender_id, receiver_id, amount))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Transfer error: {e}")
            return False

    def get_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT balance, total_winnings, total_losses, games_played, 
                   CASE WHEN games_played > 0 THEN ROUND((total_winnings::float / games_played), 2) ELSE 0 END as avg_win
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        stats = cursor.fetchone()
        conn.close()

        return dict(stats) if stats else None

    def set_admin(self, user_id: int, is_admin: bool) -> bool:
        """Make user an admin (unlimited bets, can grant balance)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users 
                SET is_admin = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (1 if is_admin else 0, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Admin update error: {e}")
            return False

    def is_admin_user(self, user_id: int) -> bool:
        """Check if user is admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] == 1 if result else False

    def is_banned_user(self, user_id: int) -> bool:
        """Check if user is banned"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        return result[0] == 1 if result else False

    def ban_user(self, user_id: int, ban: bool = True) -> bool:
        """Ban/unban a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users 
                SET is_banned = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (1 if ban else 0, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Ban update error: {e}")
            return False

    def grant_balance(self, user_id: int, amount: float) -> float:
        """Admin/Owner grant balance to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users 
            SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (amount, user_id))
        conn.commit()

        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        new_balance = cursor.fetchone()[0]
        conn.close()

        return new_balance


# Initialize database
db = Database()
