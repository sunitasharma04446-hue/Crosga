# 🗄️ MongoDB Setup Guide (Alternative to SQLite)

How to use MongoDB Atlas (free cloud database) instead of SQLite for AXL GAME BOT.

## Why MongoDB?

| Feature | SQLite | MongoDB |
|---------|--------|---------|
| Storage | Local file | Cloud (512MB free) |
| Backup | Manual | Automatic |
| Access | Local only | World-wide |
| Setup | Automatic | 5 minutes |
| Scale | Limited | Unlimited |
| Cost | Free | Free (512MB) |

---

## Part 1: Create MongoDB Atlas Account (Free)

### Step 1: Sign Up

1. Go to [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Click "Try Free"
3. Enter email and create password
4. Click "Create account"
5. Verify your email

### Step 2: Accept Terms

- Read and accept MongoDB terms
- Click "I agree..."

### Step 3: Answer Setup Questions

- **What is your goal?** → "Build with MongoDB"
- **Preferred language?** → "Python"
- Click "Tell me more"

### Step 4: Create Free Cluster

1. Click "Create a Deployment"
2. Choose **M0 Sandbox** (completely free, no credit card needed)
3. Select **Cloud Provider Region**
   - Choose location closest to you
   - Or keep default
4. Click "Create Deployment"
5. **Wait 7-10 minutes** for deployment to complete

---

## Part 2: Create Database Credentials

### Create Database User

Once cluster is created:

1. Left sidebar → "Security" → "Database Access"
2. Click "Add New Database User"
3. **Username:** `axlbot`
4. **Password:** Click "Generate" for strong password
   - **SAVE THIS PASSWORD!** You'll need it
5. **Built-in roles:** Select `readWriteAnyDatabase`
6. Click "Add User"

**Your credentials:**
```
Username: axlbot
Password: (generated password)
```

### Allow Network Access

1. Left sidebar → "Security" → "Network Access"
2. Click "Add IP Address"
3. **IP Address:** Click "Allow access from anywhere"
4. Description: "All IPs"
5. Click "Confirm"

---

## Part 3: Get Connection String

### Get MongoDB URI

1. Click "Clusters" in left sidebar
2. Your cluster should show (M0 Free Tier)
3. Click "Connect"
4. Choose "Drivers"
5. Select "Python" and version "3.6+"
6. Copy the connection string

**Format:**
```
mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority
```

### Replace with Your Credentials

**Original:**
```
mongodb+srv://axlbot:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
```

**Replace:**
- `<password>` → Your generated password

**Example:**
```
mongodb+srv://axlbot:MySecurePassword123@cluster0.mongodb.net/?retryWrites=true&w=majority
```

**Save this! You'll need it for Koyeb.**

---

## Part 4: Enable MongoDB in AXL BOT

### Option A: Use SQLite (Default)

No changes needed! SQLite works automatically.

### Option B: Use MongoDB

Update `.env`:

```
TELEGRAM_TOKEN=your_bot_token
OWNER_ID=your_user_id
MONGODB_URI=mongodb+srv://axlbot:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

---

## Part 5: Deploy with MongoDB on Koyeb

### In Koyeb Environment Variables

Add these three:

```
TELEGRAM_TOKEN=123456789:ABCDEFGhijklmnop...
OWNER_ID=987654321
MONGODB_URI=mongodb+srv://axlbot:MySecurePassword123@cluster0.mongodb.net/?retryWrites=true&w=majority
```

---

## 📊 MongoDB Atlas Dashboard

### View Your Database

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Click "Clusters"
3. Click "Browse Collections"
4. Your database structure:
   ```
   axl_game_bot/
   ├── users (player data)
   ├── game_history (all games)
   └── transactions (money transfers)
   ```

### Monitor Usage

- **Storage:** Free tier = 512MB
- **Concurrent connections:** Unlimited
- **Data transfer:** Unlimited between Koyeb and MongoDB

---

## 🔍 View Data in MongoDB

### Browse Collections

1. In MongoDB Atlas
2. Clusters → Browse Collections
3. Select database `axl_game_bot`
4. View collections:
   - `users` - All player accounts
   - `game_history` - Every slot game  
   - `transactions` - All transfers

### Example User Document

```json
{
  "_id": 987654321,
  "username": "playtester",
  "first_name": "John",
  "balance": 1500,
  "total_winnings": 5000,
  "total_losses": 3500,
  "games_played": 150,
  "last_bonus_time": 1708000000,
  "is_admin": 0,
  "is_banned": 0,
  "created_at": "2024-02-16T10:00:00Z",
  "updated_at": "2024-02-16T15:30:00Z"
}
```

---

## 🔄 MongoDB vs SQLite Comparison

### SQLite (Default)

**Pros:**
- ✅ No setup needed
- ✅ Works instantly
- ✅ No credit card needed
- ✅ Full data is yours

**Cons:**
- ❌ Data stored locally only
- ❌ Can't access from other services
- ❌ Manual backups

**Best for:** Quick testing, personal use

### MongoDB (Alternative)

**Pros:**
- ✅ Cloud backup automatic
- ✅ Access from anywhere
- ✅ Professional database
- ✅ Better for scaling

**Cons:**
- ❌ 5 minutes setup
- ❌ Slightly more complex

**Best for:** Production, team access, long-term

---

## 🛡️ Backup Your Data

### MongoDB Automatic Backup

MongoDB Atlas automatically backs up your data every 12 hours.

### Download Backup

1. MongoDB Atlas dashboard
2. Your cluster
3. Go to "Backup"
4. Click "..." next to latest backup
5. Select "Download"

### Export Data

1. MongoDB Atlas
2. Collections
3. Click "..." menu
4. "Export Collection"
5. Choose format (JSON)
6. Download

---

## 🚨 Troubleshooting

### Connection String Not Working

```
Error: Authentication failed
```

**Solutions:**
1. Verify username: `axlbot`
2. Verify password is correct (check MongoDB Atlas)
3. Check IP allowlist (should be "Anywhere")
4. In connection string, replace `<password>` with actual password

### Can't Connect to Database

```
Error: No module named 'pymongo'
```

**Solution:**
```bash
pip install pymongo
```

### Cluster Deployment Taking Too Long

- Can take 5-15 minutes
- Reload MongoDB Atlas page
- If still pending after 30 mins, create new cluster

### Data Not Saving

```
Error: Insert failed
```

**Check:**
1. Network access is "Anywhere"
2. User has `readWriteAnyDatabase` role
3. Cluster is running (M0 Free)
4. Connection string is correct

---

## 📋 MongoDB Checklist

- [ ] Created MongoDB Atlas account
- [ ] Created free M0 cluster
- [ ] Created database user (axlbot)
- [ ] Set password for user
- [ ] Allowed network access from anywhere
- [ ] Got connection string
- [ ] Replaced `<password>` in connection string
- [ ] Added MONGODB_URI to .env
- [ ] Tested bot locally
- [ ] Added MONGODB_URI to Koyeb
- [ ] Bot connected successfully

---

## 🎓 Learn More

- **MongoDB Docs:** [docs.mongodb.com](https://docs.mongodb.com)
- **Atlas Guide:** [mongodb.com/cloud/atlas/docs](https://mongodb.com/cloud/atlas/docs)
- **Python & MongoDB:** [pymongo.readthedocs.io](https://pymongo.readthedocs.io)

---

## 💾 Database Schema

### Users Collection

```
{
  user_id: Integer (Primary Key)
  username: String
  first_name: String
  balance: Float
  total_winnings: Float
  total_losses: Float
  games_played: Integer
  last_bonus_time: Integer
  is_admin: Boolean
  is_banned: Boolean
  created_at: DateTime
  updated_at: DateTime
}
```

### Game History Collection

```
{
  user_id: Integer
  game_type: String ("slots")
  bet_amount: Float
  result_amount: Float
  result_type: String ("win", "big_win", "jackpot", "loss")
  created_at: DateTime
}
```

### Transactions Collection

```
{
  sender_id: Integer
  receiver_id: Integer
  amount: Float
  created_at: DateTime
}
```

---

**MongoDB Atlas is the perfect free solution for cloud storage!**

Ready to deploy? See KOYEB_DEPLOYMENT.md
