from ui.session_list import SessionList


def test_set_sessions_and_callbacks(tk_root):
    slist = SessionList(tk_root)
    called = {}

    def on_select(sid):
        called['sid'] = sid
    slist.on_select = on_select
    sessions = [{'session_id':'s1','title':'First'},{'session_id':'s2','title':'Second'}]
    slist.set_sessions(sessions)
    # select first and fire selection event
    slist.listbox.selection_set(0)
    slist.listbox.event_generate('<<ListboxSelect>>')
    assert called.get('sid') == 's1'

    # rename callback
    called2 = {}
    def on_rename(sid):
        called2['rename'] = sid
    slist.on_rename = on_rename
    slist.listbox.selection_set(1)
    slist._on_rename()
    assert called2['rename'] == 's2'
