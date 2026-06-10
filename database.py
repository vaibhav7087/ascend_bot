"""
Database layer for the DSA Discord Bot.
Async SQLite via aiosqlite. All DB operations go through here.
"""

from __future__ import annotations

import aiosqlite
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import DB_PATH, TIMEZONE

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Get or create the database connection."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    return _db


async def close_db():
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


async def init_db():
    """Create tables if they don't exist."""
    db = await get_db()

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY,
            username        TEXT NOT NULL,
            xp              INTEGER DEFAULT 0,
            tier            TEXT DEFAULT '🪨 Noob',
            current_streak  INTEGER DEFAULT 0,
            longest_streak  INTEGER DEFAULT 0,
            last_solve_date TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS solves (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            problem_slug    TEXT NOT NULL,
            problem_name    TEXT NOT NULL,
            difficulty      TEXT NOT NULL,
            category        TEXT NOT NULL,
            subcategory     TEXT NOT NULL,
            solved_at       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, problem_slug)
        );

        CREATE TABLE IF NOT EXISTS announcements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            event_type      TEXT NOT NULL,
            event_detail    TEXT,
            announced_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_solves_user ON solves(user_id);
        CREATE INDEX IF NOT EXISTS idx_solves_slug ON solves(problem_slug);
        CREATE INDEX IF NOT EXISTS idx_solves_category ON solves(category);
    """)
    await db.commit()


# ─── User Operations ──────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str) -> dict:
    """Get user row, creating it if it doesn't exist."""
    db = await get_db()

    cursor = await db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()

    if row is None:
        await db.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()

    return dict(row)


async def update_user_xp(user_id: int, xp_delta: int, new_tier: str | None = None):
    """Add XP to a user and optionally update tier."""
    db = await get_db()
    if new_tier:
        await db.execute(
            "UPDATE users SET xp = xp + ?, tier = ? WHERE user_id = ?",
            (xp_delta, new_tier, user_id),
        )
    else:
        await db.execute(
            "UPDATE users SET xp = xp + ? WHERE user_id = ?",
            (xp_delta, user_id),
        )
    await db.commit()


async def update_streak(user_id: int) -> tuple[int, bool]:
    """
    Update streak based on today's date.
    Returns (new_streak, is_new_day) — is_new_day is False if already solved today.
    """
    db = await get_db()
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).strftime("%Y-%m-%d")

    cursor = await db.execute(
        "SELECT current_streak, longest_streak, last_solve_date FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return 0, False

    current_streak = row["current_streak"]
    longest_streak = row["longest_streak"]
    last_date = row["last_solve_date"]

    if last_date == today:
        # Already solved today — streak doesn't change
        return current_streak, False

    yesterday = (datetime.now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")

    if last_date == yesterday:
        # Consecutive day — increment streak
        new_streak = current_streak + 1
    elif last_date is None:
        # First ever solve
        new_streak = 1
    else:
        # Streak broken — reset to 1
        new_streak = 1

    new_longest = max(longest_streak, new_streak)

    await db.execute(
        """UPDATE users
           SET current_streak = ?, longest_streak = ?, last_solve_date = ?
           WHERE user_id = ?""",
        (new_streak, new_longest, today, user_id),
    )
    await db.commit()
    return new_streak, True


# ─── Solve Operations ─────────────────────────────────────────────

async def add_solve(user_id: int, problem: dict) -> bool:
    """
    Insert a solve record. Returns True if newly solved, False if duplicate.
    """
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO solves (user_id, problem_slug, problem_name, difficulty, category, subcategory)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                problem["slug"],
                problem["name"],
                problem["difficulty"],
                problem["category"],
                problem["subcategory"],
            ),
        )
        await db.commit()
        return True
    except aiosqlite.IntegrityError:
        # Duplicate — UNIQUE constraint violation
        return False


async def get_user_solves(user_id: int) -> set[str]:
    """Get set of all solved problem slugs for a user."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT problem_slug FROM solves WHERE user_id = ?", (user_id,)
    )
    rows = await cursor.fetchall()
    return {row["problem_slug"] for row in rows}


async def get_solve_counts(user_id: int) -> dict:
    """Get solve counts by difficulty."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT difficulty, COUNT(*) as cnt
           FROM solves WHERE user_id = ?
           GROUP BY difficulty""",
        (user_id,),
    )
    rows = await cursor.fetchall()
    counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    for row in rows:
        counts[row["difficulty"]] = row["cnt"]
    return counts


async def get_solvers_for_problem(problem_slug: str) -> list[dict]:
    """Get all users who solved a specific problem."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT u.user_id, u.username, s.solved_at
           FROM solves s JOIN users u ON s.user_id = u.user_id
           WHERE s.problem_slug = ?
           ORDER BY s.solved_at ASC""",
        (problem_slug,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_category_progress(user_id: int, category: str) -> tuple[int, int]:
    """Get (solved_count, total_count_in_db) for a category. Total comes from solves table only."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM solves WHERE user_id = ? AND category = ?",
        (user_id, category),
    )
    row = await cursor.fetchone()
    return row["cnt"] if row else 0


async def get_user_category_solves(user_id: int, category: str) -> set[str]:
    """Get set of solved problem slugs in a specific category."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT problem_slug FROM solves WHERE user_id = ? AND category = ?",
        (user_id, category),
    )
    rows = await cursor.fetchall()
    return {row["problem_slug"] for row in rows}


# ─── Leaderboard ──────────────────────────────────────────────────

async def get_leaderboard() -> list[dict]:
    """Get all users ordered by XP descending."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT u.user_id, u.username, u.xp, u.tier, u.current_streak,
                  COUNT(s.id) as total_solved
           FROM users u
           LEFT JOIN solves s ON u.user_id = s.user_id
           GROUP BY u.user_id
           ORDER BY u.xp DESC"""
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ─── Announcements ────────────────────────────────────────────────

async def has_been_announced(user_id: int, event_type: str, event_detail: str) -> bool:
    """Check if this specific announcement has already been made."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT id FROM announcements
           WHERE user_id = ? AND event_type = ? AND event_detail = ?""",
        (user_id, event_type, event_detail),
    )
    return await cursor.fetchone() is not None


async def log_announcement(user_id: int, event_type: str, event_detail: str):
    """Log that an announcement was made."""
    db = await get_db()
    await db.execute(
        "INSERT INTO announcements (user_id, event_type, event_detail) VALUES (?, ?, ?)",
        (user_id, event_type, event_detail),
    )
    await db.commit()


async def get_user_profile_data(user_id: int) -> dict | None:
    """Get full user data including solve counts."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)
