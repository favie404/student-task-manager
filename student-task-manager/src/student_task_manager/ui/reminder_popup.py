"""The window that appears when a deadline is close."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ..services.reminder_service import DueReminder
from ..utils.dates import describe_due

SNOOZE_CHOICES = [(5, "5 minutes"), (10, "10 minutes"), (30, "30 minutes"), (60, "1 hour")]


class ReminderPopup(tk.Toplevel):
    def __init__(self, root: tk.Tk, app, reminders: list[DueReminder]):
        super().__init__(root)
        self.app = app
        self.reminders = {str(r.assignment.id): r for r in reminders}
        self.title("Deadline reminders")
        self.configure(background=app.theme.colors["bg"])
        self.transient(root)
        self.minsize(560, 280)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda _e: self.destroy())

        body = ttk.Frame(self, padding=18)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Upcoming deadlines", style="H1.TLabel").pack(anchor="w")
        ttk.Label(body, text="These assignments need your attention.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        self.tree = ttk.Treeview(body, columns=("title", "course", "when"), show="headings",
                                 height=6, selectmode="browse")
        for col, text, width in (("title", "Assignment", 250), ("course", "Course", 110),
                                 ("when", "When", 150)):
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=width, anchor="w")
        self.tree.tag_configure("overdue", foreground=app.theme.colors["danger"])
        self.tree.pack(fill="both", expand=True)

        now = datetime.now()
        for r in reminders:
            a = r.assignment
            self.tree.insert("", "end", iid=str(a.id), tags=("overdue",) if r.overdue else (),
                             values=(a.title, a.course_code or "-", describe_due(a.due_datetime, now)))

        bar = ttk.Frame(body)
        bar.pack(fill="x", pady=(14, 0))
        ttk.Button(bar, text="Mark selected complete", style="Accent.TButton",
                   command=self._complete).pack(side="left")
        ttk.Button(bar, text="Dismiss", command=self.destroy).pack(side="right")
        ttk.Button(bar, text="Snooze all", command=self._snooze).pack(side="right", padx=(0, 8))
        self.snooze_cb = ttk.Combobox(bar, values=[lbl for _, lbl in SNOOZE_CHOICES],
                                      state="readonly", width=11)
        self.snooze_cb.current(1)
        self.snooze_cb.pack(side="right", padx=(0, 6))

        self.lift()
        try:
            self.attributes("-topmost", True)
            self.after(1000, lambda: self.winfo_exists() and self.attributes("-topmost", False))
        except tk.TclError:
            pass

    def _complete(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        iid = selected[0]
        self.app.services.assignments.set_status(int(iid), "completed")
        self.tree.delete(iid)
        self.reminders.pop(iid, None)
        self.app.refresh_current()
        if not self.reminders:
            self.destroy()

    def _snooze(self) -> None:
        minutes = SNOOZE_CHOICES[self.snooze_cb.current()][0]
        self.app.services.reminders.snooze(list(self.reminders.values()), minutes, datetime.now())
        self.destroy()
