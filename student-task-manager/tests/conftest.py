from datetime import datetime

import pytest

from student_task_manager.services.container import build_services

# A fixed "now" so tests never depend on the real clock.
NOW = datetime(2026, 10, 15, 12, 0)


class Clock:
    def __init__(self, now: datetime = NOW):
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def svc(clock):
    services = build_services(":memory:", clock=clock)
    yield services
    services.close()
