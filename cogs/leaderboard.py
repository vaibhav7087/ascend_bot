"""
Cog: /leaderboard (private) and /showleaderboard (public).
Dual-mode leaderboard — lurk quietly or flex publicly.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from database import get_leaderboard
from utils.embeds import leaderboard_embed


class LeaderboardCog(commands.Cog):
    """Leaderboard commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Check the leaderboard (only you see it)")
    async def leaderboard_private(self, interaction: discord.Interaction):
        """Private leaderboard — only you see it."""
        await interaction.response.defer(ephemeral=True)
        entries = await get_leaderboard()
        embed = leaderboard_embed(entries, title="🏆 Leaderboard (Private View)")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="showleaderboard", description="Show the leaderboard to everyone")
    async def leaderboard_public(self, interaction: discord.Interaction):
        """Public leaderboard — everyone sees it."""
        await interaction.response.defer()
        entries = await get_leaderboard()
        embed = leaderboard_embed(entries, title="🏆 Leaderboard")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))
