"""Rules for assignments: validation, completing, searching."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from ..db.repositories import AssignmentRepo, CourseRepo
from ..models import PRIORITIES, STATUSES, Assignment, AssignmentFilter
from ..utils.dates import parse_date, parse_time
from .errors import ValidationError


class AssignmentService:
    def __init__(self, repo: AssignmentRepo, courses: CourseRepo,
                 clock: Callable[[], datetime] = datetime.now):
        self.repo = repo
        self.courses = courses
        self.clock = clock

    # ---- validation -------------------------------------------------
    def _build(self, assignment_id, *, title, due_date, due_time=None, course_id=None,
               description="", priority="medium", status="pending",
               reminder_minutes=None) -> Assignment:
        title = (title or "").strip()
        if not title:
            raise ValidationError("Title is required.")
        if len(title) > 200:
            raise ValidationError("Title must be 200 characters or fewer.")
        try:
            due_date = parse_date(due_date)
            due_time = parse_time(due_time)
        except ValueError as exc:
            raise ValidationError(str(exc)) from None
        if priority not in PRIORITIES:
            raise ValidationError("Priority must be low, medium or high.")
        if status not in STATUSES:
            raise ValidationError("Status must be pending, in progress or completed.")
        if course_id is not None and self.courses.get(course_id) is None:
            raise ValidationError("The selected course does not exist.")
        if reminder_minutes is not None:
            try:
                reminder_minutes = int(reminder_minutes)
            except (TypeError, ValueError):
                raise ValidationError("Reminder time must be a number of minutes.") from None
            if not 1 <= reminder_minutes <= 60 * 24 * 30:
                raise ValidationError("Reminder time must be between 1 minute and 30 days.")
        return Assignment(
            id=assignment_id, title=title, due_date=due_date, due_time=due_time,
            course_id=course_id, description=(description or "").strip(),
            priority=priority, status=status, reminder_minutes=reminder_minutes,
        )

    # ---- create / update / delete -----------------------------------
    def create(self, **fields) -> Assignment:
        a = self._build(None, **fields)
        if a.status == "completed":
            a.completed_at = self.clock()
        a.id = self.repo.add(a)
        return self.repo.get(a.id)

    def update(self, assignment_id: int, **fields) -> Assignment:
        existing = self.repo.get(assignment_id)
        if existing is None:
            raise ValidationError("That assignment no longer exists.")
        a = self._build(assignment_id, **fields)
        if a.status == "completed":
            a.completed_at = existing.completed_at or self.clock()
        self.repo.update(a)
        return self.repo.get(assignment_id)

    def set_status(self, assignment_id: int, status: str) -> Assignment:
        a = self.repo.get(assignment_id)
        if a is None:
            raise ValidationError("That assignment no longer exists.")
        if status not in STATUSES:
            raise ValidationError("Unknown status.")
        a.status = status
        a.completed_at = (a.completed_at or self.clock()) if status == "completed" else None
        self.repo.update(a)
        return self.repo.get(assignment_id)

    def toggle_complete(self, assignment_id: int) -> Assignment:
        a = self.repo.get(assignment_id)
        if a is None:
            raise ValidationError("That assignment no longer exists.")
        return self.set_status(assignment_id, "pending" if a.is_completed else "completed")

    def delete(self, assignment_id: int) -> None:
        self.repo.delete(assignment_id)

    # ---- reading ----------------------------------------------------
    def get(self, assignment_id: int) -> Assignment | None:
        return self.repo.get(assignment_id)

    def list(self, flt: AssignmentFilter | None = None) -> list[Assignment]:
        return self.repo.search(flt or AssignmentFilter(), self.clock())

    def list_all(self) -> list[Assignment]:
        return self.repo.list_all()
