from datetime import date, datetime, time

import pytest

from student_task_manager.models import NO_COURSE, AssignmentFilter
from student_task_manager.services.errors import ValidationError


def make(svc, title="Essay", due="2026-10-20", **kw):
    return svc.assignments.create(title=title, due_date=due, **kw)


def titles(items):
    return [a.title for a in items]


# ---- create / validation ---------------------------------------------
def test_create_defaults(svc):
    a = make(svc, due_time="14:30")
    assert a.id and a.status == "pending" and a.priority == "medium"
    assert a.due_date == date(2026, 10, 20) and a.due_time == time(14, 30)
    assert a.completed_at is None


@pytest.mark.parametrize(
    "fields",
    [
        {"title": "   ", "due_date": "2026-10-20"},
        {"title": "x" * 201, "due_date": "2026-10-20"},
        {"title": "ok", "due_date": "20-10-2026"},
        {"title": "ok", "due_date": "2026-10-20", "due_time": "25:00"},
        {"title": "ok", "due_date": "2026-10-20", "priority": "urgent"},
        {"title": "ok", "due_date": "2026-10-20", "status": "done"},
        {"title": "ok", "due_date": "2026-10-20", "course_id": 999},
        {"title": "ok", "due_date": "2026-10-20", "reminder_minutes": 0},
        {"title": "ok", "due_date": "2026-10-20", "reminder_minutes": "abc"},
    ],
)
def test_validation_errors(svc, fields):
    with pytest.raises(ValidationError):
        svc.assignments.create(**fields)


def test_title_is_trimmed_and_long_text_is_ok(svc):
    a = make(svc, title="  Lab 1  ", description="d" * 5000)
    assert a.title == "Lab 1" and len(a.description) == 5000


def test_unicode_title(svc):
    assert make(svc, title="Mtihani wa Mtandao - 課題").title == "Mtihani wa Mtandao - 課題"


# ---- update / status ---------------------------------------------------
def test_update(svc):
    c = svc.courses.add("A1", "One")
    a = make(svc)
    got = svc.assignments.update(
        a.id, title="New", due_date="2026-11-01", due_time="08:00", course_id=c.id,
        priority="high", status="in_progress", description="notes", reminder_minutes=60,
    )
    assert (got.title, got.course_code, got.priority, got.reminder_minutes) == ("New", "A1", "high", 60)


def test_update_missing_assignment(svc):
    with pytest.raises(ValidationError):
        svc.assignments.update(123, title="x", due_date="2026-10-20")


def test_completing_sets_and_clears_completed_at(svc, clock):
    a = make(svc)
    done = svc.assignments.set_status(a.id, "completed")
    assert done.completed_at == clock.now
    reopened = svc.assignments.set_status(a.id, "pending")
    assert reopened.completed_at is None


def test_update_keeps_original_completed_at(svc, clock):
    a = make(svc, status="completed")
    clock.now = datetime(2026, 10, 16, 9, 0)
    again = svc.assignments.update(a.id, title="renamed", due_date="2026-10-20", status="completed")
    assert again.completed_at == datetime(2026, 10, 15, 12, 0)


def test_toggle_complete(svc):
    a = make(svc)
    assert svc.assignments.toggle_complete(a.id).is_completed
    assert not svc.assignments.toggle_complete(a.id).is_completed


def test_delete(svc):
    a = make(svc)
    svc.assignments.delete(a.id)
    assert svc.assignments.get(a.id) is None


# ---- ordering & filters -------------------------------------------------
def test_ordering_by_due_then_time(svc):
    make(svc, "late", "2026-10-21")
    make(svc, "noon", "2026-10-20", due_time="12:00")
    make(svc, "morning", "2026-10-20", due_time="08:00")
    make(svc, "no time", "2026-10-20")
    assert titles(svc.assignments.list()) == ["morning", "noon", "no time", "late"]


def test_search_title_description_and_course(svc):
    c = svc.courses.add("NET 1", "Network Administration")
    make(svc, "Subnetting", course_id=c.id)
    make(svc, "Essay", description="about ROUTING protocols")
    make(svc, "Other")
    f = lambda s: titles(svc.assignments.list(AssignmentFilter(search=s)))
    assert f("subnet") == ["Subnetting"]            # case-insensitive
    assert f("routing") == ["Essay"]                # description
    assert f("administration") == ["Subnetting"]    # course name
    assert f("net 1") == ["Subnetting"]             # course code
    assert f("zzz") == []


def test_search_treats_wildcards_literally(svc):
    make(svc, "100% done")
    make(svc, "plain")
    make(svc, "a_b")
    f = lambda s: titles(svc.assignments.list(AssignmentFilter(search=s)))
    assert f("%") == ["100% done"]
    assert f("_") == ["a_b"]


def test_filter_by_course_and_no_course(svc):
    c = svc.courses.add("A1", "One")
    make(svc, "in course", course_id=c.id)
    make(svc, "free")
    assert titles(svc.assignments.list(AssignmentFilter(course_id=c.id))) == ["in course"]
    assert titles(svc.assignments.list(AssignmentFilter(course_id=NO_COURSE))) == ["free"]


def test_filter_by_status_priority(svc):
    make(svc, "p", priority="low")
    make(svc, "ip", status="in_progress", priority="high")
    make(svc, "c", status="completed", priority="high")
    assert titles(svc.assignments.list(AssignmentFilter(status="in_progress"))) == ["ip"]
    assert titles(svc.assignments.list(AssignmentFilter(status="completed"))) == ["c"]
    assert sorted(titles(svc.assignments.list(AssignmentFilter(priority="high")))) == ["c", "ip"]


def test_filter_overdue(svc):
    # clock is 2026-10-15 12:00
    make(svc, "yesterday", "2026-10-14")
    make(svc, "today earlier", "2026-10-15", due_time="09:00")
    make(svc, "today later", "2026-10-15", due_time="18:00")
    make(svc, "today no time", "2026-10-15")
    make(svc, "old but done", "2026-10-01", status="completed")
    got = titles(svc.assignments.list(AssignmentFilter(status="overdue")))
    assert got == ["yesterday", "today earlier"]


def test_filter_date_range_is_inclusive(svc):
    for d in ("2026-10-09", "2026-10-10", "2026-10-15", "2026-10-16"):
        make(svc, d, d)
    f = AssignmentFilter(due_from=date(2026, 10, 10), due_to=date(2026, 10, 15))
    assert titles(svc.assignments.list(f)) == ["2026-10-10", "2026-10-15"]


def test_filters_combine(svc):
    c = svc.courses.add("A1", "One")
    make(svc, "match", course_id=c.id, priority="high")
    make(svc, "wrong priority", course_id=c.id, priority="low")
    make(svc, "no course", priority="high")
    f = AssignmentFilter(course_id=c.id, priority="high", search="mat")
    assert titles(svc.assignments.list(f)) == ["match"]


def test_month_boundary_and_year_rollover(svc):
    make(svc, "nye", "2026-12-31", due_time="23:59")
    make(svc, "ny", "2027-01-01")
    assert titles(svc.assignments.list()) == ["nye", "ny"]
