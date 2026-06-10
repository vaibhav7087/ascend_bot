"""
Cog: /sheet — Interactive problem browser.
Uses Discord Select Menus (dropdowns) for navigation.
Browse by Topic, Difficulty, or Unsolved Only.
"""

from __future__ import annotations

import math
import discord
from discord import app_commands
from discord.ext import commands

from utils.fuzzy import get_all_problems, get_categories, get_problems_by_difficulty
from utils.embeds import topic_progress_embed
from utils.pagination import total_pages
from database import get_user_solves
from config import COLOR_INFO


class SheetCog(commands.Cog):
    """Interactive problem sheet browser."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sheet", description="Browse the TUF A2Z DSA Sheet interactively")
    async def sheet(self, interaction: discord.Interaction):
        """Main sheet menu — PRIVATE (ephemeral)."""
        view = SheetMainView(interaction.user)
        embed = discord.Embed(
            title="📋 Striver's A2Z DSA Sheet",
            description=(
                "**474 problems** across 19 topics\n"
                "🟢 Easy: 152 · 🟡 Medium: 186 · 🔴 Hard: 136\n\n"
                "Choose how to browse:"
            ),
            color=COLOR_INFO,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ─── Main Menu View ───────────────────────────────────────────────

class SheetMainView(discord.ui.View):
    """Initial 3-button menu for /sheet."""

    def __init__(self, user: discord.User | discord.Member):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.button(label="📂 By Topic", style=discord.ButtonStyle.primary)
    async def by_topic(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TopicSelectView(self.user)
        embed = discord.Embed(
            title="📂 Select a Topic",
            description="Choose a topic to see its problems:",
            color=COLOR_INFO,
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 By Difficulty", style=discord.ButtonStyle.primary)
    async def by_difficulty(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DifficultySelectView(self.user)
        embed = discord.Embed(
            title="📊 Select Difficulty",
            description="Choose a difficulty level:",
            color=COLOR_INFO,
        )
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📋 Unsolved Only", style=discord.ButtonStyle.success)
    async def unsolved(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        solved = await get_user_solves(self.user.id)
        all_problems = get_all_problems()
        unsolved = [p for p in all_problems if p.slug not in solved]

        if not unsolved:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="🎉 All Done!",
                    description="You've solved all 474 problems! Incredible! 👑",
                    color=0x2ECC71,
                ),
                view=None,
            )
            return

        # Group unsolved by category
        by_cat: dict[str, list] = {}
        for p in unsolved:
            by_cat.setdefault(p.category, []).append(p)

        embeds = []
        for cat_name, problems in by_cat.items():
            embed = discord.Embed(
                title=f"📋 Unsolved — {cat_name}",
                description=f"**{len(problems)}** remaining",
                color=COLOR_INFO,
            )
            # Show up to 15 per embed
            lines = []
            for p in problems[:15]:
                line = f"⬜ {p.name} · {p.difficulty_emoji}"
                if p.leetcode_url:
                    line += f" [LC]({p.leetcode_url})"
                lines.append(line)
            if len(problems) > 15:
                lines.append(f"*...and {len(problems) - 15} more*")
            embed.add_field(name="Problems", value="\n".join(lines), inline=False)
            embeds.append(embed)

        if len(embeds) == 1:
            await interaction.edit_original_response(embed=embeds[0], view=None)
        else:
            view = UnsolvedPaginatedView(embeds)
            await interaction.edit_original_response(embed=embeds[0], view=view)


# ─── Topic Select ─────────────────────────────────────────────────

class TopicSelectView(discord.ui.View):
    """Dropdown of 19 topics."""

    def __init__(self, user: discord.User | discord.Member):
        super().__init__(timeout=120)
        self.user = user

        categories = get_categories()
        options = []
        for cat_name, problems in categories.items():
            # Truncate label to 100 chars (Discord limit)
            label = cat_name[:95] + "..." if len(cat_name) > 95 else cat_name
            desc = f"{len(problems)} problems"
            options.append(discord.SelectOption(label=label, description=desc, value=cat_name))

        # Discord allows max 25 options — we have 19
        self.add_item(TopicDropdown(options, self.user))


class TopicDropdown(discord.ui.Select):
    """The actual dropdown for topics."""

    def __init__(self, options: list[discord.SelectOption], user: discord.User | discord.Member):
        super().__init__(placeholder="Choose a topic...", options=options, min_values=1, max_values=1)
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        await interaction.response.defer()

        categories = get_categories()
        problems = categories.get(selected, [])
        solved = await get_user_solves(self.user.id)

        pages = total_pages(len(problems), per_page=15)
        embed = topic_progress_embed(self.user, selected, problems, solved, page=1, total_pages=pages)

        if pages > 1:
            view = TopicPaginatedView(self.user, selected, problems, solved)
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=None)


# ─── Difficulty Select ────────────────────────────────────────────

class DifficultySelectView(discord.ui.View):
    """Buttons for Easy/Medium/Hard."""

    def __init__(self, user: discord.User | discord.Member):
        super().__init__(timeout=120)
        self.user = user

    @discord.ui.button(label="🟢 Easy (152)", style=discord.ButtonStyle.success)
    async def easy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_difficulty(interaction, "Easy")

    @discord.ui.button(label="🟡 Medium (186)", style=discord.ButtonStyle.primary)
    async def medium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_difficulty(interaction, "Medium")

    @discord.ui.button(label="🔴 Hard (136)", style=discord.ButtonStyle.danger)
    async def hard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._show_difficulty(interaction, "Hard")

    async def _show_difficulty(self, interaction: discord.Interaction, difficulty: str):
        await interaction.response.defer()
        problems = get_problems_by_difficulty(difficulty)
        solved = await get_user_solves(self.user.id)

        solved_count = sum(1 for p in problems if p.slug in solved)

        # Group by category
        by_cat: dict[str, list] = {}
        for p in problems:
            by_cat.setdefault(p.category, []).append(p)

        embeds = []
        for cat_name, cat_problems in by_cat.items():
            embed = discord.Embed(
                title=f"{difficulty} Problems — {cat_name}",
                description=f"**{sum(1 for p in cat_problems if p.slug in solved)}/{len(cat_problems)}** solved",
                color={"Easy": 0x2ECC71, "Medium": 0xF39C12, "Hard": 0xE74C3C}.get(difficulty, COLOR_INFO),
            )
            lines = []
            for p in cat_problems[:15]:
                status = "✅" if p.slug in solved else "⬜"
                line = f"{status} {p.name}"
                if p.leetcode_url:
                    line += f" [LC]({p.leetcode_url})"
                lines.append(line)
            if len(cat_problems) > 15:
                lines.append(f"*...and {len(cat_problems) - 15} more*")
            embed.add_field(name="Problems", value="\n".join(lines), inline=False)
            embeds.append(embed)

        if len(embeds) == 1:
            await interaction.edit_original_response(embed=embeds[0], view=None)
        elif embeds:
            view = UnsolvedPaginatedView(embeds)
            await interaction.edit_original_response(embed=embeds[0], view=view)


# ─── Paginated Views ──────────────────────────────────────────────

class TopicPaginatedView(discord.ui.View):
    """Paginate through problems within a topic."""

    def __init__(self, user, topic_name, problems, solved_slugs):
        super().__init__(timeout=120)
        self.user = user
        self.topic_name = topic_name
        self.problems = problems
        self.solved_slugs = solved_slugs
        self.page = 1
        self.pages = total_pages(len(problems), per_page=15)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page <= 1
        self.next_btn.disabled = self.page >= self.pages

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        self._update_buttons()
        embed = topic_progress_embed(self.user, self.topic_name, self.problems, self.solved_slugs, self.page, self.pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(self.pages, self.page + 1)
        self._update_buttons()
        embed = topic_progress_embed(self.user, self.topic_name, self.problems, self.solved_slugs, self.page, self.pages)
        await interaction.response.edit_message(embed=embed, view=self)


class UnsolvedPaginatedView(discord.ui.View):
    """Paginate through multiple category embeds."""

    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.page <= 0
        self.next_btn.disabled = self.page >= len(self.embeds) - 1

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(self.embeds) - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)


async def setup(bot: commands.Bot):
    await bot.add_cog(SheetCog(bot))
