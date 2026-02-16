#!/bin/bash

# AXL GAME BOT - Setup Script
# This script sets up the bot for you automatically

echo "🎮 ===== AXL GAME BOT SETUP ====="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "✓ Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your TELEGRAM_TOKEN"
    echo ""
    echo "To get your bot token:"
    echo "1. Open Telegram and search for @BotFather"
    echo "2. Send /start"
    echo "3. Send /newbot"
    echo "4. Choose a name and username"
    echo "5. Copy the token and paste it in .env"
    echo ""
else
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the bot, run:"
echo "  python bot.py"
echo ""
echo "Join our group: @vfriendschat"
echo ""
