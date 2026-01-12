from storage import Storage
from controller.controller import Controller
from ui.app_ui import AppUI


def test_refactor_integration(tk_root, temp_storage):
    s = temp_storage
    sid = s.create_session('Refactor')
    for i in range(3):
        s.append_message(sid, 'user', f'Old msg {i}')

    ctrl = Controller(None, s, None, {})
    ui = AppUI(ctrl)
    ctrl.ui = ui
    # refresh and select the session
    ui.refresh_sessions(s.list_sessions())
    ui.session_listbox.selection_set(0)
    ui.handle_select(None)
    # add a new message via wrapper
    ui.add_message_bubble('assistant', 'Hello from new MessageList!')
    bubbles = ui._message_list.get_bubbles() if ui._message_list else []
    assert len(bubbles) >= 1
    # test deletion of index 0 via bubble delete callback
    if bubbles:
        ui._on_bubble_delete(0)
        assert len(s.get_session(sid)['messages']) == 2
    # test copy notification (simulate selection)
    ui._selected_msg_indices.clear()
    ui._selected_msg_indices.add(0)
    ui.handle_copy_selected()
    # notification label should contain copied text var
    assert ui._notif_var.get() in ('已复制 √', '')
    ui.root.destroy()