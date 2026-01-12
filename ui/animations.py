"""Simple, safe UI animation helpers (non-invasive)."""
from typing import Callable


def expand_width(widget, target_width: int, steps: int = 6, delay: int = 25):
    """Safely animate widget width from current width to target_width by incrementing width.
    This avoids messing with geometry managers like place_forget or place().
    """
    try:
        cur = widget.winfo_width() or 1
    except Exception:
        try:
            cur = int(widget.cget('width'))
        except Exception:
            cur = 1
    if cur >= target_width or steps <= 0:
        try:
            widget.config(width=target_width)
        except Exception:
            pass
        return

    step_size = (target_width - cur) // steps
    if step_size <= 0:
        step_size = 1

    def animate(step_count):
        try:
            new_width = cur + step_size * step_count
            if new_width >= target_width:
                new_width = target_width
            widget.config(width=new_width)
            if new_width < target_width and step_count < steps:
                widget.after(delay, lambda: animate(step_count + 1))
        except Exception:
            pass

    animate(1)
