"""Where the app keeps its data. Uses the correct folder for each OS.

Windows: C:\\Users\\<you>\\AppData\\Local\\StudentTaskManager
Linux:   ~/.local/share/StudentTaskManager

Set the STM_DATA_DIR environment variable to use a different folder
(handy for testing so you do not touch your real data).
"""
from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_data_dir

from . import __version__

APP_NAME = "Student Task Manager"
APP_SLUG = "StudentTaskManager"
APP_VERSION = __version__


def data_dir() -> Path:
    override = os.environ.get("STM_DATA_DIR")
    path = Path(override) if override else Path(user_data_dir(APP_SLUG, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    return data_dir() / "tasks.db"
