import pytest

from student_task_manager.services.errors import ValidationError


def test_add_and_list(svc):
    c = svc.courses.add("BCS 2101", "Network Administration", "Dr K", "#112233")
    assert c.id
    assert [x.code for x in svc.courses.list()] == ["BCS 2101"]


@pytest.mark.parametrize(
    "code,name,color",
    [("", "Name", "#112233"), ("C1", "  ", "#112233"), ("C1", "N", "red"),
     ("C1", "N", "#12345"), ("X" * 21, "N", "#112233")],
)
def test_validation(svc, code, name, color):
    with pytest.raises(ValidationError):
        svc.courses.add(code, name, "", color)


def test_duplicate_code_is_rejected_case_insensitively(svc):
    svc.courses.add("BCS 1", "One")
    with pytest.raises(ValidationError):
        svc.courses.add("bcs 1", "Two")


def test_update(svc):
    c = svc.courses.add("A1", "Old")
    svc.courses.update(c.id, "A1", "New", "Prof", "#abcdef")
    got = svc.courses.get(c.id)
    assert (got.name, got.instructor, got.color) == ("New", "Prof", "#abcdef")


def test_update_to_duplicate_code_fails(svc):
    svc.courses.add("A1", "One")
    b = svc.courses.add("B1", "Two")
    with pytest.raises(ValidationError):
        svc.courses.update(b.id, "A1", "Two")


def test_delete_keeps_assignments_with_no_course(svc):
    c = svc.courses.add("A1", "One")
    a = svc.assignments.create(title="HW", due_date="2026-10-20", course_id=c.id)
    affected = svc.courses.delete(c.id)
    assert affected == 1
    kept = svc.assignments.get(a.id)
    assert kept is not None and kept.course_id is None


def test_counts(svc):
    c = svc.courses.add("A1", "One")
    svc.courses.add("B1", "Two")
    svc.assignments.create(title="x", due_date="2026-10-20", course_id=c.id)
    svc.assignments.create(title="y", due_date="2026-10-21", course_id=c.id)
    counts = {course.code: n for course, n in svc.courses.list_with_counts()}
    assert counts == {"A1": 2, "B1": 0}
