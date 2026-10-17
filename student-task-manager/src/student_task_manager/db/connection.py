"""Opening the SQLite database."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a connection. Use ':memory:' for tests (a throwaway database)."""
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row           # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores foreign keys unless asked
    return conn
