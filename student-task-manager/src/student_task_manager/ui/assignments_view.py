"""Assignments: table with live search and filters."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from ..models import NO_COURSE, STATUS_LABELS, AssignmentFilter
from ..utils.dates import format_due
from .dialogs import AssignmentDialog

STATUS_OPTIONS = [("All statuses", None), ("Pending", "pending"), ("In progress", "in_progress"),
                  ("Completed", "completed"), ("Overdue", "overdue")]
PRIORITY_OPTIONS = [("All priorities", None), ("Low", "low"), ("Medium", "medium"), ("High", "high")]


class AssignmentsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        self._search_job = None
        self._course_options: list[tuple[str, int | None]] = [("All courses", None)]

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Assignments", style="H1.TLabel").pack(side="left")
        ttk.Button(header, text="+ New assignment", style="Accent.TButton",
                   command=self.add).pack(side="right")

        bar = ttk.Frame(self, style="Card.TFrame", padding=12)
        bar.pack(fill="x", pady=(16, 10))
        # pack the right-hand button first so it always keeps its space
        ttk.Button(bar, text="Clear filters", command=self.clear_filters).pack(side="right")
        ttk.Label(bar, text="Search", style="Card.TLabel").pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(bar, textvariable=self.search_var, width=12)
        search.pack(side="left", padx=(8, 12), fill="x", expand=True)
        self.search_var.trace_add("write", lambda *_: self._schedule_refresh())

        self.course_cb = ttk.Combobox(bar, state="readonly", width=16)
        self.course_cb.pack(side="left", padx=(0, 8))
        self.status_cb = ttk.Combobox(bar, state="readonly", width=10,
                                      values=[t for t, _ in STATUS_OPTIONS])
        self.status_cb.pack(side="left", padx=(0, 8))
        self.priority_cb = ttk.Combobox(bar, state="readonly", width=10,
                                        values=[t for t, _ in PRIORITY_OPTIONS])
        self.priority_cb.pack(side="left", padx=(0, 12))
        self.status_cb.current(0)
        self.priority_cb.current(0)
        for cb in (self.course_cb, self.status_cb, self.priority_cb):
            cb.bind("<<ComboboxSelected>>", self._on_filter_change)

        table_card = ttk.Frame(self, style="Card.TFrame", padding=2)
        table_card.pack(fill="both", expand=True)
        cols = ("title", "course", "due", "priority", "status")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        for col, text, width, stretch in (("title", "Title", 300, True), ("course", "Course", 130, False),
                                          ("due", "Due", 150, False), ("priority", "Priority", 80, False),
                                          ("status", "Status", 100, False)):
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=width, anchor="w", stretch=stretch, minwidth=60)
        scroll = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        c = app.theme.colors
        self.tree.tag_configure("overdue", foreground=c["danger"])
        self.tree.tag_configure("completed", foreground=c["muted"])
        self.tree.bind("<Double-1>", lambda _e: self.edit())
        self.tree.bind("<Return>", lambda _e: self.edit())
        self.tree.bind("<Delete>", lambda _e: self.delete())

        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=(10, 0))
        self.count_label = ttk.Label(footer, style="Muted.TLabel")
        self.count_label.pack(side="left")
        ttk.Button(footer, text="Delete", style="Danger.TButton", command=self.delete).pack(side="right")
        ttk.Button(footer, text="Edit", command=self.edit).pack(side="right", padx=(0, 8))
        ttk.Button(footer, text="Mark complete / reopen", command=self.toggle).pack(side="right", padx=(0, 8))

    # ---- filters ----------------------------------------------------
    @staticmethod
    def _value(combobox: ttk.Combobox, options: list):
        index = combobox.current()
        return options[index][1] if index >= 0 else None

    def _current_filter(self) -> AssignmentFilter:
        return AssignmentFilter(
            search=self.search_var.get(),
            course_id=self._value(self.course_cb, self._course_options),
            status=self._value(self.status_cb, STATUS_OPTIONS),
            priority=self._value(self.priority_cb, PRIORITY_OPTIONS),
        )

    def _on_filter_change(self, event=None) -> None:
        if event is not None:
            event.widget.selection_clear()
        self.refresh()

    def _schedule_refresh(self) -> None:
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(250, self.refresh)  # wait until typing pauses

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.course_cb.current(0)
        self.status_cb.current(0)
        self.priority_cb.current(0)
        self.refresh()

    def _reload_courses(self) -> None:
        previous = self._value(self.course_cb, self._course_options) if self.course_cb.current() >= 0 else None
        options = [("All courses", None), ("No course", NO_COURSE)]
        options += [(c.display, c.id) for c in self.app.services.courses.list()]
        self._course_options = options
        self.course_cb.configure(values=[t for t, _ in options])
        ids = [v for _, v in options]
        self.course_cb.current(ids.index(previous) if previous in ids else 0)

    # ---- data -------------------------------------------------------
    def refresh(self) -> None:
        self._search_job = None
        self._reload_courses()
        now = datetime.now()
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        items = self.app.services.assignments.list(self._current_filter())
        for a in items:
            overdue = a.is_overdue(now)
            tags = ("overdue",) if overdue else (("completed",) if a.is_completed else ())
            self.tree.insert("", "end", iid=str(a.id), tags=tags, values=(
                a.title, a.course_code or "-", format_due(a.due_date, a.due_time),
                a.priority.capitalize(), "Overdue" if overdue else STATUS_LABELS[a.status]))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
        self.count_label.configure(text=f"{len(items)} assignment{'s' if len(items) != 1 else ''}")

    def _selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select an assignment", "Click an assignment in the list first.",
                                parent=self)
            return None
        return int(selection[0])

    # ---- actions ----------------------------------------------------
    def add(self) -> None:
        dialog = AssignmentDialog(self, self.app.services, self.app.theme)
        dialog.show()
        if dialog.saved:
            self.refresh()

    def edit(self) -> None:
        assignment_id = self._selected_id()
        if assignment_id is None:
            return
        assignment = self.app.services.assignments.get(assignment_id)
        if assignment is None:
            self.refresh()
            return
        dialog = AssignmentDialog(self, self.app.services, self.app.theme, assignment)
        dialog.show()
        if dialog.saved:
            self.refresh()

    def toggle(self) -> None:
        assignment_id = self._selected_id()
        if assignment_id is not None:
            self.app.services.assignments.toggle_complete(assignment_id)
            self.refresh()

    def delete(self) -> None:
        assignment_id = self._selected_id()
        if assignment_id is None:
            return
        assignment = self.app.services.assignments.get(assignment_id)
        name = assignment.title if assignment else "this assignment"
        if messagebox.askyesno("Delete assignment", f"Delete '{name}'?\n\nThis cannot be undone.",
                               icon="warning", parent=self):
            self.app.services.assignments.delete(assignment_id)
            self.refresh()
