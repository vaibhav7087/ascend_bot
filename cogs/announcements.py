"""
Cog: Automatic public milestone announcements.
Not a slash command — posts to a designated channel when milestones are hit.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from database import has_been_announced, log_announcement
from utils.embeds import (
    announce_topic_clear_embed,
    announce_streak_embed,
    announce_tier_upgrade_embed,
)
from config import ANNOUNCE_CHANNEL_ID


class AnnouncementsCog(commands.Cog):
    """Handles posting public milestone announcements."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_channel(self) -> discord.TextChannel | None:
        """Get the announcements channel."""
        if ANNOUNCE_CHANNEL_ID == 0:
            return None
        return self.bot.get_channel(ANNOUNCE_CHANNEL_ID)

    async def send_topic_clear(
        self, user: discord.User | discord.Member, topic: str, xp_bonus: int
    ):
        """Announce topic clear in the designated channel."""
        channel = self._get_channel()
        if channel is None:
            return

        # Prevent duplicate announcements
        if await has_been_announced(user.id, "topic_clear", topic):
            return

        embed = announce_topic_clear_embed(user, topic, xp_bonus)
        await channel.send(embed=embed)
        await log_announcement(user.id, "topic_clear", topic)

    async def send_streak_milestone(
        self, user: discord.User | discord.Member, days: int, xp_bonus: int
    ):
        """Announce streak milestone."""
        channel = self._get_channel()
        if channel is None:
            return

        detail = f"{days}-day"
        if await has_been_announced(user.id, "streak", detail):
            return

        embed = announce_streak_embed(user, days, xp_bonus)
        await channel.send(embed=embed)
        await log_announcement(user.id, "streak", detail)

    async def send_tier_upgrade(
        self, user: discord.User | discord.Member, new_tier: str
    ):
        """Announce tier upgrade."""
        channel = self._get_channel()
        if channel is None:
            return

        if await has_been_announced(user.id, "tier_upgrade", new_tier):
            return

        embed = announce_tier_upgrade_embed(user, new_tier)
        await channel.send(embed=embed)
        await log_announcement(user.id, "tier_upgrade", new_tier)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnnouncementsCog(bot))
