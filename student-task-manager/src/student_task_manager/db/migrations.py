"""Creating and upgrading the database tables.

The schema version is stored inside the database file using SQLite's built-in
`PRAGMA user_version`. To change the schema later, add a new script to the end
of MIGRATIONS - never edit an old one.
"""
from __future__ import annotations

import sqlite3

SCHEMA_V1 = """
CREATE TABLE courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name        TEXT NOT NULL,
    instructor  TEXT,
    color       TEXT NOT NULL DEFAULT '#4F7CFF',
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE assignments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id        INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    title            TEXT NOT NULL,
    description      TEXT,
    due_date         TEXT NOT NULL,
    due_time         TEXT,
    priority         TEXT NOT NULL DEFAULT 'medium'
                     CHECK (priority IN ('low', 'medium', 'high')),
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'in_progress', 'completed')),
    completed_at     TEXT,
    reminder_minutes INTEGER,
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX idx_assignments_due    ON assignments(due_date);
CREATE INDEX idx_assignments_course ON assignments(course_id);
CREATE INDEX idx_assignments_status ON assignments(status);

CREATE TABLE reminder_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    due_snapshot  TEXT NOT NULL,
    shown_at      TEXT NOT NULL,
    snoozed_until TEXT,
    UNIQUE (assignment_id, due_snapshot)
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

MIGRATIONS = [SCHEMA_V1]


class DatabaseTooNewError(RuntimeError):
    pass


def current_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn: sqlite3.Connection) -> int:
    """Bring the database up to date. Safe to call every time the app starts."""
    version = current_version(conn)
    if version > len(MIGRATIONS):
        raise DatabaseTooNewError(
            "This database was created by a newer version of the app. "
            "Please update Student Task Manager."
        )
    for number, script in enumerate(MIGRATIONS, start=1):
        if number <= version:
            continue
        try:
            conn.executescript(
                f"BEGIN;\n{script}\nPRAGMA user_version = {number};\nCOMMIT;"
            )
        except Exception:
            conn.rollback()
            raise
    return current_version(conn)
