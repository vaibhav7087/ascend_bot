"""
Rich Discord embed builders.
Every embed the bot sends is built here for consistency.
"""

from __future__ import annotations

import discord
from models import Problem, UserProfile
from config import (
    COLOR_SUCCESS, COLOR_INFO, COLOR_XP, COLOR_GOLD,
    COLOR_STREAK, COLOR_ANNOUNCE, COLOR_ERROR, COLOR_WARNING,
)
from utils.xp import calculate_xp_progress, get_next_tier_info


def solve_embed(
    user: discord.User | discord.Member,
    problem: Problem,
    xp_earned: int,
    total_xp: int,
    tier: str,
    streak: int,
    extras: list[str] | None = None,
) -> discord.Embed:
    """Build the embed shown after /solved."""
    embed = discord.Embed(
        title=f"✅ Problem Solved!",
        color=COLOR_SUCCESS,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    # Problem info
    problem_text = f"**{problem.name}**\n{problem.difficulty_emoji} {problem.difficulty} · 📂 {problem.category}"
    if problem.leetcode_url:
        problem_text += f"\n🔗 [LeetCode]({problem.leetcode_url})"
    embed.add_field(name="Problem", value=problem_text, inline=False)

    # XP
    embed.add_field(name="XP Earned", value=f"+{xp_earned} XP", inline=True)
    embed.add_field(name="Total XP", value=f"{total_xp} XP", inline=True)
    embed.add_field(name="Tier", value=tier, inline=True)

    # Streak
    if streak > 0:
        fire = "🔥" * min(streak, 5)
        embed.add_field(name="Streak", value=f"{fire} {streak} day{'s' if streak != 1 else ''}", inline=True)

    # Bonus events
    if extras:
        embed.add_field(name="🎉 Bonuses", value="\n".join(extras), inline=False)

    return embed


def already_solved_embed(problem: Problem) -> discord.Embed:
    """Embed for when user tries to solve an already-solved problem."""
    embed = discord.Embed(
        title="⚠️ Already Solved!",
        description=f"You've already solved **{problem.name}** ({problem.difficulty_emoji} {problem.difficulty}).\nNo duplicate XP — keep grinding new ones!",
        color=COLOR_WARNING,
    )
    return embed


def no_match_embed(query: str) -> discord.Embed:
    """Embed for when no problem matches the query."""
    embed = discord.Embed(
        title="❌ Problem Not Found",
        description=(
            f"Couldn't find a problem matching **\"{query}\"**.\n\n"
            "💡 Try:\n"
            "• Use `/sheet` to browse all problems\n"
            "• Check the exact name from the TUF sheet\n"
            "• Use LeetCode slug format (e.g., `two-sum`)"
        ),
        color=COLOR_ERROR,
    )
    return embed


def confirm_match_embed(problem: Problem) -> discord.Embed:
    """Embed asking user to confirm an ambiguous match."""
    embed = discord.Embed(
        title="❓ Did you mean this problem?",
        description=(
            f"**{problem.name}**\n"
            f"{problem.difficulty_emoji} {problem.difficulty} · 📂 {problem.category}"
        ),
        color=COLOR_INFO,
    )
    if problem.leetcode_url:
        embed.add_field(name="LeetCode", value=f"[Open Problem]({problem.leetcode_url})", inline=False)
    embed.set_footer(text="Click to confirm or cancel. Times out in 30s.")
    return embed


def multiple_matches_embed(query: str, matches: list[Problem]) -> discord.Embed:
    """Embed showing multiple possible matches."""
    lines = []
    for i, p in enumerate(matches, 1):
        lines.append(f"**{i}.** {p.name} ({p.difficulty_emoji} {p.difficulty})")

    embed = discord.Embed(
        title=f"🔍 Multiple matches for \"{query}\"",
        description="\n".join(lines) + "\n\nPlease be more specific or use the exact problem name.",
        color=COLOR_INFO,
    )
    return embed


def profile_embed(
    user: discord.User | discord.Member,
    profile: UserProfile,
) -> discord.Embed:
    """Full profile card embed."""
    embed = discord.Embed(
        title=f"📊 {user.display_name}'s Profile",
        color=COLOR_XP,
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    # Tier + XP
    embed.add_field(name="Tier", value=profile.tier, inline=True)
    embed.add_field(name="Total XP", value=f"{profile.xp:,} XP", inline=True)

    # XP Progress bar
    next_tier = get_next_tier_info(profile.xp)
    if next_tier:
        bracket_xp, bracket_size, pct = calculate_xp_progress(profile.xp)
        filled = int(pct * 10)
        bar = "█" * filled + "░" * (10 - filled)
        embed.add_field(
            name="Progress to Next Tier",
            value=f"`{bar}` {pct:.0%}\n{bracket_xp}/{bracket_size} XP → {next_tier[0]}",
            inline=False,
        )
    else:
        embed.add_field(name="Progress", value="🏆 **MAX TIER REACHED!**", inline=False)

    # Solve stats
    embed.add_field(name="Problems Solved", value=profile.solve_summary, inline=False)

    # Streak
    fire = "🔥" * min(profile.current_streak, 5) if profile.current_streak > 0 else "💤"
    embed.add_field(
        name="Streak",
        value=f"{fire} **{profile.current_streak}** day{'s' if profile.current_streak != 1 else ''} (best: {profile.longest_streak})",
        inline=True,
    )

    # Topics cleared
    if profile.topics_cleared:
        topics_text = ", ".join(profile.topics_cleared[:5])
        if len(profile.topics_cleared) > 5:
            topics_text += f" +{len(profile.topics_cleared) - 5} more"
        embed.add_field(name="Topics Cleared ✅", value=topics_text, inline=False)

    return embed


def streak_embed(
    user: discord.User | discord.Member,
    current: int,
    longest: int,
    last_date: str | None,
) -> discord.Embed:
    """Streak info card."""
    fire_count = min(current, 10)
    fire = "🔥" * fire_count if current > 0 else "💤"

    embed = discord.Embed(
        title=f"🔥 {user.display_name}'s Streak",
        color=COLOR_STREAK,
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Current Streak", value=f"{fire} **{current}** days", inline=True)
    embed.add_field(name="Longest Streak", value=f"🏆 **{longest}** days", inline=True)
    if last_date:
        embed.add_field(name="Last Solved", value=last_date, inline=True)

    return embed


def leaderboard_embed(entries: list[dict], title: str = "🏆 Leaderboard") -> discord.Embed:
    """Leaderboard ranking embed."""
    embed = discord.Embed(title=title, color=COLOR_GOLD)

    if not entries:
        embed.description = "No one has solved any problems yet. Be the first!"
        return embed

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, entry in enumerate(entries):
        prefix = medals[i] if i < 3 else f"`#{i+1}`"
        lines.append(
            f"{prefix} **{entry['username']}** — {entry['xp']:,} XP · "
            f"{entry['tier']} · {entry['total_solved']} solved"
        )
        if i < 3:
            lines.append("")  # Extra spacing for top 3

    embed.description = "\n".join(lines)
    return embed


def whosolved_embed(problem: Problem, solvers: list[dict]) -> discord.Embed:
    """Shows who solved a specific problem."""
    embed = discord.Embed(
        title=f"👥 Who Solved: {problem.name}",
        color=COLOR_INFO,
    )
    embed.add_field(
        name="Problem",
        value=f"{problem.difficulty_emoji} {problem.difficulty} · 📂 {problem.category}",
        inline=False,
    )

    if not solvers:
        embed.description = "No one has solved this problem yet. Be the first! 💪"
    else:
        lines = []
        for i, s in enumerate(solvers, 1):
            lines.append(f"**{i}.** {s['username']} — <t:{_iso_to_timestamp(s['solved_at'])}:R>")
        embed.add_field(name=f"Solvers ({len(solvers)})", value="\n".join(lines), inline=False)

    return embed


def topic_progress_embed(
    user: discord.User | discord.Member,
    topic_name: str,
    problems: list[Problem],
    solved_slugs: set[str],
    page: int = 1,
    total_pages: int = 1,
) -> discord.Embed:
    """Topic view with problem checklist."""
    solved_count = sum(1 for p in problems if p.slug in solved_slugs)
    total = len(problems)
    pct = solved_count / total if total > 0 else 0

    embed = discord.Embed(
        title=f"📂 {topic_name}",
        description=f"**{solved_count}/{total}** solved ({pct:.0%})",
        color=COLOR_INFO,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

    # Show problems for current page
    per_page = 15
    start = (page - 1) * per_page
    end = start + per_page
    page_problems = problems[start:end]

    lines = []
    for p in page_problems:
        status = "✅" if p.slug in solved_slugs else "⬜"
        line = f"{status} {p.name} · {p.difficulty_emoji}"
        if p.leetcode_url:
            line += f" [LC]({p.leetcode_url})"
        lines.append(line)

    embed.add_field(name="Problems", value="\n".join(lines) if lines else "No problems.", inline=False)

    if total_pages > 1:
        embed.set_footer(text=f"Page {page}/{total_pages}")

    return embed


# ─── Announcement Embeds ──────────────────────────────────────────

def announce_topic_clear_embed(
    user: discord.User | discord.Member,
    topic: str,
    xp_bonus: int,
) -> discord.Embed:
    embed = discord.Embed(
        title="🎯 Topic Cleared!",
        description=f"**{user.display_name}** just cleared **{topic}**! 🔥\n+{xp_bonus} XP bonus",
        color=COLOR_ANNOUNCE,
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed


def announce_streak_embed(
    user: discord.User | discord.Member,
    days: int,
    xp_bonus: int,
) -> discord.Embed:
    fire = "🔥" * min(days // 7, 5)
    embed = discord.Embed(
        title=f"{fire} Streak Milestone!",
        description=f"**{user.display_name}** is on a **{days}-day** streak! 🔥\n+{xp_bonus} XP bonus",
        color=COLOR_STREAK,
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed


def announce_tier_upgrade_embed(
    user: discord.User | discord.Member,
    new_tier: str,
) -> discord.Embed:
    embed = discord.Embed(
        title="⬆️ Tier Upgrade!",
        description=f"**{user.display_name}** just hit **{new_tier}**!",
        color=COLOR_GOLD,
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    return embed


# ─── Helpers ──────────────────────────────────────────────────────

def _iso_to_timestamp(iso_str: str) -> int:
    """Convert ISO datetime string to Unix timestamp for Discord formatting."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso_str)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return 0
