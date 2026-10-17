#!/usr/bin/env bash
# Builds dist/StudentTaskManager/StudentTaskManager  (run on Linux)
set -euo pipefail
python3 -m venv --system-site-packages .venv   # --system-site-packages lets the venv see python3-tk
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
if command -v xvfb-run >/dev/null; then xvfb-run -a python -m pytest -q; else python -m pytest -q; fi
pyinstaller packaging/student_task_manager.spec --noconfirm
echo
echo "Done. Your app is in dist/StudentTaskManager/"
