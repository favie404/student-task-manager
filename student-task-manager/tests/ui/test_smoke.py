"""Smoke tests: open every screen and use the dialogs. Skipped when there is no display.

On Linux without a screen run:  xvfb-run -a pytest
"""
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime, timedelta

import pytest

from student_task_manager.services.container import build_services
from student_task_manager.services.sample_data import load_sample_data
from student_task_manager.ui.dialogs import AssignmentDialog, CourseDialog
from student_task_manager.ui.main_window import MainWindow
from student_task_manager.ui.reminder_popup import ReminderPopup
from student_task_manager.ui.theme import apply_theme


@pytest.fixture
def root():
    try:
        r = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def ui(root):
    services = build_services(":memory:")
    theme = apply_theme(root)
    app = MainWindow(root, services, theme, start_timer=False)
    yield app
    services.close()


@pytest.fixture
def errors(monkeypatch):
    shown = []
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: shown.append(a))
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: shown.append(a))
    return shown


def test_every_view_opens_empty(ui, root):
    for name in ("dashboard", "assignments", "courses", "calendar", "settings"):
        ui.show(name)
        root.update()


def test_every_view_opens_with_data(ui, root):
    load_sample_data(ui.services.courses, ui.services.assignments)
    for name in ("dashboard", "assignments", "courses", "calendar", "settings"):
        ui.show(name)
        root.update()
    assert len(ui.views["assignments"].tree.get_children()) == 8
    assert len(ui.views["courses"].tree.get_children()) == 4


def test_assignments_search_and_filters(ui, root):
    load_sample_data(ui.services.courses, ui.services.assignments)
    ui.show("assignments")
    view = ui.views["assignments"]
    view.search_var.set("sql")
    view.refresh()
    assert len(view.tree.get_children()) == 1
    view.clear_filters()
    view.status_cb.current(4)           # Overdue
    view.refresh()
    assert len(view.tree.get_children()) >= 1
    view.clear_filters()
    assert len(view.tree.get_children()) == 8


def test_assignment_dialog_creates_and_validates(ui, root, errors):
    dialog = AssignmentDialog(root, ui.services, ui.theme)
    dialog._save()                                   # empty title -> error, stays open
    assert not dialog.saved and errors
    dialog.title_var.set("From the form")
    dialog.time_var.set("14:30")
    dialog._save()
    assert dialog.saved
    created = ui.services.assignments.list()
    assert [a.title for a in created] == ["From the form"]
    assert created[0].due_time.strftime("%H:%M") == "14:30"


def test_assignment_dialog_rejects_bad_time(ui, root, errors):
    dialog = AssignmentDialog(root, ui.services, ui.theme)
    dialog.title_var.set("x")
    dialog.time_var.set("99:99")
    dialog._save()
    assert not dialog.saved and ui.services.assignments.list() == []
    dialog.destroy()


def test_assignment_dialog_edits(ui, root):
    course = ui.services.courses.add("A1", "One")
    a = ui.services.assignments.create(title="Old", due_date="2026-12-01", course_id=course.id,
                                       reminder_minutes=60, description="notes")
    dialog = AssignmentDialog(root, ui.services, ui.theme, ui.services.assignments.get(a.id))
    assert dialog.title_var.get() == "Old" and dialog.course_cb.current() == 1
    dialog.title_var.set("New")
    dialog._save()
    assert ui.services.assignments.get(a.id).title == "New"
    assert ui.services.assignments.get(a.id).description == "notes"


def test_course_dialog(ui, root, errors):
    dialog = CourseDialog(root, ui.services, ui.theme)
    dialog._save()
    assert not dialog.saved and errors
    dialog.code_var.set("NET 1")
    dialog.name_var.set("Networks")
    dialog._save()
    assert dialog.saved and [c.code for c in ui.services.courses.list()] == ["NET 1"]


def test_reminder_popup_complete_and_snooze(ui, root):
    now = datetime.now()
    due = now + timedelta(hours=2)
    a = ui.services.assignments.create(title="Soon", due_date=due.date(), due_time=due.time())
    reminders = ui.services.reminders.due_reminders(now)
    assert len(reminders) == 1
    popup = ReminderPopup(root, ui, reminders)
    root.update()
    popup.tree.selection_set(str(a.id))
    popup._complete()
    assert ui.services.assignments.get(a.id).is_completed
    assert not popup.winfo_exists()


def test_reminder_timer_shows_popup_once(ui, root):
    now = datetime.now()
    due = now + timedelta(hours=1)
    ui.services.assignments.create(title="Soon", due_date=due.date(), due_time=due.time())
    ui._check_reminders()
    assert ui._popup is not None and ui._popup.winfo_exists()
    ui._popup.destroy()
    ui._check_reminders()                       # already shown -> no second popup
    assert not ui._popup.winfo_exists()
    ui.root.after_cancel(ui._timer_id)


def test_settings_save(ui, root):
    ui.show("settings")
    view = ui.views["settings"]
    view.enabled_var.set(False)
    view.lead_cb.current(2)
    view.save()
    assert not ui.services.settings.reminders_enabled
    assert ui.services.settings.default_reminder_minutes == 60
    ui.root.after_cancel(ui._timer_id)


def test_calendar_selection_lists_the_day(ui, root):
    a = ui.services.assignments.create(title="On the day", due_date=datetime.now().date())
    ui.show("calendar")
    view = ui.views["calendar"]
    view.go_today()
    assert view.tree.get_children() == (str(a.id),)


def test_settings_shows_database_path(ui, root):
    view = ui.views["settings"]
    root.update()
    entries = [w for w in view.winfo_children()[2].winfo_children() if w.winfo_class() == "TEntry"]
    assert entries and entries[0].get() == ui.services.db_path
