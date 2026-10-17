"""Small date/time helpers shared by services and UI."""
from __future__ import annotations

from datetime import date, datetime, time

DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def parse_date(value) -> date:
    """Accept a date or a 'YYYY-MM-DD' string. Raise ValueError otherwise."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), DATE_FMT).date()
        except ValueError:
            pass
    raise ValueError("Date must look like YYYY-MM-DD (for example 2026-10-31).")


def parse_time(value) -> time | None:
    """Accept None, '', a time, or 'HH:MM'. Empty means 'no specific time'."""
    if value is None:
        return None
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        try:
            return datetime.strptime(text, TIME_FMT).time()
        except ValueError:
            pass
    raise ValueError("Time must look like HH:MM in 24-hour format (for example 14:30).")


def to_db_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_FMT)


def from_db_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_FMT)


def floor_minute(value: datetime) -> datetime:
    return value.replace(second=0, microsecond=0)


def format_due(due_date: date, due_time: time | None) -> str:
    text = due_date.strftime("%d %b %Y")
    return f"{text}  {due_time.strftime(TIME_FMT)}" if due_time else text


def _span(seconds: int) -> str:
    minutes = seconds // 60
    days, rem = divmod(minutes, 1440)
    hours, mins = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m"
    return "less than a minute"


def describe_due(due: datetime, now: datetime) -> str:
    """Human text such as 'Due in 3h 20m' or 'Overdue by 2d 4h'."""
    delta = due - floor_minute(now)
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return f"Overdue by {_span(-seconds)}"
    if seconds == 0:
        return "Due now"
    return f"Due in {_span(seconds)}"
