"""All SQL lives here. Nothing outside this file writes SQL.

Each repository wraps one table. Every method that changes data commits
immediately, so closing the app never loses work.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from ..models import NO_COURSE, Assignment, AssignmentFilter, Course
from ..utils.dates import (
    floor_minute,
    from_db_datetime,
    parse_date,
    parse_time,
    to_db_datetime,
)


def _escape_like(text: str) -> str:
    """Make % and _ typed by the user match literally in a LIKE search."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ----------------------------------------------------------------- courses
class CourseRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _to_course(row: sqlite3.Row) -> Course:
        return Course(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            instructor=row["instructor"] or "",
            color=row["color"],
        )

    def add(self, course: Course) -> int:
        cur = self.conn.execute(
            "INSERT INTO courses (code, name, instructor, color) VALUES (?, ?, ?, ?)",
            (course.code, course.name, course.instructor or None, course.color),
        )
        self.conn.commit()
        return cur.lastrowid

    def update(self, course: Course) -> None:
        self.conn.execute(
            "UPDATE courses SET code = ?, name = ?, instructor = ?, color = ? WHERE id = ?",
            (course.code, course.name, course.instructor or None, course.color, course.id),
        )
        self.conn.commit()

    def delete(self, course_id: int) -> None:
        self.conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        self.conn.commit()

    def get(self, course_id: int) -> Course | None:
        row = self.conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        return self._to_course(row) if row else None

    def get_by_code(self, code: str) -> Course | None:
        row = self.conn.execute("SELECT * FROM courses WHERE code = ?", (code,)).fetchone()
        return self._to_course(row) if row else None

    def list_all(self) -> list[Course]:
        rows = self.conn.execute("SELECT * FROM courses ORDER BY code").fetchall()
        return [self._to_course(r) for r in rows]

    def list_with_counts(self) -> list[tuple[Course, int]]:
        rows = self.conn.execute(
            """SELECT c.*, COUNT(a.id) AS n
               FROM courses c LEFT JOIN assignments a ON a.course_id = c.id
               GROUP BY c.id ORDER BY c.code"""
        ).fetchall()
        return [(self._to_course(r), r["n"]) for r in rows]

    def assignment_count(self, course_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM assignments WHERE course_id = ?", (course_id,)
        ).fetchone()
        return row["n"]


# ------------------------------------------------------------- assignments
_ASSIGNMENT_SELECT = """
SELECT a.*, c.code AS course_code, c.name AS course_name, c.color AS course_color
FROM assignments a LEFT JOIN courses c ON c.id = a.course_id
"""
_ORDER = " ORDER BY a.due_date, COALESCE(a.due_time, '23:59'), a.id"


class AssignmentRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _to_assignment(row: sqlite3.Row) -> Assignment:
        return Assignment(
            id=row["id"],
            title=row["title"],
            due_date=parse_date(row["due_date"]),
            due_time=parse_time(row["due_time"]),
            course_id=row["course_id"],
            course_code=row["course_code"] or "",
            course_name=row["course_name"] or "",
            course_color=row["course_color"] or "",
            description=row["description"] or "",
            priority=row["priority"],
            status=row["status"],
            completed_at=from_db_datetime(row["completed_at"]) if row["completed_at"] else None,
            reminder_minutes=row["reminder_minutes"],
        )

    @staticmethod
    def _values(a: Assignment) -> tuple:
        return (
            a.course_id,
            a.title,
            a.description or None,
            a.due_date.strftime("%Y-%m-%d"),
            a.due_time.strftime("%H:%M") if a.due_time else None,
            a.priority,
            a.status,
            to_db_datetime(a.completed_at) if a.completed_at else None,
            a.reminder_minutes,
        )

    def add(self, a: Assignment) -> int:
        cur = self.conn.execute(
            """INSERT INTO assignments (course_id, title, description, due_date, due_time,
                   priority, status, completed_at, reminder_minutes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            self._values(a),
        )
        self.conn.commit()
        return cur.lastrowid

    def update(self, a: Assignment) -> None:
        self.conn.execute(
            """UPDATE assignments SET course_id = ?, title = ?, description = ?, due_date = ?,
                   due_time = ?, priority = ?, status = ?, completed_at = ?, reminder_minutes = ?,
                   updated_at = datetime('now', 'localtime')
               WHERE id = ?""",
            self._values(a) + (a.id,),
        )
        self.conn.commit()

    def delete(self, assignment_id: int) -> None:
        self.conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        self.conn.commit()

    def get(self, assignment_id: int) -> Assignment | None:
        row = self.conn.execute(
            _ASSIGNMENT_SELECT + " WHERE a.id = ?", (assignment_id,)
        ).fetchone()
        return self._to_assignment(row) if row else None

    def list_all(self) -> list[Assignment]:
        rows = self.conn.execute(_ASSIGNMENT_SELECT + _ORDER).fetchall()
        return [self._to_assignment(r) for r in rows]

    def list_open(self) -> list[Assignment]:
        rows = self.conn.execute(
            _ASSIGNMENT_SELECT + " WHERE a.status != 'completed'" + _ORDER
        ).fetchall()
        return [self._to_assignment(r) for r in rows]

    def search(self, f: AssignmentFilter, now: datetime) -> list[Assignment]:
        where: list[str] = []
        params: list = []

        text = f.search.strip()
        if text:
            like = f"%{_escape_like(text)}%"
            where.append(
                "(a.title LIKE ? ESCAPE '\\' OR a.description LIKE ? ESCAPE '\\' "
                "OR c.name LIKE ? ESCAPE '\\' OR c.code LIKE ? ESCAPE '\\')"
            )
            params += [like, like, like, like]

        if f.course_id == NO_COURSE:
            where.append("a.course_id IS NULL")
        elif f.course_id is not None:
            where.append("a.course_id = ?")
            params.append(f.course_id)

        if f.status == "overdue":
            now = floor_minute(now)
            today = now.strftime("%Y-%m-%d")
            where.append(
                "a.status != 'completed' AND (a.due_date < ? OR "
                "(a.due_date = ? AND COALESCE(a.due_time, '23:59') < ?))"
            )
            params += [today, today, now.strftime("%H:%M")]
        elif f.status:
            where.append("a.status = ?")
            params.append(f.status)

        if f.priority:
            where.append("a.priority = ?")
            params.append(f.priority)
        if f.due_from:
            where.append("a.due_date >= ?")
            params.append(f.due_from.strftime("%Y-%m-%d"))
        if f.due_to:
            where.append("a.due_date <= ?")
            params.append(f.due_to.strftime("%Y-%m-%d"))

        sql = _ASSIGNMENT_SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        rows = self.conn.execute(sql + _ORDER, params).fetchall()
        return [self._to_assignment(r) for r in rows]


# --------------------------------------------------------------- reminders
class ReminderRepo:
    """Remembers which reminders were already shown (so they do not repeat)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, assignment_id: int, due_snapshot: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM reminder_log WHERE assignment_id = ? AND due_snapshot = ?",
            (assignment_id, due_snapshot),
        ).fetchone()

    def mark_shown(self, assignment_id: int, due_snapshot: str, shown_at: datetime) -> None:
        self.conn.execute(
            """INSERT INTO reminder_log (assignment_id, due_snapshot, shown_at, snoozed_until)
               VALUES (?, ?, ?, NULL)
               ON CONFLICT (assignment_id, due_snapshot)
               DO UPDATE SET shown_at = excluded.shown_at, snoozed_until = NULL""",
            (assignment_id, due_snapshot, to_db_datetime(shown_at)),
        )
        self.conn.commit()

    def snooze(self, assignment_id: int, due_snapshot: str, until: datetime) -> None:
        self.conn.execute(
            "UPDATE reminder_log SET snoozed_until = ? WHERE assignment_id = ? AND due_snapshot = ?",
            (to_db_datetime(until), assignment_id, due_snapshot),
        )
        self.conn.commit()

    def clear(self) -> None:
        self.conn.execute("DELETE FROM reminder_log")
        self.conn.commit()


# ---------------------------------------------------------------- settings
class SettingsRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        self.conn.execute(
            """INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT (key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )
        self.conn.commit()
