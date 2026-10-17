"""Optional demo data so you can see the dashboard and calendar filled in."""
from __future__ import annotations

from datetime import date, time, timedelta

from .assignment_service import AssignmentService
from .course_service import CourseService

_COURSES = [
    ("BCS 2101", "Network Administration", "Dr. Kamau", "#3D5AFE"),
    ("BCS 2102", "Database Systems", "Ms. Wanjiru", "#16A34A"),
    ("BCS 2103", "Object Oriented Programming", "Mr. Otieno", "#F59E0B"),
    ("BCS 2104", "Telecommunication Systems", "Dr. Achieng", "#DB2777"),
]

# (course index, title, day offset, time, priority, status)
_ASSIGNMENTS = [
    (0, "Subnetting worksheet", -2, time(17, 0), "high", "pending"),
    (1, "ER diagram for library system", -5, time(12, 0), "medium", "completed"),
    (2, "Java Servlets CAT", 0, time(23, 0), "high", "in_progress"),
    (3, "Switching theory assignment", 1, None, "medium", "pending"),
    (1, "SQL joins practical", 3, time(9, 0), "medium", "pending"),
    (0, "Configure DHCP lab report", 6, time(16, 30), "low", "pending"),
    (2, "OOP group project demo", 12, time(10, 0), "high", "pending"),
    (3, "Transmission systems revision quiz", 20, None, "low", "pending"),
]


def load_sample_data(courses: CourseService, assignments: AssignmentService,
                     today: date | None = None) -> int:
    """Add demo courses and assignments. Returns how many assignments were added."""
    today = today or date.today()
    ids = []
    for code, name, instructor, color in _COURSES:
        existing = next((c for c in courses.list() if c.code.lower() == code.lower()), None)
        ids.append(existing.id if existing else courses.add(code, name, instructor, color).id)
    for idx, title, offset, due_time, priority, status in _ASSIGNMENTS:
        assignments.create(
            title=title, due_date=today + timedelta(days=offset), due_time=due_time,
            course_id=ids[idx], priority=priority, status=status,
            description="Sample assignment - safe to delete.",
        )
    return len(_ASSIGNMENTS)
