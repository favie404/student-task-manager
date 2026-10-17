"""Entry point:  python -m student_task_manager   (or: python run.py)"""
from __future__ import annotations

import argparse
import sys

from . import __version__

TK_HELP = """Tkinter (the window toolkit) is not installed for this Python.

  Windows : re-run the Python installer, choose "Modify" and tick "tcl/tk and IDLE".
  Ubuntu / Debian : sudo apt install python3-tk
  Fedora : sudo dnf install python3-tkinter
  Arch : sudo pacman -S tk
"""


def _enable_hidpi() -> None:
    """Stop Windows from blurring the app on high-DPI screens. Must run before Tk()."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="student-task-manager",
                                     description="Student Task Manager")
    parser.add_argument("--db", help="use this database file instead of the default one")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    try:
        import tkinter  # noqa: F401
    except ImportError:
        sys.stderr.write(TK_HELP)
        sys.exit(1)

    _enable_hidpi()
    from .app import run
    run(args.db)


if __name__ == "__main__":
    main()
