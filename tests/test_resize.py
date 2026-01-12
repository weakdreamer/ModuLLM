from ui.app_ui import AppUI
from controller.controller import Controller
from storage import Storage


def test_layout_resize_effects(tk_root):
    s = Storage()
    ctrl = Controller(None, s, None, {})
    ui = AppUI(ctrl)
    ctrl.ui = ui
    ui.root.update_idletasks()
    w0 = ui.root.winfo_width()
    session_w0 = ui.session_listbox.winfo_width()
    input_w0 = ui.input_text.winfo_width()
    # resize
    ui.root.geometry('1200x900')
    ui.root.update_idletasks()
    w1 = ui.root.winfo_width()
    session_w1 = ui.session_listbox.winfo_width()
    input_w1 = ui.input_text.winfo_width()
    assert w1 != w0
    ui.root.destroy()