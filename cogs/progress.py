"""
Cog: /progress and /streak commands.
Personal stats — always ephemeral.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from database import get_or_create_user, get_user_profile_data, get_solve_counts, get_user_category_solves
from utils.fuzzy import get_categories
from utils.embeds import profile_embed, streak_embed
from utils.xp import resolve_tier
from models import UserProfile


class ProgressCog(commands.Cog):
    """Personal progress and streak commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="progress", description="View your full profile — XP, tier, streak, stats")
    async def progress(self, interaction: discord.Interaction):
        """Full profile card — PRIVATE."""
        await interaction.response.defer(ephemeral=True)

        user = interaction.user
        await get_or_create_user(user.id, user.display_name)
        data = await get_user_profile_data(user.id)
        counts = await get_solve_counts(user.id)

        # Check which topics are fully cleared
        topics_cleared = []
        categories = get_categories()
        for cat_name, cat_problems in categories.items():
            cat_slugs = {p.slug for p in cat_problems}
            user_solved = await get_user_category_solves(user.id, cat_name)
            if cat_slugs.issubset(user_solved) and len(cat_slugs) > 0:
                topics_cleared.append(cat_name)

        profile = UserProfile(
            user_id=user.id,
            username=user.display_name,
            xp=data["xp"],
            tier=data["tier"],
            current_streak=data["current_streak"],
            longest_streak=data["longest_streak"],
            last_solve_date=data["last_solve_date"],
            total_solved=counts["Easy"] + counts["Medium"] + counts["Hard"],
            easy_solved=counts["Easy"],
            medium_solved=counts["Medium"],
            hard_solved=counts["Hard"],
            topics_cleared=topics_cleared,
        )

        embed = profile_embed(user, profile)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="streak", description="Check your streak or someone else's")
    @app_commands.describe(user="User to check streak for (optional)")
    async def streak(self, interaction: discord.Interaction, user: discord.User | None = None):
        """Streak info — PRIVATE."""
        target = user or interaction.user

        await get_or_create_user(target.id, target.display_name)
        data = await get_user_profile_data(target.id)

        if data is None:
            await interaction.response.send_message(
                "❌ This user hasn't solved any problems yet.", ephemeral=True
            )
            return

        embed = streak_embed(
            target,
            current=data["current_streak"],
            longest=data["longest_streak"],
            last_date=data["last_solve_date"],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProgressCog(bot))
