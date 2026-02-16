# 🔑 Owner Setup Guide - Quick Start

Complete guide to set up yourself as the owner of AXL GAME BOT.

## ⚡ 3-Step Owner Setup

### Step 1: Get Your Telegram User ID

1. Open Telegram
2. Search for `@userinfobot`
3. Send `/start`
4. You'll see your **User ID** (large number like `987654321`)
5. **Copy this number!**

### Step 2: Set OWNER_ID

#### Local Testing
Edit `.env` file:
```
TELEGRAM_TOKEN=your_bot_token
OWNER_ID=987654321
```

#### On Koyeb
1. Go to [koyeb.com/apps](https://koyeb.com/apps)
2. Click your service "axl-game-bot"
3. Go to "Settings" → "Environment Variables"
4. Update `OWNER_ID=987654321` with your ID
5. Restart service

### Step 3: Verify You're Owner

In Telegram, send to your bot:
```
/admin
```

You should see the full **OWNER** panel showing all commands!

---

## 🎮 Owner Commands Reference

### Check Admin Panel
```
/admin
```
Shows your status and all available commands

### Give Unlimited Balance to Player
```
/grant 123456789 5000
```
Gives User ID 123456789 → 5000∆

### Make Someone an Admin
```
/setadmin 123456789
```
User 123456789 becomes admin with these powers:
- ✓ Unlimited bets
- ✓ Give balance to players
- ✓ View admin panel

### Ban a Player
```
/ban 123456789
```
Prevents User 123456789 from playing
- Can't use `/slots`
- Can still check `/balance`

### Unban a Player
```
/unban 123456789
```
Lets previously banned player play again

---

## 🛡️ Owner Hierarchy

### Owner (You)
- All permissions
- Unlimited bets
- Ban/unban users
- Promote admins
- Grant balance
- View admin panel

### Admin
- Unlimited bets
- Grant balance to players
- View admin panel
- **Cannot:** Ban, unban, or promote other admins

### Regular Users
- Limited bets (10∆ - 10,000∆)
- Can play normally
- Can be banned

---

## 💡 Common Owner Tasks

### Task: Give Welcome Bonus to New Player

```
/grant 123456789 1000
```

Result: Player gets 1000∆ bonus balance

### Task: Promote Friend to Admin

```
/setadmin 987654321
```

Then they can:
- Use `/admin` command
- Use `/grant` commands
- Play with unlimited bets

### Task: Stop Spam Player

```
/ban 555666777
```

They'll get error: "🚫 You have been banned from the game!"

### Task: Check Bot Status

```
/admin
```

Shows:
- Your balance
- Total wins/losses
- Available commands
- Admin status

---

## 🚀 Go Live with Koyeb

Once you set OWNER_ID:

1. **Local:** Test with `/admin` command
2. **On Koyeb:** Push to GitHub, auto-deploys in 1 minute
3. **Verify:** Test bot commands in Telegram
4. **Share:** Invite friends to `@vfriendschat`

---

## 📱 Add Bot to Your Group

1. Your group name: `@vfriendschat`
2. Add bot: Search bot username → "Add to Chat"
3. Select group → "OK"
4. Users can play directly in group

### Set Bot as Admin (Optional)
1. Right-click bot in group
2. "Promote to Admin"
3. Give basic permissions

---

## 🎁 Sample Scenarios

### Scenario 1: Welcome Tournament

```
/grant 111111111 500
/grant 222222222 500
/grant 333333333 500
```

Give 500∆ to each player to start tournament

### Scenario 2: Add Helper Admin

```
/setadmin 444444444
```

Now they can also give balance and help manage

### Scenario 3: Ban Cheater

```
/ban 999999999
```

They can't play anymore. Unban with:
```
/unban 999999999
```

### Scenario 4: Premium Member

```
/grant 555555555 10000
```

Give premium player 10,000∆ with unlimited bets

---

## ❓ FAQ

**Q: Can I change OWNER_ID later?**
A: Yes, just update .env and restart bot

**Q: What if I forget my User ID?**
A: Message @userinfobot and it will tell you

**Q: Can admins ban players?**
A: No, only owner can /ban

**Q: Can I make multiple owners?**
A: No, only 1 OWNER_ID. Use admins for others

**Q: What does infinite bet mean?**
A: Owner/Admin can bet any amount (no 10-10,000 limit)

---

## ✅ Owner Checklist

- [ ] Get Telegram User ID from @userinfobot
- [ ] Set OWNER_ID in .env
- [ ] Test `/admin` command works
- [ ] Deploy to Koyeb
- [ ] Update OWNER_ID on Koyeb
- [ ] Test `/admin` on live bot
- [ ] Promote admins with `/setadmin`
- [ ] Give balance with `/grant`
- [ ] Share bot with friends
- [ ] Monitor logs in Koyeb

---

## 🔒 Security Tips

✓ Never share your User ID with untrusted people  
✓ Keep your token secure (.env in .gitignore)  
✓ Ban players who spam/cheat  
✓ Only promote trusted friends as admin  
✓ Backup database from MongoDB regularly  

---

## 📞 Need Help?

1. **Bot not responding?**
   - Check Koyeb logs
   - Verify OWNER_ID is set
   - Restart service

2. **Admin commands don't work?**
   - Make sure OWNER_ID matches your User ID
   - Restart bot
   - Try again

3. **MongoDB issues?**
   - See KOYEB_DEPLOYMENT.md
   - Check connection string
   - Verify network access

---

**Ready to own your gaming empire!** 👑

Next: Read KOYEB_DEPLOYMENT.md to go live
