# Student Task Manager

A cross-platform desktop app for tracking assignments, courses and deadlines.
Works on **Windows 10, Windows 11 and Linux**.

**Built with:** Python 3.10+, Tkinter/ttk, SQLite, tkcalendar, pytest, PyInstaller.

## Features
- Dashboard: task statistics, overall completion bar, upcoming deadlines, progress per course
- Assignments: add, edit, delete, live search, filter by course / status / priority, overdue highlighting
- Courses: add, edit, delete, colour per course, assignment counts
- Calendar: monthly view with deadlines highlighted (course colours; red = overdue; grey = done)
- Reminders: in-app pop-ups before a deadline, with **Snooze**, **Dismiss** and **Mark complete**.
  Configure the default lead time, check frequency, and an override per assignment
- Everything is saved immediately in a local SQLite file

## 1. Install (one-time)

### Windows 10 / 11
1. Install Python 3.10 or newer from https://www.python.org/downloads/
   During setup tick **"Add python.exe to PATH"** (Tkinter is included by default).
2. Open the project folder in Command Prompt or PowerShell:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
   (PowerShell blocking activation? Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.)

### Linux (Ubuntu / Debian shown)
```
sudo apt install python3 python3-venv python3-tk xvfb
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```
Fedora: `sudo dnf install python3-tkinter xorg-x11-server-Xvfb`. Arch: `sudo pacman -S tk xorg-server-xvfb`.
(`xvfb` is only needed to run the window tests on a machine with no screen.)

## 2. Run
```
python run.py
```
First time? Open **Settings → Load sample data** to see the dashboard and calendar filled in.

Your data lives here (Settings shows the exact path):
- Windows: `C:\Users\<you>\AppData\Local\StudentTaskManager\tasks.db`
- Linux: `~/.local/share/StudentTaskManager/tasks.db`

Use a different file: `python run.py --db mytest.db`. Back up your data by copying `tasks.db`.

## 3. Run the tests
```
python -m pytest            # Windows, or Linux with a desktop
xvfb-run -a python -m pytest   # Linux with no screen (servers / CI)
```
The window tests are skipped automatically if no display is available.

## 4. Build a standalone app (no Python needed to run it)
PyInstaller cannot cross-compile: build on the OS you are targeting.

- **Windows:** double-click `build_windows.bat` (or run it in a terminal).
  Result: `dist\StudentTaskManager\StudentTaskManager.exe`
- **Linux:** `./build_linux.sh`
  Result: `dist/StudentTaskManager/StudentTaskManager`

Zip the whole `StudentTaskManager` folder to share it (the `.exe` needs the files next to it).
Windows may show a SmartScreen "unknown publisher" warning because the app is not code-signed.
Click **More info → Run anyway**. That is normal for student projects.

## 5. Put it on GitHub
```
git init
git add .
git commit -m "Student Task Manager v1.0"
git branch -M main
git remote add origin https://github.com/<your-username>/student-task-manager.git
git push -u origin main
```
Create the empty repository on github.com first (no README/licence). After pushing, the
**Actions** tab runs the tests on Windows and Linux and builds both apps automatically.

## Project layout
```
run.py                        start the app
src/student_task_manager/
  db/            connection, migrations (table creation), repositories (all SQL)
  services/      the rules: assignments, courses, stats, reminders, settings
  ui/            Tkinter windows: theme, main window, one file per screen, dialogs
  models.py      Course / Assignment data objects
tests/           pytest (logic tests + window smoke tests)
packaging/       PyInstaller recipe
```
The layers only talk downward: **ui → services → repositories → SQLite**. Services never import
Tkinter, which is why they can be tested without opening a window.

## Changing the database later
Add a new SQL script at the **end** of `MIGRATIONS` in `db/migrations.py`. Existing databases
upgrade automatically on next start. Never edit an old migration.

## Troubleshooting
| Problem | Fix |
|---|---|
| `Tkinter is not installed` message | Install it as shown in step 1 (Linux: `python3-tk`) |
| `ModuleNotFoundError: tkcalendar` | Activate the virtual environment, then `pip install -r requirements.txt` |
| Window looks blurry on Windows | Already handled; if it persists, right-click Python → Properties → Compatibility → high DPI |
| Reminder never appears | Settings → reminders enabled? Lead time long enough? Try **Show dismissed reminders again** |
| Something crashes | Check `app.log` in the data folder above |
| Built app starts then closes (Linux) | Run it from a terminal to see the message; make sure the build machine had `python3-tk` |

## Known limitations
- Reminders are in-app pop-ups: they only appear while the app is open (no system notifications).
- Single user, local only, local time (no time zones, no cloud sync).
- The Linux build runs on distributions with the same or newer system libraries than the machine
  that built it. Build on the oldest Ubuntu you want to support.
