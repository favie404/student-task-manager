"""Typed access to the key/value settings table."""
from __future__ import annotations

from ..db.repositories import SettingsRepo
from .errors import ValidationError

DEFAULTS = {
    "reminders_enabled": "1",
    "default_reminder_minutes": "1440",   # remind 1 day before
    "check_interval_seconds": "60",       # how often the app looks for due reminders
    "remind_overdue": "1",
}

INTERVAL_CHOICES = [
    (30, "30 seconds"),
    (60, "1 minute"),
    (300, "5 minutes"),
    (900, "15 minutes"),
]


class SettingsService:
    def __init__(self, repo: SettingsRepo):
        self.repo = repo

    def _raw(self, key: str) -> str:
        value = self.repo.get(key)
        return DEFAULTS[key] if value is None else value

    def _int(self, key: str) -> int:
        try:
            return int(self._raw(key))
        except ValueError:
            return int(DEFAULTS[key])

    @property
    def reminders_enabled(self) -> bool:
        return self._raw("reminders_enabled") == "1"

    @property
    def default_reminder_minutes(self) -> int:
        return self._int("default_reminder_minutes")

    @property
    def check_interval_seconds(self) -> int:
        return self._int("check_interval_seconds")

    @property
    def remind_overdue(self) -> bool:
        return self._raw("remind_overdue") == "1"

    def update(
        self,
        *,
        reminders_enabled: bool,
        default_reminder_minutes: int,
        check_interval_seconds: int,
        remind_overdue: bool,
    ) -> None:
        if not 1 <= int(default_reminder_minutes) <= 60 * 24 * 30:
            raise ValidationError("Reminder time must be between 1 minute and 30 days.")
        if not 10 <= int(check_interval_seconds) <= 3600:
            raise ValidationError("Check interval must be between 10 seconds and 1 hour.")
        self.repo.set("reminders_enabled", "1" if reminders_enabled else "0")
        self.repo.set("default_reminder_minutes", str(int(default_reminder_minutes)))
        self.repo.set("check_interval_seconds", str(int(check_interval_seconds)))
        self.repo.set("remind_overdue", "1" if remind_overdue else "0")
