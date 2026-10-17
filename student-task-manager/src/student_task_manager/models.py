"""Plain data objects passed between the layers of the app."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from .utils.dates import floor_minute

PRIORITIES = ("low", "medium", "high")
STATUSES = ("pending", "in_progress", "completed")
STATUS_LABELS = {
    "pending": "Pending",
    "in_progress": "In progress",
    "completed": "Completed",
    "overdue": "Overdue",
}
END_OF_DAY = time(23, 59)
NO_COURSE = 0  # filter value meaning "assignments without a course"

# (minutes, label) choices for reminder lead time
REMINDER_PRESETS = [
    (15, "15 minutes"),
    (30, "30 minutes"),
    (60, "1 hour"),
    (180, "3 hours"),
    (720, "12 hours"),
    (1440, "1 day"),
    (2880, "2 days"),
    (10080, "1 week"),
]


def minutes_label(minutes: int) -> str:
    for value, label in REMINDER_PRESETS:
        if value == minutes:
            return label
    return f"{minutes} minutes"


@dataclass
class Course:
    id: int | None
    code: str
    name: str
    instructor: str = ""
    color: str = "#4F7CFF"

    @property
    def display(self) -> str:
        return f"{self.code} - {self.name}"


@dataclass
class Assignment:
    id: int | None
    title: str
    due_date: date
    due_time: time | None = None
    course_id: int | None = None
    course_code: str = ""
    course_name: str = ""
    course_color: str = ""
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    completed_at: datetime | None = None
    reminder_minutes: int | None = None

    @property
    def due_datetime(self) -> datetime:
        return datetime.combine(self.due_date, self.due_time or END_OF_DAY)

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    def is_overdue(self, now: datetime) -> bool:
        return (not self.is_completed) and self.due_datetime < floor_minute(now)


@dataclass
class AssignmentFilter:
    search: str = ""
    course_id: int | None = None      # None = all, NO_COURSE = no course
    status: str | None = None         # pending / in_progress / completed / overdue
    priority: str | None = None
    due_from: date | None = None
    due_to: date | None = None
