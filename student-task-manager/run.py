"""Convenience launcher: `python run.py` (no installation needed)."""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from student_task_manager.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
