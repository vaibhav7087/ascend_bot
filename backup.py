"""
Automated database backup to GitHub.
Runs as a background task inside the bot.

Key safety features:
- Never overwrites a real backup with an empty database
- Uses download_url for restore (bypasses GitHub 1MB content API limit)
- Verifies SQLite integrity after restore
- Backs up every 10 minutes (configurable)
- Debounces per-solve backups to avoid race conditions
- Cleans up old timestamped backups (keeps last 50)
"""

import os
import base64
import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

log = logging.getLogger("dsa_bot.backup")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_BACKUP_REPO", "")  # format: "username/dsa-bot-backups"
DB_PATH = os.getenv("DB_PATH", "dsa_bot.db")
BACKUP_INTERVAL_MINUTES = int(os.getenv("BACKUP_INTERVAL_MINUTES", "10"))
TIMEZONE = "Asia/Kolkata"
MAX_BACKUPS_TO_KEEP = 50

# Debounce state for per-solve backups
_last_backup_time: float = 0.0
_backup_lock = asyncio.Lock()
DEBOUNCE_SECONDS = 60  # Minimum seconds between backups
_backup_task: asyncio.Task | None = None


def _is_valid_sqlite(file_path: Path) -> bool:
    """Check if a file is a valid SQLite database by reading its magic header."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        return header[:16] == b"SQLite format 3\x00"
    except Exception:
        return False


def _db_has_user_data(file_path: Path) -> bool:
    """
    Check if the database has any actual user data (rows in users or solves tables).
    This prevents backing up an empty freshly-initialized DB over a real backup.
    Returns False if tables don't exist yet (pre-init_db).
    """
    try:
        import sqlite3
        conn = sqlite3.connect(str(file_path))
        # Check if the tables exist first
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'solves')"
        )
        tables = {row[0] for row in cursor.fetchall()}
        if not tables:
            conn.close()
            return False
        user_count = 0
        solve_count = 0
        if "users" in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        if "solves" in tables:
            cursor = conn.execute("SELECT COUNT(*) FROM solves")
            solve_count = cursor.fetchone()[0]
        conn.close()
        return user_count > 0 or solve_count > 0
    except Exception as e:
        log.warning(f"Could not check DB for user data: {e}")
        return False


async def backup_to_github(force: bool = False) -> bool:
    """
    Upload the database file to GitHub.
    
    Safety: Will NOT upload an empty database (no user data) unless force=True.
    This prevents the catastrophic bug where a fresh empty DB overwrites real backups.
    """
    global _last_backup_time

    if not GITHUB_TOKEN or not GITHUB_REPO:
        log.warning("GitHub backup not configured. Set GITHUB_TOKEN and GITHUB_BACKUP_REPO.")
        return False

    try:
        import aiohttp

        db_path = Path(DB_PATH)
        if not db_path.exists():
            log.warning(f"Database file not found: {DB_PATH}")
            return False

        if not _is_valid_sqlite(db_path):
            log.error(f"Database file is not valid SQLite: {DB_PATH} — skipping backup")
            return False

        import tempfile
        import aiosqlite
        from database import get_db

        # Create a consistent snapshot to a temporary file (flushes WAL cleanly)
        fd, temp_path_str = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        temp_path = Path(temp_path_str)
        
        try:
            db = await get_db()
            async with aiosqlite.connect(temp_path_str) as temp_db:
                await db.backup(temp_db)

            # CRITICAL SAFETY CHECK: Never back up an empty DB over potentially good data
            # Check the snapshot so we don't miss WAL data in this check
            if not _db_has_user_data(temp_path):
                if force:
                    log.warning("⚠️ Force-backing up empty database (no user data)")
                else:
                    log.info("⏭️ Skipping backup — database has no user data (nothing to back up)")
                    return False

            # Read the consistent snapshot
            with open(temp_path, "rb") as f:
                db_content = f.read()

        finally:
            if temp_path.exists():
                temp_path.unlink()

        db_size = len(db_content)
        content_b64 = base64.b64encode(db_content).decode("utf-8")
        tz = ZoneInfo(TIMEZONE)
        now = datetime.now(tz)
        timestamp = now.strftime("%Y-%m-%d_%H-%M")

        # File paths in the repo
        files_to_upload = {
            f"backups/dsa_bot_{timestamp}.db": content_b64,
            "latest/dsa_bot_latest.db": content_b64,
        }

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with aiohttp.ClientSession() as session:
            for file_path, content in files_to_upload.items():
                url = f"{api_url}/{file_path}"

                # Check if file already exists (to get its SHA for update)
                sha = None
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sha = data.get("sha")

                # Upload/update the file
                payload = {
                    "message": f"Backup {timestamp} ({db_size} bytes)",
                    "content": content,
                }
                if sha:
                    payload["sha"] = sha

                async with session.put(url, headers=headers, json=payload) as resp:
                    if resp.status in (200, 201):
                        log.info(f"✅ Backed up: {file_path} ({db_size} bytes)")
                    else:
                        error = await resp.text()
                        log.error(f"❌ Failed to backup {file_path}: {resp.status} {error}")
                        return False

        _last_backup_time = time.monotonic()
        log.info(f"✅ Full backup complete: {timestamp} ({db_size} bytes)")

        # Clean up old backups in background (don't block)
        asyncio.create_task(_cleanup_old_backups())

        return True

    except Exception as e:
        log.error(f"❌ Backup failed: {e}", exc_info=True)
        return False


async def debounced_backup() -> bool:
    """
    Backup with debouncing — used for per-solve backups.
    Skips immediate backup if done recently, but queues a delayed task
    to ensure data isn't missed before a restart.
    Uses a lock to prevent concurrent backup uploads.
    """
    global _last_backup_time, _backup_task

    elapsed = time.monotonic() - _last_backup_time

    if elapsed < DEBOUNCE_SECONDS or _backup_lock.locked():
        if _backup_task is None or _backup_task.done():
            delay = max(0.0, DEBOUNCE_SECONDS - elapsed) if elapsed < DEBOUNCE_SECONDS else 5.0
            log.info(f"Queueing delayed backup in {delay:.1f}s")
            
            async def _delayed():
                await asyncio.sleep(delay)
                async with _backup_lock:
                    await backup_to_github()
                    
            _backup_task = asyncio.create_task(_delayed())
        else:
            log.info("Delayed backup is already queued, skipping")
        return False

    async with _backup_lock:
        return await backup_to_github()


async def restore_from_github() -> bool:
    """
    Download the latest backup from GitHub on startup.
    
    Uses the download_url from the GitHub API (not the base64 content field)
    to avoid the 1MB content limit for large database files.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO:
        log.info("No GitHub backup configured, skipping restore.")
        return False

    db_path = Path(DB_PATH)
    if db_path.exists() and db_path.stat().st_size > 0:
        if _is_valid_sqlite(db_path):
            log.info(f"Database already exists and is valid ({db_path.stat().st_size} bytes), skipping restore.")
            return False
        else:
            log.warning("Database exists but is CORRUPT — will restore from backup.")
            db_path.unlink()  # Delete corrupt file

    try:
        import aiohttp

        # Step 1: Get file metadata (including download_url)
        meta_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/latest/dsa_bot_latest.db"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(meta_url, headers=headers) as resp:
                if resp.status == 404:
                    log.info("No backup found on GitHub — starting fresh.")
                    return False
                elif resp.status != 200:
                    error = await resp.text()
                    log.error(f"❌ Failed to get backup metadata: {resp.status} {error}")
                    return False

                meta = await resp.json()
                file_size = meta.get("size", 0)
                download_url = meta.get("download_url")
                content_b64 = meta.get("content")

            # Step 2: Download the actual file
            # For files > 1MB, the content field is empty — use download_url instead
            db_content = None

            if content_b64 and file_size < 1_000_000:
                # Small file: decode from base64 content in API response
                try:
                    db_content = base64.b64decode(content_b64)
                    log.info(f"Decoded backup from API content ({len(db_content)} bytes)")
                except Exception as e:
                    log.warning(f"Failed to decode base64 content: {e}, falling back to download_url")
                    db_content = None

            if db_content is None and download_url:
                # Large file or base64 failed: download raw file via download_url
                auth_headers = {"Authorization": f"token {GITHUB_TOKEN}"}
                async with session.get(download_url, headers=auth_headers) as resp:
                    if resp.status == 200:
                        db_content = await resp.read()
                        log.info(f"Downloaded backup from raw URL ({len(db_content)} bytes)")
                    else:
                        log.error(f"❌ Failed to download backup: {resp.status}")
                        return False

            if db_content is None:
                log.error("❌ Could not retrieve backup content from GitHub")
                return False

        # Step 3: Write to disk
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(db_path, "wb") as f:
            f.write(db_content)

        # Step 4: Verify SQLite integrity
        if not _is_valid_sqlite(db_path):
            log.error(f"❌ Restored file is NOT valid SQLite ({len(db_content)} bytes) — deleting")
            db_path.unlink()
            return False

        # Step 5: Check if backup has actual data
        has_data = _db_has_user_data(db_path)
        if has_data:
            log.info(f"✅ Restored database from GitHub backup ({len(db_content)} bytes) — contains user data ✓")
        else:
            log.warning(f"⚠️ Restored database from GitHub backup ({len(db_content)} bytes) — but it has NO user data (empty)")

        return True

    except Exception as e:
        log.error(f"❌ Restore failed: {e}", exc_info=True)
        return False


async def _cleanup_old_backups():
    """Remove old timestamped backups, keeping only the last MAX_BACKUPS_TO_KEEP."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return

    try:
        import aiohttp

        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/backups"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as resp:
                if resp.status != 200:
                    return
                files = await resp.json()

            # Sort by name (timestamp-based, so alphabetical = chronological)
            db_files = [f for f in files if f["name"].endswith(".db")]
            db_files.sort(key=lambda f: f["name"])

            if len(db_files) <= MAX_BACKUPS_TO_KEEP:
                return

            # Delete oldest files
            files_to_delete = db_files[:-MAX_BACKUPS_TO_KEEP]
            deleted = 0
            for f in files_to_delete:
                url = f"{api_url}/{f['name']}"
                payload = {
                    "message": f"Cleanup: remove old backup {f['name']}",
                    "sha": f["sha"],
                }
                async with session.delete(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        deleted += 1
                    else:
                        log.warning(f"Failed to delete old backup {f['name']}: {resp.status}")

            if deleted:
                log.info(f"🧹 Cleaned up {deleted} old backups (keeping last {MAX_BACKUPS_TO_KEEP})")

    except Exception as e:
        log.warning(f"Backup cleanup failed (non-critical): {e}")


async def backup_loop():
    """Run backup every N minutes forever."""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL_MINUTES * 60)
        try:
            await backup_to_github()
        except Exception as e:
            log.error(f"Backup loop error: {e}", exc_info=True)
