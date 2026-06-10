"""
DSA Grind Bot — Entry point.
Loads all cogs, initializes the database, and starts the bot.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands
from aiohttp import web

from config import BOT_TOKEN, GUILD_ID
from database import init_db, close_db
from utils.fuzzy import load_problems
from backup import restore_from_github, backup_loop, BACKUP_INTERVAL_MINUTES

# ─── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("dsa_bot")

# ─── Bot Setup ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
)

# Guard against multiple on_ready fires (Discord reconnects)
_ready_done = False

# ─── Cogs to load ─────────────────────────────────────────────────
COGS = [
    "cogs.solve",
    "cogs.sheet",
    "cogs.progress",
    "cogs.leaderboard",
    "cogs.topic",
    "cogs.announcements",
    "cogs.guide",
]


@bot.event
async def on_ready():
    """Fired when bot connects to Discord."""
    global _ready_done

    log.info(f"Bot ready! Logged in as {bot.user} (ID: {bot.user.id})")

    if _ready_done:
        log.info("on_ready fired again (reconnect) — skipping init.")
        return

    _ready_done = True

    # Step 1: Restore database from GitHub backup if needed (on fresh deploy)
    restored = await restore_from_github()
    if restored:
        log.info("Database restored from GitHub backup.")

    # Step 2: Initialize database (creates tables if they don't exist)
    await init_db()
    log.info("Database initialized.")

    # Step 3: Load problem data into memory
    problems = load_problems()
    log.info(f"Loaded {len(problems)} problems from TUF sheet.")

    # Step 4: Sync slash commands
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        log.info(f"Synced {len(synced)} commands to guild {GUILD_ID}.")
    else:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} commands globally.")

    # Step 5: Start periodic backup loop
    # NOTE: We do NOT do an immediate backup on startup.
    # The old code would immediately backup a possibly-empty DB, overwriting
    # real user data on GitHub. The backup loop will only upload if the DB
    # actually contains user data (safety check in backup_to_github).
    asyncio.create_task(backup_loop())
    log.info(f"Backup loop started (every {BACKUP_INTERVAL_MINUTES} minutes).")

    log.info("Bot is fully operational! 🚀")


@bot.event
async def on_command_error(ctx, error):
    """Global error handler."""
    log.error(f"Command error: {error}", exc_info=error)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Global slash command error handler."""
    log.error(f"Slash command error: {error}", exc_info=error)

    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ Something went wrong. Please try again.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Something went wrong. Please try again.", ephemeral=True
        )


async def handle_ping(request):
    """Dummy endpoint for Render to keep the web service alive."""
    return web.Response(text="DSA Grind Bot is alive!")

async def web_server():
    """Start a tiny web server so Render doesn't kill the bot."""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"Web server started on port {port}")


async def main():
    """Main entry point."""
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set! Create a .env file with your bot token.")
        log.error("See .env.example for the required variables.")
        sys.exit(1)

    # Start the dummy web server
    asyncio.create_task(web_server())

    # Load all cogs
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                log.info(f"Loaded cog: {cog}")
            except Exception as e:
                log.error(f"Failed to load cog {cog}: {e}", exc_info=e)

        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot shutting down...")
    finally:
        # Ensure DB connection is closed
        asyncio.run(close_db())
