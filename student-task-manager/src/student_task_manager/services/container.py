"""Builds all services and wires them to one database connection."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from ..db.connection import connect
from ..db.migrations import migrate
from ..db.repositories import AssignmentRepo, CourseRepo, ReminderRepo, SettingsRepo
from .assignment_service import AssignmentService
from .course_service import CourseService
from .reminder_service import ReminderService
from .settings_service import SettingsService
from .stats_service import StatsService


@dataclass
class Services:
    conn: sqlite3.Connection
    db_path: str
    courses: CourseService
    assignments: AssignmentService
    stats: StatsService
    reminders: ReminderService
    settings: SettingsService

    def close(self) -> None:
        self.conn.close()


def build_services(db_path: str | Path = ":memory:",
                   clock: Callable[[], datetime] = datetime.now) -> Services:
    conn = connect(db_path)
    migrate(conn)
    course_repo = CourseRepo(conn)
    assignment_repo = AssignmentRepo(conn)
    settings = SettingsService(SettingsRepo(conn))
    return Services(
        conn=conn,
        db_path=str(db_path),
        courses=CourseService(course_repo),
        assignments=AssignmentService(assignment_repo, course_repo, clock),
        stats=StatsService(assignment_repo, clock),
        reminders=ReminderService(assignment_repo, ReminderRepo(conn), settings),
        settings=settings,
    )
