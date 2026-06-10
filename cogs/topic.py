"""
Cog: /topic <name> — View problems in a specific topic.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.fuzzy import find_category_match, get_categories
from utils.embeds import topic_progress_embed
from utils.pagination import total_pages
from database import get_user_solves, get_or_create_user
from config import COLOR_ERROR


class TopicCog(commands.Cog):
    """Topic browsing command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="topic", description="View unsolved problems in a specific topic")
    @app_commands.describe(topic_name="Topic name (e.g., arrays, binary search, dp, graphs)")
    async def topic(self, interaction: discord.Interaction, topic_name: str):
        """View topic progress — PRIVATE."""
        await interaction.response.defer(ephemeral=True)

        # Fuzzy match the topic
        matched_cat = find_category_match(topic_name)

        if matched_cat is None:
            categories = get_categories()
            cat_list = "\n".join(f"• {name}" for name in categories.keys())
            embed = discord.Embed(
                title="❌ Topic Not Found",
                description=(
                    f"Couldn't find topic matching **\"{topic_name}\"**.\n\n"
                    f"Available topics:\n{cat_list}"
                ),
                color=COLOR_ERROR,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        categories = get_categories()
        problems = categories[matched_cat]
        user = interaction.user
        await get_or_create_user(user.id, user.display_name)
        solved = await get_user_solves(user.id)

        pages = total_pages(len(problems), per_page=15)
        embed = topic_progress_embed(user, matched_cat, problems, solved, page=1, total_pages=pages)

        if pages > 1:
            from cogs.sheet import TopicPaginatedView
            view = TopicPaginatedView(user, matched_cat, problems, solved)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TopicCog(bot))
