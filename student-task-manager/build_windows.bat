@echo off
REM Builds dist\StudentTaskManager\StudentTaskManager.exe  (run on Windows)
python -m venv .venv || goto :error
call .venv\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
pip install -r requirements-dev.txt || goto :error
python -m pytest -q || goto :error
pyinstaller packaging\student_task_manager.spec --noconfirm || goto :error
echo.
echo Done. Your app is in dist\StudentTaskManager\
goto :eof
:error
echo.
echo BUILD FAILED - read the messages above.
exit /b 1
