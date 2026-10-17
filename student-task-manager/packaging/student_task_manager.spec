# PyInstaller recipe. Build from the project root with:
#     pyinstaller packaging/student_task_manager.spec --noconfirm
# Output: dist/StudentTaskManager/  (a folder - zip it to share)
#
# Run it on the OS you are building for (Windows -> .exe, Linux -> Linux binary).
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent

# tkcalendar needs Babel's locale data at run time; PyInstaller cannot see it by itself
datas = collect_data_files("babel")
hiddenimports = collect_submodules("babel") + ["tkcalendar", "platformdirs"]

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT / "src")],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "PIL", "numpy", "matplotlib"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StudentTaskManager",
    console=False,          # no black terminal window behind the app
    # icon=str(ROOT / "packaging" / "app.ico"),   # optional: add an .ico (Windows)
)
coll = COLLECT(exe, a.binaries, a.datas, name="StudentTaskManager")
