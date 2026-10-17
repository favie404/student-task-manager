"""Monthly calendar with assignment deadlines highlighted."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from tkinter import ttk

from tkcalendar import Calendar

from ..models import STATUS_LABELS
from ..utils.dates import format_due
from .dialogs import AssignmentDialog

DONE_COLOR = "#9CA3AF"


class CalendarView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        c = app.theme.colors
        self._by_date: dict[date, list] = defaultdict(list)

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Calendar", style="H1.TLabel").pack(side="left")
        ttk.Button(header, text="+ New assignment", style="Accent.TButton",
                   command=app.open_new_assignment).pack(side="right")
        ttk.Button(header, text="Today", command=self.go_today).pack(side="right", padx=(0, 8))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, pady=(16, 0))
        body.columnconfigure(0, weight=3, uniform="cal")
        body.columnconfigure(1, weight=2, uniform="cal")
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Card.TFrame", padding=10)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.cal = Calendar(
            left, selectmode="day", firstweekday="monday", showweeknumbers=False,
            date_pattern="yyyy-mm-dd", font=app.theme.fonts["base"],
            background=c["accent"], foreground="white",
            headersbackground=c["header"], headersforeground=c["text"],
            selectbackground="#111827", selectforeground="white",
            normalbackground="white", normalforeground=c["text"],
            weekendbackground="#F9FAFB", weekendforeground=c["text"],
            othermonthbackground="#F3F4F6", othermonthforeground="#9CA3AF",
            othermonthwebackground="#F3F4F6", othermonthweforeground="#9CA3AF",
            bordercolor=c["border"],
        )
        self.cal.pack(fill="both", expand=True)
        self.cal.bind("<<CalendarSelected>>", lambda _e: self.show_day())
        ttk.Label(left, style="CardMuted.TLabel", wraplength=420, justify="left",
                  text="Coloured days have deadlines (course colour). "
                       "Red = overdue, grey = completed.").pack(anchor="w", pady=(8, 0))

        right = ttk.Frame(body, style="Card.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.day_label = ttk.Label(right, style="CardH2.TLabel")
        self.day_label.pack(anchor="w")
        self.tree = ttk.Treeview(right, columns=("time", "title", "status"), show="headings",
                                 selectmode="browse", height=10)
        for col, text, width, stretch in (("time", "Time", 55, False), ("title", "Assignment", 110, True),
                                          ("status", "Status", 85, False)):
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=width, anchor="w", stretch=stretch, minwidth=45)
        self.tree.pack(fill="both", expand=True, pady=(10, 0))
        self.tree.tag_configure("overdue", foreground=c["danger"])
        self.tree.tag_configure("completed", foreground=c["muted"])
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())
        self.empty_label = ttk.Label(right, style="CardMuted.TLabel", text="")
        self.empty_label.pack(anchor="w", pady=(8, 0))
        ttk.Label(right, style="CardMuted.TLabel", wraplength=300,
                  text="Double-click an assignment to edit it.").pack(anchor="w", pady=(4, 0))

    def go_today(self) -> None:
        today = date.today()
        self.cal.selection_set(today)
        self.cal.see(today)
        self.show_day()

    def refresh(self) -> None:
        now = datetime.now()
        c = self.app.theme.colors
        self.cal.calevent_remove("all")
        self._by_date = defaultdict(list)
        self.cal.tag_config("done", background=DONE_COLOR, foreground="white")
        self.cal.tag_config("overdue", background=c["danger"], foreground="white")
        self.cal.tag_config("nocourse", background="#6B7280", foreground="white")

        items = self.app.services.assignments.list_all()
        for a in items:
            self._by_date[a.due_date].append(a)

        def priority(a):  # completed first, overdue last so the most urgent colour wins
            return 0 if a.is_completed else (2 if a.is_overdue(now) else 1)

        for a in sorted(items, key=priority):
            if a.is_completed:
                tag = "done"
            elif a.is_overdue(now):
                tag = "overdue"
            elif a.course_id:
                tag = f"course{a.course_id}"
                self.cal.tag_config(tag, background=a.course_color or c["accent"], foreground="white")
            else:
                tag = "nocourse"
            self.cal.calevent_create(a.due_date, a.title, tag)
        self.show_day()

    def show_day(self) -> None:
        now = datetime.now()
        selected = self.cal.selection_get() or date.today()
        self.day_label.configure(text=selected.strftime("%A, %d %B %Y"))
        self.tree.delete(*self.tree.get_children())
        day_items = self._by_date.get(selected, [])
        for a in day_items:
            overdue = a.is_overdue(now)
            tags = ("overdue",) if overdue else (("completed",) if a.is_completed else ())
            self.tree.insert("", "end", iid=str(a.id), tags=tags, values=(
                a.due_time.strftime("%H:%M") if a.due_time else "-", a.title,
                "Overdue" if overdue else STATUS_LABELS[a.status]))
        self.empty_label.configure(text="" if day_items else "No deadlines on this day.")

    def edit_selected(self) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        assignment = self.app.services.assignments.get(int(selection[0]))
        if assignment is None:
            self.refresh()
            return
        dialog = AssignmentDialog(self, self.app.services, self.app.theme, assignment)
        dialog.show()
        if dialog.saved:
            self.refresh()
