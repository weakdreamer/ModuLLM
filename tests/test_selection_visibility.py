from ui.bubble import MessageBubble
from ui.theme import get_theme
import tkinter as tk


def test_selection_checkbox_visibility(tk_root):
    theme = get_theme('light')
    frame = tk.Frame(tk_root)
    frame.pack()
    b = MessageBubble(frame, 'assistant', 'Hello', theme)
    # ensure selection rect was created and uses the muted outline color
    assert getattr(b, '_sel_rect', None) is not None
    outline = b.canvas.itemcget(b._sel_rect, 'outline')
    assert outline == theme.get('muted')
    # unselected state should have subtle fill and thicker border for contrast
    fill0 = b.canvas.itemcget(b._sel_rect, 'fill')
    width0 = b.canvas.itemcget(b._sel_rect, 'width')
    assert fill0 in ('#f0f0f0', '#3a3a3a')
    assert width0 in ('2', '2.0')
    # toggle selection: fill becomes selection color (contrast) and checkmark appears
    b._toggle_selection()
    fill = b.canvas.itemcget(b._sel_rect, 'fill')
    assert fill == theme.get('selection')
    assert getattr(b, '_sel_check', None) is not None
    check_text = b.canvas.itemcget(b._sel_check, 'text')
    assert check_text == '✓'
    # toggle back: checkmark removed and fill returns to subtle
    b._toggle_selection()
    fill2 = b.canvas.itemcget(b._sel_rect, 'fill')
    assert fill2 in ('#f0f0f0', '#3a3a3a')
    assert getattr(b, '_sel_check', None) is None