# 🧠 DSA Grind Bot — Discord Edition

A Discord bot that turns Striver's A2Z DSA Sheet (474 problems) into a competitive, gamified group study tracker. Track progress, earn XP, climb tiers, maintain streaks, and flex on your friends.

---

## ✨ Features

### 📊 474-Problem Sheet (Striver's A2Z)
- Full **Striver's A2Z DSA Sheet** with all 474 problems pre-loaded
- **Easy (152)** · **Medium (186)** · **Hard (136)** across 19 topics
- Browse interactively by **topic**, **difficulty**, or **unsolved only**
- Every problem name is TUF + LeetCode compatible

### 🏆 XP + Tier Gamification
| Action | XP Earned |
|--------|-----------|
| Solve Easy problem | +10 XP |
| Solve Medium problem | +25 XP |
| Solve Hard problem | +50 XP |
| Clear a full topic | +100 XP bonus |
| 7-day streak | +75 XP bonus |
| 14-day streak | +100 XP bonus |
| 30-day streak | +200 XP bonus |

**Tier Progression:**
| Tier | XP Required |
|------|-------------|
| 🪨 Noob | 0 |
| 🥉 Bronze | 500 |
| 🥈 Silver | 1,500 |
| 🥇 Gold | 3,500 |
| 💎 Platinum | 7,000 |
| 👑 Diamond | 12,000 |

### 🔥 Streak Tracking
- Tracks consecutive days of solving at least one problem
- Public announcements at 7, 14, 30, 60, and 100 day milestones

### 📢 Public Announcements
Auto-posted in a dedicated channel when someone:
- 🎯 **Clears a full topic** → *"Ravi just cleared Arrays! 🔥 +100 XP"*
- 🔥 **Hits a streak milestone** → *"Ravi is on a 7-day streak! +75 XP"*
- ⬆️ **Upgrades tier** → *"Ravi just hit Gold tier! 🥇"*

### 🔍 Fuzzy Problem Matching
Type problem names however you want — the bot figures it out:
- `"two sum"` → `two-sum` ✅
- `"twosum"` → `two-sum` ✅
- `"Two Sum"` → `two-sum` ✅
- `"kadanes algorithm"` → `kadanes-algorithm` ✅
- Ambiguous matches get a confirmation prompt before logging

---

## 🤖 Commands

### Public Commands (everyone sees)
| Command | Description |
|---------|-------------|
| `/solved <problem>` | Log a solved problem, earn XP |
| `/whosolved <problem>` | See who solved a specific problem |
| `/showleaderboard` | Show the leaderboard publicly |

### Private Commands (only you see)
| Command | Description |
|---------|-------------|
| `/sheet` | Interactive menu — browse by topic/difficulty/unsolved |
| `/progress` | Your full profile card — XP, tier, streak, stats |
| `/streak [@user]` | Check streak (yours or someone's) |
| `/leaderboard` | Check rankings quietly |
| `/topic <name>` | View unsolved problems in a specific topic |

---

## 📂 Topics (19 Categories)

| # | Topic | Problems |
|---|-------|----------|
| 1 | Learn the Basics | 54 |
| 2 | Sorting Techniques | 7 |
| 3 | Arrays | 40 |
| 4 | Binary Search | 32 |
| 5 | Strings (Basic/Medium) | 15 |
| 6 | Linked Lists | 31 |
| 7 | Recursion | 25 |
| 8 | Bit Manipulation | 18 |
| 9 | Stack and Queues | 30 |
| 10 | Sliding Window & Two Pointer | 12 |
| 11 | Heaps | 17 |
| 12 | Greedy Algorithms | 15 |
| 13 | Binary Trees | 38 |
| 14 | Binary Search Trees | 16 |
| 15 | Graphs | 53 |
| 16 | Dynamic Programming | 55 |
| 17 | Tries | 7 |
| 18 | Strings (Hard) | 9 |

---

## 🛠 Tech Stack

- **Language**: Python 3.11+
- **Discord Library**: [discord.py](https://discordpy.readthedocs.io/) v2.x (slash commands)
- **Database**: SQLite via [aiosqlite](https://aiosqlite.omnilib.dev/) (async, zero config)
- **Fuzzy Matching**: `difflib.get_close_matches` (stdlib — no extra deps)
- **Environment**: `python-dotenv`

---

## 📁 Project Structure

```
discord_dsa/
├── bot.py                  # Entry point
├── config.py               # Constants, XP/tier config
├── database.py             # SQLite schema + queries
├── models.py               # Dataclasses
├── cogs/
│   ├── solve.py            # /solved, /whosolved
│   ├── sheet.py            # /sheet (interactive menu)
│   ├── progress.py         # /progress, /streak
│   ├── leaderboard.py      # /leaderboard, /showleaderboard
│   ├── topic.py            # /topic <name>
│   └── announcements.py    # Auto milestone posts
├── utils/
│   ├── fuzzy.py            # Problem name matching
│   ├── xp.py               # XP engine
│   ├── embeds.py           # Discord embed builders
│   └── pagination.py       # Paginated views
├── data/
│   └── tuf_problems.json   # 474 problems (pre-extracted)
├── .env                    # Your secrets
├── .gitignore
└── requirements.txt
```

---

## 🚀 Local Setup (Development)

### 1. Create Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. **New Application** → name it (e.g., "DSA Grind Bot")
3. Go to **Bot** tab → click **Reset Token** → **Copy** the token
4. Enable these **Privileged Gateway Intents**:
   - ✅ `MESSAGE CONTENT INTENT`
   - ✅ `SERVER MEMBERS INTENT`
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`, `Read Message History`
6. Copy the generated URL → paste in browser → invite bot to your server
7. **Get your Server ID**: Enable Developer Mode (Settings → Advanced → Developer Mode), then right-click your server → **Copy Server ID**
8. **Get Announcements Channel ID**: Right-click the channel → **Copy Channel ID**

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your values:
```env
BOT_TOKEN=your_discord_bot_token_here
GUILD_ID=your_server_id
ANNOUNCE_CHANNEL_ID=your_channel_id
```

### 3. Install & Run
```bash
pip install -r requirements.txt
python bot.py
```

---

## ☁️ Free Hosting Guide (24/7 Uptime)

### Option 1: Oracle Cloud Free Tier ⭐ RECOMMENDED
**Why**: Truly free forever (not a trial), gives you a full VM with great uptime. Most reliable free option.

**What you get free**: 2 AMD VMs (1 GB RAM each) or 1 ARM VM (4 cores, 24 GB RAM) — **always free, no credit card charges ever**.

#### Setup Steps:
```bash
# 1. Sign up at https://cloud.oracle.com (free tier)
# 2. Create a Compute Instance:
#    - Shape: VM.Standard.E2.1.Micro (Always Free)
#    - OS: Ubuntu 22.04 (or latest)
#    - Download your SSH key during creation

# 3. SSH into your VM
ssh -i ~/your-key.key ubuntu@<your-vm-ip>

# 4. Install Python
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 5. Clone your repo
git clone https://github.com/yourusername/discord_dsa.git
cd discord_dsa

# 6. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Create .env file
cp .env.example .env
nano .env  # paste your bot token, guild ID, channel ID

# 8. Run with systemd (auto-restarts on crash + starts on boot)
sudo nano /etc/systemd/system/dsa-bot.service
```

Paste this into the systemd service file:
```ini
[Unit]
Description=DSA Grind Discord Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/discord_dsa
ExecStart=/home/ubuntu/discord_dsa/venv/bin/python bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/discord_dsa/.env

[Install]
WantedBy=multi-user.target
```

```bash
# 9. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable dsa-bot
sudo systemctl start dsa-bot

# 10. Check status
sudo systemctl status dsa-bot

# View logs
journalctl -u dsa-bot -f
```

> ✅ **Result**: Bot runs 24/7, auto-restarts on crash, auto-starts on reboot. **100% free forever.**

---

### Option 2: Railway.app (Easy Deploy)
**Why**: Dead-simple GitHub deploy, no SSH needed. Free tier gives 500 hours/month (enough for a small bot if managed).

> ⚠️ Railway's free tier has limits. For 24/7 uptime, you may need their $5/month Hobby plan eventually. But to start it's great.

```bash
# 1. Push your code to GitHub
git init && git add . && git commit -m "initial"
git remote add origin https://github.com/you/discord_dsa.git
git push -u origin main

# 2. Go to https://railway.app → New Project → Deploy from GitHub
# 3. Add environment variables in Railway dashboard:
#    BOT_TOKEN, GUILD_ID, ANNOUNCE_CHANNEL_ID
# 4. Set Start Command: python bot.py
# 5. Deploy!
```

---

### Option 3: Render.com (Free Background Worker)
**Why**: Free tier includes a background worker (not a web server), perfect for Discord bots.

> ⚠️ Render free tier spins down after inactivity. For a Discord bot, use their **Background Worker** type which stays running.

```bash
# 1. Push to GitHub
# 2. Go to https://render.com → New → Background Worker
# 3. Connect your GitHub repo
# 4. Runtime: Python 3
# 5. Build Command: pip install -r requirements.txt
# 6. Start Command: python bot.py
# 7. Add environment variables in dashboard
```

---

## 💾 Database Backup System

Your data (`dsa_bot.db`) is the single most important file. Here's how to protect it.

### Automated Cloud Backup (to GitHub — Free)

Create a backup script on your server:

```bash
nano ~/backup_dsa.sh
```

```bash
#!/bin/bash
# backup_dsa.sh — Backs up the SQLite database to a private GitHub repo

BACKUP_DIR="/home/ubuntu/dsa_backups"
DB_PATH="/home/ubuntu/discord_dsa/dsa_bot.db"
DATE=$(date +%Y-%m-%d_%H-%M)

mkdir -p "$BACKUP_DIR"

# Copy database (safe copy while bot is running)
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/dsa_bot_$DATE.db'"

# Also keep a "latest" copy
cp "$BACKUP_DIR/dsa_bot_$DATE.db" "$BACKUP_DIR/dsa_bot_latest.db"

# Push to private GitHub repo
cd "$BACKUP_DIR"
git add -A
git commit -m "Backup $DATE"
git push origin main

# Clean up old local backups (keep last 7)
ls -t "$BACKUP_DIR"/dsa_bot_2*.db | tail -n +8 | xargs rm -f 2>/dev/null

echo "✅ Backup complete: $DATE"
```

```bash
chmod +x ~/backup_dsa.sh
```

#### Set up the private backup repo:
```bash
# 1. Create a PRIVATE repo on GitHub (e.g., "dsa-bot-backups")
# 2. Set it up locally:
mkdir -p ~/dsa_backups && cd ~/dsa_backups
git init
git remote add origin https://github.com/you/dsa-bot-backups.git
git branch -M main

# First push
touch .gitkeep && git add . && git commit -m "init" && git push -u origin main
```

#### Schedule daily automatic backups (cron):
```bash
crontab -e
```
Add this line (runs every day at 3 AM IST):
```
30 21 * * * /home/ubuntu/backup_dsa.sh >> /home/ubuntu/backup.log 2>&1
```
> (21:30 UTC = 3:00 AM IST)

---

### Scheduled Backup to Your Local Machine

Pull backups from the cloud to your local Windows machine:

#### Option A: Git Pull (Easiest)
Since backups are pushed to GitHub, just clone/pull on your local machine:
```powershell
# One-time setup
git clone https://github.com/you/dsa-bot-backups.git C:\Users\Vaibhav\dsa_backups

# Whenever you want the latest backup
cd C:\Users\Vaibhav\dsa_backups
git pull
```

You can schedule this with Windows Task Scheduler:
1. Open **Task Scheduler** → Create Basic Task
2. Trigger: Daily (or Weekly)
3. Action: Start a Program
   - Program: `git`
   - Arguments: `-C C:\Users\Vaibhav\dsa_backups pull`
4. Done — your local machine auto-pulls the latest backup

#### Option B: SCP Direct Download (if using Oracle/VPS)
```powershell
# Download latest backup directly from server
scp -i ~\.ssh\oracle_key ubuntu@<your-vm-ip>:/home/ubuntu/discord_dsa/dsa_bot.db C:\Users\Vaibhav\dsa_backups\dsa_bot_%date%.db
```

Schedule this in Task Scheduler too for automatic pulls.

---

### Backup Summary

| What | Where | How Often | Cost |
|------|-------|-----------|------|
| Live database | Oracle Cloud VM | Always running | Free |
| Cloud backup | Private GitHub repo | Daily (cron) | Free |
| Local backup | Your Windows PC | Daily/Weekly (Task Scheduler) | Free |

> **3 copies of your data** (server + GitHub + local) = you'll never lose progress.

---

## 📊 Database

SQLite database (`dsa_bot.db`) created automatically on first run. Tables:

| Table | Purpose |
|-------|---------|
| `users` | Discord user profiles, XP, tier, streak |
| `solves` | Problem solve records (user × problem, unique constraint) |
| `announcements` | Prevents duplicate milestone posts |

### Manual Database Inspection
```bash
# On the server
sqlite3 dsa_bot.db

# Useful queries:
.tables
SELECT * FROM users ORDER BY xp DESC;
SELECT COUNT(*) FROM solves;
SELECT username, xp, tier, current_streak FROM users ORDER BY xp DESC LIMIT 10;
```

---

## 🔧 Bot Management Commands (on your server)

```bash
# Check if bot is running
sudo systemctl status dsa-bot

# Restart the bot
sudo systemctl restart dsa-bot

# View live logs
journalctl -u dsa-bot -f

# Stop the bot
sudo systemctl stop dsa-bot

# Update the bot (pull latest code)
cd ~/discord_dsa
git pull
sudo systemctl restart dsa-bot
```

---

## 🆘 Troubleshooting

| Issue | Fix |
|-------|-----|
| Bot doesn't respond to slash commands | Run `sudo systemctl restart dsa-bot`. Commands may take up to 1 hour to sync globally (instant for guild-specific). |
| "BOT_TOKEN not set" error | Check your `.env` file exists and has the correct token. |
| Bot goes offline after SSH disconnect | Make sure you're using `systemd` (step 8), not running directly in terminal. |
| Database locked errors | The WAL journal mode handles this, but restart the bot if persistent. |
| Slash commands show in wrong server | Set `GUILD_ID` in `.env` to your specific server. |

---

## 🤝 Contributing

This is a private study group bot. Fork and adapt for your own group!

---

## 📜 Credits

- Problem data from [Striver's A2Z DSA Sheet](https://takeuforward.org/dsa/strivers-a2z-sheet-learn-dsa-a-to-z) by takeUforward
- Built with [discord.py](https://github.com/Rapptz/discord.py)
