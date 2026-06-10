"""
Cog: /guide — Comprehensive introduction to Astra and the DSA Grind.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config import (
    COLOR_INFO, COLOR_GOLD, COLOR_STREAK, COLOR_SUCCESS,
    XP_EASY, XP_MEDIUM, XP_HARD, XP_TOPIC_CLEAR,
    STREAK_BONUSES, TIERS
)


class GuideCog(commands.Cog):
    """Guide and introductory commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="guide", description="Learn how to use Astra, view Tiers, Streaks, and XP.")
    async def guide(self, interaction: discord.Interaction):
        """Send the comprehensive guide as multiple embeds."""
        
        # Embed 1: Introduction & Commands
        intro_embed = discord.Embed(
            title="🌟 Welcome to Astra - The DSA Tracker",
            description="Astra helps you stay consistent with your DSA grind by tracking your problem-solving, maintaining daily streaks, and leveling you up as you progress through the **Striver's A2Z DSA Sheet**.",
            color=COLOR_INFO,
        )
        intro_embed.add_field(
            name="🛠️ Core Commands",
            value=(
                "**`/solved <problem>`** — Log a problem you just solved! (Start typing to search)\n"
                "**`/sheet`** — Browse the entire A2Z sheet interactively.\n"
                "**`/topic <name>`** — See your progress in a specific topic (e.g. `arrays`).\n"
                "**`/progress`** — View your personal stats, XP, and current tier.\n"
                "**`/streak`** — Check your daily solving streak.\n"
                "**`/leaderboard`** — See who's at the top of the server.\n"
                "**`/whosolved <problem>`** — See which of your friends have solved a specific problem."
            ),
            inline=False
        )

        # Embed 2: XP System & Tiers
        xp_embed = discord.Embed(
            title="🏆 XP System & Tiers",
            description="Solving problems gives you XP. Accumulate XP to climb the ranks and reach Diamond tier!",
            color=COLOR_GOLD,
        )
        xp_embed.add_field(
            name="Points per Problem",
            value=(
                f"🟢 **Easy:** {XP_EASY} XP\n"
                f"🟡 **Medium:** {XP_MEDIUM} XP\n"
                f"🔴 **Hard:** {XP_HARD} XP\n"
                f"🎉 **Clearing an entire topic:** +{XP_TOPIC_CLEAR} XP Bonus!"
            ),
            inline=True
        )
        
        tier_list = "\n".join([f"**{t[0]}** — {t[1]} XP" for t in TIERS])
        xp_embed.add_field(
            name="Rank Tiers",
            value=tier_list,
            inline=True
        )

        # Embed 3: Streaks
        streak_embed = discord.Embed(
            title="🔥 Daily Streaks",
            description="Consistency is everything. Solving at least one problem every day builds your streak. Streaks reset at midnight (IST).",
            color=COLOR_STREAK,
        )
        
        bonus_list = "\n".join([f"**{days} Days:** +{xp} XP" for days, xp in STREAK_BONUSES.items()])
        streak_embed.add_field(
            name="Streak Milestones",
            value=f"Hit these milestones for massive XP boosts and server-wide announcements:\n{bonus_list}",
            inline=False
        )
        streak_embed.set_footer(text="Pro Tip: You can pin this message using Discord's Pin feature to keep it handy!")

        await interaction.response.send_message(
            embeds=[intro_embed, xp_embed, streak_embed],
            ephemeral=True  # Make it private to the user
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(GuideCog(bot))
