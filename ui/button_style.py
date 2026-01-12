import ttkbootstrap as tb
from tkinter import ttk

# Fallback if ttkbootstrap not available, use ttk
try:
    from ttkbootstrap import Style
    HAS_TTB = True
except Exception:
    HAS_TTB = False


def configure_button_styles(theme: dict):
    """Configure ttk styles for rounded buttons using available theme colors."""
    style = ttk.Style()
    # Basic rounded-like styling via padding and flat relief
    style.configure('Primary.Rounded.TButton', relief='flat', padding=(10, 6), foreground='white', background=theme.get('accent'))
    style.map('Primary.Rounded.TButton', background=[('active', theme.get('accent'))])

    style.configure('Success.Rounded.TButton', relief='flat', padding=(10, 6), foreground='white', background=theme.get('success', '#27ae60'))
    style.map('Success.Rounded.TButton', background=[('active', theme.get('success', '#27ae60'))])

    style.configure('Danger.Rounded.TButton', relief='flat', padding=(10, 6), foreground='white', background=theme.get('danger', '#c0392b'))
    style.map('Danger.Rounded.TButton', background=[('active', theme.get('danger', '#c0392b'))])

    style.configure('Secondary.Rounded.TButton', relief='flat', padding=(10, 6), foreground='white', background=theme.get('muted'))
    style.map('Secondary.Rounded.TButton', background=[('active', theme.get('muted'))])
