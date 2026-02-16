@echo off
REM AXL GAME BOT - Setup Script for Windows

echo.
echo 🎮 ===== AXL GAME BOT SETUP (Windows) =====
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo 📥 Installing dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Dependencies installed
) else (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ⚙️ Creating .env file...
    copy .env.example .env
    echo ✓ .env file created
    echo.
    echo 📝 IMPORTANT: Edit .env and add your TELEGRAM_TOKEN
    echo.
    echo To get your bot token:
    echo 1. Open Telegram and search for @BotFather
    echo 2. Send /start
    echo 3. Send /newbot
    echo 4. Choose a name and username
    echo 5. Copy the token and paste it in .env
    echo.
) else (
    echo ✓ .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo To start the bot, run:
echo   python bot.py
echo.
echo Join our group: @vfriendschat
echo.
pause
