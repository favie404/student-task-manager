import pytest

from student_task_manager.services.errors import ValidationError


def test_defaults(svc):
    s = svc.settings
    assert s.reminders_enabled and s.remind_overdue
    assert s.default_reminder_minutes == 1440 and s.check_interval_seconds == 60


def test_update_persists(svc):
    svc.settings.update(reminders_enabled=False, default_reminder_minutes=60,
                        check_interval_seconds=300, remind_overdue=False)
    s = svc.settings
    assert not s.reminders_enabled and not s.remind_overdue
    assert (s.default_reminder_minutes, s.check_interval_seconds) == (60, 300)


@pytest.mark.parametrize("minutes,interval", [(0, 60), (10**7, 60), (60, 1), (60, 99999)])
def test_update_validation(svc, minutes, interval):
    with pytest.raises(ValidationError):
        svc.settings.update(reminders_enabled=True, default_reminder_minutes=minutes,
                            check_interval_seconds=interval, remind_overdue=True)
