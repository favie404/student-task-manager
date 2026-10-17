"""Settings: reminders, data tools, about."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..config import APP_NAME, APP_VERSION
from ..models import REMINDER_PRESETS, minutes_label
from ..services.errors import ValidationError
from ..services.sample_data import load_sample_data
from ..services.settings_service import INTERVAL_CHOICES


class SettingsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        ttk.Label(self, text="Settings", style="H1.TLabel").pack(anchor="w")

        # ---- reminders card
        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=(16, 12))
        ttk.Label(card, text="Deadline reminders", style="CardH2.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.enabled_var = tk.BooleanVar()
        ttk.Checkbutton(card, text="Show reminder pop-ups while the app is open",
                        variable=self.enabled_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(card, text="Remind me this long before a deadline", style="Card.TLabel").grid(
            row=2, column=0, sticky="w", pady=8, padx=(0, 16))
        self._lead_options = [m for m, _ in REMINDER_PRESETS]
        self.lead_cb = ttk.Combobox(card, state="readonly", width=16,
                                    values=[label for _, label in REMINDER_PRESETS])
        self.lead_cb.grid(row=2, column=1, sticky="w")

        ttk.Label(card, text="Check for due reminders every", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=8, padx=(0, 16))
        self._interval_options = [s for s, _ in INTERVAL_CHOICES]
        self.interval_cb = ttk.Combobox(card, state="readonly", width=16,
                                        values=[label for _, label in INTERVAL_CHOICES])
        self.interval_cb.grid(row=3, column=1, sticky="w")

        self.overdue_var = tk.BooleanVar()
        ttk.Checkbutton(card, text="Also remind me about assignments that are already overdue",
                        variable=self.overdue_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Button(card, text="Save settings", style="Accent.TButton", command=self.save).grid(
            row=5, column=0, sticky="w", pady=(14, 0))
        self.saved_label = ttk.Label(card, style="Card.TLabel", foreground=app.theme.colors["success"])
        self.saved_label.grid(row=5, column=1, sticky="w", pady=(14, 0))

        # ---- data card
        data = ttk.Frame(self, style="Card.TFrame", padding=20)
        data.pack(fill="x", pady=(0, 12))
        ttk.Label(data, text="Your data", style="CardH2.TLabel").pack(anchor="w")
        ttk.Label(data, text="Everything is stored in this file on your computer:",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(6, 2))
        # keep a reference (self.) - Tkinter forgets a variable once Python discards it
        self.path_var = tk.StringVar(value=app.services.db_path)
        ttk.Entry(data, textvariable=self.path_var, state="readonly").pack(fill="x")
        row = ttk.Frame(data, style="Plain.TFrame")
        row.pack(fill="x", pady=(12, 0))
        ttk.Button(row, text="Load sample data", command=self.load_samples).pack(side="left")
        ttk.Button(row, text="Show dismissed reminders again", command=self.reset_reminders).pack(
            side="left", padx=8)

        ttk.Label(self, text=f"{APP_NAME}  v{APP_VERSION}", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def refresh(self) -> None:
        s = self.app.services.settings
        self.saved_label.configure(text="")
        self.enabled_var.set(s.reminders_enabled)
        self.overdue_var.set(s.remind_overdue)
        minutes = s.default_reminder_minutes
        if minutes not in self._lead_options:       # a value set earlier outside the presets
            self._lead_options.append(minutes)
            self.lead_cb.configure(values=list(self.lead_cb.cget("values")) + [minutes_label(minutes)])
        self.lead_cb.current(self._lead_options.index(minutes))
        seconds = s.check_interval_seconds
        if seconds not in self._interval_options:
            self._interval_options.append(seconds)
            self.interval_cb.configure(values=list(self.interval_cb.cget("values")) + [f"{seconds} seconds"])
        self.interval_cb.current(self._interval_options.index(seconds))

    def save(self) -> None:
        try:
            self.app.services.settings.update(
                reminders_enabled=self.enabled_var.get(),
                default_reminder_minutes=self._lead_options[self.lead_cb.current()],
                check_interval_seconds=self._interval_options[self.interval_cb.current()],
                remind_overdue=self.overdue_var.get(),
            )
        except ValidationError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return
        self.app.restart_reminder_timer()
        self.saved_label.configure(text="Saved")

    def load_samples(self) -> None:
        if messagebox.askyesno(
                "Load sample data",
                "Add 4 sample courses and 8 sample assignments?\n\n"
                "Your existing data is kept. You can delete the samples later.", parent=self):
            load_sample_data(self.app.services.courses, self.app.services.assignments)
            messagebox.showinfo("Done", "Sample data added.", parent=self)

    def reset_reminders(self) -> None:
        self.app.services.reminders.reset()
        messagebox.showinfo("Done", "Dismissed and snoozed reminders will be shown again "
                                    "the next time the app checks.", parent=self)
