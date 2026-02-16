"""
Slots game logic for AXL GAME BOT
"""

import random
from typing import Tuple, Dict
from config import *


class SlotsGame:
    def __init__(self):
        self.emojis = ["🍎", "🍌", "🍒", "🍷", "⭐", "💎", "🎯"]
        self.paylines = 3

    def spin(self) -> Tuple[str, str, float]:
        """
        Spin the slots and return result
        Returns: (emoji_display, result_type, multiplier)
        """
        # Get 3 random positions for 3 paylines
        results = []
        for _ in range(3):
            line = [random.choice(self.emojis) for _ in range(3)]
            results.append(line)

        # Check for winning combinations
        emoji_display = self._format_display(results)
        result_type, multiplier = self._check_win(results)

        return emoji_display, result_type, multiplier

    def _format_display(self, results: list) -> str:
        """Format the slot display"""
        display = "🎰 **SLOTS SPINNING...** 🎰\n\n"
        display += "┌─────────────────┐\n"
        for i, line in enumerate(results):
            display += f"│ {' '.join(line)} │\n"
        display += "└─────────────────┘\n"
        return display

    def _check_win(self, results: list) -> Tuple[str, float]:
        """Check if there's a winning combination"""
        # Check each payline
        line_results = []
        for line in results:
            if line[0] == line[1] == line[2]:
                line_results.append((line[0], 3))  # 3 of a kind
            elif line[0] == line[1] or line[1] == line[2]:
                line_results.append((line[1], 2))  # 2 of a kind
            else:
                line_results.append((None, 0))

        # Determine prize
        wins = [r for r in line_results if r[0] is not None]

        if not wins:
            return "loss", 0

        # Check for 2+ paylines with 3 of a kind
        triple_wins = [r for r in line_results if r[1] == 3]

        if len(triple_wins) >= 3:  # All 3 lines are winners
            return "jackpot", JACKPOT_MULTIPLIER
        elif len(triple_wins) >= 2:  # 2 lines are winners
            return "big_win", BIG_WIN_MULTIPLIER
        elif len(wins) >= 2:  # Multiple wins
            return "big_win", BIG_WIN_MULTIPLIER
        else:  # Single win
            return "win", WIN_MULTIPLIER

    def play(self, bet_amount: float) -> Dict:
        """
        Play a round of slots
        Returns: {
            'display': emoji display,
            'result_type': win/big_win/jackpot/loss,
            'amount_won': amount won or lost,
            'message': formatted message
        }
        """
        emoji_display, result_type, multiplier = self.spin()

        if result_type == "loss":
            amount_won = -bet_amount
            message_template = RESULT_MESSAGES["loss"]
        else:
            amount_won = bet_amount * multiplier - bet_amount  # Profit
            message_template = RESULT_MESSAGES[result_type]

        # Format result message
        if amount_won >= 0:
            message = message_template.format(amount=int(amount_won), symbol=CURRENCY_SYMBOL)
        else:
            message = message_template.format(amount=int(abs(amount_won)), symbol=CURRENCY_SYMBOL)

        return {
            'display': emoji_display,
            'result_type': result_type,
            'amount_won': amount_won,
            'total_return': bet_amount + amount_won,  # If loss, this is (bet - loss) = remaining
            'message': message
        }


# Initialize game
slots_game = SlotsGame()
