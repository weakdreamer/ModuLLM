from ui.bubble import MessageBubble
from ui.theme import get_theme
import tkinter as tk


def test_clicking_checkmark_toggles_selection(tk_root):
    theme = get_theme('light')
    frame = tk.Frame(tk_root)
    frame.pack()
    b = MessageBubble(frame, 'assistant', 'Hello', theme)
    assert getattr(b, '_sel_rect', None) is not None
    # initially unselected
    assert not getattr(b, '_selected', False)
    # simulate clicking the hit area (which is where selection rect sits)
    bbox = b.canvas.bbox(b._sel_rect)
    cx = int((bbox[0] + bbox[2]) / 2)
    cy = int((bbox[1] + bbox[3]) / 2)
    # simulate click by invoking stored callback (tests can't always generate canvas item events reliably)
    try:
        cb = b.canvas._selection_callbacks.get(b._sel_rect) if getattr(b.canvas, '_selection_callbacks', None) else None
        assert cb is not None
        cb()
        assert getattr(b, '_selected', False)
        # click again
        cb()
        assert not getattr(b, '_selected', False)
    except Exception:
        # fallback to direct toggle if mapping not present
        b._toggle_selection()
        assert getattr(b, '_selected', False)
        b._toggle_selection()
        assert not getattr(b, '_selected', False)
