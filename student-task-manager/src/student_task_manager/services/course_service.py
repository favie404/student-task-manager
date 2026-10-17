"""Rules for courses: validation and safe deletion."""
from __future__ import annotations

import re
import sqlite3

from ..db.repositories import CourseRepo
from ..models import Course
from .errors import ValidationError

_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class CourseService:
    def __init__(self, repo: CourseRepo):
        self.repo = repo

    @staticmethod
    def _clean(code: str, name: str, instructor: str, color: str) -> tuple[str, str, str, str]:
        code, name = (code or "").strip(), (name or "").strip()
        instructor, color = (instructor or "").strip(), (color or "").strip()
        if not code:
            raise ValidationError("Course code is required (for example BCS 2101).")
        if len(code) > 20:
            raise ValidationError("Course code must be 20 characters or fewer.")
        if not name:
            raise ValidationError("Course name is required.")
        if len(name) > 150:
            raise ValidationError("Course name must be 150 characters or fewer.")
        if not _COLOR_RE.match(color):
            raise ValidationError("Colour must look like #RRGGBB (for example #4F7CFF).")
        return code, name, instructor, color

    def add(self, code: str, name: str, instructor: str = "", color: str = "#4F7CFF") -> Course:
        code, name, instructor, color = self._clean(code, name, instructor, color)
        course = Course(None, code, name, instructor, color)
        try:
            course.id = self.repo.add(course)
        except sqlite3.IntegrityError:
            raise ValidationError(f"A course with the code '{code}' already exists.") from None
        return course

    def update(self, course_id: int, code: str, name: str, instructor: str = "",
               color: str = "#4F7CFF") -> Course:
        if self.repo.get(course_id) is None:
            raise ValidationError("That course no longer exists.")
        code, name, instructor, color = self._clean(code, name, instructor, color)
        course = Course(course_id, code, name, instructor, color)
        try:
            self.repo.update(course)
        except sqlite3.IntegrityError:
            raise ValidationError(f"A course with the code '{code}' already exists.") from None
        return course

    def delete(self, course_id: int) -> int:
        """Delete a course. Its assignments are kept (they become 'No course').
        Returns how many assignments were affected."""
        affected = self.repo.assignment_count(course_id)
        self.repo.delete(course_id)
        return affected

    def get(self, course_id: int) -> Course | None:
        return self.repo.get(course_id)

    def list(self) -> list[Course]:
        return self.repo.list_all()

    def list_with_counts(self) -> list[tuple[Course, int]]:
        return self.repo.list_with_counts()
