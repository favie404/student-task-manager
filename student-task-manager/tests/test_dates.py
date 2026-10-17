from datetime import date, datetime, time

import pytest

from student_task_manager.utils.dates import describe_due, format_due, parse_date, parse_time


def test_parse_date_accepts_strings_and_dates():
    assert parse_date("2026-10-31") == date(2026, 10, 31)
    assert parse_date(date(2026, 1, 2)) == date(2026, 1, 2)
    assert parse_date(datetime(2026, 1, 2, 5, 5)) == date(2026, 1, 2)


@pytest.mark.parametrize("bad", ["31/10/2026", "2026-13-01", "2026-02-30", "", None, 5])
def test_parse_date_rejects_garbage(bad):
    with pytest.raises(ValueError):
        parse_date(bad)


def test_parse_time():
    assert parse_time("14:30") == time(14, 30)
    assert parse_time("") is None
    assert parse_time(None) is None
    assert parse_time("  09:05 ") == time(9, 5)


@pytest.mark.parametrize("bad", ["25:00", "9", "noon", "12:60"])
def test_parse_time_rejects_garbage(bad):
    with pytest.raises(ValueError):
        parse_time(bad)


def test_leap_day_is_valid():
    assert parse_date("2028-02-29") == date(2028, 2, 29)
    with pytest.raises(ValueError):
        parse_date("2027-02-29")


def test_format_due():
    assert format_due(date(2026, 10, 5), time(9, 0)) == "05 Oct 2026  09:00"
    assert format_due(date(2026, 10, 5), None) == "05 Oct 2026"


def test_describe_due():
    now = datetime(2026, 10, 15, 12, 0)
    assert describe_due(datetime(2026, 10, 15, 15, 20), now) == "Due in 3h 20m"
    assert describe_due(datetime(2026, 10, 17, 15, 0), now) == "Due in 2d 3h"
    assert describe_due(datetime(2026, 10, 15, 12, 45), now) == "Due in 45m"
    assert describe_due(datetime(2026, 10, 15, 12, 0), now) == "Due now"
    assert describe_due(datetime(2026, 10, 13, 8, 0), now) == "Overdue by 2d 4h"
