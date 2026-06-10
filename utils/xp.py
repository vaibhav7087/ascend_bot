"""
XP calculation and tier resolution engine.
"""

from __future__ import annotations

from config import (
    XP_EASY, XP_MEDIUM, XP_HARD, XP_TOPIC_CLEAR,
    TIERS, STREAK_BONUSES, STREAK_MILESTONES,
)


def calculate_solve_xp(difficulty: str) -> int:
    """Return XP for solving a problem of given difficulty."""
    return {
        "Easy": XP_EASY,
        "Medium": XP_MEDIUM,
        "Hard": XP_HARD,
    }.get(difficulty, XP_EASY)


def resolve_tier(total_xp: int) -> str:
    """Return the tier name + emoji for a given XP total."""
    tier_name = TIERS[0][0]  # Default: Noob
    for name, threshold in TIERS:
        if total_xp >= threshold:
            tier_name = name
    return tier_name


def check_tier_upgrade(old_xp: int, new_xp: int) -> str | None:
    """
    Check if crossing from old_xp to new_xp triggers a tier upgrade.
    Returns the new tier name if upgraded, None otherwise.
    """
    old_tier = resolve_tier(old_xp)
    new_tier = resolve_tier(new_xp)
    if new_tier != old_tier:
        return new_tier
    return None


def get_next_tier_info(total_xp: int) -> tuple[str, int] | None:
    """
    Get the next tier and XP needed to reach it.
    Returns (next_tier_name, xp_remaining) or None if at max tier.
    """
    for name, threshold in TIERS:
        if total_xp < threshold:
            return name, threshold - total_xp
    return None  # Already at max tier


def calculate_xp_progress(total_xp: int) -> tuple[int, int, float]:
    """
    Get XP progress within current tier bracket.
    Returns (current_bracket_xp, bracket_size, percentage).
    """
    current_floor = 0
    next_ceiling = TIERS[-1][1]

    for i, (name, threshold) in enumerate(TIERS):
        if total_xp >= threshold:
            current_floor = threshold
            if i + 1 < len(TIERS):
                next_ceiling = TIERS[i + 1][1]
            else:
                # At max tier
                return total_xp, total_xp, 1.0

    bracket_xp = total_xp - current_floor
    bracket_size = next_ceiling - current_floor
    percentage = bracket_xp / bracket_size if bracket_size > 0 else 1.0

    return bracket_xp, bracket_size, percentage


def check_streak_bonus(streak_count: int) -> int:
    """
    Check if the current streak count hits a bonus milestone.
    Returns bonus XP (0 if no milestone).
    """
    return STREAK_BONUSES.get(streak_count, 0)


def is_streak_milestone(streak_count: int) -> bool:
    """Check if streak count is a milestone worth announcing."""
    return streak_count in STREAK_MILESTONES
