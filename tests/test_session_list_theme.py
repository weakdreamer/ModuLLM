from ui.session_list import SessionList
from ui.theme import get_theme
import tkinter as tk


def test_session_list_theme_applies_select_color(tk_root):
    s = SessionList(tk_root)
    light = get_theme('light')
    s.set_theme(light)
    assert s.listbox.cget('selectbackground') == light.get('history_selected')

    dark = get_theme('dark')
    s.set_theme(dark)
    assert s.listbox.cget('selectbackground') == dark.get('history_selected')
