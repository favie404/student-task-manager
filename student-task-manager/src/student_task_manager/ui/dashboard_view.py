"""Dashboard: statistics, overall progress, upcoming deadlines, per-course progress."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ..utils.dates import describe_due


class DashboardView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        c = app.theme.colors

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Dashboard", style="H1.TLabel").pack(side="left")
        self.date_label = ttk.Label(header, style="Muted.TLabel")
        self.date_label.pack(side="left", padx=16, pady=(10, 0))
        ttk.Button(header, text="+ New assignment", style="Accent.TButton",
                   command=app.open_new_assignment).pack(side="right")

        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=(18, 12))
        self.card_values: dict[str, ttk.Label] = {}
        definitions = [
            ("total", "Total assignments", c["text"]),
            ("completed", "Completed", c["success"]),
            ("pending", "Pending", c["accent"]),
            ("overdue", "Overdue", c["danger"]),
            ("week", "Due in 7 days", c["warning"]),
        ]
        for i, (key, caption, color) in enumerate(definitions):
            cards.columnconfigure(i, weight=1, uniform="cards")
            card = ttk.Frame(cards, style="Card.TFrame", padding=16)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            value = ttk.Label(card, text="0", style="CardNumber.TLabel", foreground=color)
            value.pack(anchor="w")
            ttk.Label(card, text=caption, style="CardMuted.TLabel").pack(anchor="w")
            self.card_values[key] = value

        progress = ttk.Frame(self, style="Card.TFrame", padding=16)
        progress.pack(fill="x", pady=(0, 12))
        self.progress_label = ttk.Label(progress, style="CardH2.TLabel")
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(progress, style="Success.Horizontal.TProgressbar",
                                            maximum=100, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(10, 0))

        lower = ttk.Frame(self)
        lower.pack(fill="both", expand=True)
        lower.rowconfigure(0, weight=1)
        lower.columnconfigure(0, weight=3, uniform="lower")
        lower.columnconfigure(1, weight=2, uniform="lower")

        up_card = ttk.Frame(lower, style="Card.TFrame", padding=16)
        up_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(up_card, text="Upcoming deadlines", style="CardH2.TLabel").pack(anchor="w")
        self.upcoming_body = ttk.Frame(up_card, style="Plain.TFrame")
        self.upcoming_body.pack(fill="both", expand=True, pady=(8, 0))

        co_card = ttk.Frame(lower, style="Card.TFrame", padding=16)
        co_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(co_card, text="Progress by course", style="CardH2.TLabel").pack(anchor="w")
        self.courses_body = ttk.Frame(co_card, style="Plain.TFrame")
        self.courses_body.pack(fill="both", expand=True, pady=(8, 0))

    @staticmethod
    def _clear(frame: ttk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def refresh(self) -> None:
        now = datetime.now()
        stats = self.app.services.stats.dashboard()
        c = self.app.theme.colors
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))

        values = {"total": stats.total, "completed": stats.completed, "pending": stats.pending,
                  "overdue": stats.overdue, "week": stats.due_this_week}
        for key, label in self.card_values.items():
            label.configure(text=str(values[key]))

        self.progress_bar["value"] = stats.completion_percent
        if stats.total:
            self.progress_label.configure(
                text=f"Overall completion: {stats.completion_percent}%  "
                     f"({stats.completed} of {stats.total} completed)")
        else:
            self.progress_label.configure(text="Overall completion: no assignments yet")

        # upcoming deadlines
        self._clear(self.upcoming_body)
        if not stats.upcoming:
            text = ("Nothing due. Add an assignment, or load sample data in Settings."
                    if not stats.total else "All caught up - no open assignments!")
            ttk.Label(self.upcoming_body, text=text, style="CardMuted.TLabel").pack(anchor="w")
        for a in stats.upcoming:
            row = ttk.Frame(self.upcoming_body, style="Plain.TFrame")
            row.pack(fill="x", pady=4)
            tk.Frame(row, width=5, height=34, background=a.course_color or "#9CA3AF").pack(
                side="left", padx=(0, 10))
            text_col = ttk.Frame(row, style="Plain.TFrame")
            text_col.pack(side="left", fill="x", expand=True)
            ttk.Label(text_col, text=a.title, style="Card.TLabel",
                      font=self.app.theme.fonts["bold"]).pack(anchor="w")
            overdue = a.is_overdue(now)
            course = a.course_code or "No course"
            ttk.Label(text_col, text=f"{course}  -  {describe_due(a.due_datetime, now)}",
                      style="Danger.TLabel" if overdue else "CardMuted.TLabel").pack(anchor="w")

        # per-course progress
        self._clear(self.courses_body)
        if not stats.by_course:
            ttk.Label(self.courses_body, text="No courses yet.", style="CardMuted.TLabel").pack(anchor="w")
        for g in stats.by_course:
            block = ttk.Frame(self.courses_body, style="Plain.TFrame")
            block.pack(fill="x", pady=5)
            top = ttk.Frame(block, style="Plain.TFrame")
            top.pack(fill="x")
            tk.Frame(top, width=10, height=10, background=g.color).pack(side="left", padx=(0, 8))
            ttk.Label(top, text=g.code, style="Card.TLabel").pack(side="left")
            ttk.Label(top, text=f"{g.completed}/{g.total}  ({g.percent}%)",
                      style="CardMuted.TLabel").pack(side="right")
            bar = ttk.Progressbar(block, style="Accent.Horizontal.TProgressbar", maximum=100)
            bar["value"] = g.percent
            bar.pack(fill="x", pady=(4, 0))
