"""The main window: sidebar navigation, page switching and the reminder timer."""
from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ..config import APP_NAME, APP_VERSION
from ..services.container import Services
from .assignments_view import AssignmentsView
from .calendar_view import CalendarView
from .courses_view import CoursesView
from .dashboard_view import DashboardView
from .reminder_popup import ReminderPopup
from .settings_view import SettingsView
from .theme import Theme, scale

log = logging.getLogger(__name__)

NAV_ITEMS = [("dashboard", "Dashboard"), ("assignments", "Assignments"),
             ("courses", "Courses"), ("calendar", "Calendar"), ("settings", "Settings")]
FIRST_REMINDER_CHECK_MS = 1500


class MainWindow:
    def __init__(self, root: tk.Tk, services: Services, theme: Theme, start_timer: bool = True):
        self.root = root
        self.services = services
        self.theme = theme
        self.current = "dashboard"
        self._timer_id: str | None = None
        self._popup: ReminderPopup | None = None

        root.title(APP_NAME)
        root.geometry("1180x740")
        root.minsize(1080, 640)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        root.report_callback_exception = self._on_error

        # ---- sidebar
        sidebar = ttk.Frame(root, style="Sidebar.TFrame", width=scale(root, 230))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="Student\nTask Manager", style="Sidebar.TLabel",
                  font=theme.fonts["h2"], justify="left").pack(anchor="w", padx=20, pady=(26, 22))
        self.nav_buttons: dict[str, ttk.Button] = {}
        for key, text in NAV_ITEMS:
            button = ttk.Button(sidebar, text=text, style="Nav.TButton",
                                command=lambda k=key: self.show(k))
            button.pack(fill="x")
            self.nav_buttons[key] = button
        ttk.Label(sidebar, text=f"v{APP_VERSION}", style="SidebarMuted.TLabel").pack(
            side="bottom", anchor="w", padx=20, pady=16)

        # ---- pages (all stacked in one cell; we raise the one we want)
        container = ttk.Frame(root)
        container.grid(row=0, column=1, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.views = {
            "dashboard": DashboardView(container, self),
            "assignments": AssignmentsView(container, self),
            "courses": CoursesView(container, self),
            "calendar": CalendarView(container, self),
            "settings": SettingsView(container, self),
        }
        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        root.bind("<Control-n>", lambda _e: self.open_new_assignment())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.show("dashboard")
        if start_timer:
            self.restart_reminder_timer(first_delay_ms=FIRST_REMINDER_CHECK_MS)

    # ---- navigation -------------------------------------------------
    def show(self, name: str) -> None:
        self.current = name
        for key, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if key == name else "Nav.TButton")
        view = self.views[name]
        view.refresh()
        view.tkraise()

    def refresh_current(self) -> None:
        self.views[self.current].refresh()

    def open_new_assignment(self) -> None:
        self.show("assignments")
        self.views["assignments"].add()
        self.refresh_current()

    # ---- reminders --------------------------------------------------
    def restart_reminder_timer(self, first_delay_ms: int | None = None) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
        delay = first_delay_ms if first_delay_ms is not None else \
            self.services.settings.check_interval_seconds * 1000
        self._timer_id = self.root.after(delay, self._check_reminders)

    def _check_reminders(self) -> None:
        try:
            popup_open = self._popup is not None and self._popup.winfo_exists()
            if not popup_open:
                now = datetime.now()
                due = self.services.reminders.due_reminders(now)
                if due:
                    self.services.reminders.mark_shown(due, now)
                    self._popup = ReminderPopup(self.root, self, due)
        except Exception:  # never let a problem stop the timer
            log.exception("Reminder check failed")
        finally:
            self.restart_reminder_timer()

    # ---- lifecycle --------------------------------------------------
    def _on_error(self, exc_type, exc, tb) -> None:
        log.error("Unhandled error in UI callback", exc_info=(exc_type, exc, tb))
        messagebox.showerror("Something went wrong",
                             f"{exc_type.__name__}: {exc}\n\nDetails were saved to the log file.",
                             parent=self.root)

    def close(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None
        try:
            self.services.close()
        finally:
            self.root.destroy()
