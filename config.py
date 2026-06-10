"""
Configuration constants for the DSA Discord Bot.
XP rewards, tier thresholds, streak milestones, and environment loading.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Discord Config ───────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID", "0"))

# ─── XP Rewards ───────────────────────────────────────────────────
XP_EASY = 10
XP_MEDIUM = 25
XP_HARD = 50
XP_TOPIC_CLEAR = 100

# ─── Streak Bonuses ───────────────────────────────────────────────
STREAK_BONUSES = {
    7: 75,
    14: 100,
    30: 200,
    60: 350,
    100: 500,
}

# Milestones that trigger public announcements
STREAK_MILESTONES = list(STREAK_BONUSES.keys())

# ─── Tier Thresholds (ordered low → high) ─────────────────────────
TIERS = [
    ("🪨 Noob", 0),
    ("🥉 Bronze", 500),
    ("🥈 Silver", 1500),
    ("🥇 Gold", 3500),
    ("💎 Platinum", 7000),
    ("👑 Diamond", 12000),
]

# ─── Timezone ──────────────────────────────────────────────────────
TIMEZONE = "Asia/Kolkata"

# ─── Database ──────────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "dsa_bot.db")

# ─── Data Path ─────────────────────────────────────────────────────
import pathlib
DATA_DIR = pathlib.Path(__file__).parent / "data"
PROBLEMS_JSON = DATA_DIR / "tuf_problems.json"

# ─── Embed Colors ─────────────────────────────────────────────────
COLOR_SUCCESS = 0x2ECC71   # Green
COLOR_INFO = 0x3498DB      # Blue
COLOR_WARNING = 0xF39C12   # Orange
COLOR_ERROR = 0xE74C3C     # Red
COLOR_XP = 0x9B59B6        # Purple
COLOR_GOLD = 0xF1C40F      # Gold
COLOR_STREAK = 0xE67E22    # Fire orange
COLOR_ANNOUNCE = 0x1ABC9C  # Teal
