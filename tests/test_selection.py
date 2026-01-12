from storage import Storage
from controller.controller import Controller
from ui.app_ui import AppUI


def test_selection_toggles_update_appui(tk_root, temp_storage):
    s = temp_storage
    sid = s.create_session('SelectTest')
    for i in range(3):
        s.append_message(sid, 'assistant', f'Msg {i}')

    ctrl = Controller(None, s, None, {})
    ui = AppUI(ctrl)
    ctrl.ui = ui
    ui.refresh_sessions(s.list_sessions())
    ui.session_listbox.selection_set(0)
    ui.handle_select(None)
    bubbles = ui._message_list.get_bubbles() if ui._message_list else []
    assert len(bubbles) == 3
    if bubbles:
        b = bubbles[0]
        b._toggle_selection()
        assert 0 in ui._selected_msg_indices
        b._toggle_selection()
        assert 0 not in ui._selected_msg_indices
    ui.root.destroy()