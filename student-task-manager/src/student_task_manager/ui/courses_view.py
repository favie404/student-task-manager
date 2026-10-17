"""Courses: add, edit, delete."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .dialogs import CourseDialog


class CoursesView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Courses", style="H1.TLabel").pack(side="left")
        ttk.Button(header, text="+ New course", style="Accent.TButton",
                   command=self.add).pack(side="right")

        card = ttk.Frame(self, style="Card.TFrame", padding=2)
        card.pack(fill="both", expand=True, pady=(16, 10))
        cols = ("code", "name", "instructor", "color", "count")
        self._swatches: dict[str, tk.PhotoImage] = {}  # keep references or Tk drops the images
        self.tree = ttk.Treeview(card, columns=cols, show=("tree", "headings"), selectmode="browse")
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=44, minwidth=44, stretch=False, anchor="center")
        for col, text, width, stretch in (("code", "Code", 110, False), ("name", "Name", 280, True),
                                          ("instructor", "Instructor", 170, False),
                                          ("color", "Colour", 90, False),
                                          ("count", "Assignments", 125, False)):
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=width, anchor="w", stretch=stretch, minwidth=60)
        scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit())
        self.tree.bind("<Return>", lambda _e: self.edit())
        self.tree.bind("<Delete>", lambda _e: self.delete())

        footer = ttk.Frame(self)
        footer.pack(fill="x")
        self.hint = ttk.Label(footer, style="Muted.TLabel",
                              text="Deleting a course keeps its assignments (they show 'No course').")
        self.hint.pack(side="left")
        ttk.Button(footer, text="Delete", style="Danger.TButton", command=self.delete).pack(side="right")
        ttk.Button(footer, text="Edit", command=self.edit).pack(side="right", padx=(0, 8))

    def _swatch(self, color: str) -> tk.PhotoImage:
        if color not in self._swatches:
            image = tk.PhotoImage(width=16, height=16)
            image.put(color, to=(0, 0, 16, 16))
            self._swatches[color] = image
        return self._swatches[color]

    def refresh(self) -> None:
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for course, count in self.app.services.courses.list_with_counts():
            self.tree.insert("", "end", iid=str(course.id), image=self._swatch(course.color),
                             values=(course.code, course.name, course.instructor or "-",
                                     course.color, count))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])

    def _selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a course", "Click a course in the list first.", parent=self)
            return None
        return int(selection[0])

    def add(self) -> None:
        dialog = CourseDialog(self, self.app.services, self.app.theme)
        dialog.show()
        if dialog.saved:
            self.refresh()

    def edit(self) -> None:
        course_id = self._selected_id()
        if course_id is None:
            return
        course = self.app.services.courses.get(course_id)
        if course is None:
            self.refresh()
            return
        dialog = CourseDialog(self, self.app.services, self.app.theme, course)
        dialog.show()
        if dialog.saved:
            self.refresh()

    def delete(self) -> None:
        course_id = self._selected_id()
        if course_id is None:
            return
        course = self.app.services.courses.get(course_id)
        if course is None:
            self.refresh()
            return
        count = self.app.services.courses.repo.assignment_count(course_id)
        extra = (f"\n\n{count} assignment(s) will be kept but will no longer belong to a course."
                 if count else "")
        if messagebox.askyesno("Delete course", f"Delete '{course.display}'?{extra}",
                               icon="warning", parent=self):
            self.app.services.courses.delete(course_id)
            self.refresh()
