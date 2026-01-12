from ui.config_panel import ConfigPanel


def test_on_save_and_batch_buttons(tmp_path, tk_root):
    cp = ConfigPanel(tk_root, {})
    called = {}

    def on_save(cfg):
        called['cfg'] = cfg

    cp.on_save = on_save
    cp.timeout_var.set('60')
    cp._on_save()

    assert 'cfg' in called
    assert called['cfg']['timeout'] == 60

    # batch buttons enabled/disabled (accept different state representations for tk/ttk)
    cp.set_batch_buttons_enabled(True)
    assert 'normal' in str(cp.copy_sel_btn['state'])
    cp.set_batch_buttons_enabled(False)
    assert 'disabled' in str(cp.copy_sel_btn['state'])
