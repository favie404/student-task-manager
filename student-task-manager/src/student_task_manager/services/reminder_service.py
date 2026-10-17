"""Decides which deadline reminders should pop up right now.

How it works (in plain words):
  * An open assignment is "due for a reminder" once   now >= deadline - lead time.
  * The lead time is the assignment's own setting, or the global default.
  * When we show a reminder we write it to `reminder_log`, so it is not shown
    again every minute. Snoozing sets a time after which it may appear again.
  * The log entry is tied to the deadline ("due_snapshot"). If you move the
    deadline, the old entry no longer matches, so you get reminded again.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..db.repositories import AssignmentRepo, ReminderRepo
from ..models import Assignment
from ..utils.dates import floor_minute, from_db_datetime
from .settings_service import SettingsService


@dataclass
class DueReminder:
    assignment: Assignment
    due_snapshot: str
    overdue: bool


def snapshot_for(a: Assignment) -> str:
    return a.due_datetime.strftime("%Y-%m-%d %H:%M")


class ReminderService:
    def __init__(self, assignments: AssignmentRepo, log: ReminderRepo, settings: SettingsService):
        self.assignments = assignments
        self.log = log
        self.settings = settings

    def lead_minutes_for(self, a: Assignment) -> int:
        if a.reminder_minutes is not None:
            return a.reminder_minutes
        return self.settings.default_reminder_minutes

    def due_reminders(self, now: datetime) -> list[DueReminder]:
        if not self.settings.reminders_enabled:
            return []
        now_min = floor_minute(now)
        result: list[DueReminder] = []
        for a in self.assignments.list_open():
            due = a.due_datetime
            overdue = due < now_min
            if overdue and not self.settings.remind_overdue:
                continue
            if now_min < due - timedelta(minutes=self.lead_minutes_for(a)):
                continue
            snapshot = snapshot_for(a)
            row = self.log.get(a.id, snapshot)
            if row is not None:
                if row["snoozed_until"] is None:
                    continue                      # already shown, not snoozed
                if from_db_datetime(row["snoozed_until"]) > now:
                    continue                      # still snoozed
            result.append(DueReminder(a, snapshot, overdue))
        return result

    def mark_shown(self, reminders: list[DueReminder], now: datetime) -> None:
        for r in reminders:
            self.log.mark_shown(r.assignment.id, r.due_snapshot, now)

    def snooze(self, reminders: list[DueReminder], minutes: int, now: datetime) -> None:
        until = now + timedelta(minutes=minutes)
        for r in reminders:
            self.log.snooze(r.assignment.id, r.due_snapshot, until)

    def reset(self) -> None:
        """Forget which reminders were shown (they may appear again)."""
        self.log.clear()
