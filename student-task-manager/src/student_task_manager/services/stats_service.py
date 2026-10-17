"""Numbers shown on the dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from ..db.repositories import AssignmentRepo
from ..models import Assignment
from ..utils.dates import floor_minute


@dataclass
class CourseProgress:
    code: str
    name: str
    color: str
    total: int
    completed: int

    @property
    def percent(self) -> int:
        return round(100 * self.completed / self.total) if self.total else 0


@dataclass
class DashboardStats:
    total: int = 0
    completed: int = 0
    pending: int = 0          # not completed (pending + in progress)
    overdue: int = 0
    due_this_week: int = 0    # not completed, due within the next 7 days
    completion_percent: int = 0
    upcoming: list[Assignment] = field(default_factory=list)
    by_course: list[CourseProgress] = field(default_factory=list)


class StatsService:
    def __init__(self, repo: AssignmentRepo, clock: Callable[[], datetime] = datetime.now):
        self.repo = repo
        self.clock = clock

    def dashboard(self, upcoming_limit: int = 6) -> DashboardStats:
        now = floor_minute(self.clock())
        week_end = now + timedelta(days=7)
        items = self.repo.list_all()
        open_items = [a for a in items if not a.is_completed]

        stats = DashboardStats()
        stats.total = len(items)
        stats.completed = stats.total - len(open_items)
        stats.pending = len(open_items)
        stats.overdue = sum(1 for a in open_items if a.due_datetime < now)
        stats.due_this_week = sum(1 for a in open_items if now <= a.due_datetime <= week_end)
        stats.completion_percent = round(100 * stats.completed / stats.total) if stats.total else 0
        stats.upcoming = open_items[:upcoming_limit]  # already sorted by due date

        groups: dict[int | None, CourseProgress] = {}
        for a in items:
            key = a.course_id
            if key not in groups:
                groups[key] = CourseProgress(
                    code=a.course_code or "No course",
                    name=a.course_name or "Not linked to a course",
                    color=a.course_color or "#9CA3AF",
                    total=0, completed=0,
                )
            groups[key].total += 1
            groups[key].completed += 1 if a.is_completed else 0
        stats.by_course = sorted(groups.values(), key=lambda g: g.code)
        return stats
