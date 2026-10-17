"""Pop-up forms for assignments and courses."""
from __future__ import annotations

import tkinter as tk
from datetime import timedelta
from tkinter import colorchooser, messagebox, ttk

from tkcalendar import DateEntry

from ..models import PRIORITIES, REMINDER_PRESETS, STATUSES, Assignment, Course, minutes_label
from ..services.container import Services
from ..services.errors import ValidationError

PRIORITY_LABELS = ["Low", "Medium", "High"]
STATUS_LABELS_LIST = ["Pending", "In progress", "Completed"]


class ModalDialog(tk.Toplevel):
    """A window that sits on top of the main window until it is closed."""

    def __init__(self, parent: tk.Misc, title: str, theme):
        super().__init__(parent)
        self.theme = theme
        self.title(title)
        self.configure(background=theme.colors["bg"])
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.saved = False
        self.bind("<Escape>", lambda _e: self.destroy())

    def show(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max((parent.winfo_width() - self.winfo_reqwidth()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - self.winfo_reqheight()) // 3, 0)
        self.geometry(f"+{x}+{y}")
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.focus_set()
        self.wait_window(self)


# --------------------------------------------------------------- assignment
class AssignmentDialog(ModalDialog):
    def __init__(self, parent: tk.Misc, services: Services, theme,
                 assignment: Assignment | None = None):
        super().__init__(parent, "Edit assignment" if assignment else "New assignment", theme)
        self.services = services
        self.assignment = assignment

        courses = services.courses.list()
        self._course_ids: list[int | None] = [None] + [c.id for c in courses]
        course_labels = ["(No course)"] + [c.display for c in courses]
        self._reminder_values: list[int | None] = [None] + [m for m, _ in REMINDER_PRESETS]
        reminder_labels = ["Use default setting"] + [f"{lbl} before" for _, lbl in REMINDER_PRESETS]
        if assignment and assignment.reminder_minutes not in self._reminder_values:
            self._reminder_values.append(assignment.reminder_minutes)
            reminder_labels.append(f"{minutes_label(assignment.reminder_minutes)} before")

        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        def label(text: str, row: int) -> None:
            ttk.Label(body, text=text).grid(row=row, column=0, sticky="nw", padx=(0, 14), pady=7)

        label("Title *", 0)
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(body, textvariable=self.title_var, width=48)
        title_entry.grid(row=0, column=1, sticky="ew", pady=5)

        label("Course", 1)
        self.course_cb = ttk.Combobox(body, values=course_labels, state="readonly")
        self.course_cb.grid(row=1, column=1, sticky="ew", pady=5)

        label("Due date *", 2)
        when = ttk.Frame(body)
        when.grid(row=2, column=1, sticky="w", pady=5)
        self.date_entry = DateEntry(when, date_pattern="yyyy-mm-dd", firstweekday="monday",
                                    width=13, borderwidth=1)
        self.date_entry.pack(side="left")
        ttk.Label(when, text="   Time (optional, 24h HH:MM)").pack(side="left")
        self.time_var = tk.StringVar()
        ttk.Entry(when, textvariable=self.time_var, width=7).pack(side="left", padx=(8, 0))

        label("Priority", 3)
        self.priority_cb = ttk.Combobox(body, values=PRIORITY_LABELS, state="readonly")
        self.priority_cb.grid(row=3, column=1, sticky="ew", pady=5)

        label("Status", 4)
        self.status_cb = ttk.Combobox(body, values=STATUS_LABELS_LIST, state="readonly")
        self.status_cb.grid(row=4, column=1, sticky="ew", pady=5)

        label("Remind me", 5)
        self.reminder_cb = ttk.Combobox(body, values=reminder_labels, state="readonly")
        self.reminder_cb.grid(row=5, column=1, sticky="ew", pady=5)

        label("Notes", 6)
        self.desc = tk.Text(body, width=48, height=5, wrap="word", relief="solid", borderwidth=1,
                            highlightthickness=0, padx=6, pady=6, font=theme.fonts["base"])
        self.desc.grid(row=6, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(body)
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=self._save).pack(
            side="right", padx=(0, 10))

        self._fill(assignment)
        title_entry.focus_set()

    def _fill(self, a: Assignment | None) -> None:
        if a is None:
            self.date_entry.set_date(self.services.assignments.clock().date() + timedelta(days=1))
            self.course_cb.current(0)
            self.priority_cb.current(1)
            self.status_cb.current(0)
            self.reminder_cb.current(0)
            return
        self.title_var.set(a.title)
        self.course_cb.current(self._course_ids.index(a.course_id)
                               if a.course_id in self._course_ids else 0)
        self.date_entry.set_date(a.due_date)
        self.time_var.set(a.due_time.strftime("%H:%M") if a.due_time else "")
        self.priority_cb.current(PRIORITIES.index(a.priority))
        self.status_cb.current(STATUSES.index(a.status))
        self.reminder_cb.current(self._reminder_values.index(a.reminder_minutes))
        self.desc.insert("1.0", a.description)

    def _save(self) -> None:
        try:
            due_date = self.date_entry.get_date()
        except ValueError:
            messagebox.showerror("Cannot save", "Please enter a valid due date (YYYY-MM-DD).",
                                 parent=self)
            return
        fields = dict(
            title=self.title_var.get(),
            due_date=due_date,
            due_time=self.time_var.get(),
            course_id=self._course_ids[self.course_cb.current()],
            description=self.desc.get("1.0", "end"),
            priority=PRIORITIES[self.priority_cb.current()],
            status=STATUSES[self.status_cb.current()],
            reminder_minutes=self._reminder_values[self.reminder_cb.current()],
        )
        try:
            if self.assignment:
                self.services.assignments.update(self.assignment.id, **fields)
            else:
                self.services.assignments.create(**fields)
        except ValidationError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return
        self.saved = True
        self.destroy()


# ------------------------------------------------------------------- course
class CourseDialog(ModalDialog):
    def __init__(self, parent: tk.Misc, services: Services, theme, course: Course | None = None):
        super().__init__(parent, "Edit course" if course else "New course", theme)
        self.services = services
        self.course = course

        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        self.code_var = tk.StringVar(value=course.code if course else "")
        self.name_var = tk.StringVar(value=course.name if course else "")
        self.instructor_var = tk.StringVar(value=course.instructor if course else "")
        self.color_var = tk.StringVar(value=course.color if course else "#4F7CFF")

        rows = [("Course code *", self.code_var), ("Course name *", self.name_var),
                ("Instructor", self.instructor_var)]
        first_entry = None
        for i, (text, var) in enumerate(rows):
            ttk.Label(body, text=text).grid(row=i, column=0, sticky="w", padx=(0, 14), pady=7)
            entry = ttk.Entry(body, textvariable=var, width=36)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            first_entry = first_entry or entry

        ttk.Label(body, text="Colour").grid(row=3, column=0, sticky="w", pady=7)
        color_row = ttk.Frame(body)
        color_row.grid(row=3, column=1, sticky="w", pady=5)
        self.swatch = tk.Label(color_row, width=4, relief="solid", borderwidth=1)
        self.swatch.pack(side="left")
        ttk.Entry(color_row, textvariable=self.color_var, width=10).pack(side="left", padx=8)
        ttk.Button(color_row, text="Choose...", command=self._choose_color).pack(side="left")
        self.color_var.trace_add("write", lambda *_: self._update_swatch())
        self._update_swatch()

        buttons = ttk.Frame(body)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=self._save).pack(
            side="right", padx=(0, 10))
        first_entry.focus_set()

    def _update_swatch(self) -> None:
        try:
            self.swatch.configure(background=self.color_var.get())
        except tk.TclError:
            self.swatch.configure(background="#FFFFFF")

    def _choose_color(self) -> None:
        _rgb, hex_color = colorchooser.askcolor(color=self.color_var.get(), parent=self)
        if hex_color:
            self.color_var.set(hex_color.upper())

    def _save(self) -> None:
        args = (self.code_var.get(), self.name_var.get(), self.instructor_var.get(),
                self.color_var.get())
        try:
            if self.course:
                self.services.courses.update(self.course.id, *args)
            else:
                self.services.courses.add(*args)
        except ValidationError as exc:
            messagebox.showerror("Cannot save", str(exc), parent=self)
            return
        self.saved = True
        self.destroy()
