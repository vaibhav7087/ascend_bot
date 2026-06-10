"""
Paginated embed views for long lists.
Adds ◀️ ▶️ buttons to navigate through pages.
"""

from __future__ import annotations

import discord
import math


class PaginatedView(discord.ui.View):
    """A view that paginates through a list of embeds."""

    def __init__(self, embeds: list[discord.Embed], *, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.embeds) - 1

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.embeds) - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self):
        # Disable all buttons on timeout
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


def create_pages(items: list, per_page: int = 10) -> list[list]:
    """Split a list into pages."""
    pages = []
    for i in range(0, len(items), per_page):
        pages.append(items[i : i + per_page])
    return pages


def total_pages(item_count: int, per_page: int = 15) -> int:
    """Calculate total number of pages."""
    return max(1, math.ceil(item_count / per_page))
