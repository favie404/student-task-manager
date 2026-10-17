from student_task_manager.services.sample_data import load_sample_data


def test_empty_database(svc):
    s = svc.stats.dashboard()
    assert (s.total, s.completed, s.pending, s.overdue, s.completion_percent) == (0, 0, 0, 0, 0)
    assert s.upcoming == [] and s.by_course == []


def test_counts_and_percentage(svc):
    # clock: 2026-10-15 12:00
    svc.assignments.create(title="done", due_date="2026-10-01", status="completed")
    svc.assignments.create(title="overdue", due_date="2026-10-14")
    svc.assignments.create(title="soon", due_date="2026-10-17")
    svc.assignments.create(title="in 7 days", due_date="2026-10-22", due_time="12:00")
    svc.assignments.create(title="far", due_date="2026-11-30")
    s = svc.stats.dashboard()
    assert s.total == 5 and s.completed == 1 and s.pending == 4
    assert s.overdue == 1
    assert s.due_this_week == 2          # "soon" and "in 7 days"
    assert s.completion_percent == 20


def test_completed_items_are_never_overdue(svc):
    svc.assignments.create(title="old", due_date="2020-01-01", status="completed")
    assert svc.stats.dashboard().overdue == 0


def test_upcoming_excludes_completed_and_is_limited(svc):
    for i in range(10):
        svc.assignments.create(title=f"t{i}", due_date=f"2026-10-{20 + i}")
    svc.assignments.create(title="done", due_date="2026-10-01", status="completed")
    up = svc.stats.dashboard(upcoming_limit=4).upcoming
    assert [a.title for a in up] == ["t0", "t1", "t2", "t3"]


def test_by_course_includes_unlinked(svc):
    c = svc.courses.add("A1", "One")
    svc.assignments.create(title="a", due_date="2026-10-20", course_id=c.id, status="completed")
    svc.assignments.create(title="b", due_date="2026-10-21", course_id=c.id)
    svc.assignments.create(title="c", due_date="2026-10-22")
    groups = {g.code: (g.total, g.completed, g.percent) for g in svc.stats.dashboard().by_course}
    assert groups == {"A1": (2, 1, 50), "No course": (1, 0, 0)}


def test_sample_data_loads(svc):
    n = load_sample_data(svc.courses, svc.assignments, today=svc.assignments.clock().date())
    s = svc.stats.dashboard()
    assert n == s.total == 8
    assert len(svc.courses.list()) == 4
    assert s.overdue >= 1
