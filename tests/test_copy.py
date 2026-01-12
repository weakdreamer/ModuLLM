from storage import Storage
from controller.controller import Controller
from ui.app_ui import AppUI


def test_individual_copy_shows_confirmation(tk_root, temp_storage):
    s = temp_storage
    sid = s.create_session('CopyTest')
    s.append_message(sid, 'assistant', 'Copy target')

    ctrl = Controller(None, s, None, {})
    ui = AppUI(ctrl)
    ctrl.ui = ui
    ui.refresh_sessions(s.list_sessions())
    ui.session_listbox.selection_set(0)
    ui.handle_select(None)

    bubbles = ui._message_list.get_bubbles()
    b = bubbles[0]
    # simulate copy action (bubble will call MessageList._on_copy -> app._show_notification)
    b.on_copy('Copy target')
    assert ui._notif_var.get() == '已复制 √'
    ui.root.destroy()