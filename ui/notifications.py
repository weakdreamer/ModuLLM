"""Notification utilities for AppUI."""
import tkinter as tk
from typing import Optional


def show_notification(root: tk.Tk, label: tk.Label, text: str, duration: int = 2000, relx: float = 0.5, rely: float = 0.06):
    """Place the provided label centered at (relx, rely) and show text for duration ms."""
    try:
        label.config(text=text)
        label.place(relx=relx, rely=rely, anchor='n')
        label.lift()
        root.after(duration, lambda: label.place_forget())
    except Exception:
        try:
            # fallback: set text then clear
            label.config(text=text)
            root.after(duration, lambda: label.config(text=''))
        except Exception:
            pass
