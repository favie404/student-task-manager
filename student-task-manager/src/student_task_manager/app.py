"""Application start-up."""
from __future__ import annotations

import logging
import sqlite3
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path
from tkinter import messagebox

from .config import data_dir, default_db_path
from .db.migrations import DatabaseTooNewError
from .services.container import build_services
from .ui.main_window import MainWindow
from .ui.theme import apply_theme


def setup_logging() -> Path:
    log_file = data_dir() / "app.log"
    handler = RotatingFileHandler(log_file, maxBytes=500_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    return log_file


def run(db_path: str | Path | None = None) -> None:
    setup_logging()
    path = Path(db_path) if db_path else default_db_path()
    root = tk.Tk()
    root.withdraw()  # hide the empty window until everything is ready
    try:
        services = build_services(path)
    except DatabaseTooNewError as exc:
        messagebox.showerror("Cannot open data file", str(exc))
        root.destroy()
        return
    except sqlite3.Error as exc:
        logging.getLogger(__name__).exception("Could not open database %s", path)
        messagebox.showerror("Cannot open data file",
                             f"The database at\n{path}\ncould not be opened:\n{exc}")
        root.destroy()
        return
    theme = apply_theme(root)
    MainWindow(root, services, theme)
    root.deiconify()
    root.mainloop()
