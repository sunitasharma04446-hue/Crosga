# 🚀 Koyeb Deployment Complete Guide

Complete step-by-step guide to deploy **AXL GAME BOT** on Koyeb with MongoDB Atlas for 24/7 hosting.

## 📋 What You'll Need

- GitHub account with your bot code
- Telegram bot token from @BotFather
- Koyeb account (free - [koyeb.com](https://koyeb.com))
- MongoDB Atlas account (free - [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas))
- Your Telegram User ID (from @userinfobot)

---

## Part 1: Set Up MongoDB Atlas (Free Database)

### Step 1: Create MongoDB Account

1. Go to [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Click "Try Free"
3. Create account with email
4. Verify email

### Step 2: Create Database Cluster

1. Click "Create a Deployment"
2. Choose "M0" (Free tier) - **completely free**
3. Select your region (closest to your users)
4. Click "Create Deployment"
5. Wait 2-3 minutes for deployment

### Step 3: Create Database User

1. In MongoDB Atlas dashboard, go to "Security" → "DatabaseAccess"
2. Click "Add New Database User"
3. **Username:** `axlbot` (or your choice)
4. **Password:** Generate strong password (save it!)
5. Choose "Built-in Role" → `readWriteAnyDatabase`
6. Click "Add User"

**Save this password!** You'll need it shortly.

### Step 4: Allow Network Access

1. Go to "Security" → "Network Access"
2. Click "Add IP Address"
3. Choose "Allow access from anywhere"
4. Click "Confirm"

### Step 5: Get Connection String

1. Go back to "Clusters" or "Deployment"
2. Click "Connect"
3. Choose "Drivers" → "Python" → "3.6 or later"
4. Copy the connection string
5. It looks like: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`

**Important:** Replace:
- `username` with your database user (e.g., `axlbot`)
- `password` with your generated password
- `cluster` stays as-is

### Example Connection String:
```
mongodb+srv://axlbot:MyPassword123@cluster0.mongodb.net/axl_game_bot?retryWrites=true&w=majority
```

**Save this connection string!** You'll add it to Koyeb.

---

## Part 2: Prepare Your GitHub Repository

### Step 1: Make Sure Everything Is Committed

```bash
cd /path/to/your/Crosga
git add .
git commit -m "Add owner/admin system and MongoDB support"
git push origin main
```

### Step 2: Update Your .env File Locally (for testing)

```
TELEGRAM_TOKEN=your_real_token_here
OWNER_ID=your_telegram_user_id
```

**Never commit .env to GitHub!** (It's in .gitignore)

### Step 3: Verify Your Code

Make sure these files exist:
- `bot.py` ✓
- `config.py` ✓
- `database.py` ✓
- `slots.py` ✓
- `requirements.txt` ✓
- `.env.example` ✓
- `Dockerfile` ✓

---

## Part 3: Deploy on Koyeb

### Step 1: Create Koyeb Account

1. Go to [koyeb.com](https://koyeb.com)
2. Click "Sign up"
3. Sign up with GitHub (recommended)
4. Authorize Koyeb to access your GitHub
5. Verify email

### Step 2: Create New Service

1. After logging in, click "Create a New Service"
2. Select "Docker"
3. Click "GitHub"

### Step 3: Connect Your GitHub Repository

1. Authorize Koyeb to access GitHub (if not done)
2. Select your organization/account
3. Search and select "Crosga" repository
4. Click "Continue"

### Step 4: Configure Service

Fill in the fields:

**Builder Section:**
- **Builder:** "Dockerfile"
- Leave other options default

**Service Section:**
- **Service name:** `axl-game-bot`
- **Port:** `8000` (ignored but required)
- **HTTP port:** `8000`

### Step 5: Add Environment Variables

This is crucial! Click "Environment variables" and add:

1. **Variable Name:** `TELEGRAM_TOKEN`
   - **Value:** Your bot token from @BotFather
   - Example: `123456789:ABCDEFGhijklmnopqrstuvwxyzABC...`

2. **Variable Name:** `OWNER_ID`
   - **Value:** Your Telegram User ID
   - Get from: [@userinfobot](https://t.me/userinfobot)
   - Example: `987654321`

3. **Variable Name:** `MONGODB_URI` (optional)
   - **Value:** Your MongoDB connection string
   - Example: `mongodb+srv://axlbot:MyPass123@cluster0.mongodb.net/axl_game_bot`

Your environment should look like:
```
TELEGRAM_TOKEN=123456789:ABCDEFGhijklmnopqr...
OWNER_ID=987654321
MONGODB_URI=mongodb+srv://axlbot:MyPass123@cluster0.mongodb.net/axl_game_bot
```

### Step 6: Deployment Settings

- **Deployment region:** Choose closest to you
- **Instance type:** Free tier selected automatically
- **Scaling:** Minimum 1, Maximum 1 (good for bot)

### Step 7: Deploy

1. Review your settings
2. Click "Create and Deploy"
3. Watch the deployment (takes 2-5 minutes)
4. When done, you'll see "✅ Running"

---

## Part 4: Verify Your Bot Is Running

### Test Your Bot

1. Open Telegram
2. Search for your bot (by username)
3. Send `/start`
4. Should see welcome menu
5. Try `/balance`
6. Try `/slots 50`

### Check Logs

In Koyeb dashboard:
1. Click your service "axl-game-bot"
2. Go to "Logs"
3. Should see: `🎮 AXL GAME BOT is running!`

### Common Issues

**Issue:** Bot not responding
- Check logs for errors
- Verify TELEGRAM_TOKEN is correct
- Restart service in Koyeb

**Issue:** Permission denied errors
- Verify OWNER_ID is set
- Make sure it's your Telegram User ID

**Issue:** Database connection failed
- Check MongoDB connection string
- Verify user/password in MongoDB Atlas
- Verify IP allowlist (should be "anywhere")

---

## Part 5: Use Your Bot

### Commands Available

**For Everyone:**
- `/start` - Welcome menu
- `/balance` - Check balance
- `/leaderboard` - Top 10 players
- `/slots [amount]` - Play slots
- `/bonus` - Daily 100∆ bonus
- `/send [amount]` - Send currency

**For Admins & Owner:**
- `/admin` - Admin panel
- `/grant [user_id] [amount]` - Give balance
- `/ban [user_id]` - Ban player
- `/unban [user_id]` - Unban player

**For Owner Only:**
- `/setadmin [user_id]` - Make someone admin

### Owner Features

As owner (with your OWNER_ID):
- **Unlimited bets** - No betting limits
- **Give balance** - `/grant 123456789 1000`
- **Manage admins** - `/setadmin user_id`
- **Ban players** - `/ban user_id`
- **Full control** - All permissions

### Admin Features

As admin (given by owner):
- **Unlimited bets** - No betting limits
- **Give balance** - `/grant 123456789 1000`
- **Help owner** - Share admin duties

---

## Part 6: Monitor Your Bot

### Koyeb Dashboard

Go to [koyeb.com/apps](https://koyeb.com/apps)
- Check service status (should be ✅ Running)
- View real-time logs
- Restart if needed
- Scale if needed

### Database Monitoring

Go to [MongoDB Atlas](https://cloud.mongodb.com)
- View database usage
- Check active connections
- Monitor database size
- Free tier: 512MB storage included

---

## Part 7: Updates & Changes

### Update Your Bot

1. Make changes locally
2. Test with `/start` command
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update bot features"
   git push origin main
   ```
4. Koyeb will **auto-redeploy** (usually within 1 minute)
5. After redeployment, bot automatically restarts
6. Test again in Telegram

### Easy Updates

- Change bot name → Edit `config.py`
- Change currency → Edit `config.py`
- Change rewards → Edit `config.py`
- Add new commands → Edit `bot.py`

---

## Part 8: Make Your Bot Public

### Add to Telegram Bot Directory

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/mybots`
3. Select your bot
4. Send `/setuserpic` to add profile pic
5. Send `/setdescription` to add description
6. Send `/setshortdescription` for short bio

### Add to Group

1. Invite bot to your group: `@vfriendschat`
2. Make bot admin (optional)
3. Users can play directly in group

### Promote Your Bot

1. Share username: `@YourBotName`
2. Share group: `@vfriendschat`
3. Post screenshots on social media
4. Get friends to play!

---

## 💡 Pro Tips

### Free Tier Limits

- **Koyeb:** Free tier runs 24/7 indefinitely
- **MongoDB:** 512MB storage per database (free)
- **Bot:** Unlimited messages and users

### Backup Your Database

Regularly download your database:
```bash
# Download from MongoDB Atlas
1. Go to Collections
2. Select database
3. Click "Export"
```

### Monitoring

Check Koyeb logs weekly for errors. Restart service if bot stops.

### Scaling

If you get lots of users:
- Koyeb free tier handles ~1000 users
- MongoDB free handles millions of records
- Upgrade when needed (paid tiers available)

---

## 🆘 Troubleshooting

### Bot Offline Error

```
Telegram: "Bot username is not responding"
```

**Solution:**
1. Check Koyeb logs for errors
2. Verify TELEGRAM_TOKEN
3. Restart service in Koyeb
4. Wait 2 minutes and try again

### Database Connection Error

```
MongoDB: "Authentication failed"
```

**Solution:**
1. Verify MongoDB connection string
2. Check username/password match
3. Verify IP is allowed (check Network Access)
4. Test connection string format

### Permission Denied

```
Command: "Only owner can use this command"
```

**Solution:**
1. Get your User ID from @userinfobot
2. Set OWNER_ID in Koyeb environment
3. Restart service
4. Try command again

### Logs Full

Clear logs in Koyeb by restarting service.

---

## 📊 Command Reference

| Command | Owner | Admin | User |
|---------|-------|-------|------|
| `/start` | ✓ | ✓ | ✓ |
| `/balance` | ✓ | ✓ | ✓ |
| `/leaderboard` | ✓ | ✓ | ✓ |
| `/slots` | ✓∞ | ✓∞ | ✓ (limit) |
| `/bonus` | ✓ | ✓ | ✓ |
| `/send` | ✓ | ✓ | ✓ |
| `/admin` | ✓ | ✓ | ✗ |
| `/grant` | ✓ | ✓ | ✗ |
| `/ban` | ✓ | ✗ | ✗ |
| `/setadmin` | ✓ | ✗ | ✗ |

∞ = No betting limit

---

## 🎉 You're All Set!

Your bot is now live 24/7 on Koyeb! 

**Next steps:**
- Invite friends to play
- Set up admins with `/setadmin`
- Promote in your group `@vfriendschat`
- Monitor logs in Koyeb
- Back up database regularly

**Support:** Join group `@vfriendschat`

---

**Deployed with ❤️ on Koyeb**

Last updated: February 2026
