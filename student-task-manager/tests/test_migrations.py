import sqlite3

import pytest

from student_task_manager.db.connection import connect
from student_task_manager.db.migrations import (
    MIGRATIONS,
    DatabaseTooNewError,
    current_version,
    migrate,
)


def table_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {r["name"] for r in rows}


def test_migrate_creates_tables():
    conn = connect(":memory:")
    assert migrate(conn) == len(MIGRATIONS)
    assert {"courses", "assignments", "reminder_log", "settings"} <= table_names(conn)


def test_migrate_twice_is_harmless():
    conn = connect(":memory:")
    migrate(conn)
    conn.execute("INSERT INTO courses (code, name) VALUES ('A', 'B')")
    conn.commit()
    migrate(conn)
    assert conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 1


def test_foreign_keys_are_enforced():
    conn = connect(":memory:")
    migrate(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO assignments (course_id, title, due_date) VALUES (999, 'x', '2026-01-01')"
        )


def test_newer_database_is_rejected():
    conn = connect(":memory:")
    conn.execute(f"PRAGMA user_version = {len(MIGRATIONS) + 5}")
    with pytest.raises(DatabaseTooNewError):
        migrate(conn)


def test_data_survives_reopening_a_file(tmp_path):
    path = tmp_path / "t.db"
    conn = connect(path)
    migrate(conn)
    conn.execute("INSERT INTO courses (code, name) VALUES ('C1', 'Course')")
    conn.commit()
    conn.close()
    conn2 = connect(path)
    migrate(conn2)
    assert current_version(conn2) == len(MIGRATIONS)
    assert conn2.execute("SELECT name FROM courses").fetchone()["name"] == "Course"
