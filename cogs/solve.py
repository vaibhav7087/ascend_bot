"""
Cog: /solved and /whosolved commands.
Handles problem logging, XP, streaks, and triggers announcements.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    get_or_create_user, add_solve, update_user_xp, update_streak,
    get_user_solves, get_solvers_for_problem, get_user_profile_data,
    get_user_category_solves,
)
from utils.fuzzy import find_match, ConfirmProblemView, get_all_problems, get_categories
from utils.xp import calculate_solve_xp, resolve_tier, check_tier_upgrade, check_streak_bonus, is_streak_milestone
from utils.embeds import (
    solve_embed, already_solved_embed, no_match_embed,
    confirm_match_embed, multiple_matches_embed, whosolved_embed,
)
from config import XP_TOPIC_CLEAR


class SolveCog(commands.Cog):
    """Commands for logging and querying solved problems."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="solved", description="Log a solved problem and earn XP")
    @app_commands.describe(problem_name="Name of the problem you solved (e.g., two-sum)")
    async def solved(self, interaction: discord.Interaction, problem_name: str):
        """Log a solved problem — PUBLIC response."""
        user = interaction.user

        # Fuzzy match
        exact, close_matches = find_match(problem_name)

        if exact is None and not close_matches:
            await interaction.response.send_message(
                embed=no_match_embed(problem_name), ephemeral=True
            )
            return

        if exact is None and close_matches:
            if len(close_matches) == 1:
                # Single close match — ask for confirmation
                problem = close_matches[0]
                view = ConfirmProblemView(problem)
                await interaction.response.send_message(
                    embed=confirm_match_embed(problem), view=view, ephemeral=True
                )
                await view.wait()

                if view.confirmed is not True:
                    await interaction.edit_original_response(
                        content="❌ Cancelled.", embed=None, view=None
                    )
                    return
                exact = problem
            else:
                # Multiple matches — show options
                await interaction.response.send_message(
                    embed=multiple_matches_embed(problem_name, close_matches),
                    ephemeral=True,
                )
                return

        problem = exact
        await interaction.response.defer()  # Takes time to process

        # Ensure user exists
        await get_or_create_user(user.id, user.display_name)

        # Check if already solved
        is_new = await add_solve(user.id, {
            "slug": problem.slug,
            "name": problem.name,
            "difficulty": problem.difficulty,
            "category": problem.category,
            "subcategory": problem.subcategory,
        })

        if not is_new:
            await interaction.followup.send(embed=already_solved_embed(problem))
            return

        # Calculate XP
        xp_earned = calculate_solve_xp(problem.difficulty)
        extras = []

        # Get current user data for tier check
        user_data = await get_user_profile_data(user.id)
        old_xp = user_data["xp"]
        old_tier = user_data["tier"]

        # Update streak
        streak, is_new_day = await update_streak(user.id)

        # Streak bonus
        streak_bonus = 0
        if is_new_day and is_streak_milestone(streak):
            streak_bonus = check_streak_bonus(streak)
            xp_earned += streak_bonus
            extras.append(f"🔥 **{streak}-day streak!** +{streak_bonus} XP bonus")

        # Check topic cleared
        topic_bonus = 0
        categories = get_categories()
        if problem.category in categories:
            cat_problems = categories[problem.category]
            cat_slugs = {p.slug for p in cat_problems}
            user_solved = await get_user_category_solves(user.id, problem.category)
            # Add current solve (already in DB but this ensures accuracy)
            user_solved.add(problem.slug)

            if cat_slugs.issubset(user_solved):
                topic_bonus = XP_TOPIC_CLEAR
                xp_earned += topic_bonus
                extras.append(f"🎯 **Topic cleared: {problem.category}!** +{topic_bonus} XP bonus")

        # Update XP
        new_xp = old_xp + xp_earned
        new_tier = check_tier_upgrade(old_xp, new_xp)
        tier_name = new_tier if new_tier else old_tier

        await update_user_xp(user.id, xp_earned, new_tier)

        if new_tier:
            extras.append(f"⬆️ **Tier upgrade: {new_tier}!**")

        # Send solve response (PUBLIC)
        embed = solve_embed(
            user=user,
            problem=problem,
            xp_earned=xp_earned,
            total_xp=new_xp,
            tier=tier_name,
            streak=streak,
            extras=extras if extras else None,
        )
        await interaction.followup.send(embed=embed)

        # Trigger announcements (in announcements cog)
        announce_cog = self.bot.get_cog("AnnouncementsCog")
        if announce_cog:
            if topic_bonus > 0:
                await announce_cog.send_topic_clear(user, problem.category, topic_bonus)
            if streak_bonus > 0:
                await announce_cog.send_streak_milestone(user, streak, streak_bonus)
            if new_tier:
                await announce_cog.send_tier_upgrade(user, new_tier)

        # Trigger an immediate backup to GitHub to prevent data loss on Render redeploys
        import asyncio
        from backup import debounced_backup
        asyncio.create_task(debounced_backup())

    @app_commands.command(name="whosolved", description="See who solved a specific problem")
    @app_commands.describe(problem_name="Name of the problem to check")
    async def whosolved(self, interaction: discord.Interaction, problem_name: str):
        """Check who solved a problem — PUBLIC response."""
        exact, close_matches = find_match(problem_name)

        if exact is None and not close_matches:
            await interaction.response.send_message(
                embed=no_match_embed(problem_name), ephemeral=True
            )
            return

        if exact is None and close_matches:
            # Pick the best match
            problem = close_matches[0]
            view = ConfirmProblemView(problem)
            await interaction.response.send_message(
                embed=confirm_match_embed(problem), view=view, ephemeral=True
            )
            await view.wait()
            if view.confirmed is not True:
                await interaction.edit_original_response(
                    content="❌ Cancelled.", embed=None, view=None
                )
                return
            exact = problem

        solvers = await get_solvers_for_problem(exact.slug)
        await interaction.response.send_message(
            embed=whosolved_embed(exact, solvers)
        ) if not interaction.response.is_done() else await interaction.followup.send(
            embed=whosolved_embed(exact, solvers)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(SolveCog(bot))
