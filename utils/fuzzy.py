"""
Fuzzy problem matching engine.
Handles all the ways users might type a problem name and resolves to the canonical slug.
"""

from __future__ import annotations

import json
import re
import difflib
from typing import TYPE_CHECKING

import discord

from config import PROBLEMS_JSON
from models import Problem

if TYPE_CHECKING:
    pass

# ─── Global problem registry ──────────────────────────────────────
_problems: list[Problem] = []
_slug_map: dict[str, Problem] = {}
_name_map: dict[str, Problem] = {}
_categories: dict[str, list[Problem]] = {}
_all_slugs: list[str] = []


def load_problems() -> list[Problem]:
    """Load problems from JSON into memory. Called once on bot startup."""
    global _problems, _slug_map, _name_map, _categories, _all_slugs

    with open(PROBLEMS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    _problems = []
    _slug_map = {}
    _name_map = {}
    _categories = {}

    for p in data.get("problems", []):
        problem = Problem(
            id=str(p["id"]),
            name=p["name"].strip(),
            slug=p["slug"],
            difficulty=p["difficulty"],
            category=p["category"],
            subcategory=p["subcategory"],
            leetcode=p.get("leetcode"),
            article=p.get("article"),
            youtube=p.get("youtube"),
        )
        _problems.append(problem)
        _slug_map[problem.slug] = problem
        _name_map[normalize(problem.name)] = problem

        # Group by category
        if problem.category not in _categories:
            _categories[problem.category] = []
        _categories[problem.category].append(problem)

    _all_slugs = list(_slug_map.keys())
    return _problems


def get_all_problems() -> list[Problem]:
    """Get all loaded problems."""
    return _problems


def get_categories() -> dict[str, list[Problem]]:
    """Get problems grouped by category."""
    return _categories


def get_problems_by_difficulty(difficulty: str) -> list[Problem]:
    """Get all problems of a specific difficulty."""
    return [p for p in _problems if p.difficulty.lower() == difficulty.lower()]


def normalize(text: str) -> str:
    """Normalize a problem name for matching.

    - Lowercase
    - Replace hyphens/underscores with spaces
    - Remove special characters
    - Collapse whitespace
    """
    text = text.lower().strip()
    text = text.replace("-", " ").replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _to_slug(text: str) -> str:
    """Convert normalized text to slug format."""
    return normalize(text).replace(" ", "-")


def find_match(query: str) -> tuple[Problem | None, list[Problem]]:
    """
    Find a problem matching the query.

    Returns:
        (exact_match, close_matches)
        - If exact_match is not None, it's a definite match.
        - If exact_match is None, close_matches contains suggestions.
    """
    if not _problems:
        load_problems()

    normalized = normalize(query)
    slug = _to_slug(query)

    # 1. Exact slug match
    if slug in _slug_map:
        return _slug_map[slug], []

    # 2. Exact normalized name match
    if normalized in _name_map:
        return _name_map[normalized], []

    # 3. Check if query is a substring of any slug/name (for partial matches)
    for s, problem in _slug_map.items():
        if normalized.replace(" ", "") == s.replace("-", ""):
            return problem, []

    # 4. Fuzzy match against all slugs using difflib
    # Convert slugs to space-separated for better matching
    slug_to_spaced = {s: s.replace("-", " ") for s in _all_slugs}
    spaced_slugs = list(slug_to_spaced.values())

    close = difflib.get_close_matches(normalized, spaced_slugs, n=3, cutoff=0.55)

    if close:
        # Map back to Problems
        reverse_map = {v: k for k, v in slug_to_spaced.items()}
        matches = [_slug_map[reverse_map[c]] for c in close if reverse_map.get(c) in _slug_map]

        # If top match is very close (>= 0.85), treat as exact
        if matches:
            ratio = difflib.SequenceMatcher(None, normalized, close[0]).ratio()
            if ratio >= 0.85:
                return matches[0], []
            return None, matches

    # 5. Substring search as last resort
    substring_matches = []
    for s, problem in _slug_map.items():
        if normalized.replace(" ", "") in s.replace("-", ""):
            substring_matches.append(problem)
        elif s.replace("-", "") in normalized.replace(" ", ""):
            substring_matches.append(problem)

    if len(substring_matches) == 1:
        return substring_matches[0], []
    elif substring_matches:
        return None, substring_matches[:3]

    # No match at all
    return None, []


def find_category_match(query: str) -> str | None:
    """Fuzzy match a category/topic name."""
    if not _categories:
        load_problems()

    normalized = normalize(query)

    # Exact match
    for cat_name in _categories:
        if normalized == normalize(cat_name):
            return cat_name

    # Partial match — check if query is contained in category name
    for cat_name in _categories:
        if normalized in normalize(cat_name):
            return cat_name

    # Fuzzy match
    cat_names_normalized = {normalize(c): c for c in _categories}
    close = difflib.get_close_matches(
        normalized, list(cat_names_normalized.keys()), n=1, cutoff=0.4
    )
    if close:
        return cat_names_normalized[close[0]]

    return None


# ─── Discord UI: Confirmation View ────────────────────────────────

class ConfirmProblemView(discord.ui.View):
    """Buttons for confirming an ambiguous problem match."""

    def __init__(self, problem: Problem, *, timeout: float = 30.0):
        super().__init__(timeout=timeout)
        self.problem = problem
        self.confirmed: bool | None = None  # None = timed out

    @discord.ui.button(label="✅ Yes, that's it", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        self.stop()
        await interaction.response.defer()

    async def on_timeout(self):
        self.confirmed = None
        self.stop()
