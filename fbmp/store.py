from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from fbmp.config import FBMP_DIR

DB_PATH = FBMP_DIR / "seen.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_listings (
    listing_id TEXT PRIMARY KEY,
    keyword TEXT,
    title TEXT,
    price TEXT,
    first_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS saved_searches (
    keyword TEXT PRIMARY KEY,
    created_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    FBMP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def filter_new(keyword: str, listings: list[dict]) -> list[dict]:
    """Return only listings not previously seen, and mark them as seen."""
    if not listings:
        return []
    conn = _connect()
    now = datetime.now(UTC).isoformat()
    new = []
    for item in listings:
        lid = item.get("listing_id") or item.get("url", "")
        row = conn.execute("SELECT 1 FROM seen_listings WHERE listing_id = ?", (lid,)).fetchone()
        if not row:
            new.append(item)
            conn.execute(
                "INSERT OR IGNORE INTO seen_listings"
                " (listing_id, keyword, title, price, first_seen_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (lid, keyword, item.get("title", ""), item.get("price", ""), now),
            )
    conn.commit()
    conn.close()
    return new


# --- Saved searches ---


def list_searches() -> list[str]:
    conn = _connect()
    rows = conn.execute("SELECT keyword FROM saved_searches ORDER BY created_at").fetchall()
    conn.close()
    return [r["keyword"] for r in rows]


def add_search(keyword: str) -> None:
    conn = _connect()
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO saved_searches (keyword, created_at) VALUES (?, ?)",
        (keyword, now),
    )
    conn.commit()
    conn.close()


def remove_search(keyword: str) -> bool:
    conn = _connect()
    cur = conn.execute("DELETE FROM saved_searches WHERE keyword = ?", (keyword,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
