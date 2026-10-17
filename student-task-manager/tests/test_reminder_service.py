from datetime import datetime, timedelta

# default lead time is 1 day; reminders look at "now" passed in explicitly
T0 = datetime(2026, 10, 15, 12, 0)


def make(svc, title="HW", due="2026-10-16", due_time="12:00", **kw):
    return svc.assignments.create(title=title, due_date=due, due_time=due_time, **kw)


def due_titles(svc, now):
    return [r.assignment.title for r in svc.reminders.due_reminders(now)]


def test_inside_lead_time_is_due(svc):
    make(svc)                       # due tomorrow 12:00, lead 1 day -> due right now
    assert due_titles(svc, T0) == ["HW"]


def test_outside_lead_time_is_not_due(svc):
    make(svc)
    assert due_titles(svc, T0 - timedelta(minutes=1)) == []


def test_completed_assignments_never_remind(svc):
    make(svc, status="completed")
    assert due_titles(svc, T0) == []


def test_disabled_reminders(svc):
    make(svc)
    svc.settings.update(reminders_enabled=False, default_reminder_minutes=1440,
                        check_interval_seconds=60, remind_overdue=True)
    assert due_titles(svc, T0) == []


def test_per_assignment_override_beats_default(svc):
    make(svc, reminder_minutes=60)          # only 1 hour before
    assert due_titles(svc, T0) == []
    assert due_titles(svc, datetime(2026, 10, 16, 11, 0)) == ["HW"]


def test_overdue_respects_setting(svc):
    make(svc, due="2026-10-14")
    assert [r.overdue for r in svc.reminders.due_reminders(T0)] == [True]
    svc.settings.update(reminders_enabled=True, default_reminder_minutes=1440,
                        check_interval_seconds=60, remind_overdue=False)
    assert due_titles(svc, T0) == []


def test_shown_reminder_does_not_repeat(svc):
    make(svc)
    first = svc.reminders.due_reminders(T0)
    svc.reminders.mark_shown(first, T0)
    assert due_titles(svc, T0 + timedelta(minutes=1)) == []
    assert due_titles(svc, T0 + timedelta(hours=5)) == []


def test_snooze_hides_then_reappears(svc):
    make(svc)
    r = svc.reminders.due_reminders(T0)
    svc.reminders.mark_shown(r, T0)
    svc.reminders.snooze(r, 10, T0)
    assert due_titles(svc, T0 + timedelta(minutes=9)) == []
    assert due_titles(svc, T0 + timedelta(minutes=10)) == ["HW"]


def test_reshown_after_snooze_does_not_repeat_again(svc):
    make(svc)
    r = svc.reminders.due_reminders(T0)
    svc.reminders.mark_shown(r, T0)
    svc.reminders.snooze(r, 10, T0)
    later = T0 + timedelta(minutes=11)
    again = svc.reminders.due_reminders(later)
    svc.reminders.mark_shown(again, later)
    assert due_titles(svc, later + timedelta(minutes=1)) == []


def test_moving_the_deadline_triggers_a_new_reminder(svc):
    a = make(svc)
    svc.reminders.mark_shown(svc.reminders.due_reminders(T0), T0)
    assert due_titles(svc, T0) == []
    svc.assignments.update(a.id, title="HW", due_date="2026-10-16", due_time="15:00")
    assert due_titles(svc, T0 + timedelta(hours=3)) == ["HW"]


def test_reset_brings_reminders_back(svc):
    make(svc)
    svc.reminders.mark_shown(svc.reminders.due_reminders(T0), T0)
    svc.reminders.reset()
    assert due_titles(svc, T0) == ["HW"]


def test_deleting_assignment_cleans_log(svc):
    a = make(svc)
    svc.reminders.mark_shown(svc.reminders.due_reminders(T0), T0)
    svc.assignments.delete(a.id)
    assert svc.conn.execute("SELECT COUNT(*) FROM reminder_log").fetchone()[0] == 0


def test_reminders_sorted_by_deadline(svc):
    make(svc, "later", due="2026-10-16", due_time="18:00", reminder_minutes=2000)
    make(svc, "sooner", due="2026-10-16", due_time="08:00")
    assert due_titles(svc, T0) == ["sooner", "later"]
