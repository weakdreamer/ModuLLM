from ui.input_area import InputArea


def test_send_and_auto_expand(tk_root):
    ia = InputArea(tk_root, {})
    called = {}

    def on_send(text):
        called['sent'] = text

    ia.on_send = on_send
    ia.input_text.insert('1.0', 'hello')
    ia._on_send()
    assert called.get('sent') == 'hello'
    # input should be cleared
    assert ia.get_text() == ''

    # auto expand: insert many lines
    ia.input_text.insert('1.0', '\n'.join(['line']*10))
    ia._auto_expand_input()
    h = int(ia.input_text['height'])
    assert h >= 2
