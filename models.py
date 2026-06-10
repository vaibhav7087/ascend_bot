"""
Data models for the DSA Discord Bot.
Pure dataclasses — no DB or Discord dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Problem:
    """Represents a single DSA problem from the TUF A2Z sheet."""
    id: str
    name: str
    slug: str
    difficulty: str            # Easy / Medium / Hard
    category: str              # e.g., "Solve Problems on Arrays [Easy -> Medium -> Hard]"
    subcategory: str           # e.g., "Medium"
    leetcode: str | None = None
    article: str | None = None
    youtube: str | None = None

    @property
    def difficulty_emoji(self) -> str:
        return {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(self.difficulty, "⚪")

    @property
    def display_name(self) -> str:
        """Human-readable name with difficulty badge."""
        return f"{self.difficulty_emoji} {self.name}"

    @property
    def leetcode_url(self) -> str | None:
        """Full LeetCode URL if available."""
        if self.leetcode and self.leetcode.startswith("http"):
            return self.leetcode
        return None


@dataclass
class UserProfile:
    """Aggregated user stats for display."""
    user_id: int
    username: str
    xp: int = 0
    tier: str = "🪨 Noob"
    current_streak: int = 0
    longest_streak: int = 0
    last_solve_date: str | None = None
    total_solved: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    topics_cleared: list[str] = field(default_factory=list)

    @property
    def solve_summary(self) -> str:
        return (
            f"**{self.total_solved}**/474 solved  "
            f"(🟢 {self.easy_solved} · 🟡 {self.medium_solved} · 🔴 {self.hard_solved})"
        )


@dataclass
class SolveResult:
    """Result returned after logging a solve."""
    problem: Problem
    xp_earned: int
    total_xp: int
    new_tier: str | None          # Non-None if tier upgraded
    old_tier: str
    streak: int
    streak_bonus: int             # 0 if no milestone hit
    topic_cleared: str | None     # Non-None if topic just cleared
    topic_bonus: int              # 0 if not cleared
    already_solved: bool = False
