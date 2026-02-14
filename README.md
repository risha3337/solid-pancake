# 🎬 CINEFLIX ULTIMATE BOT

**Production-Ready Video Bot with Full Admin Panel**

---

## ✨ Premium Features

### 🎯 For Users:
- ✅ Clean Bangla + English UI
- ✅ Force Join System (unlimited channels)
- ✅ Video Protection (cannot forward/save)
- ✅ Mini App Integration
- ✅ Fast & Reliable

### 🔧 For Admin:
- ✅ **Complete Admin Panel** — control everything from Telegram
- ✅ **Message Editor** — customize all messages
- ✅ **Channel Manager** — add/remove force join channels
- ✅ **Settings Panel** — change Mini App URL, channels, etc.
- ✅ **Statistics** — track users, videos, views
- ✅ **MongoDB Storage** — no data loss on restart
- ✅ **Batch Upload Support** — multiple videos at once

---

## 🚀 Quick Deploy to Railway

### Step 1: MongoDB Setup (5 minutes)

1. Go to: **https://www.mongodb.com/cloud/atlas**
2. Sign up (FREE)
3. Create Cluster:
   - Click "Build a Cluster"
   - Choose **M0 FREE** tier
   - Select region (Singapore/Mumbai)
   - Click "Create Cluster"

4. Create Database User:
   - Database Access → Add New User
   - Username: `cineflix_admin`
   - Password: (Autogenerate) — **SAVE THIS!**
   - Privileges: "Read and write to any database"

5. Whitelist IP:
   - Network Access → Add IP Address
   - "Allow Access from Anywhere" (0.0.0.0/0)
   - Confirm

6. Get Connection String:
   - Database → Connect → "Connect your application"
   - Copy the string
   - Replace `<password>` with your password
   - Add `/cineflix_bot` before `?retryWrites`
   
   **Final format:**
   ```
   mongodb+srv://cineflix_admin:YourPassword@cluster0.xxxxx.mongodb.net/cineflix_bot?retryWrites=true&w=majority
   ```

### Step 2: Deploy to Railway

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "CINEFLIX Ultimate Bot"
   git remote add origin https://github.com/YOUR_USERNAME/cineflix-bot.git
   git push -u origin main
   ```

2. **Railway Deploy:**
   - Go to: **https://railway.app**
   - Sign in with GitHub
   - New Project → "Deploy from GitHub repo"
   - Select your repository

3. **Set Environment Variables:**
   
   Click on your project → Variables → Add these:

   ```
   BOT_TOKEN=your_bot_token_from_botfather
   
   MONGO_URI=mongodb+srv://cineflix_admin:YourPassword@cluster0.xxxxx.mongodb.net/cineflix_bot?retryWrites=true&w=majority
   
   ADMIN_ID=your_telegram_user_id
   ```

   ⚠️ **IMPORTANT:** 
   - Replace `YourPassword` with your actual MongoDB password
   - Don't add spaces
   - Check for typos

4. **Deploy:**
   - Railway will auto-deploy
   - Wait 2-3 minutes
   - Check logs for: `✅ CINEFLIX Ultimate Bot is running!`

5. **Done!** 🎉

---

## 🎮 How to Use

### For Users:

1. `/start` → Opens Mini App
2. Click video → Bot opens
3. Join channels → Get video

### For Admin (You):

#### 1️⃣ Open Admin Panel:
```
/admin
```

You'll see:
```
🔧 CINEFLIX ADMIN PANEL

📊 Statistics:
👥 Users: 0
📹 Videos: 0
🔒 Force Join: 0

[📺 Channel Manager] [📝 Edit Messages]
[⚙️ Settings]        [📊 Statistics]
[🔄 Refresh]         [❌ Close]
```

#### 2️⃣ Add Force Join Channel:

1. Click "📺 Channel Manager"
2. Click "➕ Add New Channel"
3. Send: `-1001234567890 MyChannel`
4. Done! ✅

#### 3️⃣ Edit Messages:

1. Click "📝 Edit Messages"
2. Select message to edit
3. Send new text
4. Done! All users will see new message

#### 4️⃣ Change Settings:

1. Click "⚙️ Settings"
2. Select what to change:
   - 🎮 Mini App URL
   - 📢 Main Channel
   - 🔒 Video Protection (ON/OFF)
   - 🤖 Bot Name

#### 5️⃣ Upload Videos:

- Upload video to channel
- Bot auto-saves
- You get message ID
- Use in Mini App!

**Batch Upload:**
- Upload 10 videos at once
- Get all 10 IDs
- No ID missed!

---

## 📊 Admin Panel Features

### 📺 Channel Manager:
```
📺 Channel Manager

📢 @Channel1        [❌ Remove]
📢 @Channel2        [❌ Remove]
📢 @Channel3        [❌ Remove]

[➕ Add New Channel]
[🔙 Back]
```

### 📝 Message Editor:
```
📝 Message Editor

[✏️ Welcome Message]
[✏️ Help Message]
[✏️ Force Join Message]
[✏️ After Video Message]
[✏️ Video Not Found Message]

[🔙 Back]
```

### ⚙️ Settings:
```
⚙️ Settings

[🎮 Mini App URL]
[📢 Main Channel]
[🔒 Video Protection]
[🤖 Bot Name]

[🔙 Back]
```

---

## 🔒 Security Features

✅ **Bot Token** → Environment variable (not in code)
✅ **Admin ID** → Environment variable (not in code)
✅ **MongoDB URI** → Environment variable (not in code)
✅ **Admin-only commands** → Verified by user ID
✅ **Video Protection** → Cannot forward/save

---

## 📁 File Structure

```
cineflix-ultimate-bot/
├── bot.py              # Main bot (production-ready)
├── requirements.txt    # Dependencies
├── Procfile           # Railway config
├── runtime.txt        # Python version
├── .gitignore         # Git ignore
└── README.md          # This file
```

---

## ⚠️ Important Notes

### 🔐 SECURITY WARNING:
**NEVER commit your actual tokens to GitHub!**
- Use the `.env.example` file as a template
- Set actual values only in Railway's environment variables
- Keep your `BOT_TOKEN` and `MONGO_URI` secret

### ✅ Environment Variables (Railway):

Must set these 3 variables:
```
BOT_TOKEN    → Your bot token
MONGO_URI    → MongoDB connection string
ADMIN_ID     → Your Telegram user ID
```

**How to get your Telegram ID:**
- Message @userinfobot on Telegram
- It will send your ID

### ✅ MongoDB:

- **Free tier:** 512 MB storage (enough!)
- **Connection string:** Must be correct
- **Password:** No special characters (or URL encode)
- **Whitelist IP:** Must be 0.0.0.0/0

### ✅ Railway:

- **Free tier:** $5/month credit (enough for this bot)
- **Logs:** Check logs if bot doesn't start
- **Variables:** Set all 3 variables correctly
- **Deploy:** Auto-deploys on push to GitHub

---

## 🆘 Troubleshooting

### Bot doesn't start?

**Check logs on Railway:**

1. If you see:
   ```
   ❌ ERROR: BOT_TOKEN environment variable not set!
   ```
   → Set BOT_TOKEN in Railway variables

2. If you see:
   ```
   ❌ MongoDB Connection Failed
   ```
   → Check MONGO_URI is correct
   → Check MongoDB IP whitelist (0.0.0.0/0)
   → Check password in connection string

3. If you see:
   ```
   ❌ ERROR: ADMIN_ID must be a number!
   ```
   → Make sure ADMIN_ID is just the number (no quotes)

### Admin panel not working?

- Make sure ADMIN_ID matches your Telegram ID
- Check with @userinfobot to confirm your ID

### Videos not saving?

- Make sure bot is admin in channel
- Check MongoDB is connected (logs should show ✅)
- Upload video again

---

## 📊 MongoDB Collections

The bot creates these collections automatically:

```
cineflix_bot/
├── videos              # All videos
├── channels            # Channel info
├── force_join_channels # Force join list
├── users               # User data
├── settings            # Bot settings
└── messages            # Message templates
```

---

## 🎯 Customization Examples

### Change Welcome Message:

1. `/admin`
2. "📝 Edit Messages"
3. "✏️ Welcome Message"
4. Send your new text:
   ```
   🎬 Welcome to MY BOT!
   
   Your custom text here...
   ```
5. Done! ✅

### Add Multiple Channels:

```
/admin
→ Channel Manager
→ Add New Channel

First channel:
-1001111111111 Channel1

→ Add New Channel

Second channel:
-1002222222222 Channel2

Now users must join BOTH!
```

### Change Mini App URL:

```
/admin
→ Settings
→ Mini App URL

Send new URL:
https://my-new-app.vercel.app/

Done!
```

---

## 💡 Pro Tips

1. **Backup MongoDB:**
   - MongoDB Atlas auto-backups (free tier too!)

2. **Monitor Logs:**
   - Railway dashboard → Logs
   - Watch for errors

3. **Test Before Deploy:**
   - Test locally first (optional)
   - Then deploy to Railway

4. **Update Bot:**
   - Edit code
   - `git push`
   - Railway auto-deploys!

---

## 📞 Support

- **Issues:** Create GitHub issue
- **Questions:** Check Railway logs first

---

## 📄 License

MIT License - Free to use and modify

---

**Made with ❤️ for CINEFLIX**  
🎬 Ultimate Video Bot Experience  
💾 MongoDB Powered | 🚀 Railway Deployed | 🔒 Secure | 🎨 Customizable

---

## ✅ Final Checklist

Before deploy, make sure:

- [ ] MongoDB cluster created
- [ ] Database user created
- [ ] IP whitelisted (0.0.0.0/0)
- [ ] Connection string copied
- [ ] Pushed to GitHub
- [ ] Railway project created
- [ ] All 3 environment variables set:
  - [ ] BOT_TOKEN
  - [ ] MONGO_URI
  - [ ] ADMIN_ID
- [ ] Deployment successful
- [ ] Logs show: ✅ Bot running
- [ ] Tested `/start` command
- [ ] Tested `/admin` command

**All done? Enjoy your bot! 🎉**
