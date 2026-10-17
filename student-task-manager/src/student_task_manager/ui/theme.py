"""Colours, fonts and ttk styles. Everything visual is configured here.

We force the built-in 'clam' ttk theme on every OS because it can be styled
the same way on Windows and Linux (the native Windows theme ignores many
colour settings).
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field
from tkinter import font as tkfont
from tkinter import ttk

COLORS = {
    "bg": "#F4F6FB",
    "surface": "#FFFFFF",
    "sidebar": "#1F2A44",
    "sidebar_hover": "#2B3A5C",
    "sidebar_active": "#3D5AFE",
    "sidebar_text": "#C7D0E5",
    "text": "#1F2937",
    "muted": "#6B7280",
    "border": "#E2E6EF",
    "header": "#EEF1F8",
    "accent": "#3D5AFE",
    "accent_hover": "#2F49D1",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
}

FONT_CANDIDATES = ("Segoe UI", "Noto Sans", "Ubuntu", "Cantarell", "DejaVu Sans", "Helvetica", "Arial")


@dataclass
class Theme:
    family: str
    colors: dict = field(default_factory=lambda: dict(COLORS))
    fonts: dict = field(default_factory=dict)


def scale(widget: tk.Misc, pixels: int) -> int:
    """Scale a pixel size for high-DPI screens (96 dpi = 1.0)."""
    return int(pixels * widget.winfo_fpixels("1i") / 96)


def _pick_family(root: tk.Misc) -> str:
    available = set(tkfont.families(root))
    for name in FONT_CANDIDATES:
        if name in available:
            return name
    return tkfont.nametofont("TkDefaultFont").actual("family")


def apply_theme(root: tk.Tk) -> Theme:
    c = COLORS
    style = ttk.Style(root)
    style.theme_use("clam")
    family = _pick_family(root)
    theme = Theme(family=family)

    for named in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        try:
            tkfont.nametofont(named).configure(family=family, size=10)
        except tk.TclError:
            pass
    theme.fonts = {
        "base": tkfont.Font(root=root, family=family, size=10),
        "bold": tkfont.Font(root=root, family=family, size=10, weight="bold"),
        "h1": tkfont.Font(root=root, family=family, size=20, weight="bold"),
        "h2": tkfont.Font(root=root, family=family, size=12, weight="bold"),
        "big": tkfont.Font(root=root, family=family, size=26, weight="bold"),
        "small": tkfont.Font(root=root, family=family, size=9),
    }
    f = theme.fonts

    root.configure(background=c["bg"])
    style.configure(".", background=c["bg"], foreground=c["text"], font=f["base"],
                    bordercolor=c["border"], focuscolor=c["bg"])

    # frames
    style.configure("TFrame", background=c["bg"])
    style.configure("Card.TFrame", background=c["surface"], bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], borderwidth=1, relief="solid")
    style.configure("Plain.TFrame", background=c["surface"], borderwidth=0, relief="flat")
    style.configure("Sidebar.TFrame", background=c["sidebar"])

    # labels
    style.configure("TLabel", background=c["bg"], foreground=c["text"])
    style.configure("Muted.TLabel", foreground=c["muted"])
    style.configure("H1.TLabel", font=f["h1"])
    style.configure("Card.TLabel", background=c["surface"])
    style.configure("CardMuted.TLabel", background=c["surface"], foreground=c["muted"])
    style.configure("CardH2.TLabel", background=c["surface"], font=f["h2"])
    style.configure("CardNumber.TLabel", background=c["surface"], font=f["big"])
    style.configure("Sidebar.TLabel", background=c["sidebar"], foreground="white")
    style.configure("SidebarMuted.TLabel", background=c["sidebar"], foreground="#8D99B8", font=f["small"])
    style.configure("Danger.TLabel", background=c["surface"], foreground=c["danger"])

    # buttons
    style.configure("TButton", padding=(12, 6), background="#E8ECF5", foreground=c["text"],
                    borderwidth=0, relief="flat")
    style.map("TButton", background=[("active", "#D9DFEE"), ("disabled", "#EEF1F8")],
              foreground=[("disabled", "#9CA3AF")])
    style.configure("Accent.TButton", background=c["accent"], foreground="white", font=f["bold"])
    style.map("Accent.TButton", background=[("active", c["accent_hover"]), ("disabled", "#A5B4FC")])
    style.configure("Danger.TButton", background="#FDE8E8", foreground=c["danger"])
    style.map("Danger.TButton", background=[("active", "#FACACA")])
    style.configure("Nav.TButton", background=c["sidebar"], foreground=c["sidebar_text"],
                    anchor="w", padding=(20, 11), borderwidth=0, focusthickness=0,
                    focuscolor=c["sidebar"], font=f["base"])
    style.map("Nav.TButton", background=[("active", c["sidebar_hover"])],
              foreground=[("active", "white")])
    style.configure("NavActive.TButton", background=c["sidebar_active"], foreground="white",
                    anchor="w", padding=(20, 11), borderwidth=0, focusthickness=0,
                    focuscolor=c["sidebar_active"], font=f["bold"])
    style.map("NavActive.TButton", background=[("active", c["sidebar_active"])])

    # inputs
    style.configure("TEntry", fieldbackground="white", padding=5)
    style.configure("TCombobox", fieldbackground="white", padding=4, arrowsize=14)
    style.map("TCombobox", fieldbackground=[("readonly", "white")])
    style.configure("TCheckbutton", background=c["surface"])
    style.configure("TSeparator", background=c["border"])

    # table
    style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"],
                    foreground=c["text"], rowheight=scale(root, 30), borderwidth=0)
    style.map("Treeview", background=[("selected", c["accent"])],
              foreground=[("selected", "white")])
    style.configure("Treeview.Heading", background=c["header"], foreground=c["text"],
                    font=f["bold"], relief="flat", padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", "#E2E7F3")])

    # progress bars
    style.configure("Success.Horizontal.TProgressbar", troughcolor="#E5E7EB",
                    background=c["success"], bordercolor="#E5E7EB",
                    lightcolor=c["success"], darkcolor=c["success"], thickness=scale(root, 12))
    style.configure("Accent.Horizontal.TProgressbar", troughcolor="#E5E7EB",
                    background=c["accent"], bordercolor="#E5E7EB",
                    lightcolor=c["accent"], darkcolor=c["accent"], thickness=scale(root, 8))

    # drop-down list colours (the popup list is a plain Tk widget)
    root.option_add("*TCombobox*Listbox.background", "white")
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "white")
    root.option_add("*TCombobox*Listbox.font", f["base"])
    return theme
